---
name: data-quality
description: Validate PRF accident data before analysis and machine learning.
---

# Data Quality

## Checks
- schema and dtypes
- null/missing values
- duplicate rows and identifiers
- categorical cardinality
- unexpected categories
- invalid dates/times
- invalid coordinates
- impossible numeric values
- inconsistent relationships between columns

## Output
Produce a concise quality report with:
- check
- result
- severity
- affected rows/percentage
- treatment or decision

## Rules
- Never hide missingness.
- Do not automatically impute without documenting the rationale.
- Distinguish true zero, missing, unknown, and not applicable.
- Preserve evidence needed for the academic report.

## Acceptance
No downstream modeling begins while critical quality issues remain unexplained.
