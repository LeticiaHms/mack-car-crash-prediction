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

O DuckDB é o banco analítico oficial do projeto: cada camada é um **schema**, e cada tabela tem seu próprio script de criação em `src/`.

```text
CSV / XLS (data/raw/)
        │
        ▼
┌─────────────────────────── data/prf.duckdb ───────────────────────────┐
│                                                                         │
│  raw.*        ← src/raw/*.py       ingestão bruta, sem regra de negócio│
│    │                                                                   │
│    ▼                                                                   │
│  bronze.*     ← src/bronze/*.py    limpeza, tipagem, validação         │
│    │                                                                   │
│    ▼                                                                   │
│  silver.*     ← src/silver/*.py    enriquecimento + corte de qualidade │
│    │                                                                   │
│    ▼                                                                   │
│  gold.*       ← src/gold/*.py      features + target, pronto para ML  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
   Streamlit (EDA/qualidade) · próxima etapa: Machine Learning
```

`src/database/connection.py` centraliza a conexão com o banco; `src/jobs/build_database.py` é o único orquestrador que reconstrói tudo, na ordem raw → bronze → silver → gold (ver seção 🏗️ Arquitetura de dados abaixo).

### 🗺️ Mapa rápido do repositório

| Pergunta | Resposta |
|---|---|
| Onde estão os dados de origem e o banco? | [`data/`](data/) (`data/raw/`, `data/prf.duckdb`) |
| Onde está a conexão com o DuckDB? | [`src/database/`](src/database/) |
| Onde está a Raw? | [`src/raw/`](src/raw/) → schema `raw` |
| Onde está a Bronze? | [`src/bronze/`](src/bronze/) → schema `bronze` |
| Onde está a Silver? | [`src/silver/`](src/silver/) → schema `silver` |
| Onde está a Gold? | [`src/gold/`](src/gold/) → schema `gold` |
| Onde está o pipeline/orquestrador? | [`src/jobs/build_database.py`](src/jobs/build_database.py) |
| Onde está a EDA? | [`src/eda/`](src/eda/) → resultados em `reports/eda/` |
| Onde está o dashboard? | [`app/`](app/) (`streamlit run app/app.py`) |
| Onde estão os testes? | [`tests/`](tests/) (`python -m pytest`) |
| Onde estão os resultados/relatórios? | [`reports/`](reports/) |
| Onde estão entregas, evidências, decisões e análises? | [`docs/`](docs/) (ver seção 📚 Documentação) |
| Onde estão versões antigas/experimentais? | Nenhuma no momento — ver nota em 📁 Estrutura |

---

## 🔄 Ciclo de vida do projeto de dados

| Fase do ciclo | Entrega | Situação | O que foi feito |
|---|---|---|---|
| **Entender o problema** | Etapa 0 | ✅ | Definição do problema, objetivo, unidade de análise, variável-alvo e critérios de sucesso — [`docs/specs/spec.md`](docs/specs/spec.md) |
| **Coleta de dados** | Etapa 1 | ✅ | CSVs anuais da PRF (2022–2026) + calendário de feriados, com dicionário de dados e critérios de seleção — [`etapa1-coleta.md`](docs/entregas/etapa1-coleta.md) |
| **Pré-processamento** | Etapa 1 | ✅ | Limpeza, tipagem, deduplicação e validação → camadas Bronze/Silver no DuckDB — [`etapa1-pre-processamento.md`](docs/entregas/etapa1-pre-processamento.md) |
| **Análise Exploratória** | Etapa 2 | ✅ | Distribuições, padrões, sazonalidade, anomalias, correlações e mapa de *data leakage*, com dashboard interativo — [`etapa2-eda.md`](docs/entregas/etapa2-eda.md) |
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

### 1. Construir o banco DuckDB

O dashboard **não lê os CSVs brutos** — ele lê as tabelas já materializadas em `data/prf.duckdb`. Se o arquivo não existir (ou estiver desatualizado), rode o orquestrador do pipeline:

```bash
python -m src.jobs.build_database    # ou: python src/jobs/build_database.py
```

Reconstrói `data/prf.duckdb` do zero — schemas `raw`, `bronze`, `silver`, `gold`, cada um com suas tabelas (ver seção 🏗️ Arquitetura de dados) — além dos relatórios de validação em `reports/data_quality/`, dos artefatos da Gold em `reports/gold/` e dos logs em `docs/evidencias/`. Leva ~40s a partir dos CSVs brutos.

Qualquer tabela também pode ser (re)construída isoladamente, por exemplo `python -m src.silver.acidentes` — ela garante sozinha que sua dependência (aqui, `bronze.acidentes`/`bronze.feriados`) existe antes de rodar.

### 2. (Opcional) Regerar os artefatos da EDA

```bash
python src/eda/run.py
```

Regenera `reports/eda/eda_results.json` e as 26 tabelas de `reports/eda/tables/`, lendo o schema `bronze` do banco. Todo número citado na documentação vem daqui. O dashboard **não** depende deste passo — ele calcula tudo ao vivo a partir do DuckDB.

### 3. Subir o dashboard

```bash
streamlit run app/app.py
```

O app abre em **http://localhost:8501**. Para encerrar, `Ctrl+C` no terminal.

Opções úteis:

```bash
# outra porta (útil se a 8501 já estiver ocupada)
streamlit run app/app.py --server.port 8502

# sem tentar abrir o navegador (servidor remoto, container, CI)
streamlit run app/app.py --server.headless true
```

> No **GitHub Codespaces** a porta é encaminhada automaticamente: abra a aba *Ports* e clique no endereço da 8501.

Pode ser executado de qualquer diretório — `app/common.py` resolve os caminhos a partir da raiz do projeto.

### ⚠️ Ao editar o código com o app no ar

O Streamlit recarrega o **script da página** a cada alteração, mas **não reimporta** módulos já carregados. Ou seja: mudanças em `app/common.py` ou em `src/eda/utils.py` só passam a valer depois de **reiniciar o servidor** (`Ctrl+C` e subir de novo). Um "Rerun" ou "Clear cache" pelo menu não resolve — o sintoma típico é um `ImportError` reclamando de uma função que existe no arquivo.

Se você reconstruiu o banco com o app aberto, aí sim use **⋮ → Clear cache** para descartar os resultados em memória.

### ✅ Verificar se todas as páginas funcionam

```bash
python scripts/smoke_streamlit.py             # executa as 14 páginas headless (~17s)
python scripts/smoke_streamlit.py --widgets   # + cada estado alternativo de radio/checkbox
```

Uma página quebrada não derruba as outras no navegador — o erro só aparece para quem abrir aquela aba. Este script executa todas de uma vez e falha se alguma lançar exceção. Vale rodar depois de mexer em `src/eda/utils.py` ou `app/common.py`, que são compartilhados por todas as páginas.

---

## 📊 O dashboard

13 páginas, agrupadas no menu lateral (`st.navigation`, em `app/app.py`) num fluxo de Data Science — do geral ao específico:

| Grupo | Páginas |
|---|---|
| **Visão Geral** | 🚧 Visão Geral (Home) · 💡 Insights e Hipóteses (síntese final) |
| **Qualidade e Estrutura** | 🧹 Qualidade dos Dados · 🚨 Anomalias · ✂️ Segmentação |
| **Análise Exploratória** | 📊 Distribuições · 🎯 Gravidade · 📈 Tendências · 🔄 Sazonalidade · 🔗 Correlações · 🗺️ Geografia |
| **Preparação para ML** | 🧪 Validação Estatística · 🧠 Features ML |

Os **filtros globais da sidebar** (ano, UF, gravidade, tipo de acidente, rodovia, período do dia, clima, tipo de pista) valem para a maioria das páginas — as que avaliam qualidade sobre a base inteira (🧹 Qualidade dos Dados, 💡 Insights e Hipóteses) ignoram o filtro de propósito, para não esconder o problema que se quer encontrar.

O corte da janela final não consolidada da série (registro que a PRF ainda não terminou de preencher) não é mais um filtro da sidebar — a camada **Silver** já aplica esse corte diretamente no dado. O diagnóstico completo está na página 🧹 Qualidade dos Dados.

---

## 🏗️ Arquitetura de dados

Cada camada do DuckDB (`raw`, `bronze`, `silver`, `gold`) é um schema; cada tabela dentro dela tem **um script próprio** em `src/`, responsável só por ela — "esse arquivo cria essa tabela":

| Tabela DuckDB | Script | Depende de | O que faz |
|---|---|---|---|
| `raw.acidentes` | [`src/raw/acidentes.py`](src/raw/acidentes.py) | `data/raw/datatran*.csv` | Lê os CSVs anuais da PRF (encoding/separador), sem nenhuma regra de negócio |
| `raw.feriados` | [`src/raw/feriados.py`](src/raw/feriados.py) | `data/raw/feriados_nacionais.xls` | Lê a planilha da ANBIMA tal como está, rodapé incluso |
| `bronze.acidentes` | [`src/bronze/acidentes.py`](src/bronze/acidentes.py) | `raw.acidentes` | Tipagem, tratamento de ausentes, deduplicação — [`etapa1-pre-processamento.md`](docs/entregas/etapa1-pre-processamento.md) |
| `bronze.feriados` | [`src/bronze/feriados.py`](src/bronze/feriados.py) | `raw.feriados` | Remove rodapé, padroniza tipos, filtra o período do projeto (2022–2026) |
| `silver.acidentes` | [`src/silver/acidentes.py`](src/silver/acidentes.py) | `bronze.acidentes`, `bronze.feriados` | Enriquecimento analítico (ano/mês/hora, gravidade, calendário) + corte de consolidação (D-13) |
| `gold.dataset_ml` | [`src/gold/dataset_ml.py`](src/gold/dataset_ml.py) | `silver.acidentes` | Seleciona/transforma as features + target prontos para ML, com guard-rail de *leakage* |

Validação de qualidade (`src/bronze/validation.py`) roda sobre a Bronze logo após ela ser construída — preserva as mesmas checagens de sempre (schema, tipos, nulos, intervalos, consistência entre colunas).

**Central de conexão:** [`src/database/connection.py`](src/database/connection.py) — caminho do banco (`data/prf.duckdb`), criação dos schemas e o utilitário `create_table_from_df` que todo `create_table(con)` usa para materializar sua tabela. Nenhum script abre o arquivo `.duckdb` "na mão".

**Orquestrador único:** [`src/jobs/build_database.py`](src/jobs/build_database.py) — só chama, na ordem certa, o `create_table(con)` de cada tabela; a lógica de transformação continua em cada script de tabela, nunca aqui.

```bash
python -m src.jobs.build_database
```

reconstrói o banco inteiro do zero (`raw → bronze → validação → silver → gold`). Cada `create_table(con)` também garante sozinho sua dependência direta — chamar `python -m src.silver.acidentes`, por exemplo, constrói `bronze.acidentes`/`bronze.feriados` primeiro caso ainda não existam.

**Fonte única:** o dado processado existe em um lugar só — as tabelas de `data/prf.duckdb`. Não há espelho em Parquet: cada camada lê a anterior direto do banco (`bronze.acidentes` ← `raw.acidentes`, `silver.acidentes` ← `bronze.*`, `gold.dataset_ml` ← `silver.acidentes`). Em `data/` ficam apenas os CSVs/XLS originais da PRF/ANBIMA, que não são regeneráveis, e o próprio banco, que é.

**Streamlit consome, não reconstrói:** `app/common.py` só abre conexões **somente leitura** (`read_only=True`) sobre `data/prf.duckdb` e consulta `silver.acidentes`/`gold.dataset_ml`/`bronze.*` diretamente — nenhuma página do dashboard reprocessa os CSVs brutos. Se o banco não existir ainda, rode o pipeline primeiro (passo 1 de "Como executar").

---

## ✅ Testes

```bash
python -m pytest
```

`tests/` cobre:
- **Banco** (`test_database.py`) — `data/prf.duckdb` existe, os 4 schemas existem, as 6 tabelas esperadas existem e não estão vazias;
- **Dependências** (`test_dependencies.py`) — Bronze/Silver/Gold conseguem ser (re)construídas a partir da sua dependência direta, com a granularidade certa em cada etapa;
- **Qualidade** (`test_bronze_quality.py`) — as validações já existentes (`src/bronze/validation.py`) continuam passando;
- **Gold** (`test_gold.py`) — `gold.dataset_ml` contém exatamente as colunas de id/target/features documentadas em `FEATURE_DICTIONARY`, e nenhuma coluna de *leakage* (`src.eda.utils.LEAKAGE_COLS`);
- **Conexão** (`test_connection.py`) — `src/database/connection.py` isolado, em um banco temporário próprio.

Os testes de banco/dependências/qualidade/gold constroem `data/prf.duckdb` uma vez por sessão (via o próprio `src.jobs.build_database`) — a primeira execução demora ~40s, as seguintes reusam o banco já construído na mesma sessão de teste.

---

## 📁 Estrutura

```text
data/
  raw/*.csv, *.xls          # bruto (PRF/ANBIMA) — fonte original, nunca alterado
  prf.duckdb                # banco analítico oficial (schemas raw/bronze/silver/gold)
src/
  raw/                      # 1 script por tabela Raw (ingestão bruta)
  bronze/                   # 1 script por tabela Bronze (limpeza) + validation.py
  silver/                   # 1 script por tabela Silver (enriquecimento)
  gold/                     # 1 script por tabela Gold (features + target para ML)
  database/                 # conexão central com o DuckDB
  jobs/                     # build_database.py — orquestrador único do pipeline
  eda/
    utils.py                 # camada analítica compartilhada (DuckDB + estatística)
    run.py                   # gera os artefatos reproduzíveis da EDA
app/                        # aplicação Streamlit (independente do pipeline)
  app.py                     # roteador (st.navigation) + página inicial
  common.py                  # conexão (somente leitura), cache e filtros globais
  home_view.py               # conteúdo da página "Visão Geral"
  pages/                     # as demais 12 páginas, agrupadas via st.navigation
tests/                       # banco, dependências, qualidade, gold, conexão
reports/                     # resultados gerados (nunca código-fonte)
  data_quality/              # relatórios de validação do pipeline
  gold/                      # dicionário de features + relatório da Gold
  eda/                       # eda_results.json + 26 tabelas CSV
docs/                        # documentação — ver seção 📚 Documentação
scripts/                     # utilitários de verificação (smoke test, setup do ambiente)
```

Não há pasta `archive/`: a auditoria que precedeu esta reorganização não encontrou código morto, versão duplicada ou experimento abandonado no fluxo atual — o repositório já havia sido limpo em reorganizações anteriores (a Bronze antiga em `src/preprocessing/`, o `src/pipeline.py` monolítico e as páginas Streamlit substituídas já não existem). Se isso mudar, `archive/<subpasta>/` mais um `archive/README.md` explicando o que foi movido e por quê é o padrão a seguir.

---

## 📚 Documentação

`docs/` é a fonte de verdade das entregas, evidências, decisões e análises do projeto — este README é só o mapa; os detalhes de cada etapa ficam nos documentos abaixo, não duplicados aqui.

| Pasta / documento | Conteúdo |
|---|---|
| [`docs/entregas/`](docs/entregas/) | Relatório técnico entregue em cada etapa da disciplina (coleta, pré-processamento, EDA) |
| [`docs/evidencias/`](docs/evidencias/) | Logs brutos da última execução real do pipeline (`preprocess_run.log`, `verify_run.log`) |
| [`docs/decisoes/DECISIONS.md`](docs/decisoes/DECISIONS.md) | Decisões técnicas (D-01…D-14), com as alternativas descartadas e o porquê |
| [`docs/analises/`](docs/analises/) | `EDA.md` (documento narrativo da exploração), `ANALYSIS_LOG.md` (achado → método → resultado → limitação) e `DATA_QUALITY.md` (relatório de qualidade) |
| [`docs/specs/`](docs/specs/) | Especificação original do projeto e do pré-processamento (`spec.md`, `requirements.md`, `design.md`, `tasks.md`) — planejamento anterior à implementação, mantido como referência histórica |
| [`docs/GLOSSARIO.md`](docs/GLOSSARIO.md) | Termos técnicos (z-score, qui-quadrado, Cramér's V, intervalo de confiança, data leakage…) com exemplos desta base |

Quem estiver chegando agora no projeto: comece pelo [`GLOSSARIO.md`](docs/GLOSSARIO.md) se algum termo não for familiar, depois [`docs/entregas/etapa2-eda.md`](docs/entregas/etapa2-eda.md) para o panorama da análise.

---

## 🚀 Próximas etapas

A Etapa 3 (Construção de Modelos) ainda não foi iniciada — o escopo até aqui é Coleta, Pré-processamento e EDA (ver 🔄 Ciclo de vida acima). Planejado para a próxima etapa:

- Engenharia de atributos sobre `gold.dataset_ml` (encoding de `municipio`/alta cardinalidade, split temporal treino/teste);
- Treino e avaliação de modelos de classificação para `grave_bin`, com baseline (Dummy Classifier) e métricas de Precision, Recall, F1-Score e PR-AUC da classe grave;
- A página 🤖 Modelos existia como placeholder nas etapas anteriores e foi removida do menu nesta reorganização — será recriada quando `models/metrics.json` existir de verdade, lendo os artefatos treinados (nunca recalculando nada na UI).

As hipóteses formuladas para orientar essa etapa (H-01 a H-06, cada uma com critério de confirmação/refutação) estão na página 💡 Insights e Hipóteses do dashboard, e são citadas pontualmente em [`docs/analises/ANALYSIS_LOG.md`](docs/analises/ANALYSIS_LOG.md).

---

## 🛠️ Tecnologias

`Python` · `Pandas` · `DuckDB` · `Scikit-learn` · `Streamlit` · `Plotly` · `SciPy` · `Machine Learning`

---

## 🎓 Projeto Acadêmico

Projeto desenvolvido no **Mackenzie**, aplicando conceitos de **Engenharia de Dados, Análise Exploratória e Machine Learning** a um problema do setor de viário.
