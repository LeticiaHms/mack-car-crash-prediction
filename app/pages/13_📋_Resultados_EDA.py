"""
Resumo executivo da Etapa 2 (EDA) — visão geral rápida dos achados mais
fortes, para quem quer o essencial sem navegar pelas páginas de
aprofundamento. Todo número aqui é recalculado ao vivo do banco (nada
digitado à mão); a página não repete o detalhamento estatístico completo
(IC, tamanho de efeito, todas as hipóteses) — isso mora em 💡 Insights e
Hipóteses e nas páginas de análise exploratória, propositalmente mantidas
intactas para quem quer se aprofundar.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from common import query

from src.eda import utils as eu  # noqa: E402

st.title("📋 Resultados — Análise Exploratória (Etapa 2)")
st.caption(
    "Panorama dos achados mais fortes da EDA sobre acidentes em rodovias federais (PRF, 2022–2026). "
    "Para o detalhamento completo — evidência estatística, hipóteses refutáveis e checklist da "
    "disciplina — ver 💡 Insights e Hipóteses e [`docs/entregas/etapa2-eda.md`](../docs/entregas/etapa2-eda.md)."
)

total = int(query("SELECT count(*) n FROM acidentes").iloc[0]["n"])
# `acidentes_enriquecido` já é a Silver (D-13): sempre recortada no período consolidado.
alvo = query("SELECT round(100.0*avg(grave_bin),2) pct_grave FROM acidentes_enriquecido").iloc[0]
anos = query("SELECT ano, round(100.0*avg(grave_bin),2) pct_grave FROM acidentes_enriquecido GROUP BY 1 ORDER BY 1")

pista = query(
    "SELECT tipo_pista, count(*) n, sum(grave_bin) k FROM acidentes_enriquecido "
    "WHERE tipo_pista IN ('Simples','Dupla') GROUP BY 1"
).set_index("tipo_pista")
t_pista = eu.two_proportion_test(int(pista.loc["Simples", "k"]), int(pista.loc["Simples", "n"]),
                                 int(pista.loc["Dupla", "k"]), int(pista.loc["Dupla", "n"]))

fase = query(
    "SELECT fase_dia, count(*) n, sum(grave_bin) k FROM acidentes_enriquecido GROUP BY 1"
).set_index("fase_dia")
t_fase = eu.two_proportion_test(int(fase.loc["Plena Noite", "k"]), int(fase.loc["Plena Noite", "n"]),
                                int(fase.loc["Pleno dia", "k"]), int(fase.loc["Pleno dia", "n"]))

# --- KPIs ---------------------------------------------------------------
m = st.columns(4)
m[0].metric("Acidentes analisados", f"{total:,}".replace(",", "."))
m[1].metric("% grave ou fatal", f"{alvo['pct_grave']:.1f}%")
m[2].metric("Estabilidade entre anos", f"{anos['pct_grave'].min():.1f}–{anos['pct_grave'].max():.1f}%",
            help="A % de acidentes graves não sai dessa faixa em nenhum dos anos consolidados.")
m[3].metric("Período coberto", f"{anos['ano'].min()}–{anos['ano'].max()}")

st.divider()

# --- 1. Volume x Gravidade ------------------------------------------------
st.header("1. Volume oscila, gravidade não")
c1, c2 = st.columns([2, 1])
with c1:
    fig = px.line(anos, x="ano", y="pct_grave", markers=True, labels={"ano": "Ano", "pct_grave": "% grave/fatal"})
    fig.update_yaxes(range=[0, max(35, anos["pct_grave"].max() + 5)])
    st.plotly_chart(fig, width="stretch")
with c2:
    st.markdown(
        f"A proporção de acidentes graves fica sempre entre **{anos['pct_grave'].min():.1f}%** e "
        f"**{anos['pct_grave'].max():.1f}%**, ano após ano — uma amplitude de apenas "
        f"{anos['pct_grave'].max() - anos['pct_grave'].min():.1f} pontos percentuais, enquanto o "
        "*volume* de acidentes varia bem mais entre os anos."
    )
    st.caption(
        "Por quê importa: gravidade é uma característica estrutural e estável do sistema viário, não "
        "uma tendência que sobe ou desce — e isso torna um split temporal treino/teste seguro para o modelo."
    )

st.divider()

# --- 2. Pista e fase do dia ------------------------------------------------
st.header("2. Os dois efeitos estruturais mais fortes conhecidos *a priori*")
c3, c4 = st.columns(2)
with c3:
    df_pista = pd.DataFrame({
        "Tipo de pista": ["Simples", "Dupla"],
        "% grave/fatal": [t_pista["p1"] * 100, t_pista["p2"] * 100],
    })
    fig_pista = px.bar(df_pista, x="Tipo de pista", y="% grave/fatal", color="Tipo de pista",
                        text_auto=".1f")
    fig_pista.update_layout(showlegend=False)
    st.plotly_chart(fig_pista, width="stretch")
    st.markdown(
        f"**Pista simples** tem **{t_pista['diff_pp']:+.2f} p.p.** a mais de gravidade que pista dupla "
        f"(IC95%: {t_pista['diff_ci_pp'][0]:+.2f} a {t_pista['diff_ci_pp'][1]:+.2f}) — sem separação "
        "física de fluxos, colisão frontal (o tipo de acidente mais letal) se torna possível."
    )
with c4:
    df_fase = pd.DataFrame({
        "Fase do dia": ["Pleno dia", "Plena Noite"],
        "% grave/fatal": [t_fase["p2"] * 100, t_fase["p1"] * 100],
    })
    fig_fase = px.bar(df_fase, x="Fase do dia", y="% grave/fatal", color="Fase do dia", text_auto=".1f")
    fig_fase.update_layout(showlegend=False)
    st.plotly_chart(fig_fase, width="stretch")
    st.markdown(
        f"**Plena noite** tem **{t_fase['diff_pp']:+.2f} p.p.** a mais de gravidade que pleno dia "
        f"(IC95%: {t_fase['diff_ci_pp'][0]:+.2f} a {t_fase['diff_ci_pp'][1]:+.2f}) — o pico de *volume* "
        "é no fim de tarde, mas o pico de *gravidade relativa* é noturno; são dois fenômenos distintos."
    )

st.divider()

# --- 3. Geografia: onde os acidentes acontecem ------------------------------
st.header("3. Geografia: onde os acidentes acontecem")
uf_geo = query(
    "SELECT uf, count(*) n, round(100.0*avg(grave_bin),2) pct_grave, "
    "avg(latitude) lat, avg(longitude) lon FROM acidentes_enriquecido "
    "WHERE latitude IS NOT NULL AND longitude IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"
)
c5, c6 = st.columns([1, 1])
with c5:
    fig_uf = px.bar(
        uf_geo, x="uf", y="n", color="pct_grave", color_continuous_scale="Reds",
        labels={"uf": "UF", "n": "Acidentes", "pct_grave": "% grave"},
    )
    st.plotly_chart(fig_uf, width="stretch")
    st.caption(
        f"**{uf_geo.iloc[0]['uf']}** concentra o maior volume de registros "
        f"({uf_geo.iloc[0]['n']:,}".replace(",", ".") + f", {uf_geo.iloc[0]['n']/total:.1%} do total). "
        "Volume de acidentes reflete tráfego e extensão de malha rodoviária, não necessariamente risco "
        "por viagem (falta o denominador de exposição — ver 💡 Insights e Hipóteses)."
    )
with c6:
    fig_map = px.scatter_geo(
        uf_geo, lat="lat", lon="lon", size="n", color="pct_grave", hover_name="uf",
        color_continuous_scale="Reds", size_max=45, scope="south america",
        labels={"pct_grave": "% grave", "n": "Acidentes"},
    )
    fig_map.update_geos(fitbounds="locations", visible=True, showcountries=True, countrycolor="lightgray")
    fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_map, width="stretch")
    st.caption(
        "Cada bolha é uma UF, posicionada na latitude/longitude **média real** dos seus acidentes "
        "(não um centróide fixo) — tamanho = volume, cor = % grave/fatal. Ver 🗺️ Geografia para "
        "rankings de trecho e mapa de calor completos."
    )

st.divider()

# --- 4. Feriados: exposição, não gravidade ----------------------------------
st.header("4. Feriados: mais movimento na véspera, gravidade quase não muda")
tipo_dia_stats = query(
    "SELECT tipo_dia, count(*) n, round(100.0*avg(grave_bin),2) pct_grave, "
    "count(DISTINCT dia) dias FROM acidentes_enriquecido GROUP BY 1"
)
tipo_dia_stats["media_por_dia"] = tipo_dia_stats["n"] / tipo_dia_stats["dias"]
ORDEM_TIPO_DIA = ["Dia comum", "Véspera de feriado", "Feriado", "Pós-feriado"]
tipo_dia_stats["tipo_dia"] = pd.Categorical(tipo_dia_stats["tipo_dia"], categories=ORDEM_TIPO_DIA, ordered=True)
tipo_dia_stats = tipo_dia_stats.sort_values("tipo_dia")

top_feriados = query(
    "SELECT nome_feriado, count(*) n, round(100.0*avg(grave_bin),2) pct_grave "
    "FROM acidentes_enriquecido WHERE tipo_dia = 'Feriado' AND nome_feriado IS NOT NULL "
    "GROUP BY 1 ORDER BY 2 DESC LIMIT 8"
)

c7, c8 = st.columns(2)
with c7:
    fig_dia = px.bar(
        tipo_dia_stats, x="tipo_dia", y="media_por_dia", color="tipo_dia", text_auto=".1f",
        labels={"tipo_dia": "Tipo de dia", "media_por_dia": "Acidentes por dia (média)"},
    )
    fig_dia.update_layout(showlegend=False)
    st.plotly_chart(fig_dia, width="stretch")
    media_comum = tipo_dia_stats.set_index("tipo_dia").loc["Dia comum", "media_por_dia"]
    media_vesp = tipo_dia_stats.set_index("tipo_dia").loc["Véspera de feriado", "media_por_dia"]
    st.markdown(
        f"Véspera de feriado tem **{(media_vesp/media_comum - 1)*100:+.1f}%** mais acidentes/dia que um "
        "dia comum — efeito de **exposição** (mais gente na estrada saindo de viagem)."
    )
with c8:
    st.markdown("**% grave/fatal por tipo de dia** (quase não muda):")
    tabela_pct = tipo_dia_stats.set_index("tipo_dia")[["pct_grave"]].rename(columns={"pct_grave": "% grave"})
    st.dataframe(tabela_pct, width="stretch")
    st.markdown("**Feriados com mais acidentes registrados:**")
    st.dataframe(
        top_feriados.rename(columns={"nome_feriado": "Feriado", "n": "Acidentes", "pct_grave": "% grave"}),
        width="stretch", hide_index=True,
    )
st.caption(
    "O risco (dado que houve acidente) não se desloca para a véspera — só o volume. Ver hipótese H-05 "
    "em 💡 Insights e Hipóteses para a ressalva sobre confusão com dia da semana."
)

st.divider()

# --- 5. O que não pode virar feature ---------------------------------------
st.header("5. A armadilha central do projeto: sinal forte, mas inutilizável")
st.warning(
    "`tipo_acidente` (Cramér's V ≈ 0,30) e `causa_acidente` (≈ 0,24) são as variáveis mais associadas à "
    "gravidade — muito à frente de `br`/`uf` (≈ 0,11), a melhor variável disponível *a priori*. O problema: "
    "ambas só existem **depois** da apuração do acidente. Usá-las como feature seria *data leakage* — um "
    "modelo excelente no papel e inútil na prática, porque no momento da previsão essas colunas não existem. "
    "Por isso o teto de desempenho de qualquer modelo treinado só com informação a priori é estruturalmente "
    "mais baixo do que a tabela de associações sugere."
)

st.divider()
st.subheader("Hipóteses levantadas para a etapa de modelagem")
st.write(
    "A EDA formulou 6 hipóteses refutáveis (H-01 a H-06) para orientar a Etapa 3 — detalhamento completo, "
    "com critério de confirmação/refutação de cada uma, na página 💡 Insights e Hipóteses."
)

st.divider()
st.caption(
    "📄 Relatório técnico completo da Etapa 2: "
    "[`docs/entregas/etapa2-eda.md`](../docs/entregas/etapa2-eda.md). "
    "Para navegar fundo em qualquer achado: 🧹 Qualidade dos Dados, 📊 Distribuições, 🎯 Gravidade, "
    "📈 Tendências, 🔄 Sazonalidade, 🔗 Correlações, 🚨 Anomalias, ✂️ Segmentação, 🗺️ Geografia e "
    "🧪 Validação Estatística — todas mantidas intactas para análise mais profunda."
)
