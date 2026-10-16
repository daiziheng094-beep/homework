# Replicating and extending Card and Krueger (1994): the New Jersey minimum wage and fast-food employment

This project replicates the core results of Card and Krueger's paper "Minimum Wages and
Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania", published
in the *American Economic Review* (1994), and adds an independent robustness extension.

The paper asks whether employment in fast-food restaurants fell after New Jersey raised its
minimum wage from $4.25 to $5.05 an hour on 1 April 1992. The authors compare New Jersey with
neighbouring Pennsylvania, where the minimum wage stayed at $4.25 (a difference-in-differences),
and also compare higher- and lower-wage stores within New Jersey. Their conclusion is that there
is no evidence that the increase reduced employment.

This repository rebuilds that conclusion from the paper's original survey data, `public.csv`,
and then tests how robust it is.

> A Chinese version of this README is in [`README.md`](README.md). The full empirical report
> also exists in both languages: [`report/empirical_report.md`](report/empirical_report.md)
> (Chinese) and [`report/empirical_report_en.md`](report/empirical_report_en.md) (English).

---

## 1. Quick start

```bash
# 1. Install dependencies (Python 3.10 or later)
pip install -r requirements.txt

# 2. Obtain the raw data (this repository does not contain it — see Section 5)
#    Download 01_DID.zip from the course platform, unzip it, and place
#    public.csv at: data/raw/public.csv

# 3. Generate every table and figure with one command
#    python3 on macOS/Linux; on Windows it is usually just python
python3 run_all.py
```

When it finishes, all outputs are written to `results/tables/` (tables) and `results/figures/`
(figures), with intermediate data in `data/processed/`. The whole run takes about 5 seconds and
requires no manual edits to any file.

Both language versions are produced in the same run: the figures come out as
`figN_....png` (Chinese) and `figN_..._en.png` (English), and the Table 3 and Table 4 markdown
renderings as `.md` (Chinese) and `_en.md` (English).

> **Reproducibility contract:** as long as the raw data file `public.csv` is in `data/raw/`,
> `run_all.py` rebuilds every table and figure in the report from scratch. Every random process
> (the randomisation test) has a fixed seed (`SEED` in `src/config.py`), so results reproduce
> digit for digit.
>
> If the input file is missing, `run_all.py` fails with a clear error and exits; it will not
> silently produce empty results.

---

## 2. Directory structure

```
.
├── README.md / README_en.md       How to reproduce the results (Chinese / English)
├── AI_USE_DISCLOSURE.md / _en.md  AI use disclosure (Chinese / English)
├── run_all.py                     One-command entry point (the only script you need to run)
├── requirements.txt               Python dependencies
│
├── data/
│   ├── raw/
│   │   ├── public.csv             ← Raw survey data (410 stores × 46 columns).
│   │   │                            NOT in this repository; you must supply it — see Section 5
│   │   └── README.md              Data provenance, how to obtain it, usage restrictions
│   └── processed/
│       ├── analysis_sample.csv    ← Processed data: all analysis variables, 410 rows
│       │                            (store-level). NOT in this repository; regenerated
│       │                            by step 1 — see Section 5
│       └── descriptives.csv       Descriptive statistics by sample definition (shipped)
│
├── src/                           Analysis code
│   ├── config.py                  Paths, policy parameters, sample definitions, random seed
│   ├── prepare_data.py            Build the analysis sample and derived variables
│   ├── replication.py             Reproduce the paper's Tables 3 and 4
│   ├── robustness.py              Independent extension: robustness and sensitivity checks
│   └── figures.py                 Generate every figure
│
├── results/
│   ├── tables/                    Every table (.csv, plus .md renderings in both languages)
│   └── figures/                   Every figure (.png, in both languages)
│
├── report/
│   ├── empirical_report.md        Empirical report (Chinese)
│   └── empirical_report_en.md     Empirical report (English)
│
├── docs/
│   └── njmin-aer.pdf              The paper being replicated
│
└── .claude/skills/
    ├── replicate-card-krueger-did/      Reusable skill, Chinese
    └── replicate-card-krueger-did-en/   Reusable skill, English
```

---

## 3. The analysis pipeline

`run_all.py` runs four modules in sequence; each can also be run on its own:

| Step | Script | Input | Output |
| --- | --- | --- | --- |
| 1 | `src/prepare_data.py` | `data/raw/public.csv` | `data/processed/analysis_sample.csv`, `descriptives.csv` |
| 2 | `src/replication.py` | the sample from step 1 | `table3_employment`, `table4_regressions`, `wage_distribution`, `replication_check` |
| 3 | `src/robustness.py` | the sample from step 1 | `specification_curve`, `randomization_inference`, `randomization_null`, `placebo_tests`, `balance_table`, `se_sensitivity`, `sensitivity_bounds` |
| 4 | `src/figures.py` | all of the above | `fig1`–`fig5`, in both languages |

To rerun a single module (for example, to redo only the figures):

```bash
python3 src/figures.py
```

---

## 4. Core results at a glance

**The replication reproduces the paper.** Of the five columns in Table 4, the first four match
the coefficients and standard errors reported in the original paper digit for digit to two
decimal places (2.33, 2.30, 15.65, 14.92). The fifth column (with region controls) gives
11.98 (7.42) here against the paper's 11.91 (7.39); the discrepancy is discussed in
`results/tables/replication_check.csv`. The sample size (357 stores) matches the paper's notes
exactly.

| Quantity | This replication | Original paper |
| --- | --- | --- |
| Table 4 (i) NJ dummy | 2.33 (1.19) | 2.33 (1.19) |
| Table 4 (iii) initial wage gap | 15.65 (6.08) | 15.65 (6.08) |
| Table 4 regression sample size | 357 | 357 |
| Table 3 difference-in-differences (paper's text) | 2.75 (1.34) | 2.76 (1.36) |
| Employment level, NJ before / after | 20.44 (0.51) / 21.03 (0.52) | 20.4 (0.51) / 21.0 (0.52) |
| NJ wage groups in the notes to Table 3 | 101 / 140 / 73 | 101 / 140 / 73 |

**The independent extension concludes:** of 180 equally defensible specifications, 98.9% give a
positive employment effect; randomisation inference gives p = 0.055 (New Jersey dummy) and
p = 0.011 (wage gap); and New Jersey stores already paying at or above the new floor before the
rise — stores the law does not bind — show a relative employment change of −0.03 (p = 0.986).
The estimate is robust, but describing it as significantly positive requires more caution than
the paper's own framing.

Full discussion in [`report/empirical_report_en.md`](report/empirical_report_en.md).

---

## 5. Data and usage restrictions

- The raw data `public.csv` are store-level survey data covering 410 stores and 46 columns,
  distributed for this course as part of `01_DID.zip`. Field definitions are in
  `data/raw/README.md`.
- These data may be used only for this course project, within the terms of the course data
  agreement, and **must not be publicly redistributed**. **This public repository therefore
  does not contain `data/raw/public.csv`** (it is excluded by `.gitignore`). Before
  reproducing the results, place that file in `data/raw/` as described in step 2 of Section 1;
  `data/raw/README.md` explains how to obtain it.
- The paper itself, `docs/njmin-aer.pdf`, is likewise copyrighted and is not distributed with
  the repository; obtain it from the citation above.
- **`data/processed/analysis_sample.csv` is not distributed either.** It is the 410-row
  store-level analysis sample, readable store by store and retaining every column of the raw
  file, so publishing it would amount to publishing the raw data. `src/prepare_data.py`
  rebuilds it automatically when the pipeline runs, so it does not need to ship.
- **What the repository does contain is safe to publish:** all the code (`src/`), the field
  documentation in `data/raw/README.md`, `data/processed/descriptives.csv`, and every table and
  figure under `results/`. These hold summary results only, with no store-level records.

---

## 6. Environment

- Python 3.10+
- Dependencies are in `requirements.txt`: `pandas`, `numpy`, `scipy`, `statsmodels`,
  `matplotlib`. The Chinese figures use a system CJK font (PingFang SC / Hiragino Sans GB); on
  a non-macOS machine, add an available CJK font to the font list in `src/figures.py`. The
  English figures need no CJK font.

Verified on Python 3.14, pandas 3.0.5, numpy 2.5.3, statsmodels 0.15.0, matplotlib 3.11.2.
