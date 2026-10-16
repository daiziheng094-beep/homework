# 复现并扩展 Card 与 Krueger (1994)：新泽西最低工资与快餐业就业

本项目复制 Card 与 Krueger 发表于 *American Economic Review* (1994) 的论文
《Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New
Jersey and Pennsylvania》的核心结果，并在此基础上做了一项独立的稳健性扩展。

论文研究的问题是：1992 年 4 月 1 日新泽西州把最低工资从每小时 4.25 美元提高到
5.05 美元之后，快餐店的就业是否下降。作者比较了新泽西与最低工资保持不变的宾夕法尼亚州
（双重差分），又在新泽西内部比较了改革前工资较高与较低的门店。结论是：没有证据表明这次
最低工资上调减少了就业。

本仓库用论文原始调查数据 `public.csv` 重建了该结论，并进一步检验它有多稳健。

---

## 一、快速开始

```bash
# 1. 安装依赖（Python 3.10 或更高版本）
pip install -r requirements.txt

# 2. 取得原始数据（本仓库不含该文件，原因见第五节）
#    从课程平台下载 01_DID.zip，解压后把 public.csv 放到：
#    data/raw/public.csv

# 3. 一条命令生成全部表格与图表
#    macOS/Linux 上是 python3；Windows 上通常写作 python
python3 run_all.py
```

运行结束后，所有输出写入 `results/tables/`（表格）与 `results/figures/`（图），
中间数据写入 `data/processed/`。整个流程约 5 秒，无需手工修改任何文件。

> **可复现性约定：** 只要把原始数据 `public.csv` 放进 `data/raw/`，`run_all.py`
> 就能从零重建报告中的每一张表和每一幅图。所有随机过程（置换检验）都固定了随机种子
> （`src/config.py` 中的 `SEED`），因此结果逐位可复现。
>
> 输入文件缺失时 `run_all.py` 会明确报错退出，不会静默生成空结果。

---

## 二、目录结构

```
.
├── README.md                     本文件：如何复现结果（中文）
├── README_en.md                  同一份说明的英文版
├── AI_USE_DISCLOSURE.md          人工智能使用披露（中文）
├── AI_USE_DISCLOSURE_en.md       同一份披露的英文版
├── run_all.py                    一键运行入口（唯一需要执行的脚本）
├── requirements.txt              Python 依赖
│
├── data/
│   ├── raw/
│   │   ├── public.csv            ← 原始调查数据（410 家门店 × 46 列）。
│   │   │                           本仓库不含此文件，需自行放入，见第五节
│   │   └── README.md             数据来源、获取方式与使用限制
│   └── processed/
│       ├── analysis_sample.csv   ← 处理后数据：全部分析变量，410 行（门店级）。
│       │                           本仓库不含此文件，由第 1 步自动生成，见第五节
│       └── descriptives.csv      各样本口径的描述统计（汇总结果，随仓库分发）
│
├── src/                          分析代码
│   ├── config.py                 路径、政策参数、样本定义、随机种子
│   ├── prepare_data.py           构建分析样本与派生变量
│   ├── replication.py            复制原论文表 3、表 4
│   ├── robustness.py             独立扩展：稳健性与敏感性检验
│   └── figures.py                生成全部图（中英各一套）
│
├── results/
│   ├── tables/                   全部表格（.csv，表 3/表 4 另有 .md 与 _en.md 两种渲染）
│   └── figures/                  全部图（.png 为中文版，*_en.png 为英文版）
│
├── report/
│   ├── empirical_report.md       实证报告正文（中文）
│   └── empirical_report_en.md    同一份报告的英文版
│
├── docs/
│   └── njmin-aer.pdf             被复现的论文原文
│
└── .claude/skills/
    ├── replicate-card-krueger-did/
    │   └── SKILL.md              可复用技能（中文）
    └── replicate-card-krueger-did-en/
        └── SKILL.md              可复用技能（英文）
```

**中英两套结果在同一命令中一起生成。** 图中不带后缀的是中文版（`figN_*.png`），
带 `_en` 后缀的是英文版（`figN_*_en.png`）；表 3、表 4 的格式化渲染同理。两套结果的
数字完全一致，只是语言不同。

---

## 三、分析流程

`run_all.py` 依次执行四个模块，每个模块也可单独运行：

| 步骤 | 脚本 | 输入 | 输出 |
| --- | --- | --- | --- |
| 1 | `src/prepare_data.py` | `data/raw/public.csv` | `data/processed/analysis_sample.csv`、`descriptives.csv` |
| 2 | `src/replication.py` | 上一步的样本 | `table3_employment`、`table4_regressions`、`wage_distribution`、`replication_check` |
| 3 | `src/robustness.py` | 上一步的样本 | `specification_curve`、`randomization_inference`、`randomization_null`、`placebo_tests`、`balance_table`、`se_sensitivity`、`sensitivity_bounds` |
| 4 | `src/figures.py` | 以上全部 | `fig1`–`fig5` |

单独运行某个模块（例如只重做图）：

```bash
python3 src/figures.py
```

---

## 四、核心结果一览

**复制结果与原论文完全一致。** 表 4 的五列中，前四列与原论文报告的系数和标准误差
在两位小数上逐位相同（2.33、2.30、15.65、14.92）；第五列（含地区控制变量）本复现为
11.98 (7.42)，原论文为 11.91 (7.39)，差异见 `results/tables/replication_check.csv`。
第六个样本量的口径（357 家门店）与论文注释完全一致。

| 结果 | 本复现 | 原论文 |
| --- | --- | --- |
| 表 4 (i) 新泽西虚拟变量 | 2.33 (1.19) | 2.33 (1.19) |
| 表 4 (iii) 初始工资缺口 | 15.65 (6.08) | 15.65 (6.08) |
| 表 4 回归样本量 | 357 | 357 |
| 表 3 双重差分（论文正文） | 2.75 (1.34) | 2.76 (1.36) |
| 就业水平 NJ 改革前 / 改革后 | 20.44 (0.51) / 21.03 (0.52) | 20.4 (0.51) / 21.0 (0.52) |
| 表 3 注中新泽西工资分组 | 101 / 140 / 73 | 101 / 140 / 73 |

**独立扩展的结论：** 在 180 种同样站得住脚的设定中，98.9% 给出正的就业效应；
置换检验给出的 p 值为 0.055（新泽西虚拟变量）与 0.011（工资缺口）；改革前起薪已高于
新下限、不受该法约束的新泽西门店，其相对就业变化为 −0.03（p = 0.986）。估计值稳健，
但把它精确地识别为显著为正需要比论文更谨慎的表述。

详细讨论见 `report/empirical_report.md`。

---

## 五、数据说明与使用限制

- 原始数据 `public.csv` 为门店层面的调查数据，共 410 家门店、46 列，由课程提供的
  `01_DID.zip` 分发。字段含义见 `data/raw/README.md`。
- 该数据仅供本课程项目在课程数据使用条款范围内使用，**不得公开分发**。因此
  **本公开仓库中不含 `data/raw/public.csv`**（已由 `.gitignore` 排除）。复现前请按
  第一节第 2 步把该文件放入 `data/raw/`，获取方式详见 `data/raw/README.md`。
- 论文原文 `docs/njmin-aer.pdf` 同样受版权保护，未随仓库分发；请按上文引用文献自行取得。
- **`data/processed/analysis_sample.csv` 也未随仓库分发。** 它是 410 行的门店级分析
  样本，逐店可读且保留了原始文件的全部列，公开它等同于公开原始数据。该文件由
  `src/prepare_data.py` 在复现时自动重建，不需要随仓库分发。
- **仓库中已跟踪的部分可以安全公开：** 全部代码（`src/`）、`data/raw/README.md`
  的字段说明、`data/processed/descriptives.csv`，以及 `results/` 下的全部表格与图。
  它们都是汇总结果，不含逐店记录。

---

## 六、环境

- Python 3.10+
- 依赖见 `requirements.txt`：`pandas`、`numpy`、`scipy`、`statsmodels`、
  `matplotlib`。绘图使用系统自带中文字体（PingFang SC / Hiragino Sans GB）；
  若在非 macOS 环境运行，请在 `src/figures.py` 的字体列表中补充本机可用的中文字体。

代码在以下环境验证通过：Python 3.14、pandas 3.0.5、numpy 2.5.3、
statsmodels 0.15.0、matplotlib 3.11.2。
