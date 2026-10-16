"""Build the processed analysis sample from the raw survey file.

Input :  data/raw/public.csv
Output:  data/processed/analysis_sample.csv
         data/processed/descriptives.csv

Every derived variable used anywhere else in the project is created here, so
the downstream scripts only ever read the processed file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    CHAIN_LABELS,
    CLOSED_AS_MISSING,
    CLOSED_AS_ZERO,
    DATA_PROCESSED,
    NEW_MIN_WAGE,
    OLD_MIN_WAGE,
    PT_WEIGHT_BASELINE,
    RAW_FILE,
)


def full_time_equivalent(
    empft: pd.Series,
    emppt: pd.Series,
    nmgrs: pd.Series,
    pt_weight: float = PT_WEIGHT_BASELINE,
) -> pd.Series:
    """Full-time-equivalent employment.

    FTE = full-time workers + pt_weight * part-time workers + managers.
    Card and Krueger set pt_weight = 0.5.  A store is treated as missing only
    when the parts are unavailable, which is what pandas' arithmetic already
    does for NaN inputs.
    """
    return empft + pt_weight * emppt + nmgrs


def employment_outcomes(df: pd.DataFrame, pt_weight: float = PT_WEIGHT_BASELINE) -> pd.DataFrame:
    """Add fte1, fte2 and fte_change columns for a given part-time weight.

    Kept as a separate function so the robustness module can rebuild the
    employment measure with alternative weights without touching the raw file.
    """
    df = df.copy()
    df["fte1"] = full_time_equivalent(df.EMPFT, df.EMPPT, df.NMGRS, pt_weight)
    df["fte2"] = full_time_equivalent(df.EMPFT2, df.EMPPT2, df.NMGRS2, pt_weight)

    # Second-wave closures.  Permanently closed stores keep an employment of
    # zero (their workers are gone); temporarily closed stores are treated as
    # missing because their employment is unobserved rather than zero.
    df.loc[df.STATUS2.isin(CLOSED_AS_ZERO), "fte2"] = 0.0
    df.loc[df.STATUS2.isin(CLOSED_AS_MISSING), "fte2"] = np.nan

    df["fte_change"] = df.fte2 - df.fte1
    return df


def build_sample(pt_weight: float = PT_WEIGHT_BASELINE) -> pd.DataFrame:
    """Load the raw file and add every derived variable used in the analysis."""
    df = pd.read_csv(RAW_FILE)

    # ---- Employment -------------------------------------------------------
    df = employment_outcomes(df, pt_weight)

    df["fte_growth"] = df.fte_change / df.fte1.replace(0.0, np.nan)

    # ---- Treatment and the initial wage gap -------------------------------
    df["nj"] = (df.STATE == 1).astype(int)

    # GAP = proportional wage increase a store needs to reach the new minimum.
    # Stores already paying at or above 5.05 (and every Pennsylvania store)
    # have a gap of zero and are untreated in the within-NJ design.
    needed = (NEW_MIN_WAGE - df.WAGE_ST) / df.WAGE_ST
    df["gap"] = np.where((df.STATE == 1) & (df.WAGE_ST < NEW_MIN_WAGE), np.maximum(needed, 0.0), 0.0)
    df.loc[df.WAGE_ST.isna(), "gap"] = np.nan

    # ---- Wage outcomes ----------------------------------------------------
    df["wage_change"] = df.WAGE_ST2 - df.WAGE_ST
    df["wage_growth"] = df.wage_change / df.WAGE_ST.replace(0.0, np.nan)
    # Did the store have to raise its starting wage to comply with the law?
    df["bound_before"] = ((df.STATE == 1) & (df.WAGE_ST < NEW_MIN_WAGE)).astype(int)
    df["at_new_min_after"] = (df.WAGE_ST2 >= NEW_MIN_WAGE - 1e-9).astype(int)

    # ---- Prices -----------------------------------------------------------
    for good in ["SODA", "FRY", "ENTREE"]:
        df[f"p_{good.lower()}_growth"] = df[f"P{good}2"] / df[f"P{good}"] - 1.0

    # ---- Labels and controls ---------------------------------------------
    df["chain_label"] = df.CHAIN.map(CHAIN_LABELS)
    df["company_owned"] = (df.CO_OWNED == 1).astype(int)
    df["region"] = np.select(
        [
            df.NORTHJ == 1,
            df.CENTRALJ == 1,
            df.SOUTHJ == 1,
            df.PA1 == 1,
            df.PA2 == 1,
        ],
        ["NJ-North", "NJ-Central", "NJ-South", "PA-Philadelphia", "PA-Easton"],
        default="Other",
    )
    df["state_label"] = np.where(df.STATE == 1, "New Jersey", "Pennsylvania")

    # ---- Sample flags -----------------------------------------------------
    # Balanced employment sample: FTE observed in both waves.
    df["sample_balanced"] = df.fte1.notna() & df.fte2.notna()

    # Regression sample of the paper's Table 4: wave-1 employment and starting
    # wage, plus wave-2 employment and starting wage, where permanently closed
    # stores are retained (with zero employment) even though their wave-2
    # starting wage is unobserved.  This reproduces the paper's N = 357.
    has_core = df.fte1.notna() & df.WAGE_ST.notna() & df.fte2.notna()
    df["sample_table4"] = has_core & (
        df.WAGE_ST2.notna() | df.STATUS2.isin(CLOSED_AS_ZERO)
    )

    return df


def describe(df: pd.DataFrame) -> pd.DataFrame:
    """Small descriptive table written to data/processed/descriptives.csv."""
    rows = []
    for label, mask in [
        ("All wave-1 stores", df.SHEET.notna()),
        ("Answered in wave 2", df.STATUS2 == 1),
        ("Balanced employment sample", df.sample_balanced),
        ("Table 4 regression sample", df.sample_table4),
    ]:
        sub = df[mask]
        rows.append(
            {
                "sample": label,
                "n_stores": len(sub),
                "n_new_jersey": int((sub.STATE == 1).sum()),
                "n_pennsylvania": int((sub.STATE == 0).sum()),
                "mean_fte_wave1": sub.fte1.mean(),
                "mean_fte_wave2": sub.fte2.mean(),
                "mean_starting_wage_wave1": sub.WAGE_ST.mean(),
                "mean_starting_wage_wave2": sub.WAGE_ST2.mean(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    df = build_sample()
    df.to_csv(DATA_PROCESSED / "analysis_sample.csv", index=False)

    desc = describe(df)
    desc.to_csv(DATA_PROCESSED / "descriptives.csv", index=False)

    print(f"analysis_sample.csv : {len(df)} stores, {df.shape[1]} columns")
    print(f"  balanced sample   : {int(df.sample_balanced.sum())}")
    print(f"  Table 4 sample    : {int(df.sample_table4.sum())}  (paper reports 357)")
    print(desc.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
