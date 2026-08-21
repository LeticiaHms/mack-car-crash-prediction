# Especificação do Projeto — Predição de Risco de Acidentes em Rodovias Federais

## 1. Visão geral

Projeto acadêmico de Engenharia de Dados cujo objetivo é construir um pipeline completo de dados e Machine Learning para identificar **trechos de rodovias federais brasileiras com maior risco de ocorrência de acidentes graves**.

O projeto deverá contemplar todo o ciclo de dados:

1. Coleta/ingestão de dados reais;
2. Armazenamento dos dados brutos;
3. Tratamento e transformação;
4. Análise exploratória;
5. Engenharia de atributos;
6. Treinamento de modelos de Machine Learning;
7. Avaliação dos modelos;
8. Geração de uma classificação de risco;
9. Apresentação dos resultados.

O projeto utilizará **exclusivamente dados públicos da Polícia Rodoviária Federal (PRF)**.

---

## 2. Fonte de dados

A única fonte de dados permitida no projeto será a base oficial da PRF:

> **Documento CSV de Acidentes — Agrupados por ocorrência**

Serão utilizados exclusivamente os arquivos referentes aos anos:

- 2022
- 2023
- 2024
- 2025
- 2026

Não deverão ser utilizadas fontes complementares externas, como INMET, IBGE, DNIT, ANTT ou outras bases de dados.

Fonte oficial:

https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf

O agente de IA deverá consultar o dicionário/documentação oficial da PRF antes de assumir o significado de qualquer coluna.

---

## 3. Problema

### Problema de negócio

Rodovias federais possuem milhares de acidentes todos os anos, porém os recursos disponíveis para prevenção de acidentes são limitados.

Órgãos responsáveis pela segurança viária precisam identificar quais regiões e trechos apresentam maior risco para priorizar ações como:

- fiscalização;
- melhoria da sinalização;
- manutenção da pista;
- iluminação;
- intervenções de engenharia;
- campanhas de segurança;
- priorização de recursos públicos.

O projeto pretende investigar se os próprios dados históricos de acidentes da PRF podem ser utilizados para **identificar trechos com maior risco de ocorrência de acidentes graves**.

### Pergunta principal

> É possível utilizar dados históricos de acidentes registrados pela PRF para identificar e classificar trechos de rodovias federais brasileiras com maior risco de ocorrência de acidentes graves?

---

## 4. Objetivo

Construir um modelo de Machine Learning capaz de atribuir um **nível de risco de acidentes graves** a determinados trechos de rodovias federais brasileiras.

O resultado final deverá permitir identificar, por exemplo:

- trechos de baixo risco;
- trechos de risco moderado;
- trechos de alto risco.

O modelo deverá ser utilizado como ferramenta de **apoio à priorização de ações de segurança viária**, e não como substituto da análise técnica dos órgãos responsáveis.

---

## 5. Unidade de análise

A unidade principal do projeto será um **trecho de rodovia**, e não um acidente individual.

Um trecho poderá ser definido inicialmente por:

- rodovia federal (BR);
- UF;
- município;
- intervalo de quilômetros.

Exemplo:

```text
BR-116
São Paulo
Km 80–90
```

A granularidade deverá ser definida após análise da disponibilidade e qualidade dos dados.

Uma alternativa, caso seja tecnicamente mais adequada, é utilizar uma divisão fixa dos trechos, por exemplo:

```text
segmentos de 5 km
```

ou

```text
segmentos de 10 km
```

A escolha deverá ser justificada com base nos dados disponíveis e na adequação ao problema.

---

## 6. Definição de "acidente grave"

A definição de acidente grave deverá ser estabelecida antes do treinamento do modelo.

Uma possibilidade inicial é considerar grave um acidente que:

- tenha pelo menos uma vítima fatal; ou
- tenha vítimas classificadas como graves, caso essa informação esteja disponível e seja confiável.

A definição final deverá ser baseada exclusivamente nas variáveis existentes no CSV da PRF.

O agente de IA não deverá assumir uma definição sem verificar primeiro as variáveis disponíveis.

---

## 7. Período dos dados

Serão utilizados exclusivamente os dados da PRF referentes aos anos:

```text
2022
2023
2024
2025
2026
```

Os dados deverão ser combinados em um único dataset após tratamento e padronização.

Como o problema possui dimensão temporal, a estratégia de divisão dos dados deverá respeitar a ordem cronológica sempre que possível.

Exemplo:

```text
2022–2024 → treinamento
2025 → validação
2026 → teste
```

Os períodos exatos deverão ser definidos após análise do volume e qualidade dos dados.

Não realizar divisão aleatória dos dados caso isso provoque vazamento temporal.

---

## 8. Variável alvo

A variável alvo deverá representar o risco de acidentes graves em determinado trecho e período.

Uma abordagem inicial:

```text
target = 1
se o trecho apresentar acidente grave no período

target = 0
caso contrário
```

Outra possibilidade é trabalhar com quantidade ou taxa de acidentes graves:

```text
número de acidentes graves por trecho/período
```

A escolha entre classificação binária, multiclasse ou regressão deverá ser feita após análise dos dados.

O agente deverá comparar as alternativas e justificar a escolha.

---

## 9. Características esperadas

As features deverão ser construídas exclusivamente a partir das informações presentes nos CSVs da PRF.

Possíveis features:

### Localização

- UF;
- município;
- BR;
- km;
- latitude;
- longitude;
- região, se derivada exclusivamente dos dados existentes.

### Temporais

- ano;
- mês;
- dia da semana;
- hora;
- fim de semana;
- período do dia;
- estação do ano, caso seja derivada da data.

### Características da rodovia

- tipo de pista;
- condição da pista;
- sentido;
- características da via;
- demais atributos disponíveis no dataset.

### Histórico de acidentes

- quantidade total de acidentes;
- quantidade de acidentes graves;
- quantidade de acidentes fatais;
- quantidade de feridos;
- média de acidentes;
- tendência recente;
- quantidade de acidentes em períodos anteriores;
- histórico do trecho.

A criação das features deverá respeitar o momento da previsão e evitar utilização de informações futuras.

---

## 10. Data Leakage

O projeto deverá evitar utilizar informações que só seriam conhecidas **depois que o acidente ocorreu**.

Por exemplo, se o objetivo é prever risco futuro, não utilizar como feature informações diretamente relacionadas ao resultado do evento que está sendo previsto.

Não utilizar como feature:

- número de mortos do próprio acidente;
- número de feridos do próprio acidente;
- classificação final do próprio acidente;
- qualquer informação que revele diretamente o target.

Features históricas poderão ser utilizadas desde que sejam calculadas exclusivamente com informações disponíveis antes do período previsto.

---

## 11. Engenharia de Dados

O projeto deve demonstrar claramente as etapas de Engenharia de Dados.

Arquitetura conceitual:

```text
              ┌─────────────────────┐
              │    PRF 2022 CSV     │
              ├─────────────────────┤
              │    PRF 2023 CSV     │
              ├─────────────────────┤
              │    PRF 2024 CSV     │
              ├─────────────────────┤
              │    PRF 2025 CSV     │
              ├─────────────────────┤
              │    PRF 2026 CSV     │
              └──────────┬──────────┘
                         │
                         ▼
                ┌─────────────────┐
                │    INGESTÃO     │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │    DATA LAKE    │
                │       RAW       │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │  PROCESSAMENTO  │
                │    PySpark      │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │    CURATED      │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │       EDA       │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │     FEATURES    │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │       ML        │
                └────────┬────────┘
                         ▼
                ┌─────────────────┐
                │  RISCO FINAL    │
                └─────────────────┘
```

A arquitetura tecnológica poderá utilizar, conforme disponibilidade e familiaridade da equipe:

- Python;
- PySpark;
- SQL;
- PostgreSQL;
- DuckDB;
- Parquet;
- Docker;
- MinIO ou outro armazenamento compatível com S3;
- Jupyter;
- MLflow, caso seja viável;
- Git/GitHub.

Não é obrigatório utilizar todas essas tecnologias.

A escolha deve priorizar simplicidade, reprodutibilidade e adequação ao projeto acadêmico.

---

## 12. Camadas de dados

### Raw

Dados exatamente como obtidos da PRF.

Exemplo:

```text
raw/
└── prf/
    └── acidentes/
        ├── 2022/
        ├── 2023/
        ├── 2024/
        ├── 2025/
        └── 2026/
```

Não modificar os dados originais nessa camada.

### Curated

Dados:

- padronizados;
- tipados;
- deduplicados;
- tratados;
- consolidados;
- prontos para análise.

### Feature

Dataset final utilizado pelo modelo.

Deve conter:

```text
identificação do trecho
+
features históricas
+
features temporais
+
target
```

Todos os dados deverão ter origem nos arquivos CSV da PRF.

---

## 13. Análise exploratória

A análise deverá responder perguntas como:

- Quais estados possuem maior quantidade de acidentes?
- Quais rodovias apresentam maior concentração?
- Quais trechos possuem maior frequência de acidentes graves?
- Existe sazonalidade?
- Quais horários concentram acidentes?
- Quais tipos de acidente são mais graves?
- Existem diferenças entre regiões?
- Existem trechos persistentemente problemáticos?
- Como a quantidade e a gravidade dos acidentes evoluíram entre 2022 e 2026?

A EDA deverá ser utilizada para orientar a criação das features e a modelagem.

---

## 14. Machine Learning

O projeto deverá testar pelo menos dois modelos.

### Baseline

- Dummy Classifier ou modelo estatístico simples.

### Modelos principais

- Logistic Regression;
- Random Forest;
- XGBoost ou LightGBM.

A escolha final deverá considerar:

- desempenho;
- interpretabilidade;
- tempo de treinamento;
- complexidade;
- adequação aos dados.

Não utilizar modelos complexos apenas para obter maior sofisticação acadêmica.

---

## 15. Métricas

Caso o problema seja classificação:

- Precision;
- Recall;
- F1-score;
- ROC-AUC;
- matriz de confusão.

Como acidentes graves podem ser eventos menos frequentes, o **Recall da classe de alto risco** deverá receber atenção especial.

Não utilizar apenas Accuracy como métrica principal.

---

## 16. Desbalanceamento

O dataset poderá apresentar forte desbalanceamento entre:

```text
trechos/períodos sem acidentes graves
vs.
trechos/períodos com acidentes graves
```

O projeto deverá investigar:

- distribuição das classes;
- class weights;
- undersampling;
- oversampling;
- SMOTE, caso apropriado.

Qualquer técnica aplicada deverá ser utilizada somente no conjunto de treinamento para evitar vazamento de dados.

---

## 17. Interpretabilidade

Além de prever risco, o projeto deverá buscar explicar **quais fatores estão associados ao risco**.

Possibilidades:

- feature importance;
- SHAP;
- análise de coeficientes;
- importância por permutação.

O objetivo é responder:

> Quais características mais influenciam a classificação de um trecho como alto risco?

---

## 18. Resultado esperado

O produto final deverá permitir produzir algo semelhante a:

```text
Trecho           Período       Risco
BR-116 km 80–90  2026-07       ALTO
BR-101 km 120–130 2026-07      MÉDIO
BR-381 km 50–60  2026-07       BAIXO
```

Idealmente, o resultado poderá ser apresentado visualmente em um mapa utilizando exclusivamente as informações geográficas existentes nos dados da PRF.

O mapa é desejável, mas não obrigatório.

---

## 19. Critérios de sucesso

O projeto será considerado bem-sucedido se:

- utilizar dados reais da PRF;
- utilizar exclusivamente os CSVs de acidentes agrupados por ocorrência;
- utilizar dados dos anos 2022 a 2026;
- possuir pipeline de ingestão;
- possuir armazenamento dos dados brutos;
- possuir tratamento e transformação;
- possuir análise exploratória;
- possuir engenharia de atributos;
- possuir modelo de ML;
- possuir avaliação quantitativa;
- evitar data leakage;
- gerar uma classificação/predição de risco;
- conseguir explicar os principais fatores relacionados ao risco;
- possuir código reprodutível.

O sucesso não deve ser definido apenas pela obtenção de uma alta métrica de ML.

---

## 20. Restrições acadêmicas

O projeto deve priorizar:

- dados reais;
- fonte oficial;
- dados públicos;
- dados recentes;
- reprodutibilidade;
- transparência;
- justificativa das decisões;
- simplicidade suficiente para execução dentro do prazo acadêmico.

Não criar dados fictícios para aumentar o tamanho do dataset.

Não utilizar informações externas aos CSVs da PRF.

Toda transformação ou feature derivada deverá ser rastreável aos dados originais.

---

## 21. Responsabilidades do agente de IA

A IA que auxiliar no projeto deverá:

1. Ajudar a analisar e validar os arquivos da PRF;
2. Consultar a documentação oficial antes de assumir o significado de uma coluna;
3. Ajudar a definir o schema dos dados;
4. Auxiliar na construção do pipeline de ingestão;
5. Identificar problemas de qualidade dos dados;
6. Auxiliar no tratamento e transformação;
7. Auxiliar na análise exploratória;
8. Sugerir features utilizando somente os dados da PRF;
9. Identificar possíveis casos de data leakage;
10. Auxiliar na escolha dos modelos;
11. Implementar e explicar os modelos;
12. Avaliar os resultados;
13. Comparar modelos;
14. Auxiliar na interpretação das previsões;
15. Manter o projeto reproduzível;
16. Documentar decisões técnicas;
17. Evitar adicionar complexidade sem justificativa.

A IA não deverá simplesmente gerar código sem explicar sua finalidade.

Sempre que uma decisão metodológica tiver impacto significativo no resultado, deverá apresentar a justificativa e, quando possível, alternativas.

---

## 22. Princípio importante

O projeto não deve ser tratado como:

> "Encontrar um dataset e aplicar Machine Learning."

Deve ser tratado como:

> **"Resolver um problema real utilizando uma arquitetura de dados capaz de transformar dados públicos brutos da PRF em informações úteis para tomada de decisão."**

O Machine Learning é uma etapa do projeto, e não o projeto inteiro.

---

## 23. Hipótese inicial

Hipótese a ser investigada:

> **Características geográficas, temporais, estruturais e históricas presentes nos registros de acidentes da PRF podem ser utilizadas para identificar trechos de rodovias federais com maior probabilidade de ocorrência de acidentes graves.**

A hipótese deverá ser validada ou rejeitada com base nos resultados obtidos.

---

## 24. Questões que devem ser respondidas ao final

O projeto deverá conseguir responder:

1. Quais trechos apresentam maior risco?
2. Quais fatores estão mais associados ao risco?
3. O histórico de acidentes do trecho é uma boa variável preditora?
4. Quais características dos acidentes possuem maior poder preditivo?
5. Qual modelo apresenta melhor desempenho?
6. O modelo consegue identificar corretamente os trechos de alto risco?
7. Quais são as limitações da abordagem?
8. Como o resultado poderia ser utilizado em uma aplicação real?

---

## 25. Limitações esperadas

O projeto deverá reconhecer limitações como:

- subnotificação ou inconsistência nos dados;
- mudanças na metodologia de coleta ao longo dos anos;
- ausência de dados de fluxo de veículos;
- ausência de determinadas características da infraestrutura;
- diferenças entre municípios e regiões;
- possível desbalanceamento;
- dificuldade de representar adequadamente o risco apenas com dados históricos de acidentes;
- impossibilidade de interpretar correlação como causalidade.

O modelo deverá ser apresentado como ferramenta de **apoio à decisão**, não como prova de que determinado trecho necessariamente causará acidentes.

---

## 26. Entregáveis

### Dados

- dados brutos dos CSVs da PRF;
- dados tratados;
- dataset final de ML.

### Código

- ingestão;
- transformação;
- consolidação dos anos;
- EDA;
- feature engineering;
- treinamento;
- avaliação.

### Documentação

- fonte dos dados;
- arquitetura;
- dicionário de dados;
- decisões metodológicas;
- metodologia de ML;
- resultados;
- limitações.

### Resultado

- modelo treinado;
- métricas;
- análise das features;
- classificação de risco dos trechos;
- visualização dos resultados, preferencialmente em mapa.

---

## 27. Regra para tomada de decisões

Sempre priorizar:

**fonte oficial > fonte secundária**

**dados reais > dados artificiais**

**simplicidade > complexidade desnecessária**

**reprodutibilidade > solução manual**

**problema de negócio > modelo sofisticado**

**qualidade dos dados > quantidade de dados**

**dados da PRF > qualquer fonte externa**

O projeto deve ser suficientemente simples para ser concluído no prazo, mas suficientemente completo para demonstrar competências de Engenharia de Dados e Machine Learning.
