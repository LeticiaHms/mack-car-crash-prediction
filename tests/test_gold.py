"""`gold.dataset_ml` contém as features esperadas e não contém variáveis
proibidas de leakage (item 16, bloco "Gold")."""
from src.eda import utils as eu
from src.gold import dataset_ml


def _columns(con) -> set[str]:
    return {row[0] for row in con.execute("DESCRIBE gold.dataset_ml").fetchall()}


def test_gold_nao_contem_colunas_de_leakage(con):
    cols = _columns(con)
    leaked = cols & set(eu.LEAKAGE_COLS)
    assert not leaked, f"Coluna(s) de leakage presente(s) em gold.dataset_ml: {leaked}"


def test_gold_contem_as_colunas_de_target(con):
    cols = _columns(con)
    for target in dataset_ml.TARGET_COLUMNS:
        assert target in cols, f"Coluna de target '{target}' ausente em gold.dataset_ml"


def test_gold_contem_as_colunas_de_identificacao(con):
    cols = _columns(con)
    for id_col in dataset_ml.ID_COLUMNS:
        assert id_col in cols, f"Coluna de identificação '{id_col}' ausente em gold.dataset_ml"


def test_gold_contem_todas_as_features_documentadas(con):
    cols = _columns(con)
    documented = {row[0] for row in dataset_ml.FEATURE_DICTIONARY}
    missing = documented - cols
    assert not missing, f"Feature(s) documentada(s) em FEATURE_DICTIONARY ausente(s) na tabela: {missing}"


def test_gold_nao_tem_colunas_fora_do_contrato(con):
    """Toda coluna de gold.dataset_ml é id, target ou uma feature documentada
    — nada "extra" entra na Gold por acidente (item 13: nenhuma tabela extra
    só para consumo do Streamlit)."""
    cols = _columns(con)
    esperado = set(dataset_ml.ID_COLUMNS) | set(dataset_ml.TARGET_COLUMNS) | {row[0] for row in dataset_ml.FEATURE_DICTIONARY}
    extra = cols - esperado
    assert not extra, f"Coluna(s) inesperada(s) em gold.dataset_ml: {extra}"
