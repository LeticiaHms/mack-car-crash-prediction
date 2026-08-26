"""
App Streamlit de EDA/ML — Acidentes PRF (2022-2026).

Executar: `streamlit run streamlit/app.py`

Esta página é a "🔎 Visão Geral dos Dados". As demais seções ficam em
`streamlit/pages/`, seguindo a skill `streamlit-ml-eda`. Todos os cálculos
usam DuckDB sobre `dados/curated/acidentes_2022_2026.parquet` via
`src/eda_utils.py` — nenhum número é hardcoded.
"""
import plotly.express as px
import streamlit as st

from common import get_connection, query, render_sidebar_filters, show_active_filters

st.set_page_config(page_title="EDA Acidentes PRF", page_icon="🚧", layout="wide")

st.title("🚧 EDA — Acidentes em Rodovias Federais (PRF, 2022–2026)")
st.caption(
    "Fonte: dados abertos da PRF, 'Acidentes agrupados por ocorrência'. "
    "Unidade de análise: 1 linha = 1 acidente. Este app é uma ferramenta de exploração, "
    "não gera o relatório final automaticamente (skill `streamlit-ml-eda`)."
)

con = get_connection()
where, selections = render_sidebar_filters()
show_active_filters(selections)

overview = query("SELECT count(*) n, min(data_inversa) mn, max(data_inversa) mx FROM acidentes")
filtered_overview = query(f"SELECT count(*) n FROM acidentes_enriquecido WHERE {where}")
n_total = int(overview.iloc[0]["n"])
n_filtered = int(filtered_overview.iloc[0]["n"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros (total)", f"{n_total:,}".replace(",", "."))
c2.metric("Registros (filtro atual)", f"{n_filtered:,}".replace(",", "."))
c3.metric("Período", "2022-01 a 2026-07")
c4.metric("Colunas", "30")

st.divider()

col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("Registros por ano")
    by_year = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1")
    fig = px.bar(by_year, x="ano", y="n", labels={"ano": "Ano", "n": "Acidentes"})
    fig.add_annotation(x=2026, y=by_year["n"].max(), text="parcial (jan–jul)", showarrow=True, yshift=20)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "⚠️ 2026 é parcial (só até julho). Ver `docs/DECISIONS.md` (D-12) para a comparação "
        "justa jan–jul entre anos, disponível na página 📈 Tendências Temporais."
    )

with col_b:
    st.subheader("Gravidade (`grave_bin`)")
    gb = query(
        f"SELECT CASE WHEN grave_bin=1 THEN 'Grave/Fatal' ELSE 'Sem gravidade' END AS g, count(*) n "
        f"FROM acidentes_enriquecido WHERE {where} GROUP BY 1"
    )
    fig2 = px.pie(gb, names="g", values="n", hole=0.5)
    st.plotly_chart(fig2, width="stretch")

st.divider()
st.subheader("Schema e qualidade")

cols = query("DESCRIBE SELECT * FROM acidentes")
missing = query(
    "SELECT "
    + ", ".join(f"sum(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS {c}" for c in cols["column_name"])
    + " FROM acidentes"
).T
missing.columns = ["nulos"]
missing = missing[missing["nulos"] > 0]
missing["% nulos"] = (missing["nulos"] / n_total * 100).round(3)

t1, t2 = st.columns(2)
with t1:
    st.markdown("**Tipos de dados (30 colunas)**")
    st.dataframe(cols[["column_name", "column_type"]], width="stretch", height=300)
with t2:
    st.markdown("**Colunas com valores nulos**")
    if missing.empty:
        st.success("Nenhuma coluna com nulos.")
    else:
        st.dataframe(missing, width="stretch")
    st.markdown(
        "**Outros achados de qualidade** (ver [DATA_QUALITY.md](../docs/DATA_QUALITY.md)):\n"
        "- 5,39% de divergência entre `pessoas` e a soma das categorias de vítimas\n"
        "- 0,48% de registros com `km ≤ 0` (placeholder de 'não informado')\n"
        "- 0,25% de registros com `br = 0` (rodovia não identificada)"
    )

st.divider()
st.markdown(
    """
    ### Navegue pelas páginas (menu à esquerda)
    - **📊 Distribuições** — histogramas, barras e boxplots por variável
    - **🎯 Gravidade** — cruzamentos de gravidade × explicativas
    - **📈 Tendências Temporais** — séries anuais/mensais/diárias
    - **🔄 Sazonalidade** — heatmaps mês×ano, dia×hora
    - **🔗 Correlações e Associações** — Cramér's V, Spearman, contingência
    - **🚨 Anomalias** — outliers, picos, estados/rodovias atípicos
    - **🧠 Features para ML** — disponibilidade, cardinalidade, risco de leakage
    - **🤖 Modelos** — avaliação de modelos treinados (pendente até a etapa de ML)

    Evidência completa: [`docs/EDA.md`](../docs/EDA.md) ·
    [`docs/ANALYSIS_LOG.md`](../docs/ANALYSIS_LOG.md) ·
    [`docs/DECISIONS.md`](../docs/DECISIONS.md)
    """
)
