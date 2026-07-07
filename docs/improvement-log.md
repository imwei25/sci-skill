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
