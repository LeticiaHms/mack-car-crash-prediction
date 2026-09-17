# Roteiro do apresentador · PreviVia

**Arquivo:** [`apresentacao.html`](apresentacao.html). Abrir direto no navegador, duplo clique resolve, não precisa de servidor.
**Duração alvo:** 10 minutos de apresentação mais 10 de perguntas.
**Controles:** `→` ou `Espaço` avança · `←` volta · `F` tela cheia · `Esc` sai · `Home` e `End` vão para o primeiro e o último slide.

> Os gráficos dos slides 6, 7 e 8 mostram o número exato quando o mouse passa por cima. Isso salva na hora das perguntas, se alguém pedir "e às 3 da manhã, quanto dá?".

## Os 14 slides

| # | Slide | Tempo |
|---|---|---|
| 1 | Capa | 25s |
| 2 | Problema e desafio | 50s |
| 3 | Arquitetura da solução | 45s |
| 4 | Ingestão e validação | 35s |
| 5 | Preparação dos dados | 45s |
| 6 | Dados revelam 1: hora do dia | 50s |
| 7 | Dados revelam 2: tipo de pista | 35s |
| 8 | Dados revelam 3: geografia | 35s |
| 9 | Construção do modelo | 65s |
| 10 | Comparação dos modelos | 40s |
| 11 | Principais resultados | 80s |
| 12 | Aprendizados e limitações | 50s |
| 13 | Próximos passos | 25s |
| 14 | Conclusão | 20s |

**Sugestão de divisão:** Thomas abre e apresenta dados (1, 2, 4 e 5); Letícia apresenta arquitetura e as três análises (3, 6, 7 e 8); Karina apresenta modelo, resultados e fechamento (9 a 14). Ajustem como preferirem, o roteiro funciona com qualquer divisão.

> **Regra de ouro do tempo:** se estiver atrasado, corte conteúdo dos slides **5** e **7**. Nunca corte o **11** (resultados) nem o **12** (limitações), que são os que a banca cobra.

---

## Três regras para não perder a banca

A banca não é toda de gente de dados.

1. **Diga o que o número significa antes de dizer o nome dele.** Primeiro "de cada 100 acidentes graves, o modelo apontou 56", depois "isso se chama recall". Nunca o contrário.
2. **Nunca use uma sigla sem traduzir na mesma frase.** Tem tradução pronta para cada uma no glossário abaixo.
3. **Toda métrica precisa de um ponto de comparação.** "F1 de 0,439" não diz nada sozinho. "0,439 contra 0,000 de um chute preguiçoso" diz tudo.

### Glossário de bolso

Use a coluna da direita em voz alta. A da esquerda é só para vocês se localizarem.

| Termo técnico | O que dizer |
|---|---|
| **Modelo** | Uma regra aprendida a partir dos dados antigos, usada para dar um palpite sobre um caso novo. |
| **Feature (variável)** | Uma informação que o modelo pode olhar: o estado, a rodovia, o quilômetro, a hora, o tipo de pista. |
| **Alvo** | A resposta que queremos prever: este acidente teve morto ou ferido grave, sim ou não? |
| **Classificação binária** | Um problema de sim ou não, e não de "quantos". |
| **Classe desbalanceada** | Um lado é muito mais raro que o outro. Aqui, só 28 de cada 100 acidentes são graves. |
| **Treino, validação e teste** | Treino é a matéria estudada, validação é o simulado, teste é a prova final, que só foi aberta no fim. |
| **Split temporal** | Estudamos com o passado e fomos avaliados no futuro, que é como a ferramenta seria usada de verdade. |
| **Recall** | De todos os acidentes graves que aconteceram mesmo, quantos o modelo conseguiu apontar. |
| **Precision** | De todos os alertas que o modelo deu, quantos estavam certos. |
| **F1** | Uma nota única que junta as duas anteriores. Só fica alta se as duas forem razoáveis. |
| **ROC-AUC** | A chance de o modelo dar nota de risco maior para um acidente grave do que para um não grave. 0,50 é cara ou coroa, 1,00 é perfeito. |
| **Baseline** | O chute preguiçoso de referência: responder sempre "não vai ser grave". É o mínimo que o modelo precisa superar. |
| **Falso negativo** | O acidente grave que o modelo deixou passar. É o erro caro. |
| **Falso positivo (alarme falso)** | O modelo alertou e não era grave. É o erro barato. |
| **Peso de classe** | Avisamos o modelo de que errar no lado raro dói mais, para ele não tomar o caminho preguiçoso de responder sempre "não grave". |
| **One-hot** | Transformar uma coluna de texto em várias colunas de sim ou não, porque modelo não lê palavra, lê número. |
| **Padronização** | Colocar números de escalas diferentes na mesma régua, para o quilômetro não pesar mais que a hora só por ter valor maior. |
| **Ensemble / Random Forest** | Em vez de uma árvore de decisão só, centenas delas votando. Aqui foram 200. |
| **Boosting / XGBoost** | Também são muitas árvores, mas cada uma nasce para corrigir o erro da anterior, em vez de todas votarem em paralelo. |
| **Hiperparâmetro / tuning** | Os botões de ajuste do algoritmo. Tuning é girar esses botões procurando resultado melhor. Nesta etapa, por decisão de escopo, **não** fizemos essa busca. |
| **Vazamento de dados (leakage)** | Deixar o modelo espiar uma informação que, na vida real, só existiria depois da resposta. É colar na prova. |

---

# Slide 1 · Capa · 25s

**Mensagem:** abrir por uma pergunta, não por apresentação pessoal.

> "Boa noite. O PreviVia parte de uma pergunta simples: dá para saber que um acidente tem alta chance de ser grave **antes** do socorro chegar? A base são os registros que a Polícia Rodoviária Federal publica abertos, de 2022 a 2026."

Apresentar os três integrantes em uma frase, dizer que é o MBA em Engenharia de Dados e passar adiante.

> **Não** liste tecnologias aqui. Elas aparecem no slide 3.

---

# Slide 2 · Problema e desafio · 50s

**Mensagem:** o problema não é a falta de dados, é a dificuldade de extrair padrão deles.

Ler o problema com as próprias palavras, sem decorar:

> "É difícil avaliar a segurança de uma viagem ou de uma via antes de percorrê-la. Existem milhares de registros históricos de acidentes, mas o volume e a complexidade desses dados dificultam identificar padrões ligados aos acidentes graves."

Depois o desafio, que é a frase em vermelho:

> "O desafio do projeto é transformar esses dados históricos em informação: identificar quais fatores aparecem associados à gravidade e apoiar a análise de segurança viária."

Percorrer as 4 etapas na base do slide apontando, sem ler uma a uma:

> "É o caminho de cima: temos milhares de registros, com volume e variedade grandes, o que gera dificuldade de achar padrão, e daí a necessidade de informação que apoie decisão."

> **Nota de cuidado:** este slide **não** traz nenhum resultado da análise de propósito. Ele descreve a situação de partida. Os números do estudo começam no slide 4. Se alguém perguntar "quantos acidentes graves existem?", responda que aparece no slide 8 e siga.

---

# Slide 3 · Arquitetura da solução · 45s

**Mensagem:** tudo é automatizado e reproduzível, ninguém digitou número à mão.

Percorrer o diagrama da esquerda para a direita, uma frase por bloco:

> "Na entrada, duas fontes públicas: os arquivos anuais da PRF e um calendário de feriados. Elas entram em quatro camadas dentro de um banco DuckDB. Raw é o dado como veio, sem tocar. Bronze é limpo e validado. Silver é enriquecido, já com feriado, fim de semana e a marcação de acidente grave. Gold é a tabela pronta que alimenta o modelo. Da Gold saem três consumos: a análise exploratória, a modelagem e o dashboard."

Fechar com a regra do projeto:

> "Um único comando reconstrói o banco inteiro do zero, em cerca de 40 segundos. Os arquivos originais nunca são alterados, são a única coisa que não dá para regenerar."

Citar a stack **uma vez só**, apontando a régua de baixo: Python, Pandas, DuckDB, scikit-learn, XGBoost, SciPy, Matplotlib, Plotly, Streamlit.

> **Nota: o que são Raw, Bronze, Silver e Gold?** É um padrão de organização em camadas, também chamado de arquitetura medalhão. A ideia é que cada camada tenha uma responsabilidade só e leia apenas a anterior, nunca pule etapas. Se precisar explicar em linguagem de cozinha: "Raw é o ingrediente como veio do mercado. Bronze é lavado e descascado. Silver é temperado. Gold é o prato pronto que vai para a mesa."
>
> **Nota: por que DuckDB e não um banco tradicional?** É um banco analítico que roda dentro do próprio processo, sem servidor para instalar ou configurar. Para um projeto acadêmico que precisa rodar na máquina de qualquer um do grupo, isso elimina toda a etapa de infraestrutura.

---

# Slide 4 · Ingestão e validação · 35s

**Mensagem:** antes de analisar, foi preciso provar que o dado é confiável.

Os quatro números de cima descrevem o tamanho do problema de dados:

> "São 311.751 registros, 30 variáveis em cada um, cinco anos de série e duas fontes públicas."

Depois as duas colunas, sem ler item por item:

> "A validação roda automaticamente a cada carga e confere quatro coisas: o schema, ou seja, se as colunas são as esperadas; os tipos de cada campo; nulos e intervalos; e a consistência entre colunas que deveriam fechar. Do lado direito está o que ela encontrou."

Dos três achados, narre **um** com calma, o terceiro:

> "Os últimos 38 dias da série têm só 492 acidentes, contra uma mediana histórica de 188 por dia. Isso não é queda de acidentes, é registro que a fonte ainda não consolidou. Sem esse diagnóstico, a conclusão seria exatamente o contrário da verdade."

> **Nota: o que é "schema"?** É a lista de colunas que o arquivo deveria ter, na ordem certa e com os tipos certos. Checar schema é confirmar que o arquivo deste ano tem o mesmo formato do arquivo do ano passado. Se a PRF mudar uma coluna de lugar, a validação acusa antes de qualquer análise sair errada.
>
> **Nota: se perguntarem quantas validações são.** São 42 checagens automáticas por carga, e o status da última execução é PASSOU. O número saiu do slide para não poluir, mas está em `reports/data_quality/verify_acidentes_report.json`.
>
> **Nota: o que é "mediana"?** O valor do meio. Metade dos dias tem mais que 188 acidentes, metade tem menos. Usamos mediana em vez de média porque um dia atípico de acidente em massa puxaria a média para cima e esconderia o problema.

---

# Slide 5 · Preparação · 45s

**Mensagem:** os dados não estavam prontos, e nem tudo que parece erro deve ser corrigido.

Não leia os seis cartões. Escolha **três** e narre:

1. **100% das linhas.** Quilômetro, latitude e longitude vinham escritos com vírgula, que o computador lê como texto e não como número. Sem converter, não existe geografia nenhuma.
2. **16.817 linhas mantidas.** O total de pessoas não bate com a soma das vítimas. Não corrigimos: não dá para saber qual dos dois campos está errado sem inventar dado. Ficou documentado.
3. **70.600 outliers mantidos.** Pelo critério estatístico, um acidente com ferido grave conta como caso extremo, porque na maioria esmagadora das linhas esse número é zero. Só que jogar os extremos fora seria apagar exatamente o fenômeno que queremos prever.

Fechar na caixa de baixo, que é o ponto alto do slide:

> "Tipo e causa do acidente são as informações mais ligadas à gravidade em toda a base. E nós as jogamos fora de propósito, porque elas só existem depois que o acidente aconteceu. Usá-las seria prever o que já aconteceu."

> **Nota: o que é "outlier"?** Um valor muito fora do padrão do restante da coluna. O critério estatístico usual marca como extremo tudo que foge muito do miolo dos dados. Como quase todo acidente tem zero ferido grave, qualquer acidente **com** ferido grave é matematicamente um extremo. Por isso o critério automático não serve aqui.
>
> **Nota: o que é "multi-hot" no cartão do traçado?** O campo traçado da via vem com vários valores juntos na mesma célula, tipo "Reta;Declive", em 22,52% dos registros. Em vez de tratar "Reta;Declive" como uma categoria diferente de "Reta", quebramos em 12 colunas de sim ou não, uma por característica. Assim o modelo entende que os dois casos têm "Reta" em comum.
>
> **Nota: este é o slide que explica o desempenho do modelo.** Se a banca depois perguntar por que o resultado não é maior, a resposta começa aqui.

---

# Slide 6 · Dados revelam 1: hora do dia · 50s

**Mensagem:** a hora com mais acidentes não é a hora mais perigosa.

Slide visual. Deixe o gráfico falar e **aponte** em vez de descrever.

Avise antes que os dois gráficos têm escalas diferentes:

> "São duas perguntas diferentes, por isso duas escalas. Não dá para sobrepor."

**Esquerda, o volume:**
> "Quantos acidentes acontecem em cada hora. O pico é às 18h, a hora do rush, e isso não surpreende ninguém."

**Direita, o risco:**
> "Agora outra coisa: de cada 100 acidentes daquela hora, quantos foram graves. O pico passa para as 19h, com 33,9%, e o risco fica alto a madrugada inteira, justamente quando quase não acontece acidente."

A frase que fecha:

> "Ou seja: contar acidentes aponta o lugar errado."

> **Nota: por que não juntar os dois gráficos?** Um está em número de acidentes, na casa dos milhares, o outro em porcentagem, de 20 a 36. Sobrepor os dois no mesmo eixo daria a impressão de que uma curva é maior que a outra, quando elas medem coisas incomparáveis.
>
> **Nota: a linha tracejada** no gráfico da direita é a média nacional, 28,3%. Serve para enxergar quais horas estão acima e abaixo do normal.

---

# Slide 7 · Dados revelam 2: tipo de pista · 35s

**Mensagem:** é o maior efeito que se conhece antes do acidente acontecer.

> "Em pista simples, aquela de mão dupla sem separação no meio, 33,8% dos acidentes são graves. Em pista dupla, 23,4%. É 1,45 vez mais risco."

Vale dizer por que isso faz sentido:

> "Sem separação entre os fluxos, a batida de frente se torna possível. O dado concorda com a física."

A coluna da direita é o contraponto e rende mais do que parece:

> "E aqui o que **não** se confirmou. O feriado, que todo mundo imagina ser mais perigoso, concentra mais acidentes na véspera, mas não acidentes mais graves. O mês do ano tem sazonalidade, só que de volume, não de gravidade. E o clima tem efeito pequeno, além de não ser conhecido com antecedência."

> **Nota: o que significa "1,45 vez mais risco"?** 33,8 dividido por 23,4 dá 1,45. É a razão entre as duas taxas. Se alguém pedir em outras palavras: a cada 100 acidentes, a pista simples produz cerca de 10 acidentes graves a mais que a pista dupla.
>
> **Nota: por que descartar o clima se ele é um fator real?** Duas razões. A associação medida é fraca, e a condição meteorológica registrada é a do momento do acidente, que não se conhece de antemão. Um modelo que precisa saber o clima exato do instante não serve para planejar com antecedência.
>
> **Nota: "exposição" versus "risco".** Exposição é quanta gente está na estrada. Risco é a chance de dar errado para quem está lá. O feriado muda a primeira, não a segunda.

---

# Slide 8 · Dados revelam 3: geografia · 35s

**Mensagem:** a fração de acidentes que termina grave varia muito entre os estados.

Apontar as duas pontas do gráfico:

> "Cada barra é uma unidade da federação, ordenadas da maior para a menor taxa de acidentes graves. A linha tracejada é a média nacional, 28,28%. No topo, o Maranhão, com 46,25%. Na outra ponta, São Paulo, com 18,63%."

E a ressalva, que é obrigatória:

> "Parte dessa diferença se explica por composição: o Maranhão tem proporcionalmente mais pista simples. Mas só parte. O resto a base não explica, e nós não vamos inventar explicação."

> **Nota: cuidado com a pergunta "então o Maranhão é mais perigoso?".** A resposta honesta é: os acidentes **registrados** lá terminam em desfecho grave com mais frequência. Isso pode ser característica das vias, pode ser tempo de socorro, pode ser perfil do tráfego, e pode ser diferença de registro entre estados. A base não distingue essas hipóteses.
>
> **Nota: isso não é contagem de acidentes.** É porcentagem. São Paulo tem muito mais acidentes que o Maranhão em número absoluto. O gráfico mostra a fração deles que termina grave, não o total.

---

# Slide 9 · Construção do modelo · 65s

**Mensagem:** decisões de método, não ficha técnica. Narre como uma sequência de escolhas.

Coluna da esquerda, de cima para baixo:

> "A pergunta é de sim ou não: este acidente vai ter morto ou ferido grave? O lado 'sim' é minoria, 88 mil em 311 mil, ou seja, 28%. O modelo olha 29 informações, todas conhecidas antes do desfecho: estado, rodovia, quilômetro, coordenadas, tipo de pista, traçado, hora e calendário."

Sobre o pré-processamento, traduza:

> "Antes de treinar, o dado passa por um preparo: texto vira coluna numérica, valor faltante recebe a mediana, e as escalas são igualadas. O detalhe importante é que essa regra é calculada **só** com os dados de treino. Validação e teste apenas aplicam a regra pronta."

Agora a barra, que é o centro do slide:

> "A divisão foi feita por data, não por sorteio. O modelo estudou com os 70% mais antigos, foi conferido nos 15% seguintes e só no fim abriu a prova final, os últimos 15%, que ele nunca tinha visto. Repare que a proporção de acidentes graves é praticamente a mesma nas três fatias, entre 27,9% e 28,7%, então o corte não distorceu a amostra."

Fechar na caixa:

> "Setenta por cento dá volume para aprender, e cada fatia de 15% ainda tem mais de 46 mil acidentes, o bastante para a medição ser confiável."

> **Nota: por que dividir por data e não sortear as linhas?** Porque os dados têm ordem no tempo. Se sorteássemos, o modelo estudaria com acidentes de 2026 e seria avaliado em acidentes de 2023, ou seja, aprenderia o futuro e seria cobrado sobre o passado. Na vida real a ferramenta sempre olha para frente. Se a banca cutucar, a frase pronta é: *"sortear ao acaso seria deixar o modelo estudar com a prova na mão."*
>
> **Nota: por que ajustar o pré-processamento só no treino?** Se a mediana usada para preencher valores faltantes fosse calculada sobre a base inteira, ela carregaria informação dos dados de teste para dentro do treino. É uma forma sutil de vazamento. Calculando só no treino, o teste continua sendo um dado genuinamente novo.
>
> **Nota: para que serve a validação se não houve tuning?** Boa pergunta, e pode aparecer. Como esta etapa não faz busca de hiperparâmetros, a validação não decide nenhum parâmetro. Ela serve como checagem intermediária: comparar o desempenho no treino com o da validação mostra se o modelo decorou ou generalizou, antes de gastar a prova final.
>
> **Nota: se perguntarem quais algoritmos.** Quatro: regressão logística, árvore de decisão, random forest e XGBoost. Eles aparecem na tabela do próximo slide, então não precisa listar aqui.

---

# Slide 10 · Comparação dos modelos · 40s

**Mensagem:** quatro abordagens diferentes pararam no mesmo lugar.

Não leia a tabela célula por célula. Aponte a linha destacada:

> "Quatro algoritmos, cinco métricas, todos avaliados na mesma prova final. O XGBoost lidera as cinco, e é o único dos quatro em que isso acontece."

E imediatamente relativize, que é o ponto do slide:

> "Só que a vantagem dele sobre o modelo mais simples, a regressão logística, é de 0,004 no F1. Entre o melhor e o pior dos quatro a diferença é de 0,012. Todos ficam na faixa de 0,61 a 0,63 de ROC-AUC."

A conclusão, com calma:

> "Quando quatro abordagens bem diferentes batem no mesmo teto, o gargalo não é o algoritmo. É a informação que os dados carregam."

> **Nota: o que significa "quatro caminhos diferentes"?** São quatro famílias de método: um modelo linear, que traça uma fronteira reta; uma árvore de decisão, que é uma sequência de perguntas do tipo "é pista simples?"; um random forest, que são 200 árvores votando em paralelo; e o XGBoost, em que cada árvore nova nasce para corrigir o erro da anterior. São lógicas distintas, e é isso que torna a convergência dos resultados significativa.
>
> **Nota: por que o XGBoost se ele não estava na lista da disciplina?** Os três primeiros cobrem linear, árvore única e ensemble por votação. Faltava testar o ensemble por correção sequencial, que é o tipo de algoritmo que costuma vencer esse tipo de problema. Incluímos justamente para saber se o teto era limitação do dado ou do tipo de modelo. Resposta: era do dado.
>
> **Nota: se perguntarem qual modelo vocês escolheriam na prática.** Resposta honesta: o XGBoost venceu, mas por margem pequena e consistente. Se o requisito fosse explicar cada decisão para um gestor, a regressão logística entrega quase o mesmo resultado sendo muito mais simples de justificar.

---

# Slide 11 · Principais resultados · 80s

**O slide mais importante. Fale mais devagar aqui.**

Comece pelo significado, e só depois dê o nome da métrica:

> "De cada 100 acidentes graves que realmente aconteceram na prova final, o modelo sinalizou corretamente 56. Só com informação disponível antes do desfecho. Essa métrica se chama recall."

Depois a linha de números, sempre com o ponto de comparação ao lado:

- F1 **0,439** contra **0,000** do chute preguiçoso.
- ROC-AUC **0,630** contra **0,500**, que é o resultado de cara ou coroa.
- Precision **36,1%**: de cada 3 alertas, 1 acerta.
- A queda do simulado para a prova final foi de **0,014**, ou seja, quase nada. O modelo não decorou.

Agora a armadilha da acurácia, que a banca costuma cutucar. **Atenção: a nossa acurácia é menor que a do chute preguiçoso, e isso é de propósito.**

> "Nosso modelo acerta 60% das vezes. Responder sempre 'não vai ser grave' acerta 72%. Parece que perdemos, só que esse chute de 72% não encontra **nenhum** acidente grave, que é justamente o que queremos achar. Trocamos acurácia por recall de propósito."

Depois os quatro números da direita, que é a parte concreta:

> "Os dois que importam são estes: 7.283 acidentes graves identificados, e 5.724 que passaram despercebidos. Os 12.908 alarmes falsos custam pouco, é fiscalizar um trecho que estava tranquilo. Deixar passar um acidente grave é o erro caro."

E o significado prático:

> "Na prática é uma ferramenta de triagem: serve para ordenar o que olhar primeiro, não para tomar decisão automática."

> **Nota: de onde sai o 72,1%?** Na prova final, 33.584 dos 46.591 acidentes não foram graves. Responder sempre "não grave" acerta exatamente essa fração. É o piso que qualquer modelo precisa superar em utilidade, ainda que não em acurácia.
>
> **Nota: por que acurácia engana aqui?** Acurácia é a fração de acertos no total. Quando um dos lados é raro, ela mede principalmente a raridade, não a capacidade do modelo. É o mesmo motivo pelo qual um teste que diz "você não tem a doença" para todo mundo acerta 99% das vezes numa doença rara, e é inútil.
>
> **Nota: por que aceitar 12.908 alarmes falsos?** Porque os custos são assimétricos. Um alarme falso gasta uma fiscalização num trecho tranquilo. Um falso negativo é um trecho de risco que ninguém olhou. Foi uma escolha consciente, feita através do peso de classe lá no slide 9.
>
> **Nota: se perguntarem "o modelo pode ser usado hoje?".** Como triagem, sim. Para decisão operacional, não: falta calibrar a probabilidade e ter critério de corte por região. Está no slide 13.

---

# Slide 12 · Aprendizados e limitações · 50s

**Mensagem:** este slide **ganha** pontos com a banca. Seja direto e honesto.

Dos quatro aprendizados, narre **dois** e deixe os outros na tela:

> "O primeiro é o principal: os dados são o limite. Modelos bem diferentes chegaram a resultados muito parecidos, o que indica que melhorar o dado rende mais do que trocar o algoritmo."

> "O segundo é o que mais mudou a nossa leitura: quantidade de acidente não significa gravidade maior. Uma região ou um horário pode concentrar muitos acidentes sem que eles sejam mais graves."

Passe para as limitações sem transição defensiva, com naturalidade:

> "E aqui o que ainda não podemos afirmar. A precisão é moderada: 0,63 de ROC-AUC mostra que existe padrão, mas não o bastante para cravar se uma viagem será segura. O modelo não conhece o histórico do trecho. Não temos fluxo de veículos, então não sabemos o risco por viagem, só por acidente registrado. Existem inconsistências que vêm da fonte. E, o mais importante: o que encontramos são associações, não causas."

> **Nota: a diferença entre "associação" e "causa", em uma frase.** Sabemos que acidentes em pista simples terminam graves com mais frequência. Não sabemos se é a pista que causa isso, ou se pistas simples ficam em regiões com socorro mais distante, ou tráfego mais pesado de caminhão. Nada aqui autoriza dizer que duplicar uma pista reduziria mortes.
>
> **Nota: o que é "risco por viagem" e por que não temos?** A base registra acidentes, não quantos veículos passaram por ali. Se uma rodovia tem muitos acidentes porque passa muito carro, isso é exposição, não perigo. Sem contagem de tráfego, não dá para separar as duas coisas.
>
> **Nota: não minimize as limitações na hora de falar.** Banca costuma testar se o grupo conhece os limites do próprio trabalho. Admitir o que não sabe vale mais do que defender o resultado.

---

# Slide 13 · Próximos passos · 25s

**Mensagem:** a evolução é incremental, não recomeço.

Cite **dois** da esquerda e **um** da direita, não leia a lista:

> "Os dois próximos passos com maior retorno são o histórico do trecho, que é a informação que falta hoje, e a calibração por região antes de qualquer uso operacional. Do lado da solução, o passo natural é evoluir o dashboard para um simulador de risco por trecho e horário."

Fechar na caixa:

> "O que já está pronto não é protótipo descartável: o pipeline é reprodutível, a base é auditada e o dashboard é navegável."

> **Nota: o que é "histórico do trecho"?** Hoje o modelo olha cada acidente isoladamente. Histórico do trecho seria dar a ele uma informação do tipo "neste quilômetro desta rodovia, 30% dos acidentes dos últimos 12 meses foram graves". É o ganho mais provável, e precisa ser construído com corte estrito de tempo para não virar vazamento.
>
> **Nota: o que é "calibração de probabilidade"?** O modelo dá uma nota de risco. Calibrar é fazer com que "70% de chance" signifique de fato que, entre os casos com essa nota, cerca de 70% terminem graves. Hoje a nota ordena bem, mas o valor absoluto não deve ser lido ao pé da letra.

---

# Slide 14 · Conclusão · 20s

> "Mais do que prever acidentes, o objetivo foi transformar cinco anos de registros públicos em conhecimento capaz de apoiar decisões melhores. Obrigado, abrimos para perguntas."

Não recapitule o trabalho todo. O slide já fecha sozinho.

---

# Perguntas prováveis e respostas curtas

| Pergunta | Resposta |
|---|---|
| **Por que o desempenho não é maior?** | Porque tiramos de propósito as duas informações mais preditivas, tipo e causa do acidente: elas só existem depois que o acidente aconteceu. O teto reflete o que dá para saber *antes*. |
| **Por que o XGBoost e não os outros?** | Ele lidera as cinco métricas, o único dos quatro nessa situação. Mas por margem pequena: 0,004 de F1 sobre a regressão logística. Se o critério fosse explicabilidade, a logística seria uma escolha legítima. |
| **Por que não testaram redes neurais?** | Escopo da etapa. E o resultado sugere que não mudaria muito: quatro famílias de algoritmo bem diferentes pararam todas na mesma faixa. O gargalo é o dado. |
| **Por que não houve tuning de hiperparâmetros?** | Decisão de escopo, declarada no código. Usamos os padrões de cada biblioteca com dois ajustes justificados: profundidade máxima, para conter decoreba, e peso de classe, para compensar o desbalanceamento. |
| **Por que a acurácia (60%) é menor que a do chute preguiçoso (72%)?** | Porque pedimos isso ao modelo. Com peso de classe, ele alerta mais e encontra 56% dos acidentes graves, em vez de 0%. A acurácia cai e o que interessa sobe. |
| **O que é recall, na prática?** | De todos os acidentes graves que aconteceram de verdade, a fatia que o modelo conseguiu apontar. É a métrica que importa aqui, porque deixar um grave passar é o erro caro. |
| **Como sabem que não há vazamento de dados?** | Três travas: divisão por tempo, todos os ajustes de pré-processamento calculados só sobre o treino, e uma trava na camada Gold que barra colunas que só existem depois do acidente, coberta por teste automatizado. |
| **O modelo pode ser usado hoje?** | Como triagem, sim. Para decisão operacional, não: falta calibrar a probabilidade e ter critério de corte por região. |
| **Correlação ou causa?** | Correlação. Nada aqui autoriza dizer que duplicar uma pista reduziria mortes, apenas que a associação é forte e consistente. |
| **O Maranhão é mais perigoso?** | Os acidentes registrados lá terminam graves com mais frequência. Parte disso é composição da malha, com mais pista simples. O resto a base não explica, e pode envolver tempo de socorro ou diferença de registro entre estados. |
| **De onde vêm esses números?** | De `reports/eda/` e `reports/ml/`, gerados por `python src/eda/run.py` e `python -m src.ml.modelagem`. Nenhum número foi digitado à mão. |
| **Quanto tempo leva para reproduzir?** | Cerca de 40 segundos para reconstruir o banco inteiro do zero, com um comando só. |

---

# Checklist antes de apresentar

- [ ] Abrir `apresentacao.html` no navegador e apertar `F` (tela cheia) **antes** de a banca entrar. O logo é desenhado no próprio arquivo, então não depende de imagem externa.
- [ ] Nada além do `apresentacao.html` precisa viajar junto. O logo é desenhado no próprio arquivo e o diagrama do slide 3 está embutido nele, então pendrive, e-mail ou outra máquina funcionam sem levar pasta nenhuma.
- [ ] Testar a resolução do projetor. O deck é 16:9 e se ajusta sozinho, sobrando tarja em telas de outra proporção, o que é o comportamento esperado.
- [ ] Passar rápido pelos slides 3, 6, 8 e 10 no projetor: são os de imagem, gráfico e tabela, os que mais sofrem com projetor ruim.
- [ ] Ter o dashboard rodando em outra aba (`python -m streamlit run app/app.py`) caso alguém peça para ver algo ao vivo.
- [ ] Cronometrar um ensaio completo. Se passar de 10 minutos, cortar conteúdo dos slides 5 e 7.
- [ ] Combinar quem responde o quê nas perguntas: dados e preparação, análise, modelo e métricas.
