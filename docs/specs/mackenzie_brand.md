# Mackenzie — Identidade Visual

> Guia prático de identidade visual do Mackenzie para uso em apresentações, especialmente apresentações acadêmicas em HTML.
>
> **Fonte:** materiais oficiais do Mackenzie, incluindo a página de Identidade Visual e o Manual de Comunicação do Mackenzie.  
> **Referência consultada:** https://www.mackenzie.br/sobre/identidade-visual

---

## 1. Essência visual

A identidade do Mackenzie é construída em torno de uma marca institucional forte, tradicional e reconhecível.

Características visuais principais:

- Institucional
- Acadêmica
- Tradicional
- Sólida
- Objetiva
- Alto contraste
- Uso marcante do vermelho institucional
- Tipografia sem serifa, pesada e legível
- Composição limpa, com bastante branco quando o vermelho não é protagonista

A marca oficial utiliza um **símbolo circular com a letra “M”** acompanhado do wordmark **Mackenzie**.

A identidade visual oficial disponibiliza versões positivas, negativas e aplicações sobre fundos coloridos. O próprio Mackenzie orienta que sejam utilizados os arquivos oficiais da marca e suas regras de aplicação.

---

# 2. Cor institucional

## Vermelho Mackenzie

A página oficial de Identidade Visual apresenta o vermelho institucional como a cor padrão da marca.

| Sistema | Valor |
|---|---|
| Pantone | **185 C** |
| RGB | **234, 0, 41** |
| CMYK | **0, 100, 81, 0** |
| HEX | **#EA0029** |

### CSS

```css
:root {
  --mackenzie-red: #EA0029;
}
```

### Uso recomendado

O vermelho deve funcionar como:

- Cor principal da identidade
- Destaque de títulos
- Elementos de navegação
- Linhas e divisores
- Indicadores importantes
- Destaques de dados
- Botões
- Elementos gráficos

Evitar transformar todos os elementos da interface em vermelho. O vermelho funciona melhor quando possui espaço para se destacar.

---

# 3. Cores auxiliares

O material oficial de aplicação da marca também apresenta diversas aplicações sobre fundos coloridos. Entre elas aparecem variações de:

- Vermelho escuro
- Vermelho
- Azul
- Azul escuro
- Azul-petróleo
- Verde
- Verde-limão
- Verde claro
- Magenta
- Rosa claro
- Laranja
- Cinza-esverdeado
- Amarelo-esverdeado

Essas cores aparecem como **variações de aplicação da marca**, e não devem ser interpretadas como substitutas da cor institucional principal.

Para uma apresentação acadêmica, recomenda-se manter uma paleta mais controlada:

```css
:root {
  --mackenzie-red: #EA0029;
  --black: #111111;
  --dark-gray: #333333;
  --gray: #666666;
  --light-gray: #EAEAEA;
  --off-white: #F7F7F7;
  --white: #FFFFFF;
}
```

### Regra prática

**Vermelho + branco + preto/cinza** deve ser a combinação predominante.

Cores adicionais podem ser utilizadas apenas quando necessárias para diferenciar categorias de dados em gráficos.

---

# 4. Logotipo

A marca Mackenzie possui como elemento principal:

- Símbolo circular
- Letra “M”
- Wordmark “Mackenzie”

Existem versões horizontais e outras variações institucionais.

## Versão positiva

Marca escura/preta sobre fundo claro.

Uso recomendado:

- Fundo branco
- Fundo muito claro
- Documentos
- Slides com fundo branco

## Versão negativa

Marca branca sobre fundo escuro.

Uso recomendado:

- Fundos pretos
- Fundos muito escuros
- Grandes áreas de cor institucional
- Capas e encerramentos

## Versão vermelha

A aplicação tradicional da marca utiliza o vermelho institucional.

Uso recomendado:

- Capas
- Elementos institucionais
- Materiais acadêmicos
- Destaques

---

# 5. Área de proteção

A marca possui regras próprias de espaçamento e alinhamento.

**Não encostar outros elementos diretamente no logotipo.**

Em uma apresentação HTML:

```css
.brand-logo {
  margin: 24px;
}
```

Como regra prática, manter uma área visual confortável ao redor da marca.

Não utilizar o logotipo como elemento decorativo repetitivo.

---

# 6. Tipografia

Os arquivos oficiais de orientação da marca indicam **Helvética Bold** para a construção/aplicação do logotipo.

A Helvética possui características importantes para reproduzir o espírito visual:

- Sans-serif
- Limpa
- Institucional
- Alta legibilidade
- Formas simples
- Peso forte para títulos

## Para HTML

Quando Helvetica estiver disponível:

```css
font-family: Helvetica, Arial, sans-serif;
```

Fallback recomendado:

```css
font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
```

### Hierarquia sugerida

```css
h1 {
  font-weight: 700;
}

h2 {
  font-weight: 700;
}

h3 {
  font-weight: 700;
}

body {
  font-weight: 400;
}
```

**Importante:** Helvetica Bold é uma referência da identidade da marca/logotipo. Não é necessário transformar todo o texto da apresentação em bold.

---

# 7. Estilo de títulos

Os títulos devem ser:

- Grandes
- Curtos
- Diretos
- Fortes
- Preferencialmente alinhados à esquerda
- Com alto contraste

Exemplo:

```text
O PROBLEMA
```

ou

```text
ACIDENTES RODOVIÁRIOS
```

ou

```text
O QUE OS DADOS REVELAM
```

Uma pequena linha ou detalhe vermelho pode ser utilizado como elemento de assinatura visual.

Exemplo:

```css
.section-title::before {
  content: "";
  display: block;
  width: 48px;
  height: 4px;
  background: #EA0029;
  margin-bottom: 16px;
}
```

---

# 8. Layout

A identidade visual combina muito bem com layouts editoriais e institucionais.

### Recomendações

- Muito espaço em branco
- Grid consistente
- Alinhamento rigoroso
- Poucos elementos por slide
- Hierarquia clara
- Grandes números
- Grandes títulos
- Blocos de informação bem definidos

Evitar:

- excesso de cards
- gradientes exagerados
- sombras pesadas
- excesso de ícones
- excesso de cores
- elementos decorativos sem função

---

# 9. Elementos gráficos

O manual de comunicação mostra uma linguagem visual que pode utilizar:

- Grandes áreas de vermelho
- Formas geométricas
- Curvas
- Círculos
- Linhas
- Grades
- Elementos de construção
- Grandes números
- Contraste entre vermelho, branco e preto

Para uma apresentação de Engenharia de Dados, esses elementos podem ser adaptados de maneira mais contemporânea.

### Exemplo

Utilizar um grande número:

```text
87%
```

com:

- número em vermelho
- descrição em preto
- fundo branco
- pequeno elemento geométrico vermelho

Isso cria impacto sem fugir da identidade.

---

# 10. Gráficos

Para gráficos de dados, a identidade deve continuar reconhecível sem prejudicar a leitura.

## Gráfico principal

Usar:

```css
--chart-primary: #EA0029;
```

## Elementos secundários

Preferir tons neutros:

```css
--chart-secondary: #333333;
--chart-muted: #999999;
--chart-grid: #E5E5E5;
```

### Regra

O vermelho deve destacar a informação mais importante.

Exemplo:

- Série principal → vermelho Mackenzie
- Comparação → cinza
- Referência → cinza claro
- Destaque → vermelho

Evitar transformar cada categoria em uma cor diferente.

---

# 11. Slides de apresentação

## Capa

Preferência:

- Fundo vermelho Mackenzie ou branco
- Grande título
- Poucos elementos
- Logo em posição de destaque
- Elemento gráfico geométrico

Exemplo conceitual:

```text
MACKENZIE

Mack Car Crash Prediction

Transformando dados de acidentes
em inteligência para decisão.
```

---

## Slides de conteúdo

Preferência:

- Fundo branco
- Título preto ou vermelho
- Texto preto/cinza
- Destaques vermelhos
- Gráficos com vermelho institucional

---

## Slide de resultado

Pode utilizar fundo vermelho para criar contraste.

Exemplo:

```text
RESULTADO

87%

acurácia do modelo
```

Com texto branco.

---

## Slide final

Pode utilizar:

- Fundo vermelho
- Logo branco
- Mensagem curta
- Poucos elementos

Exemplo:

```text
DADOS GERAM CONHECIMENTO.

Obrigado.

Perguntas?
```

---

# 12. Uso da marca em uma apresentação acadêmica

Para uma apresentação do MBA Mackenzie:

### Prioridade visual

1. Identidade Mackenzie
2. Conteúdo do projeto
3. Dados e gráficos
4. Elementos tecnológicos

A tecnologia não deve dominar a identidade institucional.

Evitar criar uma apresentação com estética genérica de startup/tech e apenas adicionar o logo do Mackenzie.

A apresentação deve parecer **acadêmica, institucional e moderna**.

---

# 13. Direção visual para o projeto Mack Car Crash Prediction

Para o projeto de previsão/análise de acidentes rodoviários, combinar:

**Mackenzie**
+
**Dados**
+
**Rodovias**
+
**Machine Learning**

### Paleta

```text
#EA0029  █  Vermelho Mackenzie
#111111  █  Preto
#333333  █  Cinza escuro
#666666  █  Cinza
#EAEAEA  █  Cinza claro
#F7F7F7  █  Off-white
#FFFFFF  █  Branco
```

### Linguagem

- Institucional
- Data-driven
- Moderna
- Sóbria
- Tecnológica sem parecer startup
- Acadêmica sem parecer apresentação tradicional
- Forte uso de contraste

---

# 14. Regras de ouro

1. Usar **#EA0029** como vermelho institucional.
2. Priorizar vermelho, branco, preto e cinzas.
3. Usar Helvetica/Arial como referência tipográfica.
4. Manter títulos fortes e objetivos.
5. Utilizar bastante espaço em branco.
6. Usar o vermelho para direcionar atenção.
7. Não usar excesso de cores.
8. Não distorcer o logotipo.
9. Não alterar as proporções do logotipo.
10. Não aplicar efeitos desnecessários ao logotipo.
11. Não utilizar o logo como elemento decorativo repetitivo.
12. Priorizar gráficos simples e interpretáveis.
13. Fazer o resultado mais importante visualmente.
14. Manter consistência de grid e espaçamento.
15. Adaptar a identidade institucional ao contexto de Engenharia de Dados sem perder o caráter Mackenzie.

---

# 15. Fontes oficiais

- Portal Mackenzie — Identidade Visual:  
  https://www.mackenzie.br/sobre/identidade-visual

- Manual de Comunicação Mackenzie 2023:  
  https://www.mackenzie.br/fileadmin/ARQUIVOS/Public/0-sistemas/email/mkt/manual/2023/Manual_de_Comunica%C3%A7%C3%A3o_Mackenzie_-_13.12.2023.pdf

- Orientação oficial da marca Mackenzie:  
  https://www.mackenzie.br/fileadmin/ARQUIVOS/Public/14-sobre/identidadevisual/mackenzie/completo/_orientacao.pdf

> **Observação sobre a cor:** materiais oficiais consultados apresentam pequenas diferenças de valor RGB/HEX entre documentos/páginas. Para esta apresentação, foi adotado **#EA0029**, valor apresentado na página oficial de Identidade Visual e consistente com os materiais oficiais de orientação mais recentes consultados.


# 16. Logotipo oficial

Abaixo está a versão da marca Mackenzie fornecida para utilização como referência visual neste guia:

![Logo oficial do Mackenzie](mackenzie_logo-removebg-preview.png)

### Arquivo da logo

`mackenzie_logo-removebg-preview.png`

**Recomendação:** utilizar esta versão apenas quando ela estiver de acordo com as regras oficiais de aplicação da marca. Não distorcer, rotacionar, alterar proporções ou aplicar efeitos que descaracterizem o logotipo.
