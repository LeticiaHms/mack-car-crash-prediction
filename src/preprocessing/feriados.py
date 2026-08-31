"""
Pré-processamento da base de feriados nacionais da ANBIMA.

Lê o arquivo bruto (`dados/feriados_nacionais.xls`), remove o rodapé de
notas explicativas que acompanha a planilha, padroniza tipos, filtra para
o período de interesse do projeto (2022-2026) e grava a camada curada em
Parquet (`dados/curated/feriados_nacionais.parquet`).

Esta base é utilizada exclusivamente como fonte complementar para
derivação de features temporais (ex.: indicar se um acidente ocorreu em
dia de feriado nacional), conforme `docs/spec.md`.

Todas as decisões de tratamento estão documentadas em
`docs/docs-etapas/etapa1-pre-processamento.md`.
"""
import pandas as pd
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RAW_PATH = 'dados/feriados_nacionais.xls'
CURATED_PATH = 'dados/curated/feriados_nacionais.parquet'
SHEET_NAME = 'Feriados'

# Período de dados de acidentes utilizado pelo projeto (docs/spec.md,
# seção 7). O arquivo bruto da ANBIMA cobre 2001-2099; filtramos para este
# intervalo pois a base de feriados é usada apenas como apoio para
# derivação de features temporais dos acidentes (cruzamento por data), não
# como unidade de análise própria — manter décadas fora do período
# estudado só adiciona ruído à camada curada, sem nenhum uso posterior.
ANO_MIN = 2022
ANO_MAX = 2026

# Colunas na planilha original (nomes com espaços/acentos), mapeadas para
# nomes padronizados (snake_case), seguindo a mesma convenção adotada para
# a base de acidentes da PRF.
COLUMN_RENAME = {
    'Data': 'data',
    'Dia da Semana': 'dia_semana',
    'Feriado': 'feriado',
}


def load_raw_data(file_path=RAW_PATH):
    logging.info(f"Carregando {file_path}...")
    # Arquivo .xls legado; requer o engine 'xlrd' para leitura.
    df = pd.read_excel(file_path, sheet_name=SHEET_NAME, engine='xlrd')
    logging.info(f"  -> {len(df)} linhas, {len(df.columns)} colunas (inclui rodapé de notas).")
    return df


def clean_dataframe(df):
    logging.info("Limpando o dataframe de feriados...")
    stats = {}
    stats['linhas_entrada'] = int(len(df))

    df = df.rename(columns=COLUMN_RENAME)

    # 1. Remoção do rodapé de notas explicativas.
    #    A planilha da ANBIMA traz, após a última data válida, linhas de
    #    texto livre (ex.: "Fonte: ANBIMA", notas numeradas sobre pontos
    #    facultativos) nas quais a coluna 'data' não contém uma data.
    #    Identificamos essas linhas convertendo 'data' para datetime: o
    #    texto de rodapé produz NaT e é descartado. Não é uma remoção às
    #    cegas de nulos — cada linha descartada foi inspecionada
    #    manualmente e confirmada como nota de rodapé, não um registro de
    #    feriado incompleto.
    data_convertida = pd.to_datetime(df['data'], errors='coerce')
    mask_rodape = data_convertida.isnull()
    stats['linhas_rodape_removidas'] = int(mask_rodape.sum())
    df = df.loc[~mask_rodape].copy()
    df['data'] = data_convertida.loc[~mask_rodape]

    # 2. Padronização de texto: remover espaços em branco nas bordas das
    #    colunas categóricas/textuais.
    for col in ['dia_semana', 'feriado']:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # 3. 'data' já convertida para datetime na etapa 1.
    #    'dia_semana' e 'feriado' permanecem como texto/categoria.

    # 4. Valores ausentes: não há valores ausentes nas linhas de dados
    #    válidas (verificado no diagnóstico inicial). Nenhuma imputação é
    #    necessária.
    missing = df[['data', 'dia_semana', 'feriado']].isnull().sum()
    stats['nulos_por_coluna'] = {k: int(v) for k, v in missing.items()}

    # 5. Deduplicação. Uma mesma data pode legitimamente conter mais de um
    #    feriado nomeado (ex.: 2079-04-21 possui "Paixão de Cristo" e
    #    "Tiradentes" coincidindo por serem, respectivamente, uma data
    #    móvel e uma data fixa) — portanto a deduplicação não deve usar
    #    apenas 'data'. A chave de unicidade é a combinação
    #    ('data', 'feriado'), e duplicidade de linha inteira é removida
    #    como salvaguarda adicional.
    initial_count = len(df)
    df = df.drop_duplicates(subset=['data', 'feriado'], keep='first')
    stats['duplicatas_data_feriado_removidas'] = int(initial_count - len(df))

    linhas_completamente_duplicadas = int(df.duplicated().sum())
    stats['linhas_completamente_duplicadas'] = linhas_completamente_duplicadas

    # 6. Consistência 'dia_semana' vs. 'data': valida se o dia da semana
    #    informado bate com o calculado a partir da própria data
    #    (diagnóstico apenas — nenhuma linha é alterada ou removida por
    #    causa disso, ver documento técnico).
    dias_pt = {
        0: 'segunda-feira', 1: 'terça-feira', 2: 'quarta-feira', 3: 'quinta-feira',
        4: 'sexta-feira', 5: 'sábado', 6: 'domingo',
    }
    dia_calculado = df['data'].dt.dayofweek.map(dias_pt)
    divergentes = int((dia_calculado != df['dia_semana']).sum())
    stats['linhas_dia_semana_divergente'] = divergentes
    if divergentes:
        logging.warning(f"{divergentes} registros com 'dia_semana' divergente do calculado a partir de 'data'.")

    # 7. Filtro do período de interesse do projeto (2022-2026). O arquivo
    #    bruto traz o histórico completo de feriados (2001-2099) mantido
    #    pela ANBIMA, mas o projeto só utiliza os anos correspondentes aos
    #    dados de acidentes da PRF (docs/spec.md, seção 7). Registros fora
    #    desse intervalo são descartados aqui, e não antes, para que as
    #    validações de padronização/deduplicação acima sejam feitas sobre
    #    a base íntegra.
    linhas_antes_filtro = len(df)
    df = df[df['data'].dt.year.between(ANO_MIN, ANO_MAX)].copy()
    stats['linhas_fora_do_periodo_removidas'] = int(linhas_antes_filtro - len(df))

    df = df.sort_values('data').reset_index(drop=True)

    stats['linhas_saida'] = int(len(df))
    df.attrs['clean_stats'] = stats
    return df


def save_curated_data(df, output_path=CURATED_PATH):
    logging.info(f"Salvando em {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, engine='pyarrow', compression='snappy')
    logging.info("Salvamento concluído.")


def save_run_report(stats, output_path='reports/data_quality/preprocess_feriados_report.json'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logging.info(f"Relatório de execução do pré-processamento salvo em {output_path}")


def main():
    if not os.path.exists(RAW_PATH):
        logging.error(f"Arquivo bruto não encontrado: {RAW_PATH}")
        return

    df = load_raw_data()
    linhas_brutas = len(df)
    df = clean_dataframe(df)
    stats = df.attrs.get('clean_stats', {})
    stats['linhas_brutas_carregadas'] = int(linhas_brutas)
    stats['arquivo_processado'] = RAW_PATH

    save_curated_data(df)
    save_run_report(stats)


if __name__ == '__main__':
    main()
