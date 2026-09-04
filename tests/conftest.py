"""
Fixtures compartilhadas dos testes de banco/pipeline.

`built_database` (escopo de sessão) roda o orquestrador real do projeto
(`src.jobs.build_database.main`) uma única vez por sessão de testes —
os testes não reimplementam a construção do banco, só verificam o resultado
do mesmo caminho usado em produção (`python -m src.jobs.build_database`).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
for path in (ROOT, SRC):
    if path not in sys.path:
        sys.path.insert(0, path)
os.chdir(ROOT)  # os scripts do projeto assumem caminhos relativos à raiz (data/..., reports/...)

from src.database.connection import DB_PATH, get_connection  # noqa: E402


@pytest.fixture(scope="session")
def built_database() -> str:
    """Garante que `data/prf.duckdb` existe e reflete o pipeline completo
    (raw -> bronze -> silver -> gold)."""
    from src.jobs import build_database

    build_database.main()
    assert os.path.exists(DB_PATH)
    return DB_PATH


@pytest.fixture()
def con(built_database):
    """Conexão somente leitura sobre o banco já construído — para testes que
    apenas inspecionam o resultado."""
    connection = get_connection(built_database, read_only=True)
    yield connection
    connection.close()


@pytest.fixture()
def write_con(built_database):
    """Conexão de leitura/escrita sobre o banco já construído — para testes
    que exercitam `create_table(con)` diretamente (idempotência, dependência
    entre camadas)."""
    connection = get_connection(built_database, read_only=False)
    yield connection
    connection.close()
