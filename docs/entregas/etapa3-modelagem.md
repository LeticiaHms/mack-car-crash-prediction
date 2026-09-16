# Etapa 3 — Aprendizado de Máquina Preditivo

**Projeto:** Predição de Risco de Acidentes em Rodovias Federais (base PRF + feriados ANBIMA)
**Código:** [`src/ml/modelagem.py`](../../src/ml/modelagem.py) (arquivo único) · [`src/ml/README.md`](../../src/ml/README.md)
**Evidências:** [`reports/ml/metrics.csv`](../../reports/ml/metrics.csv) · [`reports/ml/class_distribution.png`](../../reports/ml/class_distribution.png) · [`reports/ml/confusion_matrix.png`](../../reports/ml/confusion_matrix.png) · [`reports/ml/roc_curve.png`](../../reports/ml/roc_curve.png) · [`reports/ml/metric_comparison.png`](../../reports/ml/metric_comparison.png)
**Dataset de entrada:** `gold.dataset_ml` (DuckDB) — 311.259 acidentes, 2022-01-01 a 2026-06-23

> Como ler: todo número deste documento vem de `python -m src.ml.modelagem`, executado sobre a base real — nenhum foi digitado à mão. Reexecutar o comando reproduz exatamente os mesmos números (sem aleatoriedade não controlada: `random_state=42` em todos os modelos).

Esta etapa foi implementada em versão **simples e didática**, propositalmente: um único arquivo, 3 algoritmos, sem busca de hiperparâmetros, sem módulos separados de tuning/interpretabilidade/viés/inferência. O objetivo é comparar algoritmos de Machine Learning num problema de classificação binária, não construir uma arquitetura de produção (ver [`src/ml/README.md`](../../src/ml/README.md) para o que foi deliberadamente deixado de fora).

---

## 3.1 Problema de Machine Learning

**Tipo:** classificação binária supervisionada. **Unidade de análise:** um acidente individual.

**Variável alvo:** `grave_bin` — `1` se o acidente teve ao menos um morto ou ferido grave, `0` caso contrário. Já vem definida e calculada na camada Gold (`src/gold/dataset_ml.py`), não recalculada aqui.

Distribuição na base completa (311.259 registros):

| Classe | Registros | % |
|---|---:|---:|
| 0 — Não grave | 223.250 | 71,7% |
| 1 — Grave/fatal | 88.009 | 28,3% |

Desbalanceamento moderado (~2,5:1), tratado via `class_weight="balanced"`/`"balanced_subsample"` em todos os modelos (reponderação da função de perda no treino, sem reamostragem — mais simples e suficiente para um desbalanceamento não extremo).

**Objetivo:** verificar se características do acidente e da rodovia, conhecidas *antes* do desfecho, ajudam a prever se um acidente será grave — apoio à priorização, não previsão determinística.

---

## 3.2 Seleção dos algoritmos

Da lista de algoritmos permitida (Regressão Linear, Regressão Logística, Árvore de Decisão, Random Forest, KNN, SVM, K-Means, Redes Neurais), **Regressão Linear** e **K-Means** ficam de fora por não servirem a um problema de classificação binária (a primeira é para alvo contínuo, o segundo é não supervisionado). Dos algoritmos de classificação restantes, foram escolhidos:

- **Regressão Logística** — modelo linear de referência: rápido, interpretável via coeficientes, bom ponto de partida para medir se há sinal linear nos dados.
- **Árvore de Decisão** — captura relações não-lineares e interações entre features sem exigir transformação manual; caminho de decisão auditável.
- **Random Forest** — ensemble de árvores (bagging); tende a reduzir a variância/overfitting de uma árvore única, ao custo de menor interpretabilidade direta.

KNN e SVM ficaram de fora por razão prática de escala: com ~218 mil registros de treino e ~190 colunas após one-hot, KNN exigiria calcular distância para toda a base de treino a cada previsão, e SVM não escala bem além de dezenas de milhares de linhas — nenhum indício de que superariam os três modelos escolhidos justificaria esse custo neste experimento simples. Redes Neurais ficaram de fora por exigirem mais tuning/dados para justificar a complexidade extra frente aos três modelos mais simples já escolhidos.

---

## 3.3 Preparação dos dados

### Features utilizadas (29)

| Grupo | Features |
|---|---|
| Categóricas (7) | `uf`, `br`, `tipo_pista`, `sentido_via`, `uso_solo`, `dia_semana`, `fase_dia` |
| Numéricas (7) | `km`, `latitude`, `longitude`, `hora`, `hora_sin`, `hora_cos`, `mes` |
| Booleanas (15) | `br_valido`, `km_valido`, `fim_de_semana`, `tracado_reta`, `tracado_curva`, `tracado_aclive`, `tracado_declive`, `tracado_interseccao_de_vias`, `tracado_retorno_regulamentado`, `tracado_rotatoria`, `tracado_ponte`, `tracado_viaduto`, `tracado_em_obras`, `tracado_desvio_temporario`, `tracado_tunel` |

Todas descrevem o acidente/rodovia no momento do evento (onde, que tipo de via, quando) — nunca o resultado dele. Contribuem para a previsão porque a EDA da Etapa 2 já mostrou associação entre gravidade e localização (UF, coordenadas), tipo de pista (simples vs. dupla), período do dia/fase de iluminação e geometria da via (curva, declive etc.).

### Exclusão de variáveis com leakage

As colunas abaixo **já não existem** em `gold.dataset_ml` — foram removidas na camada Gold anterior (`src/gold/dataset_ml.py`), com um guard-rail automático que barra a build se alguma delas voltar como feature:

`mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `pessoas`, `veiculos`, `classificacao_acidente`, `causa_acidente`, `tipo_acidente` — todas descrevem o **resultado** do acidente, só existem depois dele.

Além disso, não são usadas como feature nesta etapa:

| Coluna | Por quê |
|---|---|
| `id` | Identificador técnico, sem significado preditivo. |
| `data_inversa`, `ano` | Usadas só para o split temporal; os componentes úteis (`mes`, `dia_semana`, `hora`) já entram como feature. |
| `grave_bin`, `gravidade_4` | São o alvo (ou uma variante dele) — nunca feature de si mesmo. |
| `municipio` | 2.057 categorias — one-hot explodiria a dimensionalidade; um encoding mais sofisticado (frequência/taxa) foge do escopo simples desta etapa. A informação geográfica já é capturada por `uf`, `latitude` e `longitude`. |
| `geocoord_valido` | Constante (100% `True` na base atual, verificado via DuckDB) — zero variância, zero informação para qualquer modelo. |

### Divisão treino/validação/teste

Os dados têm dimensão temporal (2022–2026): um split aleatório permitiria ao modelo "ver" indiretamente padrões do futuro. Por isso a divisão foi feita por **corte de data**, mantendo a ordem cronológica, sempre no limite de um dia (nunca cortando um mesmo dia entre conjuntos):

| Conjunto | Registros | % | Período | % grave |
|---|---:|---:|---|---:|
| Treino | 217.907 | 70,0% | 2022-01-01 → 2025-03-08 | 28,27% |
| Validação | 46.761 | 15,0% | 2025-03-09 → 2025-10-29 | 28,65% |
| Teste | 46.591 | 15,0% | 2025-10-30 → 2026-06-23 | 27,92% |

A taxa de `grave_bin=1` estável nos três conjuntos (27,9%–28,7%) confirma que o corte não introduziu viés de composição. Como esta etapa **não faz busca de hiperparâmetros**, a validação não decide nada — ela serve apenas como uma checagem intermediária de generalização (comparar treino vs. validação) antes da leitura final. **O teste é usado exclusivamente para a avaliação final** — não é tocado durante o treino nem durante o pré-processamento (o `ColumnTransformer` é ajustado, via `Pipeline`, apenas com dados de treino; validação e teste passam só por `.transform()`), o que evita vazamento de dados entre as etapas.

Para variáveis categóricas: valores ausentes viram a categoria explícita `"nao_informado"`, seguida de One-Hot Encoding (`handle_unknown="ignore"`, para que uma categoria nova em produção não quebre o modelo). Para variáveis numéricas: imputação pela mediana seguida de padronização (`StandardScaler`) — necessária para a Regressão Logística, neutra para os modelos de árvore, mas aplicada à mesma matriz para os três, por simplicidade. Variáveis booleanas passam direto (0/1), sem transformação.

---

## 3.4 Treinamento

Os três modelos foram treinados sobre o **mesmo** conjunto de treino e avaliados sobre os **mesmos** conjuntos de validação e teste, cada um dentro de um `Pipeline` scikit-learn (pré-processamento + modelo). Sem busca de hiperparâmetros: usamos os padrões do scikit-learn com um único ajuste simples e justificado por modelo:

| Modelo | Configuração | Por quê |
|---|---|---|
| Regressão Logística | `max_iter=1000`, `class_weight="balanced"` | Mais iterações que o padrão (100) para garantir convergência com ~190 colunas após one-hot; peso de classe para compensar o desbalanceamento. |
| Árvore de Decisão | `max_depth=10`, `min_samples_leaf=50`, `class_weight="balanced"` | Profundidade e folha mínima limitadas para conter overfitting numa árvore única com ~218 mil registros de treino. |
| Random Forest | `n_estimators=200`, `max_depth=10`, `min_samples_leaf=5`, `class_weight="balanced_subsample"` | Mesma lógica de profundidade da árvore única; `balanced_subsample` recalcula o peso de classe a cada árvore do ensemble. |

Todos usam `random_state=42` (reprodutibilidade).

---

## 3.5 Avaliação

Métricas sobre o conjunto de teste (nunca usado para treinar ou ajustar nada até este ponto):

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Regressão Logística | 0,5915 | 0,3543 | 0,5630 | **0,4349** | 0,6198 |
| Árvore de Decisão | 0,5929 | 0,3515 | 0,5422 | 0,4265 | 0,6118 |
| **Random Forest** | **0,5960** | **0,3548** | 0,5460 | 0,4301 | **0,6211** |

(Tabela também em [`reports/ml/metrics.csv`](../../reports/ml/metrics.csv); gráficos em `reports/ml/confusion_matrix.png`, `roc_curve.png` e `metric_comparison.png`.)

Como checagem intermediária (não usada para decidir nada, sem tuning nesta etapa), o F1 em **validação** ficou em 0,442 (Regressão Logística), 0,433 (Árvore de Decisão) e 0,441 (Random Forest) — muito próximo do F1 de teste de cada modelo, sem sinal de overfitting relevante entre validação e teste.

Matriz de confusão no teste (46.591 registros, 27,92% grave):

| Modelo | TN | FP | FN | TP |
|---|---:|---:|---:|---:|
| Regressão Logística | 20.237 | 13.347 | 5.684 | 7.323 |
| Árvore de Decisão | 20.571 | 13.013 | 5.954 | 7.053 |
| Random Forest | 20.668 | 12.916 | 5.905 | 7.102 |

---

## 3.6 Comparação dos modelos

As métricas de Accuracy, Precision e ROC-AUC favorecem levemente o **Random Forest**; Recall e F1 favorecem levemente a **Regressão Logística**. As diferenças são pequenas em todas as métricas — no máximo 0,004 de Accuracy, 0,003 de Precision, 0,021 de Recall, 0,008 de F1 e 0,009 de ROC-AUC entre o melhor e o pior dos três. A **Árvore de Decisão isolada é a mais fraca em toda métrica**, o que é esperado: uma única árvore, mesmo com profundidade limitada para conter overfitting, tem mais variância que um modelo linear regularizado por peso de classe ou que um ensemble de árvores.

O ganho do Random Forest sobre a Regressão Logística é pequeno o suficiente para não justificar, sozinho, abrir mão da interpretabilidade quase total da Regressão Logística (coeficientes diretos) em favor de um ensemble de 200 árvores. Essa proximidade é, em si, um resultado relevante: sugere que grande parte do "esforço extra" de um modelo mais complexo (Random Forest) não converte em desempenho real neste problema.

**Interpretabilidade simples** (importância nativa/coeficientes — associação usada pelo modelo, **não** causalidade):

- **Árvore de Decisão e Random Forest** concordam no núcleo do que mais pesa na decisão: `tipo_pista` (pista Simples vs. Dupla), `latitude` e `longitude` (localização geográfica) dominam o topo da importância, seguidos por `km`, `fase_dia` e a codificação cíclica do horário (`hora_cos`/`hora`). Isso é consistente com o achado da Etapa 2 (EDA) de que gravidade varia por tipo de pista e por região.
- **Regressão Logística**: os maiores coeficientes em módulo recaem sobre categorias específicas e pouco frequentes de `br` (código da rodovia). Isso é um efeito conhecido de One-Hot Encoding com categorias raras em modelos lineares — poucas observações de uma rodovia específica podem produzir um coeficiente grande e instável, sem necessariamente indicar a variável mais "importante" de forma robusta. Por isso, para uma leitura geral de quais características pesam mais, as árvores (que concordam entre si) são uma fonte mais estável neste experimento do que os coeficientes brutos da Regressão Logística.

---

## 3.7 Conclusão

Os três modelos superam claramente o acaso (ROC-AUC entre 0,61 e 0,62, acima de 0,50) mas ficam distantes de uma previsão de alta confiança — o que é esperado, já que as características mais fortemente associadas à gravidade de um acidente (tipo e causa do acidente) foram corretamente excluídas por só existirem depois do desfecho (*data leakage*). Isso confirma parcialmente a hipótese do projeto: **características estruturais e geográficas da rodovia (tipo de pista, localização) e temporais (horário, fase do dia) têm sinal preditivo real sobre a gravidade**, mas esse sinal, sozinho, tem teto moderado.

A proximidade entre os três modelos — nenhum vence com folga, e a Árvore de Decisão isolada é a única claramente inferior — é o achado mais relevante desta etapa: o gargalo de desempenho está no **conteúdo informativo das features disponíveis**, não na escolha do algoritmo. Um modelo mais simples e interpretável (Regressão Logística) entrega resultado equivalente a um ensemble mais complexo (Random Forest) neste problema.

Como resultado prático, os modelos são adequados como **ferramenta de triagem/priorização relativa** — ajudam a apontar onde a chance de gravidade é maior do que a média — mas não devem ser usados como previsão determinística de um acidente individual. Trabalho futuro que poderia elevar o teto de desempenho (fora do escopo desta etapa, deliberadamente simplificada): features de histórico do trecho (contagem/taxa de acidentes graves anteriores por BR/UF/km) e um encoding mais informativo para `municipio`.
