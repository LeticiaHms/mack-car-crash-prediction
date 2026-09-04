"""
Orquestrador único do banco DuckDB do projeto (`data/prf.duckdb`).

Não contém nenhuma lógica de transformação — só chama, na ordem certa de
dependência, o `create_table(con)` de cada tabela e as validações de
qualidade já existentes. Cada `create_table` sabe construir sua própria
dependência caso ela ainda não exista (ver `src/raw`, `src/bronze`,
`src/silver`, `src/gold`), mas aqui a ordem é explícita mesmo assim, para
que o fluxo completo fique visível em um único lugar:

    1. criar schemas (raw, bronze, silver, gold)
    2. RAW:     raw.acidentes, raw.feriados
    3. BRONZE:  bronze.acidentes, bronze.feriados
    4. validação de qualidade da Bronze (src/bronze/validation.py)
    5. SILVER:  silver.acidentes
    6. GOLD:    gold.dataset_ml

Uso, a partir da raiz do projeto: `python -m src.jobs.build_database` ou
`python src/jobs/build_database.py` (ambos funcionam).

Uma falha de validação (erro, não aviso) interrompe o pipeline nessa etapa,
antes da Silver/Gold serem construídas sobre uma Bronze não confiável. Ver
`docs/specs/design.md` para o desenho original do fluxo de pré-processamento,
e `docs/entregas/etapa1-pre-processamento.md`/`docs/entregas/etapa2-eda.md`
para a arquitetura completa Raw -> Bronze -> Silver -> Gold.

Cada execução também grava a evidência bruta dos logs em
`docs/evidencias/preprocess_run.log` e `docs/evidencias/verify_run.log`
(sobrescritos a cada rodada), consolidando as duas bases em cada arquivo.
"""
import contextlib
import logging
import os
import sys

# Permite rodar tanto como módulo (`python -m src.jobs.build_database`)
# quanto como script direto (`python src/jobs/build_database.py`).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import ensure_schemas, get_connection
from src.raw import acidentes as raw_acidentes
from src.raw import feriados as raw_feriados
from src.bronze import acidentes as bronze_acidentes
from src.bronze import feriados as bronze_feriados
from src.bronze import validation
from src.silver import acidentes as silver_acidentes
from src.gold import dataset_ml as gold_dataset_ml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EVIDENCIAS_DIR = 'docs/evidencias'
PREPROCESS_LOG_PATH = os.path.join(EVIDENCIAS_DIR, 'preprocess_run.log')
VERIFY_LOG_PATH = os.path.join(EVIDENCIAS_DIR, 'verify_run.log')


@contextlib.contextmanager
def _capturar_log_em_arquivo(log_path, mode='w'):
    """Anexa um FileHandler ao logger raiz durante o bloco `with`, gravando
    também em `log_path` tudo o que os módulos do pipeline logam via
    `logging.info/warning/error`. Usado para manter as evidências em
    `docs/evidencias/` sincronizadas com cada execução real do pipeline,
    em vez de dependerem de captura manual de terminal.

    `mode='w'` (padrão) inicia um arquivo novo a cada execução do
    pipeline; `mode='a'` é usado para consolidar, no mesmo arquivo, os
    logs de mais de uma etapa processada na mesma execução (ex.: raw+bronze
    de acidentes seguido de feriados, depois silver e gold)."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    handler = logging.FileHandler(log_path, mode=mode, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    try:
        yield
    finally:
        root_logger.removeHandler(handler)
        handler.close()


def run_raw(con):
    with _capturar_log_em_arquivo(PREPROCESS_LOG_PATH, mode='w'):
        logging.info("=== Etapa: Raw — acidentes (PRF) e feriados (ANBIMA) ===")
        raw_acidentes.create_table(con)
        raw_feriados.create_table(con)


def run_bronze(con):
    """Constrói as duas tabelas da Bronze e devolve os DataFrames recém-limpos,
    que a etapa de validação usa em seguida (ver `run_validacao_bronze`)."""
    with _capturar_log_em_arquivo(PREPROCESS_LOG_PATH, mode='a'):
        logging.info("=== Etapa: Bronze — pré-processamento de acidentes (PRF) ===")
        acidentes_df, _ = bronze_acidentes.create_table(con)
        logging.info("=== Etapa: Bronze — pré-processamento de feriados nacionais (ANBIMA) ===")
        feriados_df, _ = bronze_feriados.create_table(con)
    return acidentes_df, feriados_df


def run_validacao_bronze(acidentes_df, feriados_df):
    """Valida os DataFrames da Bronze em memória — antes de qualquer round-trip
    pelo banco, que converteria os `Int64` nullable do pandas em `int64` puro e
    faria a checagem de dtype falhar sem problema real no dado."""
    with _capturar_log_em_arquivo(VERIFY_LOG_PATH, mode='w'):
        logging.info("=== Etapa: validação da camada Bronze — acidentes ===")
        validation.validate_dataframe(
            acidentes_df, validation.ACIDENTES_REPORT_PATH, validation.validate_acidentes, 'acidentes',
        )
        logging.info("=== Etapa: validação da camada Bronze — feriados ===")
        validation.validate_dataframe(
            feriados_df, validation.FERIADOS_REPORT_PATH, validation.validate_feriados, 'feriados',
        )


def run_silver(con):
    with _capturar_log_em_arquivo(PREPROCESS_LOG_PATH, mode='a'):
        logging.info("=== Etapa: construção da camada Silver ===")
        silver_acidentes.create_table(con)


def run_gold(con):
    with _capturar_log_em_arquivo(PREPROCESS_LOG_PATH, mode='a'):
        logging.info("=== Etapa: construção da camada Gold ===")
        gold_dataset_ml.create_table(con)


def main():
    con = get_connection()
    ensure_schemas(con)

    run_raw(con)
    acidentes_df, feriados_df = run_bronze(con)
    run_validacao_bronze(acidentes_df, feriados_df)
    run_silver(con)
    run_gold(con)

    con.close()
    logging.info(
        "Banco DuckDB reconstruído em data/prf.duckdb "
        "(raw -> bronze -> silver -> gold)."
    )


if __name__ == '__main__':
    main()
