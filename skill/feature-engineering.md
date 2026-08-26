---
name: feature-engineering
description: Build reproducible, leakage-safe features for accident severity prediction.
---

# Feature Engineering

## Candidate transformations
- datetime → year, month, weekday, hour, time period
- categorical normalization
- numerical transformations where justified
- grouped/aggregated contextual features only when available at prediction time
- encoding through Scikit-learn pipelines

## Critical rule: leakage prevention
For every feature ask:
"Would this information be available at or before the prediction moment?"

If no, exclude it.

Do not use post-accident outcomes, derived severity information, response/medical outcomes, or variables that encode the target.

## Reproducibility
- Keep feature definitions in code.
- Fit preprocessing only on training data.
- Keep train/validation/test transformations consistent.
- Record the final feature list.

## Acceptance
A feature dictionary identifies name, type, source, transformation, and leakage rationale.
