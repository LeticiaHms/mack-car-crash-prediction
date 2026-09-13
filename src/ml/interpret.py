"""
Interpretabilidade do modelo final (seção 11 do pedido da Etapa 3).

Duas fontes de importância, deliberadamente comparadas:
1. Importância nativa do modelo (feature_importances_ para árvores/ensembles,
   coeficientes para Regressão Logística) — rápida, mas para árvores é
   calculada sobre o próprio treino (viés conhecido: infla variáveis de alta
   cardinalidade/granularidade).
2. Permutation importance sobre a VALIDAÇÃO (nunca o treino) — mede a queda
   de desempenho ao embaralhar cada feature, isolando o efeito preditivo
   real fora da amostra de treino. É a métrica priorizada na leitura do
   relatório final quando as duas divergem.

Correlação != importância preditiva != causalidade (regra 6/seção 11 do
pedido): este módulo só produz e documenta ranking; a leitura causal fica
para o relatório final, com as ressalvas explícitas.
"""
from __future__ import annotations

import json
import logging
import os
import sys

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import get_X_y, load_gold, temporal_split  # noqa: E402
from src.ml.models import RANDOM_STATE  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REPORT_DIR = "reports/ml"
TABLES_DIR = os.path.join(REPORT_DIR, "tables")


def native_importance(pipeline) -> pd.DataFrame:
    """Importância nativa: feature_importances_ (árvores) ou coeficientes
    absolutos padronizados (Regressão Logística), sobre a matriz já
    transformada (nomes reais de coluna via get_feature_names_out)."""
    model = pipeline.named_steps["model"]
    pre = pipeline.named_steps["preprocess"]
    names = pre.get_feature_names_out()

    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
        kind = "feature_importances_ (impureza/gain)"
    elif hasattr(model, "coef_"):
        values = np.abs(model.coef_[0])
        kind = "|coeficiente| (log-odds, features padronizadas)"
    else:
        raise ValueError(f"Modelo {type(model)} não expõe importância nativa.")

    df = pd.DataFrame({"feature": names, "importancia_nativa": values, "tipo_importancia": kind})
    return df.sort_values("importancia_nativa", ascending=False).reset_index(drop=True)


def permutation_importance_val(pipeline, X_val, y_val, n_repeats: int = 10) -> pd.DataFrame:
    """Permutation importance calculada sobre a VALIDAÇÃO (nunca treino nem
    teste), usando F1 como métrica de referência — mesma métrica do tuning."""
    result = permutation_importance(
        pipeline, X_val, y_val, scoring="f1", n_repeats=n_repeats,
        random_state=RANDOM_STATE, n_jobs=-1,
    )
    df = pd.DataFrame({
        "feature": X_val.columns,
        "importancia_permutacao_media": result.importances_mean,
        "importancia_permutacao_std": result.importances_std,
    })
    return df.sort_values("importancia_permutacao_media", ascending=False).reset_index(drop=True)


def main(model_path: str, model_name: str):
    import joblib

    pipeline = joblib.load(model_path)
    gold = load_gold()
    train, val, test, _info = temporal_split(gold)
    Xva, yva = get_X_y(val)

    logging.info("Calculando importância nativa...")
    native_df = native_importance(pipeline)
    native_df.to_csv(os.path.join(TABLES_DIR, f"feature_importance_native_{model_name}.csv"), index=False)

    logging.info("Calculando permutation importance sobre a validação (pode levar alguns minutos)...")
    perm_df = permutation_importance_val(pipeline, Xva, yva)
    perm_df.to_csv(os.path.join(TABLES_DIR, f"feature_importance_permutation_{model_name}.csv"), index=False)

    logging.info(f"Top 15 nativa:\n{native_df.head(15).to_string(index=False)}")
    logging.info(f"Top 15 permutação (nível de feature original, não one-hot):\n{perm_df.head(15).to_string(index=False)}")
    return native_df, perm_df


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "reports/ml/models/xgboost_tuned.joblib"
    name = sys.argv[2] if len(sys.argv) > 2 else "xgboost_tuned"
    main(path, name)
