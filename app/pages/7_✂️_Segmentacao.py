"""Comparação entre dois segmentos, com controle de composição (padronização direta).

Média geral esconde grupo: esta página existe para atacar diretamente dois erros clássicos
de EDA — analisar apenas a média global e olhar variáveis isoladamente. Toda diferença
mostrada aqui vem acompanhada de (a) incerteza amostral e (b) um teste de confundimento:
o quanto da diferença some quando os dois segmentos são forçados a ter a mesma composição.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import distinct_values, query, render_sidebar_filters, show_active_filters

from src.eda import utils as eu  # noqa: E402

st.title("✂️ Segmentação e Comparação de Grupos")
st.caption(
    "A taxa média nacional de acidentes graves é uma só; a de cada segmento não. "
    "Aqui você compara dois recortes e verifica se a diferença sobrevive ao controle de composição."
)

where, selections = render_sidebar_filters()
show_active_filters(selections)

SEG_COLS = ["uf", "br", "tipo_pista", "tracado_via", "fase_dia", "dia_semana", "tipo_dia",
            "condicao_metereologica", "uso_solo", "sentido_via", "tipo_acidente", "causa_acidente",
            "ano", "mes", "hora"]


def _in_clause(col: str, values: list) -> str:
    if not values:
        return "1=1"
    if isinstance(values[0], str):
        vals = ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)
    else:
        vals = ", ".join(str(v) for v in values)
    return f"{col} IN ({vals})"


st.subheader("1. Defina os dois segmentos")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**🟦 Segmento A**")
    col_a = st.selectbox("Variável", SEG_COLS, index=SEG_COLS.index("uf"), key="seg_col_a")
    opts_a = distinct_values(col_a)
    default_a = ["MA"] if col_a == "uf" and "MA" in opts_a else opts_a[:1]
    vals_a = st.multiselect("Valores", opts_a, default=default_a, key="seg_val_a")
with c2:
    st.markdown("**🟧 Segmento B**")
    modo_b = st.radio("Como definir B?", ["Complemento de A (todo o resto)", "Escolher valores"],
                      horizontal=False, key="seg_modo_b")
    if modo_b.startswith("Complemento"):
        col_b, vals_b = col_a, None
    else:
        col_b = st.selectbox("Variável", SEG_COLS, index=SEG_COLS.index(col_a), key="seg_col_b")
        opts_b = [o for o in distinct_values(col_b) if not (col_b == col_a and o in vals_a)]
        vals_b = st.multiselect("Valores", opts_b, default=opts_b[:1], key="seg_val_b")

if not vals_a:
    st.warning("Selecione ao menos um valor para o segmento A.")
    st.stop()

clause_a = _in_clause(col_a, vals_a)
if vals_b is None:
    clause_b = f"NOT ({clause_a})"
    label_b = f"resto (todos os outros valores de {col_a})"
else:
    if not vals_b:
        st.warning("Selecione ao menos um valor para o segmento B.")
        st.stop()
    clause_b = _in_clause(col_b, vals_b)
    label_b = f"{col_b} = {', '.join(map(str, vals_b))}"
label_a = f"{col_a} = {', '.join(map(str, vals_a))}"


@st.cache_data(show_spinner=False)
def seg_stats(where_sql: str, clause: str) -> dict:
    row = query(
        f"SELECT count(*) n, sum(grave_bin) k, sum(mortos) mortos, "
        f"sum(CASE WHEN mortos>0 THEN 1 ELSE 0 END) k_fatal, avg(veiculos) veic "
        f"FROM acidentes_enriquecido WHERE {where_sql} AND ({clause})"
    ).iloc[0]
    n, k = int(row["n"]), int(row["k"] or 0)
    lo, hi = eu.wilson_ci(k, n) if n else (np.nan, np.nan)
    return {"n": n, "k": k, "pct": 100 * k / n if n else np.nan,
            "ci": (100 * lo, 100 * hi), "mortos": int(row["mortos"] or 0),
            "pct_fatal": 100 * int(row["k_fatal"] or 0) / n if n else np.nan,
            "veiculos_medio": float(row["veic"]) if row["veic"] is not None else np.nan}


a = seg_stats(where, clause_a)
b = seg_stats(where, clause_b)

if a["n"] == 0 or b["n"] == 0:
    st.error("Um dos segmentos ficou vazio com os filtros atuais.")
    st.stop()

st.divider()
tab_bruto, tab_composicao = st.tabs(["Diferença Bruta", "Controle de Composição"])

# ---------------------------------------------------------------------------
with tab_bruto:
    st.subheader("Diferença observada (com a incerteza que ela merece)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"🟦 A — n", f"{a['n']:,}".replace(",", "."))
    m2.metric("🟦 A — % grave/fatal", f"{a['pct']:.2f}%", help=f"IC95% Wilson: {a['ci'][0]:.2f}% – {a['ci'][1]:.2f}%")
    m3.metric(f"🟧 B — n", f"{b['n']:,}".replace(",", "."))
    m4.metric("🟧 B — % grave/fatal", f"{b['pct']:.2f}%", help=f"IC95% Wilson: {b['ci'][0]:.2f}% – {b['ci'][1]:.2f}%")

    test = eu.two_proportion_test(a["k"], a["n"], b["k"], b["n"])

    fig = go.Figure()
    for nome, s, cor in [(f"🟦 A: {label_a}", a, "#3b6ea5"), (f"🟧 B: {label_b}", b, "#d98032")]:
        fig.add_trace(go.Bar(
            x=[s["pct"]], y=[nome], orientation="h", marker_color=cor, showlegend=False,
            error_x=dict(type="data", symmetric=False,
                         array=[s["ci"][1] - s["pct"]], arrayminus=[s["pct"] - s["ci"][0]]),
            text=[f"{s['pct']:.2f}%"], textposition="outside",
        ))
    fig.update_layout(height=220, title="% de acidentes graves/fatais, com IC 95% (Wilson)",
                      xaxis_title="% grave ou fatal", margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width="stretch")

    d1, d2, d3 = st.columns(3)
    d1.metric("Diferença A − B", f"{test['diff_pp']:+.2f} p.p.",
              help=f"IC95%: {test['diff_ci_pp'][0]:+.2f} a {test['diff_ci_pp'][1]:+.2f} p.p.")
    d2.metric("Razão de risco (A/B)", f"{test['risk_ratio']:.2f}×")
    d3.metric("Tamanho de efeito (h de Cohen)", f"{test['cohen_h']:+.3f}", help=f"Classificação: {test['efeito']}")

    sig = test["p_value"] < 0.05
    ic_lo, ic_hi = test["diff_ci_pp"]
    box = st.success if (sig and ic_lo * ic_hi > 0) else st.warning
    box(
        f"{'✅' if sig and ic_lo * ic_hi > 0 else '⚠️'} O intervalo de confiança da diferença vai de "
        f"**{ic_lo:+.2f}** a **{ic_hi:+.2f} p.p.** (p = {test['p_value']:.2e}) — "
        + ("ele não cruza o zero, então a diferença não é ruído amostral."
           if sig and ic_lo * ic_hi > 0 else
           "ele **cruza o zero**, então os dados são compatíveis com nenhuma diferença real.")
        + f" Tamanho de efeito (h de Cohen): **{test['efeito']}**."
    )
    with st.expander("Como ler significância × tamanho de efeito"):
        st.markdown(
            "Significância não é relevância: o h de Cohen classifica o efeito, mas o p-valor sozinho não "
            "diz se ele importa. Com n desta ordem, quase toda diferença fica \"significante\" — é o "
            "tamanho do efeito que decide se ela importa ([D-08](../docs/decisoes/DECISIONS.md))."
        )

# ---------------------------------------------------------------------------
with tab_composicao:
    st.subheader("A diferença sobrevive ao controle de composição?")
    st.caption(
        "Um segmento pode parecer mais perigoso apenas por concentrar mais do tipo de via, horário ou "
        "período que já é mais perigoso em qualquer lugar. A padronização direta recalcula a taxa de cada "
        "segmento como se ambos tivessem a **mesma composição** — a de A+B juntos."
    )

    confounders = [c for c in ["tipo_pista", "fase_dia", "hora", "dia_semana", "tipo_acidente",
                               "tracado_via", "uso_solo", "condicao_metereologica", "uf", "mes"]
                   if c not in (col_a, col_b)]
    strata = st.selectbox("Controlar por (possível confundidor):", confounders, index=0)

    counts = query(
        f"""
        SELECT {strata} AS estrato,
               sum(CASE WHEN {clause_a} THEN 1 ELSE 0 END) n_a,
               sum(CASE WHEN {clause_a} THEN grave_bin ELSE 0 END) k_a,
               sum(CASE WHEN {clause_b} THEN 1 ELSE 0 END) n_b,
               sum(CASE WHEN {clause_b} THEN grave_bin ELSE 0 END) k_b
        FROM acidentes_enriquecido
        WHERE {where} AND {strata} IS NOT NULL AND (({clause_a}) OR ({clause_b}))
        GROUP BY 1 ORDER BY 1
        """
    )
    counts["estrato"] = counts["estrato"].astype(str)
    counts = counts[(counts["n_a"] > 0) | (counts["n_b"] > 0)]
    weights = (counts.set_index("estrato")["n_a"] + counts.set_index("estrato")["n_b"]).astype(float)

    std_a = eu.standardized_rate(counts.rename(columns={"n_a": "n", "k_a": "n_grave"}), "estrato", weights)
    std_b = eu.standardized_rate(counts.rename(columns={"n_b": "n", "k_b": "n_grave"}), "estrato", weights)

    comp = pd.DataFrame({
        "segmento": [f"🟦 A: {label_a}", f"🟧 B: {label_b}"],
        "taxa bruta (%)": [std_a["crude"] * 100, std_b["crude"] * 100],
        f"taxa padronizada por {strata} (%)": [std_a["standardized"] * 100, std_b["standardized"] * 100],
    })
    comp["diferença explicada pela composição (p.p.)"] = (
        comp["taxa bruta (%)"] - comp[f"taxa padronizada por {strata} (%)"]
    ).round(2)
    st.dataframe(comp.round(2), width="stretch")

    gap_bruto = std_a["crude"] * 100 - std_b["crude"] * 100
    gap_padr = std_a["standardized"] * 100 - std_b["standardized"] * 100
    explicado = gap_bruto - gap_padr
    pct_explicado = (explicado / gap_bruto * 100) if abs(gap_bruto) > 1e-9 else np.nan

    g1, g2, g3 = st.columns(3)
    g1.metric("Diferença bruta", f"{gap_bruto:+.2f} p.p.")
    g2.metric(f"Diferença padronizada por {strata}", f"{gap_padr:+.2f} p.p.")
    g3.metric("Explicado pela composição", f"{pct_explicado:.0f}%" if np.isfinite(pct_explicado) else "—")

    if np.isfinite(pct_explicado):
        if np.sign(gap_padr) != np.sign(gap_bruto) and abs(gap_bruto) > 0.5:
            st.error(
                f"🔄 **Inversão de sinal (paradoxo de Simpson).** Controlando por `{strata}`, a vantagem muda "
                "de lado: a diferença bruta era um artefato da composição dos grupos, não do risco em si. "
                "Qualquer conclusão baseada só na comparação bruta estaria errada."
            )
        elif pct_explicado >= 60:
            st.warning(
                f"⚠️ `{strata}` explica **{pct_explicado:.0f}%** da diferença bruta. O segmento A não é "
                "intrinsecamente mais grave — ele apenas concentra estratos que já são mais graves em "
                "qualquer lugar. Reporte a taxa padronizada, não a bruta."
            )
        elif pct_explicado >= 20:
            st.info(
                f"`{strata}` explica **{pct_explicado:.0f}%** da diferença; a maior parte do excesso persiste "
                "mesmo com composição igualada. Vale testar outros confundidores antes de concluir."
            )
        else:
            st.success(
                f"A diferença é **robusta** a `{strata}` (explica apenas {pct_explicado:.0f}%). "
                "Isso reforça — mas não prova — que o efeito é do próprio segmento. Continua sendo uma "
                "associação observacional: há confundidores não medidos (fluxo de veículos, fiscalização, "
                "tempo de resgate) fora desta base."
            )

    st.markdown("**Decomposição por estrato** — Taxa (risco) e Volume (exposição), lado a lado:")
    det = counts.copy()
    det["taxa_A_%"] = (det["k_a"] / det["n_a"] * 100).round(2)
    det["taxa_B_%"] = (det["k_b"] / det["n_b"] * 100).round(2)
    det["peso_%"] = (weights.values / weights.sum() * 100).round(2)

    col_taxa, col_vol = st.columns(2)
    with col_taxa:
        taxa_plot = det.melt(id_vars="estrato", value_vars=["taxa_A_%", "taxa_B_%"],
                             var_name="segmento", value_name="pct_grave")
        fig2 = px.bar(taxa_plot, x="estrato", y="pct_grave", color="segmento", barmode="group",
                      color_discrete_map={"taxa_A_%": "#3b6ea5", "taxa_B_%": "#d98032"},
                      title=f"Taxa: % grave/fatal por {strata}",
                      labels={"pct_grave": "% grave ou fatal"})
        st.plotly_chart(fig2, width="stretch")
    with col_vol:
        vol_plot = det.melt(id_vars="estrato", value_vars=["n_a", "n_b"],
                            var_name="segmento", value_name="n")
        fig_vol = px.bar(vol_plot, x="estrato", y="n", color="segmento", barmode="group",
                         color_discrete_map={"n_a": "#3b6ea5", "n_b": "#d98032"},
                         title=f"Volume: n por {strata}", labels={"n": "registros"})
        st.plotly_chart(fig_vol, width="stretch")

    st.dataframe(det[["estrato", "n_a", "taxa_A_%", "n_b", "taxa_B_%", "peso_%"]], width="stretch")
    st.caption(
        "Estratos com `n` pequeno em um dos lados têm taxa instável — leia o painel de Taxa junto com o "
        "de Volume, nunca só a barra de %. A página 🧪 Validação Estatística calcula o IC de cada estrato."
    )

    st.divider()
    st.subheader("Perfil comparado dos segmentos")
    perfil_col = st.selectbox("Comparar a composição de:", SEG_COLS,
                              index=SEG_COLS.index("tipo_pista"), key="perfil_col")
    perfil = query(
        f"""
        SELECT {perfil_col} AS categoria,
               round(100.0*sum(CASE WHEN {clause_a} THEN 1 ELSE 0 END)/nullif(sum(sum(CASE WHEN {clause_a} THEN 1 ELSE 0 END)) OVER (), 0), 2) AS pct_A,
               round(100.0*sum(CASE WHEN {clause_b} THEN 1 ELSE 0 END)/nullif(sum(sum(CASE WHEN {clause_b} THEN 1 ELSE 0 END)) OVER (), 0), 2) AS pct_B
        FROM acidentes_enriquecido
        WHERE {where} AND {perfil_col} IS NOT NULL AND (({clause_a}) OR ({clause_b}))
        GROUP BY 1 ORDER BY 2 DESC NULLS LAST LIMIT 20
        """
    )
    perfil["categoria"] = perfil["categoria"].astype(str)
    perfil["diferença (p.p.)"] = (perfil["pct_A"] - perfil["pct_B"]).round(2)
    fig3 = px.bar(perfil.melt(id_vars="categoria", value_vars=["pct_A", "pct_B"],
                              var_name="segmento", value_name="pct"),
                  x="categoria", y="pct", color="segmento", barmode="group",
                  color_discrete_map={"pct_A": "#3b6ea5", "pct_B": "#d98032"},
                  title=f"Composição de {perfil_col} em cada segmento (% dentro do segmento)")
    st.plotly_chart(fig3, width="stretch")
    st.dataframe(perfil, width="stretch")
    st.caption(
        "É aqui que se vê **por que** a padronização muda o resultado: se A tem muito mais de uma "
        "categoria que é naturalmente mais grave, parte do excesso dele é composição, não risco."
    )
