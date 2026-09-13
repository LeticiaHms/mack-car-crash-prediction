"""
Funções reutilizáveis de EDA para o dataset de acidentes da PRF (2022-2026).

Este módulo é a camada analítica compartilhada entre:
- src/eda/run.py (gera os artefatos reproduzíveis em reports/eda/, sobre a Bronze)
- src/silver/acidentes.py (reaproveita `build_bronze_views`/`consolidation_cutoff`
  para construir a camada Silver a partir da Bronze)
- app/ (consome as mesmas funções para exploração interativa, sobre a Silver)

Segue as skills `eda`, `duckdb-analytics` e `data-quality`:
- agregações pesadas são empurradas para o DuckDB (SQL sobre as tabelas do banco);
- pandas/scipy são usados apenas sobre resultados já agregados (pequenos);
- nenhuma estatística é inventada — tudo é calculado a partir do banco.

**Fonte única:** todas as leituras aqui partem de `data/prf.duckdb`
(`src/database/connection.py`) — não existe mais espelho em Parquet das camadas
processadas. A EDA (`run.py`) roda sobre o schema `bronze` de propósito: foi a
base completa (com a janela final não consolidada) que permitiu descobrir o
problema em primeiro lugar (D-13) — rodar sobre a Silver já cortada esconderia
o próprio achado.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from src.database.connection import DB_PATH, get_connection as _connect_db
from scipy import stats

CATEGORICAL_COLS = [
    "uf", "br", "municipio", "causa_acidente", "tipo_acidente",
    "classificacao_acidente", "fase_dia", "sentido_via",
    "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo",
    "dia_semana", "regional",
]

NUMERIC_COLS = [
    "pessoas", "mortos", "feridos_leves", "feridos_graves",
    "ilesos", "ignorados", "feridos", "veiculos", "km",
]

# Colunas que descrevem o RESULTADO do próprio acidente ou que só são
# apuradas depois do evento (pós-evento). Não podem ser usadas como feature
# preditiva para risco futuro de um trecho/período ainda não ocorrido —
# apenas para (a) definir o target ou (b) compor agregados históricos de
# PERÍODOS ANTERIORES. Inclui tanto o resultado direto (vítimas, veículos,
# classificação) quanto a apuração pós-evento (`causa_acidente`,
# `tipo_acidente` — as duas variáveis de maior associação com a gravidade,
# D-07) — usado como guard-rail explícito na construção da Gold
# (`src/gold/dataset_ml.py`).
LEAKAGE_COLS = [
    "mortos", "feridos_leves", "feridos_graves", "feridos",
    "ilesos", "ignorados", "pessoas", "veiculos",
    "classificacao_acidente", "causa_acidente", "tipo_acidente",
]

WEEKDAY_ORDER = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]


def build_bronze_views(con: duckdb.DuckDBPyConnection) -> None:
    """Monta, na conexão recebida, as views que a EDA e a Silver consomem,
    sempre a partir das tabelas `bronze.*` do banco oficial:

    - `acidentes`: `bronze.acidentes`, sem alteração;
    - `feriados`: `bronze.feriados` agregada por data (uma linha por data);
    - `acidentes_enriquecido`: `acidentes` + colunas derivadas usadas na EDA
      (`ano`, `mes`, `hora`, `gravidade_4`, `grave_bin`) + o contexto de
      calendário (`tipo_dia`, `nome_feriado`), que permite separar o efeito de
      feriado/véspera do efeito de dia da semana (skill `eda`, sazonalidade).

    São TEMP VIEWs: não alteram o banco em disco e funcionam tanto em conexão
    somente leitura quanto na conexão de escrita usada pelo pipeline.
    """
    con.execute("CREATE OR REPLACE TEMP VIEW acidentes AS SELECT * FROM bronze.acidentes")
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW feriados AS
        SELECT data::DATE AS data, string_agg(DISTINCT feriado, ' / ') AS feriado
        FROM bronze.feriados
        GROUP BY 1
        """
    )
    build_enriched_view(con)


def get_connection(db_path: str = DB_PATH, read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Abre uma conexão sobre o banco oficial (`data/prf.duckdb`) já com as
    views da Bronze montadas (ver `build_bronze_views`).

    Use quando não houver uma conexão à mão (ex.: `src/eda/run.py`). Dentro do
    pipeline, que já mantém uma conexão de escrita aberta, chame
    `build_bronze_views(con)` na conexão existente — o DuckDB não permite duas
    conexões com configurações diferentes para o mesmo arquivo.
    """
    con = _connect_db(db_path, read_only=read_only)
    build_bronze_views(con)
    return con


def build_enriched_view(con: duckdb.DuckDBPyConnection) -> None:
    """Cria a view `acidentes_enriquecido` a partir das views/tabelas
    `acidentes` e `feriados` já registradas em `con`.

    Separada de `build_bronze_views` para ser reutilizável por qualquer conexão
    que já tenha `acidentes`/`feriados` disponíveis com outra origem — é o que
    `app/common.py` faz para montar a visão da Bronze no dashboard, sem
    duplicar este SQL.
    """
    con.execute(
        """
        CREATE OR REPLACE TEMP VIEW acidentes_enriquecido AS
        SELECT
            a.*,
            year(a.data_inversa)  AS ano,
            month(a.data_inversa) AS mes,
            a.data_inversa::DATE  AS dia,
            date_part('hour', try_cast(a.horario AS TIME)) AS hora,
            CASE
                WHEN a.mortos > 0 THEN 'Fatal'
                WHEN a.feridos_graves > 0 THEN 'Grave (não fatal)'
                WHEN a.feridos_leves > 0 THEN 'Leve'
                ELSE 'Sem vítimas'
            END AS gravidade_4,
            CASE WHEN a.mortos > 0 OR a.feridos_graves > 0 THEN 1 ELSE 0 END AS grave_bin,
            CASE
                WHEN f.data  IS NOT NULL THEN 'Feriado'
                WHEN fv.data IS NOT NULL THEN 'Véspera de feriado'
                WHEN fp.data IS NOT NULL THEN 'Pós-feriado'
                ELSE 'Dia comum'
            END AS tipo_dia,
            coalesce(f.feriado, fv.feriado, fp.feriado) AS nome_feriado
        FROM acidentes a
        LEFT JOIN feriados f  ON a.data_inversa::DATE = f.data
        LEFT JOIN feriados fv ON a.data_inversa::DATE = (fv.data - INTERVAL 1 DAY)::DATE
        LEFT JOIN feriados fp ON a.data_inversa::DATE = (fp.data + INTERVAL 1 DAY)::DATE
        """
    )


def df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


# ---------------------------------------------------------------------------
# 1. Profiling
# ---------------------------------------------------------------------------

def dataset_overview(con) -> dict:
    row = df(con, "SELECT count(*) n, min(data_inversa) mn, max(data_inversa) mx FROM acidentes").iloc[0]
    cols = df(con, "DESCRIBE SELECT * FROM acidentes")
    per_year = df(con, "SELECT year(data_inversa) ano, count(*) n FROM acidentes GROUP BY 1 ORDER BY 1")
    return {
        "n_rows": int(row["n"]),
        "n_cols": int(len(cols)),
        "date_min": str(row["mn"]),
        "date_max": str(row["mx"]),
        "columns": cols[["column_name", "column_type"]].to_dict("records"),
        "rows_per_year": per_year.to_dict("records"),
    }


def missing_report(con) -> pd.DataFrame:
    cols = df(con, "DESCRIBE SELECT * FROM acidentes")["column_name"].tolist()
    exprs = ", ".join(f"sum(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS {c}" for c in cols)
    total = df(con, "SELECT count(*) n FROM acidentes").iloc[0]["n"]
    res = df(con, f"SELECT {exprs} FROM acidentes").T
    res.columns = ["null_count"]
    res["null_pct"] = (res["null_count"] / total * 100).round(3)
    res.index.name = "column"
    return res.reset_index()


def duplicate_report(con) -> dict:
    total = df(con, "SELECT count(*) n FROM acidentes").iloc[0]["n"]
    distinct_id = df(con, "SELECT count(distinct id) n FROM acidentes").iloc[0]["n"]
    full_dupes = df(con, "SELECT count(*) n FROM (SELECT * FROM acidentes EXCEPT SELECT DISTINCT * FROM acidentes)").iloc[0]["n"]
    return {
        "total_rows": int(total),
        "distinct_ids": int(distinct_id),
        "duplicate_ids": int(total - distinct_id),
        "fully_duplicated_rows": int(full_dupes),
    }


def cardinality_report(con, columns: list[str] = CATEGORICAL_COLS) -> pd.DataFrame:
    total = df(con, "SELECT count(*) n FROM acidentes").iloc[0]["n"]
    rows = []
    for c in columns:
        n_unique = df(con, f"SELECT count(distinct {c}) n FROM acidentes").iloc[0]["n"]
        top = df(con, f"SELECT {c} v, count(*) n FROM acidentes GROUP BY 1 ORDER BY 2 DESC LIMIT 1").iloc[0]
        rare = df(
            con,
            f"""
            SELECT count(*) n FROM (
                SELECT {c}, count(*) c FROM acidentes GROUP BY 1
            ) t WHERE c < 0.01 * {total}
            """,
        ).iloc[0]["n"]
        rows.append({
            "column": c,
            "n_unique": int(n_unique),
            "top_category": top["v"],
            "top_pct": round(top["n"] / total * 100, 2),
            "rare_categories_below_1pct": int(rare),
        })
    return pd.DataFrame(rows)


def category_frequency(con, column: str) -> pd.DataFrame:
    total = df(con, "SELECT count(*) n FROM acidentes").iloc[0]["n"]
    # ORDER BY 1 como desempate: sem ele o DuckDB devolve empates em ordem
    # não determinística e as tabelas em reports/ mudam de ordem a cada execução.
    out = df(con, f"SELECT {column} AS categoria, count(*) AS n FROM acidentes GROUP BY 1 ORDER BY 2 DESC, 1")
    out["pct"] = (out["n"] / total * 100).round(2)
    return out


# ---------------------------------------------------------------------------
# 2. Descriptive statistics
# ---------------------------------------------------------------------------

def numeric_summary(con, columns: list[str] = NUMERIC_COLS) -> pd.DataFrame:
    data = df(con, f"SELECT {', '.join(columns)} FROM acidentes")
    rows = []
    for c in columns:
        s = data[c].dropna().astype(float)
        q1, q3 = s.quantile([0.25, 0.75])
        rows.append({
            "column": c,
            "count": int(s.count()),
            "mean": s.mean(),
            "median": s.median(),
            "mode": s.mode().iloc[0] if not s.mode().empty else np.nan,
            "min": s.min(),
            "max": s.max(),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1,
            "variance": s.var(),
            "std": s.std(),
            "cv": (s.std() / s.mean()) if s.mean() else np.nan,
            "skew": stats.skew(s),
            "kurtosis": stats.kurtosis(s),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. Associations
# ---------------------------------------------------------------------------

def contingency_table(con, col_a: str, col_b: str) -> pd.DataFrame:
    q = f"""
        SELECT {col_a} AS a, {col_b} AS b, count(*) n
        FROM acidentes_enriquecido
        WHERE {col_a} IS NOT NULL AND {col_b} IS NOT NULL
        GROUP BY 1, 2
    """
    long = df(con, q)
    return long.pivot_table(index="a", columns="b", values="n", fill_value=0)


def cramers_v(confusion_matrix: pd.DataFrame) -> float:
    """Cramér's V com correção de viés (Bergsma, 2013)."""
    chi2 = stats.chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.to_numpy().sum()
    phi2 = chi2 / n
    r, k = confusion_matrix.shape
    phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1) ** 2) / (n - 1)
    kcorr = k - ((k - 1) ** 2) / (n - 1)
    denom = min((kcorr - 1), (rcorr - 1))
    if denom <= 0:
        return float("nan")
    return float(np.sqrt(phi2corr / denom))


def chi2_association(con, col_a: str, col_b: str) -> dict:
    ct = contingency_table(con, col_a, col_b)
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return {
        "var_a": col_a,
        "var_b": col_b,
        "chi2": float(chi2),
        "dof": int(dof),
        "p_value": float(p),
        "cramers_v": cramers_v(ct),
        "n": int(ct.to_numpy().sum()),
    }


def spearman_corr(con, col_a: str, col_b: str) -> dict:
    data = df(con, f"SELECT {col_a} a, {col_b} b FROM acidentes WHERE {col_a} IS NOT NULL AND {col_b} IS NOT NULL")
    rho, p = stats.spearmanr(data["a"], data["b"])
    return {"var_a": col_a, "var_b": col_b, "rho": float(rho), "p_value": float(p), "n": int(len(data))}


def kruskal_test(con, group_col: str, value_col: str) -> dict:
    data = df(con, f"SELECT {group_col} g, {value_col} v FROM acidentes_enriquecido WHERE {group_col} IS NOT NULL AND {value_col} IS NOT NULL")
    groups = [g["v"].values for _, g in data.groupby("g")]
    h, p = stats.kruskal(*groups)
    return {"group_col": group_col, "value_col": value_col, "h_stat": float(h), "p_value": float(p), "n_groups": len(groups)}


# ---------------------------------------------------------------------------
# 4. Temporal / seasonality
# ---------------------------------------------------------------------------

def counts_by(con, *group_cols: str, order_by: str | None = None) -> pd.DataFrame:
    cols = ", ".join(group_cols)
    order = order_by or cols
    return df(con, f"SELECT {cols}, count(*) n FROM acidentes_enriquecido GROUP BY {cols} ORDER BY {order}")


def severity_rate_by(con, group_col: str) -> pd.DataFrame:
    return df(
        con,
        f"""
        SELECT {group_col} AS grupo,
               count(*) AS n,
               sum(grave_bin) AS n_grave,
               round(100.0 * sum(grave_bin) / count(*), 2) AS pct_grave,
               sum(CASE WHEN mortos > 0 THEN 1 ELSE 0 END) AS n_fatal,
               round(100.0 * sum(CASE WHEN mortos > 0 THEN 1 ELSE 0 END) / count(*), 2) AS pct_fatal
        FROM acidentes_enriquecido
        WHERE {group_col} IS NOT NULL
        GROUP BY 1
        ORDER BY n DESC
        """,
    )


# ---------------------------------------------------------------------------
# 5. Anomaly detection
# ---------------------------------------------------------------------------

def iqr_outliers(series: pd.Series) -> dict:
    s = series.dropna()
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (s < lo) | (s > hi)
    return {"lower_bound": lo, "upper_bound": hi, "n_outliers": int(mask.sum()), "pct_outliers": round(mask.mean() * 100, 3)}


def zscore_outliers(series: pd.Series, threshold: float = 3.0) -> dict:
    s = series.dropna()
    z = (s - s.mean()) / s.std(ddof=0)
    mask = z.abs() > threshold
    return {"threshold": threshold, "n_outliers": int(mask.sum()), "pct_outliers": round(mask.mean() * 100, 3)}


def daily_series(con) -> pd.DataFrame:
    out = df(con, "SELECT data_inversa::DATE AS dia, count(*) n FROM acidentes GROUP BY 1 ORDER BY 1")
    out["dia"] = pd.to_datetime(out["dia"])
    out["media_movel_7d"] = out["n"].rolling(7, min_periods=1).mean()
    return out


# ---------------------------------------------------------------------------
# 6. Cobertura temporal e sentinelas (qualidade pós-limpeza)
# ---------------------------------------------------------------------------

def calendar_coverage(con) -> dict:
    """Compara o calendário esperado com os dias efetivamente observados.

    Motivo (skill `data-quality`): uma base pode não ter nenhum nulo e ainda
    assim estar incompleta — dias inteiros ausentes não aparecem como NULL,
    aparecem como "linha que não existe". Só uma comparação com o calendário
    revela esse buraco.
    """
    rng = df(con, "SELECT min(data_inversa)::DATE mn, max(data_inversa)::DATE mx FROM acidentes").iloc[0]
    obs = df(con, "SELECT DISTINCT data_inversa::DATE AS dia FROM acidentes")
    expected = pd.date_range(rng["mn"], rng["mx"], freq="D")
    observed = pd.to_datetime(obs["dia"])
    missing = expected.difference(observed)
    return {
        "date_min": str(rng["mn"]),
        "date_max": str(rng["mx"]),
        "expected_days": int(len(expected)),
        "observed_days": int(len(observed)),
        "missing_days": int(len(missing)),
        "missing_days_list": [str(d.date()) for d in missing],
    }


def consolidation_cutoff(con, ratio: float = 0.7, ref_lag_days: int = 120) -> dict:
    """Detecta a janela final ainda não consolidada da série e sugere um corte.

    Método: compara a média móvel de 7 dias do volume diário com a mediana
    histórica de referência (calculada ignorando os últimos `ref_lag_days`
    dias, que são justamente os suspeitos). O último bloco contíguo de dias
    com média móvel abaixo de `ratio` × referência é tratado como janela de
    consolidação incompleta — e não como queda real de acidentes.
    """
    daily = df(con, "SELECT data_inversa::DATE AS dia, count(*) n FROM acidentes GROUP BY 1 ORDER BY 1")
    daily["dia"] = pd.to_datetime(daily["dia"])
    full = (
        pd.DataFrame({"dia": pd.date_range(daily["dia"].min(), daily["dia"].max(), freq="D")})
        .merge(daily, on="dia", how="left")
        .fillna({"n": 0})
    )
    max_day = full["dia"].max()
    ref = float(full[full["dia"] <= max_day - pd.Timedelta(days=ref_lag_days)]["n"].median())
    full["media_movel_7d"] = full["n"].rolling(7, center=True, min_periods=4).mean()
    full["incompleto"] = full["media_movel_7d"] < ratio * ref

    idx = len(full) - 1
    if bool(full["incompleto"].iloc[idx]):
        while idx - 1 >= 0 and bool(full["incompleto"].iloc[idx - 1]):
            idx -= 1
        cutoff = full["dia"].iloc[idx - 1]
        n_days = int((max_day - cutoff).days)
    else:
        cutoff = max_day
        n_days = 0

    rows_after = int(full[full["dia"] > cutoff]["n"].sum())
    return {
        "reference_daily_median": ref,
        "ratio": ratio,
        "cutoff_date": str(cutoff.date()),
        "last_date": str(max_day.date()),
        "days_flagged": n_days,
        "rows_flagged": rows_after,
        "pct_rows_flagged": round(rows_after / max(1, int(full["n"].sum())) * 100, 3),
        "series": full,
    }


SENTINEL_RULES = [
    ("br", "br = 0", "Rodovia não identificada (não existe BR-000)"),
    ("km", "km <= 0", "Marco quilométrico não informado"),
    ("latitude", "latitude = 0 OR longitude = 0", "Coordenada nula (ponto no Golfo da Guiné)"),
    ("sentido_via", "lower(sentido_via) LIKE '%não informado%'", "Preenchimento ausente codificado como texto"),
    ("condicao_metereologica", "lower(condicao_metereologica) IN ('ignorado','ignorada')", "Condição não registrada"),
    ("regional/delegacia/uop", "regional IS NULL OR delegacia IS NULL OR uop IS NULL",
     "Unidade da PRF ausente (não afeta o local do acidente)"),
    ("tracado_via", "tracado_via LIKE '%;%'",
     "Campo multivalorado: várias características da via na mesma string, inflando a cardinalidade"),
    ("classificacao_acidente", "classificacao_acidente IS NULL", "Classificação oficial ausente"),
]


def sentinel_report(con) -> pd.DataFrame:
    """Conta valores-sentinela: 'não informado' disfarçado de valor válido.

    São mais perigosos que NULL porque entram silenciosamente em médias,
    rankings e modelos como se fossem uma categoria/medida real.
    """
    total = int(df(con, "SELECT count(*) n FROM acidentes").iloc[0]["n"])
    rows = []
    for col, cond, why in SENTINEL_RULES:
        n = int(df(con, f"SELECT count(*) n FROM acidentes WHERE {cond}").iloc[0]["n"])
        rows.append({
            "coluna": col,
            "regra": cond,
            "n": n,
            "pct": round(n / total * 100, 3),
            "por que é sentinela": why,
        })
    return pd.DataFrame(rows).sort_values("n", ascending=False)


# ---------------------------------------------------------------------------
# 7. Validação estatística de proporções (taxa de gravidade)
# ---------------------------------------------------------------------------

def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Intervalo de confiança de Wilson para uma proporção.

    Preferido ao IC normal (Wald) porque não degenera quando p→0/1 nem quando
    n é pequeno — o caso das rodovias/municípios com poucos acidentes.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (float(max(0.0, center - margin)), float(min(1.0, center + margin)))


def two_proportion_test(k1: int, n1: int, k2: int, n2: int, alpha: float = 0.05) -> dict:
    """Teste z bicaudal para diferença entre duas proporções independentes.

    Devolve o tamanho de efeito (diferença em pontos percentuais, razão de
    risco e h de Cohen) junto do p-valor — com n desta ordem de grandeza o
    p-valor sozinho é quase sempre ~0 e não informa relevância prática (D-08).
    """
    if n1 == 0 or n2 == 0:
        return {"error": "grupo vazio"}
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se_pool if se_pool > 0 else np.nan
    p_value = float(2 * (1 - stats.norm.cdf(abs(z)))) if np.isfinite(z) else float("nan")
    se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    zc = stats.norm.ppf(1 - alpha / 2)
    cohen_h = float(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2)))
    return {
        "p1": float(p1), "n1": int(n1), "k1": int(k1),
        "p2": float(p2), "n2": int(n2), "k2": int(k2),
        "diff_pp": float((p1 - p2) * 100),
        "diff_ci_pp": (float((p1 - p2 - zc * se_diff) * 100), float((p1 - p2 + zc * se_diff) * 100)),
        "risk_ratio": float(p1 / p2) if p2 > 0 else float("nan"),
        "z": float(z),
        "p_value": p_value,
        "cohen_h": cohen_h,
        "efeito": _classify_cohen_h(abs(cohen_h)),
    }


def _classify_cohen_h(h: float) -> str:
    if h < 0.2:
        return "desprezível"
    if h < 0.5:
        return "pequeno"
    if h < 0.8:
        return "médio"
    return "grande"


def standardized_rate(counts: pd.DataFrame, strata_col: str, weights: pd.Series,
                      n_col: str = "n", k_col: str = "n_grave") -> dict:
    """Padronização direta: qual seria a taxa do grupo se a composição dele
    fosse igual à da população de referência?

    Serve para separar "esse grupo é mais perigoso" de "esse grupo apenas tem
    mais do tipo de via/horário que já é mais perigoso" — o antídoto direto
    para o paradoxo de Simpson (erro nº 7 e nº 8 do guia da disciplina).
    """
    g = counts.set_index(strata_col)
    rate = (g[k_col] / g[n_col]).replace([np.inf, -np.inf], np.nan)
    w = weights.reindex(rate.index)
    mask = rate.notna() & w.notna() & (w > 0)
    if not mask.any():
        return {"crude": float("nan"), "standardized": float("nan"), "coverage": 0.0}
    w_used = w[mask] / w[mask].sum()
    crude = float(g[k_col].sum() / g[n_col].sum()) if g[n_col].sum() else float("nan")
    return {
        "crude": crude,
        "standardized": float((rate[mask] * w_used).sum()),
        "coverage": float(w[mask].sum() / w.sum()) if w.sum() else 0.0,
        "por_estrato": pd.DataFrame({
            "n": g[n_col], "taxa_grupo": rate, "peso_referencia": w,
        }).reset_index(),
    }
