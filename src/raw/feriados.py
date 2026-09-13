"""
Camada Raw: ingestão do arquivo bruto de feriados nacionais da ANBIMA
(`data/raw/feriados_nacionais.xls`) como `raw.feriados` no DuckDB, sem
nenhuma regra de negócio aplicada (nem remoção do rodapé de notas, nem
filtro de período — isso é responsabilidade da Bronze).

Uso:
    python -m src.raw.feriados
"""
from __future__ import annotations

import logging

import pandas as pd

from src.database.connection import create_table_from_df, ensure_schemas, get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAW_PATH = 'data/raw/feriados_nacionais.xls'
SHEET_NAME = 'Feriados'


def load_raw_data(file_path: str = RAW_PATH) -> pd.DataFrame:
    """Lê a planilha bruta da ANBIMA tal como está, incluindo o rodapé de
    notas explicativas — a limpeza é responsabilidade da Bronze."""
    logging.info(f"Carregando {file_path}...")
    # Arquivo .xls legado; requer o engine 'xlrd' para leitura.
    df = pd.read_excel(file_path, sheet_name=SHEET_NAME, engine='xlrd')
    logging.info(f"  -> {len(df)} linhas, {len(df.columns)} colunas (inclui rodapé de notas).")
    return df


def create_table(con=None) -> pd.DataFrame:
    """Materializa `raw.feriados` no DuckDB."""
    import os

    own_con = con is None
    if own_con:
        con = get_connection()
        ensure_schemas(con)

    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"Arquivo bruto não encontrado: {RAW_PATH}")

    df = load_raw_data()
    create_table_from_df(con, "raw", "feriados", df)
    logging.info(f"raw.feriados materializada: {len(df)} linhas, {len(df.columns)} colunas.")

    if own_con:
        con.close()
    return df


def main():
    create_table()


if __name__ == '__main__':
    main()
