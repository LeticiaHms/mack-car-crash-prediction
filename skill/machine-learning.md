---
name: machine-learning
description: Train reproducible baseline and candidate Scikit-learn models for accident severity prediction.
---

# Machine Learning

## Workflow
1. Define target.
2. Define feature set.
3. Split data appropriately.
4. Build preprocessing pipeline.
5. Train baseline.
6. Train candidate models.
7. Save reproducible artifacts.
8. Send predictions to evaluation.

## Candidate models
Start with interpretable baselines such as Logistic Regression and Decision Tree, then compare Random Forest and Gradient Boosting when appropriate.

## Rules
- Use Pipeline and ColumnTransformer where applicable.
- Fix random seeds.
- Prevent leakage during preprocessing and feature selection.
- Handle class imbalance explicitly and document the choice.
- Do not optimize against the test set.

## Acceptance
Each trained model has configuration, training data definition, metrics, and artifact/version information.
