# Requirements: Initial Data Cleaning & Consolidation

## 1. Overview
The goal of this feature is to implement the first phase of the data pipeline: reading the raw PRF CSV datasets for the years 2022–2026, cleaning and standardizing the schema, and consolidatidating them into a single high-performance **Curated Layer** in Parquet format.

## 2. User Stories
* **As a Data Scientist**, I want to load a unified, typed, and clean historical dataset of highway accidents without worrying about file formats, column types, or parsing errors, so that I can perform reliable exploratory analysis and feature engineering.
* **As an Engineer**, I want the raw ingestion and cleaning script to be fully automated, reproducible, and robust against common CSV issues (such as different decimal separators or encoding anomalies).

## 3. Scope of Work
* Parse raw CSV files: `dados/datatran2022.csv`, `dados/datatran2023.csv`, `dados/datatran2024.csv`, `dados/datatran2025.csv`, and `dados/datatran2026.csv`.
* Combine all years into a single unified dataframe.
* Standardize data types, specifically resolving Brazilian localized formatting (e.g., converting decimal commas `,` to dots `.` in `km`, `latitude`, and `longitude`).
* Handle text encoding (`latin1` / `ISO-8859-1`) to clean and decode textual attributes (e.g., days of week, accident causes).
* Handle missing value placeholders (e.g., converting `"NA"` or empty fields to true `NULL`/`NaN` representations).
* Output a single consolidated, compressed Parquet file to the curated data folder: `dados/curated/acidentes_2022_2026.parquet`.

## 4. Acceptance Criteria
### Functional Requirements
1. **Schema Integrity**: The final curated dataset must have a stable schema with correct data types:
   - `id`: Integer
   - `data_inversa`: Date/Timestamp
   - `horario`: Time string or Time representation
   - `km`, `latitude`, `longitude`: Float / Numeric
   - Victim metrics (`mortos`, `feridos_graves`, `feridos_leves`, `pessoas`, `veiculos`): Integer
2. **Data Consistency**:
   - `latitude` and `longitude` must be valid floats representing coordinates (or NULL/NaN if truly missing, but not string representations with commas).
   - `km` must be a valid float.
3. **No Duplicates**: Any duplicate accident entries (by `id`) must be deduplicated, keeping the most complete or first record.
4. **Encoding Correctness**: Categorical columns like `dia_semana`, `causa_acidente`, and `tipo_acidente` must be properly decoded as UTF-8 in the final output (without corrupted characters like `sbado`).
5. **Output Storage**: The output must be saved in Parquet format with Snappy compression under `dados/curated/acidentes_2022_2026.parquet`.

### Quality & Performance Requirements
- The processing script must run in under 3 minutes locally.
- Logging must print basic statistics at each step (e.g., number of rows loaded per year, number of rows dropped/cleaned, final row count).
