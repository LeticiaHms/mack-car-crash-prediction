"""Validação estatística dos achados: teste formal + tamanho de efeito + incerteza.

Olhar um gráfico e declarar um padrão é o erro nº 9 do guia da disciplina. Esta página fecha
esse buraco: cada afirmação que a EDA faz pode ser submetida aqui a um teste explícito, sempre
com três números juntos — a estatística do teste, o p-valor e o **tamanho do efeito**.

O alerta que atravessa a página: com n ≈ 300 mil, o p-valor perde utilidade como filtro
(quase tudo dá p < 0,001). Quem decide relevância é o tamanho de efeito ([D-08](../docs/decisoes/DECISIONS.md)).
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from common import get_connection, query, render_sidebar_filters, show_active_filters

from src.eda import utils as eu  # noqa: E402

st.title("🧪 Validação Estatística dos Achados")

where, selections = render_sidebar_filters()
show_active_filters(selections)
con = get_connection()

tab_prop, tab_grupos, tab_num, tab_poder = st.tabs(
    ["Comparar taxas (proporções)", "Um teste por categoria", "Distribuições numéricas", "Por que não confiar no p-valor aqui"]
)

# ---------------------------------------------------------------------------
with tab_prop:
    st.subheader("A taxa de gravidade difere entre duas categorias?")
    st.caption(
        "Teste z para duas proporções + IC de Wilson de cada uma. Use para validar frases do tipo "
        "'pista simples é mais grave que pista dupla' antes de escrevê-las no relatório."
    )
    COLS = ["tipo_pista", "fase_dia", "dia_semana", "tipo_dia", "condicao_metereologica",
            "uso_solo", "sentido_via", "uf", "tracado_via", "tipo_acidente", "mes", "hora", "ano"]

    f1, f2, f3 = st.columns(3)
    with f1:
        col = st.selectbox("Variável", COLS, index=0)
    cats = query(
        f"SELECT {col} AS c, count(*) n, sum(grave_bin) k FROM acidentes_enriquecido "
        f"WHERE {where} AND {col} IS NOT NULL GROUP BY 1 HAVING count(*) >= 30 ORDER BY 2 DESC"
    )
    cats["c"] = cats["c"].astype(str)
    if len(cats) < 2:
        st.warning("São necessárias ao menos duas categorias com n ≥ 30.")
    else:
        with f2:
            cat_a = st.selectbox("Categoria A", cats["c"].tolist(), index=0)
        with f3:
            cat_b = st.selectbox("Categoria B", cats["c"].tolist(), index=1)
        ra = cats[cats["c"] == cat_a].iloc[0]
        rb = cats[cats["c"] == cat_b].iloc[0]
        res = eu.two_proportion_test(int(ra["k"]), int(ra["n"]), int(rb["k"]), int(rb["n"]))

        m = st.columns(4)
        m[0].metric(f"{cat_a}", f"{res['p1']*100:.2f}%", help=f"n = {res['n1']}")
        m[1].metric(f"{cat_b}", f"{res['p2']*100:.2f}%", help=f"n = {res['n2']}")
        m[2].metric("Diferença", f"{res['diff_pp']:+.2f} p.p.",
                    help=f"IC95%: {res['diff_ci_pp'][0]:+.2f} a {res['diff_ci_pp'][1]:+.2f}")
        m[3].metric("h de Cohen", f"{res['cohen_h']:+.3f}", help=f"efeito {res['efeito']}")

        diferenca_real = res["diff_ci_pp"][0] * res["diff_ci_pp"][1] > 0
        veredito = "diferença real (o IC não cruza zero)" if diferenca_real else "**não distinguível de zero** com estes dados"
        box = st.success if diferenca_real else st.warning
        box(
            f"- Estatística z = **{res['z']:.2f}**, p = **{res['p_value']:.3g}** → {veredito}.\n"
            f"- Razão de risco: acidentes em *{cat_a}* têm **{res['risk_ratio']:.2f}×** a chance de "
            f"serem graves em relação a *{cat_b}*.\n"
            f"- Magnitude prática: efeito **{res['efeito']}** pela escala de Cohen — "
            "significância estatística e importância prática são coisas diferentes."
        )

        st.markdown("**Todas as categorias com IC 95% (Wilson):**")
        ci = cats.apply(lambda r: eu.wilson_ci(int(r["k"]), int(r["n"])), axis=1, result_type="expand")
        cats["pct"] = (cats["k"] / cats["n"] * 100).round(2)
        cats["ic_low"] = (ci[0] * 100).round(2)
        cats["ic_high"] = (ci[1] * 100).round(2)
        plot = cats.sort_values("pct", ascending=False).head(30)
        fig = px.scatter(plot, x="pct", y="c", size="n",
                         error_x=plot["ic_high"] - plot["pct"], error_x_minus=plot["pct"] - plot["ic_low"],
                         labels={"pct": "% grave ou fatal", "c": col},
                         title=f"% grave/fatal por {col}, com IC 95%")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(cats[["c", "n", "k", "pct", "ic_low", "ic_high"]], width="stretch")
        st.caption(
            "Categorias cujos intervalos **se sobrepõem** não podem ser ordenadas com confiança — "
            "dizer que uma é 'pior' que a outra seria ler ruído como padrão."
        )

# ---------------------------------------------------------------------------
with tab_grupos:
    st.subheader("Teste global: a variável inteira está associada à gravidade?")
    st.caption(
        "Qui-quadrado de independência (a variável tem *alguma* relação com a gravidade?) + "
        "Cramér's V corrigido (o quanto essa relação vale). O V é o número que ordena a lista."
    )
    ALL_COLS = ["tipo_acidente", "causa_acidente", "br", "uf", "uso_solo", "hora", "tipo_pista",
                "fase_dia", "tipo_dia", "sentido_via", "tracado_via", "dia_semana",
                "condicao_metereologica", "mes", "ano"]
    con.execute(f"CREATE OR REPLACE TEMP VIEW filtrado AS SELECT * FROM acidentes_enriquecido WHERE {where}")

    rows = []
    for c in ALL_COLS:
        try:
            ct = con.execute(
                f"SELECT gravidade_4 a, {c} b, count(*) n FROM filtrado WHERE {c} IS NOT NULL GROUP BY 1,2"
            ).df().pivot_table(index="a", columns="b", values="n", fill_value=0)
            if ct.shape[0] < 2 or ct.shape[1] < 2:
                continue
            chi2, p, dof, _ = stats.chi2_contingency(ct)
            rows.append({
                "variável": c, "cramers_v": round(eu.cramers_v(ct), 4), "chi2": round(chi2, 1),
                "gl": int(dof), "p_value": p, "n": int(ct.to_numpy().sum()),
                "disponível a priori": c not in ("tipo_acidente", "causa_acidente", "condicao_metereologica"),
            })
        except Exception:
            continue
    assoc = pd.DataFrame(rows).sort_values("cramers_v", ascending=False)
    assoc["força"] = pd.cut(assoc["cramers_v"], [-0.01, 0.05, 0.1, 0.2, 0.3, 1.0],
                            labels=["desprezível", "fraca", "moderada", "relevante", "forte"])

    fig = px.bar(assoc, x="cramers_v", y="variável", orientation="h", color="disponível a priori",
                 color_discrete_map={True: "#2e7d5b", False: "#b03a2e"},
                 title="Cramér's V com gravidade_4 — verde = utilizável como feature, vermelho = pós-evento (leakage)")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=560)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(assoc, width="stretch")

    n_signif = int((assoc["p_value"] < 0.05).sum())
    st.error(
        f"**{n_signif} de {len(assoc)} variáveis** aparecem como 'estatisticamente significantes' (p < 0,05) — "
        "inclusive as de V ≈ 0,01, que não têm nenhum valor prático. É a demonstração empírica de que, "
        "neste tamanho de amostra, o p-valor não serve para selecionar variáveis. "
        "E note o contraste central da EDA: as duas variáveis de maior associação são justamente as "
        "**pós-evento**, que não podem virar feature (🧠 Features para ML)."
    )

# ---------------------------------------------------------------------------
with tab_num:
    st.subheader("A distribuição numérica difere entre os níveis de gravidade?")
    st.caption(
        "Kruskal-Wallis (versão não-paramétrica da ANOVA). Escolhido porque as variáveis de contagem "
        "são fortemente assimétricas e zero-infladas — a ANOVA clássica assumiria normalidade que os "
        "dados não têm (ver 📊 Distribuições: assimetria de `mortos` ≈ 10,7)."
    )
    NUM = ["veiculos", "pessoas", "km", "ilesos", "feridos_leves", "ignorados"]
    num_col = st.selectbox("Variável numérica", NUM, index=0)
    data = query(
        f"SELECT gravidade_4 g, {num_col} v FROM acidentes_enriquecido "
        f"WHERE {where} AND {num_col} IS NOT NULL"
    )
    if data["g"].nunique() < 2:
        st.warning("São necessários ao menos dois grupos de gravidade.")
    else:
        grupos = [g["v"].to_numpy(dtype=float) for _, g in data.groupby("g")]
        h, p = stats.kruskal(*grupos)
        k, n_tot = len(grupos), len(data)
        epsilon2 = (h - k + 1) / (n_tot - k) if n_tot > k else np.nan  # tamanho de efeito do Kruskal

        c1, c2, c3 = st.columns(3)
        c1.metric("H de Kruskal-Wallis", f"{h:,.1f}".replace(",", "."))
        c2.metric("p-valor", f"{p:.3g}")
        c3.metric("ε² (tamanho de efeito)", f"{epsilon2:.4f}",
                  help="0 = grupos idênticos; 0,01 pequeno; 0,06 moderado; 0,14 grande")

        resumo = data.groupby("g")["v"].agg(["count", "mean", "median", "std"]).round(3).reset_index()
        resumo.columns = ["gravidade_4", "n", "média", "mediana", "desvio-padrão"]
        st.dataframe(resumo, width="stretch")

        fig = px.violin(data, x="g", y="v", box=True, points=False,
                        category_orders={"g": ["Sem vítimas", "Leve", "Grave (não fatal)", "Fatal"]},
                        labels={"g": "gravidade_4", "v": num_col},
                        title=f"Distribuição de {num_col} por nível de gravidade")
        st.plotly_chart(fig, width="stretch")
        st.markdown(
            f"O teste rejeita a igualdade entre os grupos (p = {p:.3g}), mas o ε² = **{epsilon2:.4f}** diz "
            "o quanto da variação de `" + num_col + "` é explicada pela gravidade. "
            "Um p minúsculo com ε² minúsculo significa: a diferença existe e é detectável, "
            "porém pequena demais para sustentar uma conclusão forte sozinha."
        )
        if num_col in ("pessoas", "ilesos", "feridos_leves"):
            st.warning(
                "⚠️ Esta variável é **pós-evento**: ela descreve o resultado do acidente. O teste aqui "
                "caracteriza o fenômeno, não valida uma feature preditiva ([D-07](../docs/decisoes/DECISIONS.md))."
            )

# ---------------------------------------------------------------------------
with tab_poder:
    st.subheader("Por que o p-valor deixa de informar quando n é grande")
    st.caption(
        "Simulação sobre os próprios dados: qual a menor diferença de taxa que este dataset "
        "declararia 'significante' em cada tamanho de amostra?"
    )
    base = query(f"SELECT count(*) n, sum(grave_bin) k FROM acidentes_enriquecido WHERE {where}").iloc[0]
    p0 = float(base["k"]) / float(base["n"]) if base["n"] else 0.28

    tamanhos = np.array([100, 300, 1_000, 3_000, 10_000, 30_000, 100_000, int(base["n"])])
    z = stats.norm.ppf(0.975)
    # diferença mínima detectável em um teste de duas proporções com grupos de tamanho n cada
    mde = z * np.sqrt(2 * p0 * (1 - p0) / tamanhos) * 100
    dfm = pd.DataFrame({"n por grupo": tamanhos, "diferença mínima 'significante' (p.p.)": mde.round(3)})

    fig = go.Figure()
    fig.add_scatter(x=dfm["n por grupo"], y=dfm["diferença mínima 'significante' (p.p.)"],
                    mode="lines+markers")
    fig.update_layout(xaxis_type="log", yaxis_type="log", height=380,
                      xaxis_title="n de cada grupo (escala log)",
                      yaxis_title="menor diferença detectável (p.p., escala log)",
                      title=f"Taxa-base usada: {p0*100:.2f}% de acidentes graves")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(dfm, width="stretch")

    mde_full = z * np.sqrt(2 * p0 * (1 - p0) / int(base["n"])) * 100
    st.info(
        f"""
        Com **{int(base['n']):,} registros**, diferenças de apenas **{mde_full:.3f} p.p.** já saem
        "significantes" — uma diferença que nenhum gestor de segurança viária conseguiria usar para
        decidir nada. Por isso, neste projeto:

        1. o **tamanho de efeito** (Cramér's V, h de Cohen, ε²) é o critério de priorização;
        2. o **intervalo de confiança** é reportado sempre, porque mostra a precisão da estimativa;
        3. o p-valor entra apenas como checagem de que o achado não é ruído — nunca como medida de
           importância ([D-08](../docs/decisoes/DECISIONS.md)).
        """.replace(",", ".")
    )
