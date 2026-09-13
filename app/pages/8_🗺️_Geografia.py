"""Dimensão espacial: onde os acidentes acontecem e onde eles são mais graves.

`latitude`/`longitude`/`km` são as únicas colunas que localizam o evento no espaço contínuo.
Elas respondem a uma pergunta que nenhum agregado por UF responde: o risco se concentra em
*trechos*, não em estados inteiros — e é o trecho que a etapa de ML precisará como unidade.

Regra aplicada em toda a página: **contagem ≠ risco**. Onde há mais tráfego há mais acidentes;
por isso os rankings usam a *taxa* de gravidade com intervalo de confiança, e não o total.
"""
import plotly.express as px
import streamlit as st

from common import query, render_sidebar_filters, show_active_filters

from src.eda import utils as eu  # noqa: E402

st.title("🗺️ Distribuição Geográfica e Trechos Críticos")

where, selections = render_sidebar_filters()
show_active_filters(selections)

tab_mapa, tab_uf, tab_trechos = st.tabs(["Onde acontecem", "Risco por UF / rodovia", "Trechos críticos (BR × km)"])

# ---------------------------------------------------------------------------
with tab_mapa:
    st.subheader("Densidade espacial dos acidentes")
    ctrl1, ctrl2 = st.columns(2)
    with ctrl1:
        modo = st.radio("Visualização", ["Densidade (sem mapa base)", "Pontos sobre mapa base"],
                        horizontal=True)
    with ctrl2:
        color_by = st.selectbox("Colorir/agregar por", ["volume de acidentes", "% grave ou fatal"])

    if modo.startswith("Densidade"):
        pts = query(
            f"SELECT longitude, latitude, grave_bin FROM acidentes_enriquecido "
            f"WHERE {where} AND latitude BETWEEN -34 AND 6 AND longitude BETWEEN -75 AND -32"
        )
        if pts.empty:
            st.warning("Sem dados para os filtros atuais.")
        else:
            if color_by == "volume de acidentes":
                fig = px.density_heatmap(
                    pts, x="longitude", y="latitude", nbinsx=140, nbinsy=140,
                    color_continuous_scale="Inferno",
                    title=f"Concentração de acidentes ({len(pts):,} registros)".replace(",", "."),
                )
            else:
                fig = px.density_heatmap(
                    pts, x="longitude", y="latitude", z="grave_bin", histfunc="avg",
                    nbinsx=90, nbinsy=90, color_continuous_scale="RdYlBu_r",
                    title="Proporção de acidentes graves/fatais por célula",
                )
            fig.update_layout(height=620, yaxis_scaleanchor="x")  # evita distorcer o formato do país
            st.plotly_chart(fig, width="stretch")
            st.info(
                "💡 O desenho que emerge é a **malha das rodovias federais**, não a população: os pontos "
                "só existem onde há BR. Células vermelhas no mapa de gravidade tendem a ser trechos "
                "de baixa densidade (poucos acidentes, taxa instável) — confirme o `n` na aba de trechos."
            )
    else:
        n_max = st.slider("Amostra de pontos (o mapa base fica lento com muitos)", 2000, 40000, 12000, step=2000)
        pts = query(
            f"SELECT latitude, longitude, uf, br, km, municipio, gravidade_4, grave_bin "
            f"FROM acidentes_enriquecido WHERE {where} "
            f"AND latitude BETWEEN -34 AND 6 AND longitude BETWEEN -75 AND -32 "
            f"USING SAMPLE {n_max} ROWS"
        )
        if pts.empty:
            st.warning("Sem dados para os filtros atuais.")
        else:
            fig = px.scatter_map(
                pts, lat="latitude", lon="longitude",
                color="gravidade_4" if color_by != "volume de acidentes" else None,
                color_discrete_map={"Fatal": "#c0392b", "Grave (não fatal)": "#e67e22",
                                    "Leve": "#f1c40f", "Sem vítimas": "#7f8c8d"},
                category_orders={"gravidade_4": ["Fatal", "Grave (não fatal)", "Leve", "Sem vítimas"]},
                hover_data=["uf", "br", "km", "municipio"], zoom=3.2, opacity=0.45,
                map_style="open-street-map", height=620,
            )
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width="stretch")
            st.caption(
                f"Amostra aleatória de {len(pts):,} acidentes (`USING SAMPLE`) — plotar as centenas de "
                "milhares de pontos travaria o navegador e viraria uma mancha ilegível. "
                "O mapa base precisa de conexão com a internet.".replace(",", ".")
            )

# ---------------------------------------------------------------------------
with tab_uf:
    st.subheader("Taxa de gravidade por unidade geográfica")
    dim = st.radio("Agregar por", ["uf", "br", "municipio"], horizontal=True, key="geo_dim")
    min_n = st.slider("n mínimo do grupo", 50, 3000, 300, step=50, key="geo_min_n")
    extra = " AND br <> 0" if dim == "br" else ""

    rate = query(
        f"""
        SELECT {dim} AS grupo, count(*) n, sum(grave_bin) k,
               round(100.0*sum(grave_bin)/count(*), 2) pct_grave,
               sum(mortos) mortos
        FROM acidentes_enriquecido
        WHERE {where} AND {dim} IS NOT NULL {extra}
        GROUP BY 1 HAVING count(*) >= {min_n}
        """
    )
    if rate.empty:
        st.warning("Nenhum grupo atinge o n mínimo com os filtros atuais.")
    else:
        ci = rate.apply(lambda r: eu.wilson_ci(int(r["k"]), int(r["n"])), axis=1, result_type="expand")
        rate["ic_low"] = (ci[0] * 100).round(2)
        rate["ic_high"] = (ci[1] * 100).round(2)
        rate["grupo"] = rate["grupo"].astype(str)
        media_geral = query(
            f"SELECT round(100.0*sum(grave_bin)/count(*),2) p FROM acidentes_enriquecido WHERE {where}"
        ).iloc[0]["p"]

        top = rate.sort_values("pct_grave", ascending=False).head(25)
        fig = px.scatter(
            top, x="pct_grave", y="grupo", error_x=top["ic_high"] - top["pct_grave"],
            error_x_minus=top["pct_grave"] - top["ic_low"], size="n", color="pct_grave",
            color_continuous_scale="RdYlBu_r",
            title=f"Top 25 por % grave/fatal ({dim}, n ≥ {min_n}) — com IC 95%",
            labels={"pct_grave": "% grave ou fatal", "grupo": dim},
        )
        fig.add_vline(x=media_geral, line_dash="dash", annotation_text=f"média geral {media_geral:.1f}%")
        fig.update_layout(height=680, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")
        st.dataframe(
            rate.sort_values("pct_grave", ascending=False)[
                ["grupo", "n", "k", "pct_grave", "ic_low", "ic_high", "mortos"]],
            width="stretch", height=320,
        )
        acima = int((rate["ic_low"] > media_geral).sum())
        st.info(
            f"**{acima} de {len(rate)} grupos** têm o intervalo de confiança inteiro acima da média geral "
            f"({media_geral:.1f}%) — só esses podem ser chamados de 'acima da média' sem ressalva. "
            "As barras largas são grupos com poucos acidentes: a posição no ranking deles é instável e "
            "pode mudar completamente com um único evento a mais."
        )
        if dim == "br":
            st.caption("`br = 0` foi excluído: é um placeholder de rodovia não identificada ([D-05](../docs/decisoes/DECISIONS.md)).")

# ---------------------------------------------------------------------------
with tab_trechos:
    st.subheader("Segmentação da rodovia em trechos")
    st.caption(
        "Agrupa os acidentes por faixa de quilometragem de cada BR dentro de cada UF. É a unidade "
        "espacial que a etapa de feature engineering vai usar — mais informativa que a UF inteira "
        "e estável no tempo (o trecho não muda de lugar)."
    )
    bin_km = st.select_slider("Tamanho do trecho (km)", options=[5, 10, 20, 50], value=10)
    min_n_t = st.slider("n mínimo do trecho", 20, 500, 60, step=10, key="trecho_min_n")

    trechos = query(
        f"""
        SELECT uf, br, floor(km / {bin_km}) * {bin_km} AS km_inicio,
               count(*) n, sum(grave_bin) k, sum(mortos) mortos,
               round(100.0*sum(grave_bin)/count(*), 2) pct_grave
        FROM acidentes_enriquecido
        WHERE {where} AND br <> 0 AND km > 0
        GROUP BY 1,2,3 HAVING count(*) >= {min_n_t}
        """
    )
    if trechos.empty:
        st.warning("Nenhum trecho atinge o n mínimo com os filtros atuais.")
    else:
        ci = trechos.apply(lambda r: eu.wilson_ci(int(r["k"]), int(r["n"])), axis=1, result_type="expand")
        trechos["ic_low"] = (ci[0] * 100).round(2)
        trechos["ic_high"] = (ci[1] * 100).round(2)
        trechos["trecho"] = (trechos["br"].astype(int).astype(str).str.zfill(3) + "/" + trechos["uf"]
                             + " km " + trechos["km_inicio"].astype(int).astype(str)
                             + "–" + (trechos["km_inicio"] + bin_km).astype(int).astype(str))
        media_geral = query(
            f"SELECT round(100.0*sum(grave_bin)/count(*),2) p FROM acidentes_enriquecido WHERE {where} AND br <> 0 AND km > 0"
        ).iloc[0]["p"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Trechos analisados", f"{len(trechos):,}".replace(",", "."))
        c2.metric("Acidentes cobertos", f"{int(trechos['n'].sum()):,}".replace(",", "."))
        c3.metric("Trechos com IC acima da média", int((trechos["ic_low"] > media_geral).sum()))

        top = trechos.sort_values(["pct_grave", "n"], ascending=[False, False]).head(20)
        fig = px.bar(top, x="pct_grave", y="trecho", orientation="h", text="n",
                     error_x=top["ic_high"] - top["pct_grave"],
                     error_x_minus=top["pct_grave"] - top["ic_low"],
                     color="mortos", color_continuous_scale="Reds",
                     title=f"20 trechos de {bin_km} km com maior % grave/fatal (n ≥ {min_n_t})")
        fig.update_traces(texttemplate="n=%{text}", textposition="outside")
        fig.add_vline(x=media_geral, line_dash="dash", annotation_text=f"média {media_geral:.1f}%")
        fig.update_layout(height=640, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

        st.markdown("**Trechos por volume absoluto** (exposição, não necessariamente risco):")
        st.dataframe(
            trechos.sort_values("n", ascending=False)[
                ["trecho", "n", "k", "pct_grave", "ic_low", "ic_high", "mortos"]].head(25),
            width="stretch", height=500,
        )
        st.warning(
            "**Os dois rankings quase não se sobrepõem** — os trechos com mais acidentes (áreas urbanas, "
            "muito tráfego) não são os de maior proporção de acidentes graves (trechos de velocidade alta "
            "e menor fluxo). Priorizar fiscalização por volume bruto e por taxa de gravidade leva a "
            "listas diferentes; a base não tem contagem de tráfego para calcular risco *por viagem*, "
            "que seria a métrica ideal (limitação registrada em docs/analises/EDA.md §9)."
        )
