# Glossário de Skills — Índice de Roteamento Rápido

Este arquivo é a **primeira camada de roteamento** para qualquer tarefa de IA no projeto.
Leia só este arquivo primeiro. Abra o `SKILL.md` completo de uma skill (`skill/<nome>.md`)
somente quando a tarefa atual realmente precisar das regras detalhadas dela — isso evita
consumo de tokens carregando skills irrelevantes.

Como usar:
1. Identifique a etapa da tarefa na coluna **Quando usar (gatilhos)**.
2. Abra apenas o(s) `.md` indicado(s) na coluna **Arquivo**.
3. Siga a ordem recomendada abaixo se a tarefa cobrir múltiplas etapas.
4. Toda descoberta relevante → `docs/ANALYSIS_LOG.md`; toda decisão técnica → `docs/DECISIONS.md`.

## Ordem recomendada do pipeline

```text
sdd → project-orchestrator → data-ingestion → data-quality → duckdb-analytics → eda
   → feature-engineering → machine-learning → model-evaluation → streamlit-ml-eda
   → testing → documentation → academic-project → project-analysis-report
```

Fluxo de evidência: **EDA → analysis-log → decision-log → decisões de modelagem → relatório final**.
O relatório final nunca inventa resultado; usa só evidência registrada.

## Tabela de roteamento

| Quando usar (gatilhos) | Skill | Arquivo | Regras-chave (resumo) |
|---|---|---|---|
| Antes de qualquer mudança de escopo/arquitetura; requisito ambíguo | `sdd` | `skill/sdd.md` | Especificar antes de codificar; não expandir escopo silenciosamente. |
| Coordenar múltiplas etapas do pipeline; decidir "o que vem antes do quê" | `project-orchestrator` | `skill/project-orchestrator.md` | Preservar arquitetura existente; nunca pular data-quality; nunca introduzir leakage. |
| Ler CSV bruto da PRF, gerar/atualizar o Parquet curado | `data-ingestion` | `skill/data-ingestion.md` | `encoding='latin-1'`, `sep=';'`; nunca descartar linhas silenciosamente; dados raw imutáveis. |
| Validar schema, nulos, duplicatas, ranges antes de analisar/modelar | `data-quality` | `skill/data-quality.md` | Nunca esconder missingness; nunca imputar sem justificar; distinguir zero real de ausente. |
| Escrever/otimizar SQL de agregação sobre o Parquet | `duckdb-analytics` | `skill/duckdb-analytics.md` | Agregar em SQL, não em pandas puro; evitar `SELECT *`; validar granularidade. |
| Explorar dados: distribuições, padrões, tendências, sazonalidade, anomalias, associações, gravidade | `eda` | `skill/eda.md` | Investigar, não decorar com gráficos; provar sazonalidade com recorrência; nunca afirmar causalidade; checar leakage por feature. |
| Criar/transformar features para o modelo (trecho × período) | `feature-engineering` | `skill/feature-engineering.md` | Pergunta obrigatória por feature: "estaria disponível no momento da previsão?"; fit só no treino. |
| Treinar baseline/modelos candidatos (classificação de gravidade) | `machine-learning` | `skill/machine-learning.md` | Baseline Dummy primeiro; `Pipeline`/`ColumnTransformer`; seed fixa; não otimizar contra o teste. |
| Comparar modelos, escolher métrica, interpretar resultado | `model-evaluation` | `skill/model-evaluation.md` | Precision/Recall/F1/ROC-AUC/PR-AUC da classe grave; nunca só Accuracy. |
| Construir/alterar o app interativo de exploração de dados e ML | `streamlit-ml-eda` (arquivo `streamlit-ml.md`) | `skill/streamlit-ml.md` | UI separada da lógica (`streamlit/` chama `src/`); DuckDB para agregação; nunca retreinar ao mudar filtro. |
| Construir páginas de dashboard mais "de produto" (overview, predição) | `streamlit-dashboard` | `skill/streamlit-dashboard.md` | Complementar à `streamlit-ml-eda`; usar quando o foco é apresentação/predição, não investigação. |
| Escrever testes (unitários, integração, dados, ML) | `testing` | `skill/testing.md` | Falhar alto em violação de schema/leakage; testar reprodutibilidade com seed fixa. |
| Atualizar README/ARQUITETURA/dicionário de dados | `documentation` | `skill/documentation.md` | Linguagem acadêmica ("associado a", nunca "causa"/"prova"); documentação = espelho do código real. |
| Registrar um achado analítico (estatística, teste, padrão) | `analysis-log` | `skill/analysis-log.md` | Formato Pergunta/Dados/Método/Resultado/Interpretação/Limitação/Impacto; nunca inventar resultado. |
| Registrar uma decisão técnica/metodológica com trade-off | `decision-log` | `skill/decision-log.md` | Formato Contexto/Evidência/Decisão/Alternativas/Justificativa/Impacto; nunca "porque é melhor" sem evidência. |
| Montar o relatório acadêmico final do projeto | `project-analysis-report` | `skill/project-analysis-report.md` | Só usa evidência já registrada em analysis-log/decision-log; resultado não calculado = "pendente", nunca inventado. |
| Revisar rigor científico antes de entregar/apresentar | `academic-project` | `skill/academic-project.md` | Checklist problema→hipótese→dados→método→EDA→features→modelo→avaliação→conclusão; associação ≠ causalidade. |

## Skills auxiliares (não fazem parte do pipeline principal)

| Arquivo | Observação |
|---|---|
| `skill/sdd_skill.md` | Versão longa/legada da skill `sdd`. Preferir `skill/sdd.md` (resumida); só abrir a versão longa se `sdd.md` não cobrir o caso. |
| `skill/README.md` | Descrição narrativa do conjunto de skills. Este glossário é a referência de roteamento; o README é o texto de apresentação. |

## Regra geral

Se a tarefa não exige detalhe metodológico de uma skill (ex.: só precisa saber "qual arquivo existe"), a linha da tabela acima já é suficiente — **não abra o `SKILL.md` completo**. Abra o arquivo completo apenas quando for de fato implementar/validar aquela etapa.
