"""
Carga do dataset de ML (`gold.dataset_ml`) e divisão treino/validação/teste.

Decisão de split (ver `docs/entregas/etapa3-modelagem.md` e D-15 em
`docs/decisoes/DECISIONS.md`): o problema tem dimensão temporal explícita
(spec, seção 7) e a EDA (D-13) já mostrou que a série é estável ano a ano
(~28% de `grave_bin=1` em todos os anos, sem tendência). Em vez de dividir
por ano cheio (2022-2024/2025/2026, que ficaria desbalanceado porque 2026
só tem 6 meses consolidados), a divisão usa dois cortes de data escolhidos
para aproximar 70/15/15 em contagem de linhas, preservando a ordem
cronológica (nenhuma linha de validação/teste é anterior a uma linha de
treino) — isso evita tanto vazamento temporal quanto viés de tamanho de
amostra entre os conjuntos.

Os cortes são constantes fixas (não recalculadas a cada execução) para que
o split seja idêntico entre execuções e entre treino/inferência.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../src/ml -> raiz
sys.path.insert(0, _ROOT_DIR)

from src.database.connection import get_connection  # noqa: E402

TARGET = "grave_bin"
# gravidade_4 é o alvo alternativo (multiclasse), nunca uma feature.
# geocoord_valido é constante (100% True em toda a base — nenhum registro
# com sentinela de coordenada zerada sobreviveu até a Gold) e por isso não
# carrega informação: descartada aqui como quase-constante (achado da
# Etapa 3, não da Etapa 2 — ver seção "Seleção de Features" do relatório).
NON_FEATURE_COLUMNS = ["id", "data_inversa", "ano", "grave_bin", "gravidade_4", "geocoord_valido"]

CATEGORICAL_FEATURES = ["uf", "br", "tipo_pista", "sentido_via", "uso_solo", "dia_semana", "fase_dia"]
HIGH_CARDINALITY_FEATURES = ["municipio"]  # codificação por frequência (ver preprocessing.py)
NUMERIC_FEATURES = ["km", "latitude", "longitude", "hora", "hora_sin", "hora_cos", "mes"]
BOOLEAN_FEATURES = [
    "br_valido", "km_valido", "fim_de_semana",
    "tracado_reta", "tracado_curva", "tracado_aclive", "tracado_declive",
    "tracado_interseccao_de_vias", "tracado_retorno_regulamentado", "tracado_rotatoria",
    "tracado_ponte", "tracado_viaduto", "tracado_em_obras", "tracado_desvio_temporario", "tracado_tunel",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + HIGH_CARDINALITY_FEATURES + NUMERIC_FEATURES + BOOLEAN_FEATURES

# Cortes de data do split temporal (fixos — ver docstring do módulo).
# train: data_inversa <  TRAIN_END
# val:   TRAIN_END <= data_inversa < VAL_END
# test:  data_inversa >= VAL_END
TRAIN_END = "2025-03-09"
VAL_END = "2025-10-30"


def load_gold(con=None) -> pd.DataFrame:
    """Lê `gold.dataset_ml` do DuckDB (somente leitura, nunca reconstrói)."""
    own_con = con is None
    if own_con:
        con = get_connection(read_only=True)
    df = con.execute("SELECT * FROM gold.dataset_ml ORDER BY data_inversa, id").df()
    if own_con:
        con.close()
    return df


def temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Divide `df` em treino/validação/teste por corte de data (ver docstring do módulo).

    Retorna os três DataFrames (índices preservados, sem embaralhar) e um
    dicionário com o resumo da divisão (contagens, percentuais, distribuição
    do alvo) para auditoria/relatório.
    """
    train = df[df["data_inversa"] < TRAIN_END].reset_index(drop=True)
    val = df[(df["data_inversa"] >= TRAIN_END) & (df["data_inversa"] < VAL_END)].reset_index(drop=True)
    test = df[df["data_inversa"] >= VAL_END].reset_index(drop=True)

    n = len(df)
    info = {"train_end": TRAIN_END, "val_end": VAL_END, "n_total": int(n), "splits": {}}
    for name, part in [("train", train), ("val", val), ("test", test)]:
        info["splits"][name] = {
            "n": int(len(part)),
            "pct": round(len(part) / n * 100, 2),
            "date_min": str(part["data_inversa"].min().date()),
            "date_max": str(part["data_inversa"].max().date()),
            "grave_bin_rate_pct": round(float(part[TARGET].mean() * 100), 2),
        }
    return train, val, test, info


def get_X_y(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Recorta a matriz de features (`FEATURE_COLUMNS`) e o alvo (`TARGET`) de um split."""
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET].astype(int).copy()
    return X, y


if __name__ == "__main__":
    import json

    gold = load_gold()
    tr, va, te, split_info = temporal_split(gold)
    print(json.dumps(split_info, indent=2, ensure_ascii=False))
