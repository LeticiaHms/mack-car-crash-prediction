"""
Infraestrutura compartilhada do app Streamlit (skill `streamlit-ml-eda`).

Mantém a camada de UI separada da lógica analítica: todo cálculo pesado é
delegado a `src/eda_utils.py` (que por sua vez usa DuckDB sobre o Parquet
curado). Este módulo cuida apenas de:
- localizar o `src/` do projeto no sys.path;
- cachear a conexão DuckDB e os resultados de query (st.cache_resource/data);
- renderizar os filtros globais na sidebar e construir a view filtrada
  reutilizada por todas as páginas.
"""
from __future__ import annotations

import os
import sys

import duckdb
import pandas as pd
import streamlit as st

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
os.chdir(_ROOT)  # garante que caminhos relativos ("dados/curated/...") funcionem

import eda_utils as eu  # noqa: E402

CURATED_PATH = os.path.join(_ROOT, eu.CURATED_PATH)


@st.cache_resource(show_spinner=False)
def get_connection() -> duckdb.DuckDBPyConnection:
    return eu.get_connection(CURATED_PATH)


@st.cache_data(show_spinner=False)
def query(sql: str) -> pd.DataFrame:
    con = get_connection()
    return con.execute(sql).df()


@st.cache_data(show_spinner=False)
def consolidation_info() -> dict:
    """Diagnóstico da janela final ainda não consolidada da série (ver 🧹 Qualidade)."""
    info = eu.consolidation_cutoff(get_connection())
    info.pop("series", None)
    return info


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
    """Renderiza os filtros globais e retorna (where_clause_sql, selecoes)."""
    st.sidebar.header("🔍 Filtros")
    st.sidebar.caption(
        "Filtros ativos afetam todas as páginas. "
        "2026 só tem dados até julho — comparações anuais devem considerar isso."
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
            "⚠️ 2026 é um ano parcial (jan–jul). Comparar contagens totais com anos completos "
            "pode sugerir uma queda que não existe — veja docs/DECISIONS.md (D-12)."
        )

    st.sidebar.divider()
    info = consolidation_info()
    excluir = st.sidebar.checkbox(
        "Excluir janela não consolidada",
        value=False,
        key="filter_consolidado",
        help=(
            f"Os últimos {info['days_flagged']} dias da série (após {info['cutoff_date']}) têm volume "
            "muito abaixo do histórico — padrão típico de registro ainda não consolidado na fonte, "
            "não de queda real de acidentes. Marque para cortá-los de todas as páginas. "
            "Desmarcado por padrão para reproduzir os números de docs/specs/eda/EDA.md."
        ),
    )
    selections["_janela_consolidada"] = excluir
    if excluir:
        clauses.append(f"data_inversa <= DATE '{info['cutoff_date']}'")
        st.sidebar.caption(
            f"✂️ Excluindo {info['rows_flagged']:,} registros posteriores a {info['cutoff_date']}."
            .replace(",", ".")
        )

    where_clause = " AND ".join(clauses) if clauses else "1=1"
    if st.sidebar.button("Limpar filtros"):
        for col, _, _ in FILTER_DEFS:
            st.session_state[f"filter_{col}"] = []
        st.session_state["filter_consolidado"] = False
        st.rerun()

    return where_clause, selections


def filtered_view_sql(where_clause: str) -> str:
    """SQL de subquery pronta para uso em qualquer página: `FROM ({filtered_view_sql(where)}) t`."""
    return f"SELECT * FROM acidentes_enriquecido WHERE {where_clause}"


def show_active_filters(selections: dict):
    active = {k: v for k, v in selections.items() if v and not k.startswith("_")}
    parts = [f"**{k}**: {', '.join(map(str, v))}" for k, v in active.items()]
    if selections.get("_janela_consolidada"):
        parts.append("**período**: até " + consolidation_info()["cutoff_date"] + " (janela consolidada)")
    if not parts:
        n = total_rows()
        rng = query("SELECT min(data_inversa)::DATE mn, max(data_inversa)::DATE mx FROM acidentes").iloc[0]
        st.caption(
            f"Nenhum filtro ativo — exibindo os {n:,} registros de {rng['mn']} a {rng['mx']}.".replace(",", ".")
        )
    else:
        st.caption("Filtros ativos → " + " | ".join(parts))
