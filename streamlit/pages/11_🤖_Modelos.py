import json
import os

import streamlit as st

st.set_page_config(page_title="Modelos", page_icon="🤖", layout="wide")
st.title("🤖 Exploração dos Modelos")

MODELS_DIR = "models"
METRICS_FILE = os.path.join(MODELS_DIR, "metrics.json")

st.caption(
    "Esta página carrega artefatos já treinados; ela NUNCA treina ou retreina um modelo ao mudar um "
    "filtro (regra da skill `streamlit-ml-eda`), e nunca inventa métricas que não foram calculadas."
)

if not os.path.isdir(MODELS_DIR) or not os.path.exists(METRICS_FILE):
    st.warning(
        "⚠️ **Nenhum modelo treinado encontrado ainda.** Esta etapa do projeto "
        "(`skill/machine-learning.md` + `skill/model-evaluation.md`) ainda não foi executada — "
        "o escopo desta tarefa foi a EDA (docs/specs/eda/EDA.md, docs/ANALYSIS_LOG.md, docs/DECISIONS.md)."
    )
    st.markdown(
        """
        **O que esta página vai mostrar assim que a etapa de ML rodar** (lendo `models/metrics.json`
        e os artefatos salvos em `models/`, sem recalcular nada aqui):
        - nome/versão do modelo e da baseline (Dummy Classifier);
        - Precision, Recall, F1-score, ROC-AUC e PR-AUC da classe grave (`grave_bin=1`);
        - matriz de confusão e curva PR/ROC;
        - importância de features (quando suportado pelo modelo), rotulada como *importância
          preditiva*, nunca como *efeito causal*.

        Para gerar esses artefatos, implemente e execute o pipeline de treinamento
        (`src/train.py`, a ser criado seguindo `skill/machine-learning.md`), salvando as métricas
        em `models/metrics.json`.
        """
    )
    st.stop()

with open(METRICS_FILE, "r", encoding="utf-8") as f:
    metrics = json.load(f)

st.subheader("Comparação de modelos")
st.json(metrics)
st.info(
    "Métricas carregadas de models/metrics.json — nenhum valor foi calculado nesta página. "
    "Accuracy nunca deve ser lida isoladamente; priorize Recall/F1/PR-AUC da classe grave."
)
