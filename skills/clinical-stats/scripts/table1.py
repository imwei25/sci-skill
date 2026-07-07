#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成临床论文的 Table 1（基线特征表）。

按变量类型自动选择呈现与检验方式：
  - 连续变量：正态(Shapiro) → 均数±标准差 + t/ANOVA；非正态 → 中位数[IQR] + Mann-Whitney/Kruskal
  - 分类变量：n (%) + 卡方；期望频数 <5 或样本小 → Fisher 精确检验（2x2）
分组列可选（--group）；给了就出组间比较 p 值列。

只用已安装的 pandas/numpy/scipy，无需额外依赖。

用法：
  python table1.py --input data.csv --group arm \
      --continuous age,bmi,sbp --categorical sex,smoker \
      --out outputs/table1.csv
  # 不指定变量类型时自动推断（数值→连续，其余→分类）
  python table1.py --input data.csv --group arm --out outputs/table1.csv
"""
import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import numpy as np
    import pandas as pd
    from scipy import stats
except ImportError:
    sys.exit("缺少 pandas/numpy/scipy：请先运行 install.ps1 / install.sh（或 env-setup 技能）")


def is_normal(x):
    x = x.dropna()
    if len(x) < 3:
        return True
    if len(x) > 5000:
        x = x.sample(5000, random_state=0)
    try:
        return stats.shapiro(x)[1] > 0.05
    except Exception:
        return False


def fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "—"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def summarize_continuous(df, var, group, groups):
    x_all = pd.to_numeric(df[var], errors="coerce")
    normal = is_normal(x_all)
    row = {"变量": f"{var}" + ("（均数±SD）" if normal else "（中位数[IQR]）")}
    cells = []
    for g in groups:
        x = pd.to_numeric(df.loc[df[group] == g, var], errors="coerce").dropna() if group else x_all.dropna()
        if normal:
            cells.append((g, f"{x.mean():.2f}±{x.std():.2f}"))
        else:
            q1, q3 = x.quantile(0.25), x.quantile(0.75)
            cells.append((g, f"{x.median():.2f}[{q1:.2f}, {q3:.2f}]"))
    for g, v in cells:
        row[str(g)] = v
    # p 值
    p = None
    if group and len(groups) >= 2:
        samples = [pd.to_numeric(df.loc[df[group] == g, var], errors="coerce").dropna() for g in groups]
        samples = [s for s in samples if len(s) > 0]
        try:
            if len(samples) == 2:
                p = stats.ttest_ind(*samples, equal_var=False)[1] if normal else stats.mannwhitneyu(*samples)[1]
            elif len(samples) > 2:
                p = stats.f_oneway(*samples)[1] if normal else stats.kruskal(*samples)[1]
        except Exception:
            p = None
    row["P"] = fmt_p(p)
    row["检验"] = ("" if not group else
                   ("t/Welch" if normal and len(groups) == 2 else
                    "ANOVA" if normal else
                    "Mann-Whitney" if len(groups) == 2 else "Kruskal-Wallis"))
    return row


def summarize_categorical(df, var, group, groups):
    rows = []
    cats = df[var].dropna().unique()
    # 列联表用于检验
    p, test = None, ""
    if group and len(groups) >= 2:
        ct = pd.crosstab(df[var], df[group])
        try:
            chi2, p_chi, dof, expected = stats.chi2_contingency(ct)
            if ct.shape == (2, 2) and (expected < 5).any():
                p = stats.fisher_exact(ct.values)[1]
                test = "Fisher 精确"
            else:
                p = p_chi
                test = "卡方"
        except Exception:
            p, test = None, ""
    header = {"变量": f"{var}, n(%)"}
    for g in groups:
        header[str(g)] = ""
    header["P"] = fmt_p(p)
    header["检验"] = test
    rows.append(header)
    for c in cats:
        r = {"变量": f"　{c}"}
        for g in groups:
            sub = df[df[group] == g] if group else df
            n = (sub[var] == c).sum()
            denom = sub[var].notna().sum()
            r[str(g)] = f"{n} ({100*n/denom:.1f})" if denom else "0 (0.0)"
        r["P"] = ""
        r["检验"] = ""
        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description="生成 Table 1 基线特征表")
    ap.add_argument("--input", required=True)
    ap.add_argument("--group", default=None, help="分组列名（可选）")
    ap.add_argument("--continuous", default="", help="连续变量，逗号分隔（默认自动推断）")
    ap.add_argument("--categorical", default="", help="分类变量，逗号分隔（默认自动推断）")
    ap.add_argument("--out", default="outputs/table1.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.input) if args.input.lower().endswith(".csv") else pd.read_excel(args.input)
    group = args.group
    if group and group not in df.columns:
        sys.exit(f"分组列 {group!r} 不在数据里。可用列：{list(df.columns)}")
    groups = sorted(df[group].dropna().unique().tolist()) if group else ["总体"]

    cont = [c.strip() for c in args.continuous.split(",") if c.strip()]
    cat = [c.strip() for c in args.categorical.split(",") if c.strip()]
    if not cont and not cat:  # 自动推断
        for c in df.columns:
            if c == group:
                continue
            if pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() > 6:
                cont.append(c)
            else:
                cat.append(c)

    out_rows = []
    # 首行：各组 n
    nrow = {"变量": "样本量 n"}
    for g in groups:
        nrow[str(g)] = str((df[group] == g).sum() if group else len(df))
    nrow["P"] = ""
    nrow["检验"] = ""
    out_rows.append(nrow)

    for v in cont:
        if v in df.columns:
            out_rows.append(summarize_continuous(df, v, group, groups))
    for v in cat:
        if v in df.columns:
            out_rows.extend(summarize_categorical(df, v, group, groups))

    cols = ["变量"] + [str(g) for g in groups] + (["P", "检验"] if group else [])
    result = pd.DataFrame(out_rows)
    for c in cols:
        if c not in result.columns:
            result[c] = ""
    result = result[cols]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    result.to_csv(args.out, index=False, encoding="utf-8-sig")

    print(f"Table 1 已生成：{args.out}（{len(cont)} 连续 + {len(cat)} 分类变量，分组={group or '无'}）")
    print("⚠️ 自动选择检验只是起点：请人工核对每个变量的检验是否合适（如配对/重复测量、协变量调整需另做）。")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
