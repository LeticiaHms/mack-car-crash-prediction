"""Cada camada consegue ser (re)construída a partir da sua dependência
direta, chamando `create_table(con)` de novo sobre o banco já materializado
(item 16, bloco "Dependências": Bronze consegue ser criada; Silver consegue
ser criada; Gold consegue ser criada)."""


def _count(con, schema, table):
    return con.execute(f"SELECT count(*) FROM {schema}.{table}").fetchone()[0]


def test_bronze_acidentes_e_construida_a_partir_da_raw(write_con):
    from src.bronze import acidentes as bronze_acidentes

    bronze_acidentes.create_table(write_con)
    assert _count(write_con, "bronze", "acidentes") == _count(write_con, "raw", "acidentes")


def test_silver_acidentes_e_construida_a_partir_da_bronze(write_con):
    from src.silver import acidentes as silver_acidentes

    silver_acidentes.create_table(write_con)
    n_silver = _count(write_con, "silver", "acidentes")
    # A Silver nunca é maior que a Bronze: só remove linhas via corte de
    # consolidação (D-13), nunca adiciona (join com feriados é 1:1 por data).
    assert 0 < n_silver <= _count(write_con, "bronze", "acidentes")


def test_gold_dataset_ml_e_construida_a_partir_da_silver(write_con):
    from src.gold import dataset_ml as gold_dataset_ml

    gold_dataset_ml.create_table(write_con)
    # A Gold seleciona/transforma colunas, mas mantém a granularidade
    # "1 linha = 1 acidente" da Silver.
    assert _count(write_con, "gold", "dataset_ml") == _count(write_con, "silver", "acidentes")
