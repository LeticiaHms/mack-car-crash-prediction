# Task List: Initial Data Cleaning & Consolidation

## 1. Setup Phase
- [ ] **Task 1.1**: Create `requirements.txt` with required libraries: `pandas`, `pyarrow`, and `numpy`.
- [ ] **Task 1.2**: Set up environment (install requirements).
- [ ] **Task 1.3**: Scaffold the `src/` directory and create the `src/preprocess.py` entry point.

## 2. Ingestion & Preprocessing Phase
- [ ] **Task 2.1**: Implement raw data loading in `src/preprocess.py` (read CSVs with latin-1 encoding, semicolon separator, and NA mappings).
- [ ] **Task 2.2**: Implement localized data transformations:
  - Clean `km`, `latitude`, and `longitude` fields (commas to dots, cast to float).
- [ ] **Task 2.3**: Implement strict type casting:
  - Cast victim metric columns (`pessoas`, `mortos`, etc.) to nullable integer types (`Int64`).
  - Cast `id` to `Int64` and `data_inversa` to `datetime64[ns]`.
- [ ] **Task 2.4**: Implement deduplication on `id` column.
- [ ] **Task 2.5**: Implement parquet output saving to `dados/curated/acidentes_2022_2026.parquet`.

## 3. Verification Phase
- [ ] **Task 3.1**: Create verification script `src/verify_data.py` to inspect the final curated parquet, asserting data types, rows, and non-empty columns.
- [ ] **Task 3.2**: Execute the complete preprocessing and verification pipeline to ensure successful curation of the datasets.
