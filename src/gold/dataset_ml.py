"""
Construção da camada Gold: features selecionadas + target, prontos para ML.

Lê a Silver (`silver.acidentes`, no DuckDB) e produz o dataset final
de Machine Learning — apenas identificação mínima, features selecionadas
(já transformadas) e o target. Nunca as ~40 colunas da Silver inteira.

Cada decisão de seleção/descarte é gravada, de forma reprodutível
(nunca digitada à mão), em:

    reports/gold/feature_dictionary.csv   -> uma linha por feature selecionada
    reports/gold/discarded_features.csv   -> uma linha por feature descartada
    reports/gold/gold_report.json         -> funil de linhas, schema final, checagem de leakage

Proteção de leakage (seção 9 do pedido da Etapa 2): antes de gravar, o script
garante por asserção que nenhuma coluna de `src.eda.utils.LEAKAGE_COLS` está entre
as features finais — se alguém adicionar uma dessas colunas à lista de
features por engano, a build falha ruidosamente em vez de vazar o alvo.

`create_table(con)` materializa o resultado como `gold.dataset_ml` no DuckDB
(`src/database/connection.py`), garantindo antes que `silver.acidentes`
exista — a dependência gold -> silver fica explícita. É a única tabela Gold
do projeto (item 9/13 do pedido de arquitetura: nada é criado aqui só para
alimentar gráfico do Streamlit).

Uso:
    python -m src.gold.dataset_ml
"""
from __future__ import annotations

import json
import logging
import os
import sys

import numpy as np
import pandas as pd

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../src/gold -> raiz
sys.path.insert(0, _ROOT_DIR)

from src.eda import utils as eu  # noqa: E402
from src.database.connection import create_table_from_df, ensure_schemas, get_connection, table_exists  # noqa: E402
from src.silver import acidentes as silver_acidentes  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# O dataset final vive só na tabela `gold.dataset_ml` do DuckDB; aqui ficam
# apenas os artefatos de documentação/auditoria da seleção de features.
REPORT_DIR = "reports/gold"
GOLD_REPORT_PATH = os.path.join(REPORT_DIR, "gold_report.json")
FEATURE_DICT_PATH = os.path.join(REPORT_DIR, "feature_dictionary.csv")
DISCARDED_PATH = os.path.join(REPORT_DIR, "discarded_features.csv")

# ---------------------------------------------------------------------------
# tracado_via é multivalorado em 22,52% dos registros (ex.: "Reta;Declive").
# Estas são as 12 primitivas reais encontradas na base (verificado via
# DuckDB sobre a Silver) — multi-hot em vez de one-hot da string inteira,
# que infla a cardinalidade aparente para ~1.223 categorias.
# ---------------------------------------------------------------------------
TRACADO_PRIMITIVAS = {
    "Reta": "tracado_reta",
    "Curva": "tracado_curva",
    "Aclive": "tracado_aclive",
    "Declive": "tracado_declive",
    "Interseção de Vias": "tracado_interseccao_de_vias",
    "Retorno Regulamentado": "tracado_retorno_regulamentado",
    "Rotatória": "tracado_rotatoria",
    "Ponte": "tracado_ponte",
    "Viaduto": "tracado_viaduto",
    "Em Obras": "tracado_em_obras",
    "Desvio Temporário": "tracado_desvio_temporario",
    "Túnel": "tracado_tunel",
}

WEEKEND_DAYS = {"sábado", "domingo"}

# Colunas que NÃO são features (identificação/rastreabilidade) — presentes na
# Gold para permitir o split temporal e a auditoria da próxima etapa, mas
# nunca entram na matriz de features do modelo.
ID_COLUMNS = ["id", "data_inversa", "ano"]

TARGET_COLUMNS = ["grave_bin", "gravidade_4"]

# ---------------------------------------------------------------------------
# Dicionário de features selecionadas: feature -> (origem, transformação, tipo, justificativa, risco_leakage)
# ---------------------------------------------------------------------------
FEATURE_DICTIONARY = [
    ("uf", "Bronze", "nenhuma", "categórica", "Localização estrutural, disponível a priori (Cramér's V=0,105 com gravidade).", "nenhum"),
    ("br", "Silver", "0 -> NULL (br_valido=False)", "categórica/numérica", "Rodovia federal; br=0 é sentinela de 'não identificada' (D-05), não uma rodovia real.", "nenhum"),
    ("br_valido", "Silver", "derivado (br <> 0)", "booleana", "Sinaliza explicitamente o sentinela de br=0 sem descartar a linha.", "nenhum"),
    ("km", "Silver", "<=0 -> NULL (km_valido=False)", "numérica", "Posição no trecho; km<=0 é placeholder de 'não informado' (D-04).", "nenhum"),
    ("km_valido", "Silver", "derivado (km > 0)", "booleana", "Sinaliza o sentinela de km<=0 sem descartar a linha.", "nenhum"),
    ("municipio", "Bronze", "nenhuma", "categórica (alta cardinalidade)", "Candidata geográfica a priori; 2.057 categorias — estratégia de encoding (target/frequency) fica para a etapa de ML, após o split temporal existir, para não vazar estatística de teste.", "nenhum"),
    ("latitude", "Silver", "0 -> NULL (geocoord_valido=False)", "numérica", "Localização contínua do evento.", "nenhum"),
    ("longitude", "Silver", "0 -> NULL (geocoord_valido=False)", "numérica", "Localização contínua do evento.", "nenhum"),
    ("geocoord_valido", "Silver", "derivado (lat<>0 e lon<>0)", "booleana", "Sinaliza coordenada nula (ponto no Golfo da Guiné) sem descartar a linha.", "nenhum"),
    ("tipo_pista", "Bronze", "nenhuma", "categórica", "Achado estrutural mais forte entre as variáveis a priori: pista simples +10,44 p.p. de gravidade vs. dupla (D-14).", "nenhum"),
    ("sentido_via", "Bronze", "nenhuma", "categórica", "'Não Informado' já é categoria autoexplicativa, sem necessidade de flag extra.", "nenhum"),
    ("uso_solo", "Bronze", "nenhuma", "categórica (2 níveis)", "Diferença observada urbano vs. rural (26,20% vs. 29,85% grave).", "nenhum"),
    ("mes", "Silver (derivado)", "nenhuma", "numérica (1-12)", "Mantido apesar do sinal fraco isolado (V=0,008) por potencial de interação; sem transformação cíclica (ver descarte).", "nenhum"),
    ("dia_semana", "Bronze", "nenhuma", "categórica (7 níveis)", "Fim de semana (sáb/dom) com gravidade um pouco acima do meio de semana.", "nenhum"),
    ("fim_de_semana", "Silver (derivado)", "dia_semana in {sábado, domingo}", "booleana", "Simplificação direta do padrão observado de fim de semana.", "nenhum"),
    ("hora", "Silver (derivado)", "extraída de horario::TIME", "numérica (0-23)", "Pico de gravidade às 19h, distinto do pico de volume (18h).", "nenhum"),
    ("hora_sin", "Gold (derivado)", "sin(2*pi*hora/24)", "numérica cíclica", "Captura a continuidade 23h->0h que a hora inteira não representa; hora tem sinal moderado (V=0,097) e padrão diurno real.", "nenhum"),
    ("hora_cos", "Gold (derivado)", "cos(2*pi*hora/24)", "numérica cíclica", "Par do seno para reconstrução unívoca do ciclo de 24h.", "nenhum"),
    ("fase_dia", "Bronze", "nenhuma", "categórica (4 níveis)", "Proxy oficial de iluminação (D-11); plena noite 32,57% vs. pleno dia 25,29% de gravidade.", "nenhum"),
] + [
    (col, "Silver (derivado de tracado_via)", f"multi-hot: '{primitiva}' in tracado_via.split(';')", "booleana",
     "tracado_via é multivalorado em 22,52% dos registros; multi-hot evita explodir a cardinalidade (1.223 combinações) que o one-hot da string produziria.",
     "nenhum")
    for primitiva, col in TRACADO_PRIMITIVAS.items()
]

DISCARDED_FEATURES = [
    ("mortos", "Leakage — resultado do próprio acidente (D-07); usada só para construir o target."),
    ("feridos_leves", "Leakage — resultado do próprio acidente (D-07); usada só para construir o target."),
    ("feridos_graves", "Leakage — resultado do próprio acidente (D-07); usada só para construir o target."),
    ("feridos", "Leakage — resultado do próprio acidente (D-07)."),
    ("ilesos", "Leakage — resultado do próprio acidente (D-07)."),
    ("ignorados", "Leakage — resultado do próprio acidente (D-07)."),
    ("pessoas", "Leakage — resultado do próprio acidente (D-07); além disso diverge da soma das categorias em 5,39% dos registros (D-03)."),
    ("veiculos", "Leakage — resultado do próprio acidente (contagem apurada no boletim de ocorrência)."),
    ("classificacao_acidente", "Leakage — é a classificação oficial do desfecho; usada só para derivar gravidade_4/grave_bin (D-01/D-02)."),
    ("causa_acidente", "Leakage — apurada após o evento; apesar de ser a 2ª maior associação com gravidade (V=0,244), não está disponível no momento da previsão (D-07)."),
    ("tipo_acidente", "Leakage — apurada após o evento; é a maior associação com gravidade (V=0,300), mas não disponível a priori (D-07)."),
    ("condicao_metereologica", "Não disponível a priori em produção (exigiria previsão meteorológica) e sinal fraco (V=0,034)."),
    ("regional", "Identifica a unidade da PRF, não o local do acidente; ~1% nulos, sem relação com o desfecho."),
    ("delegacia", "Identifica a unidade da PRF, não o local do acidente; ~1% nulos, sem relação com o desfecho."),
    ("uop", "Identifica a unidade da PRF, não o local do acidente; ~1% nulos, sem relação com o desfecho."),
    ("horario", "Substituída pelas derivadas hora/hora_sin/hora_cos."),
    ("tracado_via", "Substituída pelo multi-hot (12 colunas tracado_*); string original mistura até 2 primitivas e infla a cardinalidade aparente para 1.223 categorias."),
    ("feriado", "EDA (D-14) mostrou efeito só no volume de acidentes, não na gravidade condicional (IC da diferença cruza zero)."),
    ("vespera_de_feriado", "EDA (D-14/A-20) mostrou +5,75% de volume, mas o IC da diferença de gravidade cruza zero (-0,34 a +1,44 p.p.) — sem sinal para grave_bin."),
    ("pos_feriado", "EDA (D-14) mostrou efeito só no volume de acidentes, não na gravidade condicional."),
    ("mes_sin/mes_cos", "mes tem Cramér's V=0,008 com gravidade — praticamente nulo; sazonalidade real é de volume, não de gravidade (§4.6 da EDA)."),
    ("dia_semana_sin/dia_semana_cos", "dia_semana já é categórica de baixíssima cardinalidade (7 níveis); cíclico não agrega frente à codificação direta."),
]


def _multi_hot_tracado(series: pd.Series) -> pd.DataFrame:
    tokens = series.fillna("").apply(lambda s: {t.strip() for t in s.split(";") if t.strip()})
    out = {col: tokens.apply(lambda s: primitiva in s) for primitiva, col in TRACADO_PRIMITIVAS.items()}
    return pd.DataFrame(out, index=series.index)


def build_gold(con) -> tuple[pd.DataFrame, dict]:
    """Constrói o dataset final de ML a partir de `silver.acidentes` da conexão
    recebida (o DuckDB não permite abrir uma segunda conexão para o mesmo
    arquivo, então o pipeline repassa a que já está aberta)."""
    silver = con.execute("SELECT * FROM silver.acidentes").df()
    logging.info(f"Silver carregada: {len(silver)} linhas, {len(silver.columns)} colunas.")

    out = pd.DataFrame(index=silver.index)

    # Identificação / rastreabilidade
    for col in ID_COLUMNS:
        out[col] = silver[col]

    # Target
    out["grave_bin"] = silver["grave_bin"].astype("int8")
    out["gravidade_4"] = silver["gravidade_4"]

    # Geografia (sentinelas viram NULL, mantendo a flag de validade ao lado)
    out["uf"] = silver["uf"]
    out["br"] = silver["br"].where(silver["br_valido"])
    out["br_valido"] = silver["br_valido"]
    out["km"] = silver["km"].where(silver["km_valido"])
    out["km_valido"] = silver["km_valido"]
    out["municipio"] = silver["municipio"]
    out["latitude"] = silver["latitude"].where(silver["geocoord_valido"])
    out["longitude"] = silver["longitude"].where(silver["geocoord_valido"])
    out["geocoord_valido"] = silver["geocoord_valido"]
    out["tipo_pista"] = silver["tipo_pista"]

    # Via
    out["sentido_via"] = silver["sentido_via"]
    out["uso_solo"] = silver["uso_solo"]

    # Traçado da via: multi-hot
    tracado = _multi_hot_tracado(silver["tracado_via"])
    for col in tracado.columns:
        out[col] = tracado[col]

    # Temporal
    out["mes"] = silver["mes"].astype("int8")
    out["dia_semana"] = silver["dia_semana"]
    out["fim_de_semana"] = silver["dia_semana"].isin(WEEKEND_DAYS)
    out["hora"] = silver["hora"].astype("float64")  # pode ter NaN se horario não parsear
    hora_frac = out["hora"] / 24.0
    out["hora_sin"] = np.sin(2 * np.pi * hora_frac)
    out["hora_cos"] = np.cos(2 * np.pi * hora_frac)
    out["fase_dia"] = silver["fase_dia"]

    feature_columns = [c for c in out.columns if c not in ID_COLUMNS + TARGET_COLUMNS]

    # --- Guard-rail de leakage (seção 9 do pedido) ---------------------------
    leaked = set(feature_columns) & set(eu.LEAKAGE_COLS)
    assert not leaked, (
        f"BLOQUEIO: coluna(s) de leakage encontrada(s) entre as features da Gold: {leaked}. "
        "Essas colunas só podem ser usadas para construir o target, nunca como feature (D-07)."
    )

    documented = {row[0] for row in FEATURE_DICTIONARY}
    undocumented = set(feature_columns) - documented
    assert not undocumented, (
        f"BLOQUEIO: feature(s) sem entrada em FEATURE_DICTIONARY: {undocumented}. "
        "Toda feature selecionada precisa de origem/transformação/justificativa documentadas."
    )

    report = {
        "rows_silver": int(len(silver)),
        "rows_gold": int(len(out)),
        "n_feature_columns": len(feature_columns),
        "n_id_columns": len(ID_COLUMNS),
        "n_target_columns": len(TARGET_COLUMNS),
        "feature_columns": feature_columns,
        "id_columns": ID_COLUMNS,
        "target_columns": TARGET_COLUMNS,
        "leakage_columns_checked": sorted(eu.LEAKAGE_COLS),
        "leakage_guard": "PASSOU — nenhuma coluna de leakage presente nas features.",
        "target_distribution_grave_bin": {
            str(k): int(v) for k, v in out["grave_bin"].value_counts().sort_index().items()
        },
    }
    return out, report


def save_reports(report: dict):
    """Grava os artefatos de documentação/auditoria da Gold. O dataset em si
    vive apenas na tabela `gold.dataset_ml` do DuckDB — sem espelho em Parquet."""
    os.makedirs(REPORT_DIR, exist_ok=True)

    pd.DataFrame(
        FEATURE_DICTIONARY,
        columns=["feature", "origem", "transformacao", "tipo", "justificativa", "risco_leakage"],
    ).to_csv(FEATURE_DICT_PATH, index=False)
    logging.info(f"Dicionário de features salvo em {FEATURE_DICT_PATH}")

    pd.DataFrame(DISCARDED_FEATURES, columns=["feature", "motivo_descarte"]).to_csv(DISCARDED_PATH, index=False)
    logging.info(f"Features descartadas salvas em {DISCARDED_PATH}")

    with open(GOLD_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logging.info(f"Relatório da Gold salvo em {GOLD_REPORT_PATH}")


def create_table(con=None) -> tuple[pd.DataFrame, dict]:
    """Materializa `gold.dataset_ml` no DuckDB, garantindo antes que
    `silver.acidentes` exista. Reaproveita `build_gold()` tal como está —
    a seleção/transformação de features não é duplicada aqui."""
    own_con = con is None
    if own_con:
        con = get_connection()
    ensure_schemas(con)

    if not table_exists(con, "silver", "acidentes"):
        silver_acidentes.create_table(con)

    gold, report = build_gold(con)
    save_reports(report)
    create_table_from_df(con, "gold", "dataset_ml", gold)
    logging.info(f"gold.dataset_ml materializada: {len(gold)} linhas, {len(gold.columns)} colunas.")

    if own_con:
        con.close()
    return gold, report


def main():
    create_table()


if __name__ == "__main__":
    main()
