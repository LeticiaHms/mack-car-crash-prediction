import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify():
    file_path = 'dados/curated/acidentes_2022_2026.parquet'
    if not pd.io.common.file_exists(file_path):
        logging.error(f"O arquivo {file_path} não existe.")
        return
        
    df = pd.read_parquet(file_path)
    logging.info(f"Carregados {len(df)} registros de {file_path}")
    
    # 1. Validação de Quantidade de Colunas
    expected_col_count = 30
    actual_col_count = len(df.columns)
    assert actual_col_count == expected_col_count, (
        f"Esperava {expected_col_count} colunas, mas o dataset possui {actual_col_count} colunas."
    )
    logging.info("✓ Quantidade de colunas validada (30 colunas).")
    
    # 2. Validação dos Nomes das Colunas
    expected_columns = [
        'id', 'data_inversa', 'dia_semana', 'horario', 'uf', 'br', 'km', 'municipio', 
        'causa_acidente', 'tipo_acidente', 'classificacao_acidente', 'fase_dia', 'sentido_via', 
        'condicao_metereologica', 'tipo_pista', 'tracado_via', 'uso_solo', 'pessoas', 'mortos', 
        'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos', 
        'latitude', 'longitude', 'regional', 'delegacia', 'uop'
    ]
    actual_columns = list(df.columns)
    assert actual_columns == expected_columns, (
        f"Os nomes ou a ordem das colunas não coincidem.\n"
        f"Esperado: {expected_columns}\n"
        f"Obtido: {actual_columns}"
    )
    logging.info("✓ Nomes e ordem das colunas validados.")

    # 3. Validação de Tipos de Dados (Dtypes)
    assert df['id'].dtype.name == 'Int64', f"Esperado Int64 para 'id', obtido {df['id'].dtype}"
    assert pd.api.types.is_datetime64_any_dtype(df['data_inversa']), f"Esperado datetime para 'data_inversa', obtido {df['data_inversa'].dtype}"
    assert df['latitude'].dtype == 'float64', f"Esperado float64 para 'latitude', obtido {df['latitude'].dtype}"
    assert df['longitude'].dtype == 'float64', f"Esperado float64 para 'longitude', obtido {df['longitude'].dtype}"
    assert df['km'].dtype == 'float64', f"Esperado float64 para 'km', obtido {df['km'].dtype}"
    
    # Validação de dtypes para contagens de vítimas e veículos
    victim_cols = ['pessoas', 'mortos', 'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos']
    for col in victim_cols:
        assert df[col].dtype.name == 'Int64', f"Esperado Int64 para a coluna '{col}', obtido {df[col].dtype}"
    
    logging.info("✓ Tipos de dados (dtypes) críticos validados.")

    # 4. Validação de Não-Duplicidade de IDs
    assert df['id'].is_unique, "O dataset contém IDs duplicados (falha de deduplicação)."
    logging.info("✓ Unicidade de IDs validada (sem registros duplicados).")

    # 5. Validação de Valores Nulos em Colunas Críticas
    critical_non_nulls = ['id', 'data_inversa', 'latitude', 'longitude', 'km']
    for col in critical_non_nulls:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"A coluna crítica '{col}' possui {null_count} valores nulos inesperados."
    logging.info("✓ Ausência de nulos em colunas críticas validada.")

    # 6. Validação de Intervalos de Valores (Consistência de Negócio)
    # Temporal: Anos esperados de 2022 a 2026
    anos_presentes = df['data_inversa'].dt.year.unique()
    for ano in anos_presentes:
        assert ano in [2022, 2023, 2024, 2025, 2026], f"Ano {ano} inesperado encontrado no dataset."
        
    # Dias da semana em português e sem problemas de caracteres
    expected_days = {'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo'}
    actual_days = set(df['dia_semana'].unique())
    invalid_days = actual_days - expected_days
    assert len(invalid_days) == 0, f"Dias da semana inválidos ou com erro de codificação encontrados: {invalid_days}"
    
    # Estados brasileiros (UFs) válidos
    expected_ufs = {
        'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 
        'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
    }
    actual_ufs = set(df['uf'].unique())
    invalid_ufs = actual_ufs - expected_ufs
    assert len(invalid_ufs) == 0, f"UFs inválidas encontradas no dataset: {invalid_ufs}"
    
    # Coordenadas geográficas dentro da caixa delimitadora do Brasil (aproximada)
    # Latitude de -35 a 6 graus
    assert df['latitude'].min() >= -35 and df['latitude'].max() <= 6, (
        f"Latitude fora da caixa geográfica do Brasil: [{df['latitude'].min()}, {df['latitude'].max()}]"
    )
    # Longitude de -75 a -30 graus
    assert df['longitude'].min() >= -75 and df['longitude'].max() <= -30, (
        f"Longitude fora da caixa geográfica do Brasil: [{df['longitude'].min()}, {df['longitude'].max()}]"
    )
    
    # Métricas de contagem não-negativas
    for col in victim_cols:
        assert df[col].min() >= 0, f"Valores negativos detectados na coluna de contagem '{col}'."
        
    logging.info("✓ Consistência de valores e regras de negócio validadas.")
    logging.info("Parabéns! Todas as validações passaram com sucesso.")
    print("\nResumo das informações do DataFrame curado:")
    print(df.info())

if __name__ == '__main__':
    verify()
