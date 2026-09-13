"""
Infraestrutura compartilhada do app Streamlit (skill `streamlit-ml-eda`).

Mantém a camada de UI separada da lógica analítica: todo cálculo pesado é
delegado ao DuckDB — o Streamlit **consome** as tabelas já materializadas em
`data/prf.duckdb` (`src/database/connection.py`), nunca reconstrói dado a
partir dos CSVs brutos. Este módulo cuida apenas de:
- localizar a raiz do projeto no sys.path;
- cachear a conexão DuckDB (somente leitura) e os resultados de query
  (st.cache_resource/data);
- renderizar os filtros globais na sidebar e construir a view filtrada
  reutilizada por todas as páginas.

As páginas de EDA (Visão Geral, Datas & Geografia, Sazonalidade, Correlações)
leem a camada **Silver** (`get_connection`/`query`, tabela `silver.acidentes`)
— já enriquecida e já recortada no corte de consolidação (D-13), sem precisar
de um toggle na UI para isso. A página 🧹 Qualidade dos Dados lê a **Bronze**
(`get_bronze_connection`, tabelas `bronze.acidentes`/`bronze.feriados`) para
mostrar a janela não consolidada que a Silver já removeu. A página de
Modelagem & Features lê a **Gold** (`get_gold_connection`/`query_gold`,
tabela `gold.dataset_ml`) para mostrar o schema real do dataset de ML.

Se `data/prf.duckdb` ainda não existir (ou estiver desatualizado), rode
`python -m src.jobs.build_database` antes de subir o app — o Streamlit
não faz isso por conta própria.
"""
from __future__ import annotations

import os
import sys

import duckdb
import pandas as pd
import streamlit as st

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)  # garante que caminhos relativos ("data/prf.duckdb", relatórios...) funcionem

from src.eda import utils as eu  # noqa: E402
from src.database.connection import DB_PATH, get_connection as get_db_connection  # noqa: E402


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    """Conexão somente leitura sobre `silver.acidentes`.

    As views `acidentes` e `acidentes_enriquecido` apontam para a mesma
    tabela: a Silver já contém `ano`/`mes`/`hora`/`gravidade_4`/`tipo_dia`/...
    prontas (foi assim que `src/silver/acidentes.py` a construiu) — reservar
    os dois nomes evita reescrever as páginas que já usam um ou outro.
    """
    con = get_db_connection(DB_PATH, read_only=True)
    con.execute("CREATE OR REPLACE TEMP VIEW acidentes AS SELECT * FROM silver.acidentes")
    con.execute("CREATE OR REPLACE TEMP VIEW acidentes_enriquecido AS SELECT * FROM silver.acidentes")
    return con


@st.cache_resource(show_spinner=False)
def get_bronze_connection() -> duckdb.DuckDBPyConnection:
    """Conexão somente leitura sobre a Bronze (pré-corte) — usada **apenas**
    pela página 🧹 Qualidade dos Dados, que precisa mostrar a janela final
    não consolidada (D-13) que a Silver já removeu. Monta as mesmas views
    `acidentes`/`feriados`/`acidentes_enriquecido` de `eu.build_bronze_views`,
    reaproveitando `eu.build_enriched_view` para não duplicar o SQL de
    enriquecimento."""
    con = get_db_connection(DB_PATH, read_only=True)
    con.execute("CREATE OR REPLACE TEMP VIEW acidentes AS SELECT * FROM bronze.acidentes")
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW feriados AS
        SELECT data::DATE AS data, string_agg(DISTINCT feriado, ' / ') AS feriado
        FROM bronze.feriados
        GROUP BY 1
        """
    )
    eu.build_enriched_view(con)
    return con


@st.cache_resource(show_spinner=False)
def get_gold_connection() -> duckdb.DuckDBPyConnection:
    """Conexão somente leitura sobre `gold.dataset_ml`."""
    con = get_db_connection(DB_PATH, read_only=True)
    con.execute("CREATE OR REPLACE TEMP VIEW gold AS SELECT * FROM gold.dataset_ml")
    return con


@st.cache_data(show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql).df()


@st.cache_data(show_spinner=False)
def query_gold(sql: str) -> pd.DataFrame:
    con = get_gold_connection()
    return con.execute(sql).df()


@st.cache_data(show_spinner=False)
def consolidation_info() -> dict:
    """Data e evidência do corte de consolidação (D-13) já aplicado na
    construção da Silver — lido do relatório gravado por `src/silver/acidentes.py`,
    não recalculado aqui (a Silver já está cortada, recalcular sobre ela
    não encontraria mais nada sinalizado)."""
    import json
    report_path = os.path.join(_ROOT, "reports/data_quality/silver_report.json")
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    return report["consolidation_cutoff"]


@st.cache_data(show_spinner=False)
def total_rows() -> int:
    return int(query("SELECT count(*) n FROM acidentes").iloc[0]["n"])


@st.cache_data(show_spinner=False)
def distinct_values(column: str, source: str = "acidentes_enriquecido") -> list:
    df = query(f"SELECT DISTINCT {column} AS v FROM {source} WHERE {column} IS NOT NULL ORDER BY 1")
    return df["v"].tolist()


FILTER_DEFS = [
    ("ano", "Ano", "acidentes_enriquecido"),
    ("uf", "UF", "acidentes_enriquecido"),
    ("gravidade_4", "Gravidade", "acidentes_enriquecido"),
    ("tipo_acidente", "Tipo de acidente", "acidentes_enriquecido"),
    ("br", "Rodovia (BR)", "acidentes_enriquecido"),
    ("fase_dia", "Período do dia / iluminação", "acidentes_enriquecido"),
    ("condicao_metereologica", "Condição meteorológica", "acidentes_enriquecido"),
    ("tipo_pista", "Tipo de pista", "acidentes_enriquecido"),
]


def render_sidebar_filters() -> tuple[str, dict]:
    """Renderiza os filtros globais e retorna (where_clause_sql, selecoes).

    O corte da janela final não consolidada (D-13) não é mais um filtro de
    UI: acontece na camada Silver (`src/silver/acidentes.py`), então todo dado que
    chega até aqui já está no período consolidado — a sidebar só informa a
    data de corte, não oferece um toggle para (des)aplicá-lo.
    """
    st.sidebar.header("🔍 Filtros")
    info = consolidation_info()
    st.sidebar.caption(
        f"Filtros ativos afetam todas as páginas. Dados já restritos ao período consolidado "
        f"(até {info['cutoff_date']}) na camada Silver — ver 🧹 Qualidade dos Dados."
    )
    selections: dict = {}
    clauses: list[str] = []

    for col, label, _src in FILTER_DEFS:
        options = distinct_values(col)
        key = f"filter_{col}"
        chosen = st.sidebar.multiselect(label, options, default=[], key=key)
        selections[col] = chosen
        if chosen:
            if isinstance(options[0], str):
                vals = ", ".join("'" + str(v).replace("'", "''") + "'" for v in chosen)
            else:
                vals = ", ".join(str(v) for v in chosen)
            clauses.append(f"{col} IN ({vals})")

    if selections.get("ano") and 2026 in selections["ano"] and len(selections["ano"]) > 1:
        st.sidebar.warning(
            f"⚠️ 2026 é um ano parcial (até {info['cutoff_date']}). Comparar contagens totais com anos "
            "completos pode sugerir uma queda que não existe — veja docs/decisoes/DECISIONS.md (D-12/D-13)."
        )

    where_clause = " AND ".join(clauses) if clauses else "1=1"
    if st.sidebar.button("Limpar filtros"):
        for col, _, _ in FILTER_DEFS:
            st.session_state[f"filter_{col}"] = []
        st.rerun()

    return where_clause, selections


def filtered_view_sql(where_clause: str) -> str:
    """SQL de subquery pronta para uso em qualquer página: `FROM ({filtered_view_sql(where)}) t`."""
    return f"SELECT * FROM acidentes_enriquecido WHERE {where_clause}"


def show_active_filters(selections: dict):
    active = {k: v for k, v in selections.items() if v and not k.startswith("_")}
    parts = [f"**{k}**: {', '.join(map(str, v))}" for k, v in active.items()]
    if not parts:
        n = total_rows()
        rng = query("SELECT min(data_inversa)::DATE mn, max(data_inversa)::DATE mx FROM acidentes").iloc[0]
        st.caption(
            f"Nenhum filtro ativo — exibindo os {n:,} registros de {rng['mn']} a {rng['mx']}.".replace(",", ".")
        )
    else:
        st.caption("Filtros ativos → " + " | ".join(parts))
