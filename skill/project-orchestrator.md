---
name: project-orchestrator
description: Orchestrate the Mackenzie car crash severity prediction project from ingestion through deployment, enforcing stage order, data contracts, reproducibility, and academic integrity.
---

# Project Orchestrator

## Objective
Coordinate the complete pipeline:
CSV → Parquet → DuckDB → EDA → Feature Engineering → ML → Evaluation → Streamlit.

## Rules
- Inspect the repository before changing anything.
- Preserve the existing architecture unless a change is justified.
- Never skip data-quality checks before modeling.
- Never introduce target leakage.
- Keep transformations reproducible and versioned.
- Prefer small, testable changes.
- Run relevant tests after changes.
- Do not claim causality from observational data; use "association", "relationship", or "predictive signal".
- Keep raw data immutable.

## Stage contract
1. Ingestion produces validated Parquet.
2. Data quality documents schema, missingness, duplicates, invalid values.
3. DuckDB provides analytical access to Parquet.
4. EDA produces evidence-backed findings.
5. Feature engineering produces model-ready features without leakage.
6. ML trains reproducible baselines and candidate models.
7. Evaluation compares models using appropriate metrics.
8. Streamlit consumes saved artifacts rather than retraining unexpectedly.
9. Documentation reflects the implemented pipeline.

## Acceptance
A task is complete only when code, tests, artifacts, and documentation remain consistent.
