# 🏨 ReservaCerta

> **Machine Learning para previsão de check-in e identificação de reservas com risco de cancelamento/no-show.**

## 👥 Equipe

* **Thomas Raphael de Oliveira** — [@thomasraphael96](https://github.com/thomasraphael96)
* **Letícia Homem de Melo Sanchez** — [@LeticiaHms](https://github.com/LeticiaHms)
* **Karina Gomes Dias** — [@kgdias](https://github.com/kgdias)

---

## 🎯 Objetivo

Desenvolver um modelo de **Machine Learning** capaz de prever a probabilidade de um cliente realizar o **check-in** ou cancelar a reserva/**no-show**.

A solução busca auxiliar hotéis na identificação antecipada de reservas de maior risco, contribuindo para um melhor planejamento da ocupação e redução de perdas de receita.

---

## 🏗️ Arquitetura

```text
              API
               │
               ▼
            Python
               │
               ▼
          Parquet (Raw)
               │
               ▼
            DuckDB
               │
               ▼
        Pandas / Streamlit
          │           │
          │           └──► EDA & Visualizações
          ▼
   Limpeza + Feature Engineering
               │
               ▼
       Machine Learning
               │
               ▼
       Modelo de Predição
```

---

## 🔄 Etapas

**1. Ingestão**
Dados coletados via API utilizando Python e armazenados em Parquet.

**2. Tratamento & EDA**
Pandas para limpeza, análise exploratória e Feature Engineering.

**3. Machine Learning**
Classificação binária para prever **check-in vs. cancelamento/no-show**.

**4. Avaliação**
Comparação dos modelos utilizando **Precision, Recall, F1-Score e ROC-AUC**.

**5. Visualização**
Streamlit para apresentação dos indicadores, análises e previsões.

---

## 🛠️ Tecnologias

`Python` · `Pandas` · `DuckDB` · `Parquet` · `Scikit-learn` · `Streamlit` · `Machine Learning`

---

## 🎓 Projeto Acadêmico

Projeto desenvolvido no **Mackenzie**, aplicando conceitos de **Engenharia de Dados, Análise Exploratória e Machine Learning** a um problema do setor de hospedagem.