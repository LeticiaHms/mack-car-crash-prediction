"""
Otimização de hiperparâmetros (seção 9 do pedido da Etapa 3).

Estratégia: `RandomizedSearchCV` com `PredefinedSplit` — treino e validação
já existem como partições temporais separadas (`src/ml/dataset.py`), então em
vez de um k-fold aleatório (que embaralharia a ordem cronológica dentro do
treino, contradizendo a justificativa do split temporal) a busca treina em
`train` e pontua em `val`, com um único fold fixo. O conjunto de teste
continua fora da busca inteiramente — só entra em `evaluate.py`.

Métrica otimizada: F1 da classe grave (`grave_bin=1`). Justificativa (D-19):
o problema tem desbalanceamento moderado (~2,5:1) e o negócio precisa de
equilíbrio entre Recall (não deixar de sinalizar trechos de risco) e
Precision (não gerar alertas em excesso que erodem a credibilidade do
modelo) — F1 é a métrica que resume esse equilíbrio em um único número para
comparar combinações de hiperparâmetros; PR-AUC/ROC-AUC/Recall continuam
reportados lado a lado para a decisão final (`evaluate.py`), que não se
resume a uma métrica só.

Modelos otimizados: apenas os selecionados como mais promissores em
`train.py` (maior F1/PR-AUC de validação entre os candidatos não-triviais)
— não se otimiza o baseline (não tem hiperparâmetro que faça sentido) nem
necessariamente todos os candidatos, para manter o custo computacional
proporcional ao ganho esperado (ver relatório final, seção "Tuning").

Uso:
    python -m src.ml.tune modelo1 modelo2 ...
    (default: xgboost logistic_regression — ver justificativa de custo-benefício no final do arquivo)
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
from sklearn.model_selection import PredefinedSplit, RandomizedSearchCV

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import get_X_y, load_gold, temporal_split  # noqa: E402
from src.ml.models import RANDOM_STATE, get_spec  # noqa: E402
from src.ml.train import build_pipeline, evaluate_split  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

REPORT_DIR = "reports/ml"
MODELS_DIR = os.path.join(REPORT_DIR, "models")
TABLES_DIR = os.path.join(REPORT_DIR, "tables")

N_ITER = 20
SCORING = "f1"


def tune_model(name: str, Xtr, ytr, Xva, yva, Xte, yte) -> dict:
    spec = get_spec(name)
    if not spec.tuning_grid:
        raise ValueError(f"Modelo '{name}' não tem tuning_grid definido em MODEL_REGISTRY.")

    pipeline = build_pipeline(spec)

    # Métrica "antes do tuning": mesma pipeline/hiperparâmetros usados em train.py.
    t0 = time.time()
    pipeline.fit(Xtr, ytr)
    before_metrics = {
        "train": evaluate_split(pipeline, Xtr, ytr),
        "val": evaluate_split(pipeline, Xva, yva),
        "test": evaluate_split(pipeline, Xte, yte),
    }
    before_time_s = time.time() - t0

    # PredefinedSplit: -1 = treino (nunca vira validação), 0 = validação.
    X_combined = pd.concat([Xtr, Xva], axis=0, ignore_index=True)
    y_combined = pd.concat([ytr, yva], axis=0, ignore_index=True)
    test_fold = np.concatenate([np.full(len(Xtr), -1), np.zeros(len(Xva))])
    ps = PredefinedSplit(test_fold)

    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=spec.tuning_grid,
        n_iter=min(N_ITER, _grid_size(spec.tuning_grid)),
        scoring=SCORING,
        cv=ps,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        refit=False,  # refit manual abaixo, só no treino (não temos que reajustar com val incluída)
        verbose=1,
    )
    t0 = time.time()
    search.fit(X_combined, y_combined)
    search_time_s = time.time() - t0

    best_params = search.best_params_
    best_pipeline = build_pipeline(spec)
    best_pipeline.set_params(**best_params)
    t0 = time.time()
    best_pipeline.fit(Xtr, ytr)
    refit_time_s = time.time() - t0

    after_metrics = {
        "train": evaluate_split(best_pipeline, Xtr, ytr),
        "val": evaluate_split(best_pipeline, Xva, yva),
        "test": evaluate_split(best_pipeline, Xte, yte),
    }

    result = {
        "model": name,
        "scoring": SCORING,
        "cv_strategy": "PredefinedSplit(treino=-1, validação=0) — 1 fold fixo respeitando a ordem temporal",
        "param_distributions": {k: list(v) for k, v in spec.tuning_grid.items()},
        "n_candidates_tested": len(search.cv_results_["params"]),
        "best_params": {k: str(v) for k, v in best_params.items()},
        "best_score_val_f1": float(search.best_score_),
        "search_time_s": round(search_time_s, 2),
        "before_tuning": {"train_time_s": round(before_time_s, 3), "metrics": before_metrics},
        "after_tuning": {"train_time_s": round(refit_time_s, 3), "metrics": after_metrics},
        "delta_f1_val": after_metrics["val"]["f1"] - before_metrics["val"]["f1"],
        "delta_f1_test": after_metrics["test"]["f1"] - before_metrics["test"]["f1"],
    }
    logging.info(
        f"{name}: F1(val) antes={before_metrics['val']['f1']:.4f} depois={after_metrics['val']['f1']:.4f} "
        f"(Δ={result['delta_f1_val']:+.4f}) | busca={search_time_s:.1f}s"
    )

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(best_pipeline, os.path.join(MODELS_DIR, f"{name}_tuned.joblib"))
    return result


def _grid_size(grid: dict) -> int:
    size = 1
    for v in grid.values():
        size *= len(v)
    return size


def main(model_names: list[str]):
    os.makedirs(TABLES_DIR, exist_ok=True)
    gold = load_gold()
    train, val, test, _split_info = temporal_split(gold)
    Xtr, ytr = get_X_y(train)
    Xva, yva = get_X_y(val)
    Xte, yte = get_X_y(test)

    results = {}
    for name in model_names:
        results[name] = tune_model(name, Xtr, ytr, Xva, yva, Xte, yte)

    with open(os.path.join(TABLES_DIR, "tuning_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logging.info(f"Resultados do tuning salvos em {TABLES_DIR}/tuning_results.json")
    return results


if __name__ == "__main__":
    # Default: xgboost (melhor em F1/ROC-AUC/PR-AUC de validação entre os
    # candidatos, e o mais barato de treinar — 6s vs. 171s do Random Forest)
    # + logistic_regression (barato, interpretável, contraponto ao ensemble).
    # random_forest ficou fora do tuning por decisão de custo-benefício:
    # perdeu para o xgboost em toda métrica de validação treinando ~27x mais
    # devagar — ver `docs/entregas/etapa3-modelagem.md`, seção "Tuning".
    names = sys.argv[1:] if len(sys.argv) > 1 else ["xgboost", "logistic_regression"]
    main(names)
