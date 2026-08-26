import plotly.express as px
import streamlit as st

from common import query, render_sidebar_filters, show_active_filters

st.set_page_config(page_title="Gravidade", page_icon="🎯", layout="wide")
st.title("🎯 Análise da Gravidade")
st.caption(
    "`classificacao_acidente` (3 classes) mistura ferido leve e grave. Por isso usamos `gravidade_4` "
    "= Sem vítimas / Leve / Grave (não fatal) / Fatal, derivada de mortos/feridos_graves/feridos_leves "
    "(ver docs/DECISIONS.md D-01)."
)

where, selections = render_sidebar_filters()
show_active_filters(selections)

GRAV_ORDER = ["Sem vítimas", "Leve", "Grave (não fatal)", "Fatal"]

dist = query(f"SELECT gravidade_4, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1")
total = dist["n"].sum()
dist["pct"] = (dist["n"] / total * 100).round(2)

c1, c2 = st.columns([1, 2])
with c1:
    fig = px.pie(dist, names="gravidade_4", values="n", hole=0.45,
                 category_orders={"gravidade_4": GRAV_ORDER}, title="Distribuição de gravidade_4")
    st.plotly_chart(fig, width="stretch")
with c2:
    grave_bin = query(f"SELECT grave_bin, count(*) n FROM acidentes_enriquecido WHERE {where} GROUP BY 1")
    grave_bin["label"] = grave_bin["grave_bin"].map({0: "Sem gravidade", 1: "Grave/Fatal"})
    grave_bin["pct"] = (grave_bin["n"] / grave_bin["n"].sum() * 100).round(2)
    st.markdown("**Target binário `grave_bin`** (mortos>0 OU feridos_graves>0):")
    st.dataframe(grave_bin[["label", "n", "pct"]], width="stretch")
    ratio = grave_bin.set_index("grave_bin")["n"]
    if 0 in ratio and 1 in ratio and ratio[1] > 0:
        st.metric("Razão não-grave : grave", f"{ratio[0]/ratio[1]:.2f} : 1")

st.divider()
st.subheader("Gravidade × variável explicativa")

CROSS_OPTIONS = ["uf", "br", "tipo_acidente", "causa_acidente", "condicao_metereologica",
                  "tipo_pista", "fase_dia", "dia_semana", "hora", "mes", "sentido_via", "uso_solo"]
col = st.selectbox("Cruzar gravidade com:", CROSS_OPTIONS, index=6)

rate = query(
    f"""
    SELECT {col} AS grupo, count(*) n,
           sum(grave_bin) n_grave,
           round(100.0*sum(grave_bin)/count(*),2) pct_grave,
           sum(CASE WHEN mortos>0 THEN 1 ELSE 0 END) n_fatal,
           round(100.0*sum(CASE WHEN mortos>0 THEN 1 ELSE 0 END)/count(*),2) pct_fatal
    FROM acidentes_enriquecido
    WHERE {where} AND {col} IS NOT NULL
    GROUP BY 1
    """
)
min_n = st.slider("Tamanho mínimo do grupo (evitar ruído de amostra pequena)", 1, 2000, 200)
rate_f = rate[rate["n"] >= min_n].sort_values("pct_grave", ascending=False)

left, right = st.columns([2, 1])
with left:
    fig = px.bar(rate_f.head(25), x="grupo", y="pct_grave", text="n",
                 title=f"% grave/fatal por {col} (grupos com n≥{min_n})",
                 labels={"pct_grave": "% grave ou fatal", "grupo": col})
    fig.update_traces(texttemplate="n=%{text}", textposition="outside")
    st.plotly_chart(fig, width="stretch")
with right:
    st.dataframe(rate_f, width="stretch", height=420)

st.caption(
    "Contagem absoluta reflete exposição (quanto se trafega ali), não apenas risco — "
    "leia como associação observacional, nunca causalidade (skill `eda`)."
)

st.divider()
st.subheader("Tabela de contingência")
col_b = st.selectbox("Segunda variável para contingência", CROSS_OPTIONS, index=4, key="ct2")
ct = query(
    f"SELECT gravidade_4, {col_b} AS categoria, count(*) n FROM acidentes_enriquecido "
    f"WHERE {where} AND {col_b} IS NOT NULL GROUP BY 1,2"
).pivot_table(index="categoria", columns="gravidade_4", values="n", fill_value=0)
ct = ct.reindex(columns=[c for c in GRAV_ORDER if c in ct.columns])
st.dataframe(ct, width="stretch")
st.caption("Percentuais condicionais (por linha):")
st.dataframe((ct.div(ct.sum(axis=1), axis=0) * 100).round(1), width="stretch")
