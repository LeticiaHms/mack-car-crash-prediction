Crie uma apresentação profissional em **HTML, CSS e JavaScript**, pronta para ser executada localmente no navegador, para apresentação acadêmica do projeto **Mack Car Crash Prediction**, desenvolvido no MBA em Engenharia de Dados da Universidade Presbiteriana Mackenzie.

## CONTEXTO

A apresentação terá:

* **10 minutos de apresentação**
* **10 minutos de perguntas e respostas**
* Local: **Sala Mack Graphe**
* Público: professores e avaliadores do MBA em Engenharia de Dados

A apresentação deve contar uma **história de negócio guiada por dados**, e não simplesmente apresentar uma sequência técnica de etapas.

A narrativa principal deve seguir:

**Problema → Dados → Preparação → Análise → Solução → Modelo → Resultados → Valor → Limitações e próximos passos**

O projeto utiliza **dados públicos brasileiros da Polícia Rodoviária Federal (PRF)** relacionados a acidentes rodoviários. O objetivo é utilizar engenharia de dados, análise exploratória e modelagem preditiva para extrair informações relevantes dos acidentes e construir uma solução de previsão/classificação relacionada aos acidentes rodoviários.

**IMPORTANTE:** não invente métricas, resultados, quantidades de registros, features ou conclusões que não estejam disponíveis nos dados/projeto. Quando alguma informação específica não estiver disponível, utilize um placeholder claramente identificado, como `[INSERIR MÉTRICA]`, ou estruture o slide para receber essa informação posteriormente.

---

# OBJETIVO DA APRESENTAÇÃO

A apresentação precisa responder claramente:

1. Qual problema foi resolvido?
2. Por que esse problema importa?
3. Como os dados ajudaram a compreender o problema?
4. O que foi construído?
5. Quais resultados foram alcançados?
6. Quais limitações existem?
7. Quais são os próximos passos?

Evite transformar a apresentação em uma aula sobre ferramentas.

A tecnologia deve aparecer como **meio para resolver o problema**, e não como protagonista.

---

# ESTRUTURA

Crie aproximadamente **10 a 12 slides**, adequados para uma apresentação de 10 minutos.

Distribua aproximadamente:

* **Introdução e problema:** 2 minutos
* **Dados e preparação:** 3 minutos
* **Modelagem e solução:** 3 minutos
* **Resultados e conclusão:** 2 minutos

Cada slide deve ter uma mensagem principal clara.

---

## SLIDE 1 — ABERTURA

Título:

**Mack Car Crash Prediction**

Subtítulo relacionado à previsão/análise de acidentes rodoviários utilizando dados públicos brasileiros.

Apresente:

* Nome do projeto
* Integrantes do grupo
* MBA em Engenharia de Dados
* Universidade Presbiteriana Mackenzie

Inclua uma frase de impacto, por exemplo:

> **“E se os dados dos acidentes rodoviários pudessem nos ajudar a antecipar padrões de risco?”**

Não use uma frase excessivamente genérica.

Visualmente, criar uma abertura forte, moderna e profissional, relacionada a rodovias, trânsito, dados e inteligência.

---

# SLIDE 2 — O PROBLEMA

Explique o problema de negócio/social.

Responder:

* Qual é a dor?
* Quem é impactado?
* Por que isso importa?
* Quais são as consequências?

Apresente o problema como uma situação real, e não como uma definição técnica.

Exemplo de narrativa:

**Acidentes rodoviários geram impactos humanos, sociais e econômicos. Os registros históricos da PRF contêm informações que podem revelar padrões associados à ocorrência e à gravidade dos acidentes.**

O slide deve deixar claro:

**“Por que alguém deveria se importar com esse problema?”**

Utilize poucos textos e um elemento visual forte.

---

# SLIDE 3 — OBJETIVO DO PROJETO

Apresente:

### Objetivo principal

Construir uma solução baseada em dados públicos da PRF capaz de analisar padrões dos acidentes rodoviários e aplicar modelagem preditiva ao problema definido no projeto.

### Objetivos específicos

* Coletar e consolidar dados públicos da PRF
* Realizar tratamento e padronização dos dados
* Explorar padrões e características dos acidentes
* Construir uma pipeline de dados reproduzível
* Preparar os dados para machine learning
* Treinar e avaliar modelos
* Traduzir os resultados técnicos em insights compreensíveis

Inclua também 2 ou 3 perguntas que os dados deveriam responder.

Exemplo:

* Quais características estão mais associadas aos acidentes?
* Quais padrões aparecem nos dados históricos?
* É possível utilizar essas características para realizar previsões?

---

# SLIDE 4 — OS DADOS

Mostrar de forma visual a origem dos dados.

Fonte principal:

**Polícia Rodoviária Federal — PRF**

Dados públicos de acidentes rodoviários.

Mostrar:

* Fonte
* Período analisado
* Formato dos arquivos
* Volume de registros
* Principais grupos de variáveis
* Processo de obtenção

Caso números exatos não estejam disponíveis, utilizar placeholders:

`[PERÍODO]`
`[NÚMERO DE REGISTROS]`
`[NÚMERO DE COLUNAS]`

Criar um pequeno fluxo visual:

**PRF → Arquivos CSV → Ingestão → Processamento → Dataset analítico**

Não fazer um diagrama excessivamente complexo.

---

# SLIDE 5 — PRÉ-PROCESSAMENTO

Mostrar os principais problemas encontrados nos dados e como foram tratados.

Possíveis categorias:

* Valores ausentes
* Duplicidades
* Inconsistências
* Padronização de categorias
* Formatos de datas
* Tipos de dados
* Valores inválidos
* Outliers
* Engenharia de atributos

A narrativa deve ser:

**“Os dados disponíveis não estavam prontos para responder ao problema.”**

Depois mostrar:

**Problema encontrado → Tratamento → Impacto**

Não mostrar código.

Priorizar decisões importantes e explicar o motivo delas.

---

# SLIDE 6 — ANÁLISE EXPLORATÓRIA

Este deve ser um dos slides mais visuais.

Mostrar **2 ou 3 gráficos realmente relevantes**.

Os gráficos devem ser derivados dos dados reais do projeto, caso os arquivos/dados estejam disponíveis.

Cada gráfico deve responder explicitamente:

### “O que aprendemos com isso?”

Não apresentar gráficos apenas porque são visualmente interessantes.

Para cada gráfico, adicionar uma pequena conclusão.

Exemplo:

**Insight:** determinada condição/local/período apresenta maior concentração de acidentes.

Utilizar visualizações adequadas, como:

* barras
* séries temporais
* mapas, se houver dados geográficos apropriados
* distribuição
* comparação entre categorias

Evitar gráficos excessivamente complexos.

---

# SLIDE 7 — DA ANÁLISE PARA A SOLUÇÃO

Mostrar a transformação dos dados em solução.

Criar um pipeline visual simples:

**Dados PRF**
↓
**Ingestão**
↓
**Tratamento**
↓
**Análise**
↓
**Feature Engineering**
↓
**Machine Learning**
↓
**Predição / Resultado**

Mostrar as principais tecnologias utilizadas no projeto somente neste contexto.

Exemplos, caso realmente utilizadas:

* Python
* Pandas
* PySpark / Spark
* SQL
* AWS / GCP / outras tecnologias utilizadas
* Machine Learning
* Git

Não criar uma parede de logos.

---

# SLIDE 8 — CONSTRUÇÃO DO MODELO

Explicar:

* Qual problema de machine learning foi definido
* Qual variável alvo foi utilizada
* Quais features foram consideradas
* Quais algoritmos foram testados
* Como os dados foram divididos
* Qual estratégia de treinamento foi utilizada
* Por que o modelo escolhido foi considerado adequado

Caso mais de um algoritmo tenha sido testado, mostrar uma comparação simples.

Exemplo:

| Modelo           |   Métrica | Resultado |
| ---------------- | --------: | --------: |
| Modelo A         | [MÉTRICA] |   [VALOR] |
| Modelo B         | [MÉTRICA] |   [VALOR] |
| Modelo escolhido | [MÉTRICA] |   [VALOR] |

**Não inventar valores.**

O objetivo é explicar as decisões, não ensinar machine learning em profundidade.

---

# SLIDE 9 — RESULTADOS

Este deve ser **O SLIDE MAIS IMPORTANTE DA APRESENTAÇÃO**.

Dar destaque visual máximo aos resultados.

Mostrar:

* Métrica principal
* Outras métricas relevantes
* Comparação entre modelos
* Resultado do modelo final
* Principais descobertas

Dependendo do tipo de problema, utilizar métricas adequadas, como:

* Accuracy
* Precision
* Recall
* F1-score
* ROC-AUC
* RMSE
* MAE
* outras métricas relevantes

Não utilizar todas as métricas indiscriminadamente.

Selecionar apenas as que ajudam a explicar o desempenho do modelo.

A apresentação deve traduzir o resultado técnico para impacto.

Exemplo de estrutura:

**“O modelo alcançou [MÉTRICA], demonstrando capacidade de [INTERPRETAÇÃO DO RESULTADO].”**

Adicionar uma seção:

### O que isso significa na prática?

Explicar o resultado em linguagem de negócio/social.

---

# SLIDE 10 — O QUE APRENDEMOS

Separar o resultado técnico dos principais insights.

Mostrar de 3 a 4 descobertas:

**01 — [INSIGHT]**

**02 — [INSIGHT]**

**03 — [INSIGHT]**

**04 — [INSIGHT]**

Esses insights devem responder:

**“O que sabemos agora que não sabíamos antes de analisar os dados?”**

Evitar repetir informações já apresentadas.

---

# SLIDE 11 — LIMITAÇÕES E PRÓXIMOS PASSOS

Ser transparente.

Mostrar duas colunas:

### Limitações

* Dados públicos possuem limitações
* Possíveis variáveis não disponíveis
* Qualidade/consistência dos registros
* Período histórico limitado
* Limitações do modelo
* Limitações de generalização
* [OUTRAS LIMITAÇÕES REAIS DO PROJETO]

### Próximos passos

* Incorporar novas fontes de dados
* Ampliar o período analisado
* Adicionar novas variáveis
* Testar outros algoritmos
* Melhorar feature engineering
* Avaliar modelos mais avançados
* Automatizar completamente a pipeline
* Evoluir para uma solução escalável

Somente incluir itens que façam sentido para o projeto.

---

# SLIDE 12 — CONCLUSÃO

Encerrar retomando a história.

Estrutura:

**Tínhamos um problema.**

↓

**Buscamos dados públicos.**

↓

**Tratamos e entendemos os dados.**

↓

**Encontramos padrões.**

↓

**Construímos uma solução preditiva.**

↓

**Avaliamos seus resultados.**

↓

**Geramos conhecimento para apoiar decisões.**

Finalizar com uma frase forte relacionada ao projeto.

Exemplo:

> **“Mais do que prever acidentes, o objetivo foi transformar dados históricos em conhecimento capaz de apoiar decisões melhores.”**

Adicionar:

**Obrigado!**

**Perguntas?**

---

# DESIGN

Criar uma apresentação com aparência de **projeto profissional de Data Engineering / Data Science**, evitando estética de trabalho acadêmico tradicional.

Características:

* Visual moderno
* Minimalista
* Profissional
* Alta legibilidade
* Pouco texto
* Forte hierarquia visual
* Muito espaço em branco
* Gráficos grandes
* Cards apenas quando fizer sentido
* Ícones simples
* Tipografia moderna
* Layout consistente

Tema visual inspirado em:

**dados + rodovias + segurança + tecnologia**

Pode utilizar uma paleta sofisticada baseada em tons escuros/neutros com uma cor de destaque.

Evitar excesso de cores.

Não utilizar imagens genéricas de banco de imagens em todos os slides.

---

# EXPERIÊNCIA DA APRESENTAÇÃO

A apresentação deve funcionar como um **storytelling**.

Não apresentar:

> “Primeiro fizemos coleta, depois pré-processamento, depois análise exploratória...”

Em vez disso, apresentar:

> **“Tínhamos um problema. Para entendê-lo, buscamos dados públicos da PRF. Porém, os dados apresentavam inconsistências que precisaram ser tratadas. Depois do tratamento, encontramos padrões importantes. Esses padrões orientaram a construção do modelo, que apresentou [RESULTADO].”**

Cada slide deve fazer conexão natural com o próximo.

---

# REGRAS IMPORTANTES

1. Não inventar dados.
2. Não inventar métricas.
3. Não inventar resultados.
4. Não inventar tecnologias que não foram utilizadas.
5. Não colocar código nos slides.
6. Não criar gráficos sem interpretação.
7. Não utilizar excesso de texto.
8. Não utilizar diagramas extremamente complexos.
9. Explicar as decisões importantes.
10. Mostrar limitações de forma transparente.
11. Priorizar o problema e os resultados sobre as ferramentas.
12. O resultado deve ser compreensível para alguém que não participou do desenvolvimento.
13. A apresentação deve caber confortavelmente em **10 minutos**.
14. O slide de resultados deve receber maior destaque visual.
15. Manter consistência visual entre todos os slides.

---

# IMPLEMENTAÇÃO HTML

Entregar tudo em **um único arquivo HTML**, contendo:

* HTML
* CSS
* JavaScript

Não depender de backend.

A apresentação deve funcionar abrindo o arquivo diretamente no navegador.

Implementar:

* Navegação com teclado
* Setas ← → para trocar slides
* Indicador de progresso
* Número do slide
* Transições suaves
* Layout responsivo
* Modo apresentação em tela cheia, se possível
* Atalho `F` ou equivalente para fullscreen
* Atalho `Esc` para sair do fullscreen

Criar uma navegação visual discreta.

---

# FORMATO

A apresentação deve ser construída em formato **16:9**, otimizada para projetor/TV.

Utilizar aproximadamente:

**1920 × 1080**

Garantir que textos, gráficos e elementos importantes não fiquem próximos demais das bordas.

---

# NOTAS DO APRESENTADOR

Crie um .md com o roteiro para cada slide, ajudando a manter o ritmo de aproximadamente:

* Slide 1: 30–45s
* Slide 2: 1min
* Slide 3: 45s
* Slide 4: 1min
* Slide 5: 1min
* Slide 6: 1min
* Slide 7: 45s
* Slide 8: 1min
* Slide 9: 1min30s
* Slide 10: 45s
* Slide 11: 45s
* Slide 12: 30s

Total aproximado: **10 minutos**.

---

# ENTREGA

Antes de gerar o HTML, organize mentalmente a narrativa completa.

O resultado final deve parecer uma apresentação feita por uma equipe de Engenharia de Dados que sabe **explicar o valor do projeto**, e não apenas demonstrar que sabe utilizar ferramentas técnicas.

A prioridade deve ser:

**História > Problema > Insights > Resultado > Impacto > Tecnologia**

e não:

**Tecnologia > Código > Pipeline > Ferramentas.**
