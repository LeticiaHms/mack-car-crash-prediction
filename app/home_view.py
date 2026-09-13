"""
Conteúdo da página "Visão Geral" (Home) do dashboard.

Fica fora de `pages/` porque não é uma sub-página do menu — é o conteúdo
registrado como página padrão pelo roteador (`app.py`, via `st.navigation`).
Propositalmente enxuta: KPIs + gráfico anual. Qualquer aprofundamento
(schema, nulos, corte de consolidação, distribuição do target) já tem uma
página própria — repetir aqui só adicionava scroll sem informação nova.
"""
import plotly.express as px
import streamlit as st

from common import query, render_sidebar_filters, show_active_filters

st.title("🚧 EDA — Acidentes em Rodovias Federais (PRF, 2022–2026)")
st.caption(
    "Fonte: dados abertos da PRF, 'Acidentes agrupados por ocorrência'. "
    "Unidade de análise: 1 linha = 1 acidente. Este app é uma ferramenta de exploração, "
    "não gera o relatório final automaticamente (skill `streamlit-ml-eda`)."
)

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

st.divider()
st.subheader("Registros por ano")
by_year = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1")
fig = px.bar(by_year, x="ano", y="n", labels={"ano": "Ano", "n": "Acidentes"})
fig.add_annotation(x=2026, y=by_year["n"].max(), text="parcial/não consolidado", showarrow=True, yshift=20)
st.plotly_chart(fig, width="stretch")
st.info(
    "⚠️ 2026 é parcial **e** seus últimos meses estão com registro ainda não consolidado na fonte — "
    "a explicação completa (com evidência e o corte aplicado na camada Silver) está em "
    "**🧹 Qualidade dos Dados**. A comparação defensável entre anos é feita em **📈 Tendências**."
)

st.caption(
    "📖 Não conhece algum termo? [`docs/GLOSSARIO.md`](../docs/GLOSSARIO.md) explica z-score, "
    "qui-quadrado, Cramér's V, intervalo de confiança, data leakage e demais termos usados no menu ao lado."
)
