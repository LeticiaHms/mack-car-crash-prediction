# Etapa 2 — Análise Exploratória de Dados (EDA)

**Projeto:** Predição de Risco de Acidentes em Rodovias Federais (base PRF + feriados ANBIMA)
**Scripts:** [`src/eda_utils.py`](../../src/eda_utils.py) · [`src/run_eda.py`](../../src/run_eda.py) · [`streamlit/`](../../streamlit/)
**Evidências:** [`reports/eda/eda_results.json`](../../reports/eda/eda_results.json) (37 blocos) · [`reports/eda/tables/`](../../reports/eda/tables/) (26 CSVs)
**Glossário dos termos técnicos:** [`docs/GLOSSARIO.md`](../GLOSSARIO.md) — explica z-score, qui-quadrado, Cramér's V, intervalo de confiança e demais termos usados aqui
**Documentos derivados:** [`docs/specs/eda/EDA.md`](../specs/eda/EDA.md) · [`docs/ANALYSIS_LOG.md`](../ANALYSIS_LOG.md) (A-01…A-22) · [`docs/DECISIONS.md`](../DECISIONS.md) (D-01…D-14) · [`docs/DATA_QUALITY.md`](../DATA_QUALITY.md)
**Base analisada:** `dados/curated/acidentes_2022_2026.parquet` (311.751 linhas × 30 colunas) + `dados/curated/feriados_nacionais.parquet` (63 feriados)
**Data de execução:** 2026-09-01

> Nenhum número deste documento foi digitado à mão: todos vêm de `python src/run_eda.py`, que grava `reports/eda/eda_results.json`. O app Streamlit consome as mesmas funções de `src/eda_utils.py`, então documento e dashboard não podem divergir.

---

## 1. Objetivo e escopo

Compreender a base curada da Etapa 1, identificar padrões e produzir os insumos que orientam a modelagem: definição da variável-alvo, variáveis candidatas a feature, riscos de vazamento e limitações que restringem as conclusões.

- **Unidade de análise:** 1 linha = 1 **acidente (ocorrência)** — não é uma linha por pessoa nem por veículo. Toda média de vítimas é *por acidente*.
- **Período:** 2022-01-01 a 2026-07-31 (2026 parcial — e, como a §4.5 mostra, também sub-registrado no final).
- **Pergunta de negócio:** dado que um acidente ocorre em determinado trecho/momento, qual a chance de ele ser **grave**? A base não permite responder "qual trecho é mais perigoso por viagem", porque não há dado de fluxo de veículos (§7).

### 1.1 Como reproduzir

```bash
pip install -r requirements.txt

python src/run_eda.py                      # regenera reports/eda/ (JSON + 26 tabelas CSV)
streamlit run streamlit/app.py             # dashboard interativo, 14 páginas
python scripts/smoke_streamlit.py          # verifica que todas as páginas executam sem erro
```

---

## 2. Abordagens utilizadas e por que foram escolhidas

Esta seção responde à exigência da disciplina de **justificar o método, não apenas apresentar o resultado**. Cada escolha abaixo tem uma decisão formal registrada em [`DECISIONS.md`](../DECISIONS.md).

### 2.1 Infraestrutura: DuckDB + camada analítica única

| Escolha | Alternativa descartada | Por quê |
|---|---|---|
| Agregações em SQL sobre o Parquet (DuckDB) | Carregar tudo em um DataFrame pandas | O dashboard recalcula agregados a cada mudança de filtro; empurrar o `GROUP BY` para o DuckDB mantém a interação fluida sem materializar 311 mil linhas em memória a cada rerun |
| Toda estatística em `src/eda_utils.py` | Lógica duplicada entre script e app | Fonte única de verdade: se o documento e o app divergissem, um dos dois estaria errado e não haveria como saber qual ([D-09](../DECISIONS.md#d-09)) |
| View `acidentes_enriquecido` com colunas derivadas | Derivar `ano`/`hora`/`gravidade_4` em cada consulta | Garante que "gravidade" signifique exatamente a mesma coisa em todas as páginas e em todos os relatórios |

### 2.2 Definição da variável-alvo

A coluna oficial `classificacao_acidente` tem 3 categorias, e a categoria majoritária ("Com Vítimas Feridas", 76,58%) **mistura ferido leve e ferido grave** — 72,5% dela é só ferido leve. Usá-la como alvo esconderia justamente o desfecho que o projeto quer prever.

Foram derivadas duas variáveis a partir das contagens de vítimas ([D-01](../DECISIONS.md#d-01), [D-02](../DECISIONS.md#d-02)):

- `gravidade_4` = {Sem vítimas, Leve, Grave (não fatal), Fatal} — para a análise exploratória, porque preserva a ordem do desfecho;
- `grave_bin` = 1 se `mortos > 0` **ou** `feridos_graves > 0` — para a modelagem, porque agrupa os dois desfechos que órgãos de segurança viária querem evitar e produz um desbalanceamento tratável (~2,5:1) em vez do evento raríssimo que seria "só fatal" (7,19%).

### 2.3 Medir força de associação, não significância

Com n = 311.751, **todo** teste qui-quadrado dá p ≈ 0 — inclusive `mes`, cuja associação com a gravidade é praticamente nula. O p-valor, sozinho, não distingue um achado útil de um irrelevante.

Por isso o critério de priorização é o **tamanho de efeito**, e o p-valor entra apenas como checagem de que o sinal não é ruído ([D-08](../DECISIONS.md#d-08), [D-14](../DECISIONS.md#d-14)):

| Situação | Medida adotada | Por quê |
|---|---|---|
| Categórica × categórica | **Cramér's V** com correção de viés (Bergsma) | Normalizado em [0,1] e comparável entre variáveis com números de categorias diferentes — sem a correção, variáveis com muitas categorias (`br`, 125) apareceriam artificialmente mais fortes que `tipo_pista` (3) |
| Duas proporções | **Teste z + IC 95% da diferença + h de Cohen** | O IC mostra a precisão; o h mostra a relevância prática. Uma diferença "significante" de 0,5 p.p. não muda decisão nenhuma |
| Proporção isolada | **IC de Wilson** | Não degenera quando p→0/1 nem com n pequeno — exatamente o caso de rodovias e trechos com poucos acidentes, onde o IC normal (Wald) produziria limites impossíveis |
| Numérica × grupos | **Kruskal-Wallis + ε²** | Ver §2.6 |
| Numérica × numérica | **Spearman** | Ver §2.6 |

Demonstração empírica do problema, disponível na página 🧪 do app: com n = 311.751, uma diferença de apenas **0,25 p.p.** já sai "estatisticamente significante".

### 2.4 Detecção de anomalias: método escolhido pela forma da distribuição

As variáveis de vítimas são **zero-infladas**: a mediana de `mortos` e `feridos_graves` é 0, e Q1 = Q3 = 0. Nessas colunas o IQR **degenera** — qualquer valor > 0 vira "outlier", sinalizando 22,65% das linhas em `feridos_graves` e 43,46% em `feridos`, o que não tem valor analítico nenhum.

| Coluna | IQR sinaliza | Z-score sinaliza | Método adotado |
|---|---:|---:|---|
| `feridos` | 43,46% | 1,25% | z-score |
| `feridos_graves` | 22,65% | 0,85% | z-score |
| `mortos` | 7,19% | 0,83% | z-score |
| `km` | 1,06% | 0,57% | qualquer um (distribuição bem-comportada) |

Decisão: **z-score (|z| > 3) para colunas de contagem rara**, IQR para as demais, com os dois métodos sempre reportados lado a lado para transparência ([D-06](../DECISIONS.md#d-06)). Regra transversal: **nenhuma anomalia foi removida da base** — cada uma foi classificada em *evento real*, *problema de qualidade* ou *inconclusivo* (§4.7).

### 2.5 Sazonalidade exige recorrência, não oscilação

Um gráfico que sobe e desce não é evidência de sazonalidade: séries aleatórias também sobem e descem. O critério adotado foi **correlação de Spearman entre os rankings mensais de anos diferentes** — se dezembro é alto em 2022, 2023, 2024 e 2025, o padrão recorre; se cada ano tem um mês alto diferente, é ruído.

Spearman (e não Pearson) porque interessa a **posição relativa** do mês, não a magnitude absoluta, que varia com o crescimento do volume entre anos.

### 2.6 Testes não-paramétricos para as variáveis de contagem

`mortos` tem assimetria 10,75 e curtose 560; `veiculos`, curtose 651. Nenhuma dessas variáveis é remotamente normal, o que invalida ANOVA e Pearson.

| Análise | Teste adotado | Por que não o clássico |
|---|---|---|
| `veiculos`/`pessoas` entre níveis de gravidade | Kruskal-Wallis + ε² | ANOVA assume normalidade e homocedasticidade; ambas violadas |
| Correlação entre contagens | Spearman | Pearson é sensível à cauda extrema (um acidente com 37 mortos domina o coeficiente) |
| Volume diário em feriados vs. dias comuns | Mann-Whitney | Contagem diária não é normal e o grupo de feriados é pequeno (51–57 dias) |

### 2.7 Controle de composição: padronização direta

Comparar a taxa média de dois grupos sem verificar a composição deles é o caminho mais curto para uma conclusão errada — o caso clássico do paradoxo de Simpson. A abordagem adotada foi a **padronização direta**: recalcular a taxa de cada grupo como se ambos tivessem a mesma distribuição de um possível confundidor.

Escolhida em vez de regressão logística porque nesta etapa o objetivo é *explicar*, não prever: a padronização mostra explicitamente quanto do excesso vem da composição e quanto sobra, sem exigir suposições de forma funcional. O ajuste multivariado fica para a etapa de modelagem (hipótese H-04).

### 2.8 Escolha dos gráficos

Cada tipo de gráfico responde a uma pergunta diferente; usar o errado induz leitura errada (erro nº 6 do guia).

| Pergunta | Gráfico adotado | Por que não outro |
|---|---|---|
| Como esta variável se distribui? | Histograma + boxplot por grupo | Média sozinha esconde a cauda; com assimetria 10+ ela nem representa o caso típico |
| Como duas categorias se comparam? | Barras **com barra de erro (IC 95%)** | Barra sem IC sugere precisão que grupos pequenos não têm |
| O que mudou ao longo do tempo? | Linha + média móvel de 7 dias | Barras não comunicam continuidade; a média móvel separa tendência de ruído diário |
| Volume e taxa mudam juntos? | Eixo duplo (barra = volume, linha = %) | Deixa explícito que volume alto ≠ risco alto |
| Onde duas dimensões interagem? | Heatmap (mês×ano, dia×hora) | Sete linhas sobrepostas seriam ilegíveis |
| Onde os acidentes acontecem? | Densidade 2D com eixo em escala geográfica | Mapa de pontos com 311 mil marcadores vira uma mancha uniforme; o mapa base é oferecido como opção, sobre uma amostra |
| Rankings | Barras horizontais ordenadas + `n` visível | Pizza não permite ordenar nem comparar fatias parecidas |

Regra transversal: nenhum eixo de percentual começa fora do zero, e todo ranking exibe o `n` do grupo ao lado da taxa.

### 2.9 Critério de feature: disponibilidade, não correlação

Para cada coluna foi feita **uma única pergunta**: *essa informação estaria disponível no momento em que a previsão precisa ser feita?* Se não, ela é vetada como feature direta, **independentemente de quão associada esteja ao alvo** ([D-07](../DECISIONS.md#d-07)).

Essa regra é o que impede a armadilha central deste dataset: as duas variáveis mais associadas à gravidade (`tipo_acidente`, V=0,300; `causa_acidente`, V=0,244) são apuradas **depois** do acidente. Selecionar features por correlação produziria um modelo excelente na validação e inútil em produção.

---

## 3. Qualidade dos dados após a limpeza

Ver página **🧹 Qualidade dos Dados** do app e [`DATA_QUALITY.md`](../DATA_QUALITY.md).

### 3.1 O que está correto

| Check | Resultado |
|---|---|
| IDs duplicados / linhas 100% duplicadas | 0 / 0 |
| Nulos em colunas analíticas (data, local, vítimas, via) | 0 |
| `feridos = feridos_leves + feridos_graves` | 100% coerente |
| `classificacao_acidente` × contagens de vítimas | 100% coerente |
| `dia_semana` × `data_inversa` | 100% coerente |
| `horario` convertível para `TIME` | 100% |
| UFs válidas / coordenadas dentro do Brasil | 27 UFs / 0 fora |

### 3.2 O que uma contagem de nulos não capturaria

A base quase não tem `NULL` — e é justamente por isso que os problemas restantes são traiçoeiros: todos ocupam a posição de dado válido.

| Situação | Registros | % | Tratamento |
|---|---:|---:|---|
| `tracado_via` multivalorada (`Reta;Declive`) | 70.204 | 22,52% | Exige **multi-hot** (12 primitivas reais), não one-hot da string — sem isso a coluna aparenta ter 1.223 categorias |
| `condicao_metereologica = 'Ignorado'` | 4.108 | 1,32% | Não é uma condição climática; não deve virar categoria própria sem ressalva |
| `regional`/`delegacia`/`uop` nulos | 3.365 | 1,08% | Identificam a unidade da PRF, não o acidente — não são features |
| `km <= 0` | 1.496 | 0,48% | Placeholder de "não informado"; mantido, mas excluído de agregações espaciais ([D-04](../DECISIONS.md#d-04)) |
| `br = 0` e `sentido_via = 'Não Informado'` | 788 | 0,25% | Mesmo lote de registros; `br=0` excluído de rankings por rodovia ([D-05](../DECISIONS.md#d-05)) |
| `pessoas` ≠ soma das vítimas | 16.817 | 5,39% | Não corrigido — não há como saber qual campo erra. Usar as colunas de vítimas diretamente ([D-03](../DECISIONS.md#d-03)) |

### 3.3 Cobertura temporal — o achado de maior impacto

Comparando os dias observados com o calendário completo: **8 dos 1.673 dias não têm nenhum registro**, todos entre 2026-07-01 e 2026-07-14. Investigando o entorno, o problema é maior que 8 dias:

| Janela | Acidentes | Acidentes/dia |
|---|---:|---:|
| Mediana histórica da série | — | **188** |
| Junho/2026 | 4.434 | 147,8 |
| Julho/2026 | 122 | 5,3 |
| Últimos 38 dias (após 2026-06-23) | **492** | ~13 |

Julho de 2026 tem 122 acidentes contra 5.659–6.401 nos julhos de 2022 a 2025. Nenhuma melhoria de segurança viária produz esse formato — é a assinatura de **registro administrativo ainda não consolidado na fonte**. Consequências em §4.5 e [D-13](../DECISIONS.md#d-13).

---

## 4. Resultados

### 4.1 Estatística descritiva

| Coluna | Média | Mediana | Desvio | Máx | Assimetria | Curtose |
|---|---:|---:|---:|---:|---:|---:|
| `pessoas` | 2,60 | 2 | 2,23 | 95 | 11,22 | 230,2 |
| `veiculos` | 1,99 | 2 | 1,13 | 131 | 8,65 | 650,7 |
| `feridos` | 1,15 | 1 | 1,21 | 84 | 11,22 | 356,5 |
| `feridos_graves` | 0,28 | 0 | 0,62 | 35 | 6,37 | 161,3 |
| `mortos` | 0,08 | 0 | 0,35 | 37 | 10,75 | 560,4 |
| `km` | 259,3 | 193 | 227,0 | 1.470 | 1,00 | 0,4 |

**Leitura:** todas as contagens de vítimas são fortemente assimétricas à direita e zero-infladas — o acidente típico não tem mortos, e a média é puxada por uma cauda rara de eventos catastróficos. Isso condiciona três decisões metodológicas: usar mediana e não média para descrever o caso típico, usar z-score e não IQR para anomalias (§2.4), e usar testes não-paramétricos (§2.6). `km` é a única variável bem-comportada (assimetria 1,00).

**Categóricas:** `municipio` (2.057 categorias, 2.052 abaixo de 1%), `br` (125), `causa_acidente` (77), `tipo_acidente` (17), `uf` (27). As de alta cardinalidade exigem agrupamento ou target encoding — one-hot direto produziria matriz esparsa inviável.

### 4.2 Variável-alvo

| `gravidade_4` | Registros | % |
|---|---:|---:|
| Leve | 173.003 | 55,49% |
| Grave (não fatal) | 65.746 | 21,09% |
| Sem vítimas | 50.581 | 16,22% |
| Fatal | 22.421 | 7,19% |

`grave_bin = 1` → **88.167 (28,28%)** vs. 223.584 (71,72%). Desbalanceamento moderado (2,5:1), tratável sem resampling agressivo. A avaliação do modelo deve priorizar **Recall/F1/PR-AUC da classe grave**, nunca Accuracy — um classificador que sempre responde "não grave" acertaria 71,72%.

### 4.3 Associações com a gravidade

| Variável | Cramér's V | Disponível a priori? |
|---|---:|---|
| `tipo_acidente` | 0,300 | ❌ pós-evento |
| `causa_acidente` | 0,244 | ❌ pós-evento |
| `br` | 0,110 | ✅ |
| `uf` | 0,105 | ✅ |
| `uso_solo` | 0,098 | ✅ |
| `hora` | 0,097 | ✅ |
| `tipo_pista` | 0,095 | ✅ |
| `fase_dia` | 0,081 | ✅ |
| `sentido_via` | 0,050 | ✅ |
| `tracado_via` | 0,047 | ✅ |
| `dia_semana` | 0,042 | ✅ |
| `condicao_metereologica` | 0,034 | ⚠️ não previsível |
| `mes` | 0,008 | ✅ (irrelevante) |

Todas com p ≈ 0 — o que reforça §2.3: é o V que ordena, não o p.

Contrastes principais, com validação formal:

| Contraste | Taxas | Diferença | IC 95% | Razão de risco | h de Cohen |
|---|---|---:|---|---:|---|
| Pista **Simples** vs. **Dupla** | 33,79% vs. 23,35% | +10,44 p.p. | +10,11 a +10,78 | 1,45× | 0,232 (pequeno) |
| **Plena Noite** vs. **Pleno dia** | 32,57% vs. 25,29% | +7,27 p.p. | +6,93 a +7,62 | 1,29× | 0,161 (desprezível) |

**Leitura honesta:** a *direção* desses efeitos é inequívoca — os intervalos não chegam perto do zero. A *magnitude*, porém, é modesta pela escala de Cohen. Nenhuma variável isolada separa acidentes graves dos demais; o modelo precisará da combinação delas. Outros cruzamentos: rodovia não pavimentada/rural (`uso_solo='Não'`) 29,85% vs. urbano 26,20%; fim de semana (domingo 30,37%, sábado 30,02%) acima do meio de semana (quarta 26,92%); nevoeiro/neblina 32,09% (e a maior taxa de fatalidade, 11,63%) contra 27,09% em dia de sol.

### 4.4 Padrões diários e semanais

Volume: pico às **18h** (23.139 acidentes), depois 17h e 19h; vale entre 1h e 3h. Gravidade relativa: pico às **19h (33,88%)**, seguida de 21h, 20h e 23h.

**Os dois picos não coincidem** — e essa é a distinção mais fácil de errar na leitura. Quem olha só a contagem por hora conclui que "o perigo é às 18h"; o que os dados mostram é que às 18h há muito **tráfego** (exposição), enquanto à noite cada acidente tende a ser mais grave (velocidade maior, menos visibilidade, socorro mais lento).

### 4.5 Tendências temporais — e a conclusão que precisou ser corrigida

Volume bruto por ano: 2022=64.606, 2023=67.766, 2024=73.156, 2025=72.529, 2026=33.694 (parcial).

A leitura ingênua do recorte jan–jul sugeria **queda de 17,8% em 2026**. Aplicando o corte de consolidação de §3.3 e comparando todos os anos até o **mesmo dia do ano (dia 174)**:

| Ano | Acidentes (janela consolidada) | Variação | % grave |
|---|---:|---:|---:|
| 2022 | 29.804 | — | 28,28% |
| 2023 | 31.262 | +4,89% | 28,20% |
| 2024 | 33.594 | +7,46% | 28,24% |
| 2025 | 33.344 | −0,74% | 28,07% |
| **2026** | **33.202** | **−0,43%** | 27,92% |

**A queda de 2026 não existe.** Ela era inteiramente um artefato da janela não consolidada — e note que o recorte jan–jul de [D-12](../DECISIONS.md#d-12) *não* resolvia o problema, porque junho e julho de 2026 caem dentro do trecho contaminado. Os mesmos dados contam três histórias diferentes conforme a janela escolhida (queda de 54% no bruto, queda de 17,8% em jan–jul, estabilidade na janela consolidada) e só a última é defensável.

**Estabilidade da gravidade:** a proporção de acidentes graves permanece entre **27,92% e 28,28%** nos cinco anos — amplitude de 0,36 p.p. O que oscila entre anos é o **volume**, não a gravidade condicional. Isso significa que (a) não há evidência de melhora nem piora da gravidade no período e (b) um split temporal treino/teste é seguro, porque a relação entre features e alvo não está mudando.

### 4.6 Sazonalidade e feriados

**Sazonalidade de volume, comprovada por recorrência:** ρ̄ de Spearman = **0,845** entre os rankings mensais dos 4 anos completos. Pico em março–maio (mai = 28.922), vale em setembro–novembro (nov = 23.165), alta novamente em dezembro. Já a associação entre `mes` e `gravidade_4` é de V = 0,008 — **praticamente nula**. O calendário prevê *quantos* acidentes acontecem, não *quão graves*.

**Feriados** (cruzamento com as 63 datas do calendário nacional, série truncada em 2026-06-23):

| Tipo de dia | Dias | Acidentes/dia | vs. dia comum | p (Mann-Whitney) | % grave | Dif. de gravidade (IC 95%) |
|---|---:|---:|---:|---:|---:|---|
| Dia comum | 1.475 | 190,2 | — | — | 28,23% | referência |
| **Véspera de feriado** | 51 | **201,2** | **+5,75%** | **0,004** | 28,78% | +0,55 p.p. (−0,34 a +1,44) |
| Feriado | 57 | 188,7 | −0,81% | 0,774 | 28,45% | ≈ 0 |
| Pós-feriado | 52 | 185,4 | −2,52% | 0,352 | 28,77% | ≈ 0 |

O senso comum de que "feriado é mais perigoso" **não se sustenta**: o feriado em si é estatisticamente indistinguível de um dia comum. O que se destaca é a **véspera**, com ~6% mais acidentes — compatível com o movimento de saída. E o efeito é exclusivamente de **exposição**: o IC da diferença de gravidade cruza o zero nos três casos.

**Ressalva metodológica registrada:** feriados não caem uniformemente pelos dias da semana, e o dia da semana tem efeito próprio (§4.4). Essa comparação ainda não controla esse confundidor — a página ✂️ Segmentação permite fazê-lo.

### 4.7 Anomalias — classificadas, nenhuma removida

| Anomalia | Classificação | Base da classificação |
|---|---|---|
| Eventos com dezenas de mortos (BR-116, Teófilo Otoni/MG, 2024-12-21, 37 mortos; pile-ups por neblina na BR-277) | **Evento real plausível** | Inspeção manual dos registros; consistentes entre si e com o tipo de acidente |
| Picos diários em dezembro (5 dos 8 maiores, em 3 anos diferentes) | **Evento sazonal real** | Recorrência entre anos |
| Pico isolado de 2024-10-20 (282 acidentes) | **Inconclusivo** | Não recorre em nenhum outro ano e nenhuma variável da base o explica |
| Janela final da série (38 dias, 492 registros) | **Problema de qualidade** | §3.3 — não é queda de acidentes |
| 8 dias sem nenhum registro | **Problema de qualidade** | Lacuna de cobertura, toda no mês final |
| `br=0` (7,74% grave, z=−2,81) | **Problema de qualidade** | Não é rodovia; é um "cesto" de registros heterogêneos |
| MA com 46,25% grave (z=+2,12) | **Hipótese** | Ver §4.8 |
| BR-405 (52,73%), BR-424 (50,45%), BR-402 (50,19%) | **Sinal preliminar** | n moderado (263–442); IC largo |

Detecção da série diária por IQR: limite superior de 278,5 acidentes/dia, 42 dias acima (2,52%).

### 4.8 Dimensão geográfica e controle de composição

Taxa de gravidade por UF, com IC de Wilson: **MA 46,25% (44,91–47,60)**, PI 41,24%, AL 39,15% — contra SP 18,63% e a média nacional de 28,28%.

Aplicando padronização direta (§2.7) ao Maranhão, usando `tipo_pista` como estrato:

| Métrica | Valor |
|---|---:|
| Taxa bruta do MA | 46,25% |
| Taxa do MA padronizada pela composição nacional | **41,23%** |
| Taxa nacional | 28,28% |
| **Excesso explicado apenas pela composição** | **28%** |

O MA tem 74,9% dos acidentes em pista simples contra 48,6% no país, e pista simples é o estrato mais grave — isso explica 5,02 dos 17,97 p.p. de excesso. **Mas o controle não fez o efeito desaparecer:** restam ~12,9 p.p. sem explicação estrutural na base. Candidatos plausíveis e não medidos: tempo de resposta do socorro, perfil de velocidade, densidade de fiscalização, distância a hospitais. Permanece **hipótese de investigação** — nunca uma afirmação sobre o comportamento dos motoristas do estado.

**Trechos (BR × faixa de km):** o ranking por volume absoluto e o ranking por taxa de gravidade quase não se sobrepõem. Os trechos com mais acidentes são urbanos e de tráfego intenso; os de maior proporção de acidentes graves são de velocidade alta e menor fluxo. Priorizar fiscalização por um ou por outro leva a listas diferentes — e a base não permite decidir qual está certa, porque falta o denominador de exposição (§7).

### 4.9 Features e risco de vazamento

| Categoria | Colunas | Veredito |
|---|---|---|
| Resultado do próprio acidente | `mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `pessoas`, `veiculos`, `classificacao_acidente` | ❌ Só para construir o alvo ou agregados históricos de períodos anteriores |
| Apurado após o evento | `tipo_acidente`, `causa_acidente` | ❌ Não usar direto; servem para caracterizar o histórico do trecho |
| Não previsível no futuro | `condicao_metereologica` | ⚠️ Exigiria previsão meteorológica em produção; usar só como clima típico do trecho/época |
| Estrutural (conhecido a priori) | `uf`, `br`, `km`, `municipio`, `latitude`, `longitude`, `tipo_pista`, `tracado_via`, `sentido_via`, `uso_solo` | ✅ Uso seguro |
| Temporal do período previsto | `ano`, `mes`, `dia_semana`, `hora`, `fase_dia` | ✅ Uso seguro |
| Administrativo | `regional`, `delegacia`, `uop` | ⚠️ Baixo valor, redundante com `uf`/`municipio` |

**O alerta central desta etapa:** as duas variáveis de maior associação com a gravidade estão na primeira linha da tabela. Alta correlação não é critério de elegibilidade de feature.

---

## 5. Insights consolidados

Separados pelo grau de confiança que a evidência sustenta — a distinção entre o que pode ir ao relatório como afirmação e o que ainda é suposição.

### ✅ Conclusões

1. **A queda de acidentes em 2026 não existe** — é a janela não consolidada da fonte. Na janela comparável, 2026 está estável (−0,4%). Impacto direto: um relatório que anunciasse "redução de acidentes" estaria descrevendo atraso de preenchimento.
2. **O volume oscila entre anos; a gravidade não** — 27,92% a 28,28% em cinco anos. A gravidade condicional é uma característica estrutural e estável do sistema viário.
3. **Pista simples é substancialmente mais grave que pista dupla** (+10,44 p.p., 1,45×) — o achado estrutural mais forte entre as variáveis disponíveis a priori, consistente com o mecanismo físico da colisão frontal.
4. **Escuridão agrava** — plena noite 32,57% vs. pleno dia 25,29%, com pico de gravidade às 19h contra pico de volume às 18h.
5. **A sazonalidade é de volume e recorre entre anos** (ρ̄=0,845); a gravidade não é sazonal (V=0,008).
6. **O efeito de feriado é de véspera e é de exposição** — +5,75% de volume, gravidade inalterada.
7. **As variáveis mais associadas ao alvo são justamente as inutilizáveis como feature** — `tipo_acidente` e `causa_acidente` são pós-evento.

### 🟡 Hipóteses (sinal consistente, sem controle suficiente)

8. **Excesso de gravidade do Maranhão** — 28% explicado por composição de tipo de pista; os ~12,9 p.p. restantes não têm explicação na base.
9. **Trechos com taxa extrema e poucos acidentes** — instáveis; úteis como feature com suavização, não como ranking público.

### ⚪ Inconclusivos

10. **Pico isolado de 2024-10-20** — sem recorrência e sem variável explicativa.
11. **Contagem não é risco** — sem dado de tráfego, é impossível separar "rodovia perigosa" de "rodovia movimentada". Nenhuma técnica estatística supre a ausência do dado.

---

## 6. Hipóteses para a etapa preditiva

Escritas de forma refutável — cada uma diz o que a confirmaria e o que a derrubaria.

| ID | Hipótese | Confirma se | Refuta se |
|---|---|---|---|
| **H-01** | O histórico de gravidade do próprio trecho (BR × faixa de km) é a feature mais preditiva disponível a priori | A taxa histórica do trecho eleva o PR-AUC acima do modelo só com variáveis estruturais | O ganho some ao aplicar corte temporal estrito (era vazamento) |
| **H-02** | Pista simples + período noturno prevê melhor que a soma dos efeitos isolados | Termo de interação (ou modelo de árvore) supera o modelo aditivo | O efeito conjunto é apenas a soma dos marginais |
| **H-03** | Volume e gravidade exigem dois modelos distintos | Features de calendário têm importância alta no modelo de volume e desprezível no de gravidade | Um modelo multitarefa captura ambos sem perda |
| **H-04** | O excesso do MA persiste após controlar todas as variáveis estruturais | O efeito de UF continua relevante com pista, traçado, fase do dia e uso do solo no modelo | O efeito de UF some com o conjunto completo de controles |
| **H-05** | Véspera de feriado aumenta exposição, não gravidade condicional | A flag melhora a previsão de contagem e não a de gravidade | A flag melhora o classificador de gravidade após controlar dia da semana |
| **H-06** | Perfil histórico do trecho recupera parte do poder preditivo de `causa`/`tipo_acidente` sem vazamento | Ex.: "% de colisões frontais no trecho nos últimos 12 meses" melhora o modelo | Não acrescenta nada além da taxa histórica de gravidade (H-01) |

---

## 7. Limitações da análise

1. **Sem denominador de exposição.** A base não tem fluxo de veículos (veículos·km). Todas as comparações são de *proporção de gravidade dado que houve acidente* — uma pergunta legítima, mas diferente de "risco por viagem". Enriquecer com contagem volumétrica (DNIT/ANTT) é o caminho para respondê-la.
2. **Sem condição de superfície da pista.** A camada "agrupados por ocorrência" não traz seca/molhada; `condicao_metereologica` é o proxy disponível.
3. **A janela final da série é sub-registrada.** O corte em 2026-06-23 é uma heurística derivada dos dados (média móvel abaixo de 70% da mediana de referência), não uma data oficial de fechamento da PRF; meses imediatamente anteriores podem estar parcialmente incompletos.
4. **O efeito de feriado não está controlado por dia da semana.**
5. **Todas as associações são observacionais.** Nenhuma causalidade é afirmada em nenhum ponto desta etapa. Confundidores não medidos (fiscalização, tempo de resgate, perfil de frota) permanecem fora da base.
6. **`pessoas` diverge da soma das vítimas em 5,39% das linhas** — não usar como total exato.

---

## 8. Entregáveis

| Artefato | Conteúdo |
|---|---|
| [`reports/eda/eda_results.json`](../../reports/eda/eda_results.json) | 37 blocos com todos os números citados aqui |
| [`reports/eda/tables/`](../../reports/eda/tables/) | 26 CSVs (frequências, contingências, séries, rankings com IC) |
| [`streamlit/`](../../streamlit/) | Dashboard de 14 páginas (ver abaixo) |
| [`docs/specs/eda/EDA.md`](../specs/eda/EDA.md) | Documento narrativo da EDA |
| [`docs/ANALYSIS_LOG.md`](../ANALYSIS_LOG.md) | 22 achados com pergunta, método, resultado, interpretação e limitação |
| [`docs/DECISIONS.md`](../DECISIONS.md) | 14 decisões com contexto, evidência, alternativas e impacto |
| [`scripts/smoke_streamlit.py`](../../scripts/smoke_streamlit.py) | Verificação automatizada de que todas as páginas executam |

**Páginas do dashboard:** 🔎 Visão Geral · 🧹 Qualidade dos Dados · 📊 Distribuições · 🎯 Gravidade · 📈 Tendências · 🔄 Sazonalidade · 🔗 Correlações · 🚨 Anomalias · ✂️ Segmentação · 🗺️ Geografia · 🧪 Validação Estatística · 🧠 Features para ML · 🤖 Modelos · 💡 Insights e Hipóteses.

---

## 9. Checklist da etapa

| Item | Onde | Como foi atendido |
|---|---|---|
| Qualidade dos dados após a limpeza avaliada | §3 · 🧹 | Nulos, sentinelas, coerência interna e cobertura de calendário |
| Estrutura da base compreendida | §1, §4.1 · 🧹 | Schema, tipos, cardinalidade, unidade de análise |
| Principais variáveis analisadas | §4.1 · 📊 🎯 | Cada numérica e categórica, isolada e por gravidade |
| Distribuições e medidas estatísticas | §4.1 · 📊 | Média, mediana, desvio, IQR, assimetria e curtose |
| Padrões e tendências identificados | §4.4, §4.5 · 📈 | Séries anual, mensal, semanal e horária |
| Sazonalidade investigada | §4.6 · 🔄 | Recorrência via Spearman entre anos + calendário de feriados |
| Outliers e anomalias investigados | §4.7 · 🚨 | IQR vs. z-score justificados; nada removido |
| Correlações e relações analisadas | §4.3 · 🔗 | Cramér's V, Spearman, contingência |
| Dados segmentados quando necessário | §4.8 · ✂️ 🗺️ | Comparação A/B com padronização direta e alerta de Simpson |
| Visualizações adequadas | §2.8 · todas | Um tipo de gráfico por tipo de pergunta, com IC e `n` visíveis |
| Abordagens justificadas | **§2** · DECISIONS.md | Cada escolha metodológica com alternativa descartada e motivo |
| Insights documentados | §5 · 💡 | Achados com evidência recalculada e grau de confiança |
| Hipóteses levantadas | §6 · 💡 | H-01…H-06, refutáveis |
| Conclusões validadas | §2.3, §4.3 · 🧪 | Teste + IC + tamanho de efeito, nunca leitura visual isolada |

---

## 10. Conclusão

A base curada da Etapa 1 é de qualidade estrutural alta e **está apta à modelagem**, com três ressalvas que precisam ser respeitadas: truncar a série em 2026-06-23 para qualquer análise temporal, tratar os valores-sentinela como ausência e não como categoria, e codificar `tracado_via` como multi-hot.

Para a Etapa 3, a EDA entrega: um alvo definido e justificado (`grave_bin`, 28,28%), um mapa completo de vazamento por coluna, um conjunto de variáveis estruturais seguras com força de associação medida, a unidade espacial recomendada (trecho BR × km) e seis hipóteses refutáveis. O alerta mais importante que esta etapa produz é metodológico: as variáveis mais correlacionadas com a gravidade são exatamente as que não podem ser usadas, e a maior "tendência" aparente da série era um artefato de coleta. Ambos só apareceram porque a análise foi além do gráfico e perguntou de onde o número vinha.
