import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import query, render_sidebar_filters, show_active_filters

st.set_page_config(page_title="Tendências Temporais", page_icon="📈", layout="wide")
st.title("📈 Tendências Temporais")

where, selections = render_sidebar_filters()
show_active_filters(selections)

st.subheader("Volume de acidentes por ano")
by_year = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1")
fig = px.line(by_year, x="ano", y="n", markers=True)
st.plotly_chart(fig, width="stretch")

st.markdown("**Comparação justa jan–jul** (2026 só tem dados até julho — ver docs/DECISIONS.md D-12):")
jan_jul = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} AND mes<=7 GROUP BY 1 ORDER BY 1")
fig_jj = px.bar(jan_jul, x="ano", y="n", title="Acidentes, jan–jul de cada ano")
st.plotly_chart(fig_jj, width="stretch")

st.divider()
st.subheader("A proporção de acidentes graves mudou ao longo do tempo?")
grave_year = query(
    f"SELECT ano, count(*) n, sum(grave_bin) n_grave, round(100.0*sum(grave_bin)/count(*),2) pct_grave "
    f"FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1"
)
fig2 = go.Figure()
fig2.add_bar(x=grave_year["ano"], y=grave_year["n"], name="Total de acidentes", opacity=0.4)
fig2.add_scatter(x=grave_year["ano"], y=grave_year["pct_grave"], name="% grave/fatal",
                  yaxis="y2", mode="lines+markers", line=dict(color="crimson"))
fig2.update_layout(
    yaxis=dict(title="Total de acidentes"),
    yaxis2=dict(title="% grave/fatal", overlaying="y", side="right", range=[0, 50]),
    title="Volume vs. % de gravidade por ano",
)
st.plotly_chart(fig2, width="stretch")
st.dataframe(grave_year, width="stretch")
st.caption(
    "A % de gravidade tende a ficar estável entre anos completos, mesmo quando o volume total muda "
    "(achado A-09 em docs/ANALYSIS_LOG.md) — evite concluir 'piora' ou 'melhora' de segurança só pelo volume bruto."
)

st.divider()
st.subheader("Padrão semanal e diário")
c1, c2 = st.columns(2)
with c1:
    wd = query(f"SELECT dia_semana, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1")
    order = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
    wd["dia_semana"] = wd["dia_semana"].astype("category").cat.set_categories(order)
    wd = wd.sort_values("dia_semana")
    st.plotly_chart(px.bar(wd, x="dia_semana", y="n", title="Acidentes por dia da semana"), width="stretch")
with c2:
    hr = query(f"SELECT hora, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1")
    st.plotly_chart(px.line(hr, x="hora", y="n", markers=True, title="Acidentes por hora do dia"), width="stretch")

st.divider()
st.subheader("Série diária com média móvel de 7 dias")
daily = query(
    f"SELECT data_inversa::DATE AS dia, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1"
)
daily["media_movel_7d"] = daily["n"].rolling(7, min_periods=1).mean()
fig3 = go.Figure()
fig3.add_scatter(x=daily["dia"], y=daily["n"], mode="lines", name="Diário", opacity=0.35)
fig3.add_scatter(x=daily["dia"], y=daily["media_movel_7d"], mode="lines", name="Média móvel 7d", line=dict(width=2))
st.plotly_chart(fig3, width="stretch")
