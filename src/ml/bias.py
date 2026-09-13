"""
Análise de viés e desbalanceamento (seção 12 do pedido da Etapa 3).

A base não tem nenhum atributo de pessoa (idade, gênero, renda...) — não é
possível avaliar viés demográfico, e este módulo não afirma nada sobre isso
(limitação declarada explicitamente, nunca "sem viés" por omissão). O que É
possível e É verificado aqui: desempenho do modelo final SEGMENTADO por
grupos estruturais/geográficos (UF, tipo de pista, uso do solo, fase do dia)
— para checar se o modelo trata esses grupos de forma equivalente ou se um
limiar de decisão único (0,5) produz disparidade sistemática de Recall/
Precision entre eles.

Uso:
    python -m src.ml.bias
"""
from __future__ import annotations

import os
import sys

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import TARGET, get_X_y, load_gold, temporal_split  # noqa: E402
from src.ml.plots import FIG_DIR, _save  # noqa: E402

REPORT_DIR = "reports/ml"
TABLES_DIR = os.path.join(REPORT_DIR, "tables")
MIN_GROUP_SIZE = 300  # grupos menores que isso têm métrica instável demais para reportar


def group_metrics(df: pd.DataFrame, group_col: str, min_size: int = MIN_GROUP_SIZE) -> pd.DataFrame:
    rows = []
    for value, g in df.groupby(group_col):
        if len(g) < min_size:
            continue
        rows.append({
            "grupo": group_col, "valor": value, "n": len(g),
            "taxa_grave_real": g[TARGET].mean(),
            "proba_media_prevista": g["_proba"].mean(),
            "recall": recall_score(g[TARGET], g["_pred"], zero_division=0),
            "precision": precision_score(g[TARGET], g["_pred"], zero_division=0),
            "f1": f1_score(g[TARGET], g["_pred"], zero_division=0),
        })
    return pd.DataFrame(rows).sort_values("recall")


def plot_bias_scatter(df_uf: pd.DataFrame) -> str:
    corr = df_uf["taxa_grave_real"].corr(df_uf["recall"])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.scatter(df_uf["taxa_grave_real"] * 100, df_uf["recall"] * 100,
               s=df_uf["n"] / 20, alpha=0.7, color="#4C72B0", edgecolor="white")
    for _, r in df_uf.iterrows():
        ax.annotate(r["valor"], (r["taxa_grave_real"] * 100, r["recall"] * 100),
                    fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("Taxa real de grave_bin=1 na UF, teste (%)")
    ax.set_ylabel("Recall do modelo na UF, teste (%)")
    ax.set_title(
        f"Recall por UF vs. prevalência real — evidência de viés de limiar único\n"
        f"(corr={corr:.2f}; tamanho do ponto = n de acidentes na UF)"
    )
    return _save(fig, "bias_recall_por_uf.png")


def main(model_path: str = "reports/ml/models/xgboost_tuned.joblib"):
    os.makedirs(TABLES_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    pipeline = joblib.load(model_path)
    gold = load_gold()
    _train, _val, test, _info = temporal_split(gold)
    Xte, _yte = get_X_y(test)

    test = test.copy()
    test["_pred"] = pipeline.predict(Xte)
    test["_proba"] = pipeline.predict_proba(Xte)[:, 1]

    uf_df = group_metrics(test, "uf")
    uf_df.to_csv(os.path.join(TABLES_DIR, "bias_uf_test.csv"), index=False)
    plot_bias_scatter(uf_df)

    other_groups = pd.concat([
        group_metrics(test, "tipo_pista"),
        group_metrics(test, "uso_solo"),
        group_metrics(test, "fase_dia"),
    ], ignore_index=True)
    other_groups.to_csv(os.path.join(TABLES_DIR, "bias_other_groups_test.csv"), index=False)

    corr_taxa = uf_df["taxa_grave_real"].corr(uf_df["recall"])
    corr_proba = uf_df["proba_media_prevista"].corr(uf_df["recall"])
    print(f"corr(taxa_grave_real, recall) por UF: {corr_taxa:.3f}")
    print(f"corr(proba_media_prevista, recall) por UF: {corr_proba:.3f}")
    print(f"Recall por UF: min={uf_df['recall'].min():.3f} ({uf_df.loc[uf_df['recall'].idxmin(), 'valor']}) "
          f"max={uf_df['recall'].max():.3f} ({uf_df.loc[uf_df['recall'].idxmax(), 'valor']})")
    return uf_df, other_groups


if __name__ == "__main__":
    main()
