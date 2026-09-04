# Etapa 2 — Análise Exploratória de Dados (EDA)

**Projeto:** Predição de Risco de Acidentes em Rodovias Federais (base PRF + feriados ANBIMA)
**Código:** [`src/eda/utils.py`](../../src/eda/utils.py) · [`src/eda/run.py`](../../src/eda/run.py) · [`app/`](../../app/)
**Evidências:** [`reports/eda/eda_results.json`](../../reports/eda/eda_results.json) (37 blocos) · [`reports/eda/tables/`](../../reports/eda/tables/) (26 CSVs) · [`reports/data_quality/`](../../reports/data_quality/) · [`reports/gold/`](../../reports/gold/)
**Documentos relacionados:** [`docs/analises/EDA.md`](../analises/EDA.md) · [`docs/analises/ANALYSIS_LOG.md`](../analises/ANALYSIS_LOG.md) · [`docs/decisoes/DECISIONS.md`](../decisoes/DECISIONS.md) (D-01…D-14) · [`docs/analises/DATA_QUALITY.md`](../analises/DATA_QUALITY.md) · [`docs/GLOSSARIO.md`](../GLOSSARIO.md)
**Base analisada:** 311.751 acidentes × 30 colunas (2022-01-01 a 2026-07-31) + 63 feriados nacionais

> Nenhum número deste documento foi digitado à mão: todos vêm de `python src/eda/run.py`, que grava `reports/eda/eda_results.json`. O dashboard consome as mesmas funções de `src/eda/utils.py`, então documento e aplicação não podem divergir.

> **Como ler:** este documento não descreve gráfico por gráfico. Cada seção responde à sequência **o que descobrimos → o que isso significa → que decisão gerou → como isso afeta a Etapa 3**. Os gráficos do dashboard e os CSVs em `reports/eda/` são a evidência por trás das afirmações, não o roteiro.

---

## 1. Objetivo da EDA

O problema é prever **quais condições e locais estão associados a acidentes de maior gravidade**, para priorizar ações de segurança viária. Isso é um problema de classificação: dado um acidente (ou um trecho/período), qual a probabilidade de ele ser **grave ou fatal**?

A EDA existe para responder três perguntas que precedem qualquer modelo:

1. **A base é confiável o suficiente para sustentar uma previsão?** Onde ela mente, onde ela falta, e o que isso invalida.
2. **O que existe de sinal real na base?** Quais variáveis se relacionam com a gravidade, com que força, e quais relações são artefato.
3. **O que pode virar feature?** Nem toda variável associada à gravidade pode ser usada para prever — a separação entre o que é conhecido *antes* do acidente e o que só existe *depois* é o eixo central desta etapa.

O que **não** é escopo aqui: treinar modelos, definir partições de treino/teste ou otimizar métricas. A EDA entrega o diagnóstico e as decisões que tornam a modelagem defensável.

---

## 2. Caracterização da base

| Dimensão | Valor |
|---|---|
| Registros | 311.751 acidentes |
| Colunas | 30 |
| Período | 2022-01-01 a 2026-07-31 (2026 parcial) |
| Unidade de análise | **1 linha = 1 acidente (ocorrência)** — não é uma linha por pessoa nem por veículo |
| Volume por ano | 64.606 (2022) · 67.766 (2023) · 73.156 (2024) · 72.529 (2025) · 33.694 (2026, parcial) |
| Fonte complementar | 63 feriados nacionais (ANBIMA), usados para classificar cada dia do calendário |

A unidade de análise tem consequência prática: toda média de `mortos` ou `feridos` é **por acidente**, não por pessoa envolvida. Ler "média de 0,08 mortos" como taxa de letalidade individual seria erro de interpretação.

As 30 colunas se organizam em quatro grupos, e essa separação é o que estrutura toda a análise seguinte:

| Grupo | Colunas | Disponível antes do acidente? |
|---|---|---|
| **Identificação e tempo** | `id`, `data_inversa`, `dia_semana`, `horario` | Sim |
| **Localização e via** | `uf`, `br`, `km`, `municipio`, `latitude`, `longitude`, `tipo_pista`, `tracado_via`, `sentido_via`, `uso_solo`, `fase_dia` | Sim |
| **Circunstância apurada** | `causa_acidente`, `tipo_acidente`, `condicao_metereologica`, `classificacao_acidente` | **Não** — apuradas depois |
| **Consequências** | `pessoas`, `mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `veiculos` | **Não** — são o resultado |
| **Administrativas** | `regional`, `delegacia`, `uop` | Sim, mas descrevem a unidade da PRF, não o acidente |

**Target.** A base não traz uma variável de gravidade pronta e adequada. `classificacao_acidente` existe, mas tem apenas 3 níveis e mistura ferido leve com ferido grave na mesma categoria ("Com Vítimas Feridas") — justamente a distinção que o problema precisa fazer. A construção do alvo é tratada na seção 6.

---

## 3. Qualidade e limitações

A limpeza da Etapa 1 entregou uma base tecnicamente íntegra: **0 IDs duplicados, 0 linhas integralmente duplicadas**, e nulos declarados apenas em três colunas administrativas — `regional` (1,01%), `delegacia` (1,03%) e `uop` (1,08%), que identificam a unidade da PRF e não o acidente.

Isso é exatamente o motivo pelo qual a avaliação de qualidade não podia parar em `isnull().sum()`. Os problemas reais desta base **não aparecem como nulo**.

### 3.1 Valores-sentinela: "não informado" disfarçado de valor válido

| Evidência | Impacto | Decisão |
|---|---|---|
| `tracado_via` é multivalorada em **70.204 registros (22,52%)** — ex.: `"Reta;Declive"` numa única string | Tratada como categórica simples, a coluna aparenta ter mais de mil "categorias" que na verdade são combinações de poucas primitivas. One-hot direto produziria matriz esparsa inútil | Decompor em **multi-hot**: uma coluna binária por primitiva (12 no total), não one-hot da string |
| `km <= 0` em **1.496 registros (0,48%)** | Zero não é posição real de rodovia; entra em qualquer média como se fosse | Manter a linha, marcar com flag `km_valido` e converter o valor para nulo — **D-04** |
| `br = 0` em **788 registros (0,25%)** | Não existe BR-000; vira "rodovia" fantasma em qualquer ranking por rodovia | Excluir de rankings por rodovia, com flag `br_valido` — **D-05** |
| `condicao_metereologica` = "Ignorado" em **4.108 registros (1,32%)** | Categoria de ausência tratada como condição climática real | Preservada como categoria explícita; a variável acabou descartada por outro motivo (seção 6) |
| Coordenadas zeradas | Ponto no Golfo da Guiné entra em mapas e médias geográficas | Flag `geocoord_valido`, valor convertido para nulo |

O princípio aplicado em todos os casos: **sinalizar sem descartar**. Nenhuma linha foi removida por conter sentinela — a informação de que o dado está ausente é ela própria um dado.

### 3.2 Inconsistência interna não resolvida

**Evidência:** em **16.817 registros (5,39%)**, `pessoas` não é igual à soma de `mortos + feridos_leves + feridos_graves + ilesos + ignorados`.

**Impacto:** não é possível saber qual lado está errado — se `pessoas` foi mal preenchido ou se falta alguém nas categorias. Qualquer correção automática seria invenção.

**Decisão (D-03):** nada foi imputado. A consequência prática está registrada e vale para a Etapa 3: **usar as colunas de vítimas diretamente, nunca `pessoas` como total exato**.

Em contrapartida, duas checagens de coerência passaram integralmente: `feridos = feridos_leves + feridos_graves` e a correspondência entre `classificacao_acidente` e as contagens de vítimas. É essa segunda que sustenta derivar o alvo a partir de `mortos`/`feridos_graves` com confiança.

### 3.3 Outliers: o método precisou mudar conforme a distribuição

As variáveis de contagem são fortemente assimétricas e concentradas em zero — `mortos` tem assimetria **10,75**, `pessoas` **11,22**, `ilesos` **13,15**. Nessas condições o IQR degenera: com Q1 = Q3 = 0, **qualquer valor acima de zero vira "outlier"**.

O efeito é mensurável: para `feridos_graves`, o IQR sinaliza **70.600 registros (22,65%)** como anômalos, enquanto o z-score sinaliza **2.652 (0,85%)**. Sinalizar um quarto da base como anomalia não é detecção, é ruído.

**Decisão (D-06):** z-score para as contagens raras (`mortos`, `feridos_graves`), IQR reservado para variáveis de distribuição mais simétrica, como `km` (assimetria 1,00). **Nenhum outlier foi removido** — todos foram classificados (seção 4.6).

### 3.4 Cobertura temporal: o achado de maior impacto

**Evidência:** o calendário esperado tem 1.673 dias; a base tem registro em 1.665. Os **8 dias ausentes** não estão espalhados — concentram-se todos em julho de 2026. Além disso, a média móvel de 7 dias despenca no fim da série: os últimos **38 dias** somam apenas **492 acidentes**, contra uma mediana histórica de **188 acidentes/dia**.

**Interpretação:** nenhuma melhoria de segurança viária produz esse formato. É a assinatura de **registro administrativo ainda não consolidado na fonte** — ocorrências que ainda serão inseridas.

**Impacto:** severo e não óbvio. No recorte bruto jan–jul, 2026 aparece com **−17,9%** de acidentes em relação a 2025 (33.694 contra 41.017). Um relatório que publicasse essa queda estaria descrevendo atraso de preenchimento, não realidade das rodovias.

**Decisão (D-13):** truncar a série em **2026-06-23** para qualquer análise de tendência. Comparando somente a janela consolidada (1º de janeiro ao dia 174 de cada ano), a variação de 2026 é de **−0,43%** — oscilação ordinária, não colapso. Este corte deixou de ser filtro opcional de interface e passou a ser aplicado na própria camada de dados (Silver), removendo 492 linhas de 311.751 (**0,16%**).

Isso também obrigou a revisar a decisão anterior **D-12**: recortar jan–jul *não* resolvia o problema, porque junho e julho de 2026 estão dentro do trecho não consolidado.

### 3.5 Limitação estrutural: falta o denominador de exposição

A base registra **ocorrências**, não tráfego. Não há volume de veículos·km por trecho, UF ou horário.

**Consequência:** não é possível afirmar que uma rodovia é *perigosa* — apenas que nela ocorrem muitos acidentes, o que pode refletir simplesmente movimento. Nenhuma técnica estatística supre a ausência do dado.

**Decisão:** todas as comparações desta EDA são de **proporção de gravidade dado que houve acidente** — uma pergunta legítima, respondível com o que existe, e independente do tráfego. Risco *por viagem* fica fora de escopo até que dados de contagem volumétrica (DNIT/ANTT) sejam incorporados.

---

## 4. Principais descobertas

### 4.1 O volume oscila entre anos; a gravidade não

Na série completa, a proporção de acidentes graves ou fatais fica entre **27,98% e 28,49%** ao longo dos cinco anos — amplitude de meio ponto percentual, enquanto o volume anual variou vários pontos.

**Interpretação:** a gravidade condicional (dado que houve acidente, qual a chance de ser grave) é característica **estrutural e estável** do sistema viário, não algo que oscila ano a ano. Duas consequências: (a) não há evidência de melhora nem de piora no período; (b) para a modelagem, isso é um sinal favorável — a relação entre features e alvo não parece estar mudando ao longo do tempo, o que torna uma partição temporal defensável na Etapa 3.

### 4.2 Sazonalidade existe — mas é de volume, não de gravidade

O padrão mensal **se repete entre anos**: a correlação de Spearman média entre os rankings mensais dos quatro anos completos (2022–2025) é **ρ̄ = 0,845**. O mesmo mês tende a ocupar a mesma posição todo ano, o que distingue sazonalidade real de oscilação aleatória.

Só que a associação entre `mes` e gravidade é **Cramér's V = 0,008** — praticamente nula.

**Interpretação:** o calendário ajuda a prever **quantos** acidentes acontecerão, não **quão graves** eles serão. Para um classificador de gravidade, features de mês têm pouco a oferecer; elas fariam sentido em um modelo de volume/exposição, que é outro problema.

### 4.3 Feriado desloca exposição, não gravidade

| Tipo de dia | Dias | Acidentes/dia | % grave |
|---|---|---|---|
| Dia comum | 1.475 | 190,24 | 28,23% |
| **Véspera de feriado** | 51 | **201,18** | 28,78% |
| Feriado | 57 | 188,70 | 28,45% |
| Pós-feriado | 52 | 185,44 | 28,77% |

A véspera concentra **+5,75%** de acidentes por dia em relação a um dia comum (Mann-Whitney, p = 0,0037). O feriado em si fica estatisticamente indistinguível do dia comum (−0,81%, p = 0,774).

Já para a **gravidade**, a diferença da véspera é de **+0,55 p.p. com IC95% de −0,34 a +1,44** — o intervalo cruza o zero.

**Interpretação:** contraria a intuição de que "feriado é mais perigoso". O que muda é **quantos** acidentes ocorrem, no movimento de saída da véspera — não o quão graves eles são. Em termos de negócio, isso aponta fiscalização preventiva na véspera, e não no feriado.

**Ressalva honesta:** feriados não se distribuem uniformemente pelos dias da semana, e o dia da semana tem efeito próprio. A comparação acima não controla isso, então o efeito de véspera permanece como achado com confundidor conhecido.

### 4.4 Características da via: o achado estrutural mais forte

**Pista simples: 33,79% de acidentes graves (n = 151.529) contra 23,35% em pista dupla (n = 130.753).** Diferença de **+10,44 p.p.** (IC95%: 10,11 a 10,78), razão de risco **1,45×**.

É o maior efeito entre as variáveis disponíveis *antes* do acidente, e é consistente com o mecanismo físico conhecido: sem separação de fluxos, a colisão frontal — o tipo mais letal — torna-se possível.

**Nota de calibração:** o *h* de Cohen desse efeito é 0,232, classificado como "pequeno". Ou seja: a direção é inequívoca e a diferença é grande em termos práticos (10 pontos percentuais), mas `tipo_pista` sozinha não separa acidentes graves dos demais. Ela contribui em conjunto com as demais variáveis estruturais.

### 4.5 Escuridão agrava — e o pico de risco não é o pico de volume

**Plena noite: 32,57% de acidentes graves (n = 107.904) contra 25,29% em pleno dia (n = 171.615)** — diferença de **+7,27 p.p.** (IC95%: 6,93 a 7,62).

Aqui está uma das confusões mais fáceis de cometer na base: o pico de **volume** é no fim da tarde (hora do rush), mas o pico de **gravidade relativa** é noturno. Quem olha só a contagem por hora conclui que o perigo é às 18h.

`fase_dia` tem a vantagem de ser derivável da hora e da data, então entra na modelagem sem risco de vazamento. Novamente, magnitude modesta (*h* = 0,161): é contribuição, não separação.

### 4.6 Anomalias: classificadas, nenhuma removida

O critério de IQR sobre a série diária sinaliza **42 dias (2,52%)** acima do limite superior. Em vez de tratá-los como ruído, cada um foi classificado:

- **Evento sazonal real:** os maiores picos concentram-se em dezembro e **recorrem em anos diferentes** — 2024-12-21 (319 acidentes), 2023-12-23 (303), 2025-12-20 (285), 2024-12-22 (281), 2023-12-16 (280). Recorrência entre anos distingue padrão de acaso.
- **Inconclusivo:** 2024-10-20 (282 acidentes) aparece entre os maiores picos, mas **não recorre** na mesma data em nenhum outro ano, e nenhuma variável da base explica o dia. Fica registrado como anomalia não explicada — e **não foi removido**.

**Decisão:** a base não é "limpa" de outliers. Remover picos reais de dezembro destruiria justamente o sinal sazonal que a seção 4.2 documenta.

### 4.7 Geografia: parte da diferença é composição, não risco

O Maranhão aparece com **46,25%** de acidentes graves contra **28,28%** nacional. É diferença grande demais para aceitar sem investigar.

Padronizando o MA pela composição nacional de `tipo_pista` — isto é, recalculando sua taxa como se ele tivesse a mesma proporção de pista simples/dupla do país — a taxa cai para **41,23%**. Cerca de **28% do excesso** se explica apenas por o MA ter proporcionalmente muito mais pista simples.

**Interpretação:** o excesso remanescente é real e grande, mas a base não permite atribuí-lo a uma causa. Candidatos plausíveis e **não medidos**: tempo de resposta do socorro (que converte ferido grave em óbito), perfil de velocidade, densidade de fiscalização. Isso é prioridade de investigação, nunca "MA dirige pior".

Vale como alerta metodológico geral: comparações geográficas brutas nesta base carregam confundimento de composição, e trechos com poucos acidentes têm intervalo de confiança largo demais para sustentar ranking.

---

## 5. Estatística e relações

Cada método foi escolhido por uma característica concreta dos dados, não por convenção.

**Frequências e proporções.** A pergunta central da EDA é sobre proporção de gravidade por grupo — por isso quase toda comparação é de taxa (`% grave`), acompanhada de `n`. Contagem absoluta reflete exposição, não risco.

**Estatística descritiva (média, mediana, desvio, assimetria).** Serviu principalmente para **detectar a forma da distribuição**, não para descrever tendência central. Foi ela que revelou a assimetria extrema (`mortos` = 10,75) e justificou a mudança de método na detecção de outliers e nos testes.

**Cramér's V para força de associação.** Com n ≈ 312 mil, praticamente qualquer diferença sai "estatisticamente significante" — vários p-valores são exatamente 0. O p-valor perde utilidade como filtro. O V corrigido mede a **força** da associação, e é ele que ordena a lista (**D-08**):

| Variável | Cramér's V | Disponível antes do acidente? |
|---|---|---|
| `tipo_acidente` | 0,300 | **Não** |
| `causa_acidente` | 0,243 | **Não** |
| `br` | 0,110 | Sim |
| `uf` | 0,105 | Sim |
| `uso_solo` | 0,098 | Sim |
| `hora` | 0,097 | Sim |
| `tipo_pista` | 0,095 | Sim |
| `fase_dia` | 0,081 | Sim |
| `sentido_via` | 0,050 | Sim |
| `tracado_via` | 0,047 | Sim |
| `dia_semana` | 0,042 | Sim |
| `condicao_metereologica` | 0,034 | Não (exigiria previsão) |
| `mes` | 0,008 | Sim |

**Spearman (não Pearson) entre numéricas.** As variáveis de contagem não são normais nem lineares; Spearman mede relação monotônica sem exigir isso. O resultado relevante: `pessoas × veiculos` tem ρ = 0,704 — forte, mas trivial (mais veículos, mais pessoas). As correlações com `mortos` são fracas (ρ ≤ 0,13), reforçando que gravidade não é função simples de contagem.

**Kruskal-Wallis para comparar distribuições entre níveis de gravidade.** Escolhido no lugar da ANOVA porque as contagens são assimétricas e zero-infladas — a ANOVA assumiria normalidade que os dados não têm.

**Teste de duas proporções com IC e tamanho de efeito.** Toda afirmação do tipo "A é mais grave que B" foi submetida a teste z com intervalo de confiança de Wilson e *h* de Cohen (**D-14**). O IC é o que permite dizer, no caso da véspera de feriado, que a diferença de gravidade **não é distinguível de zero**.

**Padronização direta para controle de composição.** Aplicada no caso do MA (seção 4.7). É o antídoto ao paradoxo de Simpson: separa "esse grupo é mais perigoso" de "esse grupo apenas concentra mais do que já é perigoso em qualquer lugar".

> **Associação não é causalidade.** Nenhum achado deste documento é enunciado como causa. Todas as relações são observacionais, e há confundidores conhecidos e não medidos (fluxo de veículos, fiscalização, tempo de resgate) fora desta base.

---

## 6. Target e leakage

### 6.1 Por que `classificacao_acidente` não bastava

A coluna original tem 3 níveis: "Sem Vítimas", "Com Vítimas Feridas", "Com Vítimas Fatais". O problema está no nível do meio: ele agrupa **ferido leve e ferido grave na mesma categoria** — exatamente a distinção que o projeto precisa capturar. Um acidente com arranhão e outro com politraumatismo entram juntos.

### 6.2 Construção do alvo (D-01, D-02)

Derivamos duas variáveis a partir das contagens de vítimas, que a seção 3.2 mostrou serem coerentes com a classificação oficial:

- **`gravidade_4`** — 4 níveis ordenados: `Fatal` (mortos > 0) → `Grave (não fatal)` (feridos_graves > 0) → `Leve` (feridos_leves > 0) → `Sem vítimas`.
- **`grave_bin`** — alvo binário: **1** se `mortos > 0` **ou** `feridos_graves > 0`.

| `gravidade_4` | Registros | % |
|---|---|---|
| Leve | 173.003 | 55,49% |
| Grave (não fatal) | 65.746 | 21,09% |
| Sem vítimas | 50.581 | 16,22% |
| Fatal | 22.421 | 7,19% |

**Distribuição do alvo binário:** 88.167 graves (**28,28%**) contra 223.584 não graves (71,72%) — razão aproximada de **2,5 : 1**.

**Interpretação do desbalanceamento:** é moderado, não extremo. Não exige reamostragem agressiva, mas **inviabiliza acurácia como métrica**: um modelo que classificasse tudo como "não grave" acertaria 71,72% sem prever nada. Por isso a Etapa 3 deve avaliar por **Precision, Recall, F1 e PR-AUC da classe grave**, conforme já definido no escopo do projeto.

### 6.3 Leakage: a descoberta que mais restringe a modelagem

O resultado mais importante da tabela de associações da seção 5 não é qual variável lidera — é **quais** lideram:

> `tipo_acidente` (V = 0,300) e `causa_acidente` (V = 0,243) são as duas variáveis mais associadas à gravidade, com folga sobre a melhor variável disponível a priori (`br`/`uf`, V ≈ 0,11). **E são justamente as que não podem ser usadas.**

Ambas só existem **depois** da apuração do acidente. No momento em que a previsão precisa ser feita, elas não estão disponíveis.

Este é o ponto que a EDA precisa deixar explícito: **força de associação não é critério de seleção de feature**. Selecionar variáveis por correlação produziria um modelo excelente na validação e inútil na prática — ele estaria "prevendo" a gravidade a partir de informação que só existe porque o acidente já aconteceu e já foi investigado.

**Decisão (D-07):** o critério de inclusão é **disponibilidade no momento da previsão**, não associação. As colunas classificadas como pós-evento e excluídas do conjunto preditivo:

- **Consequências do acidente:** `mortos`, `feridos_leves`, `feridos_graves`, `feridos`, `ilesos`, `ignorados`, `pessoas`, `veiculos` — usadas apenas para *construir* o alvo.
- **Apuração posterior:** `classificacao_acidente`, `causa_acidente`, `tipo_acidente`.
- **Não conhecida a priori:** `condicao_metereologica` — exigiria previsão meteorológica no momento da inferência, e tem sinal fraco (V = 0,034).

Essa proteção não ficou apenas documentada: virou **verificação automática**. A construção do dataset final falha ruidosamente se qualquer coluna dessa lista aparecer entre as features, e o teste correspondente roda na suíte do projeto.

---

## 7. Decisões para a próxima etapa

Consolidação do que a EDA decidiu, com o registro completo em [`docs/decisoes/DECISIONS.md`](../decisoes/DECISIONS.md).

| Tema | Decisão | Origem |
|---|---|---|
| **Alvo** | `grave_bin` (fatal ou ferido grave) como target binário; `gravidade_4` preservado para análise | D-01, D-02 |
| **Corte temporal** | Série truncada em **2026-06-23**; aplicado na camada de dados, não como filtro de interface | D-13 |
| **Comparação entre anos** | Sempre em janela comparável; nunca total bruto de 2026 | D-12 |
| **Sentinelas** | `km ≤ 0`, `br = 0` e coordenada zerada viram nulo **com flag de validade** — linha preservada | D-04, D-05 |
| **`tracado_via`** | Decomposta em **12 colunas multi-hot** (uma por primitiva), não one-hot da string | seção 3.1 |
| **Inconsistência `pessoas`** | Não imputada; usar as colunas de vítimas diretamente | D-03 |
| **Anomalias** | Nenhuma removida; classificadas como sazonal real ou inconclusiva | D-06 |
| **Features descartadas** | 11 colunas pós-evento + `condicao_metereologica` + administrativas (`regional`, `delegacia`, `uop`) | D-07 |
| **Critério de avaliação** | Precision/Recall/F1/PR-AUC da classe grave — nunca acurácia | seção 6.2 |

**Conjunto candidato resultante.** O dataset preparado para a Etapa 3 tem **311.259 linhas** (após o corte de consolidação) com **31 features**, 3 colunas de identificação (`id`, `data_inversa`, `ano`, para permitir partição temporal e auditoria) e os 2 alvos:

- **Geografia e via:** `uf`, `br`, `br_valido`, `km`, `km_valido`, `municipio`, `latitude`, `longitude`, `geocoord_valido`, `tipo_pista`, `sentido_via`, `uso_solo`
- **Traçado (multi-hot):** 12 colunas `tracado_*`
- **Temporais:** `mes`, `dia_semana`, `fim_de_semana`, `hora`, `hora_sin`, `hora_cos`, `fase_dia`

`hora_sin`/`hora_cos` codificam a hora ciclicamente, porque a hora inteira não representa a continuidade entre 23h e 0h. A mesma transformação foi **descartada** para `mes` e `dia_semana`: o mês tem sinal quase nulo com gravidade (V = 0,008) e o dia da semana já é categórica de baixíssima cardinalidade.

`municipio` permanece como candidata apesar de ter mais de dois mil valores — a estratégia de codificação (target ou frequency encoding) fica deliberadamente para a Etapa 3, **depois** que a partição temporal existir, para não vazar estatística do conjunto de teste.

**Limitações que a Etapa 3 precisa carregar:** ausência de denominador de exposição (seção 3.5); confundidores não medidos em qualquer comparação geográfica (seção 4.7); e o fato de que as variáveis de maior sinal são inutilizáveis por leakage (seção 6.3) — o teto de desempenho alcançável com informação *a priori* é estruturalmente mais baixo do que a tabela de associações sugere.

---

## 8. Hipóteses para modelagem

Cada hipótese vem de um achado das seções anteriores e está escrita de forma refutável — com o que a confirmaria e o que a derrubaria.

| # | Hipótese | Base empírica | Confirma se | Refuta se |
|---|---|---|---|---|
| **H-01** | O histórico de gravidade do próprio trecho (BR × faixa de km) é a feature mais preditiva disponível a priori | `br` lidera as variáveis a priori (V = 0,110); trechos concentram características fixas não medidas que a UF dilui | Adicionar a taxa histórica do trecho (janela estritamente passada) eleva o PR-AUC sobre o modelo só com variáveis estruturais | O ganho desaparece sob corte temporal estrito — indicando que vinha de vazamento |
| **H-02** | Pista simples combinada com período noturno prevê gravidade melhor que a soma dos efeitos isolados | Os dois maiores efeitos a priori: +10,44 p.p. (pista) e +7,27 p.p. (noite), por mecanismos distintos | Termo de interação ou modelo de árvore supera o modelo aditivo nas mesmas features | O efeito conjunto é apenas a soma dos efeitos marginais |
| **H-03** | Prever **volume** e prever **gravidade** exigem modelos distintos | Sazonalidade forte no volume (ρ̄ = 0,845) e nula na gravidade (V = 0,008); feriado move volume, não gravidade | Features de calendário têm importância alta no modelo de volume e desprezível no de gravidade | Um único modelo multitarefa captura ambos sem perda |
| **H-04** | O excesso de gravidade do MA persiste após controlar todas as variáveis estruturais disponíveis | A padronização por `tipo_pista` explicou apenas 28% do excesso (46,25% → 41,23%) | O efeito de UF continua relevante em modelo que já contém pista, traçado, fase do dia e uso do solo | O efeito de UF desaparece com o conjunto completo de controles |
| **H-05** | Véspera de feriado aumenta exposição, não gravidade condicional | +5,75% de volume (p = 0,0037); gravidade +0,55 p.p. com IC cruzando zero | Flag de véspera melhora previsão de contagem e não melhora a de gravidade | A flag melhora o classificador de gravidade após controlar dia da semana |
| **H-06** | Agregados históricos de `causa_acidente`/`tipo_acidente` por trecho recuperam parte do poder preditivo sem vazamento | São as variáveis de maior associação (V = 0,300 e 0,243), indisponíveis no momento da previsão | Perfil histórico do trecho (ex.: % de colisões frontais nos 12 meses anteriores) melhora o modelo | O perfil não acrescenta nada além da taxa histórica de gravidade (H-01) |

**H-06 carrega o maior risco** e precisa de disciplina: implementada sem corte temporal estrito, ela reintroduz exatamente o leakage que D-07 evitou.

---

## 9. Conclusão

**O que aprendemos sobre a base.** Ela é tecnicamente íntegra — sem duplicidade, com nulos declarados apenas em colunas administrativas — mas sua qualidade real não estava onde um `df.info()` olharia. Os problemas que importam são valores-sentinela que passam por válidos, uma inconsistência interna de 5,39% que não pôde ser resolvida, e sobretudo uma janela final não consolidada capaz de inverter a leitura de tendência recente. Sobre o fenômeno em si, o achado mais robusto é a **estabilidade**: o volume de acidentes oscila, a proporção de acidentes graves não sai da faixa de 28%.

**A base está preparada para avançar?** Sim, com ressalvas explícitas. Há sinal real e mensurável em variáveis conhecidas antes do acidente — características da via (pista simples: +10,44 p.p.), período do dia (plena noite: +7,27 p.p.) e localização. O alvo está definido, verificado contra a classificação oficial e com desbalanceamento moderado (2,5:1) que não exige tratamento agressivo. O conjunto de features candidatas está fechado, documentado e protegido por verificação automática de leakage.

**Quais são as principais limitações.** Três, em ordem de impacto: (1) **não há denominador de exposição** — a base mede ocorrências, não tráfego, então "perigoso" e "movimentado" não são separáveis; (2) **as variáveis de maior sinal são inutilizáveis** — `tipo_acidente` e `causa_acidente` lideram a associação e são pós-evento, o que rebaixa estruturalmente o teto de desempenho alcançável; (3) **confundidores não medidos** — tempo de socorro, fiscalização e perfil de velocidade estão fora da base e afetam qualquer comparação geográfica.

**O que tem potencial e o que ficou de fora.** Entram 31 features: geografia e características físicas da via, o traçado decomposto em multi-hot, e o conjunto temporal com a hora codificada ciclicamente. Ficam de fora as 11 colunas pós-evento (usadas apenas para construir o alvo), `condicao_metereologica` (indisponível a priori e de sinal fraco), as colunas administrativas da PRF (descrevem a unidade, não o acidente) e as transformações cíclicas de mês e dia da semana (sem sinal que as justifique).

**Próximo passo — Etapa 3, Modelagem Preditiva.** O caminho está definido pelo que a EDA estabeleceu: partição **temporal** (defensável porque a relação entre features e alvo se mostrou estável no tempo), codificação de `municipio` decidida **após** a partição existir, engenharia de features guiada pelas hipóteses H-01 a H-06, baseline explícito antes de qualquer modelo complexo, e avaliação por **Precision, Recall, F1 e PR-AUC da classe grave** — nunca por acurácia. A pergunta que a Etapa 3 herda não é "qual modelo tem o melhor número", e sim **quanto risco de acidente grave é possível antecipar usando apenas o que se sabe antes de o acidente acontecer**.
