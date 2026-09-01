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

from common import consolidation_info, get_connection, query, render_sidebar_filters, show_active_filters

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

overview = query("SELECT count(*) n, min(data_inversa)::DATE mn, max(data_inversa)::DATE mx FROM acidentes")
filtered_overview = query(f"SELECT count(*) n FROM acidentes_enriquecido WHERE {where}")
n_total = int(overview.iloc[0]["n"])
n_filtered = int(filtered_overview.iloc[0]["n"])
n_cols = len(query("DESCRIBE SELECT * FROM acidentes"))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros (total)", f"{n_total:,}".replace(",", "."))
c2.metric("Registros (filtro atual)", f"{n_filtered:,}".replace(",", "."))
c3.metric("Período", f"{overview.iloc[0]['mn']} a {overview.iloc[0]['mx']}")
c4.metric("Colunas", n_cols)

_info = consolidation_info()
st.warning(
    f"⚠️ **Leia antes de interpretar qualquer tendência:** os últimos {_info['days_flagged']} dias da "
    f"série (após **{_info['cutoff_date']}**) contêm apenas {_info['rows_flagged']} registros, contra uma "
    f"mediana histórica de {_info['reference_daily_median']:.0f} acidentes/dia — é registro ainda não "
    "consolidado na fonte, não redução de acidentes. Use o filtro *Excluir janela não consolidada* na "
    "sidebar. Diagnóstico completo em **🧹 Qualidade dos Dados**."
)

st.divider()

col_a, col_b = st.columns([2, 1])

with col_a:
    st.subheader("Registros por ano")
    by_year = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1")
    fig = px.bar(by_year, x="ano", y="n", labels={"ano": "Ano", "n": "Acidentes"})
    fig.add_annotation(x=2026, y=by_year["n"].max(), text="parcial (jan–jul)", showarrow=True, yshift=20)
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "⚠️ 2026 é parcial **e** seus últimos meses estão sub-registrados. Recortar jan–jul (D-12) "
        "não basta: a comparação defensável usa a janela consolidada, calculada na página "
        "📈 Tendências Temporais."
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
    st.markdown(f"**Tipos de dados ({n_cols} colunas)**")
    st.dataframe(cols[["column_name", "column_type"]], width="stretch", height=300)
with t2:
    st.markdown("**Colunas com valores nulos**")
    if missing.empty:
        st.success("Nenhuma coluna com nulos.")
    else:
        st.dataframe(missing, width="stretch")
    st.markdown(
        "**Ausência de nulo não é sinal de qualidade.** Os problemas reais desta base são "
        "valores-sentinela (`km = 0`, `br = 0`, `Ignorado`), divergência interna entre `pessoas` e a "
        "soma das vítimas, e dias inteiros faltando no calendário — nada disso aparece como `NULL`. "
        "Diagnóstico completo e quantificado na página **🧹 Qualidade dos Dados** "
        "(e em [DATA_QUALITY.md](../docs/DATA_QUALITY.md))."
    )

st.divider()
st.markdown(
    """
    ### Navegue pelas páginas (menu à esquerda)

    **Entender a base**
    - **🧹 Qualidade dos Dados** — nulos, sentinelas, coerência interna e cobertura temporal
    - **📊 Distribuições** — histogramas, barras e boxplots por variável
    - **🎯 Gravidade** — cruzamentos de gravidade × explicativas

    **Encontrar padrões**
    - **📈 Tendências Temporais** — séries anuais/mensais/diárias e a correção da janela consolidada
    - **🔄 Sazonalidade** — heatmaps mês×ano, dia×hora e o efeito de feriados/vésperas
    - **🔗 Correlações e Associações** — Cramér's V, Spearman, contingência
    - **🚨 Anomalias** — outliers, picos, estados/rodovias atípicos
    - **✂️ Segmentação** — compara dois recortes e testa se a diferença sobrevive ao confundidor
    - **🗺️ Geografia** — densidade espacial, risco por UF/rodovia e trechos críticos

    **Concluir com responsabilidade**
    - **🧪 Validação Estatística** — teste + intervalo de confiança + tamanho de efeito
    - **💡 Insights e Hipóteses** — síntese dos achados, o que fica como hipótese e o checklist da etapa
    - **🧠 Features para ML** — disponibilidade, cardinalidade, risco de leakage
    - **🤖 Modelos** — avaliação de modelos treinados (pendente até a etapa de ML)

    📖 **Não conhece algum termo?** [`docs/GLOSSARIO.md`](../docs/GLOSSARIO.md) explica z-score,
    qui-quadrado, Cramér's V, intervalo de confiança, data leakage e todos os demais, com exemplos
    tirados desta própria base.

    Evidência completa: [`docs/specs/eda/EDA.md`](../docs/specs/eda/EDA.md) ·
    [`docs/ANALYSIS_LOG.md`](../docs/ANALYSIS_LOG.md) ·
    [`docs/DECISIONS.md`](../docs/DECISIONS.md)
    """
)
