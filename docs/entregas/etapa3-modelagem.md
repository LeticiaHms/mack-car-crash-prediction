# Etapa 3 — Modelagem Preditiva

**Projeto:** Predição de Risco de Acidentes em Rodovias Federais (base PRF + feriados ANBIMA)
**Código:** [`src/ml/`](../../src/ml/) (`dataset.py` · `preprocessing.py` · `models.py` · `train.py` · `tune.py` · `evaluate.py` · `interpret.py` · `plots.py` · `inference.py` · `run_all.py`) · [`app/pages/11_🤖_Modelagem.py`](../../app/pages/11_🤖_Modelagem.py)
**Evidências:** [`reports/ml/tables/`](../../reports/ml/tables/) (métricas, comparações, tuning, importância, viés) · [`reports/ml/figures/`](../../reports/ml/figures/) (11 gráficos) · [`reports/ml/models/`](../../reports/ml/models/) (pipelines `.joblib`)
**Documentos relacionados:** [`docs/decisoes/DECISIONS.md`](../decisoes/DECISIONS.md) (D-15…D-20) · [`docs/entregas/etapa2-eda.md`](etapa2-eda.md) · [`reports/gold/feature_dictionary.csv`](../../reports/gold/feature_dictionary.csv)
**Dataset de entrada:** `gold.dataset_ml` (DuckDB) — 311.259 acidentes × 31 features + 2 alvos, 2022-01-01 a 2026-06-23

> Como ler: este documento é síntese executiva, não um passo a passo do código. Cada afirmação numérica vem de um arquivo em `reports/ml/` gerado por `python -m src.ml.run_all` — nenhum número foi digitado à mão.

---

## 🗣️ Resumo em linguagem simples

Treinamos 5 modelos para prever se um acidente vai ser **grave ou fatal**, usando só informações conhecidas *antes* do acidente (local, tipo de pista, horário — nunca o número de feridos, que só existe depois). O melhor modelo (**XGBoost ajustado**) foi testado em 46.591 acidentes que ele nunca tinha visto e conseguiu:

- **Identificar corretamente 56 de cada 100 acidentes graves reais** (métrica chamada *Recall*);
- **Acertar 37 de cada 100 vezes que ele soa o alarme de "risco alto"** (métrica chamada *Precision*);
- Separar acidente grave de leve **melhor que o acaso, mas não com grande margem** (nota de 0,63 em uma escala de 0,50=chute a 1,00=perfeito, chamada *ROC-AUC*).

**O que isso quer dizer na prática?** O modelo é útil como ferramenta de **triagem** — ajuda a priorizar onde olhar primeiro — mas não deve ser usado como verdade absoluta: ele erra bastante, e erra de forma **desigual entre estados** (funciona bem no Pará e no Piauí, mal em São Paulo e no Rio de Janeiro — ver seção 7/12). Testamos também "ajustar os botões" do modelo (*tuning*) e isso quase não mudou o resultado — sinal de que, para melhorar de verdade, precisaríamos de mais dados (como o histórico de acidentes de cada trecho de rodovia), não de um algoritmo diferente.

Um resumo interativo, com glossário e simulador, está disponível na página **🤖 Modelagem** do dashboard (`streamlit run app/app.py`). O restante deste documento é a versão técnica completa, com todas as métricas e justificativas.

---

## 1. Objetivo

O problema é **classificação binária supervisionada**: dado um acidente (localização, características da via, momento), prever se ele será **grave ou fatal** (`grave_bin=1`) antes de o desfecho ser conhecido. O objetivo não é prever acidentes individuais com certeza, mas produzir uma **probabilidade de gravidade** que sirva para priorizar trechos/condições para ações de segurança viária (spec, seções 3-4) — apoio à decisão, não substituto da análise técnica dos órgãos responsáveis (spec, seção 25).

`grave_bin` (D-02, Etapa 2) = 1 se houve pelo menos um morto ou ferido grave no acidente, 0 caso contrário. `gravidade_4` (multiclasse: Sem vítimas/Leve/Grave/Fatal) existe na Gold como alvo alternativo, não usado nesta etapa — mantido para trabalho futuro.

---

## 2. Preparação para modelagem

### 2.1 Diagnóstico inicial

| Pergunta | Resposta |
|---|---|
| Variável alvo | `grave_bin` (binária: 0=não grave, 1=grave/fatal) |
| Tipo de problema | Classificação binária |
| Registros | 311.259 (Gold, já sem leakage) |
| Desbalanceamento | 28,27% classe positiva — moderado (~2,5:1), não extremo (D-02) |
| Valores ausentes relevantes | `km` (0,48%), `br` (0,25%) — sentinelas já convertidos em NULL na Gold (D-04/D-05), com flag de validade ao lado |
| Variáveis constantes | `geocoord_valido` — 100% `True` na Gold atual, achado novo desta etapa (D-18) |
| Alta cardinalidade | `municipio` (2.057 categorias) |
| Risco de leakage | Guard-rail automático na Gold (`src/gold/dataset_ml.py`) barra `mortos`, `feridos_*`, `pessoas`, `veiculos`, `classificacao_acidente`, `causa_acidente`, `tipo_acidente` — as duas últimas são, por associação bruta, os sinais mais fortes da base (Cramér's V 0,30 e 0,24), mas não estão disponíveis no momento da previsão (D-07) |
| Colunas fora do treino | `id`, `data_inversa`, `ano` (identificação/split — `ano` deixaria o modelo aprender a fronteira do split, não um padrão real) e `gravidade_4` (alvo alternativo) |
| Limitação estrutural | Sem features de **histórico do trecho** (contagem de acidentes/graves anteriores) — a spec sugere como possível feature, mas construí-las exigiria agregação por (BR, UF, faixa de km) com corte temporal estrito, não implementada nesta iteração (ver seção 10) |

### 2.2 Seleção de features

30 features entram no treino — herdadas da seleção já leakage-checked da Gold (Etapa 2), com três decisões adicionais desta etapa: exclusão de `geocoord_valido` (constante, D-18), estratégia de encoding de `municipio` (frequência, D-17) e de `br` (categórica nominal, não numérica). Tabela completa com todas as 35 linhas (30 incluídas + 5 excluídas e por quê) em [`reports/ml/tables/feature_selection.csv`](../../reports/ml/tables/feature_selection.csv) e na página 🤖 Modelagem do dashboard. Resumo:

| Grupo | Features | Encoding |
|---|---|---|
| Categóricas (7) | `uf`, `br`, `tipo_pista`, `sentido_via`, `uso_solo`, `dia_semana`, `fase_dia` | One-hot, `handle_unknown="ignore"` |
| Alta cardinalidade (1) | `municipio` (2.057 valores) | Frequência relativa, ajustada só no treino (D-17) |
| Numéricas (7) | `km`, `latitude`, `longitude`, `hora`, `hora_sin`, `hora_cos`, `mes` | Mediana (imputação) + padronização |
| Booleanas (15) | `br_valido`, `km_valido`, `fim_de_semana`, `tracado_*` (12 primitivas) | Repassadas como 0/1 |

Após one-hot, a matriz final tem **193 colunas** (`br` sozinho contribui 124 categorias). Nenhuma feature foi removida só por correlação isolada baixa — `br_valido`/`km_valido` são quase-constantes (>99% `True`) mas mantidas porque a minoria carrega sinal forte (grave cai de 28% para 7,6%/13,7% quando `False`); `mes` tem Cramér's V=0,008 isolado mas foi mantida por potencial de interação (D-Etapa2).

### 2.3 Estratégia de divisão (70/15/15 temporal)

| Conjunto | Registros | % | Período | % grave |
|---|---:|---:|---|---:|
| Treino | 217.907 | 70,01% | 2022-01-01 → 2025-03-08 | 28,27% |
| Validação | 46.761 | 15,02% | 2025-03-09 → 2025-10-29 | 28,65% |
| Teste | 46.591 | 14,97% | 2025-10-30 → 2026-06-23 | 27,92% |

Split por **corte de data** (D-15), não por ano cheio nem aleatório: a spec pede respeitar a ordem cronológica, mas um corte por ano cheio (2022-24/2025/2026) deixaria o teste com só 10,7% da base, porque 2026 tem apenas 6 meses consolidados (corte D-13 da Etapa 2). Os cortes de data (`2025-03-09`, `2025-10-30`) foram escolhidos para aproximar 70/15/15 em contagem de linhas, preservando a garantia central de um split temporal: nenhuma linha de validação/teste antecede uma linha de treino. A taxa de `grave_bin=1` estável entre os três conjuntos (27,9%–28,7%) confirma que o corte não introduziu viés de composição temporal.

### 2.4 Pré-processamento

Um único `ColumnTransformer` (`src/ml/preprocessing.py`), ajustado **apenas no treino** e reaproveitado (via `Pipeline`) por todos os modelos — a mesma matriz de entrada serve tanto para a Regressão Logística quanto para os modelos de árvore, trocando só o estimador final. Isso garante, estruturalmente, que nenhuma estatística de validação/teste (mediana, frequência de município, categorias do one-hot) vaze para o ajuste dos transformadores — regra central desta etapa (seção 4 do pedido, D-17).

Desbalanceamento (D-16): tratado via `class_weight="balanced"`/`"balanced_subsample"` (scikit-learn) e `scale_pos_weight≈2,54` (XGBoost) — reponderação da função de perda, aplicada só no treino, sem reamostragem (SMOTE/undersampling rejeitados por desproporcionais a um desbalanceamento moderado de 2,5:1, ver D-16).

---

## 3. Modelos avaliados

5 modelos (1 baseline + 4 candidatos), escolhidos para cobrir famílias de modelagem distintas — exatamente os sugeridos pela spec (seção 14) mais um contraponto de árvore única:

| Modelo | Por que foi escolhido | Comportamento esperado |
|---|---|---|
| **Baseline Dummy** (`most_frequent`) | Piso de desempenho — evidencia por que Accuracy sozinha engana num problema desbalanceado | Accuracy alta (~71-72%, a própria taxa da classe majoritária), Recall/F1/ROC-AUC da classe grave nulos |
| **Regressão Logística** | Interpretável (coeficientes = log-odds), rápida, referência linear | Desempenho moderado, gap treino-teste pequeno (baixa variância) |
| **Árvore de Decisão** | Interpretável (caminho de decisão auditável), captura não-linearidade sem transformação manual | Profundidade limitada (max_depth=8) para conter overfitting; ainda assim mais variância que a Regressão Logística |
| **Random Forest** | Ensemble por bagging, reduz variância da árvore única, robusta a outliers | Deveria superar a árvore única com gap menor — nem sempre se confirma (ver seção 7) |
| **XGBoost** | Gradient boosting, corrige iterativamente os erros dos estimadores anteriores — geralmente o melhor desempenho bruto | Melhor desempenho de validação esperado, à custa de maior atenção ao gap treino-validação |

Detalhes de configuração, complexidade e interpretabilidade de cada um em `src/ml/models.py` (`MODEL_REGISTRY`) e em `reports/ml/tables/metrics_per_model.json`.

---

## 4. Resultados

Métricas escolhidas (seção 6 do pedido): **F1, Recall, Precision e ROC-AUC/PR-AUC da classe `grave_bin=1`** são as métricas de decisão — Accuracy é reportada, nunca usada isoladamente (a razão fica evidente na linha do baseline abaixo: 72% de Accuracy com Recall=0). PR-AUC é reportada ao lado de ROC-AUC por ser mais informativa quando a classe positiva é minoritária (D-02/skill `model-evaluation`).

**Antes do tuning** (validação), de `reports/ml/tables/model_comparison.csv`:

| Modelo | F1 treino | F1 validação | F1 teste | Recall (val) | Precision (val) | ROC-AUC (val) | PR-AUC (val) | Tempo treino |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_dummy | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 0,5000 | 0,2865 | 1,0s |
| logistic_regression | 0,4478 | 0,4468 | 0,4374 | 0,5799 | 0,3633 | 0,6228 | 0,3960 | 3,4s |
| decision_tree | 0,4547 | 0,4416 | 0,4329 | 0,5745 | 0,3586 | 0,6188 | 0,3907 | 4,5s |
| random_forest | 0,5053 | 0,4423 | 0,4336 | 0,5361 | 0,3765 | 0,6328 | 0,4091 | 171,2s |
| xgboost | 0,5082 | 0,4558 | 0,4426 | 0,5854 | 0,3732 | 0,6350 | 0,4101 | 6,2s |

Matriz de confusão do modelo final no teste (`xgboost_tuned`, ver seção 5): TN=20.843 · FP=12.741 · FN=5.661 · TP=7.346 (Recall=56,5%, Precision=36,6%). Falso negativo (acidente grave previsto como não grave) é o erro operacionalmente mais caro — 5.661 casos no teste (12,2% da base de teste) seriam trechos/momentos de risco real não sinalizados.

---

## 5. Modelo escolhido

**`xgboost_tuned`** — XGBoost com hiperparâmetros otimizados (`n_estimators=200, max_depth=8, learning_rate=0,05, scale_pos_weight=2,55`, ver seção "Tuning").

### Tuning

Estratégia (D-19): `RandomizedSearchCV` com `scoring="f1"` (classe grave) e `cv=PredefinedSplit` (treino=-1, validação=0) — um único fold fixo que respeita o corte temporal do split, em vez de um k-fold aleatório que embaralharia a ordem cronológica dentro do treino. Modelos otimizados: **XGBoost** (melhor de todos os candidatos em toda métrica de validação, e o mais rápido de treinar entre os modelos de árvore) e **Regressão Logística** (barata, interpretável, contraponto ao ensemble). `random_forest` ficou **fora do tuning por decisão de custo-benefício**: perdeu para o XGBoost em toda métrica de validação treinando ~27x mais devagar (171s vs. 6s por fit) — otimizá-lo custaria dezenas de minutos para, na melhor hipótese, alcançar um concorrente mais barato.

| Modelo | Parâmetros testados | Antes (F1 val) | Depois (F1 val) | Δ | Antes (F1 teste) | Depois (F1 teste) | Custo da busca |
|---|---|---:|---:|---:|---:|---:|---:|
| xgboost | `n_estimators`∈{200,300,500}, `max_depth`∈{3,4,6,8}, `learning_rate`∈{0,03;0,05;0,1;0,2}, `scale_pos_weight`∈{1;2;2,55} (20 combinações amostradas) | 0,4558 | 0,4559 | +0,0001 | 0,4426 | 0,4439 | 124,6s |
| logistic_regression | `C`∈{0,01; 0,1; 1; 3; 10} (5 combinações) | 0,4468 | 0,4468 | +0,0000 | 0,4374 | 0,4374 | 11,1s |

**Achado central do tuning: o ganho foi desprezível em ambos os casos** — a melhor combinação de XGBoost (`C=1,0` para a Regressão Logística já era o padrão) confirma que o teto de desempenho está no **conteúdo informativo das features disponíveis**, não na configuração do algoritmo. Isso é evidência a favor de investir esforço futuro em feature engineering (histórico do trecho, interações) em vez de busca de hiperparâmetros mais extensa — ver seção 10.

### Comparação final no teste (nunca usado para decidir até aqui)

| Modelo | F1 teste | Recall teste | Precision teste | ROC-AUC teste | PR-AUC teste | Gap treino-teste (F1) |
|---|---:|---:|---:|---:|---:|---:|
| **xgboost_tuned** | **0,4439** | 0,5648 | 0,3657 | **0,6336** | **0,4007** | 0,0713 |
| xgboost | 0,4426 | 0,5662 | 0,3633 | 0,6321 | 0,3985 | 0,0656 |
| logistic_regression | 0,4374 | 0,5729 | 0,3538 | 0,6220 | 0,3863 | 0,0104 |
| random_forest | 0,4336 | 0,5288 | 0,3675 | 0,6306 | 0,3991 | 0,0717 |
| decision_tree | 0,4329 | 0,5670 | 0,3501 | 0,6165 | 0,3813 | 0,0218 |
| baseline_dummy | 0,0000 | 0,0000 | 0,0000 | 0,5000 | 0,2792 | 0,0000 |

---

## 6. Evidências que sustentam a escolha

1. **`xgboost_tuned` lidera as três métricas de decisão no teste** (F1, ROC-AUC, PR-AUC) simultaneamente — não é um resultado que dependa de qual métrica se prioriza.
2. **A margem é pequena, e isso é dito explicitamente** (D-20): ΔF1 vs. Regressão Logística = +0,0065; vs. XGBoost sem tuning = +0,0013. A escolha não se apoia em "vitória esmagadora", mas em vantagem consistente nas três métricas ao custo computacional mais baixo entre os modelos de árvore (6-12s de treino).
3. **Custo-benefício explícito contra Random Forest**: pior em toda métrica de teste, ~27x mais lento — nenhuma dimensão favorece o Random Forest sobre o XGBoost neste problema.
4. **Interpretabilidade preservada**: XGBoost expõe importância nativa (gain) e é compatível com permutation importance — não é uma caixa-preta total, ver seção 10.
5. **Generalização aceitável apesar do gap maior**: o F1 cai só 0,012 de validação para teste (0,4559→0,4439) — a maior parte do gap treino-teste (0,0713) é overfitting relativo ao treino, não perda de capacidade preditiva real fora da amostra (ver seção 11).

---

## 7. Diagnóstico

**Faz sentido para o negócio?** PARCIALMENTE. O modelo separa razoavelmente bem trechos/momentos de maior risco do acaso (ROC-AUC 0,63 no teste, acima de 0,50) e o Recall de 56,5% significa que mais da metade dos acidentes graves teria o trecho/condição sinalizado previamente — útil como triagem, não como certeza. A Precision de 36,6% implica que, de cada ~3 alertas de "risco alto", só ~1 de fato seria grave — aceitável para priorização de fiscalização (custo de investigar um falso positivo é baixo), mas insuficiente para qualquer decisão automática de alto custo.

**Há overfitting?** POSSIVELMENTE, e de forma mensurável: `xgboost_tuned` tem gap F1 treino-teste de 0,0713 (F1 treino=0,5152 vs. teste=0,4439), o maior entre os candidatos com Random Forest (0,0717). A Regressão Logística tem gap de só 0,0104 — evidência direta de que os modelos de árvore mais complexos memorizam parte do treino que não generaliza. Ainda assim, o gap **validação→teste** de `xgboost_tuned` é pequeno (0,0120), o que limita a severidade do problema: o modelo overfita mais o treino do que a validação, e a validação já prediz bem o teste.

**Há underfitting?** NÃO, no sentido de "não aprendeu nada" — todos os candidatos superam o baseline em toda métrica de classe positiva (F1 baseline=0; melhor candidato=0,4439). SIM, num sentido mais relevante: mesmo o melhor modelo tem ROC-AUC de só 0,63 — um teto baixo em termos absolutos, porque as features circunstanciais mais associadas à gravidade (`tipo_acidente`, `causa_acidente`) foram corretamente excluídas por leakage (D-07). O gargalo é **conteúdo informativo disponível a priori**, não capacidade do algoritmo (reforçado pelo ganho quase nulo do tuning, seção 5).

**O modelo generaliza bem?** Moderadamente. F1 cai de 0,5152 (treino) para 0,4559 (validação) para 0,4439 (teste) — queda concentrada no primeiro salto (treino→validação), com estabilidade razoável depois (validação→teste). ROC-AUC/PR-AUC seguem o mesmo padrão. Não há sinal de colapso completo em dados nunca vistos (o que indicaria overfitting severo), mas também não há generalização perfeita.

**Há indícios de viés?** SIM, um viés de calibração por limiar único, com evidência quantitativa. O Recall do modelo final varia de **9,5% (SP)** a **92,8% (PA)** entre UFs no teste — correlação de 0,89 entre a taxa real de gravidade da UF e o recall obtido nela, e de 0,98 entre a probabilidade média prevista e o recall (`reports/ml/tables/bias_uf_test.csv`, gráfico `bias_recall_por_uf.png`). O mesmo padrão aparece em `tipo_pista` (Recall=77,5% em pista Simples vs. 29,2% em pista Dupla) e `fase_dia` (72,2% em Plena Noite vs. 43,3% em Pleno dia). **Interpretação:** o modelo usa um único limiar de decisão (0,5) sobre uma probabilidade calibrada para a base inteira; regiões/condições com prevalência de gravidade abaixo da média nacional (SP, RJ, DF, pista Dupla, Pleno dia) recebem sistematicamente menos alertas positivos, mesmo quando ocorre um acidente grave ali. Isso não é viés demográfico (a base não tem atributos de pessoas) nem confirma causalidade — é uma limitação de calibração de decisão com implicação real para equidade de alocação de recursos entre estados, que qualquer uso operacional precisa corrigir (ex.: limiar por UF ou por grupo, não um só global) — ver seção 10.

**O modelo é explicável?** SIM, com ressalvas. XGBoost não tem um caminho de decisão único como a árvore rasa, mas expõe importância nativa (gain) e é compatível com permutation importance — ambas calculadas (`reports/ml/tables/feature_importance_*_xgboost_tuned.csv`). A Regressão Logística, alternativa quase equivalente em desempenho, seria mais explicável ainda (coeficientes diretos); a escolha do XGBoost troca uma fração de transparência por desempenho consistentemente melhor nas três métricas de decisão.

**O custo computacional é justificável?** SIM. XGBoost treina em 6-12s (vs. 171s do Random Forest) e a busca de hiperparâmetros levou 125s — ambos triviais frente ao ganho de desempenho sobre a Regressão Logística. O único custo real é a perda parcial de interpretabilidade, discutida acima, não o tempo de computação.

---

## 8. Principais descobertas

1. **O tuning de hiperparâmetros teve efeito desprezível** (ΔF1 validação ≤ 0,0001 para os dois modelos otimizados) — o teto de desempenho está na informação disponível nas features, não na configuração do algoritmo. Acionável: investir esforço futuro em feature engineering, não em busca de hiperparâmetros mais extensa.
2. **`latitude` é a feature isoladamente mais importante por permutation importance** (queda de F1 de 0,026 ao embaralhá-la), à frente de `tipo_pista` (0,016) e `municipio` (0,014) — geografia domina sobre características estruturais da via, reforçando o achado de heterogeneidade geográfica já visto na EDA (D-14, excesso de gravidade do Maranhão).
3. **`hora_cos` aparece entre as 5 features mais importantes por permutação, mas nem `hora` nem `hora_sin` aparecem no top 15** — evidência de que a transformação cíclica capturou sinal temporal real que a hora bruta não capturava (justifica retroativamente a decisão da Gold de manter a codificação cíclica).
4. **Viés de calibração geográfico e por tipo de pista mensurável e forte** (seção 7) — não detectável olhando só a métrica agregada de teste; só aparece ao segmentar por grupo, reforçando a regra do projeto de nunca declarar ausência de viés sem checar.
5. **`geocoord_valido` (flag de coordenada sentinela) está com variância zero na Gold atual** — um achado novo desta etapa que a Etapa 2 não havia quantificado; não afeta os resultados (a coluna simplesmente foi excluída), mas é uma inconsistência de documentação entre etapas que vale registrar.
6. **A árvore de decisão rasa não superou a Regressão Logística em nenhuma métrica de teste**, apesar de ter mais capacidade de capturar não-linearidade — sinal de que a interação entre features não compensa, neste problema, a variância adicional de uma única árvore.

---

## 9. Limitações

**Da base de dados** (herdadas da Etapa 2, ver `docs/entregas/etapa2-eda.md` §3): inconsistência não resolvida entre `pessoas` e a soma de vítimas em 5,39% dos registros (D-03, não afeta features de ML); ausência de dados de fluxo de veículos e de infraestrutura além do que a PRF registra (spec, seção 25); mudanças de metodologia de coleta não auditáveis entre 2022 e 2026.

**Da metodologia desta etapa:**
- **Nenhuma feature de histórico do trecho foi construída** (contagem de acidentes/graves anteriores por BR/UF/km, sugerida na spec seção 9) — o modelo prevê exclusivamente a partir de características estruturais/temporais do próprio acidente, não do padrão histórico do local. Isso provavelmente limita o teto de ROC-AUC observado (0,63).
- **`municipio` usa frequência de contagem, não taxa de gravidade** — captura "quão movimentado é o município", não "quão perigoso"; um encoding por taxa de gravidade (com suavização/CV para evitar leakage) provavelmente adicionaria sinal, mas não foi implementado nesta iteração (D-17).
- **Limiar de decisão único (0,5) para toda a base** — a causa direta do viés geográfico documentado na seção 7.
- **Tuning restrito a 2 dos 4 modelos candidatos** (custo-benefício, D-19) — não se pode descartar que uma busca mais ampla em Random Forest ou Árvore de Decisão mudasse o ranking, embora o gap de desempenho observado torne isso improvável.

**Do modelo:** ROC-AUC de 0,63 é modesto em termos absolutos — o modelo é significativamente melhor que o acaso, mas está longe de "prever" acidentes com confiança individual; deve ser lido como ferramenta de priorização relativa entre trechos/condições, nunca como previsão determinística (spec, seção 25). Correlação entre feature e gravidade (seções 6/8) não implica causalidade — nenhuma das análises desta etapa permite afirmar que, por exemplo, mudar o tipo de pista de Simples para Dupla necessariamente reduziria acidentes graves; apenas que a associação observada é forte e consistente.

---

## 10. Mudanças e estruturações necessárias para a próxima etapa

1. **Features de histórico do trecho** — agregações de contagem/taxa de acidentes graves por (BR, UF, faixa de km) em janelas anteriores ao período previsto, com corte temporal estrito (spec, seção 9); é a mudança com maior potencial de elevar o teto de ROC-AUC atual.
2. **Calibração de limiar por grupo (UF, no mínimo)** — corrigir estruturalmente o viés de recall documentado na seção 7, em vez de um único limiar global de 0,5.
3. **Target encoding suavizado para `municipio`** (com validação cruzada interna para não vazar o próprio alvo) como alternativa à frequência simples atual — comparar as duas.
4. **Calibração de probabilidade** (ex.: `CalibratedClassifierCV`) antes de qualquer uso operacional das faixas BAIXO/MÉDIO/ALTO — os tercis atuais são relativos à distribuição da validação, não probabilidades calibradas no sentido estatístico.
5. **Granularidade de trecho explícita** — a spec (seção 5) sugere segmentos fixos (5-10km) como unidade de análise alternativa ao acidente individual; esta etapa manteve a unidade "acidente" por simplicidade, mas uma agregação por trecho/período é o que permitiria o mapa de risco do resultado final (spec, seção 18).
6. **SHAP** (não instalado nesta iteração) para explicações por previsão individual, complementando a importância global já calculada.

---

## 11. Conclusão

O modelo final (`xgboost_tuned`) separa acidentes graves do restante de forma consistente e mensuravelmente melhor que o acaso (ROC-AUC 0,63, Recall 56,5% no teste) e melhor que os demais candidatos nas três métricas de decisão, com custo computacional baixo e overfitting moderado e não catastrófico. Ele **não** é um modelo pronto para uso operacional sem ajustes: o viés de recall por UF/tipo de pista é grande o suficiente para produzir alocação desigual de atenção entre estados se usado como está, e o teto de desempenho absoluto reflete a ausência — por design correto de anti-leakage — das features circunstanciais mais informativas sobre gravidade. A hipótese do projeto (spec, seção 23) é **parcialmente confirmada**: características geográficas, temporais e estruturais **têm** sinal preditivo real (ROC-AUC significativamente acima de 0,5, robusto entre 5 algoritmos diferentes), mas esse sinal, sozinho, tem teto moderado — o próximo salto de desempenho depende de features de histórico do trecho, não de um algoritmo mais sofisticado (evidência direta: tuning não moveu a métrica). Próximo passo recomendado: features de histórico do trecho + calibração de limiar por grupo, antes de qualquer uso do modelo para priorização real de recursos.
