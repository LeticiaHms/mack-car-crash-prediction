"""
Roteador do dashboard de EDA/ML — Acidentes PRF (2022-2026).

Executar: `streamlit run app/app.py`

Único lugar do app que chama `st.set_page_config` e `st.navigation` — as
páginas em `pages/` (e o conteúdo da Home, em `home_view.py`) não chamam
`st.set_page_config` mais, só este arquivo pode.

O menu lateral é agrupado em um fluxo de Data Science, do geral ao
específico: visão geral → qualidade/estrutura da base → exploração →
preparação para a etapa de ML. A ordem dentro de cada grupo é a ordem de
navegação; os arquivos em `pages/` continuam nomeados como antes só por
histórico/compatibilidade — quem decide agrupamento e ordem agora é este
dicionário, não mais o prefixo numérico do nome do arquivo.
"""
import streamlit as st

st.set_page_config(page_title="EDA Acidentes PRF", page_icon="🚧", layout="wide")

pg = st.navigation(
    {
        "Visão Geral": [
            st.Page("home_view.py", title="Visão Geral", icon="🚧", default=True),
            st.Page("pages/12_💡_Insights_e_Hipoteses.py", title="Insights e Hipóteses", icon="💡"),
        ],
        "Qualidade e Estrutura": [
            st.Page("pages/0_🧹_Qualidade_dos_Dados.py", title="Qualidade dos Dados", icon="🧹"),
            st.Page("pages/6_🚨_Anomalias.py", title="Anomalias", icon="🚨"),
            st.Page("pages/7_✂️_Segmentacao.py", title="Segmentação", icon="✂️"),
        ],
        "Análise Exploratória": [
            st.Page("pages/1_📊_Distribuicoes.py", title="Distribuições", icon="📊"),
            st.Page("pages/2_🎯_Gravidade.py", title="Gravidade", icon="🎯"),
            st.Page("pages/3_📈_Tendencias.py", title="Tendências", icon="📈"),
            st.Page("pages/4_🔄_Sazonalidade.py", title="Sazonalidade", icon="🔄"),
            st.Page("pages/5_🔗_Correlacoes.py", title="Correlações", icon="🔗"),
            st.Page("pages/8_🗺️_Geografia.py", title="Geografia", icon="🗺️"),
        ],
        "Preparação para ML": [
            st.Page("pages/9_🧪_Validacao_Estatistica.py", title="Validação Estatística", icon="🧪"),
            st.Page("pages/10_🧠_Features_ML.py", title="Features ML", icon="🧠"),
        ],
    }
)
pg.run()
