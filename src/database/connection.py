"""
Camada central de conexão com o DuckDB analítico do projeto.

Centraliza o que, de outra forma, cada script de tabela reabriria por conta
própria: caminho do banco, criação dos schemas de camada e um pequeno
utilitário para materializar um DataFrame como tabela. Os scripts de
`src/raw`, `src/bronze`, `src/silver` e `src/gold` importam apenas isto —
nenhum deles conhece o caminho do arquivo `.duckdb` diretamente.

Uso típico, dentro de um `create_table(con)`:

    from src.database.connection import get_connection, ensure_schemas, create_table_from_df

    con = get_connection()
    ensure_schemas(con)
    create_table_from_df(con, "bronze", "acidentes", df)
"""
from __future__ import annotations

import os

import duckdb
import pandas as pd

# Caminho do banco DuckDB oficial do projeto, relativo à raiz do repositório
# (mesma convenção de `data/raw`, `data/bronze`, ... já usada no restante do
# projeto — não introduzimos uma pasta `data/` nova só para o banco).
DB_PATH = "data/prf.duckdb"

# Uma camada = um schema. Nesta ordem porque é a ordem de dependência
# (raw -> bronze -> silver -> gold), embora `CREATE SCHEMA IF NOT EXISTS`
# não exija ordem entre si.
SCHEMAS = ("raw", "bronze", "silver", "gold")


def get_connection(db_path: str = DB_PATH, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Abre (criando se necessário) a conexão com o banco DuckDB do projeto.

    `read_only=True` é usado por consumidores que só leem tabelas já
    materializadas (ex.: o Streamlit) e nunca devem reconstruir dados.
    """
    dir_name = os.path.dirname(db_path)
    if dir_name and not read_only:
        os.makedirs(dir_name, exist_ok=True)
    return duckdb.connect(db_path, read_only=read_only)


def ensure_schemas(con: duckdb.DuckDBPyConnection, schemas: tuple[str, ...] = SCHEMAS) -> None:
    """Garante a existência dos schemas de camada (`raw`, `bronze`, `silver`, `gold`)."""
    for schema in schemas:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def table_exists(con: duckdb.DuckDBPyConnection, schema: str, table: str) -> bool:
    """Verifica se `schema.table` já existe no banco conectado."""
    row = con.execute(
        """
        SELECT count(*) n FROM information_schema.tables
        WHERE table_schema = ? AND table_name = ?
        """,
        [schema, table],
    ).fetchone()
    return bool(row and row[0] > 0)


def create_table_from_df(con: duckdb.DuckDBPyConnection, schema: str, table: str, df: pd.DataFrame) -> None:
    """Materializa `df` como `schema.table` (`CREATE OR REPLACE TABLE`), substituindo por completo
    o conteúdo anterior — cada tabela é sempre reconstruível do zero a partir de sua dependência,
    nunca atualizada incrementalmente por fora deste fluxo."""
    con.register("_df_to_persist", df)
    try:
        con.execute(f"CREATE OR REPLACE TABLE {schema}.{table} AS SELECT * FROM _df_to_persist")
    finally:
        con.unregister("_df_to_persist")
