"""Figures for the report.

Input :  data/processed/analysis_sample.csv
         results/tables/*.csv
Output:  results/figures/*.png

Colours come from a colour-blind-safe categorical palette, assigned in a fixed
order.  Every figure carries a legend and direct labels, so identity never
depends on colour alone.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DATA_PROCESSED, FIGURES, NEW_MIN_WAGE, OLD_MIN_WAGE, TABLES

# --------------------------------------------------------------------------
# Palette and shared style.
# --------------------------------------------------------------------------
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#4a3aa7"
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#d9d8d3"
MUTED = "#9a9992"

NJ_COLOR = BLUE
PA_COLOR = ORANGE

DPI = 200

# --------------------------------------------------------------------------
# Language switch.
#
# Every user-visible string is wrapped in T("English", "中文"), and LANG picks
# which one is returned.  main() renders each figure twice, once per language,
# suffixing the English files with "_en".  The Chinese strings are byte-for-byte
# the ones the figures used before this switch existed.
# --------------------------------------------------------------------------
LANG = "zh"


def T(en: str, zh: str) -> str:
    """Return the string for the currently selected language."""
    return en if LANG == "en" else zh


def _out(name: str) -> Path:
    """Output path for a figure, with an "_en" suffix in English mode."""
    suffix = "" if LANG == "zh" else "_en"
    return FIGURES / f"{name}{suffix}.png"


def apply_style() -> None:
    """Recessive grid, thin marks, Chinese-capable font."""
    plt.rcParams.update(
        {
            "font.sans-serif": ["PingFang SC", "Hiragino Sans GB", "Arial Unicode MS"],
            "axes.unicode_minus": False,
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.linewidth": 0.8,
            "axes.labelcolor": TEXT_SECONDARY,
            "text.color": TEXT,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 13,
            "legend.frameon": False,
            "legend.fontsize": 10,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": DPI,
        }
    )


CAPTION_SIZE = 8.5


def finalize(fig, caption: str, top: float = 0.96) -> None:
    """Attach a wrapped caption and lay the figure out.

    The caption is wrapped to the figure width so it never runs off the canvas,
    which a single long line would.
    """
    # Roughly how many full-width characters fit on one line at CAPTION_SIZE.
    chars_per_line = max(40, int(fig.get_figwidth() * 72 / CAPTION_SIZE * 0.96))
    wrapped = "\n".join(textwrap.wrap(caption, width=chars_per_line))
    fig.supxlabel(
        wrapped,
        x=0.01,
        ha="left",
        fontsize=CAPTION_SIZE,
        color=TEXT_SECONDARY,
        linespacing=1.6,
    )


# --------------------------------------------------------------------------
# Figure 1: difference-in-differences in employment.
# --------------------------------------------------------------------------
def figure_did(df: pd.DataFrame) -> None:
    """Employment before and after the rise, by state, on the balanced sample."""
    bal = df[df.sample_balanced]
    nj = bal[bal.STATE == 1]
    pa = bal[bal.STATE == 0]

    nj_before, nj_after = nj.fte1.mean(), nj.fte2.mean()
    pa_before, pa_after = pa.fte1.mean(), pa.fte2.mean()
    did = (nj_after - nj_before) - (pa_after - pa_before)

    fig, ax = plt.subplots(figsize=(6.8, 4.8), layout="constrained")
    x = [0, 1]

    series = [
        ([nj_before, nj_after], NJ_COLOR, T("New Jersey (minimum wage raised)", "新泽西州（最低工资上调）")),
        ([pa_before, pa_after], PA_COLOR, T("Pennsylvania (control group)", "宾夕法尼亚州（对照组）")),
    ]
    for values, color, label in series:
        ax.plot(x, values, color=color, linewidth=1.9, marker="o", markersize=7, label=label, zorder=3)

    # Label each point on the side away from the other series, so the two
    # labels never overlap where the lines converge at the right-hand end.
    for values, color, _ in series:
        for xi, vi in zip(x, values):
            other = [v[xi] for v, _, _ in series if v is not values][0]
            above = vi >= other
            ax.annotate(
                f"{vi:.2f}",
                (xi, vi),
                textcoords="offset points",
                xytext=(0, 10 if above else -17),
                ha="center",
                va="bottom" if above else "top",
                fontsize=10,
                color=color,
                fontweight="bold",
                zorder=4,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [
            T("Before\nFeb–Mar 1992", "改革前\n1992年2–3月"),
            T("After\nNov–Dec 1992", "改革后\n1992年11–12月"),
        ]
    )
    ax.set_xlim(-0.28, 1.28)
    ax.set_ylabel(T("Mean full-time-equivalent (FTE) employment", "人均全职当量（FTE）就业人数"))
    ax.set_title(
        T(
            "Figure 1  Fast-food employment change in New Jersey and\nPennsylvania: difference-in-differences",
            "图1  新泽西与宾州快餐店就业变化：双重差分",
        )
    )
    ax.legend(loc="lower left")

    lo = min(pa_after, nj_after)
    ax.set_ylim(lo - 3.2, max(pa_before, nj_before) + 1.8)
    ax.text(
        0.98,
        0.04,
        T(
            f"Difference-in-differences estimate: {did:+.2f} FTE jobs\n(standard error 1.34, t = 2.05)",
            f"双重差分估计：{did:+.2f} 个 FTE 岗位\n（标准误 1.34，t = 2.05）",
        ),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.5,
        color=TEXT,
        bbox=dict(boxstyle="round,pad=0.45", facecolor=SURFACE, edgecolor=GRID, linewidth=0.8),
    )

    finalize(
        fig,
        T(
            "Note: The sample is the 384 stores that reported employment in both waves; FTE counts part-time employees as 0.5. "
            "A positive difference means New Jersey employment rose relative to Pennsylvania.",
            "注：样本为两轮调查均报告就业数据的 384 家门店；FTE 折算按兼职员工计 0.5 人。正的差分表示新泽西相对宾州就业增加。",
        ),
    )
    fig.savefig(_out("fig1_did_employment"))
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 2: starting-wage distributions.
# --------------------------------------------------------------------------
def figure_wages(df: pd.DataFrame) -> None:
    """Starting-wage distributions by state and wave: the bite of the policy.

    Each panel is normalised to shares, because New Jersey has four times as
    many stores as Pennsylvania; raw counts on a shared axis would flatten the
    Pennsylvania panel.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.6), sharey=True, layout="constrained")

    bins = np.arange(4.1, 5.7, 0.1)
    panels = [
        (axes[0], df[df.STATE == 1], T("New Jersey", "新泽西州"), NJ_COLOR),
        (axes[1], df[df.STATE == 0], T("Pennsylvania", "宾夕法尼亚州"), PA_COLOR),
    ]

    for ax, sub, title, accent in panels:
        for series, color, label in [
            (sub.WAGE_ST.dropna(), MUTED, T("Before (Feb–Mar)", "改革前（2–3月）")),
            (sub.WAGE_ST2.dropna(), accent, T("After (Nov–Dec)", "改革后（11–12月）")),
        ]:
            ax.hist(
                series,
                bins=bins,
                weights=np.full(len(series), 1.0 / len(series)),
                histtype="step",
                linewidth=1.9,
                color=color,
                label=label,
            )

        for wage in (OLD_MIN_WAGE, NEW_MIN_WAGE):
            ax.axvline(wage, color=GRID, linewidth=1.3, linestyle="--", zorder=1)
            ax.annotate(
                f"${wage:.2f}",
                xy=(wage, 0.96),
                xycoords=ax.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=9,
                color=TEXT_SECONDARY,
            )

        ax.set_title(title)
        ax.set_xlabel(T("Starting wage ($/hour)", "起薪（美元/小时）"))
        ax.set_xlim(4.05, 5.7)
        ax.set_ylim(0, 0.78)
        # The upper-left corner is empty in both panels because every tall bar
        # sits at or right of the old minimum wage.
        ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.86))

    axes[0].set_ylabel(T("Share of stores", "门店占比"))

    fig.suptitle(
        T(
            "Figure 2  Starting-wage distribution: New Jersey wages bunch at the new floor after the rise",
            "图2  起薪分布：新泽西的工资水平在改革后向新下限集中",
        ),
        fontsize=13,
    )
    nj_wave2 = df[(df.STATE == 1)].WAGE_ST2.dropna()
    share_at_new_min = (nj_wave2 >= NEW_MIN_WAGE - 1e-9).mean()

    finalize(
        fig,
        T(
            "Note: The vertical axis is the share of stores in each state, so that two states whose store counts differ fourfold can be compared. "
            "Dashed lines mark the old and new minimum wages (\\$4.25 and \\$5.05). "
            f"After the rise, {share_at_new_min:.1%} of New Jersey stores started at or above \\$5.05, while Pennsylvania barely changed.",
            "注：纵轴为各州门店的占比，以便比较门店数相差四倍的两个州。虚线为新旧最低工资（4.25 与 5.05 美元）。"
            f"新泽西改革后有 {share_at_new_min:.1%} 的门店起薪达到或超过 5.05 美元，宾州基本不变。",
        ),
    )
    fig.savefig(_out("fig2_wage_distribution"))
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 3: specification curve.
# --------------------------------------------------------------------------
def dimension_labels() -> dict:
    """Row labels for the design matrix, resolved in the current language."""
    return {
        "sample": {
            "sample_table4": T("Regression sample (N=357)", "回归样本 (N=357)"),
            "sample_balanced": T("Balanced sample (N=384)", "平衡样本 (N=384)"),
        },
        "outcome": {
            "fte_change_w50": T("FTE change (part-time = 0.5)", "FTE 变化（兼职=0.5）"),
            "fte_change_w40": T("FTE change (part-time = 0.4)", "FTE 变化（兼职=0.4）"),
            "fte_change_w60": T("FTE change (part-time = 0.6)", "FTE 变化（兼职=0.6）"),
            "headcount_change": T("Headcount change (part-time = 1)", "人数变化（兼职=1）"),
            "fte_growth_w50": T("FTE growth rate", "FTE 增长率"),
        },
        "controls": {
            "none": T("No controls", "无控制变量"),
            "chain_own": T("+ Chain and ownership", "+ 连锁品牌与产权"),
            "chain_own_regions": T("+ Chain, ownership and region", "+ 连锁、产权与地区"),
        },
        "control_group": {
            "all_pa": T("All Pennsylvania stores", "全部宾州门店"),
            "pa1_only": T("Philadelphia suburbs only", "仅费城郊区门店"),
            "exclude_pa2": T("Exclude Easton stores", "剔除伊斯顿门店"),
        },
    }

DIMENSION_ORDER = ["sample", "outcome", "controls", "control_group"]


def figure_specification_curve(df: pd.DataFrame) -> None:
    """Every New-Jersey-dummy specification, sorted, with its design matrix."""
    curve = pd.read_csv(TABLES / "specification_curve.csv")
    curve = curve[curve.treatment == "nj"].sort_values("estimate").reset_index(drop=True)

    fig, (ax_curve, ax_matrix) = plt.subplots(
        2,
        1,
        figsize=(10.6, 8.6),
        sharex=True,
        gridspec_kw={"height_ratios": [2.4, 2.0]},
        layout="constrained",
    )
    fig.get_layout_engine().set(h_pad=0.02)

    x = np.arange(len(curve))
    significant = curve.p_value < 0.05

    ax_curve.errorbar(
        x[~significant],
        curve.estimate[~significant],
        yerr=1.96 * curve.std_error[~significant],
        fmt="o",
        markersize=4,
        color=MUTED,
        elinewidth=1.1,
        capsize=0,
        label=T("Not significant (p ≥ 0.05)", "不显著（p ≥ 0.05）"),
        zorder=3,
    )
    ax_curve.errorbar(
        x[significant],
        curve.estimate[significant],
        yerr=1.96 * curve.std_error[significant],
        fmt="o",
        markersize=4,
        color=BLUE,
        elinewidth=1.1,
        capsize=0,
        label=T("Significant (p < 0.05)", "显著（p < 0.05）"),
        zorder=4,
    )
    ax_curve.axhline(0, color=TEXT_SECONDARY, linewidth=1.0, zorder=2)
    median = curve.estimate.median()
    ax_curve.axhline(median, color=AQUA, linewidth=1.6, linestyle="--", zorder=2)
    ax_curve.annotate(
        T(f"Median {median:.2f}", f"中位数 {median:.2f}"),
        (0, median),
        textcoords="offset points",
        xytext=(4, 5),
        ha="left",
        fontsize=9.5,
        color=AQUA,
        fontweight="bold",
    )
    ax_curve.set_ylabel(T("New Jersey dummy coefficient\n(FTE employment change, jobs)", "新泽西虚拟变量系数\n（FTE 就业变化，个）"))
    ax_curve.set_title(
        T(
            "Figure 3  Specification curve: 90 reasonable specifications of the New Jersey employment effect",
            "图3  规格曲线：新泽西就业效应的 90 种合理设定",
        )
    )
    ax_curve.legend(loc="upper left")
    ax_curve.text(
        0.995,
        0.04,
        T(
            f"{(curve.estimate > 0).mean():.0%} of the {len(curve)} specifications are positive",
            f"{len(curve)} 种设定中 {(curve.estimate > 0).mean():.0%} 为正",
        ),
        transform=ax_curve.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.5,
        color=TEXT,
        bbox=dict(boxstyle="round,pad=0.4", facecolor=SURFACE, edgecolor=GRID, linewidth=0.8),
    )

    # Design matrix: one block per dimension, tick per option.
    labels = dimension_labels()
    y = 0
    yticks, ylabels, separators = [], [], []
    for dim in DIMENSION_ORDER:
        options = list(labels[dim].keys())
        for option in options:
            chosen = curve[dim] == option
            ax_matrix.scatter(x[chosen], np.full(chosen.sum(), y), s=6, color=BLUE, marker="s", zorder=3)
            yticks.append(y)
            ylabels.append(labels[dim][option])
            y += 1
        y += 0.8
        separators.append(y - 0.4)

    for sep in separators[:-1]:
        ax_matrix.axhline(sep, color=GRID, linewidth=0.8, zorder=1)

    ax_matrix.set_yticks(yticks)
    ax_matrix.set_yticklabels(ylabels, fontsize=9)
    ax_matrix.set_ylim(-0.8, y - 0.4)
    ax_matrix.set_xlim(-2, len(curve) + 1)
    ax_matrix.set_xlabel(T("Specification (sorted by estimate, ascending)", "设定（按估计值从小到大排序）"))
    ax_matrix.grid(axis="x", linewidth=0.4, alpha=0.5)
    ax_matrix.grid(axis="y", visible=False)
    ax_matrix.invert_yaxis()

    finalize(
        fig,
        T(
            "Note: Each point is the New Jersey dummy coefficient under one specification, with its 95% confidence interval "
            "(conventional standard errors). The dependent variable is always an employment change, so the vertical axis is "
            "comparable across specifications. All 180 specifications (including the 90 that use the initial wage gap as the "
            "treatment) are in results/tables/specification_curve.csv.",
            "注：每一点为一种设定下的新泽西虚拟变量系数及其 95% 置信区间（常规标准误）。被解释变量统一为就业变化，"
            "因此纵轴单位可比。全部 180 种设定（含以初始工资缺口为处理变量的 90 种）见 "
            "results/tables/specification_curve.csv。",
        ),
    )
    fig.savefig(_out("fig3_specification_curve"))
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 4: randomisation inference.
# --------------------------------------------------------------------------
def figure_randomization(df: pd.DataFrame) -> None:
    """Permutation null distributions with the observed statistic marked."""
    nulls = pd.read_csv(TABLES / "randomization_null.csv")
    summary = pd.read_csv(TABLES / "randomization_inference.csv")

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2), layout="constrained")

    titles = {
        "New Jersey dummy": T("New Jersey dummy", "新泽西虚拟变量"),
        "Initial wage gap": T("Initial wage gap", "初始工资缺口"),
    }

    for ax, (label, sub) in zip(axes, nulls.groupby("variable", sort=False)):
        observed = summary.loc[summary.variable == label, "observed"].iloc[0]
        p_value = summary.loc[summary.variable == label, "p_two_sided"].iloc[0]

        ax.hist(
            sub.permuted_statistic,
            bins=60,
            color=MUTED,
            alpha=0.85,
            label=T("Null distribution (10,000 draws)", "置换零分布（10,000 次）"),
        )
        ax.axvline(
            observed,
            color=BLUE,
            linewidth=2.0,
            label=T(f"Observed {observed:.2f}", f"观测值 {observed:.2f}"),
        )
        ax.set_title(titles.get(label, label))
        ax.set_xlabel(T("Permuted estimate", "置换后估计值"))
        ax.set_yticks([])
        ax.legend(loc="upper left", fontsize=9)
        ax.text(
            0.97,
            0.93,
            T(f"Two-sided permutation p = {p_value:.3f}", f"双侧置换 p = {p_value:.3f}"),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=10,
            color=TEXT,
            bbox=dict(boxstyle="round,pad=0.4", facecolor=SURFACE, edgecolor=GRID, linewidth=0.8),
        )

    axes[0].set_ylabel(T("Frequency", "频数"))
    fig.suptitle(
        T(
            "Figure 4  Randomization inference: permutation null distributions and the observed estimates",
            "图4  随机化推断：置换零分布与观测估计值",
        ),
        fontsize=13,
    )
    finalize(
        fig,
        T(
            "Note: Under the null of no effect, the treatment is exchangeable across stores, so it can be shuffled and re-estimated. "
            "The p-value does not rely on the normal assumption behind OLS standard errors.",
            "注：在“无效应”的原假设下，处理变量在门店之间可交换，故可打乱后重新估计。p 值不依赖 OLS 标准误的正态假设。",
        ),
    )
    fig.savefig(_out("fig4_randomization_inference"))
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 5: placebo tests.
# --------------------------------------------------------------------------
def figure_placebo(df: pd.DataFrame) -> None:
    """Difference-in-differences by how tightly the law bound each group."""
    placebo = pd.read_csv(TABLES / "placebo_tests.csv")
    # Weakest binding first, so the pattern reads top to bottom.
    order = [0, 2, 1, 3]  # all NJ, >=5.05, >=5.00, <=4.25
    placebo = placebo.iloc[order].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8.8, 4.8), layout="constrained")
    y = np.arange(len(placebo))[::-1]

    for yi, (_, row) in zip(y, placebo.iterrows()):
        is_placebo = row.interpretation.startswith("Placebo")
        color = MUTED if is_placebo else BLUE
        ax.errorbar(
            row.did_estimate,
            yi,
            xerr=1.96 * row.std_error,
            fmt="o",
            markersize=7,
            color=color,
            elinewidth=1.6,
            capsize=3,
            zorder=3,
        )
        ax.annotate(
            f"{row.did_estimate:+.2f}  (p = {row.p_value:.3f})",
            (row.did_estimate, yi),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=9.5,
            color=color,
            fontweight="bold",
        )

    ax.axvline(0, color=TEXT_SECONDARY, linewidth=1.0, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [
            T(
                f'{r["test"]}\n({r.n_treated} treated / {r.n_control} control)',
                f"{r.test_zh}\n（处理组 {r.n_treated} 家 / 对照组 {r.n_control} 家）",
            )
            for _, r in placebo.iterrows()
        ],
        fontsize=9.5,
    )
    ax.set_xlabel(T("Employment change relative to Pennsylvania stores (FTE jobs)", "相对宾州门店的就业变化（FTE 岗位）"))
    ax.set_title(
        T(
            "Figure 5  Placebo tests: the weaker the law binds,\nthe smaller the estimated effect",
            "图5  安慰剂检验：法律约束越弱，估计效应越小",
        )
    )
    ax.set_xlim(-8.5, 9.5)
    ax.set_ylim(-0.85, len(placebo) - 0.35)
    ax.grid(axis="y", visible=False)

    handles = [
        plt.Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=BLUE,
            markersize=7,
            label=T("Bound by the law (treated)", "受法律约束（处理组）"),
        ),
        plt.Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=MUTED,
            markersize=7,
            label=T("Barely bound (placebo)", "几乎不受约束（安慰剂）"),
        ),
    ]
    ax.legend(handles=handles, loc="lower left", borderaxespad=0.8)

    finalize(
        fig,
        T(
            "Note: Error bars are 95% confidence intervals. New Jersey stores that already paid at least \\$5.05 before the rise were not "
            "bound by the law, and their relative employment change is close to 0, showing the estimate does not stem from a pre-existing "
            "New Jersey–Pennsylvania difference.",
            "注：误差棒为 95% 置信区间。改革前起薪已不低于 5.05 美元的新泽西门店不受该法约束，其相对就业变化接近 0，"
            "说明估计值并非来自新泽西与宾州的固有差异。",
        ),
    )
    fig.savefig(_out("fig5_placebo_tests"))
    plt.close(fig)


def main() -> None:
    global LANG

    FIGURES.mkdir(parents=True, exist_ok=True)
    apply_style()

    df = pd.read_csv(DATA_PROCESSED / "analysis_sample.csv")

    for lang in ("zh", "en"):
        LANG = lang
        figure_did(df)
        figure_wages(df)
        figure_specification_curve(df)
        figure_randomization(df)
        figure_placebo(df)

    for path in sorted(FIGURES.glob("*.png")):
        print(f"wrote {path.relative_to(FIGURES.parents[1])}")


if __name__ == "__main__":
    main()
