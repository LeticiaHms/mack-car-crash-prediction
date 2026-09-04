"""
Construção da camada Silver: enriquecimento analítico + corte de consolidação.

Lê a Bronze direto do banco (`bronze.acidentes` + `bronze.feriados`),
reaproveita a view `acidentes_enriquecido` já definida em `src.eda.utils`
(ano/mes/dia/hora, `gravidade_4`, `grave_bin`, `tipo_dia`, `nome_feriado`), adiciona
flags de qualidade sem remover nenhuma linha (D-04/D-05: `br=0`, `km<=0` e
coordenadas zeradas são sentinelas de "não informado", não valores reais) e aplica
o corte de consolidação (D-13) — a parte final da série que ainda não está
consolidada na fonte da PRF deixa de existir a partir daqui, não é mais um filtro
opcional do Streamlit.

A Silver ainda contém as colunas de leakage (`mortos`, `feridos_*`, etc.): ela serve
à EDA e à Feature Engineering, não é o dataset final de ML — isso é papel da Gold
(`src/gold/dataset_ml.py`).

`create_table(con)` materializa o resultado como `silver.acidentes` no DuckDB
(`src/database/connection.py`), garantindo antes que `bronze.acidentes` e
`bronze.feriados` existam — a dependência silver -> bronze fica explícita.

Uso:
    python -m src.silver.acidentes

Saídas:
    tabela `silver.acidentes` em data/prf.duckdb  (único lugar onde o dado vive)
    reports/data_quality/silver_report.json       (evidência do corte + flags)
"""
from __future__ import annotations

import json
import logging
import os
import sys

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../src/silver -> raiz
sys.path.insert(0, _ROOT_DIR)

from src.eda import utils as eu  # noqa: E402
from src.database.connection import create_table_from_df, ensure_schemas, get_connection, table_exists  # noqa: E402
from src.bronze import acidentes as bronze_acidentes  # noqa: E402
from src.bronze import feriados as bronze_feriados  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REPORT_PATH = "reports/data_quality/silver_report.json"


def build_silver(con) -> tuple:
    """Constrói o DataFrame da Silver e o relatório de qualidade/corte a partir
    das tabelas `bronze.*` da conexão recebida.

    Recebe a conexão (em vez de abrir a sua) porque o DuckDB não permite duas
    conexões com configurações diferentes para o mesmo arquivo — dentro do
    pipeline, a conexão de escrita já está aberta. Retorna
    (dataframe, report_dict), permitindo reuso em testes/notebooks sem gravar
    nada em disco.
    """
    eu.build_bronze_views(con)

    total_bronze = int(eu.df(con, "SELECT count(*) n FROM acidentes").iloc[0]["n"])
    logging.info(f"Bronze carregada: {total_bronze} linhas.")

    cutoff = eu.consolidation_cutoff(con)
    cutoff.pop("series", None)
    cutoff_date = cutoff["cutoff_date"]
    logging.info(
        f"Corte de consolidação (D-13): {cutoff_date} "
        f"({cutoff['days_flagged']} dias sinalizados, {cutoff['rows_flagged']} linhas removidas da Silver)."
    )

    silver = eu.df(
        con,
        f"""
        SELECT
            *,
            (br <> 0) AS br_valido,
            (km > 0) AS km_valido,
            (latitude <> 0 AND longitude <> 0) AS geocoord_valido
        FROM acidentes_enriquecido
        WHERE data_inversa::DATE <= DATE '{cutoff_date}'
        ORDER BY data_inversa, id
        """,
    )
    logging.info(f"Silver construída: {len(silver)} linhas ({len(silver.columns)} colunas).")

    report = {
        "consolidation_cutoff": cutoff,
        "rows_bronze": total_bronze,
        "rows_silver": int(len(silver)),
        "rows_removed_by_cutoff": int(total_bronze - len(silver)),
        "pct_removed_by_cutoff": round((total_bronze - len(silver)) / total_bronze * 100, 3),
        "quality_flags": {
            "br_invalido_n": int((~silver["br_valido"]).sum()),
            "km_invalido_n": int((~silver["km_valido"]).sum()),
            "geocoord_invalido_n": int((~silver["geocoord_valido"]).sum()),
        },
        "n_cols": int(len(silver.columns)),
        "columns": list(silver.columns),
    }
    return silver, report


def save_report(report, report_path: str = REPORT_PATH):
    """Grava o relatório de qualidade/corte da Silver. Os dados em si ficam
    apenas na tabela `silver.acidentes` do DuckDB — não há espelho em Parquet."""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logging.info(f"Relatório da Silver salvo em {report_path}")


def create_table(con=None) -> tuple:
    """Materializa `silver.acidentes` no DuckDB, garantindo antes que
    `bronze.acidentes`/`bronze.feriados` existam. Reaproveita `build_silver()`
    tal como está — nenhuma transformação é duplicada aqui."""
    own_con = con is None
    if own_con:
        con = get_connection()
    ensure_schemas(con)

    if not table_exists(con, "bronze", "acidentes"):
        bronze_acidentes.create_table(con)
    if not table_exists(con, "bronze", "feriados"):
        bronze_feriados.create_table(con)

    silver, report = build_silver(con)
    save_report(report)
    create_table_from_df(con, "silver", "acidentes", silver)
    logging.info(f"silver.acidentes materializada: {len(silver)} linhas, {len(silver.columns)} colunas.")

    if own_con:
        con.close()
    return silver, report


def main():
    create_table()


if __name__ == "__main__":
    main()
