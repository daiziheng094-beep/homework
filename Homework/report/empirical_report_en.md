# Minimum Wages and Fast-Food Employment in New Jersey
## A replication of Card and Krueger (1994), with a robustness extension

**Course:** ECON6067B · **Name:** Dai Ziheng · **Student number:** 3036760436

---

## Abstract

This report replicates the core empirical results of Card and Krueger (1994, *AER*) on the
1992 minimum-wage increase in New Jersey, and adds an independent robustness extension.

In the replication I rebuild the analysis sample from the paper's own survey data (410
stores; 357 in the regression sample) and re-estimate the paper's Tables 3 and 4. The result
is a near-exact reproduction: the coefficients and standard errors in the first four columns
of Table 4 match the original to two decimal places, digit for digit (2.33, 2.30, 15.65,
14.92), and the regression sample size, the first two moments of the dependent variable, the
four employment levels with their standard errors, and the New Jersey wage-group store counts
reported in the notes to Table 3 (101 / 140 / 73) all line up. The paper's running text
reports the difference-in-differences as 2.76 (t = 2.03); my replication gives 2.75 (t = 2.05).
The one larger discrepancy is column (v) of Table 4, where I obtain 11.98 (7.42) against the
paper's 11.91 (7.39), a difference of 0.069; I discuss its likely source in Section 4.4.

In the extension I ask how fragile the "no employment loss" finding is. Of 180 equally
defensible specifications, 98.9% yield a positive employment effect; randomisation inference
gives p = 0.055 (cross-state comparison) and p = 0.011 (within-state wage gap); and New Jersey
stores already paying at or above the new floor before the rise show a relative employment
change of −0.03 (p = 0.986). The conclusion is that **the sign and magnitude of the estimate
are highly robust to specification choice, but whether it clears the conventional threshold
of statistical significance is not.** A point estimate of 2.33 full-time-equivalent jobs is
only 1.95 standard errors from zero, so describing it as "significantly positive" goes beyond
what the data support; the paper's more cautious wording — "no evidence of a decline in
employment" — is the appropriate one.

---

## 1. The paper's research question and motivation

### 1.1 Basic details

- **Authors:** David Card, Alan B. Krueger
- **Title:** *Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New
  Jersey and Pennsylvania*
- **Journal:** *American Economic Review*, Vol. 84, No. 4 (September 1994), pp. 772–793

### 1.2 The research question

The competitive labour-market model in economics textbooks makes a clear prediction: a
statutory minimum wage set above the market-clearing wage reduces employment among low-skilled
workers. The prediction is almost self-evident as a matter of theory, but it has always been
hard to test cleanly, because minimum wages are usually raised nationally and no comparable
unaffected control group is available.

On 1 April 1992 the state of New Jersey raised its minimum wage in one step from $4.25 to
$5.05 an hour (an increase of 18.8%), while neighbouring Pennsylvania left its minimum wage
at $4.25. What makes this episode special is that eastern Pennsylvania and New Jersey form a
single geographic and economic unit: stores in the two states draw on the same labour market
and belong to the same chains, and consumers move freely across the state line. That provides
a setting close to a natural experiment, and it is the paper's central methodological
motivation.

Card and Krueger ask: **did this minimum-wage increase reduce employment in the New Jersey
fast-food industry?**

### 1.3 The paper's two identification strategies

The paper does not rely on a single comparison. It designs two complementary contrasts:

1. **The cross-state comparison.** New Jersey stores are compared with eastern Pennsylvania
   stores. Because the two areas share a labour market, the employment change in Pennsylvania
   can serve as the counterfactual for New Jersey in the absence of the policy.
2. **The within-New-Jersey comparison.** Within New Jersey alone, stores whose starting wage
   before the rise was exactly the old minimum ($4.25, i.e. fully "bitten" by the policy) are
   compared with stores whose starting wage was already above the new floor ($5.00 or more,
   and therefore entirely unconstrained by the policy). The strength of this design is that
   both groups sit in the same state and face the same state-level shocks (the same recession,
   the same state labour law), so the difference in exposure is exogenous.

If the minimum wage really does reduce employment as the textbook predicts, the most
constrained stores (New Jersey's $4.25 stores) should show the largest relative decline, and
the entirely unconstrained stores ($5.00 and above) should show no relative change at all.

### 1.4 The paper's conclusion

The paper finds that employment in the New Jersey fast-food industry did **not** fall after
the increase, and indeed rose slightly relative to Pennsylvania. The within-state comparison
likewise shows that the lowest-wage New Jersey stores, if anything, added employment slightly
faster than the highest-wage stores. That conclusion runs against the competitive model's
prediction and has become one of the most cited empirical results in the minimum-wage
literature.

---

## 2. Data sources, sample construction and variable definitions

### 2.1 Data sources

The data are a store-level telephone survey collected by the authors themselves, distributed
for this course as `01_DID.zip`; this project uses the file `public.csv` within it (410 stores ×
46 columns). That file is subject to the course data-use terms and is not distributed with the
public repository: to reproduce the results you must place it at `data/raw/public.csv` as
described in `data/raw/README.md`. The survey was run in two waves:

| Wave | Period | Policy status |
| --- | --- | --- |
| Wave 1 | February–March 1992 | New Jersey minimum wage still $4.25 (before the rise) |
| Wave 2 | November–December 1992 | New Jersey minimum wage now $5.05 (about 8 months after) |

The survey covers every store of four chains — Burger King, KFC, Roy Rogers and Wendy's — in
the two states, spanning all three New Jersey regions (NORTHJ / CENTRALJ / SOUTHJ) and two
eastern Pennsylvania regions (PA1 Philadelphia / PA2 Easton). These stores are highly similar
in product, production technology and staffing structure, which is a key precondition for
using the data in a difference-in-differences design.

The fields fall into four groups:

- **Identifiers and groups:** `SHEET` (store number), `CHAIN` (brand), `CO_OWNED` (company-owned
  or franchised), `STATE` (state), plus the five mutually exclusive region dummies
  `NORTHJ`/`CENTRALJ`/`SOUTHJ`/`PA1`/`PA2` and `SHORE`. The `region` column used in the code is
  a **derived** column built from those five dummies (see `src/prepare_data.py`), not a raw
  field.
- **Wave-1 outcome variables:** `EMPFT` (full-time employees), `EMPPT` (part-time employees),
  `NMGRS` (managers), `WAGE_ST` (starting wage), `HRSOPEN` (hours open), and `PSODA` / `PFRY` /
  `PENTREE` (product prices)
- **Wave-2 outcome variables:** the same names with a `2` suffix (`EMPFT2`, `WAGE_ST2`, …)
- **Wave-2 store status:** `STATUS2`, coded 1 = open, 2 = under renovation, 3 = permanently
  closed, 4 = relocated / road construction, 5 = closed after a mall fire

### 2.2 Sample construction

Four steps, all carried out in `src/prepare_data.py`.

**Step 1: compute full-time-equivalent employment (FTE).** The paper's core outcome is
full-time-equivalent employment rather than a headcount, because fast food relies heavily on
part-time staff. Each part-time employee counts as 0.5 of a full-time position:

```
FTE = EMPFT + 0.5 × EMPPT + NMGRS
```

This is computed separately for each wave, giving `fte1` and `fte2`; their difference,
`fte_change`, is the dependent variable in the regressions.

**Step 2: handle wave-2 store closures.** This step alone determines whether the paper's
sample size can be reproduced, and it is the single most important one. The notes to Table 4
state that in the sample of 357 stores "employment at six stores that had closed permanently
was recorded as zero, and the four temporarily closed stores were dropped". Accordingly:

- `STATUS2 == 3` (permanently closed, 6 stores): wave-2 employment is recorded as **0**.
  Closure *is* employment going to zero; treating it as missing would understate a negative
  effect and amounts to selection on the outcome.
- `STATUS2 ∈ {2, 4, 5}` (renovation / relocation / fire, 4 stores): wave-2 employment is
  recorded as **missing**. These stores were not trading at the survey date, so their
  "employment" is not defined; coding it as 0 would mistake a temporary shutdown for genuine
  job destruction.

**Step 3: define three sample definitions**, corresponding to different tables in the paper:

| Sample | Definition | Stores | Used for |
| --- | --- | --- | --- |
| All available | `fte1` and `WAGE_ST` observed in wave 1 | 410 | Table 3, rows 1–3 (unbalanced) |
| `sample_balanced` | Employment observed in both waves | 384 | Table 3, row 4 |
| `sample_table4` | Wave 1 complete, and wave-2 employment observed **or** the store closed permanently | **357** | Table 3 row 5, Table 4, all robustness checks |

The 357 of `sample_table4` matches the sample size reported in the notes to Table 4 exactly.
That is the first independent piece of evidence that the replication is correct.

**Step 4: construct the treatment variables.**

- **New Jersey dummy `nj`:** equals 1 when `STATE == 1`. This is an "intention-to-treat"
  variable recording whether the store sits in the policy jurisdiction. Used in Table 4
  columns (i) and (ii).
- **Initial wage gap `gap`:**

  ```
  GAP = max(0, (5.05 − WAGE_ST) / WAGE_ST)    for New Jersey stores
  GAP = 0                                      for Pennsylvania stores
  ```

  `gap` measures how far a store's starting wage falls below the new floor, i.e. how hard the
  policy bites on that store. A New Jersey store starting at exactly $4.25 has
  `gap = (5.05 − 4.25)/4.25 = 0.188`; a store already at or above $5.05 has `gap = 0`. Used in
  Table 4 columns (iii)–(v). Compared with `nj`, `gap` exploits variation across stores in the
  intensity of the policy, which in principle gives it more power; it is also the class of
  specification that performs best in the robustness extension below.

**Control variables:** brand dummies (three, with Burger King as the reference), a
company-owned dummy (`company_owned`), and region dummies (column (v)).

---

## 3. Empirical design

### 3.1 Identification strategy

The core estimator is a difference-in-differences:

```
ŷ = (ȳ_NJ,after − ȳ_NJ,before) − (ȳ_PA,after − ȳ_PA,before)
```

The key assumption identifying the policy effect is **parallel trends**: absent the
minimum-wage increase, employment in New Jersey stores would have changed in the same way as
in Pennsylvania stores. Because stores in the two states share a labour market, belong to the
same chains, and the policy change occurred during a regional recession that hit both states,
this assumption is more credible here than in the typical difference-in-differences setting.
The paper also uses a within-state "low-wage vs high-wage stores" contrast as a second leg:
that contrast does not rely on cross-state comparability, but it does rely on the two groups
of stores having the same employment trend in the absence of the policy.

### 3.2 Regression specification

Table 4 of the paper writes the idea as a regression:

```
ΔFTE_i = α + β · Treat_i + γ′ X_i + ε_i
```

where `ΔFTE_i = FTE_{i,2} − FTE_{i,1}`, `Treat` is either `nj` or `gap`, and `X` contains the
brand dummies, the company-owned dummy and region dummies. The five models differ in their
treatment and control variables:

| Column | Treatment | Controls | As reported in the paper |
| --- | --- | --- | --- |
| (i) | `nj` | none | 2.33 (1.19) |
| (ii) | `nj` | brand + ownership | 2.30 (1.20) |
| (iii) | `gap` | none | 15.65 (6.08) |
| (iv) | `gap` | brand + ownership | 14.92 (6.21) |
| (v) | `gap` | brand + ownership + region | 11.91 (7.39) |

### 3.3 Estimation method

- **Estimator:** ordinary least squares (OLS).
- **Standard errors:** conventional (homoskedastic) standard errors, matching the original
  paper. The paper states that its reported standard errors are not adjusted for
  heteroskedasticity; to compare like with like, the replication uses the same convention.
  Heteroskedasticity-robust, clustered and design-based randomisation standard errors are
  reported in Section 5 as robustness checks — which is itself an important addition to the
  paper's conclusion, since the paper's standard-error convention is on the narrow side.
- **Handling of region dummies:** in column (v), including the New Jersey dummy together with
  all region dummies makes the design matrix rank-deficient — the three New Jersey region
  dummies sum identically to the treatment variable `nj`, and the two Pennsylvania region
  dummies sum identically to `1 − nj`. Column (v) therefore includes only **one** Pennsylvania
  region dummy (the other serving as the reference category). This also explains why that
  column's estimate differs slightly from the original paper (see Section 4.4).

### 3.4 A transparency issue that has to be stated

The numeric cells of the paper's **Table 3** are **images rather than text** in the supplied
PDF (verified by text search: values such as `23.33`, `20.44` and `2.75` cannot be found in
the PDF's text layer). Table 3 itself therefore cannot be compared cell by cell
automatically.

There are, however, two alternative sources that *can* be checked directly:

1. **Table 2 of the paper** (`Means of Selected Variables`) reports its employment row as text
   rather than an image; it covers the same stores before and after the rise and is directly
   comparable with rows 1 and 2 of my Table 3;
2. the paper's running text states the difference-in-differences point estimate and t statistic
   in words.

The set of quantities that can be compared automatically is therefore: the five Table 4
coefficients and standard errors, the Table 4 sample size of 357, the dependent variable's
mean of −0.237 and standard deviation of 8.825, **the four employment levels with their
standard errors**, the difference-in-differences of 2.76 (t = 2.03) reported in the text, and
the wage-group store counts of 101/140/73 from the notes to Table 3. All of these are recorded
in `results/tables/replication_check.csv`.

The remaining cells of Table 3 (the component means for each wage group, and so on) are my own
recomputation from the paper's definitions, reported in
`results/tables/table3_employment.csv` for manual inspection. **I do not claim that every cell
of Table 3 matches the original digit for digit**, because the component cells of Table 3
cannot be read automatically.

---

## 4. Core replication results and comparison with the original paper

### 4.1 The wage distribution: did the policy actually bite?

The replication is only informative if the policy really did move store wages. Table 1 reports
the distribution of starting wages.

**Table 1 — Distribution of starting wages (`results/tables/wage_distribution.csv`)**

| State | Wave | N | Mean | Median | Share at the old floor | Share below the new floor | Share at or above the new floor |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pennsylvania | Wave 1 | 76 | 4.63 | 4.50 | 34.2% | 94.7% | 5.3% |
| Pennsylvania | Wave 2 | 71 | 4.62 | 4.50 | 28.2% | 95.8% | 4.2% |
| New Jersey | Wave 1 | 314 | 4.61 | 4.50 | 32.2% | 91.1% | 8.9% |
| New Jersey | Wave 2 | 318 | **5.08** | **5.05** | 0.0% | **0.3%** | **99.7%** |

Three facts stand out:

1. **Before the rise the two states were nearly identical.** Mean wave-1 starting wages were
   $4.61 in New Jersey and $4.63 in Pennsylvania, with a median of $4.50 in both. This
   supports the premise that stores in the two states are comparable.
2. **After the rise New Jersey moved sharply and Pennsylvania did not move at all.** New
   Jersey's mean starting wage rose from $4.61 to $5.08 and its median from $4.50 to $5.05
   (exactly the new statutory floor), while Pennsylvania stayed at $4.62.
3. **The policy bit almost completely.** In wave 2, 99.7% of New Jersey stores paid at or above
   $5.05, with only 0.3% below. Before the rise, 91.1% of New Jersey stores paid below $5.05.

This matters: the "dose" of the policy was large and its coverage broad, so **if a minimum-wage
increase reduces employment, this dataset should be able to detect it.** That gives the null
result real content, rather than leaving it open to the objection that the policy was too weak
to show up. See Figure 2.

### 4.2 Table 3: employment levels and changes

**Table 2 — Full-time-equivalent employment (`results/tables/table3_employment.csv`)**

| Variable | Pennsylvania | New Jersey | Difference NJ−PA |
| --- | --- | --- | --- |
| 1. Employment before, all available observations | 23.33 (1.35) | 20.44 (0.51) | −2.89 (1.44) |
| 2. Employment after, all available observations | 21.17 (0.94) | 21.03 (0.52) | −0.14 (1.08) |
| 3. Change in employment (unbalanced sample) | −2.17 (1.65) | 0.59 (0.73) | **2.75 (1.80)** |
| 4. Change in employment (balanced sample, 384 stores) | −2.28 (1.25) | 0.47 (0.48) | **2.75 (1.34)** |
| 5. Change in employment (temporarily closed stores set to 0) | −2.28 (1.25) | 0.23 (0.49) | 2.51 (1.35) |

The four level values in rows 1 and 2 are **identical to the paper's Table 2 employment row at
the precision the paper itself reports**, and the three standard errors that are legible match
one for one: the paper gives New Jersey 20.4 (0.51) → 21.0 (0.52) and Pennsylvania 21.2 (0.94);
my replication gives 20.44 (0.51) → 21.03 (0.52) and 21.17 (0.94). This row appears both in the
paper's Table 2 (text layer, machine readable) and in rows 1 and 2 of Table 3 (image layer), so
it is the most direct check available on Table 3.

The difference-in-differences in row 4 is 2.75 in my replication (t = 2.05) against 2.76
(t = 2.03) in the paper's running text, a difference of 0.01. The paper gives no unrounded
value for this number and the corresponding Table 3 cell is an image, so the 0.01 cannot be
traced further; it is negligible in magnitude.

How to read the table: **Pennsylvania employment fell by 2.28 FTE jobs, New Jersey employment
rose by 0.47, and the difference is +2.75.** After the minimum-wage increase, New Jersey's
employment relative to Pennsylvania did not fall but rose slightly. Row 5, which sets the four
temporarily closed stores to zero employment (a more conservative treatment of closures),
lowers the estimate to 2.51 without changing its sign.

Figure 1 plots this difference-in-differences.

### 4.3 Table 4: regression results

**Table 3 — Reduced-form regressions (`results/tables/table4_regressions.csv`)**

| Model | Treatment | Coefficient | Std. error | t | p | N | R² |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (i) NJ dummy | `nj` | **2.326** | 1.192 | 1.952 | 0.052 | 357 | 0.011 |
| (ii) NJ dummy + controls | `nj` | **2.304** | 1.196 | 1.927 | 0.055 | 357 | 0.023 |
| (iii) Initial wage gap | `gap` | **15.653** | 6.080 | 2.574 | 0.010 | 357 | 0.018 |
| (iv) Wage gap + controls | `gap` | **14.916** | 6.205 | 2.404 | 0.017 | 357 | 0.029 |
| (v) Wage gap + controls + region | `gap` | **11.979** | 7.419 | 1.615 | 0.107 | 357 | 0.041 |

Reading the coefficients: the 2.33 in column (i) means New Jersey stores changed employment by
2.33 FTE jobs more than Pennsylvania stores did. The 15.65 in column (iii) means that a 10
percentage-point higher initial wage gap (for instance, a starting wage of $4.25 against $4.63)
is associated with an employment change about 1.57 FTE jobs higher.

### 4.4 Item-by-item comparison with the original paper

**Table 4 — Replication check (`results/tables/replication_check.csv`)**

| Quantity compared | This replication | Original paper | Difference | Source |
| --- | --- | --- | --- | --- |
| Table 4 (i) NJ dummy | 2.3258 (1.1916) | 2.33 (1.19) | −0.004 | AER 1994, Table 4 |
| Table 4 (ii) + controls | 2.3039 (1.1955) | 2.30 (1.20) | +0.004 | AER 1994, Table 4 |
| Table 4 (iii) wage gap | 15.6529 (6.0802) | 15.65 (6.08) | +0.003 | AER 1994, Table 4 |
| Table 4 (iv) + controls | 14.9157 (6.2053) | 14.92 (6.21) | −0.004 | AER 1994, Table 4 |
| Table 4 (v) + controls + region | **11.9792 (7.4191)** | **11.91 (7.39)** | **+0.069** | AER 1994, Table 4 |
| Table 4 regression sample size | 357 | 357 | 0 | AER 1994, Table 4 notes |
| Table 3 difference-in-differences | 2.750 (1.342) | 2.76 (1.36) | −0.010 | AER 1994, p. 779 text |
| Employment level: NJ before | 20.44 (0.51) | 20.4 (0.51) | +0.04 | AER 1994, Table 2 |
| Employment level: NJ after | 21.03 (0.52) | 21.0 (0.52) | +0.03 | AER 1994, Table 2 |
| Employment level: PA before | 23.33 (1.35) | 23.3 | +0.03 | AER 1994, p. 776 text |
| Employment level: PA after | 21.17 (0.94) | 21.2 (0.94) | −0.03 | AER 1994, Table 2 |
| Mean of dependent variable | −0.2375 | −0.237 | −0.001 | AER 1994, Table 4 notes |
| Std. dev. of dependent variable | 8.8255 | 8.825 | +0.000 | AER 1994, Table 4 notes |
| NJ stores (wave-1 wage = $4.25) | 101 | 101 | 0 | AER 1994, Table 3 notes |
| NJ stores (wave-1 wage $4.26–4.99) | 140 | 140 | 0 | AER 1994, Table 3 notes |
| NJ stores (wave-1 wage ≥ $5.00) | 73 | 73 | 0 | AER 1994, Table 3 notes |

The "difference" column for the four employment levels is within ±0.04. That is not an error
but simply reflects that **the paper reports only one decimal place**: 20.4 / 21.0 / 23.3 / 21.2
correspond to my 20.44 / 21.03 / 23.33 / 21.17. The three legible standard errors (0.51, 0.52,
0.94) match one for one.

**Conclusion: the replication succeeds.** The first four columns of Table 4 reproduce digit for
digit to two decimal places; the regression sample size, the first two moments of the dependent
variable, the four employment levels with their standard errors, the difference-in-differences
reported in the text, and the three wage-group store counts in the notes to Table 3 all line
up. These are independent quantities: the sample size matching shows the closure rules were
recovered correctly, the group counts matching shows the wage variable and grouping thresholds
were recovered correctly, and the standard errors of the employment levels matching shows the
part-time conversion weight (0.5) and the sample definition were recovered correctly. Matching
on all of them at once indicates that the sample construction is right, rather than tuned into
place.

**On the 0.069 discrepancy in column (v) of Table 4.** This is the only inconsistency. I ruled
out three explanations: the sample definition (switching to the 384-store balanced sample makes
the discrepancy larger), the outcome definition (using other part-time weights makes it larger),
and the set of controls (the brand and ownership variables move the estimate only slightly and
in opposite directions). The most likely remaining explanation is the **reference-category
parameterisation of the region dummies**: the three New Jersey region dummies sum identically
to the treatment variable `nj`, and the two Pennsylvania dummies sum identically to `1 − nj`, so
region controls can only enter as "one Pennsylvania region as the reference plus one
Pennsylvania region dummy", and the paper does not say which parameterisation it used.
Different reference choices change that column's estimate. **I did not keep adjusting the
specification until the numbers matched** — that would amount to reverse-engineering the
specification from the answer, which destroys the value of the replication as evidence. The
0.069 discrepancy is about 0.9% of the 7.42 standard error and does not affect any substantive
conclusion.

---

## 5. Independent extension: how robust is the conclusion?

Replication only answers "can I reproduce the paper's numbers". The genuinely interesting
question is: **how fragile is this null result?** Would a different but equally defensible
specification overturn it? I ran five sets of checks; all the code is in `src/robustness.py`.

### 5.1 The specification curve: 180 equally reasonable specifications

I built a grid of 2 × 5 × 2 × 3 × 3 = 180 specifications, where every dimension is a choice a
researcher genuinely faces and every option has precedent in the literature:

| Dimension | Values |
| --- | --- |
| Sample | Table 4 sample (357) / balanced sample (384) |
| Outcome | FTE change (part-time weight 0.5) / weight 0.4 / weight 0.6 / headcount change / FTE growth rate |
| Treatment | New Jersey dummy / initial wage gap |
| Controls | none / brand + ownership / brand + ownership + region |
| Control group | all of Pennsylvania / Philadelphia-area Pennsylvania only / excluding the Easton area |

**Results (`results/tables/specification_curve.csv`, Figure 3):**

| Statistic | All 180 | `nj` class (90) | `gap` class (90) |
| --- | --- | --- | --- |
| Minimum | −0.04 | −0.04 | 0.22 |
| Median | 4.60 | 2.84 | 13.08 |
| Maximum | 18.09 | 5.18 | 18.09 |
| Share positive | **98.9%** | 97.8% | **100%** |
| Share significant at 5% | 48.3% | — | — |

Three readings:

1. **The sign is almost perfectly robust.** 178 of the 180 specifications give a positive
   estimate (all of the `gap` class are positive). The only two negative estimates come from
   the `nj` class and are −0.04 in magnitude, which is essentially zero.
2. **Significance is fragile.** Only 48.3% of specifications are significant at the 5% level.
   **This is precisely where the paper's null result calls for the most caution**: saying
   "employment did not fall" is well supported (98.9% of specifications are positive), but
   saying "employment rose significantly" depends on which half of the specifications the
   researcher happened to pick.
3. **`gap` is more powerful than `nj`.** With `nj` as the treatment the median is 2.84; with
   `gap` it is 13.08, and 100% of those estimates are positive. This is intuitive: `gap`
   exploits variation in the intensity of the policy across stores rather than treating all New
   Jersey stores as a homogeneous treatment group — including the 8.9% the policy never
   constrained — and so carries less noise.

### 5.2 Randomisation inference: a p-value that does not rely on OLS standard errors

OLS standard errors rely on normality, homoskedasticity and related assumptions. Randomisation
inference does not: under the strict null of no effect, treatment labels are exchangeable
across stores, so the labels can be reshuffled 10,000 times to see how extreme the actual
estimate is within the reshuffled distribution. The random seed is fixed at `SEED = 20260401`,
so results reproduce digit for digit.

**Results (`results/tables/randomization_inference.csv`, Figure 4):**

| Treatment | Actual estimate | Mean of reshuffled distribution | Std. dev. of reshuffled distribution | Two-sided p |
| --- | --- | --- | --- | --- |
| New Jersey dummy | 2.326 | −0.004 | 1.211 | **0.0548** |
| Initial wage gap | 15.653 | −0.027 | 6.151 | **0.0111** |

The randomisation p-values line up closely with the OLS p-values (0.055 vs 0.052; 0.011 vs
0.010), which shows that the conventional OLS standard errors behave reasonably well in this
sample and are not the weak point of the conclusion. The mean of the reshuffled distribution is
also almost exactly zero (−0.004), confirming that the randomisation scheme itself is correct.

### 5.3 Placebo tests: stores the law did not bind

This is the most persuasive set of checks. If the difference-in-differences is picking up a
**policy effect**, then New Jersey stores whose starting wage before the rise was already above
the new floor — stores the law does not bind — **should not** show any relative employment
change. If they do, then what is being captured is some pre-existing New Jersey-versus-
Pennsylvania difference rather than the policy.

**Results (`results/tables/placebo_tests.csv`, Figure 5):**

| Group | N (treated) | Difference-in-differences | p | Nature |
| --- | --- | --- | --- | --- |
| All New Jersey stores | 290 | 2.33 | 0.111 | Baseline |
| Wave-1 starting wage ≥ $5.05 | 25 | −2.72 | 0.218 | Placebo: law does not bind |
| Wave-1 starting wage ≥ $5.00 | 67 | **−0.03** | **0.986** | Placebo: barely affected |
| Wave-1 starting wage ≤ $4.25 | 93 | **3.32** | **0.039** | Treated: fully bitten by the law |

Reading:

- **For stores the law entirely fails to bind (≥ $5.00, n = 67) the estimate is −0.03 with
  p = 0.986, essentially an exact zero.** This is a strong placebo result: among stores the law
  did not touch, we also find no "New Jersey effect".
- **For stores the law fully bites (≤ $4.25, n = 93) the estimate is +3.32 with p = 0.039.**
  The stores most tightly constrained by the policy show the largest relative employment
  increase — the opposite of what the competitive model's "minimum wages reduce employment"
  prediction implies.
- **The ≥ $5.05 group (n = 25) has a point estimate of −2.72, but p = 0.218 and a confidence
  interval of [−7.05, 1.60] wide enough to contain both 0 and +3.32.** With only 25 stores this
  group has no power to distinguish anything, so it can be read neither as "a negative effect
  was found" nor as "zero was confirmed". I report it so as not to hide an unfavourable point
  estimate — but its difference from the ≥ $5.00 group (n = 67, estimate −0.03) is entirely
  within sampling noise, and the two are not in conflict.

Note that the pattern of p-values across the placebo and treated groups (0.986 vs 0.039) lines
up exactly with the ordering of how tightly the policy binds. That is more informative than
mere "insignificance".

### 5.4 Balance checks: were the two states comparable before the rise?

The credibility of a difference-in-differences rests on whether the two states were comparable
before the policy. **Results (`results/tables/balance_table.csv`):**

| Variable (wave 1) | NJ mean | PA mean | Difference | p |
| --- | --- | --- | --- | --- |
| Full-time-equivalent employment | 20.51 | 23.63 | −3.11 | 0.051 |
| Full-time employees | 7.81 | 10.35 | −2.54 | 0.074 |
| Part-time employees | 18.62 | 19.42 | −0.80 | 0.551 |
| Managers | 3.39 | 3.57 | −0.17 | 0.240 |
| Starting wage | 4.61 | 4.65 | −0.04 | 0.387 |
| Hours open | 14.41 | 14.57 | −0.16 | 0.685 |
| Price of a medium soda | 1.064 | 0.974 | +0.090 | **< 0.001** |
| Price of a small fries | 0.942 | 0.844 | +0.097 | **< 0.001** |
| Entrée price | 1.371 | 1.222 | +0.149 | 0.085 |
| Share of company-owned stores | 0.355 | 0.358 | −0.003 | 0.963 |

**One finding has to be reported honestly: the two states were not fully comparable before the
rise.**

- **Employment levels differ, and the difference approaches significance.** Pennsylvania stores
  averaged 23.63 FTE positions against New Jersey's 20.51, a difference of −3.11 (p = 0.051).
  Pennsylvania stores are larger. This does not by itself invalidate the difference-in-
  differences — a level difference does not compromise identification as long as the two states
  share the same employment *trend* — but it is a weakness worth acknowledging: the paper's
  text likewise notes that New Jersey stores are smaller. If size is correlated with
  sensitivity of employment to shocks (for instance, if larger stores ride out recessions
  better), the parallel-trends assumption is under threat.
- **Product prices differ significantly.** Sodas and fries are significantly more expensive in
  New Jersey (p < 0.001). This reflects genuine differences in the two states' market
  environments (costs, competition, demand) and is a counterexample to the claim that the two
  states "share the same labour market".
- **The good news: starting wages are almost exactly the same (4.61 vs 4.65, p = 0.387), and
  that is the comparability dimension identification depends on most.** The part-time share,
  opening hours and the company-owned share are all highly comparable too.

**The practical implication of this set of checks is** that the identifying basis for the
cross-state comparison (`nj`) is somewhat weaker than the paper's text suggests, which explains
why in Section 5.1 the `nj`-class estimates fluctuate more (standard deviation 1.78, against
6.07 for the `gap` class, though the latter is more stable relative to its own magnitude).
**The within-state comparison (`gap`) does not depend on cross-state comparability, and in that
sense is more credible — and it delivers the larger, more robust effect.** The paper's
two-legged design shows its value here.

### 5.5 Standard-error sensitivity

The original paper reports conventional (homoskedastic) standard errors. If the residuals are
heteroskedastic, conventional standard errors are understated.

**Results (`results/tables/se_sensitivity.csv`):**

| Variance estimator | Coefficient | Std. error | t | p |
| --- | --- | --- | --- | --- |
| Conventional (matching the paper) | 2.326 | 1.192 | 1.952 | **0.052** |
| HC1 heteroskedasticity-robust | 2.326 | 1.452 | 1.601 | 0.110 |
| HC3 heteroskedasticity-robust | 2.326 | 1.468 | 1.584 | 0.114 |
| Clustered by brand (4 clusters) | 2.326 | 0.952 | 2.443 | 0.092 |
| Clustered by region (5 clusters) | 2.326 | 1.224 | 1.900 | 0.130 |

**This is the single most important finding of the extension:** once heteroskedasticity-robust
standard errors are used, the p-value rises from 0.052 to 0.110–0.114 — that is, **from
marginally significant to insignificant.** Clustering by region gives p = 0.130, likewise
insignificant. Clustering by brand produces a smaller standard error (0.952), but with only
four clusters clustered standard errors are themselves unreliable at such a small count (at
least 30–50 clusters are usually recommended), so the 0.092 figure should not be read as "a
more precise estimate" — it is a sign that this route is unusable.

Taken together with the specification curve in Section 5.1 (48.3% of specifications
significant), **the conclusion is that the original paper's statistical significance depends on
the relatively narrow convention of conventional standard errors.** This is not to say the
paper is wrong — conventional standard errors were standard practice in 1994, and the
randomisation test, which relies on no variance assumption at all, gives p = 0.055, almost
identical to the conventional one, indicating that conventional standard errors are not
severely understated in this sample. But it does mean that **the stronger statement, "the
minimum-wage increase raised employment", rests on fragile statistical foundations, while the
weaker statement, "there is no evidence of an employment decline", is very solid.**

It is worth noting that **Card and Krueger were themselves cautious in how they phrased the
cross-state comparison.** The abstract concludes that "we find no indication that the rise in
the minimum wage reduced employment" — a **negative** conclusion rather than a positive
finding. In describing the cross-state employment comparison the paper also writes that, since
New Jersey stores were initially smaller, "employment gains in New Jersey coupled with losses
in Pennsylvania led to a small and statistically insignificant interstate" difference.

One detail has to be pointed out here, though, or it would conceal a fact: in discussing
Table 3 the paper reports the difference-in-differences as **2.76 FTE jobs (13 percent), with a
t statistic of 2.03** — just above the 1.96 critical value for a two-sided 5% test. That is to
say, **the t statistic the paper itself reports sits in a very marginal position.** This echoes
the finding earlier in Section 5.5: whether one uses the paper's conventional standard-error
convention or a more robust one, the statistical significance of this conclusion is not solid.

A more accurate way to put it, then, is this: **the paper chose the negative formulation in its
abstract ("no indication that employment was reduced") rather than playing up a t statistic
that barely crosses the threshold — an appropriate judgement.** The robustness checks in this
section support that judgement: they show that the paper's caution was not excessive
conservatism but what the data itself demands.

### 5.6 Sensitivity bounds: how large a bias would overturn the conclusion?

**Results (`results/tables/sensitivity_bounds.csv`):**

| Quantity | Value | Meaning |
| --- | --- | --- |
| Difference-in-differences estimate | +2.33 FTE jobs | Positive means New Jersey employment rose relative to Pennsylvania |
| Standard error | 1.19 | Conventional standard error |
| Bias needed to overturn the sign | 2.33 FTE jobs | An omitted variable would have to push the estimate down by this much |
| In standard deviations | **0.26 of a standard deviation** | The dependent variable's standard deviation is 8.83 |
| As a share of baseline employment | **11.0%** | Mean wave-1 employment is 21.10 FTE jobs |
| In standard errors | **1.95 standard errors** | — |

Reading: to flip the conclusion from "employment did not fall" to "employment fell", an
omitted variable would have to generate a bias equivalent to **0.26 of a standard deviation of
the dependent variable** or **11% of baseline employment**. That is not a small magnitude (in
observational research a bias of 0.26 standard deviations is substantial), but it is by no
means impossible — Section 5.4 has already shown a difference in store size between the two
states at the 0.05 significance level, and if that size difference happens to be correlated
with sensitivity of employment to the recession, it could contribute a bias of the same order.

**This is an honest boundary: the replication supports the paper's conclusion, but that
conclusion is not unassailable.**

---

## 6. Verification, limitations and conclusion

### 6.1 What I did to verify the results

1. **Independent cross-validation of the sample size.** The 357 stores in Table 4 were
   reverse-engineered and rebuilt from the closure rules described in the paper's notes (the
   six permanently closed stores set to zero, the four temporarily closed stores dropped), and
   they match the paper's reported 357 exactly. This is not a fitted quantity — had the closure
   rules been wrong, the sample size would have deviated immediately.
2. **Several mutually independent quantities line up at once.** The sample size (357), the mean
   of the dependent variable (−0.237), its standard deviation (8.825), the four employment
   levels with their standard errors (20.44 / 21.03 / 23.33 / 21.17), the three wage-group store
   counts (101 / 140 / 73), and the coefficients and standard errors in the first four columns
   of Table 4 are all computed from different sides of the data, and all of them match.
3. **The mean of the reshuffled distribution in the randomisation test is approximately zero**
   (−0.004), which validates the randomisation scheme itself.
4. **The placebo test passes.** Stores the law does not bind (n = 67) give −0.03 with p = 0.986.
5. **The whole pipeline was rerun from scratch.** After clearing `data/processed/` and
   `results/`, running `python3 run_all.py` rebuilds every table and figure in about 5 seconds
   with identical results.
6. **Citation checking.** Every number in this report and in `replication_check.csv` labelled as
   coming from the paper was traced back to the PDF's text layer one by one to confirm the paper
   really says it. This step caught a real error: I had written the paper's
   difference-in-differences as 2.75 when it is in fact 2.76, and the net effect of that error
   was to make the replication look more precise than it is. The same check also corrected an
   error in the other direction — I had believed Table 3 could not be checked at all, when in
   fact the employment row of the paper's Table 2 can be read and matches my results. See
   "Error 4" in `AI_USE_DISCLOSURE_en.md`.
7. **Errors found and fixed during code self-checks.** For example, the caption of Figure 2
   originally read "62% of New Jersey stores paid $5.05 or more after the rise", when the
   computed value is 99.7%; it was changed to be computed dynamically by the code rather than
   hard-coded (see "Error 1" in `AI_USE_DISCLOSURE_en.md`).

### 6.2 Limitations

**About the replication:**

1. **Table 3 cannot be compared cell by cell automatically.** The numeric cells of Table 3 are
   images in the supplied PDF and the text layer does not contain those numbers. The Table 3
   results here are my own recomputation from the paper's definitions; what can be compared
   automatically is limited to the employment row of the paper's Table 2, the
   difference-in-differences and t statistic stated in the text, and the wage-group store counts
   in the notes to Table 3. The component cells of Table 3 (the separate means for each wage
   group, and so on) cannot be checked.
2. **There is a 0.01 discrepancy in the Table 3 difference-in-differences** (2.75 here against
   2.76 in the paper's text). The paper does not give the unrounded value and the corresponding
   cell is an image, so the source cannot be traced further. The discrepancy is negligible in
   magnitude.
3. **There is an unexplained 0.069 discrepancy in column (v) of Table 4.** The most likely cause
   is the reference-category parameterisation of the region dummies, which the paper does not
   specify. I chose to report it honestly rather than tune parameters until the numbers matched.
4. **The original paper's sample selection cannot be fully reverse-engineered.** The paper does
   not report how it handled observations with missing values on individual variables; the rule
   I use reproduces 357, but other rules that also reproduce 357 cannot be ruled out.

**About the extension:**

5. **No genuine trend test was performed.** With only two time points, before and after the
   rise, parallel trends cannot be tested directly. I use the balance checks (Section 5.4) as
   indirect evidence, but whether the two states' pre-rise employment *trends* were parallel is
   a question this dataset cannot in principle answer. This is a fundamental limitation of the
   identification strategy.
6. **Clustered standard errors are unreliable.** With only four brands and five regions, the
   number of clusters is too small for the asymptotic properties of clustered standard errors to
   hold. The p = 0.092 from clustering by brand should therefore not be relied upon.
7. **The policy was not randomly assigned, and neither is `gap`.** `gap` is determined by the
   pre-rise starting wage, and starting wages may be correlated with other store
   characteristics (location, foot traffic, local labour-market tightness). Although the
   within-state comparison removes state-level confounding, store-level confounding remains.
8. **The 180 specifications do not exhaust all reasonable choices.** For example, I do not
   consider different time windows (the data have only two waves), different functional forms
   (beyond the growth rate), or different treatments of outliers.
9. **Using many specifications raises a multiple-comparison problem.** The "48.3% significant"
   figure across 180 tests cannot be read against a conventional 5% significance level — with
   this many specifications, some will be significant by chance. That is precisely why I
   emphasise **the consistency of the sign (98.9%)** rather than the share significant: the
   former is insensitive to multiple comparisons.

### 6.3 Conclusion

**On the replication:** I successfully reproduced the core results of Card and Krueger (1994)
using the paper's own data. The coefficients and standard errors in the first four columns of
Table 4 match digit for digit to two decimal places; the regression sample size (357), the mean
and standard deviation of the dependent variable, the four employment levels with their
standard errors, and the wage-group store counts from the notes to Table 3 (101/140/73) all
agree. The only larger discrepancy is the 0.069 in column (v) of Table 4; the Table 3
difference-in-differences differs by a further 0.01 (2.75 here, 2.76 in the paper's text).
Both are reported honestly. **This replication supports the conclusion that the paper's data
and code are reliable.**

**On the extension:** I tested how fragile this null result is and reached three conclusions:

1. **The sign of the estimate is highly robust, and so is its magnitude.** 98.9% of 180
   reasonable specifications give a positive employment effect; randomisation p-values are 0.055
   (cross-state) and 0.011 (within-state wage gap); stores the law does not constrain show a
   relative employment change of −0.03 (p = 0.986); and stores the policy fully bites show a
   relative employment *increase* of 3.32 (p = 0.039). There is **no evidence anywhere in the
   data that this minimum-wage increase reduced employment.**
2. **But statistical significance depends on the specification and the standard-error
   convention.** With heteroskedasticity-robust standard errors the p-value rises to 0.110, only
   48.3% of specifications are significant at the 5% level, and overturning the conclusion would
   require an omitted-variable bias of only 0.26 standard deviations. **The paper's conclusion
   should therefore be stated as "no evidence of an employment decline" rather than "the
   minimum wage raised employment".** Fortunately, that is exactly the cautious phrasing Card
   and Krueger themselves adopt in the paper.
3. **The within-state comparison (`gap`) is more credible than the cross-state one (`nj`).** The
   balance checks reveal significant pre-rise differences between the two states in store size
   and product prices, weakening the identifying basis for the cross-state comparison; the
   within-state comparison does not depend on cross-state comparability, and its estimates are
   larger and more robust (100% positive) with a lower randomisation p-value (0.011). This
   provides empirical support for the paper's choice to use both identification routes.

**A closing note on the course material:** this exercise shows why replication is valuable,
independent work in empirical economics. Replication generates no new knowledge by itself, but
it places the original paper's conclusion inside a workable robustness framework, and thereby
makes it possible to say which parts are solid (the sign, the magnitude, the substance of the
null result) and which depend on the researcher's choices (significance, specification, the
standard-error convention). **The gap between "what the paper says" and "what the data can
support" can only be seen through replication.**

---

## Appendix: list of result files

| File | Content | Report location |
| --- | --- | --- |
| `results/tables/table3_employment.csv` / `.md` / `_en.md` | Table 3: employment levels and changes | Table 2; Section 4.2 |
| `results/tables/table4_regressions.csv` / `.md` / `_en.md` | Table 4: the five regressions | Table 3; Section 4.3 |
| `results/tables/wage_distribution.csv` | Distribution of starting wages | Table 1; Section 4.1 |
| `results/tables/replication_check.csv` | Replication check | Table 4; Section 4.4 |
| `results/tables/specification_curve.csv` | The 180 specifications | Section 5.1 |
| `results/tables/randomization_inference.csv` | Randomisation inference | Section 5.2 |
| `results/tables/randomization_null.csv` | Null distribution from 10,000 reshuffles | Figure 4 |
| `results/tables/placebo_tests.csv` | Placebo tests | Section 5.3 |
| `results/tables/balance_table.csv` | Balance checks | Section 5.4 |
| `results/tables/se_sensitivity.csv` | Standard-error sensitivity | Section 5.5 |
| `results/tables/sensitivity_bounds.csv` | Sensitivity bounds | Section 5.6 |
| `results/figures/fig1_did_employment_en.png` | Difference-in-differences | Section 4.2 |
| `results/figures/fig2_wage_distribution_en.png` | Distribution of starting wages | Section 4.1 |
| `results/figures/fig3_specification_curve_en.png` | Specification curve | Section 5.1 |
| `results/figures/fig4_randomization_inference_en.png` | Randomisation inference | Section 5.2 |
| `results/figures/fig5_placebo_tests_en.png` | Placebo tests | Section 5.3 |

Files without the `_en` suffix in `results/figures/` are the Chinese-language renderings of the
same figures.
