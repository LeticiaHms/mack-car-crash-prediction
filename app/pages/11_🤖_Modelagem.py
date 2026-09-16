import os
import sys

import pandas as pd
import streamlit as st

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from src.ml.modelagem import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES  # noqa: E402

REPORT_DIR = "reports/ml"

st.title("🤖 Modelagem — previsão de gravidade de acidentes")
st.caption(
    "Esta página mostra os resultados da Etapa 3 (Machine Learning): comparação de 3 modelos de "
    "classificação treinados para prever se um acidente será grave/fatal. Os números vêm de "
    "`reports/ml/` — nada é recalculado ao vivo. Detalhes completos em `docs/entregas/etapa3-modelagem.md`."
)

metrics_path = os.path.join(REPORT_DIR, "metrics.csv")
if not os.path.exists(metrics_path):
    st.warning("Artefatos da Etapa 3 ainda não gerados. Rode `python -m src.ml.modelagem` antes de abrir esta página.")
    st.stop()


@st.cache_data(show_spinner=False)
def load_metrics() -> pd.DataFrame:
    return pd.read_csv(metrics_path, index_col="Modelo")


metrics_df = load_metrics()
best_model = metrics_df["F1"].idxmax()

# ============================================================================
# 1. O problema, em uma frase
# ============================================================================
st.header("🎯 O problema")
st.write(
    "Prever se um acidente será **grave/fatal** (`grave_bin=1`) ou **não grave** (`grave_bin=0`), "
    "usando só informações conhecidas **antes** do desfecho (localização, tipo de pista, horário...) — "
    "nunca o número de feridos/mortos, que só existe depois."
)

# ============================================================================
# 2. Resultado em uma frase + tabela comparativa
# ============================================================================
st.header("🏆 Resultado")
best_row = metrics_df.loc[best_model]
st.success(
    f"O modelo com melhor equilíbrio entre acerto de casos graves e falsos alarmes (F1) foi o "
    f"**{best_model}**: identifica corretamente **{best_row['Recall']*100:.0f} de cada 100** acidentes "
    f"graves reais do conjunto de teste, com **{best_row['Precision']*100:.0f}%** dos alertas de risco "
    f"se confirmando."
)

st.dataframe(
    metrics_df.style.format("{:.4f}").highlight_max(axis=0, color="#d4f0d4"),
    width="stretch",
)

st.image(os.path.join(REPORT_DIR, "metric_comparison.png"), caption="Comparação das 5 métricas entre os 3 modelos (conjunto de teste).")

with st.expander("📖 O que significa cada métrica?"):
    glossario = [
        ("Accuracy", "Porcentagem de acertos totais. CUIDADO: sozinha ela engana — como só ~28% dos "
                      "acidentes são graves, um modelo que sempre chuta 'não grave' já acertaria ~72%."),
        ("Precision", "Das vezes que o modelo disse 'vai ser grave', quantas realmente foram."),
        ("Recall", "De todos os acidentes graves que aconteceram de fato, quantos o modelo identificou."),
        ("F1", "Uma nota única que equilibra Precision e Recall — só é alta quando os dois são razoáveis."),
        ("ROC-AUC", "Vai de 0,50 (chute aleatório) a 1,00 (perfeito); mede a capacidade geral do modelo "
                     "de separar acidente grave de não grave."),
    ]
    for termo, explicacao in glossario:
        st.markdown(f"**{termo}** — {explicacao}")

st.divider()

# ============================================================================
# 3. Distribuição do alvo e split
# ============================================================================
st.header("📚 Os dados")
c1, c2 = st.columns(2)
c1.image(os.path.join(REPORT_DIR, "class_distribution.png"), caption="Distribuição da variável alvo (grave_bin) na base completa.")
with c2:
    st.write(
        "Os dados foram divididos por **corte de data** (não aleatório) em treino (~70%), validação "
        "(~15%) e teste (~15%) — o modelo é sempre avaliado prevendo o futuro a partir do passado, "
        "nunca misturando as fatias de tempo. Sem busca de hiperparâmetros nesta etapa, a validação "
        "só serve como checagem intermediária; os números desta página vêm do **teste**, nunca usado "
        "para treinar ou ajustar nada."
    )
    st.write(
        f"**{len(CATEGORICAL_FEATURES) + len(NUMERIC_FEATURES) + len(BOOLEAN_FEATURES)} features** "
        f"utilizadas: {len(CATEGORICAL_FEATURES)} categóricas, {len(NUMERIC_FEATURES)} numéricas e "
        f"{len(BOOLEAN_FEATURES)} booleanas — todas conhecidas *antes* do desfecho do acidente."
    )

with st.expander("🔬 Quais características o modelo usa?"):
    st.markdown(f"**Categóricas:** {', '.join(CATEGORICAL_FEATURES)}")
    st.markdown(f"**Numéricas:** {', '.join(NUMERIC_FEATURES)}")
    st.markdown(f"**Booleanas:** {', '.join(BOOLEAN_FEATURES)}")
    st.caption(
        "Não entram como feature: `mortos`, `feridos_*`, `pessoas`, `veiculos`, "
        "`classificacao_acidente`, `causa_acidente`, `tipo_acidente` (só existem depois do acidente) "
        "nem `municipio`/`geocoord_valido` (alta cardinalidade / constante — descartadas por simplicidade)."
    )

st.divider()

# ============================================================================
# 4. Matriz de confusão e curva ROC
# ============================================================================
st.header("🔍 Como cada modelo erra e acerta")
st.image(os.path.join(REPORT_DIR, "confusion_matrix.png"), caption="Matriz de confusão dos 3 modelos no conjunto de teste.")
st.image(os.path.join(REPORT_DIR, "roc_curve.png"), caption="Curva ROC comparando os 3 modelos — quanto mais afastada da linha pontilhada, melhor.")

st.divider()

# ============================================================================
# 5. Conclusão
# ============================================================================
st.header("🧠 O que os resultados indicam")
st.write(
    "Os 3 modelos ficam próximos entre si em todas as métricas — nenhum vence com folga. "
    "Isso sugere que o teto de desempenho está no **conteúdo informativo das features disponíveis** "
    "(localização, tipo de pista, horário), não na escolha do algoritmo: as características mais "
    "fortemente associadas à gravidade do acidente (tipo/causa do acidente) foram corretamente "
    "excluídas por serem conhecidas só depois do desfecho (*data leakage*)."
)
st.caption(
    "⚠️ Importância de feature (nas árvores) ou coeficiente (na Regressão Logística) indica associação "
    "usada pelo modelo, não causalidade."
)

st.divider()
st.caption(
    "📄 Relatório técnico completo: `docs/entregas/etapa3-modelagem.md`. Código: `src/ml/modelagem.py`."
)
