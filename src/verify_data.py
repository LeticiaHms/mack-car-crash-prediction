"""
Verificação de qualidade da camada curada de acidentes da PRF.

Executa um conjunto de validações de schema, tipos, ausência de dados,
duplicidade, intervalos, categorias e consistência entre variáveis sobre
`dados/curated/acidentes_2022_2026.parquet`, e grava um relatório
estruturado em `reports/data_quality/verify_report.json` para fins de
rastreabilidade e auditoria (ver documento técnico,
`docs/docs-etapas/etapa2-pre-processamento.md`, seção 9).
"""
import pandas as pd
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REPORT_PATH = 'reports/data_quality/verify_report.json'


def verify():
    report = {'checks': [], 'status': 'PASSOU'}

    def check(nome, condicao, detalhe=None, severidade='erro'):
        """Registra o resultado de uma validação. `condicao=True` -> OK.
        Quando `condicao` é False e `severidade='erro'`, o script aborta
        (assert). Quando `severidade='aviso'`, o problema é apenas
        registrado no relatório (não interrompe a execução) — reservado
        para condições conhecidas e aceitas (ver documento técnico)."""
        entry = {'check': nome, 'ok': bool(condicao), 'severidade': severidade, 'detalhe': detalhe}
        report['checks'].append(entry)
        if not condicao:
            if severidade == 'erro':
                report['status'] = 'FALHOU'
                logging.error(f"✗ {nome}: {detalhe}")
                raise AssertionError(f"{nome}: {detalhe}")
            else:
                logging.warning(f"⚠ {nome}: {detalhe}")
        else:
            logging.info(f"✓ {nome}")
        return entry

    file_path = 'dados/curated/acidentes_2022_2026.parquet'
    if not pd.io.common.file_exists(file_path):
        logging.error(f"O arquivo {file_path} não existe.")
        report['status'] = 'FALHOU'
        report['erro'] = 'arquivo_inexistente'
        _save_report(report)
        return

    df = pd.read_parquet(file_path)
    logging.info(f"Carregados {len(df)} registros de {file_path}")
    report['linhas'] = int(len(df))
    report['colunas'] = int(len(df.columns))

    # 1. Validação de Quantidade de Colunas
    expected_col_count = 30
    check('quantidade_colunas', len(df.columns) == expected_col_count,
          f"esperado {expected_col_count}, obtido {len(df.columns)}")

    # 2. Validação dos Nomes e Ordem das Colunas (schema)
    expected_columns = [
        'id', 'data_inversa', 'dia_semana', 'horario', 'uf', 'br', 'km', 'municipio',
        'causa_acidente', 'tipo_acidente', 'classificacao_acidente', 'fase_dia', 'sentido_via',
        'condicao_metereologica', 'tipo_pista', 'tracado_via', 'uso_solo', 'pessoas', 'mortos',
        'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos',
        'latitude', 'longitude', 'regional', 'delegacia', 'uop'
    ]
    check('schema_nomes_e_ordem', list(df.columns) == expected_columns,
          f"esperado {expected_columns}, obtido {list(df.columns)}")

    # 3. Validação de Tipos de Dados (Dtypes)
    check('dtype_id', df['id'].dtype.name == 'Int64', str(df['id'].dtype))
    check('dtype_data_inversa', pd.api.types.is_datetime64_any_dtype(df['data_inversa']), str(df['data_inversa'].dtype))
    check('dtype_latitude', df['latitude'].dtype == 'float64', str(df['latitude'].dtype))
    check('dtype_longitude', df['longitude'].dtype == 'float64', str(df['longitude'].dtype))
    check('dtype_km', df['km'].dtype == 'float64', str(df['km'].dtype))

    victim_cols = ['pessoas', 'mortos', 'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos']
    for col in victim_cols:
        check(f'dtype_{col}', df[col].dtype.name == 'Int64', str(df[col].dtype))

    # 4. Duplicidade: por id (chave de negócio) e por linha inteira
    check('unicidade_id', bool(df['id'].is_unique), f"{df['id'].duplicated().sum()} ids duplicados")
    linhas_duplicadas = int(df.duplicated().sum())
    check('linhas_totalmente_duplicadas', linhas_duplicadas == 0, f"{linhas_duplicadas} linhas idênticas em todas as colunas")

    # 5. Valores nulos em colunas críticas (não podem faltar)
    critical_non_nulls = ['id', 'data_inversa', 'latitude', 'longitude', 'km', 'classificacao_acidente']
    missing_report = {}
    for col in df.columns:
        n = int(df[col].isnull().sum())
        if n:
            missing_report[col] = {'nulos': n, 'pct': round(n / len(df) * 100, 3)}
    report['missing_values'] = missing_report
    for col in critical_non_nulls:
        null_count = int(df[col].isnull().sum())
        check(f'sem_nulos_{col}', null_count == 0, f"{null_count} nulos")

    # 5b. Colunas administrativas com ausência conhecida e tolerada (não
    #     imputadas — ver seção 5 do documento técnico). Falha apenas se o
    #     percentual ultrapassar um limite muito acima do observado, o que
    #     indicaria uma regressão de qualidade em uma nova carga de dados.
    for col, limite_pct in [('regional', 5.0), ('delegacia', 5.0), ('uop', 5.0)]:
        pct = df[col].isnull().sum() / len(df) * 100
        check(f'nulos_{col}_dentro_do_esperado', pct <= limite_pct,
              f"{pct:.2f}% nulos (limite tolerado: {limite_pct}%)", severidade='aviso')

    # 6. Validação de Intervalos de Valores (Consistência de Negócio)
    anos_presentes = sorted(int(a) for a in df['data_inversa'].dt.year.dropna().unique())
    anos_validos = {2022, 2023, 2024, 2025, 2026}
    check('anos_dentro_do_esperado', set(anos_presentes).issubset(anos_validos), f"anos encontrados: {anos_presentes}")

    expected_days = {'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo'}
    actual_days = set(df['dia_semana'].dropna().unique())
    invalid_days = actual_days - expected_days
    check('dias_semana_validos', len(invalid_days) == 0, f"valores inesperados: {invalid_days}")

    expected_ufs = {
        'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
        'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
    }
    actual_ufs = set(df['uf'].dropna().unique())
    invalid_ufs = actual_ufs - expected_ufs
    check('ufs_validas', len(invalid_ufs) == 0, f"UFs inválidas: {invalid_ufs}")

    check('latitude_dentro_do_brasil', df['latitude'].min() >= -35 and df['latitude'].max() <= 6,
          f"[{df['latitude'].min()}, {df['latitude'].max()}]")
    check('longitude_dentro_do_brasil', df['longitude'].min() >= -75 and df['longitude'].max() <= -30,
          f"[{df['longitude'].min()}, {df['longitude'].max()}]")

    for col in victim_cols:
        check(f'nao_negativo_{col}', df[col].min() >= 0, f"mínimo observado: {df[col].min()}")

    # 7. Consistência entre variáveis
    fl, fg, fe = df['feridos_leves'], df['feridos_graves'], df['feridos']
    mismatch_feridos = int(((fl + fg) != fe).sum())
    check('consistencia_feridos_leves_mais_graves_igual_feridos', mismatch_feridos == 0, f"{mismatch_feridos} divergências")

    soma_categorias = (
        df['mortos'].fillna(0) + df['feridos_leves'].fillna(0) + df['feridos_graves'].fillna(0)
        + df['ilesos'].fillna(0) + df['ignorados'].fillna(0)
    )
    divergentes = int((soma_categorias != df['pessoas']).sum())
    # Conhecido e documentado: inconsistência de origem na base da PRF
    # (16.817 registros / 5,39% no dataset bruto). Não é corrigido, apenas
    # monitorado — reportado como aviso, não como erro.
    check('consistencia_pessoas_igual_soma_categorias', divergentes == 0,
          f"{divergentes} registros ({divergentes / len(df) * 100:.2f}%) com 'pessoas' != soma das categorias "
          f"(inconsistência de origem na base da PRF, documentada e monitorada, não corrigida)",
          severidade='aviso')
    report['pct_pessoas_divergente_da_soma'] = round(divergentes / len(df) * 100, 3)

    def classifica(row):
        if row['mortos'] and row['mortos'] > 0:
            return 'Com Vítimas Fatais'
        if (row['feridos_leves'] and row['feridos_leves'] > 0) or (row['feridos_graves'] and row['feridos_graves'] > 0):
            return 'Com Vítimas Feridas'
        return 'Sem Vítimas'

    esperado = df.apply(classifica, axis=1)
    mismatch_class = int((esperado != df['classificacao_acidente']).sum())
    check('consistencia_classificacao_vs_vitimas', mismatch_class == 0, f"{mismatch_class} divergências")

    report['status'] = 'FALHOU' if any(not c['ok'] and c['severidade'] == 'erro' for c in report['checks']) else 'PASSOU'
    _save_report(report)

    logging.info("Parabéns! Todas as validações críticas passaram com sucesso.")
    print("\nResumo das informações do DataFrame curado:")
    print(df.info())


def _save_report(report):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    logging.info(f"Relatório de verificação salvo em {REPORT_PATH}")


if __name__ == '__main__':
    verify()
