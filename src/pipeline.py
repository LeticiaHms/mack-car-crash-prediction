"""
Orquestrador do pipeline de pré-processamento.

Executa, em sequência, o pré-processamento de cada base bruta e a
validação da respectiva camada curada:

    dados/datatran*.csv          -> preprocessing.acidentes -> validation.validate_acidentes
    dados/feriados_nacionais.xls -> preprocessing.feriados  -> validation.validate_feriados

Uso, a partir da raiz do projeto: `python3 -m src.pipeline` ou
`python3 src/pipeline.py` (ambos funcionam).

Cada etapa é independente e idempotente; uma falha de validação (erro,
não aviso) interrompe o pipeline nessa etapa, sem afetar as demais bases
já processadas. Ver `docs/specs/initial_cleaning/preprocessing_guidelines.md`
(seção 12) para o desenho do fluxo, e
`docs/docs-etapas/etapa1-pre-processamento.md` para as decisões técnicas.

Cada execução também grava a evidência bruta dos logs em
`docs/evidencias/preprocess_run.log` e `docs/evidencias/verify_run.log`
(sobrescritos a cada rodada), consolidando as duas bases em cada arquivo.
"""
import contextlib
import logging
import os
import sys

# Permite rodar tanto como módulo (`python3 -m src.pipeline`) quanto como
# script direto (`python3 src/pipeline.py`). Neste segundo caso, o Python
# usa `src/` como raiz de busca e não enxerga o pacote `src` — corrigimos
# adicionando a raiz do projeto ao sys.path antes do import.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocessing import acidentes, feriados, validation

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
    logs de mais de uma base processada na mesma execução (ex.: acidentes
    seguido de feriados)."""
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


def run_acidentes():
    with _capturar_log_em_arquivo(PREPROCESS_LOG_PATH, mode='w'):
        logging.info("=== Etapa: pré-processamento de acidentes (PRF) ===")
        acidentes.main()

    with _capturar_log_em_arquivo(VERIFY_LOG_PATH, mode='w'):
        logging.info("=== Etapa: validação da camada curada de acidentes ===")
        validation._validate_file(
            validation.ACIDENTES_PATH, validation.ACIDENTES_REPORT_PATH,
            validation.validate_acidentes, 'acidentes',
        )


def run_feriados():
    with _capturar_log_em_arquivo(PREPROCESS_LOG_PATH, mode='a'):
        logging.info("=== Etapa: pré-processamento de feriados nacionais (ANBIMA) ===")
        feriados.main()

    with _capturar_log_em_arquivo(VERIFY_LOG_PATH, mode='a'):
        logging.info("=== Etapa: validação da camada curada de feriados ===")
        validation._validate_file(
            validation.FERIADOS_PATH, validation.FERIADOS_REPORT_PATH,
            validation.validate_feriados, 'feriados',
        )


def main():
    run_acidentes()
    run_feriados()
    logging.info("Pipeline de pré-processamento concluído.")


if __name__ == '__main__':
    main()
