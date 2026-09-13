---
name: data-ingestion
description: Ingest PRF open accident CSV datasets into validated, reproducible Parquet datasets.
---

# Data Ingestion

## Responsibilities
- Discover and inspect PRF CSV files.
- Detect delimiter, encoding, headers, schema, and year coverage.
- Load safely, including large files.
- Normalize column names without destroying original meaning.
- Preserve raw files unchanged.
- Write Parquet with explicit and stable dtypes.

## Rules
- Never silently discard rows or columns.
- Record source URL, dataset/year, extraction date, row count, and schema.
- Handle malformed rows explicitly and report them.
- Avoid loading unnecessary copies of large datasets into memory.
- Validate the resulting Parquet before downstream use.

## Acceptance
- Row counts are reconciled.
- Schema is documented.
- Missingness is reported.
- Parquet can be read by DuckDB and Pandas.
