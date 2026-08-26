import pandas as pd
import numpy as np
import os
import glob
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_raw_data(file_paths):
    logging.info(f"Carregando {len(file_paths)} arquivos...")
    dfs = []
    for file in file_paths:
        logging.info(f"Lendo {file}...")
        # Arquivos da PRF possuem codificação latin-1 e separador ';'
        df = pd.read_csv(file, encoding='latin-1', sep=';', low_memory=False)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    logging.info(f"Carregados {len(combined_df)} registros no total.")
    return combined_df

def clean_dataframe(df):
    logging.info("Limpando o dataframe...")
    
    # 1. Limpar colunas numéricas com vírgula decimal
    numeric_cols = ['km', 'latitude', 'longitude']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').replace('nan', np.nan)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 2. Conversão de tipos estrita (Type Casting)
    # Métricas de vítimas/contagens para Int64
    metric_cols = ['pessoas', 'mortos', 'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos']
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
    # id para Int64
    if 'id' in df.columns:
        df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
        
    # data_inversa para datetime
    if 'data_inversa' in df.columns:
        df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')

    # 3. Deduplicação
    initial_count = len(df)
    df = df.drop_duplicates(subset=['id'], keep='first')
    logging.info(f"Removidas {initial_count - len(df)} duplicatas. Restantes: {len(df)}")
    
    return df

def save_curated_data(df, output_path):
    logging.info(f"Salvando em {output_path}...")
    df.to_parquet(output_path, engine='pyarrow', compression='snappy')
    logging.info("Salvamento concluído.")

def main():
    raw_files = glob.glob('dados/datatran*.csv')
    if not raw_files:
        logging.error("Nenhum arquivo CSV bruto encontrado em dados/")
        return
        
    df = load_raw_data(raw_files)
    df = clean_dataframe(df)
    
    os.makedirs('dados/curated', exist_ok=True)
    save_curated_data(df, 'dados/curated/acidentes_2022_2026.parquet')

if __name__ == '__main__':
    main()
