# 🚗 PreviVia

## 👥 Equipe

* **Thomas Raphael de Oliveira** — [@thomasraphael96](https://github.com/thomasraphael96)
* **Letícia Homem de Melo Sanchez** — [@LeticiaHms](https://github.com/LeticiaHms)
* **Karina Gomes Dias** — [@kgdias](https://github.com/kgdias)

---

## 🎯 Objetivo

Machine Learning para identificar antecipadamente quais condições e locais estão associados a acidentes de maior gravidade, auxiliando na priorização de ações de segurança viária.

**Origem:** https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf

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

## 🔄 Ciclo de vida do projeto de dados

| Fase do ciclo | Entrega | Situação | O que foi feito |
|---|---|---|---|
| **Entender o problema** | Etapa 0 | ✅ | Definição do problema, objetivo, unidade de análise, variável-alvo e critérios de sucesso — [`docs/spec.md`](docs/spec.md) |
| **Coleta de dados** | Etapa 1 | ✅ | CSVs anuais da PRF (2022–2026) + calendário de feriados, com dicionário de dados e critérios de seleção — [`etapa1-coleta.md`](docs/docs-etapas/etapa1-coleta.md) |
| **Pré-processamento** | Etapa 1 | ✅ | Limpeza, tipagem, deduplicação e validação → camada curada em Parquet — [`etapa1-pre-processamento.md`](docs/docs-etapas/etapa1-pre-processamento.md) |
| **Análise Exploratória** | Etapa 2 | ✅ | Distribuições, padrões, sazonalidade, anomalias, correlações e mapa de *data leakage*, com dashboard interativo — [`etapa2-eda.md`](docs/docs-etapas/etapa2-eda.md) |
| **Construção de Modelos** | Etapa 3 | 🔜 | Engenharia de atributos, treino e avaliação por **Precision, Recall, F1-Score e PR-AUC** da classe grave |

Coleta e pré-processamento compõem juntos a Etapa 1 da disciplina — daí o prefixo `etapa1-` nos dois documentos.

**Visualização** atravessa todas as fases: o dashboard Streamlit expõe a qualidade dos dados, a análise exploratória e — quando a Etapa 3 estiver concluída — a avaliação dos modelos.

---

## ⚙️ Como executar

### Pré-requisitos

Python 3.10+ e as dependências do projeto:

```bash
pip install -r requirements.txt
```

### 1. Gerar a camada curada

O dashboard **não lê os CSVs brutos** — ele lê os Parquets curados. Se a pasta `dados/curated/` estiver vazia, rode o pipeline de pré-processamento primeiro:

```bash
python src/pipeline.py        # ou: python -m src.pipeline
```

Gera `dados/curated/acidentes_2022_2026.parquet` e `dados/curated/feriados_nacionais.parquet`, com a validação de schema registrada em `reports/data_quality/` e os logs em `docs/evidencias/`.

### 2. (Opcional) Regerar os artefatos da EDA

```bash
python src/run_eda.py
```

Regenera `reports/eda/eda_results.json` e as 26 tabelas de `reports/eda/tables/`. Todo número citado na documentação vem daqui. O dashboard **não** depende deste passo — ele calcula tudo ao vivo a partir do Parquet.

### 3. Subir o dashboard

```bash
streamlit run streamlit/app.py
```

O app abre em **http://localhost:8501**. Para encerrar, `Ctrl+C` no terminal.

Opções úteis:

```bash
# outra porta (útil se a 8501 já estiver ocupada)
streamlit run streamlit/app.py --server.port 8502

# sem tentar abrir o navegador (servidor remoto, container, CI)
streamlit run streamlit/app.py --server.headless true
```

> No **GitHub Codespaces** a porta é encaminhada automaticamente: abra a aba *Ports* e clique no endereço da 8501.

Pode ser executado de qualquer diretório — `streamlit/common.py` resolve os caminhos a partir da raiz do projeto.

### ⚠️ Ao editar o código com o app no ar

O Streamlit recarrega o **script da página** a cada alteração, mas **não reimporta** módulos já carregados. Ou seja: mudanças em `streamlit/common.py` ou em `src/eda_utils.py` só passam a valer depois de **reiniciar o servidor** (`Ctrl+C` e subir de novo). Um "Rerun" ou "Clear cache" pelo menu não resolve — o sintoma típico é um `ImportError` reclamando de uma função que existe no arquivo.

Se você regerou os Parquets com o app aberto, aí sim use **⋮ → Clear cache** para descartar os resultados em memória.

### ✅ Verificar se todas as páginas funcionam

```bash
python scripts/smoke_streamlit.py             # executa as 14 páginas headless (~17s)
python scripts/smoke_streamlit.py --widgets   # + cada estado alternativo de radio/checkbox
```

Uma página quebrada não derruba as outras no navegador — o erro só aparece para quem abrir aquela aba. Este script executa todas de uma vez e falha se alguma lançar exceção. Vale rodar depois de mexer em `src/eda_utils.py` ou `streamlit/common.py`, que são compartilhados por todas as páginas.

---

## 📊 O dashboard

14 páginas, navegáveis pelo menu lateral. Os **filtros globais da sidebar** (ano, UF, gravidade, tipo de acidente, rodovia, período do dia, clima, tipo de pista) valem para todas elas.

| Grupo | Páginas |
|---|---|
| **Entender a base** | 🔎 Visão Geral · 🧹 Qualidade dos Dados · 📊 Distribuições · 🎯 Gravidade |
| **Encontrar padrões** | 📈 Tendências · 🔄 Sazonalidade · 🔗 Correlações · 🚨 Anomalias · ✂️ Segmentação · 🗺️ Geografia |
| **Concluir com responsabilidade** | 🧪 Validação Estatística · 💡 Insights e Hipóteses · 🧠 Features para ML · 🤖 Modelos |

Um filtro merece destaque: **"Excluir janela não consolidada"**. Os últimos dias da série ainda estão sendo preenchidos na fonte da PRF, o que produz uma queda falsa no fim de qualquer gráfico temporal. O filtro corta esse trecho. Vem desmarcado por padrão para reproduzir os números publicados na documentação — o diagnóstico completo está na página 🧹 Qualidade dos Dados.

---

## 📁 Estrutura

```text
dados/
  datatran20*.csv            # bruto (PRF) — nunca alterado
  feriados_nacionais.xls     # bruto (ANBIMA)
  curated/*.parquet          # camada curada, gerada pelo pipeline
src/
  pipeline.py                # orquestra o pré-processamento
  preprocessing/             # limpeza, tipagem e validação por base
  eda_utils.py               # camada analítica (DuckDB + estatística)
  run_eda.py                 # gera os artefatos reproduzíveis da EDA
streamlit/
  app.py                     # página inicial do dashboard
  common.py                  # conexão, cache e filtros globais
  pages/                     # as demais 13 páginas
reports/
  data_quality/              # relatórios de validação do pipeline
  eda/                       # eda_results.json + 26 tabelas CSV
docs/                        # documentação (ver abaixo)
scripts/                     # utilitários de verificação
```

---

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/GLOSSARIO.md`](docs/GLOSSARIO.md) | Explica os termos técnicos (z-score, qui-quadrado, Cramér's V, intervalo de confiança, data leakage…) com exemplos desta base |
| [`docs/docs-etapas/`](docs/docs-etapas/) | Relatório de cada etapa: coleta, pré-processamento e EDA |
| [`docs/specs/eda/EDA.md`](docs/specs/eda/EDA.md) | Documento narrativo da análise exploratória |
| [`docs/ANALYSIS_LOG.md`](docs/ANALYSIS_LOG.md) | Cada achado com pergunta, método, resultado e limitação |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Decisões técnicas, com as alternativas descartadas e o porquê |
| [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md) | Relatório de qualidade dos dados |

Quem estiver chegando agora no projeto: comece pelo [`GLOSSARIO.md`](docs/GLOSSARIO.md) se algum termo não for familiar, depois [`docs/docs-etapas/etapa2-eda.md`](docs/docs-etapas/etapa2-eda.md) para o panorama da análise.

---

## 🛠️ Tecnologias

`Python` · `Pandas` · `DuckDB` · `Parquet` · `Scikit-learn` · `Streamlit` · `Plotly` · `SciPy` · `Machine Learning`

---

## 🎓 Projeto Acadêmico

Projeto desenvolvido no **Mackenzie**, aplicando conceitos de **Engenharia de Dados, Análise Exploratória e Machine Learning** a um problema do setor de viário.
