---
name: model-evaluation
description: Evaluate accident severity models with metrics appropriate for classification and class imbalance.
---

# Model Evaluation

## Required metrics
- Precision
- Recall
- F1-score
- ROC-AUC

## Recommended additional analysis
- confusion matrix
- PR-AUC when the positive class is uncommon
- per-class metrics
- threshold analysis

## Rules
- Define which class represents severe accidents.
- Explain why the chosen metric matters operationally.
- Do not rely on accuracy alone.
- Evaluate on untouched test data.
- Compare models using the same evaluation protocol.

## Interpretation
Discuss false negatives for severe accidents explicitly. Never claim that model performance proves causal relationships.

## Acceptance
A model comparison table and a clear model-selection rationale are produced.
