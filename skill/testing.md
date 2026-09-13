---
name: testing
description: Test the car crash prediction pipeline for correctness, leakage, reproducibility, and integration.
---

# Testing

## Unit tests
Test:
- ingestion transformations
- schema validation
- feature transformations
- target encoding
- model prediction shape
- metric calculations

## Integration tests
Validate:
CSV → Parquet → DuckDB → features → model → prediction.

## Data tests
- required columns exist
- expected types hold
- target values are valid
- no duplicate identifiers where uniqueness is expected

## ML tests
- train/test separation
- no target column in features
- preprocessing fit only on training data
- reproducible predictions with fixed seed

## Acceptance
Tests fail loudly when schema, feature contracts, or leakage protections are violated.
