# Mackenzie Car Crash Prediction — AI Skills

Conjunto de skills para desenvolver o projeto de predição de risco de acidentes da PRF
seguindo um fluxo em etapas, reprodutível, sem vazamento de dados (data leakage) e
orientado a evidência.

## Por onde começar

👉 **Use [`_glossario_de_skills.md`](_glossario_de_skills.md) como primeira parada.**
Ele é o índice objetivo de roteamento: para cada tipo de tarefa, mostra qual skill
usar, em qual arquivo, e o resumo das regras-chave — sem precisar abrir todos os
`SKILL.md`. Abra o arquivo completo de uma skill (`skill/<nome>.md`) só quando for
de fato executar aquela etapa.

Este README fica só com a visão geral narrativa; a tabela de roteamento vive no glossário
para não haver duas fontes de verdade divergentes.

## Skills do projeto

`sdd` · `project-orchestrator` · `data-ingestion` · `data-quality` · `duckdb-analytics` ·
`eda` · `feature-engineering` · `machine-learning` · `model-evaluation` ·
`streamlit-ml-eda` (arquivo `streamlit-ml.md`) · `streamlit-dashboard` · `testing` ·
`documentation` · `analysis-log` · `decision-log` · `project-analysis-report` ·
`academic-project`.

## Ordem recomendada

```text
sdd → project-orchestrator → data-ingestion → data-quality → duckdb-analytics → eda
   → feature-engineering → machine-learning → model-evaluation → streamlit-ml-eda
   → testing → documentation → academic-project → project-analysis-report
```

## Fluxo de evidência

```text
Achados de EDA → docs/ANALYSIS_LOG.md → docs/DECISIONS.md → decisões de modelagem → relatório final
```

O relatório final (`project-analysis-report`) deve usar exclusivamente evidência medida e
registrada no projeto — nunca inventar resultado, estatística ou métrica.
