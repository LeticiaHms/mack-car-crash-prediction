"""
Modelagem preditiva (Etapa 3) — classificação binária supervisionada.

Problema: prever `grave_bin` (1 = acidente grave/fatal, 0 = não grave) a
partir de características do acidente e da rodovia conhecidas *antes* do
desfecho, usando `gold.dataset_ml` (DuckDB) como única fonte de dados.

Este é, deliberadamente, o único arquivo de modelagem do projeto: carga,
seleção de features, split treino/validação/teste, pré-processamento,
treino, avaliação, gráficos e interpretação simples vivem todos aqui, na
ordem em que aparecem no relatório da Etapa 3. Não é uma arquitetura de
produção — é um experimento acadêmico simples e reproduzível.

Uso:
    python -m src.ml.modelagem
"""
from __future__ import annotations

import os
import sys

import duckdb
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../src/ml -> raiz
sys.path.insert(0, _ROOT_DIR)

DB_PATH = "data/prf.duckdb"
REPORT_DIR = "reports/ml"

# ---------------------------------------------------------------------------
# 1. Features
#
# Todas vêm de `gold.dataset_ml` e descrevem o acidente/rodovia no momento
# do evento (localização, tipo de via, data/hora) — nunca o resultado dele.
# Ficam de fora das features, por razões diferentes:
#   - `id`, `data_inversa`, `ano`: identificação/apoio ao split, não sinal preditivo.
#   - `grave_bin`, `gravidade_4`: são o alvo (ou uma variante dele).
#   - `mortos`, `feridos_*`, `pessoas`, `veiculos`, `classificacao_acidente`,
#     `causa_acidente`, `tipo_acidente`: já nem existem na Gold — foram
#     removidas na etapa anterior por serem conhecidas só depois do
#     acidente (data leakage), ver `src/gold/dataset_ml.py`.
#   - `municipio`: 2.057 categorias — one-hot explodiria a dimensionalidade
#     e um encoding mais sofisticado (frequência/taxa) foge do escopo
#     simples desta etapa; a informação geográfica já é capturada por
#     `uf`, `latitude` e `longitude`.
#   - `geocoord_valido`: constante (100% `True` na base atual) — zero
#     variância, portanto zero informação para qualquer modelo.
# ---------------------------------------------------------------------------
CATEGORICAL_FEATURES = ["uf", "br", "tipo_pista", "sentido_via", "uso_solo", "dia_semana", "fase_dia"]
NUMERIC_FEATURES = ["km", "latitude", "longitude", "hora", "hora_sin", "hora_cos", "mes"]
BOOLEAN_FEATURES = [
    "br_valido", "km_valido", "fim_de_semana",
    "tracado_reta", "tracado_curva", "tracado_aclive", "tracado_declive",
    "tracado_interseccao_de_vias", "tracado_retorno_regulamentado", "tracado_rotatoria",
    "tracado_ponte", "tracado_viaduto", "tracado_em_obras", "tracado_desvio_temporario",
    "tracado_tunel",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES + BOOLEAN_FEATURES
TARGET = "grave_bin"

# Justificativa resumida de cada grupo (impressa no resumo final):
FEATURE_JUSTIFICATIVAS = {
    "Categóricas (localização/via)": "uf, br, tipo_pista, sentido_via, uso_solo, dia_semana, fase_dia — "
                                      "características estruturais da rodovia e do calendário, estáveis e conhecidas a priori.",
    "Numéricas (posição/tempo)": "km, latitude, longitude, hora (+ hora_sin/hora_cos cíclicos), mes — "
                                  "localização contínua do acidente e momento do dia/ano.",
    "Booleanas (traçado e validade)": "br_valido, km_valido, fim_de_semana, tracado_* (12 primitivas de traçado da via) — "
                                       "sinalizam sentinelas de dado ausente e a geometria do trecho (reta, curva, viaduto, etc.).",
}

TRAIN_FRACTION = 0.70
VAL_FRACTION = 0.15
# Teste = fração restante (~0.15)


# ---------------------------------------------------------------------------
# 2. Carga dos dados (DuckDB)
# ---------------------------------------------------------------------------
def load_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """Lê `gold.dataset_ml` já ordenada cronologicamente (necessário para o
    split temporal do passo seguinte)."""
    con = duckdb.connect(db_path, read_only=True)
    try:
        df = con.execute("SELECT * FROM gold.dataset_ml ORDER BY data_inversa, id").df()
    finally:
        con.close()

    # `br` é numérica na Gold (double, com NaN nos casos "não identificada"),
    # mas é um código nominal de rodovia (BR-101 não é "maior" que BR-116) —
    # convertida para string para ser tratada como categórica, preservando
    # os ausentes (viram "não informado" no pré-processamento).
    df["br"] = df["br"].map(lambda v: str(int(v)) if pd.notna(v) else np.nan)
    return df


# ---------------------------------------------------------------------------
# 3. Divisão treino/validação/teste (split temporal, sem embaralhar)
#
# Os dados têm dimensão temporal (acidentes de 2022 a 2026): dividir de
# forma aleatória permitiria ao modelo "ver" indiretamente padrões do
# futuro. Por isso o corte é feito por DATA: os ~70% dias mais antigos
# formam o treino, os ~15% seguintes a validação e os ~15% finais o teste —
# nunca um corte no meio de um mesmo dia (a ordem de linhas dentro de um dia
# não é necessariamente cronológica).
#
# Sem tuning de hiperparâmetros nesta etapa (pedido explícito), a validação
# não decide nenhum parâmetro — serve só como uma checagem intermediária de
# generalização (treino vs. validação) antes da leitura final. O teste
# nunca é tocado até a avaliação final reportada abaixo.
# ---------------------------------------------------------------------------
def split_temporal(df: pd.DataFrame, train_fraction: float = TRAIN_FRACTION, val_fraction: float = VAL_FRACTION):
    daily_counts = df.groupby(df["data_inversa"].dt.date).size().sort_index()
    cumulative_fraction = daily_counts.cumsum() / len(df)
    train_end_date = cumulative_fraction[cumulative_fraction >= train_fraction].index[0]
    val_end_date = cumulative_fraction[cumulative_fraction >= train_fraction + val_fraction].index[0]

    train_df = df[df["data_inversa"].dt.date <= train_end_date].copy()
    val_df = df[(df["data_inversa"].dt.date > train_end_date) & (df["data_inversa"].dt.date <= val_end_date)].copy()
    test_df = df[df["data_inversa"].dt.date > val_end_date].copy()
    return train_df, val_df, test_df, train_end_date, val_end_date


# ---------------------------------------------------------------------------
# 4. Pré-processamento (mínimo necessário, ajustado só no treino)
# ---------------------------------------------------------------------------
def build_preprocessor() -> ColumnTransformer:
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="nao_informado")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    return ColumnTransformer([
        ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ("num", numeric_pipeline, NUMERIC_FEATURES),
        ("bool", "passthrough", BOOLEAN_FEATURES),
    ])


# ---------------------------------------------------------------------------
# 5. Modelos — os 3 algoritmos de classificação escolhidos da lista do
# professor (Regressão Linear e K-Means ficam de fora por não servirem a
# classificação binária).
#
#   - Regressão Logística: modelo linear de referência, rápido e
#     interpretável via coeficientes.
#   - Árvore de Decisão: captura relações não-lineares e interações sem
#     transformação manual das features; caminho de decisão auditável.
#   - Random Forest: ensemble de árvores (bagging), tende a reduzir a
#     variância/overfitting de uma árvore única.
#
# Sem busca de hiperparâmetros: usamos os padrões do scikit-learn com um
# ajuste simples e justificado em cada modelo (profundidade máxima para
# conter overfitting nos ~218 mil registros de treino, e peso de classe
# para compensar o desbalanceamento moderado de ~28% de acidentes graves).
# ---------------------------------------------------------------------------
def build_models() -> dict:
    return {
        "Regressão Logística": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=42,
        ),
        "Árvore de Decisão": DecisionTreeClassifier(
            max_depth=10, min_samples_leaf=50, class_weight="balanced", random_state=42,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            class_weight="balanced_subsample", random_state=42, n_jobs=-1,
        ),
    }


# ---------------------------------------------------------------------------
# 6. Treino + previsão + métricas
# ---------------------------------------------------------------------------
def compute_metrics(y_true, y_pred, y_proba) -> dict:
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred),
        "F1": f1_score(y_true, y_pred),
        "ROC-AUC": roc_auc_score(y_true, y_proba),
    }


def train_and_evaluate(models: dict, X_train, y_train, X_val, y_val, X_test, y_test) -> dict:
    """Treina cada modelo (dentro de um Pipeline com o pré-processamento,
    ajustado só no treino) e calcula métricas em validação (checagem de
    generalização, não usada para decidir nada, já que não há tuning) e em
    teste (avaliação final — a que entra nos gráficos e no `metrics.csv`)."""
    results = {}
    for name, estimator in models.items():
        pipeline = Pipeline([
            ("preprocess", build_preprocessor()),
            ("model", estimator),
        ])
        pipeline.fit(X_train, y_train)

        val_pred = pipeline.predict(X_val)
        val_proba = pipeline.predict_proba(X_val)[:, 1]
        val_metrics = compute_metrics(y_val, val_pred, val_proba)

        test_pred = pipeline.predict(X_test)
        test_proba = pipeline.predict_proba(X_test)[:, 1]
        test_metrics = compute_metrics(y_test, test_pred, test_proba)

        results[name] = {
            "pipeline": pipeline,
            "val_metrics": val_metrics,
            "metrics": test_metrics,
            "y_pred": test_pred,
            "y_proba": test_proba,
            "confusion_matrix": confusion_matrix(y_test, test_pred),
        }
        print(f"  [{name}] treinado — Validação: F1={val_metrics['F1']:.3f} | "
              f"Teste: Accuracy={test_metrics['Accuracy']:.3f}  F1={test_metrics['F1']:.3f}  ROC-AUC={test_metrics['ROC-AUC']:.3f}")
    return results


# ---------------------------------------------------------------------------
# 7. Gráficos (só os essenciais para apresentar o resultado)
# ---------------------------------------------------------------------------
def plot_target_distribution(df: pd.DataFrame, path: str) -> None:
    counts = df[TARGET].value_counts().sort_index()
    labels = ["Não grave (0)", "Grave/fatal (1)"]
    total = counts.sum()

    fig, ax = plt.subplots(figsize=(5, 4.5))
    bars = ax.bar(labels, counts.values, color=["#4C72B0", "#C44E52"])
    ax.set_ylim(0, counts.max() * 1.18)
    for bar, count in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f"{count:,}\n({count / total:.1%})".replace(",", "."),
                 ha="center", va="bottom")
    ax.set_ylabel("Número de acidentes")
    ax.set_title(f"Distribuição da variável alvo (grave_bin)\nn = {total:,}".replace(",", "."))
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_confusion_matrices(results: dict, path: str) -> None:
    fig, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 4.5))
    for ax, (name, res) in zip(axes, results.items()):
        cm = res["confusion_matrix"]
        ax.imshow(cm, cmap="Blues")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, f"{cm[i, j]:,}".replace(",", "."), ha="center", va="center")
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Previsto 0", "Previsto 1"])
        ax.set_yticklabels(["Real 0", "Real 1"])
        ax.set_title(name)
    fig.suptitle("Matriz de confusão — conjunto de teste")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_roc_curve(results: dict, y_test, path: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, res in results.items():
        fpr, tpr, _ = roc_curve(y_test, res["y_proba"])
        ax.plot(fpr, tpr, label=f"{name} (AUC={res['metrics']['ROC-AUC']:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Modelo aleatório (AUC=0,5)")
    ax.set_xlabel("Taxa de falsos positivos")
    ax.set_ylabel("Taxa de verdadeiros positivos")
    ax.set_title("Curva ROC — conjunto de teste")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_metric_comparison(results: dict, path: str) -> None:
    metric_names = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    model_names = list(results.keys())
    x = np.arange(len(metric_names))
    width = 0.8 / len(model_names)

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, name in enumerate(model_names):
        values = [results[name]["metrics"][m] for m in metric_names]
        ax.bar(x + i * width, values, width, label=name)
    ax.set_xticks(x + width * (len(model_names) - 1) / 2)
    ax.set_xticklabels(metric_names)
    ax.set_ylim(0, 1)
    ax.set_title("Comparação de métricas — conjunto de teste")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8. Interpretabilidade simples
#
# Só o que é necessário para responder "quais características parecem
# importar mais para o modelo?" — importância nativa (árvores) ou
# coeficientes (regressão logística). Importância NÃO significa
# causalidade: apenas descreve o que o modelo usou para prever.
# ---------------------------------------------------------------------------
def print_top_features(name: str, pipeline: Pipeline, top_n: int = 10) -> None:
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    model = pipeline.named_steps["model"]

    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        label = "importância (feature_importances_)"
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
        label = "|coeficiente|"
    else:
        return

    order = np.argsort(importances)[::-1][:top_n]
    print(f"\n  {name} — top {top_n} features por {label}:")
    for rank, idx in enumerate(order, start=1):
        print(f"    {rank:2d}. {feature_names[idx]:<40s} {importances[idx]:.4f}")


# ---------------------------------------------------------------------------
# 9. Orquestração
# ---------------------------------------------------------------------------
def main():
    os.makedirs(REPORT_DIR, exist_ok=True)

    print("1) Carregando gold.dataset_ml via DuckDB...")
    df = load_data()
    print(f"   {len(df):,} registros carregados.".replace(",", "."))

    print("\n2) Selecionando features e separando X/y...")
    y = df[TARGET].astype(int)
    print(f"   {len(FEATURE_COLUMNS)} features "
          f"({len(CATEGORICAL_FEATURES)} categóricas, {len(NUMERIC_FEATURES)} numéricas, {len(BOOLEAN_FEATURES)} booleanas).")
    for grupo, justificativa in FEATURE_JUSTIFICATIVAS.items():
        print(f"   - {grupo}: {justificativa}")

    print("\n3) Dividindo treino/validação/teste por corte temporal (~70%/15%/15%, por data, sem embaralhar)...")
    train_df, val_df, test_df, train_end_date, val_end_date = split_temporal(df)
    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET].astype(int)
    X_val, y_val = val_df[FEATURE_COLUMNS], val_df[TARGET].astype(int)
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET].astype(int)
    print(f"   Cortes: treino até {train_end_date} · validação até {val_end_date} · teste a partir do dia seguinte.")
    for label, part in (("Treino", train_df), ("Validação", val_df), ("Teste", test_df)):
        rate = part[TARGET].astype(int).mean()
        print(f"   {label:<10s} {len(part):>7,} registros ({len(part) / len(df):.1%}) — "
              f"{part['data_inversa'].min().date()} a {part['data_inversa'].max().date()} — % grave: {rate:.2%}".replace(",", "."))
    print("   A validação não decide nenhum hiperparâmetro (sem tuning nesta etapa) — é só uma checagem "
          "intermediária de generalização; a avaliação final usa exclusivamente o teste.")

    print("\n4) Treinando os 3 modelos (pré-processamento ajustado só no treino)...")
    models = build_models()
    results = train_and_evaluate(models, X_train, y_train, X_val, y_val, X_test, y_test)

    print("\n5) Gerando gráficos em reports/ml/...")
    plot_target_distribution(df, os.path.join(REPORT_DIR, "class_distribution.png"))
    plot_confusion_matrices(results, os.path.join(REPORT_DIR, "confusion_matrix.png"))
    plot_roc_curve(results, y_test, os.path.join(REPORT_DIR, "roc_curve.png"))
    plot_metric_comparison(results, os.path.join(REPORT_DIR, "metric_comparison.png"))

    print("\n6) Salvando tabela comparativa de métricas...")
    metrics_df = pd.DataFrame({name: res["metrics"] for name, res in results.items()}).T
    metrics_df.index.name = "Modelo"
    metrics_df.to_csv(os.path.join(REPORT_DIR, "metrics.csv"), float_format="%.4f")
    print(metrics_df.round(4).to_string())

    best_model = metrics_df["F1"].idxmax()

    print("\n7) Interpretabilidade simples (importância de features)...")
    for name, res in results.items():
        print_top_features(name, res["pipeline"])

    print("\n" + "=" * 78)
    print("RESUMO FINAL")
    print("=" * 78)
    print(f"Registros totais (gold.dataset_ml): {len(df):,}".replace(",", "."))
    print(f"Features utilizadas: {len(FEATURE_COLUMNS)}")
    print(f"Treino: {len(train_df):,} | Validação: {len(val_df):,} | Teste: {len(test_df):,} registros".replace(",", "."))
    print(f"Distribuição de grave_bin (base completa): 0={int((y == 0).sum()):,} ({(y == 0).mean():.1%})  "
          f"1={int((y == 1).sum()):,} ({(y == 1).mean():.1%})".replace(",", "."))
    print("\nMétricas por modelo (conjunto de teste — avaliação final):")
    print(metrics_df.round(4).to_string())
    print(f"\nMelhor modelo segundo F1 (classe grave): {best_model}")
    print("Nota: importância de feature indica associação usada pelo modelo, não causalidade.")
    print("=" * 78)


if __name__ == "__main__":
    main()
