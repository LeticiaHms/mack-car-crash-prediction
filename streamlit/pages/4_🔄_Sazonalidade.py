import numpy as np
import plotly.express as px
import streamlit as st

from common import query, render_sidebar_filters, show_active_filters

st.set_page_config(page_title="Sazonalidade", page_icon="🔄", layout="wide")
st.title("🔄 Sazonalidade")
st.caption(
    "Um gráfico oscilar não basta para chamar de sazonal — aqui exigimos evidência de recorrência "
    "entre anos diferentes antes de rotular um padrão como sazonalidade (skill `eda`, seção 7)."
)

where, selections = render_sidebar_filters()
show_active_filters(selections)

st.subheader("Heatmap Mês × Ano (volume)")
my = query(f"SELECT ano, mes, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1,2")
if my.empty:
    st.warning("Sem dados para os filtros selecionados.")
else:
    pivot = my.pivot(index="mes", columns="ano", values="n").reindex(range(1, 13))
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="Oranges",
                     labels=dict(x="Ano", y="Mês", color="Acidentes"))
    st.plotly_chart(fig, width="stretch")

    complete_years = [y for y in pivot.columns if my[my["ano"] == y]["mes"].nunique() == 12]
    if len(complete_years) >= 2:
        corr = pivot[complete_years].corr(method="spearman")
        tri = corr.to_numpy()[np.triu_indices(len(complete_years), k=1)]
        st.metric("Recorrência do padrão mensal entre anos completos (Spearman médio)", f"{np.nanmean(tri):.3f}")
        st.caption(
            f"Anos completos comparados: {complete_years}. Valor próximo de 1 = o mesmo mês tende a ranquear "
            "igual (alto/baixo) em anos diferentes → evidência de sazonalidade real de volume."
        )
        st.dataframe(corr.round(3), width="stretch")
    else:
        st.info("São necessários pelo menos 2 anos completos (12 meses) para testar recorrência.")

st.divider()
st.subheader("Mês × Gravidade")
mg = query(
    f"SELECT mes, count(*) n, round(100.0*sum(grave_bin)/count(*),2) pct_grave "
    f"FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1"
)
fig2 = px.bar(mg, x="mes", y="n", title="Volume por mês (todos os anos agregados)")
st.plotly_chart(fig2, width="stretch")
fig3 = px.line(mg, x="mes", y="pct_grave", markers=True, title="% grave/fatal por mês")
fig3.update_yaxes(range=[0, max(35, mg["pct_grave"].max() + 5)])
st.plotly_chart(fig3, width="stretch")
st.caption(
    "A associação entre `mes` e gravidade é praticamente nula (Cramér's V≈0,008 — ver 🔗 Correlações): "
    "a sazonalidade observada é de **volume**, não de risco relativo de gravidade."
)

st.divider()
st.subheader("Heatmap Dia da Semana × Hora")
wh = query(f"SELECT dia_semana, hora, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1,2")
order = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
if not wh.empty:
    pivot2 = wh.pivot(index="dia_semana", columns="hora", values="n").reindex(order)
    fig4 = px.imshow(pivot2, aspect="auto", color_continuous_scale="Blues",
                      labels=dict(x="Hora", y="Dia da semana", color="Acidentes"))
    st.plotly_chart(fig4, width="stretch")

st.divider()
st.subheader("Hora × Gravidade")
hg = query(
    f"SELECT hora, count(*) n, round(100.0*sum(grave_bin)/count(*),2) pct_grave "
    f"FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1"
)
fig5 = px.line(hg, x="hora", y="pct_grave", markers=True, title="% grave/fatal por hora do dia")
st.plotly_chart(fig5, width="stretch")
st.caption("Pico de volume ~18h, mas pico de gravidade relativa à noite (19h–23h) — achado A-11.")
