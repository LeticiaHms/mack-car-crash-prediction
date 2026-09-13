# Glossário — termos estatísticos e técnicos do projeto

Este documento explica, em linguagem simples, todo termo técnico que aparece em [`EDA.md`](specs/eda/EDA.md), [`ANALYSIS_LOG.md`](ANALYSIS_LOG.md), [`DECISIONS.md`](DECISIONS.md), [`docs-etapas/etapa2-eda.md`](docs-etapas/etapa2-eda.md) e no dashboard Streamlit.

Cada verbete segue a mesma estrutura:

- **O que é** — a ideia, sem fórmula.
- **Como ler** — a regra prática para interpretar o número.
- **No projeto** — um exemplo real, com o valor que aparece na nossa análise.

Não é preciso ler na ordem: use o índice.

---

## Índice

**[1. Descrever os dados](#1-descrever-os-dados)** — média · mediana · moda · desvio-padrão · variância · coeficiente de variação · quartis · IQR · assimetria · curtose · distribuição zero-inflada · cardinalidade · tabela de contingência

**[2. Encontrar o que está fora do padrão](#2-encontrar-o-que-está-fora-do-padrão)** — outlier · z-score · método IQR · média móvel · tendência, sazonalidade e ruído · recorrência

**[3. Medir relações entre variáveis](#3-medir-relações-entre-variáveis)** — correlação · Pearson · Spearman · qui-quadrado · graus de liberdade · Cramér's V · associação ≠ causalidade

**[4. Saber se um achado é confiável](#4-saber-se-um-achado-é-confiável)** — proporção e taxa · ponto percentual · p-valor · significância estatística vs. prática · intervalo de confiança · IC de Wilson · teste z de duas proporções · razão de risco · h de Cohen · Kruskal-Wallis · ε² · Mann-Whitney · teste paramétrico vs. não-paramétrico

**[5. Comparar grupos sem se enganar](#5-comparar-grupos-sem-se-enganar)** — segmentação · confundidor · paradoxo de Simpson · padronização direta · exposição vs. risco · unidade de análise

**[6. Qualidade dos dados](#6-qualidade-dos-dados)** — NULL vs. zero vs. desconhecido · valor-sentinela · campo multivalorado · deduplicação · cobertura de calendário · janela não consolidada · camada raw e curada

**[7. Machine Learning](#7-machine-learning)** — variável-alvo · feature · data leakage · desbalanceamento · accuracy, precision, recall, F1 · ROC-AUC e PR-AUC · baseline · split temporal · one-hot, multi-hot e target encoding · matriz esparsa

**[8. Ferramentas](#8-ferramentas)** — Parquet · DuckDB · view · Streamlit · cache

---

## 1. Descrever os dados

### Média
**O que é:** a soma dos valores dividida pela quantidade deles.
**Como ler:** é sensível a valores extremos — um único caso gigante puxa a média para cima e ela deixa de representar o caso típico.
**No projeto:** a média de `mortos` por acidente é **0,084**. Mas a maioria absoluta dos acidentes tem zero mortos; a média só não é zero por causa de uma minoria de acidentes graves. Sozinha, ela engana.

### Mediana
**O que é:** o valor do meio quando você ordena todos os dados — metade fica abaixo, metade acima.
**Como ler:** representa o caso típico melhor que a média quando existem valores extremos, porque não se move quando o maior valor fica ainda maior.
**No projeto:** a mediana de `mortos` é **0**. Ou seja: o acidente típico não tem vítima fatal. Comparar média (0,084) e mediana (0) já revela que a distribuição é torta.

### Moda
**O que é:** o valor que mais se repete.
**Como ler:** útil em variáveis categóricas, onde média e mediana não fazem sentido.
**No projeto:** a moda de `tipo_acidente` é "Colisão traseira" (19,27% dos casos).

### Desvio-padrão
**O que é:** o quanto os valores costumam se afastar da média, na mesma unidade dos dados.
**Como ler:** desvio pequeno = dados agrupados perto da média; desvio grande = dados espalhados.
**No projeto:** `pessoas` tem média 2,60 e desvio 2,23 — os acidentes variam muito em número de envolvidos.

### Variância
**O que é:** o desvio-padrão elevado ao quadrado.
**Como ler:** mede a mesma coisa que o desvio-padrão, mas em unidade ao quadrado ("pessoas²"), o que é difícil de interpretar. Por isso reportamos o desvio-padrão.

### Coeficiente de variação (CV)
**O que é:** o desvio-padrão dividido pela média.
**Como ler:** permite comparar a dispersão de variáveis em escalas diferentes. Acima de 1, a variável é muito dispersa em relação ao seu próprio tamanho médio.
**No projeto:** `mortos` tem CV = **4,11** (extremamente disperso); `km` tem CV = 0,88 (comportado).

### Quartis (Q1, Q2, Q3)
**O que é:** os três cortes que dividem os dados ordenados em quatro partes iguais. Q1 = 25% dos dados abaixo dele; Q2 = a mediana; Q3 = 75% abaixo.
**Como ler:** a distância entre Q1 e Q3 mostra onde está "o miolo" dos dados.
**No projeto:** em `mortos`, Q1 = Q2 = Q3 = **0** — três quartos dos acidentes não têm nenhuma vítima fatal.

### IQR (intervalo interquartil)
**O que é:** Q3 − Q1, ou seja, a faixa onde estão os 50% centrais dos dados.
**Como ler:** é uma medida de dispersão que ignora as pontas, então não é afetada por casos extremos.
**No projeto:** o IQR de `mortos` é **zero**, e é por isso que o método de outliers baseado em IQR não funciona nessa coluna (ver [método IQR](#método-iqr)).

### Assimetria (*skewness*)
**O que é:** o quanto a distribuição pende para um lado.
**Como ler:** 0 = simétrica (como um sino). Positiva = cauda longa à direita (poucos valores muito altos). Acima de 1 já é bem assimétrica.
**No projeto:** `mortos` tem assimetria **10,75** — extremamente assimétrica à direita: quase tudo em zero e uma cauda rara de tragédias. `km` tem 1,00, bem mais comportada.

### Curtose
**O que é:** o quanto a distribuição tem "caudas pesadas", isto é, valores extremos mais frequentes do que uma curva normal teria.
**Como ler:** 0 = como a curva normal. Valores altos = eventos extremos acontecem mais do que o esperado.
**No projeto:** `mortos` tem curtose **560,4**. Traduzindo: acidentes catastróficos são raríssimos, mas acontecem muito mais do que uma distribuição normal preveria — como o acidente com 37 mortos em Teófilo Otoni/MG.

### Distribuição zero-inflada
**O que é:** uma distribuição em que o valor zero aparece muito mais do que qualquer outro.
**Como ler:** exige cuidado redobrado: mediana, quartis e IQR podem todos ser zero, quebrando as ferramentas estatísticas usuais.
**No projeto:** `mortos` e `feridos_graves` são zero-infladas — a razão pela qual usamos z-score em vez de IQR para detectar anomalias nelas ([D-06](DECISIONS.md#d-06)).

### Cardinalidade
**O que é:** quantos valores diferentes uma coluna tem.
**Como ler:** cardinalidade alta em variável categórica complica a modelagem (ver [one-hot](#one-hot-multi-hot-e-target-encoding)).
**No projeto:** `municipio` tem **2.057** valores distintos (2.052 deles aparecem em menos de 1% dos casos); `tipo_pista` tem 3.

### Tabela de contingência
**O que é:** uma tabela que cruza duas variáveis categóricas, mostrando quantos casos caem em cada combinação.
**Como ler:** as contagens brutas enganam quando os grupos têm tamanhos diferentes — sempre olhe também os percentuais por linha.
**No projeto:** `gravidade_4` × `tipo_pista` é a tabela que revela que pista simples tem 33,79% de acidentes graves contra 23,35% da pista dupla.

---

## 2. Encontrar o que está fora do padrão

### Outlier (valor atípico)
**O que é:** um valor muito distante dos demais.
**Como ler:** outlier **não é sinônimo de erro**. Pode ser erro de digitação, mas também pode ser um evento raro e verdadeiro — e no nosso caso é justamente o evento que queremos prever.
**No projeto:** nenhum outlier foi removido da base. Cada um foi classificado como *evento real plausível*, *problema de qualidade de dados* ou *inconclusivo*.

### Z-score (escore z)
**O que é:** quantos desvios-padrão um valor está distante da média. Um z-score de +3 significa "três desvios acima da média".
**Como ler:** a convenção é tratar |z| > 3 como valor extremo. Funciona bem quando a maior parte dos dados está agrupada e as exceções são raras.
**No projeto:** usado como critério primário de anomalia em `mortos` e `feridos_graves`, sinalizando 0,83% e 0,85% dos registros — números plausíveis para "acidentes catastróficos". Também usado para achar UFs atípicas: o Maranhão tem z = **+2,12** na taxa de gravidade, ou seja, está a dois desvios acima da média dos estados.

### Método IQR
**O que é:** a regra clássica de outlier, também chamada de "regra do 1,5×" — é atípico todo valor abaixo de `Q1 − 1,5×IQR` ou acima de `Q3 + 1,5×IQR`.
**Como ler:** funciona bem em distribuições razoavelmente espalhadas. **Degenera quando o IQR é zero**: se Q1 = Q3, a fórmula passa a sinalizar qualquer valor diferente de zero.
**No projeto:** em `feridos`, o IQR sinaliza **43,46%** das linhas como outlier — um resultado inútil, porque quase metade da base não pode ser "exceção". O z-score, na mesma coluna, sinaliza 1,25%. Foi essa comparação que motivou [D-06](DECISIONS.md#d-06). Já na série diária de acidentes o IQR funciona bem: limite superior de 278,5 acidentes/dia, com 42 dias (2,52%) acima dele.

### Média móvel
**O que é:** a média dos últimos N dias, recalculada dia a dia. Uma média móvel de 7 dias suaviza a série.
**Como ler:** separa o **movimento de fundo** do barulho do dia a dia. Uma janela de 7 dias também elimina o efeito de dia da semana, já que cada janela contém exatamente um de cada.
**No projeto:** é a média móvel de 7 dias que torna visível o colapso do registro no fim da série (janela não consolidada).

### Tendência, sazonalidade e ruído
**O que é:** as três partes de uma série temporal. **Tendência** é o movimento de longo prazo (crescer ou cair ao longo dos anos). **Sazonalidade** é o padrão que se repete em ciclos fixos (todo dezembro, toda sexta-feira). **Ruído** é a variação aleatória do dia a dia.
**Como ler:** confundir ruído com tendência é o erro mais comum em análise temporal — qualquer série sobe e desce por acaso.
**No projeto:** o volume de acidentes tem sazonalidade real (pico em março–maio, vale em setembro–novembro), mas a gravidade não tem nenhuma.

### Recorrência
**O que é:** o critério que adotamos para aceitar um padrão como sazonal: ele precisa **se repetir em anos diferentes**, não apenas aparecer uma vez.
**Como ler:** um pico isolado é ruído até prova em contrário; um pico que volta na mesma época todo ano é padrão.
**No projeto:** medimos a recorrência com a correlação de Spearman entre os rankings mensais de anos diferentes: **ρ̄ = 0,845**, ou seja, o mês que é alto num ano tende a ser alto nos outros. Já o pico de 2024-10-20 não se repete em nenhum outro ano e por isso foi classificado como **inconclusivo**, não como padrão.

---

## 3. Medir relações entre variáveis

### Correlação
**O que é:** o grau em que duas variáveis andam juntas.
**Como ler:** varia de −1 (quando uma sobe, a outra desce sem falha) a +1 (sobem juntas sem falha), passando por 0 (nenhuma relação).
**No projeto:** `pessoas` e `veiculos` têm correlação 0,70 — quanto mais veículos, mais gente envolvida, o que faz sentido óbvio. Já `km` e `mortos` têm 0,03: a posição na rodovia, sozinha, não diz nada sobre letalidade.

### Correlação de Pearson
**O que é:** a correlação clássica; mede se a relação entre duas variáveis é uma **linha reta**.
**Como ler:** sensível a valores extremos — um único acidente com 37 mortos pode dominar o coeficiente.
**No projeto:** evitada nas variáveis de contagem, justamente por causa das caudas extremas.

### Correlação de Spearman (ρ, "rho")
**O que é:** a mesma ideia, mas aplicada às **posições** (rankings) em vez dos valores brutos: o maior vira 1º, o segundo maior 2º, e assim por diante.
**Como ler:** captura relações que sobem juntas sem serem uma reta, e é imune a valores extremos.
**No projeto:** usada tanto nas correlações entre contagens quanto no teste de recorrência sazonal — ali interessa se o mês *ocupa a mesma posição* entre os anos, não se tem o mesmo número absoluto de acidentes (que cresce com o volume geral).

### Teste qui-quadrado (χ²) de independência
**O que é:** um teste que responde a uma pergunta binária: *as duas variáveis categóricas têm alguma relação, ou são independentes?* Ele compara as contagens observadas na tabela de contingência com as contagens que existiriam se as variáveis não tivessem relação nenhuma. Quanto maior a diferença, maior o χ².
**Como ler:** ele diz **se** existe relação, mas **não diz o quanto ela é forte** — e é aí que quase todo mundo erra. Com muitos dados, o χ² acusa relação em praticamente tudo.
**No projeto:** todos os 13 cruzamentos com a gravidade deram "relação existe" (p ≈ 0), inclusive o mês, cuja relação é irrelevante na prática. Por isso o χ² nunca é usado sozinho aqui — sempre acompanhado do Cramér's V.

### Graus de liberdade (gl)
**O que é:** um número que descreve o tamanho da tabela testada — quantas células podem variar livremente depois de fixados os totais.
**Como ler:** você não precisa interpretá-lo diretamente; ele serve para o teste saber qual é o valor de χ² "normal" para uma tabela daquele tamanho. Uma tabela maior naturalmente produz χ² maior.

### Cramér's V
**O que é:** a **força** da relação entre duas variáveis categóricas, numa escala de 0 a 1. É derivado do qui-quadrado, mas corrigido pelo tamanho da amostra e pelo tamanho da tabela.
**Como ler:** 0 = nenhuma relação; perto de 1 = relação muito forte. Como referência prática neste projeto: abaixo de 0,05 desprezível, 0,05–0,10 fraca, 0,10–0,20 moderada, acima de 0,20 relevante.
**No projeto:** é a medida que **ordena** as variáveis por importância. `tipo_acidente` = **0,300** (a mais forte), `br` = 0,110, `mes` = **0,008** (praticamente nula). Usamos a versão com correção de viés (Bergsma), sem a qual variáveis com muitas categorias — `br` tem 125 — pareceriam artificialmente mais fortes do que `tipo_pista`, que tem 3.

### Associação ≠ causalidade
**O que é:** o princípio de que duas variáveis andarem juntas **não** significa que uma cause a outra.
**Como ler:** sempre existem três explicações alternativas: pode ser coincidência, pode ser causa invertida, ou pode haver uma terceira variável causando as duas (ver [confundidor](#confundidor-variável-de-confusão)).
**No projeto:** pista simples tem mais acidentes graves. Isso **não** prova que a pista causa a gravidade — pistas simples também ficam em regiões com socorro mais distante, velocidade diferente e fiscalização diferente, e nada disso está na base. Nenhuma afirmação causal é feita em nenhum documento deste projeto.

---

## 4. Saber se um achado é confiável

### Proporção e taxa
**O que é:** a fração de casos com determinada característica, geralmente em percentual.
**No projeto:** "taxa de gravidade" significa sempre *a proporção de acidentes que foram graves ou fatais, entre os acidentes que aconteceram* — e não "quantos acidentes graves por quilômetro" ou "por viagem".

### Ponto percentual (p.p.)
**O que é:** a diferença entre dois percentuais.
**Como ler:** ir de 20% para 30% é uma diferença de **10 pontos percentuais**, mas um aumento de **50%**. Confundir os dois inflaciona ou desinfla resultados sem querer.
**No projeto:** pista simples tem +10,44 p.p. de acidentes graves em relação à pista dupla (33,79% vs. 23,35%) — o que equivale a 1,45× o risco.

### p-valor
**O que é:** a probabilidade de observar uma diferença deste tamanho (ou maior) **se na realidade não houvesse diferença nenhuma**. É uma medida de "isso pode ser só sorte?".
**Como ler:** p pequeno (convencionalmente < 0,05) = improvável que seja acaso. **O p-valor não diz o tamanho nem a importância do efeito** — só diz que ele provavelmente não é zero.
**No projeto:** com 311.751 registros, quase tudo dá p ≈ 0. Simulando sobre os próprios dados, uma diferença de apenas **0,25 p.p.** já sairia "significante" — uma diferença que nenhum gestor usaria para decidir nada. Por isso o p-valor aqui é só uma checagem de que o achado não é ruído, nunca o critério de prioridade ([D-08](DECISIONS.md#d-08)).

### Significância estatística vs. significância prática
**O que é:** duas coisas diferentes que a palavra "significante" confunde. **Estatística:** o efeito provavelmente não é zero. **Prática:** o efeito é grande o suficiente para mudar uma decisão.
**Como ler:** com amostra grande, tudo vira estatisticamente significante; com amostra pequena, nem um efeito enorme aparece. Nenhum dos dois casos fala sobre relevância.
**No projeto:** a diferença de gravidade entre plena noite e pleno dia é altamente significante (p ≈ 0) e ao mesmo tempo de magnitude **desprezível** pela escala de Cohen (h = 0,161). As duas afirmações são verdadeiras ao mesmo tempo, e reportamos as duas.

### Intervalo de confiança (IC)
**O que é:** uma faixa de valores plausíveis para a quantidade real, dado o que a amostra mostrou. Um IC de 95% significa: se repetíssemos o levantamento muitas vezes, ~95% dos intervalos construídos assim conteriam o valor verdadeiro.
**Como ler:** **intervalo estreito = estimativa precisa; intervalo largo = pouco dado, estimativa frágil.** Se o IC de uma *diferença* inclui o zero, os dados são compatíveis com "não há diferença".
**No projeto:** a taxa do Maranhão é 46,25%, com IC de **44,91% a 47,60%** — estreito, porque são 5.260 acidentes. Já em trechos de rodovia com 60 acidentes o intervalo fica largo o bastante para o trecho mudar completamente de posição no ranking, e é por isso que todo ranking do dashboard exibe barra de erro e o `n` do grupo.

### IC de Wilson
**O que é:** uma fórmula específica de intervalo de confiança para proporções.
**Como ler:** interpreta-se como qualquer IC. A vantagem sobre a fórmula clássica (Wald) é que ele não produz absurdos quando a proporção é próxima de 0% ou 100%, nem quando o grupo é pequeno — a fórmula clássica chega a devolver limites negativos ou acima de 100%.
**No projeto:** é o IC usado em todas as taxas de gravidade por UF, rodovia e trecho, precisamente porque muitos grupos são pequenos.

### Teste z de duas proporções
**O que é:** o teste que responde *"a taxa do grupo A é realmente diferente da taxa do grupo B, ou a diferença cabe no acaso?"*.
**Como ler:** devolve um p-valor, mas o que interessa mais é a **diferença com seu intervalo de confiança**: se o intervalo não cruza o zero, a diferença é real.
**No projeto:** pista simples vs. dupla → diferença de +10,44 p.p., IC de +10,11 a +10,78. O intervalo inteiro é positivo e estreito: a diferença existe e está bem estimada.

### Razão de risco (*risk ratio*)
**O que é:** a taxa de um grupo dividida pela do outro.
**Como ler:** 1,0 = risco igual; 1,45 = 45% mais provável; 0,5 = metade do risco. É mais intuitivo que a diferença em pontos percentuais, mas exagera quando as duas taxas são pequenas (dobrar de 0,1% para 0,2% é "2×" e continua irrelevante).
**No projeto:** acidentes em pista simples têm **1,45×** a chance de serem graves em relação à pista dupla.

### h de Cohen
**O que é:** uma medida de **tamanho de efeito** para diferença entre duas proporções — quantifica o quanto a diferença importa, independentemente do tamanho da amostra.
**Como ler:** convenção usual: abaixo de 0,2 desprezível, 0,2–0,5 pequeno, 0,5–0,8 médio, acima de 0,8 grande.
**No projeto:** é o contrapeso do p-valor. Pista simples vs. dupla dá h = 0,232 ("pequeno") apesar dos 10 pontos percentuais de diferença; plena noite vs. pleno dia dá h = 0,161 ("desprezível"). A leitura correta é: a **direção** desses efeitos é certa, mas nenhuma variável isolada distingue acidentes graves — o modelo precisará da combinação delas.

### Kruskal-Wallis
**O que é:** um teste que compara **três ou mais grupos** para saber se os valores de uma variável numérica diferem entre eles. É a versão da ANOVA que não exige que os dados sigam uma curva normal.
**Como ler:** devolve uma estatística H e um p-valor. H grande = os grupos são diferentes. Como qualquer teste, precisa vir acompanhado de tamanho de efeito.
**No projeto:** usado para testar se o número de veículos difere entre os níveis de gravidade (H = 7.371). Escolhido em vez da ANOVA porque `veiculos` tem curtose 650,7 — está longe de qualquer normalidade.

### ε² (épsilon quadrado)
**O que é:** o tamanho de efeito do Kruskal-Wallis: **que fração da variação** da variável numérica é explicada pela diferença entre os grupos.
**Como ler:** 0 = grupos idênticos. Referência: 0,01 pequeno, 0,06 moderado, 0,14 grande.
**No projeto:** um p-valor minúsculo com ε² minúsculo significa "a diferença existe e é detectável, mas é pequena demais para sustentar uma conclusão forte sozinha".

### Mann-Whitney (U)
**O que é:** o mesmo que Kruskal-Wallis, mas para exatamente **dois** grupos. Compara as posições dos valores em vez das médias.
**Como ler:** igual aos demais testes — p pequeno indica que os grupos diferem.
**No projeto:** usado para comparar o número de acidentes por dia em vésperas de feriado (201,2/dia) contra dias comuns (190,2/dia): p = 0,004. Escolhido porque contagens diárias não são normais e o grupo de vésperas é pequeno (51 dias).

### Teste paramétrico vs. não-paramétrico
**O que é:** testes **paramétricos** (média, teste t, ANOVA, Pearson) assumem que os dados seguem uma distribuição conhecida, geralmente a normal. Os **não-paramétricos** (Spearman, Kruskal-Wallis, Mann-Whitney) trabalham com posições/rankings e não fazem essa exigência.
**Como ler:** usar um teste paramétrico em dados que violam a suposição produz p-valores errados.
**No projeto:** com assimetrias de 10 e curtoses acima de 500, praticamente todas as variáveis de contagem violam a normalidade — daí a preferência sistemática pelos não-paramétricos.

---

## 5. Comparar grupos sem se enganar

### Segmentação
**O que é:** dividir os dados em grupos (por região, período, perfil) em vez de olhar só o número geral.
**Como ler:** a média global é a média de coisas muito diferentes. Ela pode não descrever nenhum grupo real.
**No projeto:** a taxa nacional de acidentes graves é 28,28%. Segmentando por estado, ela vai de 18,63% (SP) a 46,25% (MA) — quase o dobro do valor nacional em um caso, dois terços dele em outro.

### Confundidor (variável de confusão)
**O que é:** uma terceira variável que afeta as duas que você está comparando e cria uma relação aparente entre elas.
**Como ler:** sempre que dois grupos diferem, pergunte: *o que mais é diferente entre eles?*
**No projeto:** o Maranhão tem taxa de gravidade muito acima da média — mas também tem 74,9% dos acidentes em pista simples, contra 48,6% no país. Como pista simples já é mais grave em qualquer lugar, parte da diferença "do Maranhão" é, na verdade, do tipo de pista.

### Paradoxo de Simpson
**O que é:** a situação em que um padrão observado no total **se inverte** quando você olha os subgrupos. Clássico exemplo real: um tratamento que parece pior no geral, mas é melhor tanto para casos leves quanto para casos graves — porque foi aplicado desproporcionalmente aos casos graves.
**Como ler:** é a razão pela qual comparar médias brutas de grupos com composições diferentes é perigoso.
**No projeto:** a página ✂️ Segmentação do dashboard alerta automaticamente quando o sinal da diferença muda depois do controle de composição.

### Padronização direta
**O que é:** uma técnica que responde *"e se os dois grupos tivessem exatamente a mesma composição?"*. Ela mantém as taxas observadas dentro de cada subgrupo, mas recalcula o total usando os mesmos pesos para ambos.
**Como ler:** compare a taxa **bruta** com a **padronizada**. A diferença entre elas é a parte do efeito que era só composição; o que sobra é o efeito próprio do grupo.
**No projeto:** a taxa do MA cai de **46,25% (bruta)** para **41,23% (padronizada por tipo de pista)**, contra 28,28% nacional. Ou seja: 28% do excesso era composição — e os ~12,9 pontos restantes continuam sem explicação na base, o que mantém o caso como **hipótese**, não como conclusão.

### Exposição vs. risco
**O que é:** **exposição** é o quanto se anda por um lugar; **risco** é a chance de algo dar errado por unidade de exposição. Contagem bruta mede as duas coisas misturadas.
**Como ler:** onde há mais tráfego há mais acidentes, sem que o lugar seja mais perigoso. Para separar, seria preciso dividir pelo volume de tráfego — o "denominador".
**No projeto:** a base **não tem** dado de fluxo de veículos. Por isso todas as comparações são de *proporção de gravidade dado que houve acidente* — uma pergunta legítima, mas diferente de "qual rodovia é mais perigosa por viagem", que estes dados não conseguem responder.

### Unidade de análise
**O que é:** o que cada linha da tabela representa.
**Como ler:** define o que qualquer média significa.
**No projeto:** **1 linha = 1 acidente (ocorrência)** — não uma linha por pessoa nem por veículo. Portanto "média de 0,084 mortos" significa *por acidente*, e não por pessoa envolvida.

---

## 6. Qualidade dos dados

### NULL vs. zero real vs. desconhecido
**O que é:** três situações que parecem iguais e não são. **NULL** = ausência declarada de valor. **Zero real** = o valor medido é de fato zero. **Desconhecido** = o valor existe mas não foi registrado.
**Como ler:** tratar desconhecido como zero real distorce toda média.
**No projeto:** `mortos = 0` é um zero verdadeiro (o acidente não teve vítimas fatais); `km = 0` é um desconhecido disfarçado (não existe acidente no marco zero de todas essas rodovias).

### Valor-sentinela
**O que é:** um valor comum usado para significar "não informado" — como `0`, `-1`, `"Ignorado"` ou `"Não Informado"`.
**Como ler:** é **mais perigoso que NULL**, porque passa despercebido: um `isnull().sum()` não o encontra, e ele entra silenciosamente em médias, rankings e modelos como se fosse um valor real.
**No projeto:** `km ≤ 0` (1.496 registros), `br = 0` (788 — não existe BR-000), `sentido_via = 'Não Informado'` (788) e `condicao_metereologica = 'Ignorado'` (4.108). Nenhum deles aparece como nulo.

### Campo multivalorado
**O que é:** uma coluna que guarda vários valores numa mesma célula, separados por um caractere.
**Como ler:** infla artificialmente a cardinalidade e quebra a codificação para modelos.
**No projeto:** `tracado_via` traz coisas como `Reta;Declive`, o que faz a coluna aparentar ter **1.223 categorias** quando na verdade existem apenas **12 características reais** combinadas entre si. O tratamento correto é multi-hot (uma coluna binária por característica).

### Deduplicação
**O que é:** remover linhas repetidas.
**No projeto:** feita por `id` na Etapa 1; a EDA confirmou 0 IDs duplicados e 0 linhas integralmente repetidas.

### Cobertura de calendário
**O que é:** checar se todos os dias do período têm registro, comparando os dias observados com o calendário completo.
**Como ler:** um dia inteiro faltando **não aparece como NULL** — ele simplesmente não é uma linha, e nenhuma checagem de nulos o encontra.
**No projeto:** 8 dos 1.673 dias do período não têm nenhum acidente registrado, todos concentrados em julho de 2026.

### Janela não consolidada
**O que é:** o trecho final de uma base alimentada continuamente, em que os registros ainda estão sendo inseridos. O período existe no calendário, mas os dados dele ainda não chegaram.
**Como ler:** produz uma **queda falsa** no fim de qualquer série temporal. O sinal característico é um colapso abrupto nos últimos períodos, não um declínio gradual.
**No projeto:** os últimos 38 dias da série (após 2026-06-23) têm 492 acidentes, contra uma mediana histórica de 188 **por dia**. Ler isso como "queda de acidentes em 2026" seria descrever o atraso de preenchimento da PRF. Corrigindo a janela, 2026 está estável (−0,4%) em vez de cair 17,8% ([D-13](DECISIONS.md#d-13)).

### Camada raw e camada curada
**O que é:** **raw** = o dado como veio da fonte, sem alteração. **Curada** = o dado limpo, tipado e validado, pronto para análise.
**Como ler:** a camada raw nunca é sobrescrita — assim qualquer transformação pode ser auditada e refeita.
**No projeto:** raw = `dados/datatran*.csv`; curada = `dados/curated/acidentes_2022_2026.parquet`.

---

## 7. Machine Learning

### Variável-alvo (*target*)
**O que é:** aquilo que o modelo deve prever.
**No projeto:** `grave_bin` — 1 se o acidente teve morto ou ferido grave, 0 caso contrário.

### Feature (variável preditora)
**O que é:** cada informação usada como entrada do modelo para prever o alvo.
**No projeto:** as candidatas seguras são as estruturais (`uf`, `br`, `km`, `tipo_pista`, `tracado_via`…) e as temporais do período previsto (`mes`, `dia_semana`, `hora`, `fase_dia`).

### Data leakage (vazamento de dados)
**O que é:** usar como feature uma informação que **só existe depois** do que se quer prever. O modelo fica excelente na avaliação e inútil na vida real, porque em produção essa informação não estará disponível no momento da previsão.
**Como ler:** o teste é sempre a mesma pergunta: *eu teria esse dado em mãos no instante em que preciso fazer a previsão?*
**No projeto:** é o risco central deste dataset. `mortos` e `feridos_graves` **definem** o alvo. E as duas variáveis com maior associação estatística com a gravidade — `tipo_acidente` (V = 0,300) e `causa_acidente` (V = 0,244) — só são apuradas depois do acidente ocorrer e ser investigado. Escolher features por correlação levaria direto à armadilha ([D-07](DECISIONS.md#d-07)).

### Desbalanceamento de classes
**O que é:** quando uma categoria do alvo é muito mais frequente que a outra.
**Como ler:** com classes desbalanceadas, a acurácia deixa de significar qualquer coisa.
**No projeto:** 28,28% de acidentes graves contra 71,72% não graves — cerca de 2,5:1. É moderado, tratável sem técnicas agressivas de reamostragem.

### Accuracy, Precision, Recall e F1
**O que é:** quatro formas de medir o acerto de um classificador.
- **Accuracy (acurácia):** o percentual total de acertos.
- **Precision (precisão):** dos casos que o modelo apontou como graves, quantos eram mesmo graves? Mede o custo do alarme falso.
- **Recall (revocação/sensibilidade):** dos casos que eram realmente graves, quantos o modelo encontrou? Mede o custo de deixar passar.
- **F1:** a média harmônica entre precisão e recall — um número só, quando ambos importam.

**Como ler:** precisão e recall se opõem: apertar o critério aumenta um e derruba o outro. Qual priorizar depende do custo do erro.
**No projeto:** a acurácia é enganosa aqui — um modelo que responda "não grave" para tudo acerta **71,72%** sem ter aprendido nada. A avaliação deve priorizar recall e F1 da classe grave, porque deixar de identificar um trecho de risco é pior que investigar um trecho seguro.

### ROC-AUC e PR-AUC
**O que é:** duas métricas que resumem o desempenho do modelo em **todos** os limiares de decisão possíveis, não em um só. **ROC-AUC** avalia a capacidade geral de separar as duas classes; **PR-AUC** foca no desempenho sobre a classe minoritária.
**Como ler:** 0,5 em ROC-AUC = equivalente a sortear. Com classes desbalanceadas, a ROC-AUC parece otimista, e a PR-AUC é a leitura mais honesta.
**No projeto:** a PR-AUC da classe grave é a métrica de comparação recomendada entre modelos.

### Baseline
**O que é:** um modelo propositalmente burro (por exemplo, sempre responder a classe majoritária), usado como piso de comparação.
**Como ler:** um modelo sofisticado que não supera a baseline não aprendeu nada.
**No projeto:** a baseline a bater é o classificador que sempre responde "não grave" — 71,72% de acurácia e recall **zero** na classe que interessa.

### Split temporal
**O que é:** dividir treino e teste **por data** (treinar no passado, testar no futuro), em vez de sortear as linhas aleatoriamente.
**Como ler:** o sorteio aleatório permitiria treinar com dados de 2026 e testar em 2023, o que não corresponde a como o modelo será usado.
**No projeto:** viável com segurança, porque a proporção de acidentes graves é estável ao longo dos anos (27,92%–28,28%) — a relação entre features e alvo não está mudando com o tempo.

### One-hot, multi-hot e target encoding
**O que é:** formas de transformar variável categórica em número, já que modelos não leem texto.
- **One-hot:** uma coluna binária por categoria (`é_pista_simples`, `é_pista_dupla`…). Adequado para poucas categorias mutuamente exclusivas.
- **Multi-hot:** mesma ideia, mas o registro pode ter várias colunas marcadas ao mesmo tempo.
- **Target encoding:** substitui a categoria pela taxa histórica do alvo naquele grupo. Serve para alta cardinalidade, mas exige cuidado redobrado com vazamento.

**No projeto:** `tipo_pista` (3 categorias) → one-hot. `tracado_via` (multivalorada) → **multi-hot** sobre as 12 características reais. `municipio` (2.057 categorias) → agrupamento ou target encoding.

### Matriz esparsa
**O que é:** uma tabela em que a esmagadora maioria das células é zero — resultado típico de one-hot em variável de alta cardinalidade.
**No projeto:** one-hot em `municipio` criaria 2.057 colunas com um único 1 por linha. É o motivo de tratar alta cardinalidade de outra forma.

---

## 8. Ferramentas

### Parquet
**O que é:** um formato de arquivo colunar e comprimido para dados tabulares.
**Como ler:** diferente do CSV, guarda os tipos das colunas (data é data, número é número) e permite ler só as colunas necessárias, o que o torna muito mais rápido.
**No projeto:** é o formato da camada curada.

### DuckDB
**O que é:** um banco de dados analítico que roda dentro do próprio processo Python, sem servidor — permite escrever SQL diretamente sobre arquivos Parquet.
**Como ler:** o papel dele aqui é fazer as agregações pesadas (`GROUP BY`, contagens, cruzamentos) sem carregar as 311 mil linhas na memória a cada interação do dashboard.

### View
**O que é:** uma consulta salva com um nome, que se comporta como se fosse uma tabela — mas é recalculada na hora, sem duplicar dados.
**No projeto:** a view `acidentes_enriquecido` adiciona as colunas derivadas (`ano`, `hora`, `gravidade_4`, `grave_bin`, `tipo_dia`) de forma que "gravidade" signifique exatamente a mesma coisa em todas as páginas e relatórios.

### Streamlit
**O que é:** biblioteca Python que transforma um script em aplicação web. O script inteiro é reexecutado a cada interação do usuário.
**No projeto:** é o dashboard de 14 páginas em `streamlit/`.

### Cache
**O que é:** guardar o resultado de um cálculo caro para reaproveitá-lo em vez de refazê-lo.
**Como ler:** como o Streamlit reexecuta tudo a cada clique, sem cache cada movimento de filtro recalcularia todas as agregações do zero.
**No projeto:** `@st.cache_data` nos resultados de consulta e `@st.cache_resource` na conexão com o banco.

---

## Ver também

- [`docs-etapas/etapa2-eda.md`](docs-etapas/etapa2-eda.md) — o relatório da EDA, com as justificativas metodológicas completas
- [`EDA.md`](specs/eda/EDA.md) — documento narrativo da análise
- [`ANALYSIS_LOG.md`](ANALYSIS_LOG.md) — os 22 achados, com método e limitação de cada um
- [`DECISIONS.md`](DECISIONS.md) — as 14 decisões técnicas, com as alternativas que foram descartadas e por quê
