---
name: render-docx
description: 把 Markdown 稿件渲染成 Word (.docx) 投稿版。医学期刊投稿绝大多数要 Word（不是 PDF），国自然正文、中文核心期刊也多用 .docx 模板。支持套用期刊 Word 模板（--reference-doc）、可选按 GB/T 7714 等 CSL 渲染参考文献。用 pandoc，中文不会像 xelatex 那样漏字。当用户说"出 Word""转 docx""投稿要 Word 版""按期刊模板排版""生成 .docx"时使用。要出 PDF 用 render-pdf-doc；要查引用真实性用 reference-check。
---

# Markdown → Word (.docx) 投稿排版技能

医学期刊投稿系统绝大多数**只收 Word**，编辑修订、Turnitin 查重、作者返修也都基于 .docx。本技能把 Markdown 稿件转成 Word。相比 PDF（xelatex）路线，Word 有个天然好处：**中文不会漏字**——Word 存的是 UTF-8 文本、由系统字体渲染，不像 xelatex 缺字就静默丢掉。

## 依赖
需要 **pandoc**（仓库根 `install.ps1 -WithPdf` / `install.sh --with-pdf` 已装；单独装：`winget install JohnMacFarlane.Pandoc` / `apt-get install pandoc` / `brew install pandoc`）。**不需要 xelatex/MiKTeX**（那是 PDF 才要的）。

## 用法
脚本在 `skills/render-docx/scripts/`，从仓库根运行或用全路径（Windows 经 Git Bash 跑 .sh）：
```bash
# 最简：Markdown → Word
bash skills/render-docx/scripts/render_docx.sh -i outputs/manuscript.md -o outputs/manuscript.docx

# 套用期刊/机构的 Word 模板（继承其样式与字体）
bash skills/render-docx/scripts/render_docx.sh -i outputs/manuscript.md --ref templates/journal_template.docx

# 按 GB/T 7714 渲染参考文献（稿件用 pandoc @citekey 引用、配 .bib 时）
bash skills/render-docx/scripts/render_docx.sh -i outputs/manuscript.md \
  --csl assets/csl/gb-t-7714-2015-numeric.csl --bib outputs/refs.bib
```

## 说明
- **中文**：无需任何字体参数，pandoc 直接产出可正常显示中文的 .docx。若想统一正文字体（如宋体/Times New Roman 混排），提供一份设好样式的 `--reference-doc` 模板即可。
- **期刊模板**：多数中华系列/SCI 期刊提供 Word 模板。把模板作为 `--reference-doc` 传入，pandoc 会套用其"Normal/标题/表格"等样式——比手动排版稳。若用户有目标刊模板，优先用它。
- **参考文献两种情形**：
  - 稿件里已是写好的 `[n]` 编号引用文本 → 直接转，不用 `--csl`。
  - 稿件用 pandoc 引用键 `[@Smith2024]` + 提供 `.bib` → 加 `--csl`（GB/T 7714 见 `assets/csl/`，需先由 `render-pdf-doc`/本仓库分发的 CSL）+ `--bib`，pandoc 自动生成文末参考文献表并按国标格式化。
- **图表**：Markdown 里用 `![标题](图片路径)` 引用的图会嵌入 docx；出版级图先用 `nature-figure` 生成 PNG/TIFF 再引用。

## 衔接
- 上游：`write-paper`（论文）、`grant-proposal`（标书）、`literature-review`（综述）等写完 `.md`，交本技能出 Word。
- 引用真实性：出稿前把参考文献交 `reference-check` 核查（本技能只排版、不核查）。
- 要 PDF 版：用 `render-pdf-doc`。

## 约定
- 产出写 `outputs/`（或工作区约定路径）。
- 渲染后**打开 Word 抽查**：中文显示正常、表格未错位、图已嵌入、参考文献格式对。
- 不虚构内容：本技能只做格式转换，不改写、不补数据。
