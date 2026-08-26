# Análise Exploratória de Dados (EDA) — Acidentes PRF (2022–2026)

> Documento narrativo da EDA, exigido pela skill `eda`. Todos os números citados aqui têm
> evidência detalhada em [ANALYSIS_LOG.md](ANALYSIS_LOG.md) (achados A-01…A-18) e nas decisões
> técnicas derivadas em [DECISIONS.md](DECISIONS.md). Os números brutos e reproduzíveis estão em
> `reports/eda/eda_results.json`, gerado por `python src/run_eda.py`. Qualidade de dados detalhada
> em [DATA_QUALITY.md](DATA_QUALITY.md). Exploração interativa em `streamlit/app.py`.

## 0. Fonte, escopo e reprodutibilidade

- **Fonte:** CSVs oficiais "Acidentes — Agrupados por ocorrência" da PRF (dados abertos), anos 2022–2026.
- **Pipeline:** `dados/datatran*.csv` → `src/preprocess.py` (limpeza/tipagem/deduplicação) → `dados/curated/acidentes_2022_2026.parquet` → `src/verify_data.py` (validação de schema) → `src/eda_utils.py` + `src/run_eda.py` (esta EDA) → `streamlit/app.py` (exploração interativa).
- **Escopo:** 311.751 acidentes, 30 colunas, 2022-01-01 a 2026-07-31 (2026 parcial, só jan–jul). Unidade de análise: **1 linha = 1 acidente**, não pessoa/veículo individual.
- Reproduzir: `python src/run_eda.py` regenera `reports/eda/eda_results.json` e as tabelas em `reports/eda/tables/`.

## 1. Estrutura e qualidade dos dados

Ver [A-01](ANALYSIS_LOG.md#a-01--estrutura-geral-do-dataset) e [A-02](ANALYSIS_LOG.md#a-02--qualidade-duplicidade-e-nulos), e o relatório completo [DATA_QUALITY.md](DATA_QUALITY.md).

Resumo: sem duplicatas de `id`; nulos residuais (<1,1%) apenas em `classificacao_acidente`/`regional`/`delegacia`/`uop`; 5,39% de inconsistência interna entre `pessoas` e a soma das categorias de vítimas (não corrigida, documentada); 0,48% de `km≤0` (placeholder de "não informado"); 0,25% de `br=0` (rodovia não identificada, mesmo lote de registros com `sentido_via='Não Informado'`). Nenhum problema de qualidade crítico bloqueia a EDA ou a modelagem, desde que as limitações acima sejam respeitadas nas features.

## 2. Estatística descritiva

- **Numéricas** (contagens de vítimas/veículos): fortemente assimétricas à direita, zero-infladas, curtose muito alta (ex.: `mortos` assimetria=10,75, curtose=560) — mediana=0 na maioria, cauda rara de eventos catastróficos. `km`: distribuição mais suave (assimetria=1,00, curtose=0,36), 0 a 1.470. Detalhe completo: [A-07](ANALYSIS_LOG.md#a-07--distribuições-numéricas-fortemente-assimétricas).
- **Categóricas:** `uf` (27), `br` (125), `municipio` (2.057), `causa_acidente` (77), `tipo_acidente` (17), `classificacao_acidente` (3+nulo). Frequências completas em `reports/eda/tables/freq_*.csv`.

## 3. Variável-alvo (gravidade)

A classificação oficial de 3 classes mistura ferido leve e grave dentro de "Com Vítimas Feridas" ([A-03](ANALYSIS_LOG.md#a-03--classificacao_acidente-esconde-a-diferença-entre-ferido-leve-e-grave)). Por isso foi criada:

- `gravidade_4` = {Sem vítimas 16,22%, Leve 55,49%, Grave não fatal 21,09%, Fatal 7,19%}
- `grave_bin` = 1 se `mortos>0` ou `feridos_graves>0`, senão 0 → **28,28% grave vs. 71,72% não-grave** (desbalanceamento moderado, ~2,5:1).

Detalhe e decisão: [A-04](ANALYSIS_LOG.md#a-04--distribuição-da-variável-alvo-gravidade_4--grave_bin), [D-01](DECISIONS.md#d-01), [D-02](DECISIONS.md#d-02).

## 4. Padrões e associações com a gravidade

Força de associação (Cramér's V, corrigido por viés) entre `gravidade_4` e variáveis categóricas, da mais forte para a mais fraca:

| Variável | Cramér's V | Observação |
|---|---|---|
| `tipo_acidente` | 0,300 | Mais forte; porém pós-evento (leakage) |
| `causa_acidente` | 0,244 | Forte; porém pós-evento (leakage) |
| `br` | 0,110 | Disponível a priori |
| `uf` | 0,105 | Disponível a priori |
| `uso_solo` | 0,098 | Disponível a priori |
| `hora` | 0,097 | Disponível a priori |
| `tipo_pista` | 0,095 | Disponível a priori |
| `fase_dia` | 0,081 | Disponível a priori (proxy de iluminação) |
| `sentido_via` | 0,050 | Disponível a priori |
| `tracado_via` | 0,047 | Disponível a priori |
| `dia_semana` | 0,042 | Disponível a priori |
| `condicao_metereologica` | 0,034 | Observada no momento; não previsível em produção |
| `mes` | 0,008 | Praticamente nula — sazonalidade afeta volume, não gravidade |

Todas as associações são estatisticamente significantes (p≈0) apenas porque n=311.751 é grande — o Cramér's V, não o p-valor, é o que orienta a priorização ([D-08](DECISIONS.md#d-08), [A-05](ANALYSIS_LOG.md#a-05--força-de-associação-entre-gravidade-e-variáveis-explicativas-cramérs-v)).

Achados específicos por cruzamento (números completos no Analysis Log e no Streamlit):
- **Gravidade × Tipo de pista**: pista Simples 33,79% grave vs. Dupla 23,35% vs. Múltipla 21,85% ([A-17](ANALYSIS_LOG.md#a-17--ausência-de-campo-de-condição-da-pista-superfície-na-fonte)).
- **Gravidade × Fase do dia (proxy de iluminação)**: Plena Noite 32,57% grave vs. Pleno dia 25,29% ([A-12](ANALYSIS_LOG.md#a-12--fase_dia-luminosidade-noite-e-amanhecer-mais-graves-que-pleno-dia)).
- **Gravidade × Hora**: pico de volume às 18h, mas pico de gravidade relativa à noite (19–23h, ~32–34%) ([A-11](ANALYSIS_LOG.md#a-11--padrões-diários-e-semanais-clássicos-de-tráfego)).
- **Gravidade × Dia da semana**: fins de semana mais graves (domingo 30,37%) que meio de semana (quarta 26,92%) ([A-11](ANALYSIS_LOG.md#a-11--padrões-diários-e-semanais-clássicos-de-tráfego)).
- **Gravidade × UF**: Maranhão (MA) destoa com 46,25% grave, outlier estatístico (z=+2,12) ([A-15](ANALYSIS_LOG.md#a-15--estado-ma-e-algumas-rodovias-com-taxa-de-gravidade-atipicamente-alta--hipótese-não-conclusão)).
- **Gravidade × Condição meteorológica**: associação fraca (V=0,034); nevoeiro/neblina levemente mais grave (32,09%) que garoa (22,69%).

**Correlação/associação ≠ causalidade** — todos os achados acima são leituras observacionais.

## 5. Tendências temporais

- **Volume:** crescimento 2022→2024 (+13,2%), estabilização/leve recuo em 2025, e queda de ~17,8% em jan–jul/2026 vs. mesmo período de 2025 — causa inconclusiva (crescimento real de segurança viária vs. atraso de consolidação de dados recentes). Ver [A-08](ANALYSIS_LOG.md#a-08--tendência-de-volume-crescimento-20222024-estabilização-em-2025-e-2026-abaixo-do-esperado).
- **Gravidade:** a proporção de acidentes graves permaneceu estável (27,98%–28,49%) em todos os anos — **não há evidência de piora nem melhora da gravidade relativa ao longo do tempo**. Ver [A-09](ANALYSIS_LOG.md#a-09--a-proporção-de-acidentes-graves-é-estável-ao-longo-do-tempo).
- **Padrão diário/semanal:** pico de volume 17–19h e fins de semana; menor volume de madrugada e meio de semana ([A-11](ANALYSIS_LOG.md#a-11--padrões-diários-e-semanais-clássicos-de-tráfego)).

## 6. Sazonalidade

Evidência de recorrência (não apenas oscilação pontual) confirmada por correlação de Spearman entre os rankings mensais dos 4 anos completos (ρ̄=0,845): pico em mar–mai, vale em set–nov, alta novamente em dez. Essa sazonalidade é de **volume**, não de gravidade (`mes` tem Cramér's V=0,008 com `gravidade_4`). Ver [A-10](ANALYSIS_LOG.md#a-10--sazonalidade-de-volume-comprovada-por-recorrência-entre-anos-ausente-na-gravidade).

Picos diários de acidentes concentram-se recorrentemente em dezembro (3 anos diferentes) e coincidem com Carnaval em 2026 — reforça a leitura de sazonalidade real ligada a feriados/deslocamentos de fim de ano. Ver [A-14](ANALYSIS_LOG.md#a-14--picos-diários-de-acidentes-concentram-se-em-dezembro-recorrente--evidência-de-eventos-sazonais-reais).

## 7. Anomalias

| Anomalia | Classificação | Evidência |
|---|---|---|
| Eventos com dezenas de mortos/veículos (ex.: BR-116 Teófilo Otoni/MG 2024-12-21, 37 mortos; BR-277 Balsa Nova/PR, 2 pile-ups por neblina em anos diferentes) | **Evento real plausível** | [A-13](ANALYSIS_LOG.md#a-13--anomalias-eventos-catastróficos-raros-são-plausíveis-não-erros-de-dados) |
| Picos diários recorrentes em dezembro | **Evento sazonal real** | [A-14](ANALYSIS_LOG.md#a-14--picos-diários-de-acidentes-concentram-se-em-dezembro-recorrente--evidência-de-eventos-sazonais-reais) |
| Pico isolado em 2024-10-20 | **Inconclusivo** (sem recorrência) | [A-14](ANALYSIS_LOG.md#a-14--picos-diários-de-acidentes-concentram-se-em-dezembro-recorrente--evidência-de-eventos-sazonais-reais) |
| MA com pct_grave muito acima da média | **Hipótese a investigar** (n grande, mas sem controle de exposição) | [A-15](ANALYSIS_LOG.md#a-15--estado-ma-e-algumas-rodovias-com-taxa-de-gravidade-atipicamente-alta--hipótese-não-conclusão) |
| BR-402/424/405 com pct_grave ~50% | **Sinal preliminar, n moderado** | [A-15](ANALYSIS_LOG.md#a-15--estado-ma-e-algumas-rodovias-com-taxa-de-gravidade-atipicamente-alta--hipótese-não-conclusão) |
| `br=0` / `sentido_via='Não Informado'` (mesmo lote, 788 registros) | **Problema de qualidade de dados** (placeholder) | [A-16](ANALYSIS_LOG.md#a-16--inconsistência-interna-em-pessoas-54-e-km0-048-são-limitações-de-qualidade-não-de-análise) |
| `km≤0` (1.496 registros) | **Problema de qualidade de dados** (placeholder) | [A-16](ANALYSIS_LOG.md#a-16--inconsistência-interna-em-pessoas-54-e-km0-048-são-limitações-de-qualidade-não-de-análise) |
| `pessoas` ≠ soma de vítimas (5,39%) | **Problema de qualidade de dados** | [A-16](ANALYSIS_LOG.md#a-16--inconsistência-interna-em-pessoas-54-e-km0-048-são-limitações-de-qualidade-não-de-análise) |
| Queda de volume em jan–jul/2026 | **Inconclusivo** (real vs. atraso de consolidação) | [A-08](ANALYSIS_LOG.md#a-08--tendência-de-volume-crescimento-20222024-estabilização-em-2025-e-2026-abaixo-do-esperado) |

Nenhuma anomalia foi removida do dataset automaticamente (regra da skill `eda`).

## 8. Implicações para Machine Learning

- **Target recomendado:** `grave_bin` (binário, ~28% positivo) para a primeira versão do modelo; `gravidade_4` disponível para uma versão multiclasse futura. [D-02](DECISIONS.md#d-02)
- **Features estruturalmente seguras (sem leakage):** `uf`, `br`, `km`, `municipio`, `latitude`, `longitude`, `tipo_pista`, `tracado_via`, `sentido_via`, `uso_solo`, e as temporais do período previsto (`ano`, `mes`, `dia_semana`, `hora`, `fase_dia`).
- **Features proibidas como valor do próprio evento (leakage):** `mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `pessoas`, `veiculos`, `classificacao_acidente`, `tipo_acidente`, `causa_acidente`, `condicao_metereologica` (esta última por não ser conhecida com certeza no futuro). Mapeamento completo: [A-18](ANALYSIS_LOG.md#a-18--mapeamento-de-risco-de-data-leakage-por-coluna-insumo-direto-para-a-feature-engineering). Decisão: [D-07](DECISIONS.md#d-07).
- **Alerta importante:** as variáveis com maior associação estatística com gravidade (`tipo_acidente`, `causa_acidente`) são exatamente as que não podem virar feature direta — reforça que correlação alta ≠ elegibilidade como feature.
- **Uso histórico permitido:** todas as colunas "proibidas" acima podem alimentar agregados de janelas passadas por trecho/período (ex.: "% de acidentes graves no trecho nos últimos 12 meses"), desde que com corte temporal estrito antes do período previsto — implementação a cargo da etapa `feature-engineering` (ainda não executada neste ciclo).
- **Desbalanceamento:** moderado (2,5:1) — recall/F1/PR-AUC da classe grave devem ser priorizados na avaliação, não accuracy (spec §15, skill `model-evaluation`).

## 9. Limitações gerais da EDA

- Dataset não tem informação de fluxo de veículos/frota — contagens absolutas por UF/BR/hora refletem exposição, não necessariamente risco por viagem.
- Não há campo de condição de superfície da pista (seca/molhada) nesta camada de dados da PRF ([A-17](ANALYSIS_LOG.md#a-17--ausência-de-campo-de-condição-da-pista-superfície-na-fonte)).
- 2026 é um ano parcial (jan–jul); conclusões sobre 2026 são preliminares.
- Associações relatadas são observacionais; nenhuma causalidade é afirmada.

## 10. Próximos passos

1. Feature engineering por trecho/período (spec §5/§9), respeitando o mapeamento de leakage do §8.
2. Definição final do split temporal treino/validação/teste (spec §7) — a estabilidade da gravidade ao longo do tempo (§5) simplifica essa escolha.
3. Treinamento de baseline + modelos candidatos (skill `machine-learning`), com avaliação orientada a recall/F1/PR-AUC da classe grave.
