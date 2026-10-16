"""Independent extension: how sensitive is the Card-Krueger null result?

Input :  data/processed/analysis_sample.csv
Output:  results/tables/specification_curve.csv
         results/tables/randomization_inference.csv
         results/tables/placebo_tests.csv
         results/tables/balance_table.csv
         results/tables/se_sensitivity.csv
         results/tables/sensitivity_bounds.csv

Five checks are run:

1. Specification curve    - 180 defensible designs, to see how the estimate moves.
2. Randomisation inference - a design-based p-value that does not rely on OLS
                             standard errors.
3. Placebo tests          - stores the law did not bind, which should show no
                             relative employment change.
4. Balance table          - whether New Jersey and Pennsylvania looked alike
                             before the increase.
5. Sensitivity bounds     - how large an omitted confound would have to be to
                             overturn the conclusion.
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
    CLOSED_AS_ZERO,
    DATA_PROCESSED,
    N_PERMUTATIONS,
    NEW_MIN_WAGE,
    OLD_MIN_WAGE,
    SEED,
    TABLES,
)
from prepare_data import employment_outcomes


# --------------------------------------------------------------------------
# Alternative outcome variables.
# --------------------------------------------------------------------------
def add_alternative_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """Add employment outcomes built under alternative measurement choices."""
    df = df.copy()

    for weight in (0.4, 0.5, 0.6):
        built = employment_outcomes(df, weight)
        tag = int(round(weight * 100))
        df[f"fte_change_w{tag}"] = built.fte_change
        df[f"fte_growth_w{tag}"] = built.fte_growth

    # Headcount: every worker counts as one, regardless of hours.
    head1 = df.EMPFT + df.EMPPT + df.NMGRS
    head2 = df.EMPFT2 + df.EMPPT2 + df.NMGRS2
    head2 = head2.copy()
    head2[df.STATUS2.isin(CLOSED_AS_ZERO)] = 0.0
    head2[df.STATUS2.isin(CLOSED_AS_MISSING)] = np.nan
    df["headcount_change"] = head2 - head1

    return df


# --------------------------------------------------------------------------
# 1. Specification curve.
# --------------------------------------------------------------------------
SPEC_GRID = {
    "sample": ["sample_table4", "sample_balanced"],
    "outcome": [
        "fte_change_w50",
        "fte_change_w40",
        "fte_change_w60",
        "headcount_change",
        "fte_growth_w50",
    ],
    "treatment": ["nj", "gap"],
    "controls": ["none", "chain_own", "chain_own_regions"],
    "control_group": ["all_pa", "pa1_only", "exclude_pa2"],
}

OUTCOME_LABELS = {
    "fte_change_w50": "FTE change (part-time weight 0.50)",
    "fte_change_w40": "FTE change (part-time weight 0.40)",
    "fte_change_w60": "FTE change (part-time weight 0.60)",
    "headcount_change": "Headcount change (all workers count 1)",
    "fte_growth_w50": "FTE growth rate (proportional)",
}


def _restrict_control_group(df: pd.DataFrame, control_group: str) -> pd.DataFrame:
    """Apply the alternative control-group definition."""
    if control_group == "pa1_only":
        return df[(df.STATE == 1) | (df.PA1 == 1)]
    if control_group == "exclude_pa2":
        return df[df.PA2 != 1]
    return df


def estimate(
    df: pd.DataFrame,
    sample: str,
    outcome: str,
    treatment: str,
    controls: str,
    control_group: str,
) -> dict:
    """Fit one specification and return its coefficient, standard error and N.

    When the treatment is the New Jersey dummy, only the Pennsylvania region
    dummies enter as controls.  The three New Jersey region dummies sum to the
    treatment indicator, so including them alongside it would make the design
    matrix rank deficient.
    """
    d = _restrict_control_group(df, control_group)
    d = d[d[sample]]

    use_controls = controls in {"chain_own", "chain_own_regions"}
    use_regions = controls == "chain_own_regions"

    parts = [d[[treatment]].astype(float)]
    if use_controls:
        parts.append(pd.get_dummies(d.CHAIN, prefix="chain", drop_first=True).astype(float))
        parts.append(d[["company_owned"]].astype(float))
    if use_regions:
        region = pd.get_dummies(d.region, prefix="region").astype(float)
        if treatment == "nj":
            # The New Jersey region dummies are spanned by the treatment, and
            # the two Pennsylvania dummies sum to 1 - nj, so only one
            # Pennsylvania dummy can enter alongside it.  The other is the
            # reference category.
            region = region[[c for c in region.columns if c.startswith("region_PA")]]
        if region.shape[1]:
            region = region.drop(columns=[region.columns[0]])  # reference category
        parts.append(region)

    X = pd.concat(parts, axis=1)
    # Restricting the control group can leave a region dummy that never varies
    # (for example the Easton dummy when only Philadelphia stores are kept).
    # Such a column carries no information and would make the design singular.
    X = X.loc[:, X.nunique(dropna=True) > 1]

    y = d[outcome]
    X = sm.add_constant(X)
    keep = y.notna() & X.notna().all(axis=1)
    result = sm.OLS(y[keep], X[keep]).fit()

    return {
        "sample": sample,
        "outcome": outcome,
        "treatment": treatment,
        "controls": controls,
        "control_group": control_group,
        "estimate": float(result.params[treatment]),
        "std_error": float(result.bse[treatment]),
        "p_value": float(result.pvalues[treatment]),
        "ci_low": float(result.conf_int().loc[treatment, 0]),
        "ci_high": float(result.conf_int().loc[treatment, 1]),
        "n": int(result.nobs),
    }


def specification_curve(df: pd.DataFrame) -> pd.DataFrame:
    """Run every combination in SPEC_GRID and return the sorted estimates."""
    rows = []
    for sample in SPEC_GRID["sample"]:
        for outcome in SPEC_GRID["outcome"]:
            for treatment in SPEC_GRID["treatment"]:
                for controls in SPEC_GRID["controls"]:
                    for control_group in SPEC_GRID["control_group"]:
                        rows.append(estimate(df, sample, outcome, treatment, controls, control_group))

    curve = pd.DataFrame(rows)
    curve["outcome_label"] = curve.outcome.map(OUTCOME_LABELS)
    curve = curve.sort_values("estimate").reset_index(drop=True)
    curve.insert(0, "rank", np.arange(1, len(curve) + 1))
    return curve


# --------------------------------------------------------------------------
# 2. Randomisation inference.
# --------------------------------------------------------------------------
def difference_in_means(y: np.ndarray, treated: np.ndarray) -> float:
    """Simple difference in means."""
    return y[treated == 1].mean() - y[treated == 0].mean()


def randomization_inference(
    df: pd.DataFrame, n_permutations: int = N_PERMUTATIONS, seed: int = SEED
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Permutation p-values for the New Jersey dummy and for the wage gap.

    Under the sharp null of no effect, the treatment label is exchangeable
    across stores, so the observed statistic can be compared with the
    distribution obtained by reshuffling the label.  Returns the summary table
    and the full set of permuted statistics (kept for the figure).
    """
    s = df[df.sample_table4]
    rng = np.random.default_rng(seed)
    rows, null_rows = [], []

    for variable, label in [("nj", "New Jersey dummy"), ("gap", "Initial wage gap")]:
        y = s.fte_change.to_numpy()
        x = s[variable].to_numpy(dtype=float)

        # Observed statistic: the OLS slope on the treatment variable.
        observed = sm.OLS(y, sm.add_constant(x)).fit().params[1]

        null = np.empty(n_permutations)
        for i in range(n_permutations):
            x_perm = rng.permutation(x)
            null[i] = sm.OLS(y, sm.add_constant(x_perm)).fit().params[1]

        rows.append(
            {
                "variable": label,
                "observed": observed,
                "permutation_mean": null.mean(),
                "permutation_sd": null.std(ddof=1),
                "p_two_sided": float(np.mean(np.abs(null) >= abs(observed))),
                "n_permutations": n_permutations,
            }
        )
        null_rows.append(pd.DataFrame({"variable": label, "permuted_statistic": null}))

    return pd.DataFrame(rows), pd.concat(null_rows, ignore_index=True)


# --------------------------------------------------------------------------
# 3. Placebo tests.
# --------------------------------------------------------------------------
def placebo_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Falsification checks on stores the minimum wage did not bind.

    New Jersey stores that already paid at or above the new minimum in wave 1
    were not required to change their starting wage.  If the difference-in-
    differences is picking up a genuine policy effect rather than a spurious
    New Jersey-Pennsylvania difference, these stores should show no relative
    employment change.
    """
    s = df[df.sample_table4]

    groups = [
        (
            "All New Jersey stores",
            "新泽西：全部门店",
            s.STATE == 1,
            "Treated: baseline",
        ),
        (
            "NJ stores paying >= $5.05 in wave 1",
            "新泽西：改革前起薪 ≥ 5.05 美元",
            (s.STATE == 1) & (s.WAGE_ST >= NEW_MIN_WAGE - 1e-9),
            "Placebo: the law does not bind",
        ),
        (
            "NJ stores paying >= $5.00 in wave 1",
            "新泽西：改革前起薪 ≥ 5.00 美元",
            (s.STATE == 1) & (s.WAGE_ST >= 5.00 - 1e-9),
            "Placebo: barely affected",
        ),
        (
            "NJ stores paying <= $4.25 in wave 1",
            "新泽西：改革前起薪 ≤ 4.25 美元",
            (s.STATE == 1) & (s.WAGE_ST <= OLD_MIN_WAGE + 1e-9),
            "Treated: fully bound by the law",
        ),
    ]

    control = s[s.STATE == 0]
    y_c = (control.fte2 - control.fte1).dropna()

    rows = []
    for label, label_zh, treated_mask, interpretation in groups:
        y_t = (s.loc[treated_mask, "fte2"] - s.loc[treated_mask, "fte1"]).dropna()
        est = y_t.mean() - y_c.mean()
        se = np.sqrt(y_t.var(ddof=1) / len(y_t) + y_c.var(ddof=1) / len(y_c))
        rows.append(
            {
                "test": label,
                "test_zh": label_zh,
                "n_treated": len(y_t),
                "n_control": len(y_c),
                "did_estimate": est,
                "std_error": se,
                "t_statistic": est / se,
                "p_value": 2 * (1 - _normal_cdf(abs(est / se))),
                "interpretation": interpretation,
            }
        )

    return pd.DataFrame(rows)


def _normal_cdf(z: float) -> float:
    """Standard normal CDF, avoided importing scipy for one line."""
    from math import erf, sqrt

    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


# --------------------------------------------------------------------------
# 4. Balance table.
# --------------------------------------------------------------------------
BALANCE_VARIABLES = {
    "fte1": "FTE employment, wave 1",
    "EMPFT": "Full-time workers, wave 1",
    "EMPPT": "Part-time workers, wave 1",
    "NMGRS": "Managers, wave 1",
    "WAGE_ST": "Starting wage, wave 1",
    "HRSOPEN": "Hours open per day, wave 1",
    "PSODA": "Price of a medium soda, wave 1",
    "PFRY": "Price of small fries, wave 1",
    "PENTREE": "Price of an entree, wave 1",
    "CO_OWNED": "Company-owned store",
}


def balance_table(df: pd.DataFrame) -> pd.DataFrame:
    """Wave-1 characteristics by state, with a difference and a t test."""
    s = df[df.sample_table4]
    nj = s[s.STATE == 1]
    pa = s[s.STATE == 0]
    rows = []
    for var, label in BALANCE_VARIABLES.items():
        a, b = nj[var].dropna(), pa[var].dropna()
        diff = a.mean() - b.mean()
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        rows.append(
            {
                "variable": label,
                "nj_mean": a.mean(),
                "pa_mean": b.mean(),
                "difference": diff,
                "std_error": se,
                "t_statistic": diff / se if se > 0 else np.nan,
                "p_value": 2 * (1 - _normal_cdf(abs(diff / se))) if se > 0 else np.nan,
                "n_nj": len(a),
                "n_pa": len(b),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5. Standard-error sensitivity.
# --------------------------------------------------------------------------
def se_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """The New Jersey dummy estimated with alternative variance estimators."""
    s = df[df.sample_table4].copy()
    y = s.fte_change
    X = sm.add_constant(s[["nj"]].astype(float))
    base = sm.OLS(y, X).fit()

    specs = [
        ("Conventional (as in the paper)", {}),
        ("HC1 heteroskedasticity-robust", {"cov_type": "HC1"}),
        ("HC3 heteroskedasticity-robust", {"cov_type": "HC3"}),
        ("Clustered by chain (4 clusters)", {"cov_type": "cluster", "groups": s.CHAIN}),
        ("Clustered by region (5 clusters)", {"cov_type": "cluster", "groups": s.region}),
    ]

    rows = []
    for label, kwargs in specs:
        res = base.get_robustcov_results(**kwargs) if kwargs else base
        coef = res.params[1] if not isinstance(res.params, pd.Series) else res.params["nj"]
        se = res.bse[1] if not isinstance(res.bse, pd.Series) else res.bse["nj"]
        p = res.pvalues[1] if not isinstance(res.pvalues, pd.Series) else res.pvalues["nj"]
        rows.append(
            {
                "variance_estimator": label,
                "coefficient": float(coef),
                "std_error": float(se),
                "t_statistic": float(coef / se),
                "p_value": float(p),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 6. Sensitivity bounds.
# --------------------------------------------------------------------------
def sensitivity_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """How large would a bias have to be to overturn the conclusion?

    The paper's conclusion is that employment did not fall.  To reverse it, the
    difference-in-differences would have to be biased downwards by roughly the
    size of the estimate itself.  We express that required bias in three
    interpretable units.
    """
    s = df[df.sample_table4]
    # Use the regression estimate and its conventional standard error, so the
    # numbers line up with column (i) of the replication table.
    fitted = sm.OLS(s.fte_change, sm.add_constant(s[["nj"]].astype(float))).fit()
    estimate_value = float(fitted.params["nj"])
    se = float(fitted.bse["nj"])
    sd_outcome = s.fte_change.std(ddof=1)
    mean_baseline = s.fte1.mean()

    rows = [
        {
            "quantity": "Difference-in-differences estimate (FTE jobs)",
            "value": estimate_value,
            "note": "Positive means relative employment rose in New Jersey.",
        },
        {
            "quantity": "Standard error of the estimate",
            "value": se,
            "note": "Conventional (homoskedastic) regression standard error.",
        },
        {
            "quantity": "Bias needed to overturn the sign (FTE jobs)",
            "value": abs(estimate_value),
            "note": "An omitted confound would have to shift the estimate by this much.",
        },
        {
            "quantity": "That bias in standard deviations of the outcome",
            "value": abs(estimate_value) / sd_outcome,
            "note": f"Outcome standard deviation is {sd_outcome:.3f} FTE jobs.",
        },
        {
            "quantity": "That bias as a share of wave-1 employment",
            "value": abs(estimate_value) / mean_baseline,
            "note": f"Mean wave-1 employment is {mean_baseline:.3f} FTE jobs.",
        },
        {
            "quantity": "That bias in standard errors",
            "value": abs(estimate_value) / se,
            "note": "How many standard errors the confound would have to move the estimate.",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df = add_alternative_outcomes(pd.read_csv(DATA_PROCESSED / "analysis_sample.csv"))

    curve = specification_curve(df)
    curve.to_csv(TABLES / "specification_curve.csv", index=False)

    ri, ri_null = randomization_inference(df)
    ri.to_csv(TABLES / "randomization_inference.csv", index=False)
    ri_null.to_csv(TABLES / "randomization_null.csv", index=False)

    placebo = placebo_tests(df)
    placebo.to_csv(TABLES / "placebo_tests.csv", index=False)

    balance = balance_table(df)
    balance.to_csv(TABLES / "balance_table.csv", index=False)

    se_tab = se_sensitivity(df)
    se_tab.to_csv(TABLES / "se_sensitivity.csv", index=False)

    bounds = sensitivity_bounds(df)
    bounds.to_csv(TABLES / "sensitivity_bounds.csv", index=False)

    print(f"Specification curve: {len(curve)} specifications")
    print(f"  minimum estimate : {curve.estimate.min():.2f}")
    print(f"  median  estimate : {curve.estimate.median():.2f}")
    print(f"  maximum estimate : {curve.estimate.max():.2f}")
    print(f"  share positive   : {(curve.estimate > 0).mean():.1%}")
    print(f"  share significant at 5%: {(curve.p_value < 0.05).mean():.1%}")
    print()
    print("Randomisation inference:")
    print(ri.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()
    print("Placebo tests:")
    print(placebo.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print()
    print("Balance table (New Jersey minus Pennsylvania, wave 1):")
    print(balance.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print()
    print("Standard-error sensitivity:")
    print(se_tab.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print()
    print("Sensitivity bounds:")
    print(bounds.to_string(index=False, float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    main()
