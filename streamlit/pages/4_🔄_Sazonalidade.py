import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats

from common import query, render_sidebar_filters, show_active_filters

import eda_utils as eu  # noqa: E402

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

st.divider()
st.header("🎉 Feriados: o calendário explica parte da sazonalidade?")
st.caption(
    "Cruzamento com `dados/curated/feriados_nacionais.parquet` (63 feriados nacionais, 2022–2026). "
    "Cada dia da série é classificado em Feriado / Véspera / Pós-feriado / Dia comum — a hipótese "
    "de senso comum é que feriado concentra acidentes graves; abaixo ela é testada, não assumida."
)

TIPO_ORDER = ["Dia comum", "Véspera de feriado", "Feriado", "Pós-feriado"]

diario = query(
    f"""
    SELECT dia, tipo_dia, dia_semana, count(*) n, sum(grave_bin) k
    FROM acidentes_enriquecido WHERE {where}
    GROUP BY 1,2,3
    """
)

if diario.empty or diario["tipo_dia"].nunique() < 2:
    st.warning("Sem dados suficientes para a análise de feriados com os filtros atuais.")
else:
    resumo = (
        diario.groupby("tipo_dia")
        .agg(dias=("dia", "nunique"), acidentes=("n", "sum"), graves=("k", "sum"),
             media_dia=("n", "mean"), mediana_dia=("n", "median"))
        .reindex([t for t in TIPO_ORDER if t in set(diario["tipo_dia"])])
        .reset_index()
    )
    resumo["pct_grave"] = (resumo["graves"] / resumo["acidentes"] * 100).round(2)
    resumo["media_dia"] = resumo["media_dia"].round(1)

    base_mask = diario["tipo_dia"] == "Dia comum"
    base_media = diario[base_mask]["n"].mean()
    resumo["vs dia comum (%)"] = ((resumo["media_dia"] / base_media - 1) * 100).round(1)

    c1, c2 = st.columns([3, 2])
    with c1:
        fig_f = px.bar(resumo, x="tipo_dia", y="media_dia", text="media_dia",
                       color="tipo_dia", category_orders={"tipo_dia": TIPO_ORDER},
                       title="Média de acidentes por dia, segundo o tipo de dia",
                       labels={"media_dia": "acidentes/dia", "tipo_dia": ""})
        fig_f.add_hline(y=base_media, line_dash="dash",
                        annotation_text=f"dia comum: {base_media:.0f}/dia")
        fig_f.update_traces(textposition="outside", showlegend=False)
        st.plotly_chart(fig_f, width="stretch")
    with c2:
        st.dataframe(resumo, width="stretch")

    # Teste formal: volume diário (Mann-Whitney) e taxa de gravidade (z de proporções)
    linhas = []
    comuns = diario[base_mask]["n"].to_numpy(dtype=float)
    k_base = int(diario[base_mask]["k"].sum())
    n_base = int(diario[base_mask]["n"].sum())
    for tipo in [t for t in TIPO_ORDER if t != "Dia comum" and t in set(diario["tipo_dia"])]:
        sub = diario[diario["tipo_dia"] == tipo]
        vals = sub["n"].to_numpy(dtype=float)
        if len(vals) < 5:
            continue
        u, p_u = stats.mannwhitneyu(vals, comuns, alternative="two-sided")
        prop = eu.two_proportion_test(int(sub["k"].sum()), int(sub["n"].sum()), k_base, n_base)
        linhas.append({
            "tipo de dia": tipo,
            "dias": len(vals),
            "volume: dif. da média (%)": round((vals.mean() / comuns.mean() - 1) * 100, 1),
            "volume: p (Mann-Whitney)": p_u,
            "gravidade: dif. (p.p.)": round(prop["diff_pp"], 2),
            "gravidade: IC95 (p.p.)": f"{prop['diff_ci_pp'][0]:+.2f} a {prop['diff_ci_pp'][1]:+.2f}",
            "gravidade: p": prop["p_value"],
        })
    testes = pd.DataFrame(linhas)
    st.markdown("**Cada tipo de dia contra o dia comum — volume e gravidade testados separadamente:**")
    st.dataframe(testes, width="stretch")

    vesp = testes[testes["tipo de dia"] == "Véspera de feriado"]
    if not vesp.empty:
        v = vesp.iloc[0]
        grav_ic = v["gravidade: IC95 (p.p.)"]
        st.info(
            f"""
            **O efeito de feriado é de véspera, e é de volume — não de gravidade.**
            A véspera concentra **{v['volume: dif. da média (%)']:+.1f}%** de acidentes por dia em
            relação a um dia comum (p = {v['volume: p (Mann-Whitney)']:.3g}), enquanto o feriado em si
            fica próximo de um dia comum. Já a *proporção* de acidentes graves na véspera difere em
            apenas {v['gravidade: dif. (p.p.)']:+.2f} p.p. (IC95%: {grav_ic}) — ou seja, o feriado
            **muda quantos acidentes acontecem, não o quão graves eles são**.

            Leitura de negócio: o deslocamento de véspera (saída para o feriado) é o momento de
            exposição, o que aponta fiscalização preventiva na véspera, não no feriado.
            """
        )

    st.markdown("**Ressalva metodológica — feriado não é sorteado no calendário:**")
    wd = (
        diario.assign(is_feriado=diario["tipo_dia"] != "Dia comum")
        .groupby(["dia_semana", "is_feriado"])["n"].mean().reset_index()
    )
    order_wd = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
    wd["dia_semana"] = pd.Categorical(wd["dia_semana"], categories=order_wd, ordered=True)
    fig_wd = px.bar(wd.sort_values("dia_semana"), x="dia_semana", y="n", color="is_feriado",
                    barmode="group", labels={"n": "acidentes/dia", "is_feriado": "dia de feriado?"},
                    title="Média diária por dia da semana, separando dias de calendário comum e de feriado")
    st.plotly_chart(fig_wd, width="stretch")
    st.caption(
        "Feriados caem desproporcionalmente em certos dias da semana, e o dia da semana já tem efeito "
        "próprio sobre volume e gravidade. A comparação acima **não** controla isso — para separar os "
        "dois efeitos, use a página ✂️ Segmentação com `tipo_dia` como segmento e `dia_semana` como "
        "confundidor. É exatamente o caso em que a comparação bruta pode enganar."
    )

    st.divider()
    st.subheader("Quais feriados concentram mais acidentes?")
    por_feriado = query(
        f"""
        SELECT nome_feriado, tipo_dia, count(DISTINCT dia) dias, count(*) n, sum(grave_bin) k
        FROM acidentes_enriquecido
        WHERE {where} AND nome_feriado IS NOT NULL AND tipo_dia = 'Feriado'
        GROUP BY 1,2
        """
    )
    if not por_feriado.empty:
        por_feriado["media_dia"] = (por_feriado["n"] / por_feriado["dias"]).round(1)
        por_feriado["pct_grave"] = (por_feriado["k"] / por_feriado["n"] * 100).round(2)
        por_feriado = por_feriado.sort_values("media_dia", ascending=False)
        fig_pf = px.bar(por_feriado, x="media_dia", y="nome_feriado", orientation="h",
                        color="pct_grave", color_continuous_scale="RdYlBu_r", text="dias",
                        title="Acidentes por dia em cada feriado nacional (cor = % grave/fatal)",
                        labels={"media_dia": "acidentes/dia", "nome_feriado": ""})
        fig_pf.add_vline(x=base_media, line_dash="dash", annotation_text="média do dia comum")
        fig_pf.update_traces(texttemplate="%{text} dias", textposition="outside")
        fig_pf.update_layout(height=520, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_pf, width="stretch")
        st.dataframe(por_feriado[["nome_feriado", "dias", "n", "media_dia", "pct_grave"]], width="stretch")
        st.caption(
            "Cada feriado aparece 4–5 vezes na série (uma por ano), então `dias` é pequeno e a média "
            "de um feriado específico é uma estimativa **frágil** — trate como indício, não conclusão. "
            "É a mesma cautela aplicada aos picos diários em 🚨 Anomalias."
        )
