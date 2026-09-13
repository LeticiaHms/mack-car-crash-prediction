"""
Registro dos modelos treinados na Etapa 3 — baseline + candidatos.

Cada entrada documenta, além do estimador e do grid de tuning: complexidade,
interpretabilidade, vantagens e limitações — exigidos na seção 5 do pedido
da Etapa 3 e usados tal como estão em `train.py`/no relatório final, para
nunca haver dois lugares descrevendo o mesmo modelo de forma diferente.

Todos usam `random_state=42` (reprodutibilidade) e `class_weight`/
`scale_pos_weight` para lidar com o desbalanceamento (28% de `grave_bin=1`)
sem reamostragem — decisão justificada em D-16 (ver relatório): o
desbalanceamento é moderado (~2,5:1), então ajustar o peso da perda é
suficiente e mais simples que SMOTE/undersampling, que alterariam a
distribuição do treino sem necessidade.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

RANDOM_STATE = 42


@dataclass
class ModelSpec:
    name: str
    build: Callable[[], Any]
    complexity: str
    interpretability: str
    advantages: str
    limitations: str
    expected_behavior: str
    tuning_grid: dict = field(default_factory=dict)  # vazio => não é candidato a tuning


MODEL_REGISTRY: list[ModelSpec] = [
    ModelSpec(
        name="baseline_dummy",
        build=lambda: DummyClassifier(strategy="most_frequent"),
        complexity="Nula — memoriza a classe majoritária.",
        interpretability="Total (regra trivial: sempre prevê 'não grave').",
        advantages="Custo zero; define o piso de desempenho que qualquer modelo precisa superar.",
        limitations="Recall/F1 da classe grave sempre 0 — inútil para o negócio, serve só de referência.",
        expected_behavior=(
            "Accuracy alta (~72%, a própria taxa da classe majoritária) mas Recall/F1/ROC-AUC "
            "da classe grave nulos — evidência direta de por que Accuracy sozinha engana aqui."
        ),
    ),
    ModelSpec(
        name="logistic_regression",
        build=lambda: LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
        ),
        complexity="Baixa — fronteira de decisão linear no espaço das features transformadas.",
        interpretability="Alta — coeficientes com sinal e magnitude interpretáveis (log-odds).",
        advantages="Rápida, estável, boa referência interpretável; funciona bem quando o sinal é aproximadamente aditivo/linear.",
        limitations="Não captura interações não-lineares entre features (ex.: hora x tipo_pista) sem engenharia manual.",
        expected_behavior=(
            "Desempenho moderado, próximo entre treino/validação/teste (baixa variância, "
            "pouco propensa a overfitting); teto de desempenho mais baixo que os modelos de árvore "
            "se houver interações relevantes não-lineares na base."
        ),
        tuning_grid={"model__C": [0.01, 0.1, 1.0, 3.0, 10.0]},
    ),
    ModelSpec(
        name="decision_tree",
        build=lambda: DecisionTreeClassifier(
            max_depth=8, min_samples_leaf=50, class_weight="balanced", random_state=RANDOM_STATE,
        ),
        complexity="Média — profundidade limitada (max_depth=8) para conter overfitting; sem limite explodiria.",
        interpretability="Alta — caminho de decisão auditável nó a nó; a versão rasa pode ser desenhada/lida diretamente.",
        advantages="Captura interações e não-linearidades sem transformação manual; não exige escala das features.",
        limitations="Alta variância — sensível a pequenas mudanças no treino; fronteiras em degrau (menos suave que ensembles).",
        expected_behavior=(
            "Sem limitar profundidade, memoriza o treino (overfitting clássico); com max_depth=8 "
            "espera-se lacuna treino-validação moderada, ainda maior que a da Regressão Logística."
        ),
        tuning_grid={
            "model__max_depth": [4, 6, 8, 12, None],
            "model__min_samples_leaf": [20, 50, 100, 200],
        },
    ),
    ModelSpec(
        name="random_forest",
        build=lambda: RandomForestClassifier(
            n_estimators=300, max_depth=16, min_samples_leaf=5,
            class_weight="balanced_subsample", random_state=RANDOM_STATE, n_jobs=-1,
        ),
        complexity="Alta — 300 árvores; custo de treino/inferência maior, mas paralelizável.",
        interpretability="Média — sem caminho único de decisão, mas expõe feature_importances_ nativamente (impureza) e aceita permutation importance.",
        advantages="Reduz a variância da árvore única (bagging); robusta a outliers e a features irrelevantes; poucos hiperparâmetros críticos.",
        limitations="Modelo maior em disco/memória; importância por impureza pode inflar variáveis de alta cardinalidade (viés conhecido — mitigado com permutation importance).",
        expected_behavior=(
            "Deve superar a árvore única em validação/teste com lacuna treino-teste menor "
            "(variância reduzida pelo bagging); ainda pode overfitar se as árvores individuais forem profundas demais."
        ),
        tuning_grid={
            "model__n_estimators": [200, 300, 500],
            "model__max_depth": [8, 16, 24, None],
            "model__min_samples_leaf": [1, 5, 10, 20],
        },
    ),
    ModelSpec(
        name="xgboost",
        build=lambda: XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=2.54,  # ~= negativos/positivos no treino (156294/61613), mesmo princípio do class_weight="balanced"
            eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1,
            tree_method="hist",
        ),
        complexity="Alta — boosting sequencial de 300 árvores rasas; mais hiperparâmetros para ajustar que Random Forest.",
        interpretability="Média — feature_importances_ nativo (gain/weight) e compatível com permutation importance; sem caminho único de decisão.",
        advantages="Em geral o melhor desempenho bruto entre os candidatos por corrigir iterativamente os erros dos estimadores anteriores; robusto a features irrelevantes e a diferentes escalas.",
        limitations="Maior custo de treino/tuning; mais fácil overfitar sem controlar profundidade/learning_rate/regularização; menos transparente que a árvore única.",
        expected_behavior=(
            "Espera-se o melhor desempenho de validação entre os candidatos, à custa de maior "
            "tempo de treino e maior atenção ao gap treino-validação (boosting overfita se "
            "deixado rodar demais sem controle de profundidade/learning_rate)."
        ),
        tuning_grid={
            "model__n_estimators": [200, 300, 500],
            "model__max_depth": [3, 4, 6, 8],
            "model__learning_rate": [0.03, 0.05, 0.1, 0.2],
            "model__scale_pos_weight": [1.0, 2.0, 2.55],
        },
    ),
]


def get_spec(name: str) -> ModelSpec:
    for spec in MODEL_REGISTRY:
        if spec.name == name:
            return spec
    raise KeyError(f"Modelo '{name}' não encontrado em MODEL_REGISTRY.")
