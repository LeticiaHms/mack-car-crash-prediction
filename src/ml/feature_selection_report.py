"""
Gera `reports/ml/tables/feature_selection.csv` — a tabela Feature | Tipo |
Decisão | Justificativa exigida na seção 2 do pedido da Etapa 3.

Não recalcula a seleção de features do zero: a Gold (`src/gold/dataset_ml.py`,
Etapa 2) já filtrou leakage e documentou origem/transformação de cada
feature (`reports/gold/feature_dictionary.csv`). Este módulo aplica, por
cima disso, as decisões ESPECÍFICAS de ML (D-15 a D-19 em
`docs/decisoes/DECISIONS.md`): remoção de constantes, estratégia de
encoding por coluna e exclusão de identificadores/alvo alternativo — e
grava tudo em uma única tabela para rastreabilidade.

Uso:
    python -m src.ml.feature_selection_report
"""
from __future__ import annotations

import os
import sys

import pandas as pd

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT_DIR)

from src.ml.dataset import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, HIGH_CARDINALITY_FEATURES, NUMERIC_FEATURES  # noqa: E402

TABLES_DIR = "reports/ml/tables"

ROWS = [
    # (feature, tipo, decisão, justificativa)
    ("id", "identificador", "EXCLUIR (não-feature)", "Chave técnica sem significado preditivo; usada só para rastreabilidade/deduplicação."),
    ("data_inversa", "data", "EXCLUIR (não-feature)", "Usada para construir o split temporal (D-15), não como input do modelo — o modelo não pode 'ver' a data calendário completa, só mes/dia_semana/hora, que já são features."),
    ("ano", "numérica", "EXCLUIR (não-feature)", "Treino e teste têm suporte de 'ano' quase disjunto por construção do split temporal (D-15); incluí-la deixaria o modelo aprender 'ano=2026 => teste' em vez de padrão real, e não generaliza para anos futuros fora do range visto."),
    ("gravidade_4", "alvo alternativo", "EXCLUIR (não-feature)", "É o alvo multiclasse alternativo (D-01) — jamais uma feature de si mesma."),
    ("geocoord_valido", "booleana", "EXCLUIR (constante)", "100% True em toda a Gold atual (D-18) — variância zero, nenhuma informação para qualquer modelo."),
]

for c in CATEGORICAL_FEATURES:
    if c == "br":
        just = "Código nominal de rodovia (124 valores); one-hot evita ordem artificial entre BRs. br=0 já virou NULL na Gold (D-05), tratado como categoria 'ausente' explícita pelo imputador constante."
    else:
        just = "Baixa/média cardinalidade; one-hot com handle_unknown='ignore' (categoria nova em produção vira vetor de zeros, não erro)."
    ROWS.append((c, "categórica", "INCLUIR — one-hot (fit só no treino)", just))

ROWS.append((
    "municipio", "categórica (alta cardinalidade — 2.057 valores)", "INCLUIR — frequência (fit só no treino, D-17)",
    "One-hot explodiria dimensionalidade sem ganho proporcional; frequência relativa calculada exclusivamente no treino evita leakage de estatística de validação/teste.",
))

NUMERIC_JUST = {
    "km": "Posição no trecho; sentinela <=0 já é NULL na Gold (D-04), imputado pela mediana do treino; km_valido preserva o sinal de 'não informado'.",
    "latitude": "Localização contínua do evento; sem sentinela remanescente na Gold atual (D-18).",
    "longitude": "Localização contínua do evento; sem sentinela remanescente na Gold atual (D-18).",
    "hora": "Hora do relógio (0-23); pico de gravidade às 19h documentado na EDA, distinto do pico de volume.",
    "hora_sin": "Componente cíclica da hora — captura a continuidade 23h->0h que a hora inteira não representa.",
    "hora_cos": "Par do seno, para reconstrução unívoca do ciclo de 24h.",
    "mes": "Sinal isolado fraco (Cramér's V=0,008, D-08) mas mantido por potencial de interação com outras features (regra: não remover só por baixa correlação isolada).",
}
for c in NUMERIC_FEATURES:
    ROWS.append((c, "numérica", "INCLUIR — imputação mediana + padronização (fit só no treino)", NUMERIC_JUST[c]))

BOOL_JUST = {
    "br_valido": "Quase-constante (99,75% True) mas a minoria carrega sinal forte: grave=28,33% quando True vs. 7,64% quando False — mantida (D-17/regra de não remover por quase-constância sem checar o efeito da minoria).",
    "km_valido": "Quase-constante (99,52% True); grave=28,35% (True) vs. 13,68% (False) — mesma lógica de br_valido.",
    "fim_de_semana": "Simplificação direta de dia_semana; grave levemente maior no fim de semana (30,19% vs. 27,35%).",
}
for c in BOOLEAN_FEATURES:
    if c.startswith("tracado_"):
        just = "Multi-hot de tracado_via (Gold, D-Etapa2); frequência varia de 71,58% (reta) a 0,06% (túnel) — as mais raras têm baixo poder estatístico isolado, mas nenhuma foi removida sem evidência de variância zero (só geocoord_valido, D-18, se qualifica)."
    else:
        just = BOOL_JUST.get(c, "")
    ROWS.append((c, "booleana", "INCLUIR — repassada como 0/1 (sem escala)", just))


def main():
    os.makedirs(TABLES_DIR, exist_ok=True)
    df = pd.DataFrame(ROWS, columns=["feature", "tipo", "decisao", "justificativa"])
    path = os.path.join(TABLES_DIR, "feature_selection.csv")
    df.to_csv(path, index=False)
    print(f"{len(df)} linhas gravadas em {path}")
    n_include = (df["decisao"].str.startswith("INCLUIR")).sum()
    print(f"Features incluídas no treino: {n_include}")
    return df


if __name__ == "__main__":
    main()
