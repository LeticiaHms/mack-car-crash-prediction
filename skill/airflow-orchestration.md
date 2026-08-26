---
name: airflow-orchestration
description: Orchestrate the Mackenzie PRF car crash data and ML pipeline with Apache Airflow, including ingestion, quality checks, EDA, feature engineering, training, evaluation, retries, dependencies, logging, and reproducible execution.
---

# Airflow Orchestration

## Objective

Use Apache Airflow to orchestrate the end-to-end data and machine-learning workflow:

CSV/PRF → ingestion → Parquet → data quality → DuckDB → EDA → feature engineering → ML → evaluation → model artifact.

Airflow is responsible for **execution orchestration**, not for implementing business logic, statistical analysis, or model training itself.

## Pipeline

The main DAG should represent the project lifecycle:

```text
download_or_validate_source
          ↓
      ingest_data
          ↓
   validate_schema
          ↓
   data_quality
          ↓
   parquet_validation
          ↓
   duckdb_validation
          ↓
 exploratory_analysis
          ↓
 feature_engineering
          ↓
    train_models
          ↓
   evaluate_models
          ↓
 select_best_model
          ↓
    save_artifacts
```

## DAG design

Create a clear DAG with:
- descriptive task IDs
- explicit dependencies
- retry configuration
- execution logging
- deterministic parameters
- failure visibility
- sensible timeouts

Prefer TaskFlow API when it improves readability and type-safe task boundaries.

Keep the DAG thin. Complex processing belongs in reusable Python modules, not inside the DAG definition.

## Task responsibilities

### Ingestion
- Validate the expected PRF source.
- Process CSV input.
- Produce Parquet.
- Record row count and schema metadata.

### Data quality
- Validate schema.
- Check nulls, duplicates, invalid values, and expected categories.
- Fail the DAG for critical violations.
- Allow documented warnings for non-critical findings.

### DuckDB
- Validate that Parquet is queryable.
- Run basic row-count and aggregation checks.
- Avoid unnecessary data duplication.

### EDA
- Execute reproducible EDA code.
- Generate analytical datasets and visualizations.
- Persist findings/artifacts for downstream inspection.
- Do not make Airflow responsible for interpreting findings.

### Feature engineering
- Execute the same feature pipeline used during training and inference.
- Prevent target leakage.
- Persist the feature schema.

### ML
- Train candidate models.
- Store model metadata.
- Use deterministic seeds where applicable.
- Never use the test set for iterative tuning.

### Evaluation
- Calculate Precision, Recall, F1, ROC-AUC and appropriate additional metrics.
- Produce a model comparison artifact.
- Select the model according to a documented criterion.

### Artifacts
Persist versioned:
- Parquet outputs
- analytical datasets
- EDA artifacts
- feature metadata
- trained model
- preprocessing pipeline
- evaluation metrics
- model metadata

## Scheduling

For an academic project, do not force unnecessary frequent execution.

Use:
- manual execution during development;
- scheduled execution only when a recurring data-refresh workflow is actually required.

The DAG must also support reruns/backfills without corrupting existing artifacts.

## Retries and failures

Use retries for transient failures such as:
- temporary filesystem/network errors;
- external source availability;
- infrastructure interruptions.

Do not blindly retry deterministic data-quality or code errors.

When a task fails:
1. preserve logs;
2. identify the failing stage;
3. avoid silently producing partial outputs;
4. make rerun behavior explicit.

## Idempotency

Tasks should be safe to rerun.

Avoid:
- blindly appending duplicate records;
- overwriting unrelated datasets;
- creating uncontrolled artifact versions.

Prefer deterministic paths/version identifiers and atomic writes where practical.

## Configuration

Keep configuration outside the DAG where possible.

Examples:
- source location
- data year
- output paths
- model configuration
- random seed
- evaluation threshold

Do not hard-code environment-specific paths.

## Observability

Airflow should make it easy to identify:
- which task failed;
- execution duration;
- retries;
- logs;
- dataset/version processed;
- model version produced.

Do not treat Airflow logs as the only project documentation.

## Testing

Test:
- DAG import
- task dependencies
- task configuration
- Python processing functions independently
- successful end-to-end execution on a small sample

A DAG must not contain hidden side effects at import time.

## Academic/reproducibility requirements

Record:
- DAG version
- execution date
- dataset/version
- code version when available
- model version
- relevant configuration

The orchestration layer must make the complete workflow reproducible.

## Acceptance criteria

The Airflow implementation is complete when:

- the DAG loads successfully;
- dependencies represent the intended pipeline;
- tasks are small and testable;
- processing logic is outside the DAG where appropriate;
- retries are used only for transient failures;
- tasks are rerunnable/idempotent;
- critical data-quality failures stop downstream execution;
- ML evaluation uses the intended protocol;
- artifacts are versioned or reproducibly identified;
- logs allow diagnosis of failures;
- the full pipeline can be executed from ingestion through model evaluation.
