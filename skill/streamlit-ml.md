---
name: streamlit-ml-eda
description: Build a Streamlit application focused on exploratory data analysis and machine-learning investigation of PRF accident severity, including distributions, patterns, trends, seasonality, anomalies, associations, model behavior, and feature importance.
---

# Streamlit ML Exploratory Analysis

## Objective

Build an interactive analytical application for investigating the PRF accident dataset and the machine-learning problem.

This application is **not a reporting/document-generation tool**.

Its purpose is to let the user explore the data, discover patterns, validate hypotheses, inspect model behavior, and understand the relationship between features and accident severity.

## Core sections

### 1. Dataset Overview

Show:
- number of records;
- number of variables;
- period covered;
- available years;
- target variable;
- class distribution;
- missing-value summary;
- selected data-quality indicators.

Allow filtering by relevant dimensions.

### 2. Univariate Analysis

Allow the user to select a variable and inspect:
- frequency distribution;
- numerical distribution;
- categorical distribution;
- missing values;
- cardinality;
- summary statistics;
- rare categories.

For numerical variables show, where appropriate:
- mean;
- median;
- standard deviation;
- quartiles;
- IQR;
- min/max;
- skewness.

### 3. Severity Analysis

Focus the exploration on the target/severity variable.

Allow comparisons such as:

```text
Severity × State
Severity × Accident Type
Severity × Weather
Severity × Road Condition
Severity × Lighting
Severity × Hour
Severity × Day of Week
Severity × Month
```

Display counts and conditional percentages where useful.

### 4. Temporal Analysis

Provide interactive views for:
- accidents by year;
- accidents by month;
- accidents by day of week;
- accidents by hour;
- period of day;
- severity over time.

Allow filtering by severity, state, accident type, and other relevant dimensions.

Use line charts for ordered temporal trends.

### 5. Seasonality Exploration

Provide views such as:
- month × year;
- month × severity;
- weekday × hour;
- month × weekday;
- hour × severity.

The UI must not automatically label a pattern as "seasonality" without sufficient evidence.

Instead, present repeated patterns and allow the analyst to interpret them.

### 6. Pattern and Association Analysis

Allow the user to select:
- target variable;
- categorical feature;
- numerical feature.

For categorical variables show:
- contingency tables;
- conditional percentages;
- group comparisons;
- Cramér's V when appropriate.

For numerical relationships show:
- correlation;
- scatter plots where meaningful;
- grouped distributions.

Use Pearson or Spearman only when appropriate to the variable types and assumptions.

### 7. Statistical Analysis

Provide an analytical area for appropriate statistical tests.

Possible tests:
- chi-square;
- Fisher's exact test when appropriate;
- Mann–Whitney;
- Kruskal–Wallis;
- t-test/ANOVA only when assumptions are justified;
- Pearson/Spearman correlation.

Show:
- test name;
- statistic;
- p-value;
- effect size where applicable;
- interpretation.

Do not equate statistical significance with practical importance.

### 8. Anomaly Exploration

Provide interactive anomaly investigation using methods appropriate to the variable.

Possible methods:
- IQR;
- z-score;
- percentile thresholds;
- rolling statistics for time series;
- robust statistics.

Show:
- affected observations or groups;
- magnitude;
- time/location;
- potential interpretation.

Do not automatically delete anomalies.

Distinguish:
- plausible real-world event;
- possible data-quality issue;
- insufficient evidence.

### 9. Feature Analysis for ML

Allow the user to inspect candidate features before modeling.

Show:
- feature type;
- missingness;
- cardinality;
- distribution;
- relationship with target;
- potential leakage warning;
- transformation applied.

For every candidate feature expose enough information to answer:

"Would this information be available at prediction time?"

### 10. Model Exploration

The application may load already-trained models and artifacts.

Do not retrain models merely because a user changes a dashboard filter.

Show:
- model name/version;
- Precision;
- Recall;
- F1-score;
- ROC-AUC;
- confusion matrix;
- PR curve when appropriate;
- ROC curve when appropriate.

Allow model comparison using a consistent evaluation dataset.

### 11. Model Explainability

When supported by the selected model, show:
- feature importance;
- permutation importance;
- coefficients for linear models;
- other appropriate explainability techniques.

Clearly distinguish:
- predictive importance;
- statistical association;
- causal effect.

Feature importance must never be described as proof that a variable causes accident severity.

### 12. Interactive Filtering

Filters should be reusable across analytical sections where possible.

Potential filters:
- year;
- month;
- state;
- road;
- severity;
- accident type;
- weather;
- lighting;
- road condition;
- period of day.

Show active filters clearly.

## Architecture

Keep the Streamlit UI separate from analytical logic:

```text
streamlit/
├── app.py
├── pages/
├── components/
└── services/

src/
├── data/
├── eda/
├── statistics/
├── features/
└── models/
```

The Streamlit layer should call reusable functions from `src`.

Do not place large data-processing operations directly inside UI callbacks.

## Performance

For large datasets:
- use DuckDB for aggregations;
- query only required columns;
- cache stable datasets/queries;
- avoid repeatedly loading the complete dataset into Pandas;
- precompute expensive analytical tables when justified.

## Visualization standards

Use visualizations to answer analytical questions.

Recommended:
- bar charts for category comparisons;
- line charts for trends;
- histograms for distributions;
- boxplots for group distributions;
- heatmaps for temporal/category matrices;
- scatter plots for numeric relationships.

Avoid:
- decorative charts;
- excessive dashboards on one screen;
- misleading axes;
- unnecessary 3D visualizations;
- charts without analytical context.

## ML-specific safety

Never:
- use the test set interactively for model tuning;
- leak target information into features;
- imply causality from feature importance;
- report invented model metrics;
- silently change the preprocessing pipeline used during training.

## Outputs

The Streamlit application may export analytical tables or figures for later use in the project's documentation, but it must not generate the final academic report itself.

Its role is:

```text
Explore → Investigate → Compare → Validate hypotheses → Understand model
```

not:

```text
Explore → Automatically write report
```

## Acceptance criteria

The application is complete when:
- users can inspect dataset structure;
- users can investigate distributions;
- severity can be compared against important variables;
- temporal trends can be explored;
- seasonality can be investigated;
- anomalies can be inspected;
- statistical relationships can be analyzed;
- candidate ML features can be investigated;
- trained model performance can be explored;
- feature importance can be inspected when supported;
- DuckDB/Pandas are used appropriately for performance;
- the application does not retrain models unexpectedly;
- analytical and UI logic are separated;
- no unsupported causal claims are presented.
