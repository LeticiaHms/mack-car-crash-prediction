"""Testes unitários da camada central de conexão (`src/database/connection.py`),
isolados do pipeline completo — usam um banco DuckDB temporário próprio."""
import os

import pandas as pd

from src.database.connection import SCHEMAS, create_table_from_df, ensure_schemas, get_connection, table_exists


def test_get_connection_cria_arquivo_do_banco(tmp_path):
    db_path = str(tmp_path / "sub" / "test.duckdb")
    con = get_connection(db_path)
    try:
        assert os.path.exists(db_path)
    finally:
        con.close()


def test_ensure_schemas_cria_raw_bronze_silver_gold(tmp_path):
    con = get_connection(str(tmp_path / "test.duckdb"))
    try:
        ensure_schemas(con)
        schemas = {r[0] for r in con.execute("SELECT schema_name FROM information_schema.schemata").fetchall()}
        for schema in SCHEMAS:
            assert schema in schemas
    finally:
        con.close()


def test_create_table_from_df_materializa_e_substitui_por_completo(tmp_path):
    con = get_connection(str(tmp_path / "test.duckdb"))
    try:
        ensure_schemas(con)
        create_table_from_df(con, "bronze", "exemplo", pd.DataFrame({"a": [1, 2, 3]}))
        assert table_exists(con, "bronze", "exemplo")
        assert con.execute("SELECT count(*) FROM bronze.exemplo").fetchone()[0] == 3

        # CREATE OR REPLACE: a segunda chamada substitui o conteúdo, não concatena.
        create_table_from_df(con, "bronze", "exemplo", pd.DataFrame({"a": [1]}))
        assert con.execute("SELECT count(*) FROM bronze.exemplo").fetchone()[0] == 1
    finally:
        con.close()


def test_table_exists_e_falso_para_tabela_inexistente(tmp_path):
    con = get_connection(str(tmp_path / "test.duckdb"))
    try:
        ensure_schemas(con)
        assert table_exists(con, "bronze", "nao_existe") is False
    finally:
        con.close()
