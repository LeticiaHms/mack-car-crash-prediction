import sys

import pandas as pd
import plotly.express as px
import streamlit as st

from common import get_connection, query, render_sidebar_filters, show_active_filters

sys.path.insert(0, "src") if "src" not in sys.path else None
import eda_utils as eu  # noqa: E402

st.set_page_config(page_title="Correlações e Associações", page_icon="🔗", layout="wide")
st.title("🔗 Correlações e Associações")
st.caption(
    "Correlação/associação ≠ causalidade. Com n grande, quase todo p-valor fica ≈0 — "
    "o Cramér's V (categórica×categórica) e o rho de Spearman (numérica×numérica) medem a força real."
)

where, selections = render_sidebar_filters()
show_active_filters(selections)
con = get_connection()

CAT_COLS = ["uf", "br", "tipo_acidente", "causa_acidente", "condicao_metereologica", "tipo_pista",
            "tracado_via", "fase_dia", "dia_semana", "sentido_via", "uso_solo", "mes", "hora"]
NUM_COLS = ["pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos", "feridos", "veiculos", "km"]

tab1, tab2, tab3 = st.tabs(["Gravidade × Categóricas (Cramér's V)", "Numérica × Numérica (Spearman)", "Tabela de contingência"])

with tab1:
    st.subheader("Força de associação com `gravidade_4`")
    if where != "1=1":
        st.info("Os filtros da sidebar afetam esta tabela — desative-os para reproduzir os valores de docs/specs/eda/EDA.md.")
    rows = []
    filtered_sql = f"(SELECT * FROM acidentes_enriquecido WHERE {where})"
    con.execute(f"CREATE OR REPLACE TEMP VIEW tmp_filtered AS SELECT * FROM {filtered_sql}")
    for col in CAT_COLS:
        try:
            ct = con.execute(
                f"SELECT gravidade_4 a, {col} b, count(*) n FROM tmp_filtered "
                f"WHERE {col} IS NOT NULL GROUP BY 1,2"
            ).df().pivot_table(index="a", columns="b", values="n", fill_value=0)
            if ct.shape[0] < 2 or ct.shape[1] < 2:
                continue
            from scipy import stats
            chi2, p, dof, _ = stats.chi2_contingency(ct)
            v = eu.cramers_v(ct)
            rows.append({"variável": col, "cramers_v": round(v, 4), "p_value": p, "n": int(ct.to_numpy().sum())})
        except Exception:
            continue
    assoc_df = pd.DataFrame(rows).sort_values("cramers_v", ascending=False)
    fig = px.bar(assoc_df, x="cramers_v", y="variável", orientation="h",
                 title="Cramér's V vs. gravidade_4 (ordenado)")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
    st.dataframe(assoc_df, width="stretch")
    st.caption(
        "Lembrete de leakage: `tipo_acidente` e `causa_acidente` têm as maiores associações, mas são "
        "pós-evento e NÃO podem virar feature preditiva direta (ver 🧠 Features para ML)."
    )

with tab2:
    c1, c2 = st.columns(2)
    col_a = c1.selectbox("Variável A", NUM_COLS, index=0)
    col_b = c2.selectbox("Variável B", NUM_COLS, index=NUM_COLS.index("mortos"))
    data = query(f"SELECT {col_a} a, {col_b} b, gravidade_4 FROM acidentes_enriquecido WHERE {where} AND {col_a} IS NOT NULL AND {col_b} IS NOT NULL")
    from scipy import stats as sstats
    if len(data) > 1 and col_a != col_b:
        rho, p = sstats.spearmanr(data["a"], data["b"])
        st.metric(f"Spearman ρ ({col_a} × {col_b})", f"{rho:.3f}", help=f"p={p:.2e}, n={len(data)}")
    sample = data.sample(min(5000, len(data)), random_state=42) if len(data) > 5000 else data
    fig2 = px.scatter(sample, x="a", y="b", color="gravidade_4", opacity=0.5,
                       labels={"a": col_a, "b": col_b},
                       title=f"{col_a} vs {col_b} (amostra de até 5.000 pontos)")
    st.plotly_chart(fig2, width="stretch")

with tab3:
    c1, c2 = st.columns(2)
    col_a = c1.selectbox("Linha", CAT_COLS, index=CAT_COLS.index("condicao_metereologica"), key="ct_a")
    col_b = c2.selectbox("Coluna", ["gravidade_4"] + CAT_COLS, index=0, key="ct_b")
    ct = query(
        f"SELECT {col_a} AS linha, {col_b} AS coluna, count(*) n FROM acidentes_enriquecido "
        f"WHERE {where} AND {col_a} IS NOT NULL AND {col_b} IS NOT NULL GROUP BY 1,2"
    ).pivot_table(index="linha", columns="coluna", values="n", fill_value=0)
    st.markdown("**Contagens**")
    st.dataframe(ct, width="stretch")
    st.markdown("**% por linha**")
    st.dataframe((ct.div(ct.sum(axis=1), axis=0) * 100).round(1), width="stretch")
    if ct.shape[0] >= 2 and ct.shape[1] >= 2:
        v = eu.cramers_v(ct)
        st.metric("Cramér's V", f"{v:.4f}")
