---
name: eda
description: Perform a rigorous exploratory data analysis of PRF accident data to identify structure, distributions, patterns, trends, seasonality, associations, anomalies, and statistically relevant findings, while recording evidence for the final academic report.
---

# Exploratory Data Analysis

## Objective
Treat EDA as an investigation, not a collection of charts.

The analysis must answer:
- What does the dataset contain?
- What is its coverage and structure?
- How are variables distributed?
- Which patterns and relationships appear?
- Are there temporal trends or seasonality?
- Are there anomalies or suspicious data-quality patterns?
- Which findings should influence feature engineering or modeling?

## 1. Dataset profiling
Document:
- number of rows and columns
- period covered
- years/months available
- variable types
- unique values/cardinality
- missingness
- duplicates
- categorical distributions
- numeric ranges
- rare categories
- suspicious values

Separate data-quality findings from analytical findings.

## 2. Descriptive statistics
For relevant numerical variables calculate, when applicable:
- count
- mean
- median
- mode
- minimum/maximum
- quartiles
- IQR
- variance
- standard deviation
- coefficient of variation
- skewness
- kurtosis

For categorical variables report:
- frequency
- percentage
- number of unique categories
- rare-category frequency

Do not calculate statistics mechanically when they have no analytical meaning.

## 3. Target analysis
Analyze the target/severity variable first.

Report:
- class frequencies
- class percentages
- class imbalance
- distribution by year
- distribution by relevant categorical variables

Explicitly assess whether imbalance affects model strategy and evaluation metrics.

## 4. Pattern and association analysis
Investigate relationships between severity and available explanatory variables, including when relevant:
- state
- road/highway
- accident type
- weather/environmental conditions
- road/pavement conditions
- lighting
- lane/road characteristics
- time period
- day of week
- month
- hour
- other available pre- or contemporaneous variables

Use appropriate summaries such as:
- cross-tabulations
- conditional percentages
- grouped statistics
- rate comparisons
- contingency tables

Do not infer causality from associations.

## 5. Statistical analysis
Choose statistical methods according to variable types and assumptions.

Possible methods include:
- Pearson correlation for suitable continuous/approximately linear relationships
- Spearman correlation for monotonic ordinal/rank relationships or non-normal variables
- chi-square tests for categorical associations when assumptions are met
- Cramér's V for strength of association between categorical variables
- t-test/ANOVA only when assumptions are appropriate
- non-parametric alternatives such as Mann–Whitney or Kruskal–Wallis when appropriate

For hypothesis tests document:
- null/alternative hypothesis
- test used
- assumptions checked
- statistic
- p-value
- effect size when applicable
- practical interpretation

Statistical significance must not be treated as practical significance.

## 6. Temporal analysis
Investigate:
- yearly trends
- monthly trends
- day-of-week patterns
- hourly patterns
- period-of-day patterns
- severity over time
- changes in category composition over time

Use time-series visualizations when the ordering of time matters.

Never replace a complete temporal series with only an aggregate when investigating trends.

## 7. Seasonality
Investigate repeated temporal patterns at appropriate granularities:
- month
- quarter, when meaningful
- day of week
- hour
- month × year
- weekday × hour

Do not label a pattern as seasonality solely because a chart oscillates. Look for recurrence across comparable periods and document the evidence.

## 8. Anomaly detection
Search for:
- extreme numeric observations
- unusually high/low accident counts
- sudden temporal spikes
- sudden drops
- unusual state/road behavior
- rare category concentrations
- abrupt distribution changes

Possible techniques:
- IQR
- z-score when appropriate
- robust statistics
- rolling statistics
- percentile thresholds
- visual inspection

Every anomaly must be classified as:
1. plausible real-world event,
2. possible data-quality issue,
3. insufficient evidence.

Never automatically delete an anomaly.

## 9. Visualization standards
Every visualization must answer a question.

Prefer:
- bar charts for categorical comparisons
- line charts for ordered time trends
- histograms/density views for distributions
- boxplots for numeric distributions across groups
- heatmaps for temporal/category matrices
- scatterplots for numeric relationships

Avoid decorative charts.

For every important chart record:
- analytical question
- variables
- aggregation/grain
- finding
- implication

## 10. Findings → decisions
Every material EDA finding should be evaluated for downstream impact.

Use this structure:

Finding:
Decision:
Reason:
Impact:
Evidence:

Example:

Finding: The severe-accident class is strongly underrepresented.
Decision: Do not use accuracy as the primary model-selection metric.
Reason: Accuracy may hide poor detection of severe cases.
Impact: Prioritize recall, F1, Precision and ROC-AUC, with PR-AUC when appropriate.
Evidence: Store the calculated class distribution.

## 11. Leakage protection
Do not use post-accident information to justify predictive features.

Before recommending a variable for ML ask:
"Would this information be available at or before the prediction moment?"

If not, flag it as unsuitable for prediction even if it has a strong statistical association with severity.

## 12. Reproducibility
EDA must be executable from code.

Save:
- analysis configuration
- dataset/version reference
- generated tables
- important statistical results
- chart source/code
- key findings

Do not manually type measured values into the final report.

## 13. Output artifacts
The EDA stage should contribute to:
- `docs/EDA.md`
- `docs/ANALYSIS_LOG.md`
- `docs/DECISIONS.md`
- generated statistical tables
- generated visualizations

## Acceptance criteria
EDA is complete only when:
- dataset structure is documented;
- descriptive statistics are available;
- target distribution is analyzed;
- relevant patterns/relationships are investigated;
- temporal trends are investigated;
- seasonality is explicitly assessed;
- anomalies are investigated;
- appropriate statistical tests are used where justified;
- findings are connected to modeling decisions;
- no unsupported causal claim is made;
- findings are reproducible;
- evidence is available for the final report.
