# GEMINI.md — Project Context & Workspace Instructions

> **IMPORTANT WARNING FOR FUTURE AI AGENTS:**
> Although the workspace/repository is named `mack-booking-prediction` and has a `README.md` describing a hotel cancellation prediction project ("ReservaCerta"), the **actual, active project** specified in `docs/spec.md` and supported by the datasets in `dados/` is:
> **"Predição de Risco de Acidentes em Rodovias Federais"** (Brazilian Federal Highway Accident Risk Prediction).
> Do **NOT** implement hotel booking reservation models unless explicitly directed by the user. Align all engineering efforts with the highway accident prediction project.

---

## 1. Project Overview

### Purpose
Develop a complete data engineering and machine learning pipeline to identify and classify **trechos de rodovias federais brasileiras com maior risco de ocorrência de acidentes graves** (Brazilian federal highway segments with the highest risk of severe accidents). 

Severe accidents are defined initially as events with at least one death or severe injury, based on public records from the **Polícia Rodoviária Federal (PRF)**.

### Target Unit of Analysis
The unit of analysis is a **highway segment over a specific time window** (e.g., BR-116 SP, km 80–90, during a given month/year), rather than individual accident records.

### Conceptual Pipeline Architecture
```text
  [ PRF Raw CSVs (2022-2026) ]
               │
               ▼
         1. INGESTÃO
               │
               ▼
      2. DATA LAKE (Raw)
               │
               ▼
      3. PROCESSAMENTO (Curated)
               │
               ▼
     4. EXPLORATORY ANALYSIS (EDA)
               │
               ▼
     5. FEATURE ENGINEERING (Feature)
               │
               ▼
         6. MODELAGEM ML
               │
               ▼
   7. RISCO FINAL / VISUALIZAÇÃO (Streamlit / Maps)
```

---

## 2. Directory Structure & Key Files

```text
/workspaces/mack-booking-prediction/
├── LICENSE
├── README.md               # Outdated: Describes "ReservaCerta" (Hotel Reservation ML)
├── GEMINI.md               # Active Workspace Instructions (This file)
├── dados/                  # Raw PRF accident CSV files for years 2022-2026
│   ├── datatran2022.csv
│   ├── datatran2023.csv
│   ├── datatran2024.csv
│   ├── datatran2025.csv
│   └── datatran2026.csv
├── docs/
│   └── spec.md             # Core specification of the Accident Risk Prediction Project
└── skill/
    └── sdd_skill.md        # Spec-Driven Development (SDD) Workflow Guidelines
```

---

## 3. Data Specification

### Source Datasets
The `dados/` directory contains official public records from the PRF (Agrupados por ocorrência):
- **Years**: 2022 to 2026 inclusive.
- **Delimiter**: Semicolon (`;`).
- **Encoding**: Uses `ISO-8859-1` / `latin1` (indicated by corrupted characters like `"sbado"`). Ensure proper encoding parameters are set when reading using Python/Pandas/PySpark (e.g., `encoding='latin1'`).

### Core Schema Columns
* **Identifiers & Timing**: `id`, `data_inversa` (YYYY-MM-DD), `dia_semana`, `horario` (HH:MM:SS)
* **Location**: `uf`, `br` (highway number), `km` (kilometer position), `municipio`, `latitude`, `longitude`
* **Metadata/Context**: `causa_acidente`, `tipo_acidente`, `classificacao_acidente`, `fase_dia`, `sentido_via`, `condicao_metereologica`, `tipo_pista`, `tracado_via`, `uso_solo`, `regional`, `delegacia`, `uop`
* **Counts & Victims**: `pessoas`, `mortos`, `feridos_leves`, `feridos_graves`, `ilesos`, `ignorados`, `feridos`, `veiculos`

---

## 4. Engineering & ML Specifications

### Data Lake Layers
1. **Raw**: Original unprocessed PRF CSV files.
2. **Curated**: Standardized, typed, deduplicated, and unified across all five years.
3. **Feature**: Structured by highway segment & period (e.g., segment of 5km or 10km, per month), containing geographical features, temporal features, historical accident rates, and the target variable.

### Data Leakage Prevention
Do **not** use immediate accident consequences (such as individual `mortos`, `feridos_graves`, or `classificacao_acidente` from the target prediction period) as features. Features must represent historical aggregates or static contextual attributes known *prior* to the prediction window.

### Machine Learning
- **Task**: Supervised classification (low, medium, high risk of severe accidents) or binary classification (presence/absence of severe accidents in segment/period).
- **Models**: Baseline (Dummy Classifier), main models (Logistic Regression, Random Forest, XGBoost/LightGBM).
- **Core Metric**: Precision, Recall (of high risk), F1-Score, and ROC-AUC. Accuracy should not be the sole evaluation metric due to high class imbalance.

---

## 5. Development Conventions & Workflow

This project adheres to **Spec-Driven Development (SDD)** as detailed in `skill/sdd_skill.md`.

### SDD Phase Gates
Before implementing any major feature, you must proceed through these phases sequentially, securing explicit user approval at each gate:
1. **Explore & Research**: Inspect data and patterns.
2. **Requirements**: Outline what must be achieved. **(Gate 1 Approval)**
3. **Design**: Detail the technical approach (schemas, structures). **(Gate 2 Approval)**
4. **Tasks**: Break down development steps. **(Gate 3 Approval)**
5. **Implement**: Code the solution.
6. **Verify**: Perform comprehensive testing (unit, data checks).

---

## 6. Building, Running, and Testing (TODO Checklist)

As of now, this is a planning/data phase with no active Python scripts. Future agents must implement code and update these instructions.

- [ ] **Setup Environment**: Create a virtual environment (`venv` or `conda`), and a `requirements.txt` containing `pandas`, `duckdb`, `scikit-learn`, `streamlit`, and any optional library like `pyspark`.
- [ ] **Data Pipeline (Ingestion & Curated)**: Implement `src/ingest.py` or `src/preprocess.py`.
- [ ] **Feature Engineering**: Implement `src/features.py`.
- [ ] **Training**: Implement `src/train.py`.
- [ ] **Dashboard**: Implement a Streamlit dashboard in `src/app.py`.

### Execution Drafts (Future Use)
```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run preprocessing pipeline
python src/preprocess.py

# Run model training
python src/train.py

# Launch Streamlit visualization app
streamlit run src/app.py
```
