---
name: duckdb-analytics
description: Use DuckDB efficiently for analytical SQL over Parquet in the car crash project.
---

# DuckDB Analytics

## Principles
- Query Parquet directly when practical.
- Push filtering, aggregation, and projection into SQL.
- Avoid unnecessary full-data Pandas materialization.
- Keep analytical queries reproducible and documented.

## Query standards
- Explicitly select columns.
- Use meaningful aliases.
- Avoid SELECT * in production queries.
- Validate aggregation grain.
- Check counts before and after joins.

## Acceptance
Queries return reproducible results and do not accidentally duplicate accident records.
