# Coleta dos Dados

**Objetivo:** ter dados relevantes, confiáveis e representativos do problema de negócio.

## Entregáveis

### 1. Dataset bruto (raw data)
Dados ainda não tratados, vindos diretamente das fontes.

- `dados/datatran2022.csv`
- `dados/datatran2023.csv`
- `dados/datatran2024.csv`
- `dados/datatran2025.csv`
- `dados/datatran2026.csv`
- `dados/feriados_nacionais.xls`

### 2. Lista/documentação das fontes de dados
De onde os dados vieram.

| Fonte | Dados obtidos | Link |
|---|---|---|
| Polícia Rodoviária Federal (PRF) | Dados abertos de acidentes de trânsito, agrupados por ocorrência (`datatran202*.csv`) | https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf |
| ANBIMA | Feriados nacionais (`feriados_nacionais.xls`) | https://www.anbima.com.br/feriados/feriados.asp |

### 3. Dicionário de dados (data dictionary)
Descrição das variáveis, seus significados, tipos e unidades.

#### `dados/datatran202*.csv` (dados de acidentes — PRF)

Arquivo delimitado por `;`, codificação Latin-1 (ISO-8859-1). Cada linha representa um acidente (ou uma pessoa/veículo envolvido, conforme granularidade da PRF).

| Coluna | Tipo | Descrição / unidade |
|---|---|---|
| `id` | inteiro | Identificador único do acidente |
| `data_inversa` | data (AAAA-MM-DD) | Data em que o acidente ocorreu |
| `dia_semana` | texto (categórico) | Dia da semana do acidente (ex: `segunda-feira`, `domingo`) |
| `horario` | texto (HH:MM:SS) | Horário do acidente |
| `uf` | texto (categórico) | Unidade Federativa (sigla do estado) onde ocorreu o acidente |
| `br` | inteiro | Número da rodovia federal (BR) |
| `km` | texto (decimal, vírgula) | Quilômetro da rodovia onde ocorreu o acidente |
| `municipio` | texto | Município de ocorrência |
| `causa_acidente` | texto (categórico) | Causa principal do acidente (ex: `Velocidade Incompatível`, `Ingestão de álcool pelo condutor`) |
| `tipo_acidente` | texto (categórico) | Tipo/forma do acidente (ex: `Colisão frontal`, `Tombamento`) |
| `classificacao_acidente` | texto (categórico) | Gravidade do acidente: `Sem Vítimas`, `Com Vítimas Feridas`, `Com Vítimas Fatais` |
| `fase_dia` | texto (categórico) | Período do dia (`Pleno dia`, `Anoitecer`, `Plena Noite`, `Amanhecer`) |
| `sentido_via` | texto (categórico) | Sentido da via (`Crescente`, `Decrescente`, `Não Informado`) |
| `condicao_metereologica` | texto (categórico) | Condição climática no momento (ex: `Céu Claro`, `Chuva`, `Nevoeiro/Neblina`) |
| `tipo_pista` | texto (categórico) | Tipo de pista (`Simples`, `Dupla`, `Múltipla`) |
| `tracado_via` | texto (categórico) | Traçado da via (ex: `Reta`, `Curva`, `Reta;Aclive`) |
| `uso_solo` | texto (`Sim`/`Não`) | Indica se o trecho é em área urbana (uso de solo) |
| `pessoas` | inteiro | Número total de pessoas envolvidas no acidente |
| `mortos` | inteiro | Número de vítimas fatais |
| `feridos_leves` | inteiro | Número de feridos leves |
| `feridos_graves` | inteiro | Número de feridos graves |
| `ilesos` | inteiro | Número de pessoas ilesas |
| `ignorados` | inteiro | Número de pessoas com estado não informado |
| `feridos` | inteiro | Número total de feridos (leves + graves) |
| `veiculos` | inteiro | Número de veículos envolvidos |
| `latitude` | decimal (vírgula) | Latitude do local do acidente |
| `longitude` | decimal (vírgula) | Longitude do local do acidente |
| `regional` | texto | Superintendência Regional da PRF responsável (ex: `SPRF-SP`) |
| `delegacia` | texto | Delegacia da PRF responsável (ex: `DEL01-SP`) |
| `uop` | texto | Unidade Operacional da PRF responsável (ex: `UOP01-DEL01-SP`) |

> **Observação:** os campos numéricos decimais (`km`, `latitude`, `longitude`) usam vírgula como separador decimal (padrão brasileiro), exigindo conversão antes de tratamento numérico. O arquivo de 2025 contém 72.529 registros e 30 colunas; espera-se estrutura equivalente nos demais anos (2022–2026).

#### `dados/feriados_nacionais.xls` (feriados nacionais — ANBIMA)

Arquivo Excel legado (`.xls`), com uma única planilha (`Feriados`), contendo o histórico de feriados nacionais.

| Coluna | Tipo | Descrição / unidade |
|---|---|---|
| `Data` | data (AAAA-MM-DD) | Data do feriado nacional |
| `Dia da Semana` | texto (categórico) | Dia da semana correspondente à data (ex: `segunda-feira`) |
| `Feriado` | texto | Nome do feriado (ex: `Confraternização Universal`, `Tiradentes`, `Natal`) |

> **Observação:** o arquivo contém o histórico de feriados desde 2001, permitindo o cruzamento com as datas do dataset de acidentes para identificar se um acidente ocorreu em dia de feriado.

### 4. Scripts ou processos de coleta
Código ou pipelines utilizados para extrair os dados.

- Não há scripts de coleta. Os arquivos foram baixados manualmente diretamente das fontes (PRF e ANBIMA).

### 5. Critérios de seleção dos dados
Justificativa de por que esses dados foram escolhidos (alinhamento com o problema).

- Os dados da PRF (`datatran202*.csv`, 2022 a 2026) foram selecionados por conterem registros oficiais e detalhados de acidentes de trânsito em rodovias federais, sendo a base central para a análise do problema de negócio.
- Os dados de feriados nacionais (ANBIMA) foram incluídos para permitir a análise de correlação entre datas de feriado e a ocorrência/padrão dos acidentes.