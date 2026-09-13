"""
Treina o baseline e os modelos candidatos (`src/ml/models.py`) sobre o split
temporal (`src/ml/dataset.py`), avalia em treino/validação/teste com o mesmo
protocolo para todos, e grava os artefatos de comparação em `reports/ml/`.

Regra de ouro (seção 18 do pedido): o conjunto de teste NUNCA participa de
decisão nesta etapa — é calculado e registrado, mas a escolha do(s)
modelo(s) para tuning (`tune.py`) usa exclusivamente treino/validação.

Uso:
    python -m src.ml.train
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import TARGET, get_X_y, load_gold, temporal_split  # noqa: E402
from src.ml.models import MODEL_REGISTRY, ModelSpec  # noqa: E402
from src.ml.preprocessing import build_preprocessor  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REPORT_DIR = "reports/ml"
MODELS_DIR = os.path.join(REPORT_DIR, "models")
TABLES_DIR = os.path.join(REPORT_DIR, "tables")


def build_pipeline(spec: ModelSpec) -> Pipeline:
    return Pipeline([("preprocess", build_preprocessor()), ("model", spec.build())])


def compute_metrics(y_true, y_pred, y_proba) -> dict:
    """Métricas padronizadas (seção 6 do pedido): a Accuracy é reportada mas
    nunca usada isoladamente — Recall/F1/ROC-AUC/PR-AUC da classe grave
    (`pos_label=1`) são as métricas de decisão, conforme D-02/skill
    `model-evaluation`."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
    except ValueError:
        metrics["roc_auc"] = None
    try:
        metrics["pr_auc"] = float(average_precision_score(y_true, y_proba))
    except ValueError:
        metrics["pr_auc"] = None
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics["confusion_matrix"] = cm.tolist()  # [[TN, FP], [FN, TP]]
    return metrics


def evaluate_split(pipeline: Pipeline, X, y) -> dict:
    y_pred = pipeline.predict(X)
    if hasattr(pipeline.named_steps["model"], "predict_proba"):
        y_proba = pipeline.predict_proba(X)[:, 1]
    else:
        y_proba = y_pred.astype(float)
    return compute_metrics(y, y_pred, y_proba)


def train_one(spec: ModelSpec, Xtr, ytr, Xva, yva, Xte, yte) -> dict:
    pipeline = build_pipeline(spec)
    t0 = time.time()
    pipeline.fit(Xtr, ytr)
    train_time_s = time.time() - t0

    result = {
        "model": spec.name,
        "train_time_s": round(train_time_s, 3),
        "complexity": spec.complexity,
        "interpretability": spec.interpretability,
        "advantages": spec.advantages,
        "limitations": spec.limitations,
        "expected_behavior": spec.expected_behavior,
        "params": {k: str(v) for k, v in pipeline.named_steps["model"].get_params().items()},
        "metrics": {
            "train": evaluate_split(pipeline, Xtr, ytr),
            "val": evaluate_split(pipeline, Xva, yva),
            "test": evaluate_split(pipeline, Xte, yte),
        },
    }
    logging.info(
        f"{spec.name:20s} treino={train_time_s:6.2f}s "
        f"F1(val)={result['metrics']['val']['f1']:.4f} "
        f"ROC-AUC(val)={result['metrics']['val']['roc_auc']:.4f} "
        f"PR-AUC(val)={result['metrics']['val']['pr_auc']:.4f}"
    )
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(pipeline, os.path.join(MODELS_DIR, f"{spec.name}.joblib"))
    return result, pipeline


def build_comparison_table(all_results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in all_results:
        rows.append({
            "modelo": r["model"],
            "f1_treino": r["metrics"]["train"]["f1"],
            "f1_validacao": r["metrics"]["val"]["f1"],
            "f1_teste": r["metrics"]["test"]["f1"],
            "recall_validacao": r["metrics"]["val"]["recall"],
            "precision_validacao": r["metrics"]["val"]["precision"],
            "roc_auc_validacao": r["metrics"]["val"]["roc_auc"],
            "pr_auc_validacao": r["metrics"]["val"]["pr_auc"],
            "accuracy_validacao": r["metrics"]["val"]["accuracy"],
            "gap_treino_teste_f1": r["metrics"]["train"]["f1"] - r["metrics"]["test"]["f1"],
            "tempo_treino_s": r["train_time_s"],
            "complexidade": r["complexity"],
            "interpretabilidade": r["interpretability"],
        })
    return pd.DataFrame(rows)


def main():
    os.makedirs(TABLES_DIR, exist_ok=True)

    gold = load_gold()
    train, val, test, split_info = temporal_split(gold)
    Xtr, ytr = get_X_y(train)
    Xva, yva = get_X_y(val)
    Xte, yte = get_X_y(test)

    logging.info(f"Split: treino={len(Xtr)} validação={len(Xva)} teste={len(Xte)}")

    all_results = []
    for spec in MODEL_REGISTRY:
        result, _pipeline = train_one(spec, Xtr, ytr, Xva, yva, Xte, yte)
        all_results.append(result)

    with open(os.path.join(TABLES_DIR, "metrics_per_model.json"), "w", encoding="utf-8") as f:
        json.dump({"split_info": split_info, "target": TARGET, "results": all_results}, f, indent=2, ensure_ascii=False)

    comparison = build_comparison_table(all_results)
    comparison.to_csv(os.path.join(TABLES_DIR, "model_comparison.csv"), index=False)
    logging.info(f"Comparação salva em {TABLES_DIR}/model_comparison.csv")
    print(comparison.to_string(index=False))

    return all_results, split_info


if __name__ == "__main__":
    main()
