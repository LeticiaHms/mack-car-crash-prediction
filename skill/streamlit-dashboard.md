---
name: streamlit-dashboard
description: Build a clear Streamlit application for PRF accident analysis, model evaluation, and severity prediction.
---

# Streamlit Dashboard

## Suggested pages
- Overview
- Accident Analysis
- Geographic Analysis
- Severity Factors
- Model Performance
- Prediction

## Rules
- Keep UI separate from data/model logic.
- Do not retrain models on every page interaction.
- Load versioned artifacts.
- Display data coverage and limitations.
- Make filters explicit.
- Use accessible labels and useful empty/error states.
- Never expose raw sensitive information if it appears in source data.

## Prediction
Show:
- input features
- selected model
- predicted class
- probability/confidence where appropriate
- model limitations

## Acceptance
The app runs from a clean environment and uses the same feature pipeline as training.
