# sci-skill 改进日志

> 本文档记录 2026-07 全面审查后的逐批修复与功能补齐。审查方法：主会话通读全部 SKILL.md 与脚本后，5 个并行调研 agent 分别完成文献链代码审查（含实测）、图表排版链审查、写作思考链审查（含领域事实联网核查）、环境与主控方案调研、功能缺口生态调研。每批修复由独立验证 agent 复核后合入。

## 修复批次

### F1 · 全仓路径修复（已完成）

**问题**
1. 全仓 20+ 处 Python 解释器路径写成 `.venv\Scripts\python.exe`（反斜杠）。在 Git Bash / POSIX shell 下反斜杠被转义吞掉，变成 `.venvScriptspython.exe`，运行必失败——而 Claude Code for Windows、OpenCode 等框架的 Bash 工具正是走 Git Bash。
2. 5 处文档/报错信息指向不存在的 `scripts/setup.ps1` / `scripts/setup.sh`（实际安装脚本是仓库根的 `install.ps1` / `install.sh`）。
3. 各技能只写 Windows 解释器路径，无 Linux/macOS 分支。
4. 陈旧引用：`requirements-skills.txt` 注释里的旧技能名 `literature-download`/`journal-formatting`（已改名 `fulltext-retrieval`/`render-pdf-doc`）；`THIRD_PARTY_SKILLS.md` 引用不存在的 `deploy/Dockerfile`。

**修复**
- 全仓 `.venv\Scripts\python.exe` → `.venv/Scripts/python.exe`（正斜杠，Windows Python 同样接受，bash 与 PowerShell 通用）。
- 各技能「Python 环境」代码块统一为双行：Windows `.venv/Scripts/python.exe` + Linux/macOS `.venv/bin/python`。
- `env-setup/SKILL.md`、`search.py`、`verify_refs.py`、`requirements-skills.txt` 的安装脚本引用改为仓库根 `install.ps1` / `install.sh`。
- 清理旧技能名与 `deploy/Dockerfile` 死引用。

**影响文件**：README.md、THIRD_PARTY_SKILLS.md、scripts/requirements-skills.txt、skills/*/SKILL.md（13 个）、skills/literature-review/search.py、skills/reference-check/verify_refs.py。

**验证**：独立验证 agent 复核后发现 4 个 vendored 技能顶部引用块漏补 Linux 行，已在 F2 批次补齐。

### F2 · 一键安装脚本加固（已完成）

**问题**（install.ps1 / install.sh）
1. **静默假成功**：PowerShell 5.1 中 `$ErrorActionPreference="Stop"` 对原生 exe 的非零退出码不生效，install.ps1 全程不查 `$LASTEXITCODE`——pip/winget/校验失败后照样绿字打印 "Done."。
2. 无 pip 镜像 fallback：大陆直连 pypi.org 常超时，脚本不重试不换源。
3. 不排除 Windows Store 假 Python（WindowsApps 执行别名），可能建出坏 venv。
4. 无 Python 3.10+ 版本门槛；env-setup 承诺"没有就装"但脚本只 throw。
5. winget 装 pandoc/MiKTeX 后不刷新 PATH，同会话不可用；MiKTeX 未开 AutoInstall，首次非交互渲染会卡在装宏包询问。
6. 装完不帮用户把 skills 装进任何框架目录。

**修复**（两个脚本同步）
- 每个关键步骤记录 OK/FAIL，结尾输出清单；有失败绝不打印 "Done."，退出码 1。
- pip 加 `--timeout 30 --retries 2`，失败自动切清华镜像重试；成功后把镜像写入 `.venv/pip.ini`（Windows）/ `.venv/pip.conf`（Linux），后续 pip 全部走对的源。
- Python 探测跳过 WindowsApps 假别名；强制 3.10+；缺 Python 时 Windows 自动 `winget install Python.3.12`（失败回退人话提示）。
- `-WithPdf`：winget 后从注册表刷新 PATH + 探测 MiKTeX bin 目录 + `initexmf --set-config-value "[MPM]AutoInstall=1"` + `miktex packages update`，并验证 pandoc/xelatex 落位。
- 新增 `-LinkClaude` / `--link-claude`：把 skills/* 复制进 `~/.claude/skills`（Claude Code 即插即用；其他框架仍按 README 指路，保持跨框架中立）。
- requirements 移除已弃更的 `pymed`（2019 年后无维护，且 NCBI 大陆不可达）。

### F3 · validate_skills.py 升级为真自检（已完成）

**问题**：旧校验器逐行按冒号切分、不懂 YAML 折叠块——`description: >-` 被解析成字符串 `">-"` 也算通过；不校验官方 Agent Skills 规范的 name 规则与 description ≤1024 上限（nature-figure 实测 1501 字符超标而旧校验器放行）；不警告非规范 frontmatter 字段；完全不检查运行环境，却被安装脚本当"装机自检"用。

**修复**：重写解析器支持折叠块/块标量；校验 name（≤64、a-z0-9-、不以连字符开头结尾、与目录一致）与 description（非空、≤1024，超限报错）；非规范字段（triggers/tools/model/version/author）警告；新增 `--env` 模式——检查 Python≥3.10、按能力组 import 全部关键依赖、探测 pandoc/xelatex（含 MiKTeX 默认安装位置），按"数据分析/文献检索/全文下载/文档生成/PDF 排版"输出人话结论。安装脚本收尾改调 `validate_skills.py --env`。

**已知遗留**：校验器现在会如实报出 nature-figure description 超长错误，该问题在 F6 批次修复。

**验证**：独立 agent 逐行审查 + 实测两模式运行，结论 PASS；提了一个非阻断建议（install.ps1 后段 cmdlet 缺 try/catch，异常会裸崩而非走汇总）——已在 F4 顺带加固。

### F4 · 文献链代码修复（已完成，均经实测）

1. **引号注入 / 静默失败**（`search-lit/references/pubmed_eutils.sh:52`）：query 曾通过 shell 拼进 `python3 -c` 字符串，含单引号的检索式静默失败、含 `$()` 可命令注入。改用 `curl -G --data-urlencode`，query 永远是数据不是代码。实测：含单引号检索式正常返回、注入串被当纯文本。
2. **Europe PMC 回退**（同脚本）：新增 `epmc_search` / `epmc_cite_lookup` / `epmc_fetch` 三个走 ebi.ac.uk 的子命令（大陆可达），SKILL.md 把「无 MCP → 先 Europe PMC，NCBI 仅境外/代理时用」写成明确路由。`_curl` 捕获 curl 退出码、输出结构化错误 JSON，不再让 `set -e` 中途裸退（去掉 `-e`）。实测 EPMC 检索命中真实文献。
3. **假阳性根治**（`reference-check/verify_refs.py:81`）：`resolve_pmid` 去掉 `AND SRC:MED`——该过滤会把真实但未进 MEDLINE 的 PMID（在版/仅 PMC/预印本）误判为 FABRICATED。实测真实 PMID 现在正确判 OK。另加：DOI 路径 Crossref 失败/404 时回退 Europe PMC；标题查询转义引号；新增首作者姓氏+年份交叉核验（抓「DOI 真但张冠李戴」，OK→CHECK）；UA 邮箱可用 `CONTACT_EMAIL` 覆盖。
4. **PMC 分支国内可用**（`fulltext-retrieval/fetch_oa.py`）：DOI/PMID→PMCID 改为「先 Europe PMC，后 NCBI idconv」，NCBI 被墙不再拖垮整个 PMC 路径；idconv 补 `tool`/`email` 参数。
5. **标题核验换 PyMuPDF**（同文件 `extract_pdf_text`）：从依赖外部 poppler `pdftotext`（Windows 默认没有）改为优先用已装的 `fitz`，poppler 仅作次选——Windows 上「防下错 PDF」护栏终于生效。
6. **报告计数口径统一**（同文件 `build_report`）：`skip`（已存在文件）从 `retrieved` 拆出，新增 `already_present` / `available` 字段，重复跑时报告与摘要不再打架。
7. **snowball 限流**（`search-lit/references/snowball.py`）：`_http_get_json` 加 429 指数退避 + `Retry-After` + `S2_API_KEY` 支持，退避耗尽抛 RuntimeError（不再把限流静默当「0 新增候选」）；实时调用间 sleep 1s。
8. **literature-review 韧性**（`search.py`）：裸 `requests.get` 换成带 429/503 退避的 `_get`；排序键改数值型（原 `str(year)` 字符串比较语义脏）。实测检索正常。
9. **parse_pubmed DOI**：esummary 表补 DOI 列（原算出不输出）；efetch/bibtex 的 DOI 抽取加 `PubmedData/ArticleIdList` 兜底（原只取 ELocationID 会漏，导致 verified_by 降级）。

**影响文件**：skills/search-lit/references/{pubmed_eutils.sh, snowball.py, parse_pubmed.py}、skills/search-lit/SKILL.md、skills/reference-check/verify_refs.py、skills/fulltext-retrieval/fetch_oa.py、skills/literature-review/search.py。

**验证**：独立 agent 逐行审查+实测，结论基本 PASS，抓出 1 处关键缺陷——`fetch_oa.py:657` 标题核验门槛只认 `pdftotext`、没跟着改认 `fitz`，导致 PyMuPDF 改动在目标环境（仅装 pymupdf）下不生效。已修：门槛改为「fitz 可导入 或 pdftotext 存在」。另修 snowball 429 耗尽路径的死代码（RuntimeError 现可达）。

### F5 · 全仓死引用清理（已完成）

vendored 技能大量引用本仓库不存在的东西，会让 agent 照着撞空或调不存在的技能。清理约 60 处：

- **路径/token 级**（sed 批量）：`${CLAUDE_SKILL_DIR}/references/` → `skills/search-lit/references/`；`references/library.bib` → `outputs/refs.bib`；`${MEDSCI_SKILLS_ROOT:-...}/...fetch_oa.py` → `skills/fulltext-retrieval/fetch_oa.py`。
- **跨仓库幽灵技能** → 本仓库真实技能：`/verify-refs` → reference-check；`/analyze-stats`/`/check-reporting` → data-analysis/peer-review；`/make-figures`/`/present-paper` → nature-figure；`/manage-refs` → render-pdf-doc/reference-check；`/lit-sync`/`/write-paper`/`/self-review` 及其"SSOT refs.bib"契约、`manuscript/_src/refs.bib`、`docs/artifact_contract.md`、`snowball_challenge/`、`fetch_oa_report_challenge/`、`~/.claude/rules/*.md` → 删除或改为自包含说明。
- **skill.yml**：search-lit / fulltext-retrieval / render-pdf-doc 三个 skill.yml 的 when_NOT_to_use / downstream_consumers / forbidden_actions / validation_commands 全部改指本仓库真实技能，删掉指向不存在夹具的 validation_commands。
- snowball.py 删掉对 `manuscript/_src/refs.bib` 的硬拒写守卫（该路径概念已不存在），默认输出改 `outputs/refs.bib`。

清理后全仓 dead-ref sweep：0 处活引用（仅剩历史日志 docs/ 里作为"修复前问题"的描述性文字）。

### F6 · 图表排版链修复（已完成）

**render-pdf-doc（中文漏字三连 + redact 空实现）**
1. **中文默认字体**（`scripts/render_pdf.sh`）：新增按内容探测——扫描稿件含汉字→默认 Microsoft YaHei（Windows）/ Noto Sans CJK SC（Linux）/ PingFang SC（macOS）；含韩文→Malgun / Noto CJK KR / Apple SD Gothic Neo。之前 Windows 无条件用韩文 Malgun Gothic，简体汉字被 xelatex 静默丢弃。实测探测逻辑：中文→han、韩文→hangul。
2. **`-V` 不再覆盖 frontmatter**（同脚本）：只有当用户在 CLI 传了 `--font`/`--cjk-font`，或 frontmatter 未定义该字体键时，才注入 `-V mainfont/CJKmainfont`；frontmatter 已写 `CJKmainfont` 时脚本让它生效。实测 grep 能正确识别 frontmatter 字体键。
3. **`redact_internal: true` 落地**（同脚本）：之前是文档承诺、脚本零实现。现在渲染前扫描并剔除修订史/版本号/PI 署名行（中英韩关键词）。实测：3 行内部信息被剔除、正文保留。
4. **check_deps.sh**：Windows 改查 `msyh.ttc`（中文，主）+ Malgun（韩文，附）；Linux 改查 Noto CJK SC/KR。
5. SKILL.md 顶部与正文全部改为"字体按内容自动探测、无需手动 `--cjk-font`、frontmatter 优先"，Core Principle 2/3 同步。

**nature-figure（description 超长 + 后端矛盾 + assets 死链）**
6. **description 1501→849 字符**（<1024 上限）：精简冗余触发词、保留中文触发词并补森林图/生存曲线/KM/火山图；validator 现在通过。
7. **后端矛盾统一**：顶部明确"本仓库策略覆盖 vendored 正文的'必须问一次'——默认直接 Python，不为选后端停下来问，除非用户明确要 R"，消除顶部 vs 正文/manifest 的冲突指令。
8. **assets 死链**：demos.md、README、manifest.yaml 都加"assets 图库未随本仓库分发、勿 Read `../assets/...`"的醒目说明；README 顶部说明裂图属预期。

**验证方式说明**：本机未装 pandoc/xelatex，PDF 全链路渲染无法本地跑；字体探测、frontmatter 识别、redact 过滤三段核心逻辑已单元测试通过，完整渲染留待有排版工具链的环境或静态审查。

**验证 + 修复**：独立 agent 审查 8/9 项 PASS，抓出 1 处真实缺陷——redact_internal 的正则 `version\s*\d` 会匹配正文"we used version 2.1 of Bowtie"并整行误删，违背"保留正文"承诺。已修：正则收紧为**仅匹配元数据行**（行首 `Label:／Label：` 形式，含 markdown 标题/列表前缀），并对 `## Change History` 标题**连同其小节正文一起删除**（遇到下一个标题即停）。实测：正文含"version 2.1"的科研句子保留，Version:/负责人：元数据行与整个 Change History 小节删除。

### F7 · 内容与领域正确性批（已完成）

**grant-proposal（会直接害用户的事实错误）**
- NSFC 预算：旧九科目 → **2022 改革后三大类（设备费/业务费/劳务费）**，间接费单列。
- NIH modular：错误的"$250K/模块" → **$25K/模块、年直接费 ≤$250K 才可用、最多 10 模块**；R21 上限写实。
- 人才项目：杰青/优青/青基 → **青年科学基金 A/B/C 类**（包干不编明细）。
- 新增顶部**时效护栏**（政策以当年指南为准）+ **AI 合规红线**（NSFC 禁 AI 生成申请书、NIH NOT-OD-25-132、产出定位为草稿须实质改写）。
- NSFC 结构补形式审查件（≤400 字摘要、科学问题属性四选一、申请代码、5 篇代表作、瘦身提质说明）；NIH 补 **2025 简化评审三因素**组织法。
- 自查清单从一行扩为 10 项可勾选清单。

**peer-review**
- NIH 评审：废止的五项 → **2025 简化三因素框架**（Importance / Rigor & Feasibility / Expertise & Resources）；国自然补科学问题属性匹配 + 综合评价 ABCD。
- 新增**保密与合规**段（不得用于正式盲审，NIH NOT-OD-23-149 / NSFC 禁 AI）。
- 报告规范从 5 个扩为 12+ 类对照表（补 TRIPOD+AI、SPIRIT、CHEERS 2022、CARE、COREQ、MOOSE、SQUIRE、CLAIM、DECIDE-AI 等，附版本年份 + EQUATOR 兜底）。
- 补机械/统计可核对项（数字一致、注册号、伦理号）；结论加四档 + 分维打分；意见改**四元组**（位置|问题|依据|改法）；PDF 稿接 pdf_to_md.py；两种模式（自查/模拟审稿）。

**humanize-academic（中文去 AI 味——市场空白）**
- 新增**中文 AI 腔清单 9 条**（机械三段式、空转套话、大词口号、四字堆砌、"进行/加以"冗余、过度关联词、句段单调、对冲/绝对、标点腔），英文清单从 8 扩为 11（补 AI 高频词、not-X-but-Y、em-dash、保留清单）。
- 新增**保留清单**防误删正当学术用语；两遍改写升级为对照清单终检 + 字数守恒 + 可选声纹校准。
- 新增 `scripts/check_invariants.py`：机械校验改写前后**数字/引用标记/DOI/PMID/术语**集合 diff，把硬约束从声明变检查。

**F7 验证发现并修复的问题**：
- ⚠️ `check_invariants.py` 数字正则用 `\w` 做边界，而 Python `\w` 把汉字算词字符——导致"共45名"这种中文无空格写法里的数字被漏抓（假阴性，篡改数据会被放过）。已修为 ASCII 边界 `(?<![0-9A-Za-z.])...(?![0-9A-Za-z])`。**重测**：中文等价改写通过、中文篡改（45→60/12→18/8%→20%）被逐条揪出。
- grant-proposal 人才项目 A/B/C 类称谓经 **NSFC 官网核实属实**（官网有青年科学基金项目 A/B/C 类各自指南页、B 类启动会新闻），已补充明确映射：A 类=原杰青、B 类=原优青、C 类=原青年基金。（F7 验证 agent 曾据旧知识存疑，联网核实后确认原表述正确。）
- 其余领域事实（NSFC 三大类预算、NIH modular $25K/≤$250K、NIH 2025 简化评审三因素、报告规范对照表、统计护栏）经复核准确、无自相矛盾。

**data-analysis**
- 新增**医学统计方法选择护栏**（正态性→参数/非参、卡方 vs Fisher、多重比较校正、Cox PH 检验、诊断试验指标）+ **报告规范**（效应量+95%CI+精确 p+n）+ PII 脱敏提醒。

**description 消歧**
- research-scan / deep-research / literature-review 三方互撞 → 各加边界句（全貌快扫 / 单问题求证 / 成文综述）。
- data-analysis 加"探索性 vs 投稿级图→nature-figure"边界。search-lit 大陆不可用风险已在 F4 顶部路由说明处理。

### F8 · 写作思考链剩余项（已完成）

- **topic-selection**：第 5 步夸大 reference-check 能力（"确实支持该论断"）——拆成"存在性核验（reference-check 只查真伪）+ 支持性核验（主代理回读摘要/全文自己确认）"，消除它本想防的幻觉；评分矩阵从 4 维扩为 **5 维**（补伦理/合规可行性，可一票否决）+ 打分方向 + 申请人条件匹配 + 1–5 分带证据。
- **deep-research**：删"适配 OpenCode + DeepSeek"改为框架中立；能力检测补"能并发调工具 ≠ 能开子代理，拿不准就串行"；学术取证默认改 Europe PMC（literature-review/search.py）；新增来源分级、检索日志、停止标准、**成稿前反向核查一轮**、速览结论标置信度。
- **research-scan**：默认检索改 Europe PMC；"高被引/关键团队机构"强制走 **OpenAlex（pyalex 已装）** 聚合，查不到标"未核实"，堵住凭记忆报团队名的幻觉；补默认参数（近 5 年、30–50 篇、≤3000 字）。后续按 F8 验证 agent 建议改为：高被引默认用 Europe PMC 的 `citedByCount`（无需 key），OpenAlex 降为需 key 的可选增强。

---

## 二、补充缺口（新增技能，每个经"测试 + 挑刺"两 agent 并行验证后合入）

> 说明：因 GitHub 克隆在本环境不稳、且上游 medsci-skills 的技能带有本仓库刚清理掉的同类死引用生态，**改为自研精简 SKILL.md**——更符合"简单全自动、不折腾环境、跨框架"目标，且不引入陌生依赖。

### G1 · write-paper（原创论文写作 IMRaD）
最大空白（原有综述、标书，无"写原创研究论文"）。纯 prompt，零新依赖，串起检索/分析/作图/查引用/去 AI 味/排版。**两 agent 验证后补齐**：render-docx 前向引用 + pandoc 缺失降级；ICMJE 投稿必备声明（作者贡献/COI/资助/数据可用性/ORCID）；AI 不得署名；CONSORT/PRISMA 流程图硬性产出；讨论引用内容失真警告（reference-check≠支持论断）；数字来源核对；post-hoc power 警示；投稿前自查接 peer-review。

### G2 · render-docx（Word 投稿输出）
医学期刊多要 Word 而非 PDF；pandoc 转 docx，中文比 xelatex 更不易漏字。**两 agent 验证后补齐**：CSL 未内置→改为下载指引（不指幽灵路径）+ 讲清 `--csl` 只对 pandoc `[@key]` 引用生效（本套件默认 `[n]` 文本引用用不上）；讲清中文投稿基本必须配期刊模板；脚本拒绝未知 `-选项`、`--csl`/`--bib` 强制成对、`-o` 去最后一个扩展名；如实列出 track-changes/行号/题注域等当前限制。

### G3 · deidentify（患者数据脱敏）
安全/伦理护栏，纯 stdlib。一致性假名化 + 映射表分离。**两 agent 验证后补齐**（脱敏工具漏一个就是事故）：手机号容忍 `+86`/分隔符（原漏 `138-1234-5678`）；银行卡加 **Luhn 校验**（原 16-19 位裸匹配误伤科研长数字）；**拒绝 .xlsx 等二进制**（原静默当文本读产出乱码、假装"无 PII"）；GBK/gb18030 编码回退（原 utf-8 硬编码对国内 HIS 导出乱码）；手机/座机假名前缀分开（原都叫 TEL 撞名）；病案标签放宽（病历号/档案号 + "为/是"连接词）；疑似标识列未指定时告警；文档：**假名化≠匿名化**的个保法区别、链接攻击风险、不覆盖类型（住址等）、自由文本姓名盲区提到最醒目处。

### G4 · clinical-stats（Table 1 + 样本量）
临床最高频两件事，纯用已装 pandas/scipy/statsmodels（无新依赖）。**两 agent（含统计学挑刺）验证后补齐关键统计错误**：
- **样本量 two-props 换算法**：原用 arcsine/Cohen's h + t-power，在比例接近 0/1 时系统性低估**最高达 -19%**（罕见事件/高有效率场景 underpower）。改为**标准正态近似（Fleiss）公式**——实测 .05/.01 从错误的 251 修正为正确的 285/组；.30/.15 精确到 121；极端比例加警告。
- **Table 1 正态性判断**：原对**整列合并**做 Shapiro，组间均值差异大时双峰→误判非正态→错切非参数。改为**逐组分别判正态**，各组都正态才用 t——实测组内正态(p=0.8/0.64)、合并非正态(p=6.5e-13)的数据现在正确用 t/Welch。
- 样本量边界**友好报错**（HR=1、p1=p2、power≥1、dropout≥1、sd≤0 等原抛裸异常）；Table1 空文件/读取失败友好报错、单组不再显示假检验名、连续/分类**指定用反时告警**、RxC 期望<5 标 `卡方⚠期望<5`。
- 文档诚实边界：只支持双侧优效（非劣效勿套）、多组只给总体 p（事后另做）、Freedman/正态近似局限、SMD 建议。
- 修 write-paper/data-analysis 的交叉引用：样本量/Table1 指向 clinical-stats（原 write-paper 误指 data-analysis，而后者并不做样本量）。

---

## 三、总结

- **技能数**：14 → **18**（新增 write-paper、render-docx、deidentify、clinical-stats）。
- **提交**：约 20 个原子提交，每个 fix 批次或新技能都经独立 Sonnet agent 验证（bug 批 1 个验证 agent；新技能 1 测试 + 1 挑刺，最多并行 2 个）。
- **跨平台/一键**：全程保持——正斜杠路径 bash/PowerShell 通用；install.ps1/sh 自动装 Python+镜像 fallback+成败汇报；新技能全走 `.venv` 或已装 pandoc，无陌生依赖；4 个框架（Claude Code/OpenCode/OpenClaw/WorkBuddy）加载方式不变。
- **未做/受限**：GB/T 7714 CSL 因本环境访问 GitHub/Gitee 拉取失败，未内置文件，改为在 render-docx 给出下载指引（citation-style-language/styles、zotero-chinese/styles、Gitee 镜像）。

---

## 四、主控层（跨框架核心三件套，已完成）

> 只做跨框架核心（markdown + 目录约定 + stdlib 脚本），**不做** Claude Code 专属增强层（plugin/hooks/subagent）——按用户要求。

### M1 · sci-pilot 路由技能（`skills/sci-pilot/`）
新增全流程总控技能：判断意图→选流水线→逐步调用各单项技能→维护项目状态。SKILL.md 只放决策逻辑（意图→流水线映射 + 交互协议"何时自动往下/何时停下问用户"），流水线细节放 references/（review/grant/paper/research 四条 + workspace-protocol）。description 面向"完整目标"抢触发，末尾划界"单步任务直接用单项技能"。无子代理框架里退化为顺序编排。

### M2 · AGENTS.md + CLAUDE.md（仓库根常驻索引）
约 40 行路由表 + 消歧规则 + `.venv`/中国网络/工作区约定。OpenCode 读 AGENTS.md、Claude Code 读 CLAUDE.md，两文件同内容。常驻上下文=路由表永远在场，不依赖触发。

### M3 · workspace/manifest 状态约定（`skills/sci-pilot/scripts/workspace.py`）
每课题一个 `workspace/<slug>/` + `manifest.json`（唯一状态真源），纯 stdlib 脚本管理：`init`（建骨架，按流水线预置步骤与产物路径）/ `path`（给各技能的 `--out` 路径）/ `set`（更新状态并自动推进 `next`）/ `show` / `list`。**技能间只传文件路径不传大块内容**；用户说"继续上次那个课题"→ `list`→`show`→从 `next` 续跑。产物落进课题工作区、不再混写 `outputs/` 互相覆盖；单独用某技能时回退 `outputs/`（向后兼容）。`workspace/` 已 gitignore。实测：paper 流水线 9 步初始化、进度推进、续跑流程全通。

### 未做（增强层，按用户要求跳过）
`.claude-plugin` 打包、SessionStart hook 环境探针、lit-searcher 检索子代理——这些绑定 Claude Code，作为可选增强留待需要时再加。
