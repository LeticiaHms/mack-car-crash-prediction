"""
Pipeline de pré-processamento — features -> matriz numérica para os modelos.

Regra central (evitar leakage no pré-processamento, seção 4 do pedido da
Etapa 3): todo transformador é ajustado (`fit`) apenas no conjunto de
treino. Isso é garantido estruturalmente aqui porque `build_preprocessor()`
retorna um `ColumnTransformer` não ajustado — quem chama `fit`/`fit_transform`
é sempre `train.py`/`tune.py`, e sempre com `X_train`. Validação e teste
passam apenas por `.transform()`.

Encoding por tipo de coluna:
- Categóricas de baixa/média cardinalidade (`uf`, `br`, `tipo_pista`,
  `sentido_via`, `uso_solo`, `dia_semana`, `fase_dia`): one-hot
  (`handle_unknown="ignore"` — uma categoria nova em validação/teste vira
  vetor de zeros, nunca erro).
- `municipio` (2.057 categorias): one-hot explodiria a dimensionalidade
  sem ganho proporcional (a maioria dos municípios tem poucochíssimos
  registros). Usa-se `FrequencyEncoder` (frequência relativa no treino) —
  decisão registrada em D-15/D-16, adiada da Etapa 2 justamente para ser
  calculada só sobre o treino.
- Numéricas (`km`, `latitude`, `longitude`, `hora`, `hora_sin`, `hora_cos`,
  `mes`): imputação por mediana do treino + padronização (`StandardScaler`)
  — necessária para Regressão Logística, neutra para os modelos de árvore.
- Booleanas (`br_valido`, `km_valido`, `fim_de_semana`, `tracado_*`):
  repassadas como 0/1, sem escala (já estão na mesma unidade).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.ml.dataset import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, HIGH_CARDINALITY_FEATURES, NUMERIC_FEATURES


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    """Codifica uma coluna categórica pela frequência relativa de cada categoria
    observada em `fit` (sempre o treino). Categoria nunca vista em `transform`
    (município novo em validação/teste) recebe frequência 0.0 — sinaliza
    "não visto no histórico de treino" em vez de inventar uma taxa.
    """

    def fit(self, X: pd.DataFrame, y=None):
        col = X.iloc[:, 0]
        counts = col.value_counts(normalize=True)
        self.freq_map_ = counts.to_dict()
        self.n_features_in_ = 1
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        col = X.iloc[:, 0]
        out = col.map(self.freq_map_).fillna(0.0).to_numpy(dtype=float).reshape(-1, 1)
        return out

    def get_feature_names_out(self, input_features=None):
        return np.array([f"{input_features[0]}_freq"])


def _to_float(X):
    """Booleanas chegam como dtype bool; ColumnTransformer/estimadores esperam float."""
    return np.asarray(X, dtype=float)


def _to_str(X):
    """`br` é numérica com NaN (float64); forçar string ANTES do imputer de
    valor constante evita misturar float e str na mesma coluna, que o
    OneHotEncoder rejeita. NaN vira a string 'nan', unificada depois pelo
    imputer de valor constante para '__missing__'."""
    return pd.DataFrame(X).astype(str).replace("nan", np.nan).to_numpy()


def build_preprocessor() -> ColumnTransformer:
    """Monta (sem ajustar) o `ColumnTransformer` único, reaproveitado por todos
    os modelos — mesma matriz de entrada para Regressão Logística e para os
    modelos de árvore, trocando apenas o estimador final do pipeline."""
    categorical_pipe = Pipeline([
        ("to_str", FunctionTransformer(_to_str, feature_names_out="one-to-one")),
        ("imputer", SimpleImputer(strategy="constant", fill_value="__missing__")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    freq_pipe = Pipeline([
        ("freq", FrequencyEncoder()),
        ("scaler", StandardScaler()),
    ])
    boolean_pipe = Pipeline([
        ("to_float", FunctionTransformer(_to_float, feature_names_out="one-to-one")),
    ])

    return ColumnTransformer(
        transformers=[
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
            ("municipio_freq", freq_pipe, HIGH_CARDINALITY_FEATURES),
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("bool", boolean_pipe, BOOLEAN_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
