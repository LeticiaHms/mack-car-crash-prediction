# Analysis Log — EDA Acidentes PRF (2022–2026)

Segue o formato da skill `analysis-log`. Dataset/versão: `dados/curated/acidentes_2022_2026.parquet`
(311.751 registros, gerado por `src/preprocess.py`). Todos os números vêm de `reports/eda/eda_results.json`,
produzido por `python src/run_eda.py` — nenhum valor foi digitado manualmente sem essa fonte.

---

## A-01 — Estrutura geral do dataset

**Pergunta:** Quantos registros, colunas e qual período o dataset curado cobre?

**Dados:** `acidentes_2022_2026.parquet` completo.

**Método:** `DESCRIBE` + `count(*)` + `min/max(data_inversa)` via DuckDB (`eda_utils.dataset_overview`).

**Resultado:** 311.751 registros, 30 colunas, de 2022-01-01 a 2026-07-31. Registros por ano: 2022=64.606, 2023=67.766, 2024=73.156, 2025=72.529, 2026=33.694 (parcial, jan–jul).

**Interpretação:** A unidade de análise é o **acidente (ocorrência)**, não pessoa nem veículo. 2026 é um ano incompleto na fonte.

**Limitação:** Qualquer comparação que inclua 2026 deve usar janela comparável (jan–jul), nunca o total anual bruto — ver A-08.

**Impacto:** Define a base de todas as demais análises; motivou a decisão [D-12](DECISIONS.md#d-12).

**Evidência:** `reports/eda/eda_results.json → overview`.

---

## A-02 — Qualidade: duplicidade e nulos

**Pergunta:** Existem IDs duplicados ou nulos em colunas críticas?

**Método:** Contagem de IDs distintos vs. total; contagem de nulos por coluna via DuckDB.

**Resultado:** 0 IDs duplicados, 0 linhas 100% duplicadas. Nulos: `classificacao_acidente`=5 (0,0016%), `regional`=3.132 (1,00%), `delegacia`=3.220 (1,03%), `uop`=3.365 (1,08%). Demais 26 colunas sem nulos.

**Interpretação:** Qualidade estrutural alta; a deduplicação de `src/preprocess.py` funcionou corretamente.

**Limitação:** N/A.

**Decisão:** Nenhuma ação de imputação necessária.

**Impacto:** Nenhum bloqueio para EDA/ML por nulos.

**Evidência:** `reports/eda/eda_results.json → duplicates, missing`.

---

## A-03 — `classificacao_acidente` esconde a diferença entre ferido leve e grave

**Pergunta:** A variável de classificação oficial da PRF já distingue bem os níveis de gravidade?

**Método:** Cruzamento de `classificacao_acidente` com `mortos`/`feridos_graves`/`feridos_leves` (SQL `CASE WHEN`).

**Resultado:** Da categoria "Com Vítimas Feridas" (238.746 registros), 173.002 (72,5%) têm só feridos leves e 65.744 (27,5%) têm ao menos um ferido grave. "Sem Vítimas"=50.581 (16,2%); "Com Vítimas Fatais"=22.419 (7,2%); 5 nulos.

**Interpretação:** A categoria oficial de 3 classes não é suficiente para o objetivo do projeto (identificar acidentes graves). É necessário decompor.

**Limitação:** A decomposição usa `mortos`/`feridos_graves`, que já são as próprias colunas de resultado — coerente, mas confirma que essas colunas não podem servir de feature (ver A-14).

**Decisão:** Criar `gravidade_4`/`grave_bin` — ver [D-01](DECISIONS.md#d-01) e [D-02](DECISIONS.md#d-02).

**Impacto:** Variável-alvo revisada para todo o projeto de ML.

**Evidência:** `reports/eda/eda_results.json → target_gravidade_4`.

---

## A-04 — Distribuição da variável-alvo (`gravidade_4` / `grave_bin`)

**Pergunta:** Qual a distribuição de classes do alvo e o grau de desbalanceamento?

**Método:** Contagem/percentual por classe.

**Resultado:** `gravidade_4`: Leve=55,49%, Grave (não fatal)=21,09%, Sem vítimas=16,22%, Fatal=7,19%. `grave_bin`: 0 (sem gravidade)=71,72%, 1 (grave/fatal)=28,28% → razão ~2,5:1.

**Interpretação:** Desbalanceamento **moderado**, não extremo. Ainda assim, a classe positiva (grave) é minoritária o suficiente para que Accuracy seja enganosa.

**Limitação:** A classe "Fatal" isolada (7,19%) é, sim, fortemente minoritária — se o projeto optar por prever fatalidade isoladamente em vez de `grave_bin`, o desbalanceamento é muito mais severo.

**Decisão:** Priorizar Recall/F1/PR-AUC da classe grave, conforme spec e skill `model-evaluation`.

**Impacto:** Orienta a escolha de métrica e estratégia de balanceamento na etapa de ML.

**Evidência:** `reports/eda/eda_results.json → target_gravidade_4, target_grave_bin`.

---

## A-05 — Força de associação entre gravidade e variáveis explicativas (Cramér's V)

**Pergunta:** Quais variáveis categóricas têm associação mais forte com a gravidade?

**Método:** Qui-quadrado + Cramér's V (com correção de viés) para `gravidade_4` × {uf, br, tipo_acidente, causa_acidente, condicao_metereologica, tipo_pista, tracado_via, fase_dia, dia_semana, sentido_via, uso_solo, mes, hora}.

**Resultado:** Todos os testes deram p≈0 (n=311.751 infla significância). Ordenando por Cramér's V: `tipo_acidente`=0,300 (moderado) > `causa_acidente`=0,244 (fraco-moderado) > `br`=0,110 ≈ `uf`=0,105 ≈ `uso_solo`=0,098 ≈ `hora`=0,097 ≈ `tipo_pista`=0,095 > `fase_dia`=0,081 > `sentido_via`=0,050 > `tracado_via`=0,047 > `dia_semana`=0,042 > `condicao_metereologica`=0,034 > `mes`=0,008 (praticamente nula).

**Interpretação:** O **tipo** e a **causa** do acidente são os sinais categóricos mais fortes associados à gravidade — mas ambos só são conhecidos após o acidente ocorrer (ver A-14, leakage). Entre variáveis potencialmente disponíveis a priori, `uf`, `br`, `tipo_pista`, `hora` e `fase_dia` têm associação fraca-mas-real (V≈0,08–0,11). `mes` (sazonalidade) tem associação desprezível com a gravidade — o mês influencia volume, não o "mix" de gravidade (ver A-09/A-10).

**Limitação:** Cramér's V não implica causalidade; e p-valor ≈0 aqui é esperado por n grande, não indica força.

**Decisão:** [D-08](DECISIONS.md#d-08).

**Impacto:** Ranking usado para priorizar candidatos a features estruturais/temporais na próxima etapa (feature engineering), respeitando a restrição de leakage.

**Evidência:** `reports/eda/eda_results.json → chi2_gravidade_vs_explicativas`.

---

## A-06 — Relações entre variáveis numéricas de contagem

**Pergunta:** Existe relação entre número de veículos/pessoas envolvidas e o número de mortos?

**Método:** Correlação de Spearman (variáveis de contagem, não-normais).

**Resultado:** `pessoas`×`veiculos`: ρ=0,704 (forte, esperado). `veiculos`×`mortos`: ρ=0,128. `pessoas`×`mortos`: ρ=0,130. `feridos_graves`×`veiculos`: ρ=0,084. `km`×`mortos`: ρ=0,029 (desprezível). Kruskal-Wallis confirma que `veiculos` e `pessoas` diferem significativamente entre as classes de `gravidade_4` (H=7.371 e H=11.100, p≈0).

**Interpretação:** Mais pessoas/veículos envolvidos tende fracamente a se associar a mais mortes — mas a relação é fraca, não um preditor forte isolado. A posição quilométrica (`km`) não tem relação monotônica com fatalidade (esperado, pois `km` é um índice de localização, não uma medida de risco).

**Limitação:** Contagens de pessoas/veículos do próprio acidente são pós-evento — não usáveis como feature preditiva direta (ver A-14), mas úteis para entender o fenômeno.

**Impacto:** Confirma que gravidade é multifatorial; nenhuma variável numérica isolada domina.

**Evidência:** `reports/eda/eda_results.json → spearman_numeric_pairs, kruskal_*`.

---

## A-07 — Distribuições numéricas fortemente assimétricas

**Pergunta:** Como se distribuem as contagens de vítimas/veículos por acidente?

**Método:** Estatística descritiva completa (média, mediana, moda, quartis, IQR, variância, desvio-padrão, assimetria, curtose).

**Resultado:** Todas as colunas de contagem de vítimas são fortemente assimétricas à direita e leptocúrticas: `mortos` (média=0,08, mediana=0, assimetria=10,75, curtose=560), `feridos_graves` (média=0,28, assimetria=6,37), `pessoas` (média=2,60, mediana=2, assimetria=11,22). `km`: média=259,3, mediana=193,0, assimetria=1,00, curtose=0,36 (leve assimetria à direita, sem cauda extrema).

**Interpretação:** Consistente com o fenômeno: a maioria dos acidentes não tem mortos/feridos graves, mas uma cauda rara concentra eventos catastróficos (ver A-13). `km` reflete apenas a extensão das rodovias analisadas (até 1.470 km), sem anomalia de forma.

**Limitação:** Média é pouco representativa para essas colunas; preferir mediana/percentis na comunicação de resultados.

**Impacto:** Reforça a necessidade de log/transformação ou binning se essas colunas históricas forem usadas como features agregadas (ex.: "quantidade de mortos no trecho no último ano").

**Evidência:** `reports/eda/eda_results.json → numeric_summary`.

---

## A-08 — Tendência de volume: crescimento 2022→2024, estabilização em 2025, e 2026 abaixo do esperado

**Pergunta:** O volume de acidentes mudou ao longo de 2022–2026?

**Método:** Série anual de contagens; comparação adicional restrita a jan–jul para incluir 2026 de forma justa.

**Resultado:** Total anual: 2022=64.606, 2023=67.766, 2024=73.156, 2025=72.529, 2026=33.694 (parcial). Jan–jul apenas: 2022=36.605, 2023=38.543, 2024=41.639, 2025=41.017, 2026=33.694 — ou seja, jan–jul/2026 é ~17,8% menor que jan–jul/2025.

**Interpretação:** Houve crescimento de volume entre 2022 e 2024 (+13,2%), leve recuo em 2025 (-0,86% vs 2024) e uma queda mais visível no recorte jan–jul de 2026. Não é possível concluir se a queda de 2026 é uma tendência real de redução de acidentes ou um artefato de **atraso de consolidação** dos registros mais recentes da PRF (comum em bases abertas de órgãos públicos).

**Limitação:** Sem mais um corte temporal futuro (ex.: dados de 2026 revisados alguns meses depois), a causa da queda de 2026 é **inconclusiva**.

**Decisão:** Tratar a queda de 2026 como sinal a ser monitorado, não como fato consolidado no relatório final.

**Impacto:** Reforça [D-12](DECISIONS.md#d-12); qualquer feature de "tendência recente" (spec §9) deve ter cautela redobrada ao usar os meses mais recentes de 2026.

**Evidência:** `reports/eda/eda_results.json → accidents_by_year, accidents_jan_jul_by_year`.

---

## A-09 — A proporção de acidentes graves é estável ao longo do tempo

**Pergunta:** A proporção de acidentes graves mudou entre 2022 e 2026?

**Método:** `% grave_bin=1` por ano, total e restrito a jan–jul.

**Resultado:** pct_grave por ano (total): 2022=28,49%, 2023=28,35%, 2024=28,19%, 2025=28,25%, 2026=27,98%. Restrito a jan–jul: 28,35% / 28,33% / 28,17% / 28,24% / 27,98%. Variação máxima entre anos: 0,51 p.p.

**Interpretação:** Ao contrário do volume (que mudou, ver A-08), o **mix de gravidade permaneceu essencialmente estável** ao longo dos 4,5 anos — não há evidência de piora nem melhora consistente na proporção de acidentes graves.

**Limitação:** Estabilidade agregada não descarta mudanças compensatórias em subgrupos específicos (ex.: uma UF piorando enquanto outra melhora); não investigado neste log.

**Impacto:** Não há tendência temporal de gravidade que precise ser modelada como "deriva" (drift) forte no alvo; simplifica a estratégia de split temporal da spec (§7).

**Evidência:** `reports/eda/eda_results.json → grave_pct_by_year, grave_pct_by_year_jan_jul`.

---

## A-10 — Sazonalidade de volume comprovada por recorrência entre anos; ausente na gravidade

**Pergunta:** Existe sazonalidade real (não apenas oscilação) no volume de acidentes? Ela afeta a gravidade?

**Método:** Distribuição por mês (agregado); correlação de Spearman do **ranking de meses** entre os 4 anos completos (2022–2025), par a par, para checar recorrência — critério explícito da skill `eda` antes de rotular como sazonalidade.

**Resultado:** Volume por mês (todos os anos): pico em mar–mai (28.545–28.922) e mínimo em set/nov (23.165–23.435); dez volta a subir (25.827). Correlação de Spearman média entre os rankings mensais dos 4 anos completos: **ρ̄=0,845** — forte recorrência do mesmo padrão mês a mês entre anos diferentes. Associação de `mes` com `gravidade_4` (Cramér's V=0,008, A-05): praticamente nula.

**Interpretação:** Há evidência estatística (recorrência ρ̄=0,845, não apenas um gráfico oscilante) de **sazonalidade real no volume** de acidentes ao longo do ano civil. Porém, essa sazonalidade **não se traduz em variação do risco de gravidade** — a proporção de acidentes graves não muda por mês.

**Limitação:** Sazonalidade de volume pode refletir exposição (mais viagens em certos meses), não risco por viagem; sem dado de fluxo de veículos não é possível separar as duas coisas.

**Impacto:** `mes`/estação pode ser útil para prever **quantidade** de acidentes num trecho, mas não para prever se um acidente será grave.

**Evidência:** `reports/eda/eda_results.json → accidents_by_month, month_pattern_spearman_between_years`.

---

## A-11 — Padrões diários e semanais clássicos de tráfego

**Pergunta:** Existem padrões por dia da semana e por hora?

**Método:** Contagem por `dia_semana` e por `hora` (extraída de `horario`); `% grave_bin=1` por grupo.

**Resultado:** Fins de semana concentram mais acidentes (domingo=50.780, sábado=50.474) que dias úteis (terça=38.711 é o mínimo), e têm gravidade um pouco maior (domingo pct_grave=30,37%, sábado=30,02% vs. quarta=26,92%). Por hora: pico de volume às 18h (23.139) e mínimo às 2h–4h (5.210–6.840); porém a **gravidade relativa** é maior à noite (19h=33,88%, 21h=33,13%, 23h=32,49%) e menor de manhã (8h=23,30%, 9h=23,49%).

**Interpretação:** Padrão clássico de tráfego: mais acidentes no horário de pico de deslocamento (17–19h), mas proporcionalmente **mais graves à noite** — coerente com menor visibilidade e maiores velocidades médias em vias com menos tráfego.

**Limitação:** Contagem absoluta por hora reflete exposição (quantos carros trafegam), não só risco.

**Impacto:** `hora`/`fase_dia` e `dia_semana` são candidatos razoáveis a features temporais (associação fraca-mas-real, consistente com A-05).

**Evidência:** `reports/eda/eda_results.json → accidents_by_hour, accidents_by_weekday, severity_rate_by_column['hora'|'dia_semana']`.

---

## A-12 — `fase_dia` (luminosidade): noite e amanhecer mais graves que pleno dia

**Pergunta:** A luminosidade/período do dia está associada à gravidade?

**Método:** `% grave_bin=1` por `fase_dia` (proxy oficial de iluminação — ver [D-11](DECISIONS.md#d-11)).

**Resultado:** Plena Noite=32,57% grave (10,10% fatal); Amanhecer=30,98% (11,10% fatal — a maior taxa de fatalidade entre as 4 fases); Anoitecer=28,82%; Pleno dia=25,29% (a menor).

**Interpretação:** Acidentes em condições de menor luminosidade (noite/amanhecer) são proporcionalmente mais graves e mais fatais que os ocorridos de dia, apesar do volume absoluto ser maior de dia (171.615 registros).

**Limitação:** Não há controle por velocidade da via ou volume de tráfego simultâneo.

**Impacto:** `fase_dia` é um bom candidato a feature estrutural/temporal (disponível a priori pela hora prevista, não depende do resultado do acidente).

**Evidência:** `reports/eda/eda_results.json → severity_rate_by_column['fase_dia']`.

---

## A-13 — Anomalias: eventos catastróficos raros são plausíveis, não erros de dados

**Pergunta:** Os valores extremos de vítimas/veículos são erros de digitação ou eventos reais?

**Método:** Para colunas zero-infladas (`mortos`, `feridos_graves`), IQR degenera (ver [D-06](DECISIONS.md#d-06)); usado z-score (|z|>3). Inspeção manual dos registros mais extremos (`veiculos`, `mortos`, `pessoas`).

**Resultado:** z-score aponta 0,83% dos registros (`mortos`) e 0,85% (`feridos_graves`) como extremos. Os casos mais extremos são identificáveis: (1) BR-116, km 286,5, Teófilo Otoni/MG, 2024-12-21 — 37 mortos, 54 pessoas envolvidas (consistente com o acidente de ônibus amplamente noticiado nesse local/data); (2) BR-277, km 136, Balsa Nova/PR — dois engavetamentos por neblina em datas distintas (2023-09-02, 131 veículos/95 pessoas; 2024-10-10, 26 veículos), no mesmo ponto e mesma causa ("Neblina") — indicando um **ponto crítico recorrente** de neblina, não erro de digitação.

**Interpretação:** Classificados como **eventos reais plausíveis** (categoria 1 da skill `eda`), não removidos.

**Limitação:** Não há como confirmar 100% via apenas os dados tabulares (sem cruzamento com notícia/fonte externa, o que a spec proíbe usar como feature, mas não proíbe como verificação qualitativa de plausibilidade).

**Decisão:** Nenhum outlier extremo foi removido do dataset. Ver também 2026-02-13 (pico coincidente com período de Carnaval) e o agrupamento recorrente de picos diários em dezembro (A-14b abaixo) como reforço de plausibilidade.

**Impacto:** Nenhuma exclusão de linhas por "valor extremo"; a engenharia de features deve tratar esses eventos como caudas legítimas da distribuição (ex.: winsorização apenas se necessário para estabilidade do modelo, nunca remoção).

**Evidência:** `reports/eda/eda_results.json → numeric_anomalies`; inspeção direta via DuckDB (registros `id`=595429, 661121, 633813).

---

## A-14 — Picos diários de acidentes concentram-se em dezembro (recorrente) — evidência de eventos sazonais reais

**Pergunta:** Os dias com volume anormalmente alto de acidentes (outliers na série diária) são aleatórios ou recorrentes?

**Método:** IQR sobre a série diária de contagem de acidentes (todos os anos); limite superior=278,5 acidentes/dia; 42 dias (2,52%) acima do limite.

**Resultado:** Entre os 8 maiores picos diários, 5 caem entre 12 e 23 de dezembro, em três anos diferentes (2023-12-16, 2023-12-23, 2024-12-21, 2024-12-22, 2025-12-12, 2025-12-20) — janela de véspera de festas de fim de ano/deslocamento de retorno ao trabalho. Um pico isolado em 2026-02-13 coincide com a semana de Carnaval. Um pico em 2024-10-20 não tem recorrência aparente em outros anos na mesma data (inconclusivo).

**Interpretação:** A recorrência dos picos na mesma janela de dezembro, em anos diferentes, é evidência de um padrão sazonal real de fim de ano (viagens/tráfego intenso), reforçando A-10.

**Limitação:** O pico de 2024-10-20 permanece sem explicação — classificado como **inconclusivo** (categoria 3 da skill `eda`), não descartado nem explicado.

**Impacto:** Justifica considerar "proximidade de feriados/fim de ano" como possível feature sazonal futura, com evidência empírica (não suposição).

**Evidência:** `reports/eda/eda_results.json → top_spike_days`; `reports/eda/tables/spike_days.csv`.

---

## A-15 — Estado (MA) e algumas rodovias com taxa de gravidade atipicamente alta — hipótese, não conclusão

**Pergunta:** Existem UFs ou rodovias com comportamento de gravidade muito diferente da média?

**Método:** `% grave_bin=1` por `uf`/`br` (mínimo 200 registros para evitar ruído de amostra pequena); z-score sobre a taxa entre grupos.

**Resultado:** UF: **Maranhão (MA)** com pct_grave=46,25% (z=+2,12), muito acima da média das UFs — único outlier nesse corte. BR: `br=0` (placeholder, ver [D-05](DECISIONS.md#d-05)) e BR-448 com taxas baixas (z=-2,81 e -2,41); BR-402, BR-424, BR-405 com taxas altas (~50%, z>2,0), mas com n moderado (263–442 registros).

**Interpretação:** MA destoa de forma consistente (n=5.260, amostra grande o suficiente para ser confiável) — hipótese de fator regional (malha viária, fiscalização, tipo de tráfego) a ser investigada com mais dados/contexto, não uma conclusão causal. As rodovias BR-402/424/405 têm n menor; a taxa alta é real nos dados, mas o **intervalo de confiança é mais largo** — tratar como sinal preliminar, não ranking definitivo.

**Limitação:** Nenhuma variável de exposição (frota, fluxo) está disponível para normalizar a taxa; "gravidade alta" aqui é sobre os acidentes que já ocorreram, não sobre risco por veículo-km.

**Impacto:** Não usar isoladamente para decisões de política pública; registrar como direção de investigação futura (ex.: feature de UF/BR histórica na modelagem, com suavização para BRs de baixo n).

**Evidência:** `reports/eda/eda_results.json → uf_severity_outliers, br_severity_outliers`; `reports/eda/tables/uf_severity_rate.csv`, `br_severity_rate.csv`.

---

## A-16 — Inconsistência interna em `pessoas` (5,4%) e `km=0` (0,48%) são limitações de qualidade, não de análise

**Pergunta:** As colunas usadas nas análises acima são internamente consistentes?

**Método:** Ver `docs/DATA_QUALITY.md` (checks completos).

**Resultado:** 16.817 registros (5,39%) com `pessoas` ≠ soma das categorias de vítimas; 1.496 (0,48%) com `km≤0`; 788 (0,25%) com `br=0` — mesmo conjunto de 788 registros também tem `sentido_via='Não Informado'`, confirmando que é um lote de acidentes com localização/sentido mal preenchidos na fonte, não erro de processamento do pipeline.

**Interpretação:** Limitações herdadas da fonte PRF, não introduzidas pelo pipeline de ingestão (`src/preprocess.py`/`src/verify_data.py` já garantem tipagem e ausência de duplicatas).

**Limitação:** Reduz a confiabilidade de features derivadas de `km`/`br` para ~0,5–0,7% dos registros; não afeta as análises de gravidade × tempo/clima/tipo.

**Decisão:** [D-03](DECISIONS.md#d-03), [D-04](DECISIONS.md#d-04), [D-05](DECISIONS.md#d-05).

**Impacto:** A segmentação por trecho de rodovia (spec §5) deve excluir explicitamente `br=0` e `km≤0` da agregação espacial.

**Evidência:** `docs/DATA_QUALITY.md`; `reports/eda/eda_results.json → consistency_pessoas_vs_vitimas, km_zero_or_negative`.

---

## A-17 — Ausência de campo de "condição da pista" (superfície) na fonte

**Pergunta:** É possível analisar Gravidade × Condição da pista (seca/molhada) como pedido?

**Método:** Inspeção do schema curado (30 colunas) e comparação com o dicionário conceitual da PRF.

**Resultado:** A camada "agrupados por ocorrência" **não contém** uma coluna de condição de superfície da pista. Existem apenas `tipo_pista` (Simples/Dupla/Múltipla — configuração de faixas) e `tracado_via` (Reta/Curva/etc. — geometria).

**Interpretação:** Essa cruz específica pedida na tarefa não pode ser respondida com os dados disponíveis sem inventar uma coluna. Usamos `tipo_pista` como proxy estrutural mais próximo disponível: pistas **Simples** têm pct_grave=33,79% (fatal=9,89%) vs. **Dupla**=23,35% (fatal=4,74%) e **Múltipla**=21,85% (fatal=4,21%) — pistas de mão única/simples são notavelmente mais graves, coerente com risco de colisão frontal.

**Limitação:** Isso é uma limitação de dados, não de análise — deve constar explicitamente no relatório final.

**Impacto:** `tipo_pista` entra como candidato a feature; "condição de superfície" fica registrado como lacuna da fonte.

**Evidência:** `reports/eda/eda_results.json → severity_rate_by_column['tipo_pista']`; `docs/DATA_QUALITY.md §4`.

---

## A-18 — Mapeamento de risco de data leakage por coluna (insumo direto para a Feature Engineering)

**Pergunta:** Quais colunas do dataset curado podem ser usadas como feature preditiva sem vazamento?

**Método:** Para cada coluna, perguntar: "essa informação estaria disponível antes/no momento em que a previsão precisa ser feita para um trecho/período futuro?" (critério da skill `eda`/`feature-engineering`).

**Resultado:**

| Coluna | Disponível a priori? | Veredito |
|---|---|---|
| `mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `pessoas`, `classificacao_acidente` | Não — são o resultado do próprio acidente | **NÃO usar como feature direta** (leakage). Só para construir o target ou agregados históricos de períodos passados. |
| `veiculos` | Não — número de veículos do próprio acidente | **NÃO usar diretamente**; agregável historicamente (ex.: acidentes multi-veículo passados no trecho). |
| `causa_acidente` | Não — apurada após investigação do acidente | **NÃO usar como feature preditiva individual do evento futuro**; útil só para caracterizar o histórico do trecho. |
| `tipo_acidente` | Não — descreve o acidente ocorrido | Mesma restrição de `causa_acidente`. |
| `uf`, `br`, `km`, `municipio`, `latitude`, `longitude` | Sim — atributos do trecho, conhecidos antes de qualquer acidente | **Uso seguro** como feature estrutural/geográfica. |
| `tipo_pista`, `tracado_via`, `sentido_via`, `uso_solo` | Sim — características físicas da via, estáveis no tempo | **Uso seguro** como feature estrutural. |
| `data_inversa`, `horario`, `dia_semana` | Sim, para o período **que está sendo previsto** (ano/mês/dia da semana/hora são conhecidos de antemão) | **Uso seguro** como feature temporal do período-alvo. |
| `fase_dia`, `condicao_metereologica` | Parcial — `fase_dia` é previsível a partir da hora prevista; `condicao_metereologica` **não é conhecida com certeza no futuro** (é uma observação do momento do acidente) | `fase_dia`: uso seguro (derivável de hora/data). `condicao_metereologica`: **NÃO usar como está** (seria preciso previsão de tempo real para uso em produção); pode ser usada apenas para caracterizar o clima histórico típico do trecho/época, não o clima do evento futuro. |
| `regional`, `delegacia`, `uop` | Identificam a unidade da PRF, não o local do acidente | Não recomendado como feature (baixo valor preditivo esperado, redundante com `uf`/`municipio`). |

**Interpretação:** A maior parte das variáveis com **maior associação estatística** com gravidade (`tipo_acidente`, `causa_acidente`, A-05) é justamente a que **não pode** ser usada como feature preditiva direta — reforça a importância de não escolher features só por correlação alta (regra explícita da tarefa).

**Limitação:** A classificação acima é conceitual, baseada na definição do problema (spec §5/§10); a implementação concreta de agregados históricos "sem vazamento" (corte temporal estrito) é responsabilidade da etapa de feature engineering, ainda não implementada.

**Decisão:** [D-07](DECISIONS.md#d-07).

**Impacto:** Este mapeamento é o insumo direto para a próxima etapa (`feature-engineering`), evitando redescobrir o mesmo raciocínio.

**Evidência:** Análise conceitual + `reports/eda/eda_results.json → chi2_gravidade_vs_explicativas` (para saber quais colunas "leakage" têm associação alta, o que reforça por que são tentadoras e por que precisam ser explicitamente vetadas).
