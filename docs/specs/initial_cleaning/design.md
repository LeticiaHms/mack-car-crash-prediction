# Technical Design: Initial Data Cleaning & Consolidation

## 1. System Architecture & Components
We will implement a Python-based preprocessing utility using `pandas` and `pyarrow`. The utility will be modularized in a script `src/preprocess.py`.

```text
  [ raw CSVs ] ──► [ src/preprocess.py ] ──► [ curated/acidentes_2022_2026.parquet ]
```

### Components:
1. **Dependency Manager (`requirements.txt`)**: Declares `pandas`, `pyarrow`, and `numpy`.
2. **Preprocessor Engine (`src/preprocess.py`)**:
   - `load_raw_data(file_paths)`: Reads files using `encoding='latin-1'` and separator `;`.
   - `clean_dataframe(df)`: Performs localized string parsing, type casting, text decoding, and duplicate removal.
   - `save_curated_data(df, output_path)`: Writes to a snappy-compressed Parquet file.
   - `main()`: Orchestrates the pipeline and prints logs.

---

## 2. Detailed Data Transformation Logic

### A. Encoding & Reading
- **Raw CSV Encoding**: `latin-1` (or `ISO-8859-1`).
- **Delimiter**: `;`.
- **NA representations**: `"NA"`, `""`, `"nan"`, `"None"`.

### B. Localized Numeric Conversions
Columns `km`, `latitude`, and `longitude` use `,` as the decimal separator in the raw PRF files. 
- **Transformation**: 
  1. Cast to string.
  2. Replace `,` with `.`.
  3. Convert to numeric (`float64`), forcing invalid parses to `NaN` using `pd.to_numeric(..., errors='coerce')`.

### C. Type Castings & Mappings
The pipeline will enforce the following schema in the final Pandas DataFrame before exporting:

| Column | Raw Type | Target Pandas / PyArrow Type | Notes |
| :--- | :--- | :--- | :--- |
| `id` | int / string | `Int64` (nullable integer) | Deduplication key |
| `data_inversa` | string (YYYY-MM-DD) | `datetime64[ns]` | Date representation |
| `horario` | string (HH:MM:SS) | `string` | Time of day |
| `uf`, `br` | string | `string` | Highway & State tags |
| `km` | string with commas | `Float64` | Converted to decimal float |
| `latitude`, `longitude` | string with commas | `Float64` | Converted to decimal float |
| `pessoas`, `mortos`, `feridos_leves`, `feridos_graves`, `ilesos`, `ignorados`, `feridos`, `veiculos` | string / float | `Int64` | Cast to nullable integer |
| Categorical strings | string | `string` | Stripped whitespace and normalized casing |

### D. Deduplication
- We will identify duplicates by the `id` column.
- Duplicates will be resolved by keeping the first occurrence.

### E. Output Specification
- **Path**: `dados/curated/acidentes_2022_2026.parquet`.
- **Format**: Parquet.
- **Compression**: `snappy`.

---

## 3. Implementation Details & Modules
To keep the pipeline robust, the python script will use Python's built-in `logging` module to log steps clearly:
```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```

We will also output some data validation diagnostics:
- Total rows processed vs. rows outputted.
- Count of rows with missing `latitude` or `longitude`.
- Count of severe/fatal accidents versus minor ones.

---

## 4. Verification Plan
- **Unit/Execution Verification**:
  - Run the preprocessing script via command line.
  - Assert the curated Parquet file is successfully created in `dados/curated/`.
- **Data Quality Assertions**:
  - Check that the final row count matches the sum of the input rows (minus duplicates/corrupt rows if any).
  - Verify that `df['latitude'].dtype` and `df['longitude'].dtype` are floats.
  - Verify that there are no unhandled encoding artifacts (e.g. text containing ``).
