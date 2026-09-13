import pandas as pd
import plotly.express as px
import streamlit as st

from common import get_connection, query, render_sidebar_filters, show_active_filters

st.title("🧠 Análise das Features para Machine Learning")
st.caption(
    "Para cada candidato a feature: 'essa informação estaria disponível no momento em que a previsão "
    "precisa ser feita?' Se não, é marcada como risco de data leakage e não deve virar feature direta "
    "(skill `eda`/`feature-engineering`; ver docs/analises/ANALYSIS_LOG.md A-18 e docs/decisoes/DECISIONS.md D-07)."
)

where, selections = render_sidebar_filters()
show_active_filters(selections)
con = get_connection()

LEAKAGE_MAP = [
    ("mortos", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("feridos_leves", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("feridos_graves", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("feridos", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("ilesos", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("ignorados", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("pessoas", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("veiculos", "Resultado do próprio acidente", "❌ Não usar direto — só p/ target ou histórico"),
    ("classificacao_acidente", "Resultado do próprio acidente", "❌ Não usar — define o target"),
    ("tipo_acidente", "Apurado sobre o acidente ocorrido", "❌ Não usar direto — só p/ caracterizar histórico do trecho"),
    ("causa_acidente", "Apurado após investigação", "❌ Não usar direto — só p/ caracterizar histórico do trecho"),
    ("condicao_metereologica", "Observação do momento do acidente", "⚠️ Não conhecida com certeza no futuro — usar só como clima histórico típico"),
    ("uf", "Atributo do trecho, conhecido a priori", "✅ Uso seguro (estrutural)"),
    ("br", "Atributo do trecho, conhecido a priori", "✅ Uso seguro (estrutural)"),
    ("km", "Atributo do trecho, conhecido a priori", "✅ Uso seguro (estrutural)"),
    ("municipio", "Atributo do trecho, conhecido a priori", "✅ Uso seguro (estrutural)"),
    ("latitude", "Atributo do trecho, conhecido a priori", "✅ Uso seguro (estrutural)"),
    ("longitude", "Atributo do trecho, conhecido a priori", "✅ Uso seguro (estrutural)"),
    ("tipo_pista", "Característica física estável da via", "✅ Uso seguro (estrutural)"),
    ("tracado_via", "Característica física estável da via", "✅ Uso seguro (estrutural)"),
    ("sentido_via", "Característica física estável da via", "✅ Uso seguro (estrutural)"),
    ("uso_solo", "Característica estável da via", "✅ Uso seguro (estrutural)"),
    ("data_inversa/ano/mes", "Conhecido a priori para o período previsto", "✅ Uso seguro (temporal)"),
    ("dia_semana", "Conhecido a priori para o período previsto", "✅ Uso seguro (temporal)"),
    ("horario/hora", "Conhecido a priori para o período previsto", "✅ Uso seguro (temporal)"),
    ("fase_dia", "Derivável de hora/data (proxy de iluminação)", "✅ Uso seguro (temporal)"),
    ("regional/delegacia/uop", "Identifica a unidade da PRF, não o local do acidente", "⚠️ Não recomendado — baixo valor, redundante com uf/municipio"),
]
leak_df = pd.DataFrame(LEAKAGE_MAP, columns=["coluna", "por que", "veredito"])

with st.expander("🗺️ Mapa de leakage (conceitual, não estatístico) — ver tabela completa", expanded=False):
    st.dataframe(leak_df, width="stretch", height=420)

st.divider()
st.subheader("Diagnóstico por coluna candidata")

SAFE_COLS = ["uf", "br", "km", "municipio", "tipo_pista", "tracado_via", "sentido_via", "uso_solo",
             "ano", "mes", "dia_semana", "hora", "fase_dia"]
RISKY_COLS = ["tipo_acidente", "causa_acidente", "condicao_metereologica"]

col = st.selectbox("Coluna", SAFE_COLS + RISKY_COLS)
is_risky = col in RISKY_COLS
if is_risky:
    st.warning(f"⚠️ `{col}` é pós-evento/observacional — diagnóstico abaixo é só para entender a variável, NÃO uma recomendação de uso direto.")
else:
    st.success(f"✅ `{col}` está disponível a priori para o momento da previsão.")

total = query(f"SELECT count(*) n FROM acidentes_enriquecido WHERE {where}").iloc[0]["n"]
missing = query(f"SELECT sum(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) n FROM acidentes_enriquecido WHERE {where}").iloc[0]["n"]
n_unique = query(f"SELECT count(DISTINCT {col}) n FROM acidentes_enriquecido WHERE {where}").iloc[0]["n"]

c1, c2, c3 = st.columns(3)
c1.metric("Missing", f"{missing} ({missing/total*100:.2f}%)" if total else "—")
c2.metric("Cardinalidade", int(n_unique))
c3.metric("Tipo", "categórica" if n_unique < 200 or not str(col) in ("km", "latitude", "longitude") else "numérica")

dist_left, dist_right = st.columns(2)
with dist_left:
    dist = query(f"SELECT {col} AS v, count(*) n FROM acidentes_enriquecido WHERE {where} AND {col} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 25")
    fig = px.bar(dist, x="v", y="n", title=f"Distribuição de {col} (top 25)")
    st.plotly_chart(fig, width="stretch")
with dist_right:
    rel = query(
        f"SELECT {col} AS v, round(100.0*sum(grave_bin)/count(*),2) pct_grave, count(*) n "
        f"FROM acidentes_enriquecido WHERE {where} AND {col} IS NOT NULL GROUP BY 1 ORDER BY n DESC LIMIT 25"
    )
    fig2 = px.bar(rel, x="v", y="pct_grave", title=f"% grave/fatal por valor de {col} (top 25 por volume)")
    st.plotly_chart(fig2, width="stretch")

st.warning(
    "⚠️ Relação com o target mostrada apenas para caracterização exploratória — nunca use associação alta "
    "isoladamente como critério de inclusão de feature (regra explícita da tarefa)."
)
