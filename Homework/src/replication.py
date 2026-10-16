"""Core replication of Card and Krueger (1994), Tables 3 and 4.

Input :  data/processed/analysis_sample.csv
Output:  results/tables/table3_employment.csv
         results/tables/table3_employment.md
         results/tables/table4_regressions.csv
         results/tables/table4_regressions.md
         results/tables/wage_distribution.csv
         results/tables/replication_check.csv

The estimator is ordinary least squares with conventional (homoskedastic)
standard errors, matching the original paper.  Robust, clustered and
randomisation-based variants are reported in the robustness extension.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    CLOSED_AS_MISSING,
    DATA_PROCESSED,
    NEW_MIN_WAGE,
    OLD_MIN_WAGE,
    TABLES,
)

# --------------------------------------------------------------------------
# Column layout of the paper's Table 3.
# --------------------------------------------------------------------------
WAGE_LOW = "Wage = $4.25 (iv)"
WAGE_MID = "Wage = $4.26-$4.99 (v)"
WAGE_HIGH = "Wage >= $5.00 (vi)"
COL_PA = "PA (i)"
COL_NJ = "NJ (ii)"
COL_DID = "Difference NJ-PA (iii)"
COL_LOWHIGH = "Low-high (vii)"
COL_MIDHIGH = "Midrange-high (viii)"

TABLE3_COLUMNS = [COL_PA, COL_NJ, COL_DID, WAGE_LOW, WAGE_MID, WAGE_HIGH, COL_LOWHIGH, COL_MIDHIGH]


# --------------------------------------------------------------------------
# Small statistics helpers.  Each returns (estimate, standard_error, n).
# --------------------------------------------------------------------------
def level_stats(series: pd.Series) -> tuple[float, float, int]:
    """Mean of a variable and the standard error of that mean."""
    s = series.dropna()
    if len(s) == 0:
        return np.nan, np.nan, 0
    return s.mean(), s.std(ddof=1) / np.sqrt(len(s)), len(s)


def change_stats(sub: pd.DataFrame, mask: pd.Series, col2: str = "fte2") -> tuple[float, float, int]:
    """Mean within-store change and the standard error of that mean."""
    diff = (sub.loc[mask, col2] - sub.loc[mask, "fte1"]).dropna()
    if len(diff) == 0:
        return np.nan, np.nan, 0
    return diff.mean(), diff.std(ddof=1) / np.sqrt(len(diff)), len(diff)


def combine(a: tuple, b: tuple, sign: int = 1) -> tuple[float, float, int]:
    """Difference between two independent estimates, a - b (or a + b)."""
    return sign * a[0] - b[0], np.sqrt(a[1] ** 2 + b[1] ** 2), min(a[2], b[2])


def fmt(value: float, se: float) -> str:
    """Format an estimate as 'value (se)', or blank when missing."""
    if pd.isna(value):
        return ""
    return f"{value:.2f}" if pd.isna(se) else f"{value:.2f} ({se:.2f})"


def _nj_wage_masks(sub: pd.DataFrame) -> dict[str, pd.Series]:
    """Wave-1 wage groups among the New Jersey stores of a given sample."""
    nj = sub.STATE == 1
    return {
        WAGE_LOW: nj & (sub.WAGE_ST == OLD_MIN_WAGE),
        WAGE_MID: nj & (sub.WAGE_ST > OLD_MIN_WAGE) & (sub.WAGE_ST < 5.00),
        WAGE_HIGH: nj & (sub.WAGE_ST >= 5.00),
    }


def table3(df: pd.DataFrame) -> pd.DataFrame:
    """Average employment before and after the rise, by state and NJ wage group.

    Rows 1-2 report levels; rows 3-5 report changes.  Row 3 uses every store
    with data in the relevant wave (an unbalanced sample).  Row 4 restricts to
    stores observed in both waves.  Row 5 additionally sets wave-2 employment
    at the four temporarily closed stores to zero.
    """
    df = df.copy()

    # Wave-2 employment with temporarily closed stores recoded to zero.
    temp_closed = df.STATUS2.isin(CLOSED_AS_MISSING)
    df["fte2_temp0"] = df.fte2
    df.loc[temp_closed & df.fte1.notna(), "fte2_temp0"] = 0.0

    groups = {COL_PA: df.STATE == 0, COL_NJ: df.STATE == 1, **_nj_wage_masks(df)}

    rows: dict[str, dict] = {}

    # ---- Rows 1-2: levels, all available observations ---------------------
    levels = {"fte1": {}, "fte2": {}}
    for col in levels:
        levels[col] = {key: level_stats(df.loc[mask, col]) for key, mask in groups.items()}

    for label, col in [
        ("1. FTE employment before, all available observations", "fte1"),
        ("2. FTE employment after, all available observations", "fte2"),
    ]:
        lv = levels[col]
        row = {key: fmt(*lv[key][:2]) for key in groups}
        row[COL_DID] = fmt(*combine(lv[COL_NJ], lv[COL_PA])[:2])
        row[COL_LOWHIGH] = fmt(*combine(lv[WAGE_LOW], lv[WAGE_HIGH])[:2])
        row[COL_MIDHIGH] = fmt(*combine(lv[WAGE_MID], lv[WAGE_HIGH])[:2])
        rows[label] = row

    # ---- Row 3: change in mean employment, unbalanced sample --------------
    chg = {key: combine(levels["fte2"][key], levels["fte1"][key]) for key in groups}
    row = {key: fmt(*chg[key][:2]) for key in groups}
    row[COL_DID] = fmt(*combine(chg[COL_NJ], chg[COL_PA])[:2])
    row[COL_LOWHIGH] = fmt(*combine(chg[WAGE_LOW], chg[WAGE_HIGH])[:2])
    row[COL_MIDHIGH] = fmt(*combine(chg[WAGE_MID], chg[WAGE_HIGH])[:2])
    rows["3. Change in mean FTE employment"] = row

    # ---- Rows 4-5: changes on restricted samples --------------------------
    balanced = df[df.fte1.notna() & df.fte2.notna()]
    balanced_closed0 = df[df.fte1.notna() & (df.fte2.notna() | temp_closed)]

    rows["4. Change in mean FTE employment, balanced sample of stores"] = _change_row(balanced)
    rows["5. Change in mean FTE employment, temporarily closed stores set to 0"] = _change_row(
        balanced_closed0, col2="fte2_temp0"
    )

    out = pd.DataFrame(rows).T.reindex(columns=TABLE3_COLUMNS)
    out.index.name = "Variable"
    return out


def _change_row(sub: pd.DataFrame, col2: str = "fte2") -> dict[str, str]:
    """One row of mean employment changes, with the DID and within-NJ contrasts."""
    groups = {COL_PA: sub.STATE == 0, COL_NJ: sub.STATE == 1, **_nj_wage_masks(sub)}
    stats = {key: change_stats(sub, mask, col2) for key, mask in groups.items()}
    row = {key: fmt(*stats[key][:2]) for key in groups}
    row[COL_DID] = fmt(*combine(stats[COL_NJ], stats[COL_PA])[:2])
    row[COL_LOWHIGH] = fmt(*combine(stats[WAGE_LOW], stats[WAGE_HIGH])[:2])
    row[COL_MIDHIGH] = fmt(*combine(stats[WAGE_MID], stats[WAGE_HIGH])[:2])
    return row


# --------------------------------------------------------------------------
# Table 4: reduced-form models for the change in employment.
# --------------------------------------------------------------------------
MODELS = {
    "(i) NJ dummy": {"regressors": ["nj"], "controls": False, "regions": False},
    "(ii) NJ dummy + controls": {"regressors": ["nj"], "controls": True, "regions": False},
    "(iii) Wage gap": {"regressors": ["gap"], "controls": False, "regions": False},
    "(iv) Wage gap + controls": {"regressors": ["gap"], "controls": True, "regions": False},
    "(v) Wage gap + controls + regions": {"regressors": ["gap"], "controls": True, "regions": True},
}


def design_matrix(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """Assemble the regressor matrix for one Table 4 column.

    Controls are three chain dummies and a company-ownership dummy.  Region
    controls are dummies for the three New Jersey regions and the two eastern
    Pennsylvania regions, as described in the paper's text.
    """
    parts = [df[spec["regressors"]].astype(float)]

    if spec["controls"]:
        chain = pd.get_dummies(df.CHAIN, prefix="chain", drop_first=True).astype(float)
        own = df[["company_owned"]].astype(float)
        parts += [chain, own]

    if spec["regions"]:
        region = pd.get_dummies(df.region, prefix="region", drop_first=True).astype(float)
        parts.append(region)

    return pd.concat(parts, axis=1)


def table4(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate the five reduced-form models of the paper's Table 4.

    Returns a tidy table with one row per model.
    """
    s = df[df.sample_table4].copy()
    y = s.fte_change

    rows = []
    for name, spec in MODELS.items():
        X = sm.add_constant(design_matrix(s, spec))
        res = sm.OLS(y, X).fit()
        key = spec["regressors"][0]
        rows.append(
            {
                "model": name,
                "regressor": key,
                "coefficient": float(res.params[key]),
                "std_error": float(res.bse[key]),
                "t_statistic": float(res.tvalues[key]),
                "p_value": float(res.pvalues[key]),
                "n": int(res.nobs),
                "r_squared": float(res.rsquared),
                "controls_pvalue": _joint_pvalue(res, X, spec),
            }
        )
    return pd.DataFrame(rows)


def _joint_pvalue(res, X: pd.DataFrame, spec: dict) -> float:
    """Joint F test that all control variables are jointly zero (Table 4 row 6)."""
    controls = [c for c in X.columns if c.startswith(("chain_", "company_owned", "region_"))]
    if not controls:
        return np.nan
    return float(res.f_test(" = 0, ".join(controls) + " = 0").pvalue)


def wage_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Starting-wage distribution by state and wave: the 'bite' of the policy."""
    rows = []
    for state, label in [(0, "Pennsylvania"), (1, "New Jersey")]:
        sub = df[df.STATE == state]
        for wave, col in [("Wave 1 (Feb-Mar 1992)", "WAGE_ST"), ("Wave 2 (Nov-Dec 1992)", "WAGE_ST2")]:
            w = sub[col].dropna()
            rows.append(
                {
                    "state": label,
                    "wave": wave,
                    "n": int(len(w)),
                    "mean": w.mean(),
                    "median": w.median(),
                    "share_at_old_minimum": float((w <= OLD_MIN_WAGE + 1e-9).mean()),
                    "share_below_new_minimum": float((w < NEW_MIN_WAGE).mean()),
                    "share_at_or_above_new_minimum": float((w >= NEW_MIN_WAGE - 1e-9).mean()),
                }
            )
    return pd.DataFrame(rows)


def markdown(df: pd.DataFrame, index_name: str = "") -> str:
    """Render a DataFrame as a GitHub-flavoured markdown table.

    Values keep the precision the analysis produced; ``markdown_rounded``
    formats a copy for display.
    """
    return _markdown(df if df.index.name else df, index_name, formatter=str)


def _markdown(df: pd.DataFrame, index_name: str, formatter) -> str:
    d = df.copy()
    d.index.name = index_name or d.index.name or "Variable"
    lines = [
        "| " + str(d.index.name) + " | " + " | ".join(str(c) for c in d.columns) + " |",
        "|" + "---|" * (len(d.columns) + 1),
    ]
    for idx, row in d.iterrows():
        cells = ["" if pd.isna(v) else formatter(v) for v in row]
        lines.append("| " + str(idx) + " | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def markdown_rounded(df: pd.DataFrame, decimals: int = 3, index_name: str = "") -> str:
    """Render a DataFrame as markdown, rounding numeric cells for display.

    Counts stay whole numbers; only genuine floating-point columns are rounded.
    """

    def fmt(value):
        if isinstance(value, (bool, np.bool_)):
            return str(value)
        if isinstance(value, (int, np.integer)):
            return str(value)
        if isinstance(value, (float, np.floating)):
            return f"{value:.{decimals}f}"
        return str(value)

    return _markdown(df, index_name, fmt)


# --------------------------------------------------------------------------
# Language switch for the markdown renderings.
#
# Table 3 is built with language-neutral labels; these two dictionaries give
# the Chinese and English renderings of them.  Table 4's rendering differs only
# in the index header.  Both language sets are written on every run so the
# repository keeps a complete mirror in each language.
# --------------------------------------------------------------------------
TABLE3_LABELS_ZH = {
    "1. FTE employment before, all available observations":
        "1. 改革前全职当量就业（全部可得样本）",
    "2. FTE employment after, all available observations":
        "2. 改革后全职当量就业（全部可得样本）",
    "3. Change in mean FTE employment": "3. 就业变化均值（非平衡样本）",
    "4. Change in mean FTE employment, balanced sample of stores":
        "4. 就业变化均值（平衡样本）",
    "5. Change in mean FTE employment, temporarily closed stores set to 0":
        "5. 就业变化均值（临时关店记为 0）",
    "PA (i)": "宾州 (i)",
    "NJ (ii)": "新泽西 (ii)",
    "Difference NJ-PA (iii)": "差分 NJ−PA (iii)",
    "Wage = $4.25 (iv)": "起薪 = 4.25 美元 (iv)",
    "Wage = $4.26-$4.99 (v)": "起薪 4.26–4.99 美元 (v)",
    "Wage >= $5.00 (vi)": "起薪 ≥ 5.00 美元 (vi)",
    "Low-high (vii)": "低−高 (vii)",
    "Midrange-high (viii)": "中−高 (viii)",
    "Variable": "变量",
}


def localise(table: pd.DataFrame, labels: dict, index_name: str) -> pd.DataFrame:
    """Return a copy of ``table`` with its index and columns renamed."""
    out = table.copy()
    out.index = [labels.get(str(i), str(i)) for i in out.index]
    out.columns = [labels.get(str(c), str(c)) for c in out.columns]
    out.index.name = index_name
    return out


def replication_check(df: pd.DataFrame, t4: pd.DataFrame) -> pd.DataFrame:
    """Side-by-side comparison of our estimates with the values stated in the paper.

    Only quantities that the supplied PDF exposes in its text layer can be
    compared automatically.  The numeric cells of the paper's Table 3 are
    stored as images, so Table 3 is checked through the figures the text
    quotes (the difference-in-differences and the group counts in the notes).
    """
    paper = {
        "(i) NJ dummy": (2.33, 1.19),
        "(ii) NJ dummy + controls": (2.30, 1.20),
        "(iii) Wage gap": (15.65, 6.08),
        "(iv) Wage gap + controls": (14.92, 6.21),
        "(v) Wage gap + controls + regions": (11.91, 7.39),
    }
    rows = []
    for key, (value, se) in paper.items():
        matched = t4[t4.model == key].iloc[0]
        ours = matched.coefficient
        ours_se = matched.std_error
        rows.append(
            {
                "quantity": f"Table 4 {key}",
                "replication": ours,
                "replication_se": ours_se,
                "paper": value,
                "paper_se": se,
                "difference": ours - value,
                "source": "AER 1994, Table 4 (text layer)",
            }
        )

    s = df[df.sample_table4]
    bal = df[df.sample_balanced]
    all_nj = df[df.STATE == 1]
    did = change_stats(bal, bal.STATE == 1)
    did_pa = change_stats(bal, bal.STATE == 0)
    did_est = combine(did, did_pa)

    rows += [
        {
            "quantity": "Table 4 sample size",
            "replication": len(s),
            "replication_se": np.nan,
            "paper": 357,
            "paper_se": np.nan,
            "difference": len(s) - 357,
            "source": "AER 1994, Table 4 notes",
        },
        {
            # The paper states this in the running text: "The relative gain
            # (the 'difference in differences' of the changes in employment)
            # is 2.76 FTE employees (or 13 percent), with a t statistic of
            # 2.03."  The implied standard error is 2.76 / 2.03 = 1.36.
            # Table 3's own cells are images in the supplied PDF, so this
            # sentence is the only machine-readable source for the number.
            "quantity": "Table 3: DID in employment change",
            "replication": did_est[0],
            "replication_se": did_est[1],
            "paper": 2.76,
            "paper_se": 1.36,
            "difference": did_est[0] - 2.76,
            "source": "AER 1994 p. 779 text (2.76 FTE, t = 2.03; SE implied by t)",
        },
        # Employment levels.  The paper's Table 2 (Means of Selected
        # Variables) is in the text layer, unlike Table 3, and its
        # employment row is directly comparable with rows 1-2 of our
        # Table 3.  It is quoted to one decimal, so agreement here is
        # agreement at the paper's own precision.
        {
            "quantity": "Employment level, NJ wave 1",
            "replication": level_stats(df.loc[df.STATE == 1, "fte1"])[0],
            "replication_se": level_stats(df.loc[df.STATE == 1, "fte1"])[1],
            "paper": 20.4,
            "paper_se": 0.51,
            "difference": level_stats(df.loc[df.STATE == 1, "fte1"])[0] - 20.4,
            "source": "AER 1994, Table 2 employment row (1 d.p.)",
        },
        {
            "quantity": "Employment level, NJ wave 2",
            "replication": level_stats(df.loc[df.STATE == 1, "fte2"])[0],
            "replication_se": level_stats(df.loc[df.STATE == 1, "fte2"])[1],
            "paper": 21.0,
            "paper_se": 0.52,
            "difference": level_stats(df.loc[df.STATE == 1, "fte2"])[0] - 21.0,
            "source": "AER 1994, Table 2 employment row (1 d.p.)",
        },
        {
            "quantity": "Employment level, PA wave 1",
            "replication": level_stats(df.loc[df.STATE == 0, "fte1"])[0],
            "replication_se": level_stats(df.loc[df.STATE == 0, "fte1"])[1],
            "paper": 23.3,
            "paper_se": np.nan,
            "difference": level_stats(df.loc[df.STATE == 0, "fte1"])[0] - 23.3,
            "source": "AER 1994 p. 776 text (1 d.p.; SE not in text layer)",
        },
        {
            "quantity": "Employment level, PA wave 2",
            "replication": level_stats(df.loc[df.STATE == 0, "fte2"])[0],
            "replication_se": level_stats(df.loc[df.STATE == 0, "fte2"])[1],
            "paper": 21.2,
            "paper_se": 0.94,
            "difference": level_stats(df.loc[df.STATE == 0, "fte2"])[0] - 21.2,
            "source": "AER 1994, Table 2 employment row (1 d.p.)",
        },
        {
            "quantity": "Mean of dependent variable",
            "replication": s.fte_change.mean(),
            "replication_se": np.nan,
            "paper": -0.237,
            "paper_se": np.nan,
            "difference": s.fte_change.mean() + 0.237,
            "source": "AER 1994, Table 4 notes",
        },
        {
            "quantity": "Std. dev. of dependent variable",
            "replication": s.fte_change.std(ddof=1),
            "replication_se": np.nan,
            "paper": 8.825,
            "paper_se": np.nan,
            "difference": s.fte_change.std(ddof=1) - 8.825,
            "source": "AER 1994, Table 4 notes",
        },
        {
            "quantity": "NJ stores with wave-1 wage = $4.25",
            "replication": int((all_nj.WAGE_ST == OLD_MIN_WAGE).sum()),
            "replication_se": np.nan,
            "paper": 101,
            "paper_se": np.nan,
            "difference": int((all_nj.WAGE_ST == OLD_MIN_WAGE).sum()) - 101,
            "source": "AER 1994, Table 3 notes",
        },
        {
            "quantity": "NJ stores with wave-1 wage $4.26-$4.99",
            "replication": int(((all_nj.WAGE_ST > OLD_MIN_WAGE) & (all_nj.WAGE_ST < 5.00)).sum()),
            "replication_se": np.nan,
            "paper": 140,
            "paper_se": np.nan,
            "difference": int(((all_nj.WAGE_ST > OLD_MIN_WAGE) & (all_nj.WAGE_ST < 5.00)).sum()) - 140,
            "source": "AER 1994, Table 3 notes",
        },
        {
            "quantity": "NJ stores with wave-1 wage >= $5.00",
            "replication": int((all_nj.WAGE_ST >= 5.00).sum()),
            "replication_se": np.nan,
            "paper": 73,
            "paper_se": np.nan,
            "difference": int((all_nj.WAGE_ST >= 5.00).sum()) - 73,
            "source": "AER 1994, Table 3 notes",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PROCESSED / "analysis_sample.csv")

    t3 = table3(df)
    t3.to_csv(TABLES / "table3_employment.csv")
    (TABLES / "table3_employment.md").write_text(
        markdown(localise(t3, TABLE3_LABELS_ZH, "变量")), encoding="utf-8"
    )
    (TABLES / "table3_employment_en.md").write_text(markdown(t3, "Variable"), encoding="utf-8")

    t4 = table4(df)
    t4.to_csv(TABLES / "table4_regressions.csv", index=False)
    display = t4.set_index("model")[
        ["regressor", "coefficient", "std_error", "t_statistic", "p_value", "n", "r_squared", "controls_pvalue"]
    ]
    (TABLES / "table4_regressions.md").write_text(
        markdown_rounded(display, index_name="模型"), encoding="utf-8"
    )
    (TABLES / "table4_regressions_en.md").write_text(
        markdown_rounded(display, index_name="Model"), encoding="utf-8"
    )

    wage_distribution(df).to_csv(TABLES / "wage_distribution.csv", index=False)

    check = replication_check(df, t4)
    check.to_csv(TABLES / "replication_check.csv", index=False)

    print("Table 3 - mean FTE employment:")
    print(t3.to_string())
    print()
    print("Table 4 - reduced-form models:")
    print(t4.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print()
    print("Replication check against the paper:")
    print(check.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
