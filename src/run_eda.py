"""
Orquestra a Análise Exploratória de Dados (EDA) completa do dataset curado de
acidentes da PRF e grava artefatos reproduzíveis em `reports/eda/`.

Uso:
    python src/run_eda.py

Saídas:
    reports/eda/eda_results.json   -> todos os números citados em docs/specs/eda/EDA.md,
                                       docs/ANALYSIS_LOG.md e docs/DECISIONS.md
    reports/eda/tables/*.csv       -> tabelas de apoio (contingência, séries)

Nenhum número em docs/specs/eda/EDA.md, docs/ANALYSIS_LOG.md ou docs/DECISIONS.md deve
ser digitado à mão sem vir deste script (skill `eda`, regra de reprodutibilidade).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy import stats

from eda_utils import (
    CATEGORICAL_COLS,
    NUMERIC_COLS,
    calendar_coverage,
    cardinality_report,
    category_frequency,
    chi2_association,
    consolidation_cutoff,
    contingency_table,
    counts_by,
    daily_series,
    dataset_overview,
    df,
    duplicate_report,
    get_connection,
    iqr_outliers,
    kruskal_test,
    missing_report,
    numeric_summary,
    sentinel_report,
    severity_rate_by,
    spearman_corr,
    standardized_rate,
    two_proportion_test,
    wilson_ci,
    zscore_outliers,
)

OUT_DIR = "reports/eda"
TABLES_DIR = os.path.join(OUT_DIR, "tables")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    raise TypeError(f"Not serializable: {type(o)}")


def main():
    os.makedirs(TABLES_DIR, exist_ok=True)
    con = get_connection()
    results: dict = {}

    # ---- 1. Profiling -----------------------------------------------------
    results["overview"] = dataset_overview(con)
    results["missing"] = missing_report(con).to_dict("records")
    results["duplicates"] = duplicate_report(con)
    results["cardinality"] = cardinality_report(con).to_dict("records")

    # Consistência interna (pessoas = mortos+leves+graves+ilesos+ignorados)
    mismatch = df(
        con,
        """
        SELECT
          sum(CASE WHEN pessoas <> (mortos+feridos_leves+feridos_graves+ilesos+ignorados) THEN 1 ELSE 0 END) AS mismatch,
          count(*) AS total
        FROM acidentes
        """,
    ).iloc[0]
    results["consistency_pessoas_vs_vitimas"] = {
        "mismatch": int(mismatch["mismatch"]),
        "total": int(mismatch["total"]),
        "pct_mismatch": round(mismatch["mismatch"] / mismatch["total"] * 100, 3),
    }

    km_zero = df(con, "SELECT count(*) n FROM acidentes WHERE km <= 0").iloc[0]["n"]
    results["km_zero_or_negative"] = {"n": int(km_zero), "pct": round(km_zero / results["overview"]["n_rows"] * 100, 3)}

    # ---- 2. Descriptive statistics ----------------------------------------
    results["numeric_summary"] = numeric_summary(con).to_dict("records")

    cat_freqs = {}
    for c in ["classificacao_acidente", "fase_dia", "condicao_metereologica", "tipo_pista",
              "sentido_via", "uso_solo", "dia_semana", "uf", "tipo_acidente", "causa_acidente"]:
        f = category_frequency(con, c)
        cat_freqs[c] = f.head(20).to_dict("records")
        f.to_csv(os.path.join(TABLES_DIR, f"freq_{c}.csv"), index=False)
    results["categorical_frequencies_top20"] = cat_freqs

    # ---- 3. Target analysis -------------------------------------------------
    gravidade_4 = df(con, "SELECT gravidade_4 AS categoria, count(*) n FROM acidentes_enriquecido GROUP BY 1 ORDER BY 2 DESC")
    total_n = results["overview"]["n_rows"]
    gravidade_4["pct"] = (gravidade_4["n"] / total_n * 100).round(2)
    results["target_gravidade_4"] = gravidade_4.to_dict("records")

    grave_bin = df(con, "SELECT grave_bin, count(*) n FROM acidentes_enriquecido GROUP BY 1 ORDER BY 1")
    grave_bin["pct"] = (grave_bin["n"] / total_n * 100).round(2)
    results["target_grave_bin"] = grave_bin.to_dict("records")

    results["target_by_year"] = counts_by(con, "ano", "gravidade_4", order_by="ano").to_dict("records")

    # ---- 4/6/7. Pattern & association analysis (gravidade x explicativas) --
    assoc_targets = ["uf", "br", "tipo_acidente", "causa_acidente", "condicao_metereologica",
                      "tipo_pista", "tracado_via", "fase_dia", "dia_semana", "sentido_via",
                      "uso_solo", "mes", "hora"]
    assoc_results = []
    severity_by = {}
    for col in assoc_targets:
        try:
            assoc_results.append(chi2_association(con, "gravidade_4", col))
        except Exception as e:  # pragma: no cover
            assoc_results.append({"var_a": "gravidade_4", "var_b": col, "error": str(e)})
        severity_by[col] = severity_rate_by(con, col).to_dict("records")
    results["chi2_gravidade_vs_explicativas"] = assoc_results
    results["severity_rate_by_column"] = severity_by

    # Spearman entre variáveis numéricas de contagem
    numeric_pairs = [("pessoas", "veiculos"), ("veiculos", "mortos"), ("pessoas", "mortos"),
                      ("feridos_graves", "veiculos"), ("km", "mortos")]
    results["spearman_numeric_pairs"] = [spearman_corr(con, a, b) for a, b in numeric_pairs]

    # Kruskal-Wallis: nº de veículos difere entre classes de gravidade?
    results["kruskal_veiculos_por_gravidade"] = kruskal_test(con, "gravidade_4", "veiculos")
    results["kruskal_pessoas_por_gravidade"] = kruskal_test(con, "gravidade_4", "pessoas")

    # Contingência completa gravidade x uf e gravidade x tipo_acidente (para o app)
    contingency_table(con, "gravidade_4", "uf").to_csv(os.path.join(TABLES_DIR, "ct_gravidade_uf.csv"))
    contingency_table(con, "gravidade_4", "tipo_acidente").to_csv(os.path.join(TABLES_DIR, "ct_gravidade_tipo_acidente.csv"))
    contingency_table(con, "gravidade_4", "condicao_metereologica").to_csv(os.path.join(TABLES_DIR, "ct_gravidade_clima.csv"))
    contingency_table(con, "gravidade_4", "fase_dia").to_csv(os.path.join(TABLES_DIR, "ct_gravidade_fase_dia.csv"))

    # ---- 5. Temporal trends --------------------------------------------------
    by_year = counts_by(con, "ano")
    by_year.to_csv(os.path.join(TABLES_DIR, "by_year.csv"), index=False)
    results["accidents_by_year"] = by_year.to_dict("records")

    # Comparação justa Jan-Jul (2026 só tem dados até julho)
    jan_jul = df(con, "SELECT ano, count(*) n FROM acidentes_enriquecido WHERE mes <= 7 GROUP BY 1 ORDER BY 1")
    results["accidents_jan_jul_by_year"] = jan_jul.to_dict("records")

    by_month = counts_by(con, "mes")
    results["accidents_by_month"] = by_month.to_dict("records")

    by_weekday = df(con, "SELECT dia_semana, count(*) n FROM acidentes GROUP BY 1")
    results["accidents_by_weekday"] = by_weekday.to_dict("records")

    by_hour = counts_by(con, "hora")
    results["accidents_by_hour"] = by_hour.to_dict("records")

    grave_by_year = df(
        con,
        "SELECT ano, count(*) n, sum(grave_bin) n_grave, round(100.0*sum(grave_bin)/count(*),2) pct_grave "
        "FROM acidentes_enriquecido GROUP BY 1 ORDER BY 1",
    )
    results["grave_pct_by_year"] = grave_by_year.to_dict("records")
    grave_by_year_jan_jul = df(
        con,
        "SELECT ano, count(*) n, sum(grave_bin) n_grave, round(100.0*sum(grave_bin)/count(*),2) pct_grave "
        "FROM acidentes_enriquecido WHERE mes <= 7 GROUP BY 1 ORDER BY 1",
    )
    results["grave_pct_by_year_jan_jul"] = grave_by_year_jan_jul.to_dict("records")

    daily = daily_series(con)
    daily.to_csv(os.path.join(TABLES_DIR, "daily_series.csv"), index=False)

    # ---- 6. Seasonality -------------------------------------------------------
    month_year = df(con, "SELECT ano, mes, count(*) n FROM acidentes_enriquecido GROUP BY 1,2 ORDER BY 1,2")
    month_year.to_csv(os.path.join(TABLES_DIR, "heatmap_mes_ano.csv"), index=False)

    weekday_hour = df(con, "SELECT dia_semana, hora, count(*) n FROM acidentes_enriquecido GROUP BY 1,2 ORDER BY 1,2")
    weekday_hour.to_csv(os.path.join(TABLES_DIR, "heatmap_diasemana_hora.csv"), index=False)

    # Recorrência: mesmo mês tem rank de volume semelhante entre anos completos?
    complete_years = [y for y in [2022, 2023, 2024, 2025] if y in month_year["ano"].unique()]
    pivot = month_year[month_year["ano"].isin(complete_years)].pivot(index="mes", columns="ano", values="n")
    month_rank_corr = pivot.corr(method="spearman")
    month_rank_corr.to_csv(os.path.join(TABLES_DIR, "month_rank_correlation_between_years.csv"))
    results["month_pattern_spearman_between_years"] = {
        "years_compared": complete_years,
        "mean_pairwise_spearman": float(np.nanmean(month_rank_corr.to_numpy()[np.triu_indices(len(complete_years), k=1)])) if len(complete_years) > 1 else None,
    }

    # ---- 7. Anomaly detection --------------------------------------------------
    raw_numeric = df(con, f"SELECT {', '.join(NUMERIC_COLS)} FROM acidentes")
    anomalies = {}
    for c in NUMERIC_COLS:
        anomalies[c] = {"iqr": iqr_outliers(raw_numeric[c]), "zscore": zscore_outliers(raw_numeric[c])}
    results["numeric_anomalies"] = anomalies

    daily_iqr = iqr_outliers(daily["n"])
    results["daily_count_anomalies_iqr"] = daily_iqr
    spike_days = daily[(daily["n"] > daily_iqr["upper_bound"])].sort_values("n", ascending=False)
    spike_days.to_csv(os.path.join(TABLES_DIR, "spike_days.csv"), index=False)
    results["top_spike_days"] = spike_days.head(15).assign(dia=lambda d: d["dia"].astype(str)).to_dict("records")

    # Estados com taxa de gravidade atípica (z-score sobre pct_grave por UF, min 200 registros)
    uf_rate = severity_rate_by(con, "uf")
    uf_rate = uf_rate[uf_rate["n"] >= 200].copy()
    uf_rate["z_pct_grave"] = (uf_rate["pct_grave"] - uf_rate["pct_grave"].mean()) / uf_rate["pct_grave"].std(ddof=0)
    uf_rate.to_csv(os.path.join(TABLES_DIR, "uf_severity_rate.csv"), index=False)
    results["uf_severity_outliers"] = uf_rate[uf_rate["z_pct_grave"].abs() > 2].sort_values("z_pct_grave").to_dict("records")

    # BR com comportamento atípico (mesma lógica, min 200 registros)
    br_rate = severity_rate_by(con, "br")
    br_rate = br_rate[br_rate["n"] >= 200].copy()
    br_rate["z_pct_grave"] = (br_rate["pct_grave"] - br_rate["pct_grave"].mean()) / br_rate["pct_grave"].std(ddof=0)
    br_rate.to_csv(os.path.join(TABLES_DIR, "br_severity_rate.csv"), index=False)
    results["br_severity_outliers"] = br_rate[br_rate["z_pct_grave"].abs() > 2].sort_values("z_pct_grave").to_dict("records")

    # ---- 8. Cobertura temporal e consolidação da fonte -----------------------
    # Uma base pode não ter nenhum nulo e mesmo assim estar incompleta: dias inteiros
    # ausentes não viram NULL, viram linhas inexistentes.
    results["calendar_coverage"] = calendar_coverage(con)

    cutoff = consolidation_cutoff(con)
    cutoff_series = cutoff.pop("series")
    cutoff_series.to_csv(os.path.join(TABLES_DIR, "daily_series_consolidacao.csv"), index=False)
    results["consolidation_window"] = cutoff

    # Comparação entre anos usando só a janela efetivamente consolidada de cada ano
    doy = pd.Timestamp(cutoff["cutoff_date"]).dayofyear
    consolidado = df(
        con,
        f"""
        SELECT ano, count(*) n, sum(grave_bin) n_grave,
               round(100.0*sum(grave_bin)/count(*), 2) pct_grave
        FROM acidentes_enriquecido
        WHERE dayofyear(data_inversa) <= {doy}
        GROUP BY 1 ORDER BY 1
        """,
    )
    consolidado["pct_change_vs_ano_anterior"] = (
        (consolidado["n"].pct_change() * 100).round(2).astype(object).where(lambda c: c.notna(), None)
    )
    consolidado.to_csv(os.path.join(TABLES_DIR, "by_year_janela_consolidada.csv"), index=False)
    results["accidents_by_year_consolidated_window"] = {
        "day_of_year_cutoff": int(doy),
        "rows": consolidado.to_dict("records"),
    }

    results["sentinel_values"] = sentinel_report(con).to_dict("records")

    # ---- 9. Feriados ----------------------------------------------------------
    daily_tipo = df(
        con,
        f"""
        SELECT dia, tipo_dia, dia_semana, count(*) n, sum(grave_bin) k
        FROM acidentes_enriquecido
        WHERE data_inversa <= DATE '{cutoff["cutoff_date"]}'
        GROUP BY 1,2,3
        """,
    )
    resumo_tipo = (
        daily_tipo.groupby("tipo_dia")
        .agg(dias=("dia", "nunique"), acidentes=("n", "sum"), graves=("k", "sum"),
             media_acidentes_dia=("n", "mean"))
        .reset_index()
    )
    resumo_tipo["pct_grave"] = (resumo_tipo["graves"] / resumo_tipo["acidentes"] * 100).round(2)
    resumo_tipo["media_acidentes_dia"] = resumo_tipo["media_acidentes_dia"].round(2)
    resumo_tipo.to_csv(os.path.join(TABLES_DIR, "tipo_dia_feriado.csv"), index=False)

    comuns = daily_tipo[daily_tipo["tipo_dia"] == "Dia comum"]
    testes_feriado = []
    for tipo in ["Véspera de feriado", "Feriado", "Pós-feriado"]:
        sub = daily_tipo[daily_tipo["tipo_dia"] == tipo]
        if len(sub) < 5:
            continue
        u, p_u = stats.mannwhitneyu(sub["n"].to_numpy(float), comuns["n"].to_numpy(float),
                                    alternative="two-sided")
        prop = two_proportion_test(int(sub["k"].sum()), int(sub["n"].sum()),
                                   int(comuns["k"].sum()), int(comuns["n"].sum()))
        testes_feriado.append({
            "tipo_dia": tipo,
            "dias": int(sub["dia"].nunique()),
            "media_acidentes_dia": round(float(sub["n"].mean()), 2),
            "diff_volume_pct_vs_dia_comum": round(float(sub["n"].mean() / comuns["n"].mean() - 1) * 100, 2),
            "mannwhitney_u": float(u),
            "mannwhitney_p": float(p_u),
            "grave_diff_pp": round(prop["diff_pp"], 3),
            "grave_diff_ci_pp": [round(v, 3) for v in prop["diff_ci_pp"]],
            "grave_p_value": prop["p_value"],
        })
    results["holiday_effect"] = {
        "por_tipo_de_dia": resumo_tipo.to_dict("records"),
        "testes_vs_dia_comum": testes_feriado,
    }

    # ---- 10. Validação estatística dos principais contrastes -------------------
    contrastes = [("tipo_pista", "Simples", "Dupla"), ("fase_dia", "Plena Noite", "Pleno dia")]
    validacao = []
    for col, a, b in contrastes:
        row = df(
            con,
            f"SELECT {col} AS c, count(*) n, sum(grave_bin) k FROM acidentes_enriquecido "
            f"WHERE {col} IN ('{a}', '{b}') GROUP BY 1",
        ).set_index("c")
        if a in row.index and b in row.index:
            res = two_proportion_test(int(row.loc[a, "k"]), int(row.loc[a, "n"]),
                                      int(row.loc[b, "k"]), int(row.loc[b, "n"]))
            res.update({"variavel": col, "grupo_a": a, "grupo_b": b})
            validacao.append(res)
    results["two_proportion_tests"] = validacao

    # Padronização direta: quanto do excesso de gravidade do MA é composição de tipo_pista?
    ct_ma = df(
        con,
        """
        SELECT tipo_pista AS estrato,
               sum(CASE WHEN uf = 'MA' THEN 1 ELSE 0 END) n,
               sum(CASE WHEN uf = 'MA' THEN grave_bin ELSE 0 END) n_grave,
               sum(CASE WHEN uf <> 'MA' THEN 1 ELSE 0 END) n_fora
        FROM acidentes_enriquecido WHERE tipo_pista IS NOT NULL GROUP BY 1
        """,
    )
    pesos = (ct_ma["n"] + ct_ma["n_fora"]).astype(float)
    pesos.index = ct_ma["estrato"]
    std = standardized_rate(ct_ma, "estrato", pesos)
    nacional = float(df(con, "SELECT avg(grave_bin) p FROM acidentes_enriquecido").iloc[0]["p"])
    results["ma_standardization"] = {
        "strata": "tipo_pista",
        "crude_rate_ma": round(std["crude"] * 100, 2),
        "standardized_rate_ma": round(std["standardized"] * 100, 2),
        "national_rate": round(nacional * 100, 2),
        "excess_explained_by_composition_pct": round(
            (std["crude"] - std["standardized"]) / (std["crude"] - nacional) * 100, 1
        ),
    }

    # Taxa de gravidade por UF com intervalo de confiança de Wilson
    uf_ci = severity_rate_by(con, "uf")
    ci_bounds = uf_ci.apply(lambda r: wilson_ci(int(r["n_grave"]), int(r["n"])), axis=1, result_type="expand")
    uf_ci["ic95_low"] = (ci_bounds[0] * 100).round(2)
    uf_ci["ic95_high"] = (ci_bounds[1] * 100).round(2)
    uf_ci.to_csv(os.path.join(TABLES_DIR, "uf_severity_rate_ci.csv"), index=False)
    results["uf_severity_rate_with_ci"] = uf_ci.to_dict("records")

    # ---- Save -------------------------------------------------------------
    with open(os.path.join(OUT_DIR, "eda_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=_json_default)

    print(f"EDA concluída. {len(results)} blocos de resultados salvos em {OUT_DIR}/eda_results.json")
    print(f"Tabelas auxiliares salvas em {TABLES_DIR}/")


if __name__ == "__main__":
    main()
