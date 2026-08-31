# Orientação para Implementação do Pré-Processamento de Dados

## 1. Objetivo

Implementar a etapa de **pré-processamento dos dados** do projeto de previsão de risco de acidentes, garantindo que os dados estejam preparados para as etapas posteriores de análise exploratória, engenharia de atributos e Machine Learning.

O pré-processamento deve priorizar:

* qualidade dos dados;
* confiabilidade;
* integridade;
* rastreabilidade;
* reprodutibilidade;
* preservação das informações relevantes para o fenômeno estudado.

**Não realizar transformações automaticamente apenas porque são consideradas boas práticas.** Antes de modificar ou remover qualquer informação, analisar o contexto dos dados e justificar tecnicamente a decisão.

---

## 2. Análise inicial dos dados

Antes de implementar as transformações, realizar uma análise inicial dos datasets para identificar:

* dados inconsistentes;
* dados incompletos;
* valores duplicados;
* valores fora do padrão esperado;
* tipos de dados incorretos;
* categorias inconsistentes;
* valores ausentes;
* possíveis outliers;
* colunas que possam conter informações relevantes;
* diferenças de estrutura ou nomenclatura entre os arquivos/anos.

A IA deve primeiro **entender o significado das colunas e dos dados** antes de decidir como tratá-los.

Não assumir que um valor é inválido apenas por parecer incomum. Avaliar se ele pode representar um evento real do fenômeno estudado.

---

## 3. Padronização dos dados

Padronizar os dados de forma consistente, considerando:

* formatos de datas;
* horários;
* textos;
* nomes de categorias;
* unidades de medida;
* codificações;
* tipos numéricos;
* tipos categóricos;
* nomes das colunas.

Datas devem ser tratadas como datas, números devem ser tratados como números e categorias devem ser tratadas como categorias quando apropriado.

Evitar situações como:

* datas armazenadas como texto;
* números armazenados como strings;
* categorias interpretadas como variáveis numéricas;
* diferentes representações para a mesma categoria.

Caso existam diferenças entre os arquivos dos diferentes anos, identificar essas diferenças e estabelecer uma estratégia de padronização que permita posteriormente consolidar os dados.

---

## 4. Tratamento de valores ausentes

Identificar e analisar os **missing values** de cada coluna.

Para cada variável relevante, avaliar:

* quantidade de valores ausentes;
* percentual de valores ausentes;
* possível motivo da ausência;
* importância da variável;
* impacto da ausência nas análises posteriores;
* possibilidade de preenchimento;
* possibilidade de manutenção do valor nulo;
* possibilidade de remoção da coluna ou registro.

Escolher a estratégia de tratamento de acordo com o contexto.

Possíveis abordagens incluem:

* preenchimento;
* utilização de categorias como "Não informado", quando fizer sentido;
* manutenção do valor ausente;
* remoção de registros;
* remoção de colunas.

**Não remover dados indiscriminadamente.**

Remover uma grande quantidade de linhas ou colunas sem análise pode reduzir significativamente a informação disponível e prejudicar a capacidade de generalização do modelo.

Toda decisão relacionada a missing values deve ser **documentada e justificada**.

---

## 5. Identificação e tratamento de duplicidades

Verificar a existência de registros duplicados.

Antes de remover duplicidades, determinar:

* se são realmente registros duplicados;
* se representam ocorrências distintas;
* quais colunas devem ser utilizadas para identificar uma duplicidade;
* se existem duplicidades entre arquivos ou anos;
* se a duplicidade pode ser consequência da própria estrutura da base.

Não remover registros apenas porque possuem valores semelhantes.

A regra de deduplicação deve ser clara, reproduzível e documentada.

---

## 6. Análise de outliers

Detectar e analisar possíveis outliers nas variáveis numéricas.

A análise deve considerar que valores extremos **não são necessariamente erros**.

Um valor muito alto ou muito baixo pode representar:

* erro de preenchimento;
* inconsistência;
* situação excepcional;
* ou um evento real importante para o fenômeno estudado.

Portanto, não remover outliers automaticamente.

Para cada tratamento, explicar:

1. qual variável apresentou o comportamento;
2. como o outlier foi identificado;
3. se o valor aparenta ser inválido ou apenas extremo;
4. qual decisão foi tomada;
5. por que essa decisão é adequada ao contexto do projeto.

Valores extremos que representem eventos reais devem ser preservados sempre que possível.

---

## 7. Escalonamento e normalização

Avaliar a necessidade de normalização ou padronização das variáveis numéricas considerando os modelos que serão utilizados posteriormente.

Algoritmos como:

* K-NN;
* SVM;
* regressão logística;

podem ser sensíveis à escala das variáveis.

Entretanto, **não aplicar normalização ou padronização indiscriminadamente durante o pré-processamento**.

A estratégia deve considerar:

* quais modelos serão utilizados;
* quais variáveis precisam de escala;
* em qual etapa o escalonamento deve ocorrer;
* como evitar vazamento de dados.

Caso o escalonamento seja necessário para o Machine Learning, garantir que parâmetros como média e desvio padrão sejam calculados somente sobre o conjunto de treinamento e posteriormente aplicados aos demais conjuntos.

---

## 8. Variáveis categóricas

Identificar as variáveis categóricas e avaliar a melhor estratégia de representação.

Não utilizar encoding de forma automática.

Por exemplo, **Label Encoding em categorias sem ordem pode induzir o modelo a interpretar uma relação que não existe**.

A escolha do encoding deve considerar:

* natureza da variável;
* quantidade de categorias;
* existência ou não de ordem;
* modelo de Machine Learning;
* risco de criar relações artificiais entre categorias.

Documentar a estratégia escolhida e sua justificativa.

---

## 9. Compreensão do significado dos dados

Esta é uma etapa fundamental.

Nenhuma transformação deve ser realizada sem compreender o significado da variável.

Antes de tratar uma coluna, verificar:

* o que ela representa;
* quais são seus valores possíveis;
* qual é o tipo correto;
* se existe documentação oficial;
* se valores aparentemente inválidos podem representar situações reais;
* se a coluna possui relação com o fenômeno estudado;
* se a coluna poderá ser utilizada posteriormente na análise ou modelagem.

**Não remover atributos simplesmente porque possuem muitos valores nulos, alta cardinalidade ou valores aparentemente estranhos sem antes avaliar seu significado.**

O contexto de negócio e o significado dos dados devem orientar o tratamento.

---

## 10. Evitar perda desnecessária de informação

O objetivo do pré-processamento não é produzir o dataset "mais limpo possível", mas produzir um dataset **confiável e adequado ao problema**.

Evitar:

* remover muitas linhas;
* remover muitas colunas;
* descartar categorias raras automaticamente;
* substituir valores sem analisar sua origem;
* eliminar valores extremos sem justificativa;
* transformar variáveis sem compreender seu significado.

Sempre priorizar a preservação das informações relevantes.

---

## 11. Prevenção de Data Leakage

Todas as transformações devem ser planejadas considerando o risco de **data leakage**.

O projeto possui dimensão temporal e pretende utilizar dados históricos para identificar risco futuro. Portanto, nenhuma informação futura deve ser utilizada indevidamente durante a preparação dos dados.

Especial atenção deve ser dada a:

* criação de variáveis históricas;
* agregações;
* cálculo de estatísticas;
* normalização;
* encoding baseado nos dados;
* criação do target;
* divisão entre treinamento, validação e teste.

Informações relacionadas ao resultado do próprio acidente não devem ser utilizadas como features quando essas informações revelarem diretamente o target.

---

## 12. Reprodutibilidade

O pré-processamento deve ser implementado como um **pipeline reprodutível**.

O mesmo código deve conseguir processar novamente os dados caso:

* novos arquivos sejam adicionados;
* novos anos sejam disponibilizados;
* os dados sejam atualizados;
* seja necessário refazer o processamento.

Evitar procedimentos manuais que não possam ser reproduzidos.

Idealmente, o processo deve seguir uma estrutura semelhante a:

```text
Dados Raw
   ↓
Validação
   ↓
Padronização
   ↓
Tratamento de missing values
   ↓
Deduplicação
   ↓
Validação de tipos e regras
   ↓
Dados Curated
```

---

## 13. Documentação das decisões

**Toda transformação realizada deve ser documentada.**

Para cada decisão relevante, registrar:

* problema identificado;
* coluna(s) afetada(s);
* análise realizada;
* abordagem escolhida;
* motivo da escolha;
* impacto esperado;
* alternativas consideradas, quando relevante.

Exemplo:

```text
Problema:
A coluna X apresenta 18% de valores ausentes.

Análise:
Os valores ausentes não parecem representar erro de coleta,
mas ausência de informação no registro original.

Decisão:
Manter os valores ausentes.

Justificativa:
Preencher os valores poderia introduzir informações artificiais
e distorcer a distribuição original da variável.
```

A documentação deve permitir que outra pessoa compreenda **por que o tratamento foi realizado daquela maneira e consiga reproduzi-lo**.

---

## 14. Validação após o pré-processamento

Após todas as transformações, realizar uma nova validação dos dados.

Verificar:

* quantidade de registros antes e depois;
* quantidade de colunas antes e depois;
* tipos de dados;
* valores ausentes;
* duplicidades;
* categorias;
* valores inválidos;
* distribuição das principais variáveis;
* consistência entre os anos;
* integridade dos dados.

Comparar o dataset original com o dataset tratado para garantir que nenhuma transformação tenha provocado perda ou alteração inesperada de informação.

O dataset tratado deve continuar representando corretamente o fenômeno estudado.

---

## 15. Organização do código

Separar o código de acordo com suas responsabilidades.

Uma estrutura sugerida é:

```text
src/
├── pipeline.py
│
├── ingestion/
│   ├── prf.py
│   └── anbima.py
│
├── preprocessing/
│   ├── acidentes.py
│   └── feriados.py
│
├── analysis/
│   └── eda.py
│
├── features/
│   └── engenharia.py
│
└── ml/
    ├── train.py
    └── evaluate.py
```

O `pipeline.py` deve atuar como **orquestrador**, chamando as diferentes etapas.

Não concentrar toda a lógica de processamento em um único arquivo.

O processamento dos acidentes deve ser reutilizável para os diferentes anos, evitando criar um script independente para 2022, outro para 2023, etc.

---

## 16. Resultado esperado

Ao final desta etapa, deve existir uma camada **Curated** contendo os dados:

* padronizados;
* tipados corretamente;
* tratados;
* deduplicados;
* validados;
* consolidados;
* rastreáveis à origem;
* prontos para a análise exploratória.

A EDA será realizada posteriormente sobre esses dados e deverá utilizar seus resultados para orientar a engenharia de atributos.

---

## 17. Regra principal

Durante todo o desenvolvimento, seguir estas prioridades:

**Entender os dados antes de transformá-los.**

**Preservar informação antes de removê-la.**

**Justificar antes de aplicar uma técnica.**

**Documentar todas as decisões relevantes.**

**Evitar complexidade sem necessidade.**

**Garantir que o processo seja reproduzível.**

O objetivo não é simplesmente "limpar os dados", mas construir uma preparação de dados **tecnicamente justificável, reproduzível e adequada ao problema de negócio**.
