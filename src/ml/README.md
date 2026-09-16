# `src/ml/` — Modelagem Preditiva (Etapa 3)

Implementação simples e didática da etapa de Aprendizado de Máquina Preditivo do projeto. Tudo vive em um único arquivo, propositalmente: [`modelagem.py`](modelagem.py).

## O problema

Classificação binária supervisionada: prever `grave_bin` (1 = acidente grave/fatal, 0 = não grave) a partir de características do acidente e da rodovia conhecidas **antes** do desfecho — nunca a partir de informação que só existe depois (número de feridos/mortos, tipo/causa do acidente etc.), que já foi removida na camada Gold (`src/gold/dataset_ml.py`).

## Como rodar

Pré-requisito: `gold.dataset_ml` já materializada em `data/prf.duckdb` (ver `src/jobs/build_database.py`).

```bash
python -m src.ml.modelagem
```

O script imprime, em ordem, cada uma das 9 etapas (carga → features → split → treino → gráficos → métricas → interpretabilidade → resumo final) e grava os artefatos abaixo em `reports/ml/`:

```text
reports/ml/
├── metrics.csv               # tabela comparativa (Accuracy, Precision, Recall, F1, ROC-AUC)
├── class_distribution.png    # distribuição da variável alvo (grave_bin)
├── confusion_matrix.png      # matriz de confusão dos 3 modelos (teste)
├── roc_curve.png             # curva ROC comparando os 3 modelos (teste)
└── metric_comparison.png     # gráfico de barras comparando as 5 métricas
```

## O que o script faz

1. Carrega `gold.dataset_ml` via DuckDB (somente leitura).
2. Seleciona 29 features (7 categóricas + 7 numéricas + 15 booleanas) e separa `X`/`y`.
3. Divide treino/validação/teste por **corte de data** (~70%/15%/15%, sem embaralhar) — o corte é sempre no limite de um dia, nunca no meio dele. Sem tuning nesta etapa, a validação só serve como checagem intermediária de generalização; a avaliação final usa exclusivamente o teste.
4. Treina 3 modelos de classificação (Regressão Logística, Árvore de Decisão, Random Forest), cada um dentro de um `Pipeline` com um `ColumnTransformer` ajustado apenas no treino.
5. Calcula Accuracy, Precision, Recall, F1 e ROC-AUC de cada modelo sobre o teste.
6. Gera os 4 gráficos acima.
7. Imprime a importância das features (nativa para as árvores, coeficientes para a Regressão Logística) e um resumo final com os números-chave.

## Por que só 3 algoritmos, e por que esses

Da lista de algoritmos permitida (Regressão Linear, Regressão Logística, Árvore de Decisão, Random Forest, KNN, SVM, K-Means, Redes Neurais), Regressão Linear e K-Means ficam de fora por não servirem a um problema de classificação binária. Entre os demais, escolhemos:

- **Regressão Logística** — modelo linear de referência, rápido e interpretável via coeficientes.
- **Árvore de Decisão** — captura relações não-lineares sem transformação manual das features; caminho de decisão auditável.
- **Random Forest** — ensemble de árvores (bagging), tende a reduzir a variância/overfitting de uma árvore única.

KNN e SVM foram deixados de fora por razão prática: com ~218 mil registros de treino e ~29 features (que viram ~190 colunas após one-hot), ambos ficam computacionalmente caros (KNN precisa calcular distância para todo o treino a cada previsão; SVM não escala bem além de dezenas de milhares de linhas) sem indício de que superariam os três modelos escolhidos neste problema. Redes Neurais foram deixadas de fora por exigirem mais tuning/dados para justificar a complexidade extra num experimento que já usa configurações simples e padrão do scikit-learn.

## O que este arquivo deliberadamente NÃO faz

Busca extensa de hiperparâmetros, XGBoost/LightGBM, SHAP, permutation importance, calibração de probabilidade, análise de viés por subgrupo, sistema de risco BAIXO/MÉDIO/ALTO, API de inferência, ou qualquer artefato de "produção". Isso é um experimento acadêmico simples e reproduzível, não uma arquitetura de ML profissional — ver `docs/entregas/etapa3-modelagem.md` para a documentação completa dos resultados e conclusões.
