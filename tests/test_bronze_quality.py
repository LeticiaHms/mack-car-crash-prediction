"""As validações de qualidade da Bronze (`src/bronze/validation.py`) continuam
passando — item "Qualidade" da suíte.

A validação de produção roda sobre o DataFrame em memória, dentro do pipeline
(ver `src/jobs/build_database.py`): é o único momento em que os dtypes nullable
do pandas (`Int64`) existem exatamente como a limpeza os produziu. Por isso os
testes aqui checam as duas pontas:

1. o relatório gravado pela execução real do pipeline (evidência do que rodou);
2. uma reexecução ao vivo de `validate_feriados` sobre `bronze.feriados` lida do
   banco — tabela pequena e sem colunas inteiras nullable, então o round-trip
   pelo DuckDB não altera nenhum dtype que a validação verifique.
"""
import json

from src.bronze import validation


def _load_report(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_relatorio_de_validacao_de_acidentes_passou(built_database):
    report = _load_report(validation.ACIDENTES_REPORT_PATH)
    assert report["status"] == "PASSOU"
    # o relatório precisa conter as checagens críticas, não só o status
    checks = {c["check"] for c in report["checks"]}
    for esperado in ("schema_nomes_e_ordem", "dtype_id", "unicidade_id", "ufs_validas"):
        assert esperado in checks, f"checagem '{esperado}' ausente no relatório"


def test_relatorio_de_validacao_de_feriados_passou(built_database):
    report = _load_report(validation.FERIADOS_REPORT_PATH)
    assert report["status"] == "PASSOU"


def test_validacao_de_feriados_roda_sobre_a_tabela_do_banco(con):
    df = con.execute("SELECT * FROM bronze.feriados").df()
    report = validation.validate_feriados(df)
    assert report["status"] == "PASSOU"
