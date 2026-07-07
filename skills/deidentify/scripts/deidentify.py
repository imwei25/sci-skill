#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临床数据脱敏：检测并替换中国医疗数据里最常见的可识别信息(PII/PHI)。

覆盖：身份证号(18/15位,含校验)、手机号、住院号/病案号/门诊号、银行卡、Email、
座机、车牌、（可选）姓名列、具体日期。可对 CSV/Excel 的指定列、或任意文本做脱敏。

设计原则：
  - 宁可多报（把疑似 PII 标出来让人确认），也不要漏掉真 PII。
  - **一致性假名化**：同一个原值在整份数据里替换成同一个假名（P0001、P0002…），
    保留可分析性（能按患者聚合），又不泄露真实身份。映射表单独存，供必要时人工回溯。
  - **默认不把映射表混进脱敏输出**；映射另存 mapping.csv，提醒用户单独妥善保管/或销毁。

用法：
  # 文本/Markdown 文件
  python deidentify.py --input notes.txt --out outputs/notes_deid.txt

  # CSV：脱敏全表（自动扫每个单元格），姓名列显式指定按列假名化
  python deidentify.py --input patients.csv --out outputs/patients_deid.csv \
      --name-cols 姓名,患者姓名 --id-cols 住院号,身份证号

  # 只扫描报告有哪些 PII、不改数据（先看看）
  python deidentify.py --input patients.csv --scan-only
"""
import argparse
import csv
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ---- 检测规则（按精确度从高到低）----

def _id_card_ok(s):
    """18 位身份证校验位核验，降低误报（把随便一串 18 位数字当身份证）。"""
    if len(s) != 18:
        return len(s) == 15 and s.isdigit()  # 老 15 位无校验位，只按长度
    if not re.match(r"^\d{17}[\dXx]$", s):
        return False
    w = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check = "10X98765432"
    total = sum(int(s[i]) * w[i] for i in range(17))
    return check[total % 11] == s[17].upper()


PATTERNS = [
    # (类别, 正则, 可选校验函数)
    ("身份证", re.compile(r"(?<!\d)(\d{17}[\dXx]|\d{15})(?!\d)"), _id_card_ok),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), None),
    ("Email", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), None),
    ("银行卡", re.compile(r"(?<!\d)\d{16,19}(?!\d)"), None),
    ("座机", re.compile(r"(?<!\d)0\d{2,3}-?\d{7,8}(?!\d)"), None),
    ("车牌", re.compile(r"[京津沪渝冀豫云辽黑湘皖鲁苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼新]\s?[A-Z]\s?[A-Z0-9]{5,6}"), None),
    # 住院号/病案号/门诊号/床号：靠标签+数字（避免误伤普通数字）
    ("病案标识", re.compile(r"(住院号|病案号|门诊号|就诊卡号|床号|登记号|标本号)[:：\s]*([A-Za-z0-9\-]{4,})"), None),
    # 具体日期（默认不脱，用 --dates 开启）
    ("日期", re.compile(r"(?<!\d)(19|20)\d{2}[-/年.](0?[1-9]|1[0-2])[-/月.](0?[1-9]|[12]\d|3[01])日?(?!\d)"), None),
]


def make_masker():
    """返回 (mask 函数, 映射表)。同一原值→同一假名，跨整份数据一致。"""
    counters, mapping = {}, {}

    def mask(category, value):
        key = (category, value)
        if key not in mapping:
            counters[category] = counters.get(category, 0) + 1
            prefix = {
                "身份证": "ID", "手机号": "TEL", "Email": "MAIL", "银行卡": "CARD",
                "座机": "TEL", "车牌": "PLATE", "病案标识": "MRN", "日期": "DATE", "姓名": "P",
            }.get(category, "X")
            mapping[key] = f"[{prefix}{counters[category]:04d}]"
        return mapping[key]

    return mask, mapping


def deidentify_text(text, mask, do_dates=False):
    hits = []
    for category, pat, validator in PATTERNS:
        if category == "日期" and not do_dates:
            continue

        def _sub(m):
            # 病案标识：保留标签，替换其后的号码
            if category == "病案标识":
                label, num = m.group(1), m.group(2)
                hits.append((category, num))
                return f"{label}{mask(category, num)}"
            val = m.group(0)
            if validator and not validator(val):
                return val  # 校验不过，不当 PII
            hits.append((category, val))
            return mask(category, val)

        text = pat.sub(_sub, text)
    return text, hits


def process_csv(path, out, mask, name_cols, id_cols, do_dates, scan_only):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        return [], 0
    header = rows[0]
    name_idx = {i for i, h in enumerate(header) if h.strip() in name_cols}
    id_idx = {i for i, h in enumerate(header) if h.strip() in id_cols}
    all_hits = []
    for r in rows[1:]:
        for i, cell in enumerate(r):
            if i in name_idx and cell.strip():
                all_hits.append(("姓名", cell))
                if not scan_only:
                    r[i] = mask("姓名", cell.strip())
                continue
            if i in id_idx and cell.strip():
                all_hits.append(("病案标识", cell))
                if not scan_only:
                    r[i] = mask("病案标识", cell.strip())
                continue
            new, hits = deidentify_text(cell, mask, do_dates)
            all_hits.extend(hits)
            if not scan_only:
                r[i] = new
    if not scan_only:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)
    return all_hits, len(rows) - 1


def main():
    ap = argparse.ArgumentParser(description="临床数据脱敏（中国 PII/PHI）")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="outputs/deidentified_output")
    ap.add_argument("--name-cols", default="", help="CSV 里的姓名列名，逗号分隔")
    ap.add_argument("--id-cols", default="", help="CSV 里的标识号列名（住院号等），逗号分隔")
    ap.add_argument("--dates", action="store_true", help="同时脱敏具体日期（默认不脱）")
    ap.add_argument("--scan-only", action="store_true", help="只报告 PII、不改数据")
    args = ap.parse_args()

    name_cols = {x.strip() for x in args.name_cols.split(",") if x.strip()}
    id_cols = {x.strip() for x in args.id_cols.split(",") if x.strip()}
    mask, mapping = make_masker()
    ext = os.path.splitext(args.input)[1].lower()

    if ext == ".csv":
        hits, n = process_csv(args.input, args.out, mask, name_cols, id_cols, args.dates, args.scan_only)
        scope = f"CSV {n} 行"
    else:
        text = open(args.input, encoding="utf-8", errors="replace").read()
        new, hits = deidentify_text(text, mask, args.dates)
        scope = "文本"
        if not args.scan_only:
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            open(args.out, "w", encoding="utf-8").write(new)

    from collections import Counter
    dist = Counter(c for c, _ in hits)
    print(f"扫描范围：{scope}")
    print("检出 PII：" + ("，".join(f"{k} {v}" for k, v in dist.items()) if dist else "无") )
    if args.scan_only:
        print("（--scan-only：仅扫描，未改数据）")
        print("⚠️ 姓名等中文命名实体正则难以穷尽，务必人工复核！")
        return

    # 映射表另存，提醒单独保管
    if mapping:
        map_path = os.path.splitext(args.out)[0] + "_mapping.csv"
        with open(map_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["类别", "原值", "假名"])
            for (cat, val), pseudo in mapping.items():
                w.writerow([cat, val, pseudo])
        print(f"脱敏输出：{args.out}")
        print(f"⚠️ 映射表：{map_path} —— 含原始 PII，请单独妥善保管或用后销毁，切勿随数据一起外发。")
    print("⚠️ 本工具是辅助：中文姓名/自由文本里的隐性标识难以穷尽，脱敏后务必人工复核再对外共享。")


if __name__ == "__main__":
    main()
