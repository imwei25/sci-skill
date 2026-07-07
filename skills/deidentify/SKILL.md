---
name: deidentify
description: 临床数据脱敏 / 去标识化。上传含患者信息的数据（CSV/Excel/病历文本）做研究、作图、投稿前，先把身份证号、手机号、住院号/病案号、姓名、日期、地址、Email 等可识别信息(PII/PHI)检测并替换成一致的假名，保护患者隐私、满足伦理合规。当用户说"脱敏""去标识化""去隐私""患者数据能不能直接分析""上传病历/临床数据前处理""匿名化""deidentify"时使用，或在 data-analysis 检测到疑似患者标识时提示先脱敏。
---

# 临床数据脱敏技能

医学用户把**真实患者数据**上传给 AI 分析/作图/写论文，是隐私与伦理的高风险动作。本技能在数据进入分析前，先检测并替换可识别信息，把风险降到可控。**核心原则：宁可多标（疑似的也标出来让人确认），不可漏标真 PII。**

## Python 环境
> 没有项目根 `.venv`？先运行 `env-setup` 技能。
```
.venv/Scripts/python.exe   # Windows
.venv/bin/python           # Linux / macOS
```

## 覆盖的可识别信息
身份证号（18/15 位，18 位做**校验位核验**降低误报）、手机号、住院号/病案号/门诊号/床号（靠"标签+号码"识别）、银行卡号、座机、Email、车牌、（可选）具体日期、（CSV 按列指定的）姓名。

## 用法
脚本在 `skills/deidentify/scripts/`，从仓库根运行或用全路径：
```bash
# 先扫描看看有哪些 PII、不改数据
.venv/Scripts/python.exe skills/deidentify/scripts/deidentify.py --input uploads/patients.csv --scan-only

# CSV 脱敏：自动扫每个单元格；姓名列、标识号列显式指定按列假名化
.venv/Scripts/python.exe skills/deidentify/scripts/deidentify.py \
  --input uploads/patients.csv --out outputs/patients_deid.csv \
  --name-cols 姓名,患者姓名 --id-cols 住院号,身份证号

# 病历/自由文本
.venv/Scripts/python.exe skills/deidentify/scripts/deidentify.py --input uploads/notes.txt --out outputs/notes_deid.txt

# 同时脱敏具体日期（默认不脱，因日期常是分析变量）
.venv/Scripts/python.exe skills/deidentify/scripts/deidentify.py --input uploads/notes.txt --out outputs/notes_deid.txt --dates
```
> Excel(.xlsx)：先用 `data-analysis` 把工作表另存成 CSV 再脱敏，或在脚本里用 pandas 读入后按列处理。

## 关键设计
- **一致性假名化**：同一个原值在整份数据里替换成同一个假名（`[ID0001]`、`[TEL0001]`、姓名 `[P0001]`……）。这样**既保护身份、又保留可分析性**——能按患者聚合、能追同一手机的多次就诊，但拿不到真实身份。
- **映射表单独存**：脱敏输出**不含**原始 PII；原值↔假名的映射另存 `*_mapping.csv`。⚠️ 该映射表含真实 PII，**必须单独妥善保管或用后销毁，绝不能随脱敏数据一起外发**。
- **默认不脱日期**：日期常是研究变量（随访时间、发病日期），默认保留；需要时加 `--dates`。若要做日期偏移（保留时间间隔但隐藏真实日期），在分析阶段统一平移。

## 何时用
- `data-analysis` / `nature-figure` / `write-paper` 处理**患者级原始数据**前，先跑本技能。
- 投稿的补充材料、公开的数据集，发布前必须脱敏。

## 硬约束与诚实边界
- **本技能是辅助、不是保证**：正则能可靠抓结构化标识（身份证/手机/住院号），但**中文姓名与自由文本里的隐性标识（如"某院长的女儿""住XX小区"）正则难以穷尽**。脚本会明确提示这一点——**脱敏后务必人工复核再对外共享**，尤其是自由文本病历。
- 不改动非 PII 的临床数值（检验值、诊断、用药）——那是分析要用的。
- 涉及公开发布或跨机构共享，提醒用户遵循本机构伦理/数据安全规定与《个人信息保护法》。
