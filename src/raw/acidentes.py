"""
Camada Raw: ingestão do CSV bruto da PRF (`data/raw/datatran*.csv`) como
`raw.acidentes` no DuckDB, sem nenhuma regra de negócio aplicada.

Esta é a mesma leitura que antes vivia dentro do pré-processamento (encoding
latin-1, separador ';', tratamento dos tokens de ausência de valor da PRF) —
é parsing de formato de arquivo, não limpeza de dado, então mora na Raw. A
camada Bronze (`src/bronze/acidentes.py`) parte de `raw.acidentes`, nunca lê
os CSVs diretamente, para que a dependência raw -> bronze fique explícita.

Uso:
    python -m src.raw.acidentes
"""
from __future__ import annotations

import glob
import logging

import pandas as pd

from src.database.connection import create_table_from_df, ensure_schemas, get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAW_GLOB = 'data/raw/datatran*.csv'

# Tokens que representam ausência de informação nos CSVs da PRF.
NA_TOKENS = ['NA', 'na', 'NaN', 'nan', 'None', 'none', '']


def load_raw_data(file_paths: list[str] | None = None) -> pd.DataFrame:
    """Lê e concatena os CSVs anuais da PRF, sem qualquer limpeza além do
    parsing de encoding/separador/tokens de nulo — puramente estrutural."""
    file_paths = file_paths if file_paths is not None else glob.glob(RAW_GLOB)
    logging.info(f"Carregando {len(file_paths)} arquivos...")
    dfs = []
    for file in sorted(file_paths):
        logging.info(f"Lendo {file}...")
        # Arquivos da PRF possuem codificação latin-1 e separador ';'
        df = pd.read_csv(
            file,
            encoding='latin-1',
            sep=';',
            low_memory=False,
            na_values=NA_TOKENS,
            keep_default_na=True,
        )
        logging.info(f"  -> {len(df)} registros, {len(df.columns)} colunas em {file}")
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)
    logging.info(f"Carregados {len(combined_df)} registros no total.")
    return combined_df


def create_table(con=None) -> pd.DataFrame:
    """Materializa `raw.acidentes` no DuckDB. Reutiliza a conexão passada em
    `con` (para encadear com bronze/silver/gold no mesmo banco) ou abre e
    fecha uma própria quando chamado de forma independente."""
    own_con = con is None
    if own_con:
        con = get_connection()
        ensure_schemas(con)

    raw_files = glob.glob(RAW_GLOB)
    if not raw_files:
        raise FileNotFoundError(f"Nenhum arquivo CSV bruto encontrado em {RAW_GLOB}")

    df = load_raw_data(raw_files)
    create_table_from_df(con, "raw", "acidentes", df)
    logging.info(f"raw.acidentes materializada: {len(df)} linhas, {len(df.columns)} colunas.")

    if own_con:
        con.close()
    return df


def main():
    create_table()


if __name__ == '__main__':
    main()
