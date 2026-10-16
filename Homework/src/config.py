"""Project-wide constants and paths.

All scripts read their settings from here so that the pipeline can be rerun
without editing any analysis code.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths.  ROOT is the repository root (the folder that contains this /src).
# The workflow only ever reads from DATA_RAW: drop the input CSV there and run
# `python3 run_all.py`.
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"

RAW_FILE = DATA_RAW / "public.csv"

# --------------------------------------------------------------------------
# Policy parameters of the New Jersey minimum-wage increase.
# On 1 April 1992 the NJ minimum wage rose from 4.25 to 5.05 USD per hour.
# Pennsylvania's minimum wage stayed at 4.25 USD throughout the sample period.
# --------------------------------------------------------------------------
OLD_MIN_WAGE = 4.25
NEW_MIN_WAGE = 5.05

# Hours per week that one full-time worker supplies.  Used only in the
# descriptive section, not in the replication.
FULL_TIME_HOURS = 40.0

# --------------------------------------------------------------------------
# Sample definitions (see the report for the exact wording of each rule).
# --------------------------------------------------------------------------
# STATUS2 codes in the second wave.
STATUS_REFUSED = 0
STATUS_ANSWERED = 1
STATUS_RENOVATION = 2  # temporarily closed
STATUS_PERMANENT_CLOSURE = 3  # permanently closed -> employment set to 0
STATUS_HIGHWAY = 4  # temporarily closed
STATUS_MALL_FIRE = 5  # temporarily closed

# Second-wave closures that the original paper treats as zero employment.
CLOSED_AS_ZERO = [STATUS_PERMANENT_CLOSURE]
# Second-wave closures whose employment is treated as missing.
CLOSED_AS_MISSING = [STATUS_RENOVATION, STATUS_HIGHWAY, STATUS_MALL_FIRE]

# Reported value of the baseline part-time weight.  Card and Krueger count each
# part-time worker as half a full-time worker.
PT_WEIGHT_BASELINE = 0.5

# Baseline NJ region / PA region labels used for the region controls.
NJ_REGIONS = ["NORTHJ", "CENTRALJ", "SOUTHJ"]
PA_REGIONS = ["PA1", "PA2"]

CHAIN_LABELS = {1: "Burger King", 2: "KFC", 3: "Roy Rogers", 4: "Wendy's"}

# Seed for every random draw (randomisation inference, bootstrap) so that the
# reported numbers are exactly reproducible.
SEED = 20260401
N_PERMUTATIONS = 10_000


def ensure_dirs() -> None:
    """Create every output directory if it does not already exist."""
    for path in (DATA_RAW, DATA_PROCESSED, TABLES, FIGURES):
        path.mkdir(parents=True, exist_ok=True)
