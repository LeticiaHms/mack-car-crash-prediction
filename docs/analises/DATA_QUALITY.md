# Relatório de Qualidade de Dados — Acidentes PRF (2022–2026)

> Gerado a partir de `dados/curated/acidentes_2022_2026.parquet` pelo script `src/run_eda.py`
> (artefato bruto: `reports/eda/eda_results.json`). Segue a skill `data-quality`.
> Fonte primária: CSVs oficiais "Acidentes — Agrupados por ocorrência" da PRF
> (https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf),
> anos 2022–2026, processados por `src/preprocess.py`.

## 1. Visão geral do dataset

| Item | Valor |
|---|---|
| Registros (acidentes) | 311.751 |
| Colunas | 30 |
| Período coberto | 2022-01-01 a 2026-07-31 |
| Unidade de análise | 1 linha = 1 acidente (ocorrência), não pessoa/veículo |
| Anos completos | 2022, 2023, 2024, 2025 |
| Ano parcial | **2026 — apenas jan/jul (7 meses)**, os demais meses ainda não existem na fonte |

Registros por ano: 2022=64.606, 2023=67.766, 2024=73.156, 2025=72.529, 2026=33.694 (parcial).

## 2. Checks executados

| Check | Resultado | Severidade | Linhas afetadas | Tratamento / Decisão |
|---|---|---|---|---|
| Duplicidade de `id` | 0 IDs duplicados; 0 linhas 100% duplicadas | OK | 0 (0%) | Nenhuma ação necessária. `src/pipeline.py` (módulo `preprocessing.acidentes`) já deduplica por `id`. |
| Nulos em colunas críticas (`id`, `data_inversa`, `latitude`, `longitude`, `km`) | 0 nulos | OK | 0 (0%) | Validado também em `src/verify_data.py`. |
| Nulos em `classificacao_acidente` | 0 nulos | OK | 0 (0%) | Os 5 nulos observados antes da modularização de `src/pipeline.py` não existem mais na camada curada atual. |
| Nulos em `regional` / `delegacia` / `uop` | 3.132 / 3.220 / 3.365 nulos | Baixa | ~1,0–1,1% | Não são usados como features preditivas (identificam a unidade da PRF, não o local do acidente); ausência não bloqueia a EDA. |
| Consistência `pessoas == mortos+feridos_leves+feridos_graves+ilesos+ignorados` | 16.817 divergências | **Média** | 5,39% | **Não corrigido automaticamente.** Ver Decisão [D-03](DECISIONS.md#d-03). Mantido como limitação documentada; `pessoas` não deve ser tratado como soma exata das demais colunas. |
| Consistência `feridos == feridos_leves+feridos_graves` | 0 divergências | OK | 0% | Campo derivado internamente consistente na base. |
| Coerência `dia_semana` × `data_inversa` | 0 divergências | OK | 0% | O rótulo textual bate com a data em 100% das linhas. |
| `horario` convertível para `TIME` | 0 inválidos | OK | 0% | Permite derivar `hora` e `fase_dia` sem perda. |
| Cobertura do calendário (dias sem nenhum registro) | 8 dias ausentes de 1.673 esperados | **Média** | 0,48% dos dias | Todos entre 2026-07-01 e 2026-07-14: sintoma da janela não consolidada. Ver [A-19](ANALYSIS_LOG.md#a-19--a-queda-de-volume-no-fim-da-série-é-falta-de-consolidação-da-fonte-não-redução-de-acidentes) e [D-13](DECISIONS.md#d-13). |
| Janela final não consolidada | 38 dias (após 2026-06-23) com 492 registros vs. mediana de 188/dia | **Alta** (para análise temporal) | 0,16% das linhas | Não removido da base; truncado nas análises de tendência via corte automático ([D-13](DECISIONS.md#d-13)). |
| Valores-sentinela `condicao_metereologica = 'Ignorado'` | 4.108 registros | Baixa | 1,32% | Categoria de "não informado" disfarçada de valor válido; não deve virar uma categoria própria em one-hot sem ressalva. |
| `sentido_via = 'Não Informado'` | 788 registros | Baixa | 0,25% | Mesmo lote de registros com `br=0`. |
| `tracado_via` multivalorada (contém `;`) | 70.204 registros | Informativo | 22,52% | Característica da fonte, não erro: 12 primitivas reais combinadas em uma string. Exige **multi-hot**, não one-hot. Ver [A-22](ANALYSIS_LOG.md#a-22--valores-sentinela-e-campo-multivalorado-o-que-não-aparece-em-uma-contagem-de-nulos). |
| `km <= 0` | 1.496 registros com km=0 | Baixa/Média | 0,48% | Tratado como possível valor "não informado" (placeholder), não removido. Ver [D-04](DECISIONS.md#d-04). |
| `veiculos == 0` / `pessoas == 0` | 0 ocorrências | OK | 0% | Nenhum acidente sem pessoas ou veículos envolvidos — consistente com o esperado. |
| UFs fora do conjunto de 27 unidades federativas | 0 inválidas | OK | 0% | Validado em `src/verify_data.py`. |
| Coordenadas fora da bounding box do Brasil | 0 fora do intervalo | OK | 0% | Validado em `src/verify_data.py` (lat ∈ [-35,6], lon ∈ [-75,-30]). |
| `br == 0` (rodovia inexistente) | 788 registros | Baixa | 0,25% | Tratado como placeholder de rodovia não identificada; excluído de rankings por rodovia (ver [D-05](DECISIONS.md#d-05)). |
| Cardinalidade de categóricas | `uf`=27, `br`=125, `municipio`=2.057, `causa_acidente`=77, `tipo_acidente`=17, `classificacao_acidente`=3 | OK | — | Cardinalidade compatível com uso em modelos (one-hot/target encoding viável para `causa_acidente`/`tipo_acidente`; `municipio` exige agrupamento/redução se usado). |
| Contagem de vítimas/veículos — outliers extremos | Ver `reports/eda/eda_results.json → numeric_anomalies` | Informativo | 0,57%–1,27% (z-score \|z\|>3) | Inspecionados manualmente (§ Anomalias do EDA.md); eventos plausíveis (multi-vítimas reais), não removidos. |

## 3. Observação metodológica sobre o método de detecção de outliers

Para `mortos` e `feridos_graves`, a mediana e o Q1/Q3 são 0 (variáveis de contagem raras e zero-infladas). Isso torna o **IQR degenerado**: qualquer valor > 0 é sinalizado como outlier (7,19% para `mortos`, 22,65% para `feridos_graves`), o que **não é informativo** para essas colunas. Para essas variáveis, o **z-score (|z|>3)** é o método adequado e foi usado como critério primário de anomalia (0,83% e 0,85%, respectivamente). Isso é registrado como decisão metodológica explícita — ver [D-06](DECISIONS.md#d-06).

## 4. Limitações de qualidade herdadas da fonte (não corrigíveis via engenharia)

- **Subnotificação/():** dados são o que a PRF registrou; acidentes não flagrados por unidades da PRF (rodovias estaduais/municipais, ou não notificados) não aparecem.
- **`classificacao_acidente` não distingue gravidade de ferimento:** a categoria "Com Vítimas Feridas" mistura ferimentos leves e graves (ver EDA §3). Por isso foi criada uma variável derivada mais granular (`gravidade_4`) — ver [D-01](DECISIONS.md#d-01).
- **Ausência de campo de condição de superfície da pista** (seca/molhada/em obras): o layer "agrupados por ocorrência" da PRF não traz esse atributo; apenas `tipo_pista` (configuração de faixas) e `tracado_via` (geometria) estão disponíveis. Registrado como limitação para o relatório final.
- **Ausência de dado de volume de tráfego/frota:** contagens absolutas por UF/BR refletem exposição (quanto se trafega ali), não necessariamente risco por veículo-km. Qualquer ranking de "rodovia mais perigosa" baseado em contagem bruta deve ser lido como associação observacional, não como taxa de risco real.
- **2026 incompleto:** qualquer comparação ano a ano deve usar a janela comparável jan–jul (ver EDA.md §5), nunca o total anual bruto de 2026.

## 5. Critério de aceite (skill `data-quality`)

Nenhum problema crítico de qualidade permanece sem explicação. Os itens de severidade "Média" (mismatch de `pessoas`, `km<=0`, `br==0`) estão documentados, não foram corrigidos silenciosamente, e têm decisões associadas no [DECISIONS.md](DECISIONS.md). A modelagem pode prosseguir com essas limitações declaradas.
