"""Avaliação da qualidade dos dados *depois* da limpeza (etapa 1 do checklist da disciplina).

Responde a três perguntas que um `df.info()` não responde:
1. o que ainda está faltando (nulos e, principalmente, valores-sentinela)?
2. a base é internamente coerente?
3. a cobertura temporal é completa — existem dias inteiros ausentes?
"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import consolidation_info, get_connection, query

st.title("🧹 Qualidade dos Dados (pós-limpeza)")
st.caption(
    "Esta página **não** usa os filtros da sidebar: qualidade se avalia sobre a base inteira, "
    "senão o filtro esconde justamente o problema que se quer encontrar."
)

from src.eda import utils as eu  # noqa: E402

con = get_connection()
total = int(query("SELECT count(*) n FROM acidentes").iloc[0]["n"])

_info = consolidation_info()
with st.expander("ℹ️ Por que a série é cortada na camada Silver (leia antes de interpretar tendências)"):
    st.warning(
        f"""
        Os últimos {_info['days_flagged']} dias da série (após **{_info['cutoff_date']}**) contêm apenas
        {_info['rows_flagged']} registros, contra uma mediana histórica de
        {_info['reference_daily_median']:.0f} acidentes/dia — é registro ainda não consolidado na fonte da
        PRF, não redução real de acidentes. Por isso a camada **Silver** já aplica esse corte diretamente
        no dado (não é mais um filtro opcional da sidebar). A evidência completa, com a série e o funil
        Bronze → Silver, está na aba *Cobertura temporal* abaixo.
        """
    )

tab_estrutura, tab_falta, tab_coerencia, tab_cobertura = st.tabs(
    ["Estrutura", "O que falta", "Coerência interna", "Cobertura temporal"]
)

# ---------------------------------------------------------------------------
with tab_estrutura:
    st.subheader("Estrutura da base")
    cols = query("DESCRIBE SELECT * FROM acidentes")
    rng = query("SELECT min(data_inversa)::DATE mn, max(data_inversa)::DATE mx FROM acidentes").iloc[0]
    dup = eu.duplicate_report(con)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros", f"{total:,}".replace(",", "."))
    c2.metric("Colunas", len(cols))
    c3.metric("Período", f"{rng['mn']} → {rng['mx']}")
    c4.metric("IDs duplicados", dup["duplicate_ids"], delta="ok" if dup["duplicate_ids"] == 0 else "revisar",
              delta_color="normal" if dup["duplicate_ids"] == 0 else "inverse")

    st.markdown(
        "**Unidade de análise: 1 linha = 1 acidente (ocorrência)** — não é uma linha por pessoa "
        "nem por veículo. Toda média de `mortos`/`feridos` abaixo é *por acidente*."
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Tipos de dados**")
        st.dataframe(cols[["column_name", "column_type"]], width="stretch", height=380)
    with right:
        st.markdown("**Cardinalidade das categóricas**")
        card = eu.cardinality_report(con)
        card["top_category"] = card["top_category"].astype(str)  # br é numérico: Arrow exige tipo único
        st.dataframe(card, width="stretch", height=380)
        st.caption(
            "`municipio` (>2.000 categorias) e `causa_acidente` (77) são de alta cardinalidade: "
            "one-hot direto criaria uma matriz esparsa gigantesca — tratar por agrupamento ou "
            "target/ordinal encoding na etapa de feature engineering."
        )

# ---------------------------------------------------------------------------
with tab_falta:
    st.subheader("1. Nulos declarados")
    miss = eu.missing_report(con)
    miss_pos = miss[miss["null_count"] > 0].sort_values("null_count", ascending=False)
    if miss_pos.empty:
        st.success("Nenhuma coluna com valores nulos.")
    else:
        fig = px.bar(miss_pos, x="null_pct", y="column", orientation="h",
                     labels={"null_pct": "% de nulos", "column": ""},
                     title="Colunas com nulos (% do total)")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=260)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(miss_pos, width="stretch")
        st.info(
            "Os nulos restantes estão apenas em `regional`/`delegacia`/`uop` (~1%), que identificam a "
            "**unidade administrativa da PRF**, não o acidente. Nenhuma variável analítica "
            "(data, local, vítimas, via) tem nulo — a limpeza da etapa 1 fez seu trabalho."
        )

    st.divider()
    st.subheader("2. Valores-sentinela — o que *parece* preenchido mas não está")
    sent = eu.sentinel_report(con)
    st.dataframe(sent, width="stretch")
    st.warning(
        "Sentinela é mais perigoso que `NULL`: `km = 0` entra em qualquer média como se fosse uma "
        "posição real de rodovia, e `br = 0` vira uma 'rodovia' em qualquer ranking. Como não são "
        "nulos, passam despercebidos em um `isnull().sum()`. Decisões tomadas: "
        "[D-04](../docs/decisoes/DECISIONS.md) (manter `km≤0`, sinalizado) e "
        "[D-05](../docs/decisoes/DECISIONS.md) (excluir `br=0` de rankings por rodovia)."
    )

    multi = int(query("SELECT count(*) n FROM acidentes WHERE tracado_via LIKE '%;%'").iloc[0]["n"])
    n_tracado = int(query("SELECT count(DISTINCT tracado_via) n FROM acidentes").iloc[0]["n"])
    st.markdown(
        f"**Caso especial — `tracado_via` é multivalorada:** {multi:,} registros "
        f"({multi/total*100:.1f}%) trazem várias características na mesma string "
        "(ex.: `Reta;Declive`), o que infla a coluna para "
        f"{n_tracado} 'categorias' que na verdade são combinações de poucas primitivas. "
        "Para modelagem, o correto é **multi-hot** (uma coluna binária por primitiva), não one-hot da string inteira."
        .replace(",", ".")
    )
    prim = query(
        """
        SELECT trim(p) AS primitiva, count(*) n
        FROM acidentes, unnest(string_split(tracado_via, ';')) AS t(p)
        GROUP BY 1 ORDER BY 2 DESC
        """
    )
    fig = px.bar(prim, x="n", y="primitiva", orientation="h",
                 title="Primitivas reais de tracado_via (após separar por ';')")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
with tab_coerencia:
    st.subheader("As colunas contam a mesma história entre si?")
    checks = query(
        """
        SELECT
          sum(CASE WHEN pessoas <> (mortos+feridos_leves+feridos_graves+ilesos+ignorados) THEN 1 ELSE 0 END) AS soma_vitimas,
          sum(CASE WHEN feridos <> (feridos_leves+feridos_graves) THEN 1 ELSE 0 END) AS feridos_total,
          sum(CASE WHEN classificacao_acidente = 'Sem Vítimas' AND (mortos+feridos) > 0 THEN 1 ELSE 0 END) AS sem_vitimas_com_vitima,
          sum(CASE WHEN classificacao_acidente = 'Com Vítimas Fatais' AND mortos = 0 THEN 1 ELSE 0 END) AS fatal_sem_morto,
          sum(CASE WHEN veiculos = 0 THEN 1 ELSE 0 END) AS zero_veiculos,
          sum(CASE WHEN pessoas = 0 THEN 1 ELSE 0 END) AS zero_pessoas,
          sum(CASE WHEN dia_semana <> (['domingo','segunda-feira','terça-feira','quarta-feira',
                                        'quinta-feira','sexta-feira','sábado'])[dayofweek(data_inversa)+1]
                   THEN 1 ELSE 0 END) AS dia_semana_incoerente,
          sum(CASE WHEN try_cast(horario AS TIME) IS NULL THEN 1 ELSE 0 END) AS horario_invalido
        FROM acidentes
        """
    ).T
    checks.columns = ["registros"]
    checks["% do total"] = (checks["registros"] / total * 100).round(3)
    checks["regra verificada"] = [
        "pessoas = mortos + feridos_leves + feridos_graves + ilesos + ignorados",
        "feridos = feridos_leves + feridos_graves",
        "classificação 'Sem Vítimas' não pode ter morto/ferido",
        "classificação 'Com Vítimas Fatais' precisa ter mortos > 0",
        "todo acidente registrado deve envolver ≥ 1 veículo",
        "todo acidente registrado deve envolver ≥ 1 pessoa",
        "dia_semana deve bater com o dia da semana de data_inversa",
        "horario deve ser convertível para TIME",
    ]
    checks["situação"] = checks["registros"].map(lambda v: "✅ coerente" if v == 0 else "⚠️ divergência")
    st.dataframe(checks[["regra verificada", "registros", "% do total", "situação"]], width="stretch")

    n_mismatch = int(checks.loc["soma_vitimas", "registros"])
    st.markdown(
        f"""
        **Leitura crítica.** A única divergência relevante é a primeira: {n_mismatch:,} registros
        ({n_mismatch/total*100:.2f}%) em que `pessoas` não é a soma das categorias de vítimas.
        Não sabemos qual dos dois lados está errado na fonte, então nada foi imputado
        ([D-03](../docs/decisoes/DECISIONS.md)). A consequência prática é direta: **use as colunas de vítimas
        diretamente, nunca `pessoas` como se fosse o total exato.**

        O fato de `dia_semana` e `classificacao_acidente` baterem com as colunas numéricas é a
        evidência que sustenta usar `gravidade_4` (derivada de mortos/feridos) como alvo confiável.
        """.replace(",", ".")
    )

    st.divider()
    st.subheader("Coerência do domínio geográfico")
    geo = query(
        """
        SELECT
          sum(CASE WHEN latitude NOT BETWEEN -34 AND 6 THEN 1 ELSE 0 END) AS lat_fora_do_brasil,
          sum(CASE WHEN longitude NOT BETWEEN -75 AND -32 THEN 1 ELSE 0 END) AS lon_fora_do_brasil,
          sum(CASE WHEN km > 1500 THEN 1 ELSE 0 END) AS km_implausivel,
          count(DISTINCT uf) AS ufs_distintas
        FROM acidentes
        """
    )
    st.dataframe(geo, width="stretch")
    st.caption(
        "27 UFs, coordenadas dentro do retângulo do território brasileiro e `km` dentro da extensão "
        "plausível de uma BR — a camada geográfica está utilizável para a página 🗺️ Geografia."
    )

# ---------------------------------------------------------------------------
with tab_cobertura:
    st.subheader("Existem dias inteiros faltando?")
    cov = eu.calendar_coverage(con)
    c1, c2, c3 = st.columns(3)
    c1.metric("Dias esperados no calendário", cov["expected_days"])
    c2.metric("Dias com pelo menos 1 registro", cov["observed_days"])
    c3.metric("Dias ausentes", cov["missing_days"], delta_color="inverse")
    if cov["missing_days"]:
        st.markdown("**Datas sem nenhum registro:** " + ", ".join(cov["missing_days_list"]))
        st.info(
            "Um dia inteiro ausente **não aparece como nulo** — ele simplesmente não é uma linha. "
            "Só a comparação com o calendário completo revela o buraco. Repare que todos se "
            "concentram no último mês da série: é o sintoma do problema diagnosticado abaixo."
        )

    st.divider()
    st.subheader("A série termina de verdade ou apenas para de ser preenchida?")
    info = eu.consolidation_cutoff(con)
    series = info.pop("series")

    fig = go.Figure()
    fig.add_scatter(x=series["dia"], y=series["n"], mode="lines", name="Acidentes/dia", opacity=0.35)
    fig.add_scatter(x=series["dia"], y=series["media_movel_7d"], mode="lines",
                    name="Média móvel 7d", line=dict(width=2))
    fig.add_hline(y=info["reference_daily_median"], line_dash="dot",
                  annotation_text=f"mediana histórica ({info['reference_daily_median']:.0f}/dia)")
    fig.add_vrect(x0=info["cutoff_date"], x1=info["last_date"], fillcolor="red", opacity=0.15,
                  line_width=0, annotation_text="janela não consolidada", annotation_position="top left")
    fig.update_layout(title="Volume diário e a janela final suspeita", height=420)
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3 = st.columns(3)
    c1.metric("Corte sugerido", info["cutoff_date"])
    c2.metric("Dias afetados", info["days_flagged"])
    c3.metric("Registros na janela", f"{info['rows_flagged']:,}".replace(",", "."))

    ult = query(
        """
        SELECT year(data_inversa) ano, month(data_inversa) mes, count(*) n,
               count(DISTINCT data_inversa::DATE) dias,
               round(count(*)*1.0/count(DISTINCT data_inversa::DATE), 1) media_dia
        FROM acidentes WHERE data_inversa >= DATE '2026-01-01'
        GROUP BY 1,2 ORDER BY 1,2
        """
    )
    st.markdown("**Volume médio diário nos meses finais da série:**")
    st.dataframe(ult, width="stretch")

    st.error(
        f"""
        **Achado de qualidade com impacto direto na interpretação.** A queda de volume no fim da
        série não é gradual: ela desaba nos últimos {info['days_flagged']} dias, e o último mês tem
        média diária de poucos acidentes contra ~{info['reference_daily_median']:.0f} do histórico.
        Nenhuma melhoria de segurança viária produz esse formato — é a assinatura de
        **registro ainda não consolidado na fonte** (ocorrências que ainda serão inseridas).

        **Consequência:** ler "queda de acidentes em 2026" a partir do volume bruto é uma conclusão
        falsa. Use o filtro **"Excluir janela não consolidada"** na sidebar antes de qualquer
        leitura de tendência recente — o efeito está quantificado na página 📈 Tendências.
        """
    )
