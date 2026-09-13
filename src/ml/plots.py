"""
Visualizações obrigatórias (seção 13 do pedido da Etapa 3) — cada gráfico
responde a uma pergunta analítica específica, nunca gerado só por obrigação:

- distribuicao_classes.png     -> a base está desbalanceada? quanto?
- matriz_confusao_<modelo>.png -> onde o modelo erra (falso negativo grave é o erro caro)?
- curva_roc.png                -> os modelos separam as classes melhor que o acaso, e o quanto melhor entre si?
- curva_pr.png                 -> com que precisão o modelo sinaliza a classe rara, em cada nível de recall?
- comparacao_metricas.png      -> qual modelo domina em qual métrica, treino x validação x teste?
- overfitting_gap.png          -> qual modelo generaliza melhor (menor gap treino-teste)?
- feature_importance_<modelo>.png -> quais variáveis mais pesam na decisão do modelo final?

Salva PNGs em `reports/ml/figures/`. Usa Agg (sem display) — ambiente
headless.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay

FIG_DIR = "reports/ml/figures"
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "axes.titlesize": 12, "axes.labelsize": 10})


def _save(fig, name: str):
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_class_distribution(y_train, y_val, y_test) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    splits = ["Treino", "Validação", "Teste"]
    rates = [y.mean() * 100 for y in (y_train, y_val, y_test)]
    counts = [len(y) for y in (y_train, y_val, y_test)]
    bars = ax.bar(splits, rates, color=["#4C72B0", "#55A868", "#C44E52"])
    for bar, n, r in zip(bars, counts, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, r + 0.5, f"{r:.1f}%\n(n={n:,})".replace(",", "."),
                ha="center", fontsize=9)
    ax.set_ylabel("% de acidentes graves/fatais (grave_bin=1)")
    ax.set_title("Distribuição da classe alvo por conjunto")
    ax.set_ylim(0, max(rates) * 1.35)
    return _save(fig, "distribuicao_classes.png")


def plot_confusion_matrix(y_true, y_pred, model_name: str, split_name: str) -> str:
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred, display_labels=["Não grave", "Grave/Fatal"],
        cmap="Blues", ax=ax, colorbar=False,
    )
    ax.set_title(f"Matriz de confusão — {model_name} ({split_name})")
    return _save(fig, f"matriz_confusao_{model_name}_{split_name}.png")


def plot_roc_curves(fitted_pipelines: dict, X, y, split_name: str) -> str:
    fig, ax = plt.subplots(figsize=(6, 5.5))
    for name, pipeline in fitted_pipelines.items():
        if hasattr(pipeline.named_steps["model"], "predict_proba"):
            RocCurveDisplay.from_estimator(pipeline, X, y, name=name, ax=ax)
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Acaso (AUC=0,50)")
    ax.set_title(f"Curva ROC — comparação de modelos ({split_name})")
    ax.legend(fontsize=8, loc="lower right")
    return _save(fig, f"curva_roc_{split_name}.png")


def plot_pr_curves(fitted_pipelines: dict, X, y, split_name: str) -> str:
    fig, ax = plt.subplots(figsize=(6, 5.5))
    base_rate = y.mean()
    for name, pipeline in fitted_pipelines.items():
        if hasattr(pipeline.named_steps["model"], "predict_proba"):
            PrecisionRecallDisplay.from_estimator(pipeline, X, y, name=name, ax=ax)
    ax.axhline(base_rate, color="k", linestyle="--", linewidth=1, label=f"Base (prevalência={base_rate:.2f})")
    ax.set_title(f"Curva Precision-Recall — comparação de modelos ({split_name})")
    ax.legend(fontsize=8, loc="upper right")
    return _save(fig, f"curva_pr_{split_name}.png")


def plot_metric_comparison(comparison_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(comparison_df))
    width = 0.25
    ax.bar(x - width, comparison_df["f1_treino"], width, label="F1 treino", color="#8DA0CB")
    ax.bar(x, comparison_df["f1_validacao"], width, label="F1 validação", color="#4C72B0")
    ax.bar(x + width, comparison_df["f1_teste"], width, label="F1 teste", color="#264478")
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df["modelo"], rotation=30, ha="right")
    ax.set_ylabel("F1-score (classe grave_bin=1)")
    ax.set_title("Comparação de F1 entre modelos — treino x validação x teste")
    ax.legend(fontsize=9)
    return _save(fig, "comparacao_metricas.png")


def plot_overfitting_gap(comparison_df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    order = comparison_df.sort_values("gap_treino_teste_f1")
    colors = ["#55A868" if g < 0.03 else ("#DD8452" if g < 0.08 else "#C44E52") for g in order["gap_treino_teste_f1"]]
    ax.barh(order["modelo"], order["gap_treino_teste_f1"], color=colors)
    ax.axvline(0, color="k", linewidth=0.8)
    ax.set_xlabel("F1(treino) − F1(teste)  [gap maior = mais overfitting]")
    ax.set_title("Gap de generalização por modelo")
    return _save(fig, "overfitting_gap.png")


def plot_feature_importance(importance_df: pd.DataFrame, model_name: str, value_col: str, top_n: int = 20) -> str:
    top = importance_df.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, max(4, top_n * 0.3)))
    ax.barh(top["feature"], top[value_col], color="#4C72B0")
    ax.set_xlabel(value_col)
    ax.set_title(f"Top {top_n} features mais importantes — {model_name}")
    return _save(fig, f"feature_importance_{model_name}.png")
