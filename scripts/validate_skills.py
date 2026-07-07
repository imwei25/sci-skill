#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 skills/ 下所有 SKILL.md，并可选自检运行环境。

格式校验（默认）：
  - 无 UTF-8 BOM（BOM 会让部分技能加载器崩溃）
  - frontmatter 合法：能解析 name/description（支持 YAML 折叠块 >- / > / | / |-）
  - name 符合 Agent Skills 规范：与目录名一致、<=64 字符、仅 a-z0-9-、不以连字符开头/结尾
  - description 非空且 <=1024 字符（规范硬上限，超长会被部分加载器截断/拒载）
  - 非规范 frontmatter 字段（triggers/tools/model/version/author 等）给出警告：
    官方规范只认 name/description/license/compatibility/metadata/allowed-tools

环境自检（--env，install.ps1 / install.sh 收尾时调用）：
  - Python 版本 >= 3.10
  - 逐能力组 import 关键依赖包
  - pandoc / xelatex 是否在 PATH
  - 按能力输出人话结论（文献检索、数据分析、PDF 排版……各自可不可用）

退出码非 0 表示有错误（警告不影响退出码）。"""
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "skills")

SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_OK = set("abcdefghijklmnopqrstuvwxyz0123456789-")


def parse_fm(text):
    """极简 YAML frontmatter 解析：支持 k: v、折叠块 >- / > / | / |-（后续缩进行并入值）。
    只为校验 name/description 服务，不求完整 YAML 语义。"""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm = {}
    lines = text[3:end].splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("#"):
            i += 1
            continue
        if line[:1] in (" ", "\t"):  # 缩进行（未被块收集的，如 metadata 子键）跳过
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v in (">", ">-", "|", "|-"):  # 块标量：吃掉后续所有缩进行
            block = []
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                block.append(lines[i].strip())
                i += 1
            sep = " " if v.startswith(">") else "\n"
            fm[k] = sep.join(b for b in block if b)
            continue
        fm[k] = v.strip("'\"")
        i += 1
    return fm


def check_skills():
    errs, warns, names = [], [], []
    if not os.path.isdir(BASE):
        return ["[x] 找不到 skills/ 目录"], [], []
    for d in sorted(os.listdir(BASE)):
        sk = os.path.join(BASE, d, "SKILL.md")
        if not os.path.isfile(sk):
            continue
        names.append(d)
        raw = open(sk, "rb").read()
        if raw.startswith(b"\xef\xbb\xbf"):
            errs.append(f"[BOM] {d}/SKILL.md 带 UTF-8 BOM，会导致加载器崩溃")
        fm = parse_fm(raw.decode("utf-8", "replace"))
        if not fm:
            errs.append(f"[frontmatter] {d}/SKILL.md 缺少合法 frontmatter")
            continue
        name = fm.get("name", "")
        if name != d:
            errs.append(f"[name] {d}/SKILL.md name={name!r} 与目录名不一致")
        if not name or len(name) > 64 or (set(name) - NAME_OK) or name[0] == "-" or name[-1] == "-":
            errs.append(f"[name] {d}: name 须 <=64 字符、仅小写字母/数字/连字符、不以连字符开头结尾")
        desc = fm.get("description", "")
        if not desc:
            errs.append(f"[description] {d}/SKILL.md 缺 description")
        elif len(desc) > 1024:
            errs.append(f"[description] {d}: description {len(desc)} 字符，超过规范上限 1024，会被部分加载器截断/拒载")
        extra = set(fm) - SPEC_FIELDS
        if extra:
            warns.append(f"[字段] {d}: 非规范 frontmatter 字段 {sorted(extra)}（严格加载器可能忽略或报错；tools 不等于 allowed-tools）")
    return errs, warns, names


# ---- 环境自检（--env）----

CAPABILITIES = [
    ("数据分析 / 统计（data-analysis）",
     ["pandas", "numpy", "scipy", "statsmodels", "sklearn", "seaborn", "matplotlib", "lifelines", "openpyxl"]),
    ("文献检索 / 核查（literature-review, reference-check, search-lit）",
     ["requests", "bibtexparser", "rispy", "pyalex", "habanero"]),
    ("全文下载 / PDF 转换（fulltext-retrieval）",
     ["fitz", "pymupdf4llm"]),
    ("文档生成（grant-proposal 等）",
     ["docx", "reportlab", "lxml", "bs4"]),
]


def check_env():
    import importlib
    lines, problems = [], []
    v = sys.version_info
    py_ok = v >= (3, 10)
    lines.append(f"{'[ OK ]' if py_ok else '[FAIL]'} Python {v.major}.{v.minor}.{v.micro}"
                 + ("" if py_ok else "（需要 3.10+）"))
    if not py_ok:
        problems.append("Python 版本过低，需 3.10+")
    for cap, mods in CAPABILITIES:
        missing = []
        for m in mods:
            try:
                importlib.import_module(m)
            except Exception:
                missing.append(m)
        if missing:
            lines.append(f"[FAIL] {cap}：缺 {', '.join(missing)} —— 重跑 install.ps1 / install.sh")
            problems.append(f"{cap} 缺包")
        else:
            lines.append(f"[ OK ] {cap}：依赖齐全")
    pandoc = shutil.which("pandoc")
    xelatex = shutil.which("xelatex")
    if not xelatex and os.name == "nt":
        guess = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX", "miktex", "bin", "x64", "xelatex.exe")
        if os.path.isfile(guess):
            xelatex = guess
    if pandoc and xelatex:
        lines.append(f"[ OK ] PDF 排版（render-pdf-doc）：pandoc + xelatex 就绪")
    else:
        miss = [n for n, p in (("pandoc", pandoc), ("xelatex", xelatex)) if not p]
        lines.append(f"[跳过] PDF 排版（render-pdf-doc）：缺 {'+'.join(miss)}。只在需要出 PDF 时安装："
                     f"install.ps1 -WithPdf / install.sh --with-pdf")
        # PDF 工具链是可选项，不计入 problems
    return lines, problems


def main():
    env_mode = "--env" in sys.argv
    errs, warns, names = check_skills()
    print(f"skills/: {len(names)} 个技能 -> {', '.join(names)}")
    print("-" * 50)
    for w in warns:
        print("  [!]", w)
    if errs:
        print(f"发现 {len(errs)} 个错误：")
        for e in errs:
            print("  [x]", e)
    else:
        print(f"[OK] SKILL.md 格式全部通过（{len(names)} 个技能）。")
    exit_code = 1 if errs else 0
    if env_mode:
        print("-" * 50)
        print("环境自检：")
        lines, problems = check_env()
        for line in lines:
            print(" ", line)
        if problems:
            exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
