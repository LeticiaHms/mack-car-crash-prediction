import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def verify():
    file_path = 'dados/curated/acidentes_2022_2026.parquet'
    if not pd.io.common.file_exists(file_path):
        logging.error(f"File {file_path} does not exist.")
        return
        
    df = pd.read_parquet(file_path)
    logging.info(f"Loaded {len(df)} records from {file_path}")
    
    # Assertions
    assert len(df) > 0, "Curated dataset is empty"
    assert df['latitude'].dtype == 'float64', f"Expected float64 for latitude, got {df['latitude'].dtype}"
    assert df['longitude'].dtype == 'float64', f"Expected float64 for longitude, got {df['longitude'].dtype}"
    assert df['mortos'].dtype.name == 'Int64', f"Expected Int64 for mortos, got {df['mortos'].dtype}"
    
    logging.info("Verification passed: Types are correct and dataset is not empty.")
    print(df.info())

if __name__ == '__main__':
    verify()
