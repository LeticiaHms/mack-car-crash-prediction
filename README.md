# 🚗 PreviVia

## 👥 Equipe

* **Thomas Raphael de Oliveira** — [@thomasraphael96](https://github.com/thomasraphael96)
* **Letícia Homem de Melo Sanchez** — [@LeticiaHms](https://github.com/LeticiaHms)
* **Karina Gomes Dias** — [@kgdias](https://github.com/kgdias)

---

## 🎯 Objetivo

Machine Learning para identificar antecipadamente quais condições e locais estão associados a acidentes de maior gravidade, auxiliando na priorização de ações de segurança viária.

---

## 🏗️ Arquitetura

```text
              CSV
               │
               ▼
            Python
               │
               ▼
            Parquet
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
           Avaliação
```

---

## 🔄 Etapas

**1. Ingestão:** 
Dados coletados via CSV utilizando Python e armazenando em Parquet.

**2. Tratamento & EDA:** 
Pandas para limpeza, análise exploratória e Feature Engineering.

**3. Machine Learning:** 
Descobrir quais fatores estão associados à gravidade

**4. Avaliação:** 
Comparação dos modelos utilizando **Precision, Recall, F1-Score e ROC-AUC**.

**5. Visualização:** 
Streamlit para apresentação dos indicadores, análises e previsões.

---

## 🛠️ Tecnologias

`Python` · `Pandas` · `DuckDB` · `Parquet` · `Scikit-learn` · `Streamlit` · `Machine Learning`

---

## 🎓 Projeto Acadêmico

Projeto desenvolvido no **Mackenzie**, aplicando conceitos de **Engenharia de Dados, Análise Exploratória e Machine Learning** a um problema do setor de viário.
