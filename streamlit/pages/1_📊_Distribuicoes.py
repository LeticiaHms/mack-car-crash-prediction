import numpy as np
import plotly.express as px
import streamlit as st
from scipy import stats

from common import query, render_sidebar_filters, show_active_filters

st.set_page_config(page_title="Distribuições", page_icon="📊", layout="wide")
st.title("📊 Distribuições")
st.caption("Cada gráfico responde: como esta variável se distribui, isoladamente e por gravidade?")

where, selections = render_sidebar_filters()
show_active_filters(selections)

NUMERIC = ["pessoas", "mortos", "feridos_leves", "feridos_graves", "ilesos", "ignorados", "feridos", "veiculos", "km"]
CATEGORICAL = ["uf", "br", "tipo_acidente", "causa_acidente", "classificacao_acidente", "fase_dia",
               "condicao_metereologica", "tipo_pista", "tracado_via", "sentido_via", "uso_solo", "dia_semana"]

tab_num, tab_cat = st.tabs(["Variáveis numéricas", "Variáveis categóricas"])

with tab_num:
    col = st.selectbox("Variável numérica", NUMERIC, index=0)
    df = query(f"SELECT {col} AS v, gravidade_4 FROM acidentes_enriquecido WHERE {where} AND {col} IS NOT NULL")
    if df.empty:
        st.warning("Sem dados para os filtros selecionados.")
    else:
        s = df["v"].astype(float)
        q1, q3 = s.quantile([0.25, 0.75])
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Média", f"{s.mean():.2f}")
        c2.metric("Mediana", f"{s.median():.2f}")
        c3.metric("Desvio-padrão", f"{s.std():.2f}")
        c4.metric("IQR", f"{q3 - q1:.2f}")
        c5.metric("Assimetria", f"{stats.skew(s):.2f}")
        c6.metric("Curtose", f"{stats.kurtosis(s):.2f}")

        left, right = st.columns(2)
        with left:
            fig = px.histogram(df, x="v", nbins=40, title=f"Distribuição de {col}")
            st.plotly_chart(fig, width="stretch")
        with right:
            fig2 = px.box(df, x="gravidade_4", y="v", title=f"{col} por gravidade",
                          category_orders={"gravidade_4": ["Sem vítimas", "Leve", "Grave (não fatal)", "Fatal"]})
            st.plotly_chart(fig2, width="stretch")

        if col in ("mortos", "feridos_graves", "feridos_leves"):
            st.info(
                "Esta variável é zero-inflacionada: IQR tende a degenerar (Q1=Q3=0). "
                "Veja a página 🚨 Anomalias para a detecção correta via z-score (ver docs/DECISIONS.md D-06)."
            )

with tab_cat:
    col = st.selectbox("Variável categórica", CATEGORICAL, index=0)
    total = query(f"SELECT count(*) n FROM acidentes_enriquecido WHERE {where}").iloc[0]["n"]
    freq = query(
        f"SELECT {col} AS categoria, count(*) n FROM acidentes_enriquecido "
        f"WHERE {where} AND {col} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"
    )
    freq["pct"] = (freq["n"] / total * 100).round(2)
    n_unique = len(freq)
    rare = int((freq["n"] < 0.01 * total).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Cardinalidade", n_unique)
    c2.metric("Categoria mais frequente", str(freq.iloc[0]["categoria"]) if not freq.empty else "—")
    c3.metric("Categorias raras (<1%)", rare)

    top_n = st.slider("Mostrar top N categorias", 5, min(40, max(5, n_unique)), min(15, n_unique) or 5)
    fig = px.bar(freq.head(top_n), x="n", y="categoria", orientation="h",
                 title=f"Top {top_n} categorias de {col}", text="pct")
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
    st.dataframe(freq, width="stretch", height=250)
