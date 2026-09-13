"""
Orquestrador único da Etapa 3 (mesmo papel de `src/jobs/build_database.py`
para a Etapa 1/2): roda, na ordem, todo o pipeline de Machine Learning e
deixa `reports/ml/` completo e reprodutível a partir de `gold.dataset_ml`.

    split -> treino (baseline + candidatos) -> tuning (mais promissores)
    -> avaliação final (teste) -> interpretabilidade (modelo final)
    -> viés/desbalanceamento (modelo final)

Uso:
    python -m src.ml.run_all
"""
from __future__ import annotations

import logging

from src.ml import bias, evaluate, interpret, train, tune

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    logging.info("=== 1/5 Treino: baseline + candidatos ===")
    train.main()

    logging.info("=== 2/5 Tuning: modelos mais promissores ===")
    tune.main(["xgboost", "logistic_regression"])

    logging.info("=== 3/5 Avaliação final (conjunto de teste) ===")
    evaluate.main()

    logging.info("=== 4/5 Interpretabilidade (modelo final) ===")
    interpret.main(f"reports/ml/models/{evaluate.FINAL_MODEL_NAME}.joblib", evaluate.FINAL_MODEL_NAME)

    logging.info("=== 5/5 Viés e desbalanceamento (modelo final) ===")
    bias.main(f"reports/ml/models/{evaluate.FINAL_MODEL_NAME}.joblib")

    logging.info("Pipeline de ML completo. Artefatos em reports/ml/.")


if __name__ == "__main__":
    main()
