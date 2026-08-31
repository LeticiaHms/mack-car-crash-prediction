# Task List: Initial Data Cleaning & Consolidation

> Nota (2026-08-31): esta task list original cobria só a base de acidentes e
> referenciava `src/preprocess.py`/`src/verify_data.py`. O código evoluiu para
> a estrutura de pacote `src/preprocessing/` (`acidentes.py`, `feriados.py`,
> `validation.py`) orquestrada por `src/pipeline.py`, e passou a cobrir também
> a base de feriados nacionais (ANBIMA). Os itens abaixo são marcados como
> concluídos com o caminho atual entre parênteses onde mudou. Ver
> `docs/docs-etapas/etapa1-pre-processamento.md` para o relatório técnico.

## 1. Setup Phase
- [x] **Task 1.1**: Create `requirements.txt` with required libraries: `pandas`, `pyarrow`, and `numpy` (também `xlrd`, para ler `feriados_nacionais.xls`).
- [x] **Task 1.2**: Set up environment (install requirements).
- [x] **Task 1.3**: Scaffold the `src/` directory and create the entry point (`src/preprocessing/acidentes.py`, não mais `src/preprocess.py`).

## 2. Ingestion & Preprocessing Phase
- [x] **Task 2.1**: Implement raw data loading in `src/preprocessing/acidentes.py` (read CSVs with latin-1 encoding, semicolon separator, and NA mappings).
- [x] **Task 2.2**: Implement localized data transformations:
  - Clean `km`, `latitude`, and `longitude` fields (commas to dots, cast to float).
- [x] **Task 2.3**: Implement strict type casting:
  - Cast victim metric columns (`pessoas`, `mortos`, etc.) to nullable integer types (`Int64`).
  - Cast `id` to `Int64` and `data_inversa` to `datetime64[ns]`.
- [x] **Task 2.4**: Implement deduplication on `id` column.
- [x] **Task 2.5**: Implement parquet output saving to `dados/curated/acidentes_2022_2026.parquet`.
- [x] **Task 2.6** (adicionada): Implement preprocessing for the ANBIMA national holidays file (`src/preprocessing/feriados.py`) — remove footer notes, deduplicate by `(data, feriado)`, filter to the project's 2022-2026 period, save to `dados/curated/feriados_nacionais.parquet`.

## 3. Verification Phase
- [x] **Task 3.1**: Create verification module (`src/preprocessing/validation.py`, não mais `src/verify_data.py`) com `validate_acidentes` e `validate_feriados`, para inspecionar os parquets curados (schema, dtypes, nulos, duplicidade, categorias e consistência).
- [x] **Task 3.2**: Execute the complete preprocessing and verification pipeline (`python3 -m src.pipeline` ou `python3 src/pipeline.py`) to ensure successful curation of both datasets.
