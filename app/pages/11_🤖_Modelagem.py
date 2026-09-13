import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import streamlit as st

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from src.ml.dataset import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, FEATURE_COLUMNS, HIGH_CARDINALITY_FEATURES, NUMERIC_FEATURES, load_gold  # noqa: E402
from src.ml.inference import predict_risk  # noqa: E402

REPORT_DIR = "reports/ml"
TABLES_DIR = os.path.join(REPORT_DIR, "tables")
FIG_DIR = os.path.join(REPORT_DIR, "figures")

# --- Traduções para deixar a página legível sem jargão técnico -------------
MODELO_NOME_AMIGAVEL = {
    "baseline_dummy": "🎲 Chute (referência)",
    "logistic_regression": "📏 Modelo simples (linear)",
    "logistic_regression_tuned": "📏 Modelo simples (ajustado)",
    "decision_tree": "🌳 Árvore de decisão",
    "random_forest": "🌲 Floresta (várias árvores)",
    "xgboost": "🚀 XGBoost (antes do ajuste)",
    "xgboost_tuned": "🏆 XGBoost (modelo final)",
}

FEATURE_NOME_AMIGAVEL = {
    "latitude": "Localização (latitude)", "longitude": "Localização (longitude)",
    "municipio": "Cidade", "tipo_pista": "Tipo de pista (simples/dupla)",
    "hora": "Hora do relógio", "hora_sin": "Horário (padrão cíclico)", "hora_cos": "Horário (padrão cíclico)",
    "fase_dia": "Período do dia (dia/noite)", "uf": "Estado (UF)", "br": "Rodovia (BR)",
    "km": "Quilômetro da via", "sentido_via": "Sentido da via", "uso_solo": "Área urbana ou rural",
    "mes": "Mês do ano", "dia_semana": "Dia da semana", "fim_de_semana": "Se é fim de semana",
    "br_valido": "Rodovia identificada?", "km_valido": "Quilômetro informado?",
    "tracado_reta": "Trecho reto", "tracado_curva": "Trecho em curva", "tracado_aclive": "Subida",
    "tracado_declive": "Descida", "tracado_interseccao_de_vias": "Cruzamento de vias",
    "tracado_retorno_regulamentado": "Retorno regulamentado", "tracado_rotatoria": "Rotatória",
    "tracado_ponte": "Ponte", "tracado_viaduto": "Viaduto", "tracado_em_obras": "Trecho em obras",
    "tracado_desvio_temporario": "Desvio temporário", "tracado_tunel": "Túnel",
}


def nome_modelo(m: str) -> str:
    return MODELO_NOME_AMIGAVEL.get(m, m)


def nome_feature(f: str) -> str:
    return FEATURE_NOME_AMIGAVEL.get(f, f)


st.title("🤖 Modelagem — o motor de previsão de risco")
st.caption(
    "Esta página traduz, em linguagem simples, os resultados dos modelos treinados na Etapa 3. "
    "Os números vêm de arquivos já calculados (`reports/ml/`) — nada é recalculado ao vivo. "
    "Quem quiser os detalhes técnicos completos encontra tudo nos expansores marcados 🔬 e em "
    "`docs/entregas/etapa3-modelagem.md`."
)

if not os.path.exists(os.path.join(TABLES_DIR, "final_comparison.csv")):
    st.warning(
        "Artefatos da Etapa 3 ainda não gerados. Rode `python -m src.ml.run_all` "
        "(e depois `python -m src.ml.feature_selection_report`) antes de abrir esta página."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(TABLES_DIR, name))


@st.cache_resource(show_spinner=False)
def load_final_model():
    with open(os.path.join(TABLES_DIR, "metrics_per_model.json"), encoding="utf-8") as f:
        split_info = json.load(f)["split_info"]
    model = joblib.load(os.path.join(REPORT_DIR, "models", "xgboost_tuned.joblib"))
    return model, split_info


final_comparison = load_table("final_comparison.csv")
feature_selection = load_table("feature_selection.csv")
model, split_info = load_final_model()
final_row = final_comparison[final_comparison["modelo"] == "xgboost_tuned"].iloc[0]

# ============================================================================
# 1. DESTAQUES — os números que mais importam, em linguagem simples
# ============================================================================
st.header("🏆 Resultado em uma frase")
st.success(
    f"O melhor modelo encontrado foi o **{nome_modelo('xgboost_tuned')}**. Ele consegue identificar "
    f"corretamente **{final_row['recall_teste']*100:.0f} de cada 100** acidentes graves que realmente "
    f"aconteceram, testado em dados que ele nunca viu durante o treino."
)

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "🚨 Acidentes graves detectados", f"{final_row['recall_teste']*100:.0f}%",
    help="Recall: de todos os acidentes graves que aconteceram de verdade, quantos o modelo conseguiu "
         "prever com antecedência. Quanto maior, menos casos graves passam despercebidos.",
)
k2.metric(
    "✅ Confiabilidade do alerta", f"{final_row['precision_teste']*100:.0f}%",
    help="Precision: das vezes que o modelo disse 'isso vai ser grave', quantas realmente foram. "
         "Quanto maior, menos alarmes falsos.",
)
k3.metric(
    "⚖️ Nota geral (F1)", f"{final_row['f1_teste']*100:.0f}/100",
    help="F1-score: uma média que equilibra os dois números acima — só é alta quando o modelo acerta "
         "muitos casos graves E não exagera nos alarmes falsos ao mesmo tempo.",
)
k4.metric(
    "📈 Poder de separação (ROC-AUC)", f"{final_row['roc_auc_teste']:.2f}",
    help="Vai de 0,50 (chute aleatório, uma moeda) a 1,00 (perfeito). Mede o quanto o modelo consegue "
         "diferenciar um acidente grave de um leve, de forma geral.",
)
st.caption(
    "Todos os números acima foram calculados sobre os **46.591 acidentes de teste** — dados de "
    "2025-10-30 a 2026-06-23, um período que o modelo nunca usou para aprender."
)

# ============================================================================
# 2. GLOSSÁRIO — o que essas palavras significam
# ============================================================================
with st.expander("📖 O que significam essas palavras? (glossário rápido)", expanded=True):
    glossario = [
        ("🚨 Recall", "De todos os acidentes graves que aconteceram, quantos o modelo conseguiu prever? "
                       "Se Recall = 60%, o modelo 'pegou' 6 em cada 10 casos graves reais."),
        ("✅ Precision (Precisão)", "Das vezes que o modelo disse 'risco alto', quantas vezes ele acertou? "
                                    "Se Precision = 37%, de cada 10 alertas, ~4 realmente eram graves."),
        ("⚖️ F1-score", "Uma nota única que combina Recall e Precision. É baixa se qualquer um dos dois "
                        "for ruim — evita escolher um modelo que só é bom em um dos dois."),
        ("🎯 Acurácia (Accuracy)", "Porcentagem de acertos totais (grave + não grave). CUIDADO: sozinha "
                                   "ela engana — um modelo 'preguiçoso' que sempre chuta 'não grave' já "
                                   "acerta ~72% só porque a maioria dos acidentes não é grave."),
        ("📈 ROC-AUC / PR-AUC", "Notas de 0,5 a 1,0 que resumem a capacidade geral do modelo de separar "
                                "os casos graves dos leves, olhando para todos os níveis de sensibilidade "
                                "possíveis, não só um ponto de corte."),
        ("🔧 Tuning (ajuste fino)", "Testar várias configurações do modelo — como girar os botões de um "
                                    "rádio até achar a melhor sintonia — para ver qual combinação funciona "
                                    "melhor nos dados de validação."),
        ("📚 Treino / Validação / Teste", "Treino = onde o modelo estuda. Validação = um 'simulado' para "
                                          "escolher a melhor versão. Teste = a prova final, com dados que "
                                          "o modelo nunca viu — é o número que realmente importa."),
        ("🎲 Baseline (referência)", "Um modelo 'bobo' que serve de régua de comparação (aqui, ele sempre "
                                     "responde 'não é grave'). Se um modelo real não superar o baseline, "
                                     "ele não está aprendendo nada de útil."),
        ("📉 Overfitting", "Quando o modelo 'decora' os dados de treino em vez de aprender o padrão geral "
                           "— tira nota ótima na prova que já viu, mas erra mais na prova nova."),
    ]
    gc1, gc2 = st.columns(2)
    for i, (termo, explicacao) in enumerate(glossario):
        alvo = gc1 if i % 2 == 0 else gc2
        alvo.markdown(f"**{termo}**")
        alvo.caption(explicacao)

st.divider()

# ============================================================================
# 3. COMPARAÇÃO ENTRE MODELOS — versão simples
# ============================================================================
st.header("🥊 Testamos 5 modelos diferentes — qual venceu?")
st.write(
    "Cada barra é a 'nota geral' (F1) de um modelo nos dados de teste — quanto maior, melhor o "
    "equilíbrio entre pegar os casos graves e não gerar alarme falso demais."
)

chart_df = final_comparison.copy()
chart_df["Modelo"] = chart_df["modelo"].map(nome_modelo)
chart_df["Nota geral (F1)"] = (chart_df["f1_teste"] * 100).round(1)
chart_df = chart_df.sort_values("Nota geral (F1)")
st.bar_chart(chart_df.set_index("Modelo")["Nota geral (F1)"], horizontal=True, color="#4C72B0")

st.caption(
    "O modelo 'Chute' fica em zero de propósito — ele nunca arrisca dizer que um acidente é grave, "
    "então nunca acerta um caso grave (mas erraria muito menos se a métrica fosse só Acurácia — "
    "é exatamente por isso que não usamos só Acurácia)."
)

with st.expander("🔬 Tabela técnica completa (todas as métricas, todos os modelos)"):
    tabela_tecnica = final_comparison.rename(columns={
        "modelo": "Modelo", "f1_treino": "F1 treino", "f1_validacao": "F1 validação", "f1_teste": "F1 teste",
        "recall_teste": "Recall teste", "precision_teste": "Precision teste",
        "roc_auc_teste": "ROC-AUC teste", "pr_auc_teste": "PR-AUC teste", "accuracy_teste": "Acurácia teste",
        "gap_treino_teste_f1": "Diferença treino-teste (overfitting)", "gap_val_teste_f1": "Diferença validação-teste",
    })
    tabela_tecnica["Modelo"] = tabela_tecnica["Modelo"].map(nome_modelo)
    st.dataframe(
        tabela_tecnica.style.format({c: "{:.4f}" for c in tabela_tecnica.columns if c != "Modelo"}),
        width="stretch",
    )
    c1, c2 = st.columns(2)
    c1.image(os.path.join(FIG_DIR, "curva_roc_teste.png"), caption="Curva ROC — quanto mais afastada da linha pontilhada, melhor.")
    c2.image(os.path.join(FIG_DIR, "curva_pr_teste.png"), caption="Curva Precision-Recall.")
    st.image(os.path.join(FIG_DIR, "overfitting_gap.png"), caption="Diferença entre nota no treino e no teste, por modelo (quanto menor, melhor generaliza).")

st.divider()

# ============================================================================
# 4. COMO O MODELO FOI TREINADO — split
# ============================================================================
st.header("📚 Como o modelo aprendeu")
st.write(
    "Separamos os acidentes em 3 grupos por data — como estudar para uma prova: parte para estudar, "
    "parte para simulado, e uma parte final que o modelo só vê depois de estar pronto (a 'prova real')."
)
cols = st.columns(3)
labels_split = [("train", "📖 Treino (estudo)"), ("val", "📝 Validação (simulado)"), ("test", "🎓 Teste (prova real)")]
for col, (name, label) in zip(cols, labels_split):
    s = split_info["splits"][name]
    col.metric(label, f"{s['n']:,}".replace(",", "."), f"{s['pct']}% da base")
    col.caption(f"{s['date_min']} → {s['date_max']} · {s['grave_bin_rate_pct']}% eram graves")
st.image(os.path.join(FIG_DIR, "distribuicao_classes.png"))
st.caption(
    "Os 3 grupos são fatias de tempo diferentes (não misturadas) — assim garantimos que o modelo é "
    "testado como seria usado de verdade: prevendo o futuro a partir do passado, nunca 'colando' com "
    "dados que só existiriam depois."
)

with st.expander("🔬 Quais informações o modelo usa? (30 características)"):
    st.write(
        "Usamos características do acidente conhecidas **antes** dele acontecer (local, tipo de pista, "
        "horário...). Nunca usamos informações que só existem **depois** do acidente (nº de feridos, "
        "causa apurada...) — isso seria 'colar a resposta' em vez de aprender a prever."
    )
    st.dataframe(feature_selection, width="stretch", height=380)

st.divider()

# ============================================================================
# 5. TUNING
# ============================================================================
st.header("🔧 Ajuste fino (tuning)")
st.write(
    "Depois de escolher os modelos mais promissores, testamos várias configurações diferentes de cada "
    "um (quantas 'árvores' usar, quão rápido aprender, etc.) para ver se melhorava o resultado — como "
    "girar os botões de um rádio até achar a melhor sintonia."
)
if os.path.exists(os.path.join(TABLES_DIR, "tuning_results.json")):
    with open(os.path.join(TABLES_DIR, "tuning_results.json"), encoding="utf-8") as f:
        tuning = json.load(f)
    tc = st.columns(len(tuning))
    for col, (nome, r) in zip(tc, tuning.items()):
        antes = r["before_tuning"]["metrics"]["val"]["f1"] * 100
        depois = r["after_tuning"]["metrics"]["val"]["f1"] * 100
        col.metric(nome_modelo(nome), f"{depois:.1f}/100", f"{depois - antes:+.2f} pontos após o ajuste")
    st.info(
        "O ajuste fino quase não mudou o resultado (menos de 1 ponto em 100). Isso é uma descoberta "
        "importante: o limite do modelo não está na configuração — está na quantidade de informação "
        "disponível. Para melhorar de verdade, precisaríamos de mais/melhores dados (ex.: histórico de "
        "acidentes de cada trecho), não de mais ajustes."
    )

st.divider()

# ============================================================================
# 6. O QUE MAIS PESA NA DECISÃO
# ============================================================================
st.header("🧠 O que mais pesa na decisão do modelo?")
st.write(
    "Testamos 'confundir' o modelo embaralhando uma característica de cada vez e vendo o quanto a nota "
    "piora — quanto maior a piora, mais aquela característica importa para a previsão."
)
perm_path = os.path.join(TABLES_DIR, "feature_importance_permutation_xgboost_tuned.csv")
if os.path.exists(perm_path):
    perm_df = pd.read_csv(perm_path).head(10).copy()
    perm_df["Característica"] = perm_df["feature"].map(nome_feature)
    perm_df["Importância"] = perm_df["importancia_permutacao_media"]
    perm_df = perm_df.sort_values("Importância")
    st.bar_chart(perm_df.set_index("Característica")["Importância"], horizontal=True, color="#55A868")
    st.caption(
        "**Localização (onde o acidente acontece) é o fator mais importante**, à frente do tipo de "
        "pista e da cidade. Isso confirma o que a análise exploratória já mostrava: gravidade varia "
        "muito de região para região."
    )

with st.expander("🔬 Importância técnica completa (nativa vs. permutação)"):
    c1, c2 = st.columns(2)
    p1 = os.path.join(FIG_DIR, "feature_importance_xgboost_tuned_nativa.png")
    p2 = os.path.join(FIG_DIR, "feature_importance_xgboost_tuned_permutacao.png")
    if os.path.exists(p1):
        c1.image(p1)
    if os.path.exists(p2):
        c2.image(p2)
    st.caption(
        "Importância nativa tende a inflar variáveis com muitas categorias (ex.: um código específico "
        "de rodovia); a permutação, calculada sobre a validação, é a leitura mais confiável."
    )

st.divider()

# ============================================================================
# 7. LIMITAÇÕES E VIÉS
# ============================================================================
st.header("⚠️ Onde o modelo funciona pior")
st.warning(
    "O modelo **não** funciona igual em todo o país. Em estados como Pará e Piauí, ele identifica "
    "corretamente mais de 90% dos acidentes graves. Em São Paulo e Rio de Janeiro, esse número cai "
    "para menos de 20%. Isso acontece porque o modelo usa o mesmo 'ponto de corte' para o Brasil "
    "inteiro, e estados com menos acidentes graves em geral acabam sendo sub-avaliados."
)
bias_path = os.path.join(FIG_DIR, "bias_recall_por_uf.png")
if os.path.exists(bias_path):
    with st.expander("🔬 Ver o gráfico técnico da diferença por estado"):
        st.image(bias_path)
        st.caption(
            "Cada ponto é um estado. Quanto mais à direita (mais acidentes graves de verdade), mais alto "
            "tende a ser o ponto (mais o modelo identifica corretamente) — evidência de que o mesmo "
            "'ponto de corte' não deveria valer para todo o país."
        )
st.caption(
    "⚠️ Importante: a base de dados não tem informações sobre as pessoas envolvidas (idade, gênero...), "
    "então não é possível avaliar viés demográfico — só o viés geográfico acima, que É mensurável."
)

st.divider()

# ============================================================================
# 8. SIMULADOR
# ============================================================================
st.header("🧪 Experimente: calcule o risco de uma situação")
st.write(
    "Escolha algumas características abaixo e veja a previsão do modelo final. As demais "
    "características usam o valor mais comum da base, só para completar a previsão."
)


@st.cache_data(show_spinner=False)
def train_defaults() -> pd.DataFrame:
    gold = load_gold()
    row = {}
    for c in NUMERIC_FEATURES:
        row[c] = gold[c].median()
    for c in CATEGORICAL_FEATURES + HIGH_CARDINALITY_FEATURES:
        row[c] = gold[c].mode().iloc[0]
    for c in BOOLEAN_FEATURES:
        row[c] = bool(gold[c].mode().iloc[0])
    return pd.DataFrame([row])


defaults = train_defaults()
gold_sample = load_gold()

with st.form("simulador_risco"):
    f1, f2, f3, f4 = st.columns(4)
    uf = f1.selectbox("Estado (UF)", sorted(gold_sample["uf"].unique()), index=0)
    tipo_pista = f2.selectbox("Tipo de pista", sorted(gold_sample["tipo_pista"].unique()))
    fase_dia = f3.selectbox("Período do dia", sorted(gold_sample["fase_dia"].unique()))
    dia_semana = f4.selectbox("Dia da semana", sorted(gold_sample["dia_semana"].unique()))
    hora = st.slider("Hora do dia", 0, 23, 19)
    submitted = st.form_submit_button("Calcular risco")

if submitted:
    row = defaults.copy()
    row["uf"] = uf
    row["tipo_pista"] = tipo_pista
    row["fase_dia"] = fase_dia
    row["dia_semana"] = dia_semana
    row["hora"] = float(hora)
    row["hora_sin"] = np.sin(2 * np.pi * hora / 24)
    row["hora_cos"] = np.cos(2 * np.pi * hora / 24)
    row["fim_de_semana"] = dia_semana in ("sábado", "domingo")

    result = predict_risk(model, row)
    prob = result["probabilidade_grave"].iloc[0]
    risco = result["risco"].iloc[0]

    cor = {"BAIXO": "green", "MÉDIO": "orange", "ALTO": "red"}[risco]
    st.metric("Probabilidade de acidente grave/fatal", f"{prob*100:.1f}%")
    st.markdown(f"### Risco: :{cor}[**{risco}**]")
    st.caption(
        "As faixas (BAIXO/MÉDIO/ALTO) comparam esta situação com o histórico — não são um julgamento "
        "de segurança viária, e lembre-se do aviso acima: em alguns estados o modelo é mais confiável "
        "do que em outros."
    )

st.divider()
st.caption(
    "📄 Relatório técnico completo, com todas as decisões metodológicas justificadas: "
    "`docs/entregas/etapa3-modelagem.md`. Código: `src/ml/`."
)
