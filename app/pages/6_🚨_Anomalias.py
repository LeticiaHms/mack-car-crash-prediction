import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import query, render_sidebar_filters, show_active_filters

st.title("🚨 Investigação de Anomalias")
with st.expander("ℹ️ Metodologia — como uma anomalia é classificada aqui"):
    st.markdown(
        "Nenhuma anomalia é removida automaticamente. Cada uma é classificada como: "
        "evento real plausível, problema de qualidade de dados, ou inconclusivo (skill `eda`, seção 8)."
    )

where, selections = render_sidebar_filters()
show_active_filters(selections)

tab1, tab2, tab3 = st.tabs(["Série diária (picos)", "Outliers numéricos", "Grupos atípicos (UF/BR)"])

with tab1:
    daily = query(
        f"SELECT data_inversa::DATE AS dia, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1"
    )
    if daily.empty:
        st.warning("Sem dados.")
    else:
        q1, q3 = daily["n"].quantile([0.25, 0.75])
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        lower = max(0, q1 - 1.5 * iqr)
        spikes = daily[daily["n"] > upper].sort_values("n", ascending=False)

        st.metric("Limite superior (IQR)", f"{upper:.1f} acidentes/dia")
        st.metric("Dias acima do limite", f"{len(spikes)} ({len(spikes)/len(daily)*100:.2f}%)")

        fig = go.Figure()
        fig.add_scatter(x=daily["dia"], y=daily["n"], mode="lines", name="Acidentes/dia", opacity=0.5)
        fig.add_scatter(x=spikes["dia"], y=spikes["n"], mode="markers", name="Picos (> limite IQR)",
                         marker=dict(color="red", size=7))
        fig.add_hline(y=upper, line_dash="dash", line_color="red", annotation_text="limite superior IQR")
        st.plotly_chart(fig, width="stretch")

        st.info(
            "5 dos 8 maiores picos caem entre 12–23 de dezembro, em 3 anos diferentes — "
            "recorrência que sustenta classificá-los como **evento sazonal real** de fim de ano, "
            "não ruído (achado A-14). O pico de 2024-10-20 não recorre em outros anos → **inconclusivo**."
        )
        st.markdown("**Top 15 dias com mais acidentes:**")
        st.dataframe(spikes.head(15), width="stretch")

with tab2:
    col = st.selectbox(
        "Coluna numérica",
        ["mortos", "feridos_graves", "feridos_leves", "pessoas", "veiculos", "ilesos", "ignorados", "km"],
    )
    method = st.radio("Método", ["Z-score (|z|>3)", "IQR (1.5×)"], horizontal=True)
    data = query(f"SELECT {col} AS v FROM acidentes_enriquecido WHERE {where} AND {col} IS NOT NULL")["v"].astype(float)

    if method.startswith("IQR"):
        q1, q3 = data.quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (data < lo) | (data > hi)
        st.write(f"Limites IQR: [{lo:.2f}, {hi:.2f}]")
        if lo == hi:
            st.warning(
                "Q1 = Q3 nesta coluna (muitos zeros) — o IQR degenera e sinaliza qualquer valor > 0 "
                "como outlier. Prefira Z-score para colunas de contagem rara (ver docs/decisoes/DECISIONS.md D-06)."
            )
    else:
        z = (data - data.mean()) / data.std(ddof=0)
        mask = z.abs() > 3

    st.metric("Outliers detectados", f"{int(mask.sum())} ({mask.mean()*100:.2f}%)")
    fig = px.histogram(data, nbins=40, title=f"Distribuição de {col} (outliers em vermelho)")
    st.plotly_chart(fig, width="stretch")

    if mask.sum() > 0:
        cols = "id,data_inversa,uf,br,km,municipio,tipo_acidente,causa_acidente,pessoas,mortos,feridos_leves,feridos_graves,veiculos"
        top_records = query(
            f"SELECT {cols} FROM acidentes_enriquecido WHERE {where} AND {col} IS NOT NULL "
            f"ORDER BY {col} DESC LIMIT 10"
        )
        st.markdown("**Registros mais extremos (inspeção manual de plausibilidade):**")
        st.dataframe(top_records, width="stretch")

with tab3:
    dim = st.radio("Dimensão", ["uf", "br"], horizontal=True)
    min_n = st.slider("Tamanho mínimo do grupo", 50, 2000, 200, key="anom_min_n")
    rate = query(
        f"""
        SELECT {dim} AS grupo, count(*) n, sum(grave_bin) n_grave,
               round(100.0*sum(grave_bin)/count(*),2) pct_grave
        FROM acidentes_enriquecido WHERE {where} GROUP BY 1
        """
    )
    rate = rate[rate["n"] >= min_n].copy()
    if len(rate) < 2:
        st.warning("Poucos grupos após o filtro de tamanho mínimo.")
    else:
        rate["z"] = (rate["pct_grave"] - rate["pct_grave"].mean()) / rate["pct_grave"].std(ddof=0)
        outliers = rate[rate["z"].abs() > 2].sort_values("z")
        fig = px.scatter(rate, x="n", y="pct_grave", hover_name="grupo",
                          color=(rate["z"].abs() > 2).map({True: "Atípico (|z|>2)", False: "Dentro do esperado"}),
                          title=f"% grave/fatal por {dim} (tamanho do grupo no eixo X)")
        st.plotly_chart(fig, width="stretch")
        st.markdown(f"**Grupos atípicos (|z|>2, n≥{min_n}):**")
        st.dataframe(outliers, width="stretch")
        if dim == "br":
            st.caption(
                "`br=0` não é uma rodovia real (placeholder) — excluído de conclusões de risco por rodovia "
                "(docs/decisoes/DECISIONS.md D-05). Rodovias com n pequeno merecem cautela (intervalo de confiança largo)."
            )
