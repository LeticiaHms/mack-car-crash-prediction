"""
Avaliação final (seção 10 do pedido da Etapa 3) — roda por último, depois de
`train.py` e `tune.py`, e é a ÚNICA etapa em que o conjunto de TESTE é usado
para reportar (nunca para decidir hiperparâmetro ou arquitetura).

Produz:
- `reports/ml/tables/final_comparison.csv`      -> todos os modelos (baseline,
  candidatos e versões com tuning) lado a lado em treino/validação/teste.
- `reports/ml/tables/risk_thresholds.json`       -> tercis de probabilidade
  do modelo final sobre a VALIDAÇÃO, usados por `inference.py` para BAIXO/
  MÉDIO/ALTO.
- `reports/ml/figures/*.png`                     -> os gráficos obrigatórios
  (seção 13 do pedido), via `plots.py`.

A escolha do modelo final NÃO é feita aqui por argmax de métrica — é uma
decisão registrada em `docs/entregas/etapa3-modelagem.md` (seção "Avaliação
final"), que pondera desempenho, generalização, custo e interpretabilidade
usando exatamente os números que este script calcula.

Uso:
    python -m src.ml.evaluate
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sys

import joblib
import numpy as np
import pandas as pd

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import get_X_y, load_gold, temporal_split  # noqa: E402
from src.ml.plots import (  # noqa: E402
    plot_class_distribution, plot_confusion_matrix, plot_feature_importance,
    plot_metric_comparison, plot_overfitting_gap, plot_pr_curves, plot_roc_curves,
)
from src.ml.train import evaluate_split  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REPORT_DIR = "reports/ml"
MODELS_DIR = os.path.join(REPORT_DIR, "models")
TABLES_DIR = os.path.join(REPORT_DIR, "tables")
FINAL_MODEL_NAME = "xgboost_tuned"  # ver justificativa no relatório final


def load_all_pipelines() -> dict:
    pipelines = {}
    for path in sorted(glob.glob(os.path.join(MODELS_DIR, "*.joblib"))):
        name = os.path.splitext(os.path.basename(path))[0]
        pipelines[name] = joblib.load(path)
    return pipelines


def build_final_comparison(pipelines: dict, Xtr, ytr, Xva, yva, Xte, yte) -> pd.DataFrame:
    rows = []
    for name, pipeline in pipelines.items():
        m_tr = evaluate_split(pipeline, Xtr, ytr)
        m_va = evaluate_split(pipeline, Xva, yva)
        m_te = evaluate_split(pipeline, Xte, yte)
        rows.append({
            "modelo": name,
            "f1_treino": m_tr["f1"], "f1_validacao": m_va["f1"], "f1_teste": m_te["f1"],
            "recall_teste": m_te["recall"], "precision_teste": m_te["precision"],
            "roc_auc_teste": m_te["roc_auc"], "pr_auc_teste": m_te["pr_auc"],
            "accuracy_teste": m_te["accuracy"],
            "gap_treino_teste_f1": m_tr["f1"] - m_te["f1"],
            "gap_val_teste_f1": m_va["f1"] - m_te["f1"],
        })
    return pd.DataFrame(rows).sort_values("f1_teste", ascending=False).reset_index(drop=True)


def compute_risk_thresholds(pipeline, X_val) -> dict:
    """Tercis da probabilidade prevista NA VALIDAÇÃO (nunca no teste) — usados
    por `inference.py` para bandas BAIXO/MÉDIO/ALTO em dados novos."""
    proba = pipeline.predict_proba(X_val)[:, 1]
    t1, t2 = np.quantile(proba, [1 / 3, 2 / 3])
    return {"baixo_alto": float(t1), "medio_alto": float(t2)}


def main():
    os.makedirs(TABLES_DIR, exist_ok=True)
    gold = load_gold()
    train, val, test, split_info = temporal_split(gold)
    Xtr, ytr = get_X_y(train)
    Xva, yva = get_X_y(val)
    Xte, yte = get_X_y(test)

    pipelines = load_all_pipelines()
    logging.info(f"Modelos carregados: {list(pipelines.keys())}")

    # --- Comparação final (treino/val/teste, todos os modelos) -----------
    final_comparison = build_final_comparison(pipelines, Xtr, ytr, Xva, yva, Xte, yte)
    final_comparison.to_csv(os.path.join(TABLES_DIR, "final_comparison.csv"), index=False)
    print(final_comparison.to_string(index=False))

    # --- Thresholds de risco do modelo final, sobre a validação ----------
    final_pipeline = pipelines[FINAL_MODEL_NAME]
    thresholds = compute_risk_thresholds(final_pipeline, Xva)
    with open(os.path.join(TABLES_DIR, "risk_thresholds.json"), "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2)
    logging.info(f"Thresholds de risco (validação, modelo {FINAL_MODEL_NAME}): {thresholds}")

    # --- Gráficos obrigatórios --------------------------------------------
    logging.info("Gerando gráficos...")
    plot_class_distribution(ytr, yva, yte)

    y_pred_final_test = final_pipeline.predict(Xte)
    plot_confusion_matrix(yte, y_pred_final_test, FINAL_MODEL_NAME, "teste")

    baseline_and_candidates = {
        k: v for k, v in pipelines.items()
        if k in ("baseline_dummy", "logistic_regression", "decision_tree", "random_forest", "xgboost")
    }
    plot_roc_curves(baseline_and_candidates, Xte, yte, "teste")
    plot_pr_curves(baseline_and_candidates, Xte, yte, "teste")

    # comparação/overfitting usam o metrics_per_model.json de train.py (antes do tuning)
    with open(os.path.join(TABLES_DIR, "metrics_per_model.json"), encoding="utf-8") as f:
        train_results = json.load(f)["results"]
    comp_df = pd.DataFrame([{
        "modelo": r["model"],
        "f1_treino": r["metrics"]["train"]["f1"],
        "f1_validacao": r["metrics"]["val"]["f1"],
        "f1_teste": r["metrics"]["test"]["f1"],
        "gap_treino_teste_f1": r["metrics"]["train"]["f1"] - r["metrics"]["test"]["f1"],
    } for r in train_results])
    plot_metric_comparison(comp_df)
    plot_overfitting_gap(comp_df)

    logging.info("Avaliação final concluída.")
    return final_comparison, thresholds


if __name__ == "__main__":
    main()
