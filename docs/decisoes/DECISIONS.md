# Log de Decisões — Projeto de Predição de Risco de Acidentes PRF

Segue o formato da skill `decision-log`: Contexto, Evidência, Decisão, Alternativas, Justificativa, Impacto.
Todas as decisões abaixo nasceram de achados registrados em [ANALYSIS_LOG.md](ANALYSIS_LOG.md) e nos artefatos em `reports/eda/`.

---

## D-01: Criar uma variável de gravidade derivada (`gravidade_4`) além de `classificacao_acidente`

- **Contexto:** `classificacao_acidente` só tem 3 categorias (Sem Vítimas / Com Vítimas Feridas / Com Vítimas Fatais).
- **Evidência:** Dentro de "Com Vítimas Feridas" (238.746 registros), 173.002 (72,5%) têm apenas feridos leves e 65.744 (27,5%) têm feridos graves — ou seja, a categoria mistura dois níveis de gravidade bem diferentes (ver `reports/eda/eda_results.json`, achado A-03).
- **Decisão:** Criar `gravidade_4` = {Sem vítimas, Leve, Grave (não fatal), Fatal}, derivada de `mortos`/`feridos_graves`/`feridos_leves`, e usá-la como variável de análise principal na EDA (em vez de `classificacao_acidente` bruta).
- **Alternativas consideradas:** (a) usar `classificacao_acidente` como está — rejeitada por esconder o grupo de feridos graves; (b) usar contagem de mortos/feridos como alvo de regressão — mantida como possibilidade futura, não descartada.
- **Justificativa:** Sem essa distinção, feridos graves ficariam estatisticamente "escondidos" dentro do grupo majoritário de feridos leves, prejudicando a etapa de ML (definição de "acidente grave" da spec, seção 6).
- **Impacto:** Toda a EDA de associação (`chi2_gravidade_vs_explicativas`) e o Streamlit usam `gravidade_4`/`grave_bin`, não apenas `classificacao_acidente`.

## D-02: Definir `grave_bin` (fatal OU ferido grave) como candidato a target binário

- **Contexto:** A spec (seção 6 e 8) pede uma definição objetiva de "acidente grave" e permite classificação binária, multiclasse ou regressão.
- **Evidência:** `grave_bin=1` (mortos>0 ou feridos_graves>0) representa 88.167 registros (28,28%) vs. 223.584 (71,72%) sem gravidade — desbalanceamento moderado (~2,5:1), não extremo.
- **Decisão:** Adotar `grave_bin` como definição de trabalho para a etapa de Machine Learning (classificação binária), mantendo `gravidade_4` disponível para uma eventual versão multiclasse.
- **Alternativas consideradas:** (a) usar somente `mortos>0` (fatal) como target — rejeitada por deixar o evento positivo raríssimo (7,19%) e por descartar informação relevante de feridos graves; (b) regressão sobre contagem de vítimas graves — mantida como trabalho futuro.
- **Justificativa:** Combina "vítima fatal" e "ferido grave" porque ambos representam desfechos que órgãos de segurança viária querem prevenir, e o desbalanceamento resultante (2,5:1) é tratável sem técnicas agressivas de resampling.
- **Impacto:** Métricas de avaliação (skill `model-evaluation`) devem priorizar Recall/F1/PR-AUC da classe `grave_bin=1`, não Accuracy.

## D-03: Não corrigir automaticamente a divergência `pessoas` vs. soma das categorias de vítimas

- **Contexto:** Checagem de consistência interna do dataset curado.
- **Evidência:** 16.817 registros (5,39%) têm `pessoas != mortos+feridos_leves+feridos_graves+ilesos+ignorados`.
- **Decisão:** Manter os valores como estão na fonte; não imputar nem recalcular `pessoas`. Documentar a divergência como limitação de qualidade (`DATA_QUALITY.md`).
- **Alternativas consideradas:** (a) recalcular `pessoas` a partir da soma das categorias — rejeitada por não sabermos qual dos dois campos está errado na fonte PRF; (b) descartar as 16.817 linhas — rejeitada por eliminar 5,4% dos dados sem certeza de que o erro invalida o restante do registro (gravidade/local/data continuam confiáveis).
- **Justificativa:** Regra do projeto (`data-quality`): nunca imputar sem justificar, e preservar evidência para o relatório final.
- **Impacto:** `pessoas` não deve ser usada como se fosse sempre a soma exata das demais colunas em features futuras; preferir usar as colunas de vítimas diretamente.

## D-04: Tratar `km <= 0` como valor "não informado", sem remover ou imputar

- **Contexto:** 1.496 registros (0,48%) têm `km = 0`; nenhum valor negativo foi encontrado.
- **Evidência:** `km=0` é implausível como posição real em rodovias de centenas de quilômetros; é consistente com um placeholder de campo não preenchido pela PRF.
- **Decisão:** Manter os registros no dataset (o acidente em si é válido), mas sinalizar `km<=0` como "localização quilométrica desconhecida" nas análises que dependem de `km` (ex.: segmentação de trechos na feature engineering).
- **Alternativas consideradas:** (a) remover as linhas — rejeitada, perderia informação de gravidade/temporal válida; (b) imputar pela mediana da rodovia — rejeitada nesta fase por poder introduzir viés de localização na futura segmentação por trecho.
- **Justificativa:** Regra "nunca remover anomalia sem justificativa" (skill `eda`) e "distinguir true zero, missing, unknown" (skill `data-quality`).
- **Impacto:** Na feature engineering por trecho (segmento de rodovia), registros com `km<=0` devem ser excluídos apenas da agregação espacial, não do dataset geral.

## D-05: Excluir `br == 0` de rankings por rodovia

- **Contexto:** Análise de anomalias por rodovia (`br_severity_outliers`).
- **Evidência:** 788 registros (0,25%) têm `br = 0`, que não corresponde a nenhuma rodovia federal real; esse grupo aparece como outlier estatístico (pct_grave=7,74%, z=-2,81) apenas por ser um "cesto" de rodovia não identificada.
- **Decisão:** Tratar `br=0` como placeholder de "rodovia não identificada" e excluí-lo de comparações/rankings de risco por rodovia.
- **Alternativas consideradas:** manter no ranking — rejeitada, pois distorce comparações ao misturar registros heterogêneos sob um código inexistente.
- **Justificativa:** Consistência de negócio: não existe BR-000.
- **Impacto:** Features de histórico por rodovia (`br`) devem filtrar `br <> 0` antes de agregar.

## D-06: Usar z-score (não IQR) para detectar anomalias em `mortos` e `feridos_graves`

- **Contexto:** Detecção de outliers em variáveis de contagem raras (skill `eda`, seção 8).
- **Evidência:** Mediana e Q1/Q3 de `mortos` e `feridos_graves` são 0 (dados zero-inflacionados). O método IQR sinaliza qualquer valor >0 como outlier (7,19% e 22,65% das linhas, respectivamente) — resultado sem valor analítico.
- **Decisão:** Usar z-score (|z|>3) como critério primário de anomalia para essas duas colunas, resultando em 0,83% e 0,85% de registros extremos — coerente com "eventos catastróficos raros" (ex.: acidente com 37 mortos em Teófilo Otoni/MG, 2024-12-21).
- **Alternativas consideradas:** IQR puro — descartado por degenerar quando IQR=0; percentil fixo (ex.: top 0,1%) — não escolhido por ser arbitrário sem base na dispersão real dos dados.
- **Justificativa:** Escolher o método de acordo com a distribuição real da variável, como exige a skill `eda`.
- **Impacto:** O Streamlit e `run_eda.py` reportam ambos os métodos lado a lado para transparência, mas a interpretação textual usa z-score para essas colunas.

## D-07: Excluir colunas pós-evento do conjunto de features preditivas (prevenção de data leakage)

- **Contexto:** Regra central da spec (seção 10) e das skills `eda`/`feature-engineering`: nunca usar informação que só existe depois do acidente ocorrer.
- **Evidência:** `mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `pessoas` e `classificacao_acidente` descrevem o **resultado** do acidente que está sendo previsto; todas têm associação estatística forte com a gravidade (por definição), mas nenhuma estaria disponível no momento da previsão de risco de um trecho/período futuro.
- **Decisão:** Essas colunas só podem ser usadas para (a) construir o target (`gravidade_4`/`grave_bin`) ou (b) compor agregados **históricos** de períodos anteriores ao período previsto (ex.: "número de acidentes graves no trecho nos últimos 12 meses"). Nunca como valor do próprio acidente/período-alvo.
- **Alternativas consideradas:** usá-las diretamente como features — rejeitada categoricamente, geraria um modelo que "prevê" o passado, inútil em produção.
- **Justificativa:** Regra de leakage explícita da spec e das skills do projeto.
- **Impacto:** `docs/analises/EDA.md` §7 lista essas colunas com o rótulo "NÃO usar como feature direta"; a futura etapa de feature engineering deve implementar agregações com corte temporal estrito (apenas dados anteriores ao período previsto).

## D-08: Reportar Cramér's V como medida principal de força de associação, não apenas p-valor

- **Contexto:** Todos os testes qui-quadrado entre `gravidade_4` e variáveis explicativas deram p ≈ 0.
- **Evidência:** Com n=311.751, mesmo associações fracas (ex.: `mes`, Cramér's V=0,008) atingem p<0,00001 — significância estatística trivial em amostras grandes.
- **Decisão:** Reportar e ordenar achados por Cramér's V (força do efeito), tratando o p-valor apenas como confirmação de que a associação não é ruído, nunca como medida de importância prática.
- **Alternativas consideradas:** reportar apenas p-valor — rejeitado por ser enganoso nesse volume de dados.
- **Justificativa:** Regra explícita da skill `eda`: "significância estatística não deve ser tratada como significância prática".
- **Impacto:** Ranking de variáveis candidatas a features fortes por associação: `tipo_acidente` (V=0,30) e `causa_acidente` (V=0,24) primeiro; `mes` e `condicao_metereologica` (V<0,04) como sinais fracos isoladamente.

## D-09: Usar DuckDB como motor de agregação para EDA e Streamlit

- **Contexto:** Skills `duckdb-analytics` e `streamlit-ml-eda` recomendam empurrar agregações para SQL em vez de pandas puro.
- **Evidência:** O dataset (311k linhas, 30 colunas) cabe em memória, mas o app Streamlit precisa recalcular agregações a cada interação de filtro.
- **Decisão:** Centralizar leitura/agrupamento em `src/eda_utils.py` via DuckDB (`get_connection`), com view `acidentes_enriquecido` pré-computando `ano`, `mes`, `hora`, `gravidade_4`, `grave_bin`; cache de resultados no Streamlit via `st.cache_data`.
- **Alternativas consideradas:** carregar tudo em um DataFrame pandas global — mantido como fallback simples, mas os agrupamentos pesados (contingência, séries temporais) usam SQL.
- **Justificativa:** Reprodutibilidade e performance; evita duplicar lógica de agregação entre `run_eda.py` e o Streamlit.
- **Impacto:** Uma única fonte de verdade (`src/eda_utils.py`) para todas as métricas exibidas em documentos e no app.

## D-10: Atualizar `requirements.txt` com as dependências da EDA/Streamlit

- **Contexto:** `requirements.txt` só tinha `pandas`, `pyarrow`, `numpy` (suficiente apenas para a etapa de ingestão).
- **Evidência:** A EDA estatística exige `scipy` (testes/qui-quadrado/Cramér's V), a exploração interativa exige `streamlit` e `plotly`, e a agregação eficiente exige `duckdb`. `scikit-learn` é necessário para a etapa de ML já prevista na spec.
- **Decisão:** Adicionar `duckdb`, `scipy`, `scikit-learn`, `streamlit`, `plotly` ao `requirements.txt`.
- **Alternativas consideradas:** `matplotlib`/`seaborn` em vez de `plotly` — descartado porque o Streamlit se integra melhor com gráficos interativos Plotly (zoom, tooltip, filtro) exigidos pela skill `streamlit-ml-eda`.
- **Justificativa:** Sem essas libs a EDA e o dashboard não executam.
- **Impacto:** Ambiente precisa de `pip install -r requirements.txt` antes de rodar `src/run_eda.py` ou `streamlit run streamlit/app.py`.

## D-11: Usar `fase_dia` como proxy de "iluminação" / período do dia

- **Contexto:** O prompt de análise pede "Gravidade × Iluminação", mas a camada "agrupados por ocorrência" da PRF não tem uma coluna própria de condição de iluminação.
- **Evidência:** `fase_dia` (Amanhecer/Pleno dia/Anoitecer/Plena Noite) é o campo oficial da PRF mais próximo do conceito de luminosidade no momento do acidente.
- **Decisão:** Usar `fase_dia` como a variável de "iluminação/período do dia" em todas as análises e no Streamlit, documentando explicitamente essa equivalência.
- **Alternativas consideradas:** derivar período do dia apenas a partir de `horario` (hora do relógio) — mantido como variável complementar (`hora`), mas `fase_dia` é preferível por refletir luz solar real (varia por estação/latitude), não apenas o relógio.
- **Justificativa:** Evita inventar uma coluna inexistente e reaproveita um campo já oficial da fonte.
- **Impacto:** `docs/analises/EDA.md` e o Streamlit rotulam claramente `fase_dia` como "período do dia / luminosidade (proxy oficial PRF)".

## D-12: Comparações ano a ano usam janela comparável (jan–jul), nunca o total bruto de 2026

- **Contexto:** 2026 só tem dados até 2026-07-31 no dataset curado.
- **Evidência:** Total bruto de 2026 (33.694) é ~54% menor que 2025 (72.529), o que sozinho sugeriria queda drástica — mas 2026 simplesmente não tem ago–dez ainda.
- **Decisão:** Toda comparação de volume entre anos que inclua 2026 deve restringir os demais anos ao mesmo intervalo jan–jul.
- **Alternativas consideradas:** excluir 2026 da EDA — rejeitada, pois os 7 meses disponíveis são dados reais e úteis (ex.: para o mês corrente da análise, 2026-08); anualizar 2026 (extrapolar) — rejeitada por poder "inventar" acidentes que não ocorreram.
- **Justificativa:** Regra "não inventar resultados" e "não confundir agregação parcial com tendência real".
- **Impacto:** `run_eda.py` calcula `accidents_jan_jul_by_year` e `grave_pct_by_year_jan_jul` especificamente para permitir essa comparação justa; o Streamlit expõe um aviso quando o filtro de ano inclui 2026.

## D-13: Truncar a série em 2026-06-23 para qualquer análise de tendência recente

- **Contexto:** [D-12](#d-12) determinou usar janela comparável (jan–jul) para comparar anos, assumindo que o problema de 2026 era apenas o ano estar incompleto.
- **Evidência:** [A-19](ANALYSIS_LOG.md#a-19--a-queda-de-volume-no-fim-da-série-é-falta-de-consolidação-da-fonte-não-redução-de-acidentes) mostra que o problema é mais profundo: os últimos 38 dias da série (após 2026-06-23) têm 492 registros contra uma mediana histórica de 188/dia, 8 dias do calendário não têm nenhum registro, e julho/2026 tem 122 acidentes contra 5.659–6.401 nos julhos anteriores. Como junho e julho de 2026 estão *dentro* da janela jan–jul, o recorte de D-12 continua contaminado.
- **Decisão:** Adotar um corte de consolidação calculado automaticamente (`eda_utils.consolidation_cutoff`, atualmente 2026-06-23) e usá-lo em toda análise de tendência recente. Comparações entre anos passam a usar o mesmo dia do ano para todos (dia 174), não o recorte de meses.
- **Alternativas consideradas:** (a) manter apenas D-12 — rejeitada, produz a conclusão falsa de queda de 17,8%; (b) remover 2026 da base — rejeitada, os ~33 mil registros consolidados de 2026 são dados reais e úteis; (c) extrapolar/anualizar 2026 — rejeitada por inventar acidentes que não ocorreram.
- **Justificativa:** O corte é derivado dos dados (média móvel de 7 dias abaixo de 70% da mediana histórica de referência), não escolhido a olho, e é recalculado automaticamente se a base for atualizada.
- **Impacto:** `run_eda.py` passa a gravar `consolidation_window` e `accidents_by_year_consolidated_window`; o Streamlit ganhou o filtro global "Excluir janela não consolidada" (desmarcado por padrão, para preservar a reprodutibilidade dos números históricos deste documento) e um alerta na página inicial. A conclusão publicável sobre 2026 passa a ser "estável (−0,4%) em relação a 2025", não "queda acentuada".

## D-14: Comparações entre grupos exigem intervalo de confiança, tamanho de efeito e teste de composição

- **Contexto:** A EDA compara taxas de gravidade entre UFs, rodovias, tipos de pista, fases do dia e trechos. Com n grande, qualquer diferença sai "significante" ([D-08](#d-08)), e diferenças brutas entre grupos podem ser puro efeito de composição.
- **Evidência:** [A-21](ANALYSIS_LOG.md#a-21--parte-do-excesso-de-gravidade-do-maranhão-é-composição-de-tipo-de-pista-mas-a-maior-parte-não-é): 28% do excesso de gravidade do MA desaparece ao padronizar por `tipo_pista`. [A-20](ANALYSIS_LOG.md#a-20--o-efeito-de-feriado-é-de-véspera-e-é-de-volume-não-de-gravidade): a diferença de gravidade em vésperas de feriado tem IC de −0,34 a +1,44 p.p., ou seja, é indistinguível de zero apesar de a amostra ter 10.260 acidentes. Contrastes fortes como pista Simples vs. Dupla (+10,44 p.p.) têm h de Cohen de apenas 0,23 ("pequeno").
- **Decisão:** Toda comparação de taxas entre grupos publicada neste projeto deve trazer: (a) IC 95% de Wilson de cada proporção; (b) diferença com IC e tamanho de efeito (h de Cohen para proporções, Cramér's V para associação categórica, ε² para Kruskal-Wallis); (c) pelo menos uma verificação de confundimento por padronização direta quando a comparação for entre grupos com composições diferentes.
- **Alternativas consideradas:** reportar só a diferença bruta com p-valor — rejeitada por ser exatamente o erro que a disciplina aponta (concluir sem validação adequada e ignorar segmentação).
- **Justificativa:** IC comunica precisão, tamanho de efeito comunica relevância, padronização protege contra o paradoxo de Simpson. Nenhum dos três é substituível pelos outros.
- **Impacto:** Novas funções em `eda_utils.py` (`wilson_ci`, `two_proportion_test`, `standardized_rate`), novos blocos em `run_eda.py` (`two_proportion_tests`, `ma_standardization`, `uf_severity_rate_with_ci`) e duas páginas novas no Streamlit (✂️ Segmentação e 🧪 Validação Estatística). Rankings por UF, rodovia e trecho passam a exibir barras de erro.
