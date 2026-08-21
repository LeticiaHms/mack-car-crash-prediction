import pandas as pd
import numpy as np
import os
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_raw_data(file_paths):
    logging.info(f"Loading {len(file_paths)} files...")
    dfs = []
    for file in file_paths:
        logging.info(f"Reading {file}...")
        # PRF files have encoding latin-1 and separator ';'
        df = pd.read_csv(file, encoding='latin-1', sep=';', low_memory=False)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    logging.info(f"Loaded {len(combined_df)} total records.")
    return combined_df

def clean_dataframe(df):
    logging.info("Cleaning dataframe...")
    
    # 1. Clean numeric columns with decimal commas
    numeric_cols = ['km', 'latitude', 'longitude']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').replace('nan', np.nan)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 2. Strict type casting
    # Victim/Count metrics to Int64
    metric_cols = ['pessoas', 'mortos', 'feridos_leves', 'feridos_graves', 'ilesos', 'ignorados', 'feridos', 'veiculos']
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
    # id to Int64
    if 'id' in df.columns:
        df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
        
    # data_inversa to datetime
    if 'data_inversa' in df.columns:
        df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')

    # 3. Deduplication
    initial_count = len(df)
    df = df.drop_duplicates(subset=['id'], keep='first')
    logging.info(f"Deduplicated {initial_count - len(df)} records. Remaining: {len(df)}")
    
    return df

def save_curated_data(df, output_path):
    logging.info(f"Saving to {output_path}...")
    df.to_parquet(output_path, engine='pyarrow', compression='snappy')
    logging.info("Save complete.")

def main():
    raw_files = glob.glob('dados/datatran*.csv')
    if not raw_files:
        logging.error("No raw CSV files found in dados/")
        return
        
    df = load_raw_data(raw_files)
    df = clean_dataframe(df)
    
    os.makedirs('dados/curated', exist_ok=True)
    save_curated_data(df, 'dados/curated/acidentes_2022_2026.parquet')

if __name__ == '__main__':
    main()
