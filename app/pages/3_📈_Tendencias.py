import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import consolidation_info, query, render_sidebar_filters, show_active_filters

st.title("📈 Tendências Temporais")

where, selections = render_sidebar_filters()
show_active_filters(selections)

tab_anual, tab_serie = st.tabs(["Visão Anual & Viés", "Série Histórica"])

# ---------------------------------------------------------------------------
with tab_anual:
    st.subheader("Volume de acidentes por ano")
    by_year = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1 ORDER BY 1")
    fig = px.line(by_year, x="ano", y="n", markers=True)
    st.plotly_chart(fig, width="stretch")

    info = consolidation_info()
    cutoff = pd.Timestamp(info["cutoff_date"])
    doy = int(cutoff.dayofyear)

    st.error(
        f"""
        ⚠️ **Recortar jan–jul não basta — e o gráfico acima ainda engana.** A página 🧹 Qualidade dos Dados
        mostra que os últimos {info['days_flagged']} dias da série (após **{info['cutoff_date']}**) estão
        com registro ainda não consolidado na fonte: junho e julho de 2026 aparecem quase vazios.
        Como esses meses entram no recorte "jan–jul", a queda de 2026 exibida acima é em grande parte um
        **artefato de coleta**, não uma redução de acidentes.
        """
    )

    jan_jul = query(f"SELECT ano, count(*) n FROM acidentes_enriquecido WHERE {where} AND mes<=7 GROUP BY 1 ORDER BY 1")
    consolidado = query(
        f"""
        SELECT ano, count(*) n, sum(grave_bin) n_grave,
               round(100.0*sum(grave_bin)/count(*), 2) pct_grave
        FROM acidentes_enriquecido
        WHERE {where} AND dayofyear(data_inversa) <= {doy}
        GROUP BY 1 ORDER BY 1
        """
    )
    if len(consolidado) > 1:
        consolidado["variação vs ano anterior (%)"] = (consolidado["n"].pct_change() * 100).round(1)

    c1, c2 = st.columns(2)
    with c1:
        fig_jj = px.bar(jan_jul, x="ano", y="n", title="Acidentes, jan–jul de cada ano (bruto, com viés)")
        st.plotly_chart(fig_jj, width="stretch")
    with c2:
        comp = jan_jul.rename(columns={"n": "jan–jul (bruto)"}).merge(
            consolidado[["ano", "n"]].rename(columns={"n": f"janela consolidada (até dia {doy})"}), on="ano", how="outer"
        )
        fig_cmp = px.bar(
            comp.melt(id_vars="ano", var_name="janela", value_name="acidentes"),
            x="ano", y="acidentes", color="janela", barmode="group",
            title="Bruto vs. janela consolidada — a escolha muda a conclusão",
        )
        st.plotly_chart(fig_cmp, width="stretch")

    st.markdown(f"**Comparação com janela efetivamente consolidada** (1º de janeiro até o dia {doy} de cada ano):")
    st.dataframe(consolidado, width="stretch")

    if len(consolidado) > 1 and 2026 in set(consolidado["ano"]):
        ult = consolidado[consolidado["ano"] == 2026].iloc[0]
        var_ultimo = ult.get("variação vs ano anterior (%)")
        if pd.notna(var_ultimo):
            direcao = "alta" if var_ultimo > 0 else "queda"
            st.success(
                f"""
                **Conclusão corrigida.** Comparando apenas o período consolidado, 2026 registra
                **{var_ultimo:+.1f}%** em relação ao mesmo intervalo de 2025 — uma {direcao} de magnitude
                ordinária, e não a queda abrupta que o total bruto sugeria. A gravidade relativa segue
                no mesmo patamar ({ult['pct_grave']:.2f}%), reforçando o achado A-09: o que oscila
                entre anos é o **volume**, não a proporção de acidentes graves.
                """
            )

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
    with st.expander("Ver tabela e detalhes"):
        st.dataframe(grave_year, width="stretch")
        st.caption(
            "A % de gravidade tende a ficar estável entre anos completos, mesmo quando o volume total "
            "muda (achado A-09 em docs/analises/ANALYSIS_LOG.md) — evite concluir 'piora' ou 'melhora' de "
            "segurança só pelo volume bruto."
        )

# ---------------------------------------------------------------------------
with tab_serie:
    st.subheader("Volume normalizado por dia (remove o efeito do tamanho do mês)")
    por_mes = query(
        f"""
        SELECT ano, mes, count(*) n, count(DISTINCT dia) dias_com_registro
        FROM acidentes_enriquecido WHERE {where} GROUP BY 1,2 ORDER BY 1,2
        """
    )
    if not por_mes.empty:
        por_mes["acidentes_por_dia"] = (por_mes["n"] / por_mes["dias_com_registro"]).round(1)
        por_mes["periodo"] = por_mes["ano"].astype(str) + "-" + por_mes["mes"].astype(str).str.zfill(2)
        fig_norm = px.line(por_mes, x="periodo", y="acidentes_por_dia", markers=True,
                           title="Acidentes por dia registrado, mês a mês")
        st.plotly_chart(fig_norm, width="stretch")
        st.caption(
            "Fevereiro tem 28 dias e dezembro 31: comparar totais mensais brutos embute uma diferença de "
            "~10% que não tem nada a ver com segurança viária. A média diária elimina esse artefato — "
            "e deixa o colapso final da série (não consolidação) ainda mais evidente."
        )

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
    st.caption(
        "O padrão semanal e horário (dia da semana × hora do dia) tem página própria — ver 🔄 Sazonalidade."
    )
