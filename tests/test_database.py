"""O banco existe, os schemas de camada existem e cada tabela esperada existe
e não está vazia (item 16, bloco "Banco")."""
import os

from src.database.connection import SCHEMAS, table_exists

EXPECTED_TABLES = [
    ("raw", "acidentes"),
    ("raw", "feriados"),
    ("bronze", "acidentes"),
    ("bronze", "feriados"),
    ("silver", "acidentes"),
    ("gold", "dataset_ml"),
]


def test_arquivo_do_banco_existe(built_database):
    assert os.path.exists(built_database)


def test_schemas_de_camada_existem(con):
    schemas = {r[0] for r in con.execute("SELECT schema_name FROM information_schema.schemata").fetchall()}
    for schema in SCHEMAS:
        assert schema in schemas, f"schema {schema} não existe"


def test_tabelas_esperadas_existem(con):
    for schema, table in EXPECTED_TABLES:
        assert table_exists(con, schema, table), f"{schema}.{table} não existe"


def test_tabelas_esperadas_nao_estao_vazias(con):
    for schema, table in EXPECTED_TABLES:
        n = con.execute(f"SELECT count(*) FROM {schema}.{table}").fetchone()[0]
        assert n > 0, f"{schema}.{table} está vazia"
