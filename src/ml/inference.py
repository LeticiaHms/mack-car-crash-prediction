"""
Pipeline de inferência (seção 14 do pedido da Etapa 3) — aplica o modelo
final em dados novos, sempre pelo mesmo caminho:

    novos dados -> validação de schema -> pré-processamento (o MESMO
    ColumnTransformer ajustado no treino, empacotado dentro do .joblib) ->
    modelo treinado -> probabilidade -> faixa de risco -> resultado

O pré-processamento nunca é reajustado aqui: o `Pipeline` salvo por
`train.py`/`tune.py` já contém o `ColumnTransformer` com os parâmetros
aprendidos no treino (médias/medianas para imputação, categorias do
one-hot, frequências de município) — reaplicar `fit` em dados novos
reintroduziria exatamente o vazamento que o resto do projeto evita.

Faixas de risco: tercis da distribuição de probabilidade prevista no
conjunto de VALIDAÇÃO do modelo final (nunca do teste) — ver
`reports/ml/tables/risk_thresholds.json`, gerado por `evaluate.py`.
Fallback de 1/3 e 2/3 é usado apenas se o arquivo de thresholds não existir
(ex.: uso do módulo antes de `evaluate.py` ter rodado).

Uso:
    from src.ml.inference import load_pipeline, predict_risk
    pipeline = load_pipeline("reports/ml/models/xgboost_tuned.joblib")
    resultado = predict_risk(pipeline, novos_dados_df)
"""
from __future__ import annotations

import json
import os
import sys

import joblib
import pandas as pd

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import FEATURE_COLUMNS  # noqa: E402

RISK_THRESHOLDS_PATH = "reports/ml/tables/risk_thresholds.json"
DEFAULT_THRESHOLDS = {"baixo_alto": 0.3333, "medio_alto": 0.6667}  # fallback: tercis ingênuos de [0,1]


class SchemaError(ValueError):
    """Dados novos não têm as colunas exigidas pelo pipeline treinado."""


def load_pipeline(path: str):
    return joblib.load(path)


def validate_schema(df: pd.DataFrame) -> None:
    """Falha ruidosamente (em vez de silenciosamente inventar/zerar) se
    faltar alguma feature exigida pelo pré-processamento treinado."""
    missing = set(FEATURE_COLUMNS) - set(df.columns)
    if missing:
        raise SchemaError(
            f"Dados novos sem as colunas exigidas: {sorted(missing)}. "
            f"Esperado (mínimo): {FEATURE_COLUMNS}"
        )


def _load_thresholds() -> dict:
    if os.path.exists(RISK_THRESHOLDS_PATH):
        with open(RISK_THRESHOLDS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_THRESHOLDS


def _risk_band(prob: float, thresholds: dict) -> str:
    if prob < thresholds["baixo_alto"]:
        return "BAIXO"
    if prob < thresholds["medio_alto"]:
        return "MÉDIO"
    return "ALTO"


def predict_risk(pipeline, df: pd.DataFrame) -> pd.DataFrame:
    """Recebe um DataFrame com (pelo menos) `FEATURE_COLUMNS`, valida o
    schema, aplica o pipeline treinado (pré-processamento + modelo) e
    devolve probabilidade + faixa de risco por linha, preservando o índice
    original de `df` para rastreabilidade."""
    validate_schema(df)
    X = df[FEATURE_COLUMNS]
    proba = pipeline.predict_proba(X)[:, 1]
    thresholds = _load_thresholds()

    out = df.copy()
    out["probabilidade_grave"] = proba
    out["risco"] = [_risk_band(p, thresholds) for p in proba]
    return out


if __name__ == "__main__":
    # Demonstração mínima: reaplica o pipeline final a uma amostra da própria
    # Gold, só para validar que o fluxo roda ponta a ponta (não é avaliação).
    from src.ml.dataset import load_gold

    model_path = sys.argv[1] if len(sys.argv) > 1 else "reports/ml/models/xgboost_tuned.joblib"
    pipeline = load_pipeline(model_path)
    sample = load_gold().sample(5, random_state=42)
    result = predict_risk(pipeline, sample)
    print(result[["uf", "municipio", "br", "hora", "probabilidade_grave", "risco", "grave_bin"]])
