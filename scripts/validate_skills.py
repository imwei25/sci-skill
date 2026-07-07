#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 skills/ 下所有 SKILL.md：无 BOM、frontmatter 含 name+description、name 与目录名一致。
BOM 会让部分技能加载器（OpenCode 等）崩溃，所以单独查。退出码非 0 表示有问题。"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "skills")


def parse_fm(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def main():
    if not os.path.isdir(BASE):
        print("[x] 找不到 skills/ 目录"); sys.exit(1)
    errs, names = [], []
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
            errs.append(f"[frontmatter] {d}/SKILL.md 缺少合法 frontmatter"); continue
        if fm.get("name") != d:
            errs.append(f"[name] {d}/SKILL.md name={fm.get('name')!r} 与目录名不一致")
        if not fm.get("description"):
            errs.append(f"[frontmatter] {d}/SKILL.md 缺 description")
    print(f"skills/: {len(names)} 个技能 -> {', '.join(names)}")
    print("-" * 50)
    if errs:
        print(f"发现 {len(errs)} 个问题：")
        for e in errs:
            print("  [x]", e)
        sys.exit(1)
    print(f"[OK] 全部通过：{len(names)} 个技能，无 BOM，frontmatter 合法。")


if __name__ == "__main__":
    main()
