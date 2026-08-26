"""
Funções reutilizáveis de EDA para o dataset de acidentes da PRF (2022-2026).

Este módulo é a camada analítica compartilhada entre:
- src/run_eda.py (gera os artefatos reproduzíveis em reports/eda/)
- streamlit/app.py (consome as mesmas funções para exploração interativa)

Segue as skills `eda`, `duckdb-analytics` e `data-quality`:
- agregações pesadas são empurradas para o DuckDB (SQL sobre o Parquet);
- pandas/scipy são usados apenas sobre resultados já agregados (pequenos);
- nenhuma estatística é inventada — tudo é calculado a partir do parquet curado.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

CURATED_PATH = "dados/curated/acidentes_2022_2026.parquet"

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

# Colunas que descrevem o RESULTADO do próprio acidente (pós-evento).
# Não podem ser usadas como feature preditiva para risco futuro de um
# trecho/período ainda não ocorrido — apenas para (a) definir o target
# ou (b) compor agregados históricos de PERÍODOS ANTERIORES.
LEAKAGE_COLS = [
    "mortos", "feridos_leves", "feridos_graves", "feridos",
    "ilesos", "ignorados", "pessoas", "classificacao_acidente",
]

WEEKDAY_ORDER = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]


def get_connection(path: str = CURATED_PATH) -> duckdb.DuckDBPyConnection:
    """Abre uma conexão DuckDB in-memory que enxerga o Parquet curado como uma view."""
    con = duckdb.connect(database=":memory:")
    con.execute(f"CREATE OR REPLACE VIEW acidentes AS SELECT * FROM '{path}'")
    con.execute(
        """
        CREATE OR REPLACE VIEW acidentes_enriquecido AS
        SELECT
            *,
            year(data_inversa)  AS ano,
            month(data_inversa) AS mes,
            date_part('hour', try_cast(horario AS TIME)) AS hora,
            CASE
                WHEN mortos > 0 THEN 'Fatal'
                WHEN feridos_graves > 0 THEN 'Grave (não fatal)'
                WHEN feridos_leves > 0 THEN 'Leve'
                ELSE 'Sem vítimas'
            END AS gravidade_4,
            CASE WHEN mortos > 0 OR feridos_graves > 0 THEN 1 ELSE 0 END AS grave_bin
        FROM acidentes
        """
    )
    return con


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
    out = df(con, f"SELECT {column} AS categoria, count(*) AS n FROM acidentes GROUP BY 1 ORDER BY 2 DESC")
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
