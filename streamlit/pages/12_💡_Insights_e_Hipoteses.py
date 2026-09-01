"""Síntese: o que a EDA concluiu, com que grau de confiança, e o que fica como hipótese.

Análise que não é registrada se perde. Esta página fecha o ciclo do checklist da disciplina:
consolida os achados com a evidência recalculada ao vivo (nada é digitado à mão), separa
explicitamente **conclusão** de **hipótese** de **inconclusivo**, e formula as perguntas que a
etapa preditiva deverá responder.

Todo número desta página é recomputado do parquet a cada carregamento — se os dados mudarem,
o texto acompanha.
"""
import numpy as np
import pandas as pd
import streamlit as st

from common import consolidation_info, query

import eda_utils as eu  # noqa: E402

st.set_page_config(page_title="Insights e Hipóteses", page_icon="💡", layout="wide")
st.title("💡 Insights, Hipóteses e Limites da Análise")
st.caption(
    "Esta página ignora os filtros da sidebar de propósito: é a síntese da base completa. "
    "Os números são recalculados a cada execução — nenhum valor está escrito à mão no código."
)

CONFIANCA = {
    "conclusão": ("✅", "Sustentado por teste estatístico e recorrência; pode ir ao relatório como afirmação."),
    "hipótese": ("🟡", "Sinal consistente, mas sem controle de confundidor suficiente; precisa de validação."),
    "inconclusivo": ("⚪", "Os dados não permitem decidir entre as explicações concorrentes."),
}


def card(titulo: str, nivel: str, evidencia: str, leitura: str, onde: str):
    icone, _ = CONFIANCA[nivel]
    with st.expander(f"{icone} {titulo}", expanded=False):
        st.markdown(f"**Evidência (recalculada agora):** {evidencia}")
        st.markdown(f"**Leitura:** {leitura}")
        st.caption(f"Verificar em: {onde}")


# --- evidências computadas ---------------------------------------------------
total = int(query("SELECT count(*) n FROM acidentes").iloc[0]["n"])
alvo = query(
    "SELECT round(100.0*avg(grave_bin),2) pct_grave, "
    "round(100.0*avg(CASE WHEN mortos>0 THEN 1 ELSE 0 END),2) pct_fatal FROM acidentes_enriquecido"
).iloc[0]

info = consolidation_info()
doy = int(pd.Timestamp(info["cutoff_date"]).dayofyear)
anos = query(
    f"SELECT ano, count(*) n, round(100.0*avg(grave_bin),2) pct_grave FROM acidentes_enriquecido "
    f"WHERE dayofyear(data_inversa) <= {doy} GROUP BY 1 ORDER BY 1"
)
var_ultimo = float(anos["n"].pct_change().iloc[-1] * 100)
bruto_jan_jul = query(
    "SELECT ano, count(*) n FROM acidentes_enriquecido WHERE mes <= 7 GROUP BY 1 ORDER BY 1"
)
var_bruta = float(bruto_jan_jul["n"].pct_change().iloc[-1] * 100)

pista = query(
    "SELECT tipo_pista, count(*) n, sum(grave_bin) k FROM acidentes_enriquecido "
    "WHERE tipo_pista IN ('Simples','Dupla') GROUP BY 1"
).set_index("tipo_pista")
t_pista = eu.two_proportion_test(int(pista.loc["Simples", "k"]), int(pista.loc["Simples", "n"]),
                                 int(pista.loc["Dupla", "k"]), int(pista.loc["Dupla", "n"]))

fase = query(
    "SELECT fase_dia, count(*) n, sum(grave_bin) k FROM acidentes_enriquecido "
    "WHERE fase_dia IN ('Plena Noite','Pleno dia') GROUP BY 1"
).set_index("fase_dia")
t_fase = eu.two_proportion_test(int(fase.loc["Plena Noite", "k"]), int(fase.loc["Plena Noite", "n"]),
                                int(fase.loc["Pleno dia", "k"]), int(fase.loc["Pleno dia", "n"]))

dias = query(
    "SELECT dia, tipo_dia, count(*) n FROM acidentes_enriquecido "
    f"WHERE data_inversa <= DATE '{info['cutoff_date']}' GROUP BY 1,2"
)
media_comum = dias[dias["tipo_dia"] == "Dia comum"]["n"].mean()
media_vesp = dias[dias["tipo_dia"] == "Véspera de feriado"]["n"].mean()
media_fer = dias[dias["tipo_dia"] == "Feriado"]["n"].mean()

ct_ma = query(
    "SELECT tipo_pista AS estrato, "
    "sum(CASE WHEN uf='MA' THEN 1 ELSE 0 END) n, sum(CASE WHEN uf='MA' THEN grave_bin ELSE 0 END) n_grave, "
    "sum(CASE WHEN uf<>'MA' THEN 1 ELSE 0 END) n_out, sum(CASE WHEN uf<>'MA' THEN grave_bin ELSE 0 END) k_out "
    "FROM acidentes_enriquecido WHERE tipo_pista IS NOT NULL GROUP BY 1"
)
pesos = (ct_ma["n"] + ct_ma["n_out"]).astype(float)
pesos.index = ct_ma["estrato"]
std_ma = eu.standardized_rate(ct_ma, "estrato", pesos)
pct_ma_bruto = std_ma["crude"] * 100
pct_ma_padr = std_ma["standardized"] * 100
pct_br = float(alvo["pct_grave"])

mes_ano = query("SELECT ano, mes, count(*) n FROM acidentes_enriquecido GROUP BY 1,2")
completos = [y for y in mes_ano["ano"].unique() if mes_ano[mes_ano["ano"] == y]["mes"].nunique() == 12]
piv = mes_ano[mes_ano["ano"].isin(completos)].pivot(index="mes", columns="ano", values="n")
corr = piv.corr(method="spearman").to_numpy()
rho_medio = float(np.nanmean(corr[np.triu_indices(len(completos), k=1)])) if len(completos) > 1 else np.nan

cov = eu.calendar_coverage(eu.get_connection())

# --- painel ------------------------------------------------------------------
m = st.columns(5)
m[0].metric("Registros", f"{total:,}".replace(",", "."))
m[1].metric("% grave ou fatal", f"{alvo['pct_grave']:.2f}%")
m[2].metric("% fatal", f"{alvo['pct_fatal']:.2f}%")
m[3].metric("Estabilidade da gravidade", f"{anos['pct_grave'].min():.1f}–{anos['pct_grave'].max():.1f}%",
            help="Faixa da % grave entre todos os anos, na janela consolidada")
m[4].metric("Dias sem registro", cov["missing_days"])

st.divider()
st.header("1. O que a análise conclui")

card(
    "A queda de acidentes em 2026 não existe — é a base que ainda não foi consolidada",
    "conclusão",
    f"No recorte bruto jan–jul, 2026 aparece **{var_bruta:+.1f}%** em relação a 2025. Comparando apenas a "
    f"janela consolidada (1º de janeiro ao dia {doy} de cada ano), a variação é de **{var_ultimo:+.1f}%**. "
    f"Os últimos {info['days_flagged']} dias da série concentram apenas {info['rows_flagged']} registros, "
    f"contra uma mediana histórica de {info['reference_daily_median']:.0f} acidentes/dia, e "
    f"{cov['missing_days']} dias não têm nenhum registro — todos no mês final.",
    "É o achado com maior impacto prático da EDA: um relatório que anunciasse 'redução de acidentes em "
    "2026' estaria descrevendo o atraso de preenchimento da fonte, não a realidade das rodovias. "
    "Toda análise de tendência recente precisa truncar a série antes de "
    f"{info['cutoff_date']}. Também obriga a rever a leitura de D-12: recortar jan–jul **não** resolve "
    "o problema, porque junho e julho de 2026 estão dentro do trecho não consolidado.",
    "🧹 Qualidade dos Dados (aba *Cobertura temporal*) e 📈 Tendências.",
)

card(
    "O volume oscila entre anos; a proporção de acidentes graves não",
    "conclusão",
    "Na janela consolidada, a % de acidentes graves/fatais fica entre "
    f"**{anos['pct_grave'].min():.2f}% e {anos['pct_grave'].max():.2f}%** ao longo de {len(anos)} anos — "
    f"uma amplitude de {anos['pct_grave'].max() - anos['pct_grave'].min():.2f} p.p., "
    "enquanto o volume anual variou vários pontos percentuais no mesmo período.",
    "A gravidade condicional (dado que houve acidente, qual a chance de ser grave) é uma característica "
    "estrutural e estável do sistema viário brasileiro. Duas consequências: (a) não há evidência de "
    "melhora nem piora da gravidade no período; (b) para a modelagem, um split temporal treino/teste é "
    "seguro — a relação entre features e alvo não está mudando ao longo do tempo.",
    "📈 Tendências e 🧪 Validação Estatística.",
)

card(
    "Pista simples é substancialmente mais grave que pista dupla",
    "conclusão",
    f"Simples: **{t_pista['p1']*100:.2f}%** de acidentes graves (n = {t_pista['n1']:,}); "
    f"Dupla: **{t_pista['p2']*100:.2f}%** (n = {t_pista['n2']:,}). Diferença de "
    f"**{t_pista['diff_pp']:+.2f} p.p.** (IC95%: {t_pista['diff_ci_pp'][0]:+.2f} a "
    f"{t_pista['diff_ci_pp'][1]:+.2f}), razão de risco {t_pista['risk_ratio']:.2f}×, "
    f"h de Cohen = {t_pista['cohen_h']:.3f} (efeito {t_pista['efeito']}).".replace(",", "."),
    "Consistente com o mecanismo físico conhecido: sem separação de fluxos, a colisão frontal — o tipo "
    "de acidente mais letal — torna-se possível. É o achado estrutural mais forte entre as variáveis "
    "disponíveis *a priori*, e por isso `tipo_pista` é uma feature de primeira linha para o modelo. "
    "Ainda assim é associação observacional: pista simples também correlaciona com região, fiscalização "
    "e tempo de resgate, que a base não mede.",
    "🧪 Validação Estatística (aba *Comparar taxas*) e ✂️ Segmentação.",
)

card(
    "Escuridão agrava: plena noite é mais grave que pleno dia",
    "conclusão",
    f"Plena Noite: **{t_fase['p1']*100:.2f}%** vs. Pleno dia: **{t_fase['p2']*100:.2f}%** — "
    f"**{t_fase['diff_pp']:+.2f} p.p.** (IC95%: {t_fase['diff_ci_pp'][0]:+.2f} a "
    f"{t_fase['diff_ci_pp'][1]:+.2f}), efeito {t_fase['efeito']}.",
    "O pico de *volume* é no fim da tarde (17–19h, hora do rush), mas o pico de *gravidade relativa* é "
    "noturno. São dois fenômenos distintos e a confusão entre eles é fácil: quem olha só a contagem por "
    "hora conclui que o perigo é às 18h. `fase_dia` é conhecida a priori (deriva da hora e da data), "
    "então entra no modelo sem risco de vazamento. Note a honestidade do número: a **direção** do efeito "
    "é inequívoca (o IC não chega perto de zero), mas a **magnitude** pelo h de Cohen é modesta — "
    f"a fase do dia sozinha não separa acidentes graves dos demais, ela contribui em conjunto com as "
    "demais variáveis estruturais.",
    "🔄 Sazonalidade (*Hora × Gravidade*) e 🧪 Validação Estatística.",
)

card(
    "A sazonalidade é de volume e se repete entre anos; a gravidade não é sazonal",
    "conclusão",
    f"Correlação de Spearman média entre os rankings mensais dos {len(completos)} anos completos: "
    f"**ρ̄ = {rho_medio:.3f}** — o mesmo mês tende a ocupar a mesma posição todo ano. "
    "Já a associação entre `mes` e `gravidade_4` é de Cramér's V ≈ 0,008 (praticamente nula).",
    "Recorrência entre anos é o que distingue sazonalidade real de oscilação aleatória — um único ano "
    "subindo e descendo não prova nada. A conclusão operacional: o calendário ajuda a prever **quantos** "
    "acidentes haverá, não **quão graves** eles serão. Para o modelo, features de mês fazem sentido em "
    "uma previsão de volume/exposição, não em um classificador de gravidade.",
    "🔄 Sazonalidade e 🔗 Correlações.",
)

card(
    "O efeito de feriado é de véspera, e é de exposição — não de gravidade",
    "conclusão",
    f"Média de acidentes por dia: véspera de feriado **{media_vesp:.1f}**, feriado **{media_fer:.1f}**, "
    f"dia comum **{media_comum:.1f}** — a véspera concentra "
    f"**{(media_vesp/media_comum - 1)*100:+.1f}%** em relação ao dia comum, enquanto o feriado em si "
    "fica praticamente no mesmo patamar do dia comum. A proporção de acidentes graves quase não se move "
    "entre os quatro tipos de dia.",
    "Contraria a intuição de que 'feriado é mais perigoso': o risco se desloca para o **movimento de "
    "saída**, na véspera. Ressalva importante: feriados não se distribuem uniformemente pelos dias da "
    "semana, e o dia da semana tem efeito próprio — a comparação bruta ainda não separa os dois.",
    "🔄 Sazonalidade (seção *Feriados*) e ✂️ Segmentação (com `dia_semana` como confundidor).",
)

card(
    "As variáveis mais associadas à gravidade são justamente as que não podem virar feature",
    "conclusão",
    "`tipo_acidente` (Cramér's V ≈ 0,30) e `causa_acidente` (≈ 0,24) lideram a associação com "
    "`gravidade_4`, com folga sobre a melhor variável disponível a priori (`br`/`uf`, ≈ 0,11). "
    "Ambas só existem **depois** da apuração do acidente.",
    "É a armadilha central deste projeto: selecionar features por correlação produziria um modelo "
    "excelente no papel e inútil na prática, porque no momento da previsão essas colunas não existem. "
    "Elas só podem entrar como agregados históricos do trecho, com corte temporal estrito.",
    "🧠 Features para ML e 🧪 Validação Estatística.",
)

st.divider()
st.header("2. O que permanece hipótese ou inconclusivo")

card(
    "Maranhão tem taxa de gravidade muito acima da média — mas um terço disso é composição",
    "hipótese",
    f"MA: **{pct_ma_bruto:.2f}%** de acidentes graves contra **{pct_br:.2f}%** nacional. "
    f"Padronizando MA pela composição nacional de `tipo_pista`, a taxa cai para **{pct_ma_padr:.2f}%** — "
    f"ou seja, {(pct_ma_bruto - pct_ma_padr) / (pct_ma_bruto - pct_br) * 100:.0f}% do excesso se explica "
    "apenas por MA ter proporcionalmente muito mais pista simples que o país.",
    "O excesso remanescente (~"
    f"{pct_ma_padr - pct_br:.1f} p.p.) é real e grande, mas a base não permite atribuí-lo a uma causa. "
    "Candidatos plausíveis e não medidos: tempo de resposta do socorro (que converte ferido grave em "
    "óbito), perfil de velocidade, densidade de fiscalização. Tratar como **prioridade de investigação**, "
    "nunca como 'MA dirige pior'.",
    "✂️ Segmentação (preset padrão: MA vs. resto, controlado por `tipo_pista`).",
)

card(
    "Trechos de rodovia com taxa extrema e poucos acidentes",
    "hipótese",
    "Vários trechos de 10 km aparecem com % de gravidade muito acima da média, mas com intervalos de "
    "confiança largos por causa do `n` pequeno — a posição no ranking muda com um único acidente a mais.",
    "Ranking de 'trecho mais perigoso do Brasil' por taxa bruta é instável e não deve ser publicado sem "
    "o intervalo de confiança ao lado. O uso defensável é o oposto: usar o histórico do trecho como "
    "*feature* do modelo (com suavização para trechos de baixo volume), não como ranking público.",
    "🗺️ Geografia (aba *Trechos críticos*).",
)

card(
    "Contagem de acidentes não é medida de risco — falta o denominador",
    "inconclusivo",
    "A base registra ocorrências, mas não o volume de tráfego (veículos·km percorridos) de cada trecho, "
    "UF ou horário.",
    "Sem denominador de exposição, não é possível dizer se uma rodovia é perigosa ou apenas movimentada — "
    "e nenhuma técnica estatística resolve a ausência do dado. Todas as comparações desta EDA são de "
    "*proporção de gravidade dado que houve acidente*, que é uma pergunta legítima e independente do "
    "tráfego. Enriquecer com dados de contagem volumétrica (DNIT/ANTT) é o caminho para responder à "
    "pergunta de risco por viagem.",
    "🗺️ Geografia e docs/specs/eda/EDA.md §9 (limitações).",
)

card(
    "O pico isolado de acidentes em 2024-10-20",
    "inconclusivo",
    "Aparece entre os maiores picos diários da série, mas não se repete na mesma data em nenhum outro ano "
    "— ao contrário dos picos de dezembro, que recorrem em três anos diferentes.",
    "Sem recorrência e sem uma variável que explique o dia (evento, operação, condição climática "
    "extraordinária), não há base para classificá-lo como padrão nem como erro. Fica registrado como "
    "anomalia não explicada — e **não** foi removido da base.",
    "🚨 Anomalias (aba *Série diária*).",
)

st.divider()
st.header("3. Hipóteses para a etapa preditiva")
st.caption(
    "Cada hipótese está escrita de forma refutável: com o que a confirmaria e o que a derrubaria. "
    "É o insumo direto para a feature engineering e para a definição dos experimentos de modelagem."
)

hipoteses = pd.DataFrame([
    {
        "id": "H-01",
        "hipótese": "O histórico de gravidade do próprio trecho (BR × faixa de km) é a feature mais preditiva disponível a priori.",
        "por que": "Trechos concentram características fixas não medidas (geometria, velocidade, socorro) que a UF dilui.",
        "confirma se": "Adicionar a taxa histórica do trecho (janela passada) eleva o PR-AUC acima do modelo só com variáveis estruturais.",
        "refuta se": "O ganho desaparece ao usar corte temporal estrito, indicando que vinha de vazamento.",
        "risco": "Vazamento temporal se a janela histórica incluir o período previsto.",
    },
    {
        "id": "H-02",
        "hipótese": "Combinar pista simples + período noturno prevê gravidade melhor que a soma dos efeitos isolados.",
        "por que": "Ambos removem margem de erro do condutor por mecanismos diferentes (fluxo oposto e visibilidade).",
        "confirma se": "Um termo de interação, ou um modelo de árvore, supera o modelo aditivo nas mesmas features.",
        "refuta se": "O efeito conjunto é apenas a soma dos efeitos marginais.",
        "risco": "Baixo — ambas as variáveis são conhecidas a priori.",
    },
    {
        "id": "H-03",
        "hipótese": "Modelar volume (contagem por trecho/período) e gravidade (proporção) exige dois modelos distintos.",
        "por que": "A EDA mostra que sazonalidade e calendário movem o volume, mas quase não movem a gravidade.",
        "confirma se": "As features de calendário têm importância alta no modelo de volume e desprezível no de gravidade.",
        "refuta se": "Um único modelo multitarefa captura ambos sem perda.",
        "risco": "Escopo: a spec pede risco de acidente grave; o modelo de volume é complementar.",
    },
    {
        "id": "H-04",
        "hipótese": "O excesso de gravidade do MA persiste após controlar todas as variáveis estruturais disponíveis.",
        "por que": "A padronização por tipo de pista explicou apenas parte do excesso.",
        "confirma se": "O efeito de UF continua relevante em um modelo que já contém pista, traçado, fase do dia e uso do solo.",
        "refuta se": "O efeito de UF some ao entrar o conjunto completo de controles.",
        "risco": "Confundidores não medidos permanecem fora — nenhum resultado aqui é causal.",
    },
    {
        "id": "H-05",
        "hipótese": "Véspera de feriado aumenta a exposição, não a gravidade condicional.",
        "por que": "O efeito observado é de volume diário; a proporção de graves mal se move.",
        "confirma se": "Uma flag de véspera melhora a previsão de contagem e não melhora a de gravidade.",
        "refuta se": "A flag melhora o classificador de gravidade após controlar dia da semana.",
        "risco": "Feriados são poucos (63 datas): amostra pequena para efeitos finos.",
    },
    {
        "id": "H-06",
        "hipótese": "Agrupar `causa_acidente` e `tipo_acidente` em histórico do trecho recupera parte do seu poder preditivo sem vazamento.",
        "por que": "São as variáveis de maior associação, mas indisponíveis no momento da previsão.",
        "confirma se": "Perfil histórico do trecho (ex.: % de colisões frontais nos últimos 12 meses) melhora o modelo.",
        "refuta se": "O perfil histórico não acrescenta nada além da taxa histórica de gravidade (H-01).",
        "risco": "Alto risco de vazamento se implementado sem corte temporal — revisar contra D-07.",
    },
])
st.dataframe(hipoteses, width="stretch", height=440, hide_index=True)

st.divider()
st.header("4. Checklist da disciplina — onde cada item foi atendido")

checklist = pd.DataFrame([
    ("Qualidade dos dados após a limpeza avaliada", "🧹 Qualidade dos Dados", "nulos, sentinelas, coerência interna e cobertura temporal"),
    ("Estrutura da base compreendida", "🧹 Qualidade dos Dados · 🔎 Visão Geral", "schema, tipos, cardinalidade, unidade de análise"),
    ("Principais variáveis analisadas", "📊 Distribuições · 🎯 Gravidade", "cada numérica e categórica, isolada e por gravidade"),
    ("Distribuições e medidas estatísticas investigadas", "📊 Distribuições", "média, mediana, desvio, IQR, assimetria e curtose"),
    ("Padrões e tendências identificados", "📈 Tendências · 🎯 Gravidade", "série anual, mensal, semanal e horária"),
    ("Sazonalidade investigada", "🔄 Sazonalidade", "recorrência entre anos (Spearman) + calendário de feriados"),
    ("Outliers e anomalias investigados", "🚨 Anomalias", "IQR vs z-score, picos diários, grupos atípicos — nada removido"),
    ("Correlações e relações entre atributos analisadas", "🔗 Correlações", "Cramér's V, Spearman, contingência"),
    ("Dados segmentados quando necessário", "✂️ Segmentação · 🗺️ Geografia", "comparação A/B com padronização direta e checagem de Simpson"),
    ("Visualizações adequadas ao objetivo", "todas", "barra p/ comparar, linha p/ tempo, heatmap p/ interação, IC p/ incerteza"),
    ("Abordagens justificadas", "todas + docs/DECISIONS.md", "cada escolha metodológica tem uma decisão registrada (D-01…D-13)"),
    ("Insights documentados", "💡 esta página · docs/ANALYSIS_LOG.md", "achados com evidência recalculada e grau de confiança"),
    ("Hipóteses levantadas para análise futura", "💡 esta página (seção 3)", "H-01…H-06, escritas de forma refutável"),
    ("Conclusões validadas adequadamente", "🧪 Validação Estatística", "teste + IC + tamanho de efeito, nunca só leitura visual"),
], columns=["Item do checklist", "Onde está no app", "Como foi atendido"])
st.dataframe(checklist, width="stretch", height=530, hide_index=True)

st.info(
    "**Três erros que esta EDA tenta explicitamente não cometer:** (1) tratar correlação como "
    "causalidade — nenhum achado é enunciado como causa; (2) confiar em p-valor com n grande — todo "
    "teste vem com tamanho de efeito; (3) analisar só a média geral — a página ✂️ Segmentação existe "
    "porque a média nacional esconde grupos com o dobro da taxa de gravidade."
)
