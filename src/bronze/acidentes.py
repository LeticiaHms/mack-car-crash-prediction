"""
Pré-processamento dos dados de acidentes da PRF (2022-2026) — camada Bronze.

Parte de `raw.acidentes` (`src/raw/acidentes.py`), padroniza tipos e formatos,
trata valores ausentes de forma documentada, remove duplicidades e materializa
a tabela `bronze.acidentes` no DuckDB (`src/database/connection.py`).

Todas as decisões de tratamento estão documentadas em
`docs/entregas/etapa1-pre-processamento.md`. A camada Silver
(`src/silver/acidentes.py`) parte desta tabela para aplicar o corte de
consolidação e o enriquecimento analítico.
"""
import pandas as pd
import numpy as np
import os
import glob
import json
import logging

from src.database.connection import create_table_from_df, ensure_schemas, get_connection, table_exists
from src.raw import acidentes as raw_acidentes

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Colunas com metadados textuais/numéricos conhecidos, na ordem original da PRF
NUMERIC_COMMA_COLS = ['km', 'latitude', 'longitude']
METRIC_COLS = ['pessoas', 'mortos', 'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos']
TEXT_COLS = [
    'dia_semana', 'horario', 'uf', 'municipio', 'causa_acidente', 'tipo_acidente',
    'classificacao_acidente', 'fase_dia', 'sentido_via', 'condicao_metereologica',
    'tipo_pista', 'tracado_via', 'uso_solo', 'regional', 'delegacia', 'uop',
]

# Reexportados por compatibilidade: a leitura bruta do CSV agora é
# responsabilidade de `src.raw.acidentes` (parsing de arquivo, não regra de
# negócio) — Bronze só faz a limpeza a partir dela.
NA_TOKENS = raw_acidentes.NA_TOKENS
load_raw_data = raw_acidentes.load_raw_data


def clean_dataframe(df):
    logging.info("Limpando o dataframe...")
    stats = {}
    stats['linhas_entrada'] = int(len(df))

    # 0. Padronização de texto: remover espaços em branco nas bordas das
    #    colunas categóricas/textuais (defensivo — nenhuma ocorrência foi
    #    encontrada nos dados atuais, mas protege contra novas cargas).
    for col in TEXT_COLS:
        if col in df.columns and (df[col].dtype == object or pd.api.types.is_string_dtype(df[col])):
            df[col] = df[col].str.strip()

    # 1. Limpar colunas numéricas com vírgula decimal (padrão brasileiro:
    #    'km', 'latitude' e 'longitude' chegam como texto, ex: "-7,4328").
    for col in NUMERIC_COMMA_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').replace('nan', np.nan)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 2. Conversão de tipos estrita (Type Casting)
    # Métricas de vítimas/contagens para Int64 (nullable)
    for col in METRIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

    # id para Int64. pd.to_numeric já resolve corretamente casos de
    # formatação numérica não usual (ex.: notação científica "6e+05"
    # encontrada em 1 registro de data/datatran2024.csv), convertendo
    # para o valor inteiro correspondente sem gerar NaN.
    if 'id' in df.columns:
        ids_antes_nulos = df['id'].isnull().sum()
        df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
        ids_depois_nulos = int(df['id'].isnull().sum())
        stats['ids_nao_parseaveis'] = ids_depois_nulos - int(ids_antes_nulos)

    # data_inversa para datetime
    if 'data_inversa' in df.columns:
        df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')

    # 3. Tratamento de valores ausentes em 'classificacao_acidente'.
    #    Diagnóstico: a coluna possui apenas 5 valores ausentes (0,002%) em
    #    todo o dataset combinado. Nos 311.746 registros não-nulos restantes,
    #    a regra abaixo (derivada de mortos/feridos_leves/feridos_graves)
    #    reproduz 100% dos valores observados de 'classificacao_acidente'
    #    (0 divergências verificadas em diagnóstico prévio). Por isso, a
    #    regra é aplicada apenas para preencher os 5 registros ausentes,
    #    em vez de descartá-los ou deixá-los como NaN — é uma inferência
    #    validada empiricamente contra os próprios dados, não um valor
    #    inventado. Colunas administrativas (regional/delegacia/uop), que
    #    não possuem regra determinística equivalente, são mantidas como
    #    NaN (ver seção 5 do documento técnico).
    if 'classificacao_acidente' in df.columns:
        mask_nulo = df['classificacao_acidente'].isnull()
        stats['classificacao_ausente_antes'] = int(mask_nulo.sum())
        if mask_nulo.any():
            mortos = df.loc[mask_nulo, 'mortos']
            leves = df.loc[mask_nulo, 'feridos_leves']
            graves = df.loc[mask_nulo, 'feridos_graves']
            inferido = np.where(
                mortos.fillna(0) > 0, 'Com Vítimas Fatais',
                np.where((leves.fillna(0) > 0) | (graves.fillna(0) > 0), 'Com Vítimas Feridas', 'Sem Vítimas')
            )
            df.loc[mask_nulo, 'classificacao_acidente'] = inferido
        stats['classificacao_ausente_depois'] = int(df['classificacao_acidente'].isnull().sum())

    # 4. Deduplicação por 'id' (chave de negócio). Mantém a primeira
    #    ocorrência em caso de duplicidade.
    initial_count = len(df)
    df = df.drop_duplicates(subset=['id'], keep='first')
    stats['duplicatas_por_id_removidas'] = int(initial_count - len(df))
    logging.info(f"Removidas {initial_count - len(df)} duplicatas por id. Restantes: {len(df)}")

    # 5. Verificação de duplicidade de linha inteira (todas as colunas),
    #    como salvaguarda adicional independente do id.
    linhas_completamente_duplicadas = int(df.duplicated().sum())
    stats['linhas_completamente_duplicadas'] = linhas_completamente_duplicadas
    if linhas_completamente_duplicadas:
        logging.warning(f"{linhas_completamente_duplicadas} linhas totalmente duplicadas detectadas (todas as colunas).")

    # 6. Diagnóstico de consistência entre colunas (não corrigido
    #    automaticamente — ver justificativa no documento técnico, seção 3
    #    e seção 4). Reportado apenas via log/estatísticas para
    #    rastreabilidade; os valores originais são preservados.
    soma_categorias = (
        df['mortos'].fillna(0) + df['feridos_leves'].fillna(0) + df['feridos_graves'].fillna(0)
        + df['ilesos'].fillna(0) + df['ignorados'].fillna(0)
    )
    divergentes = int((soma_categorias != df['pessoas']).sum())
    stats['linhas_pessoas_divergente_da_soma'] = divergentes
    logging.info(
        f"{divergentes} registros ({divergentes / len(df) * 100:.2f}%) com 'pessoas' "
        f"diferente da soma de mortos+feridos_leves+feridos_graves+ilesos+ignorados "
        f"(inconsistência de origem na base da PRF; não corrigida — ver documento técnico)."
    )

    # 7. Diagnóstico de outliers (apenas sinalização/registro, sem remoção
    #    de linhas — ver seção 8 do documento técnico para a justificativa
    #    de cada variável).
    outlier_stats = {}
    for col in ['km', 'pessoas', 'mortos', 'feridos_leves', 'feridos_graves', 'veiculos']:
        s = df[col].astype('float64')
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_out = int(((s < lower) | (s > upper)).sum())
        outlier_stats[col] = {'q1': float(q1), 'q3': float(q3), 'lower': float(lower), 'upper': float(upper), 'outliers': n_out}
    stats['outliers_iqr'] = outlier_stats
    logging.info(f"Diagnóstico de outliers (IQR) calculado para: {list(outlier_stats.keys())}")

    stats['linhas_saida'] = int(len(df))
    df.attrs['clean_stats'] = stats
    return df


def save_run_report(stats, output_path='reports/data_quality/preprocess_report.json'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logging.info(f"Relatório de execução do pré-processamento salvo em {output_path}")


def build_bronze(raw_df: pd.DataFrame | None = None) -> tuple:
    """Aplica a limpeza da Bronze sobre o DataFrame bruto e devolve (df, stats).

    `raw_df=None` (uso standalone, ex.: `python -m src.bronze.acidentes`) lê
    os CSVs diretamente via `src.raw.acidentes.load_raw_data`; quando chamado
    a partir de `create_table(con)`, recebe `raw.acidentes` já materializada
    no DuckDB, para que a dependência raw -> bronze fique explícita.
    """
    if raw_df is None:
        raw_files = glob.glob('data/raw/datatran*.csv')
        if not raw_files:
            raise FileNotFoundError("Nenhum arquivo CSV bruto encontrado em data/raw/")
        raw_df = load_raw_data(raw_files)
        arquivos_processados = sorted(raw_files)
    else:
        arquivos_processados = None

    linhas_brutas = len(raw_df)
    df = clean_dataframe(raw_df)
    stats = df.attrs.get('clean_stats', {})
    stats['linhas_brutas_carregadas'] = int(linhas_brutas)
    if arquivos_processados is not None:
        stats['arquivos_processados'] = arquivos_processados
    return df, stats


def create_table(con=None) -> tuple:
    """Materializa `bronze.acidentes` no DuckDB a partir de `raw.acidentes`
    (criando-a primeiro se ainda não existir) e grava o relatório de execução
    do pré-processamento. Devolve `(df, stats)` — o DataFrame ainda com os
    dtypes originais do pandas (`Int64` nullable), que é o que a validação em
    `src/bronze/validation.py` verifica."""
    own_con = con is None
    if own_con:
        con = get_connection()
    ensure_schemas(con)

    if not table_exists(con, "raw", "acidentes"):
        raw_acidentes.create_table(con)
    raw_df = con.execute("SELECT * FROM raw.acidentes").df()

    df, stats = build_bronze(raw_df)

    save_run_report(stats)
    create_table_from_df(con, "bronze", "acidentes", df)
    logging.info(f"bronze.acidentes materializada: {len(df)} linhas, {len(df.columns)} colunas.")

    if own_con:
        con.close()
    return df, stats


def main():
    create_table()


if __name__ == '__main__':
    main()
