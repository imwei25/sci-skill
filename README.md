# sci-skill — 科研医学 Agent 技能套件

覆盖「调研 → 选题 → 标书 → 综述 → 文献 → 深研 → 分析 → 作图 → 去 AI 味 → 排版 → 评审 → 查假引用」全链路的 **14 个 Agent 技能**（SKILL.md 格式，跨框架通用：OpenCode / OpenClaw / WorkBuddy / Claude Code 等）。Python 统一走**项目根 `.venv`**，不写死任何机器路径，`git clone` 到任意电脑即可用。

## 一键安装

```powershell
# Windows
git clone https://github.com/imwei25/sci-skill && cd sci-skill
powershell -ExecutionPolicy Bypass -File install.ps1          # 加 -WithPdf 连 pandoc/xelatex 一起装
```
```bash
# Linux / macOS
git clone https://github.com/imwei25/sci-skill && cd sci-skill
bash install.sh                                               # 加 --with-pdf 连 pandoc/xelatex 一起装
```

安装脚本：在仓库根建 `.venv` → 装 `scripts/requirements-skills.txt` 全部依赖 → 校验所有 SKILL.md（无 BOM、frontmatter 合法）。也可以让 agent 直接跑仓库里的 **`env-setup`** 技能完成同样的事。

## 怎么加载进各框架

技能都在 `skills/`，每个是一个 `<name>/SKILL.md` 目录。

- **OpenCode**：把 `skills/*` 放进项目的 `.opencode/skills/`（或就在本仓库根 `opencode`）。
- **OpenClaw**：在配置 `skills.load.extraDirs` 里加上本仓库的 `skills/` 路径（它会自动发现，最深 6 层）。
- **WorkBuddy**：把 `skills/*` 复制到它的技能根（通常 `~/.workbuddy/skills-marketplace/skills/`，以实际为准）。
- **Claude Code**：把 `skills/*` 放进 `.claude/skills/`。

加载后，技能靠**对话内容匹配 description 触发**（不是斜杠命令）。例：「核对这几个 DOI 是不是真的」→ `reference-check`；「画一张 Nature 级森林图」→ `nature-figure`。

## 解释器约定

各技能调 Python 一律用项目根 `.venv`：
- Windows：`.venv/Scripts/python.exe`
- Linux / macOS：`.venv/bin/python`

没有 `.venv` 时，先跑 `install.*` 或让 agent 跑 `env-setup` 技能。

## 17 个技能

| 方向 | 技能 | 说明 |
|---|---|---|
| 环境自举 | `env-setup` | 查 Python→建 `.venv`→装依赖+pandoc；换机器先跑它 |
| 数据脱敏 | `deidentify` | 上传患者数据前去标识化（身份证/手机/住院号/姓名…） |
| 调研 | `research-scan` | 领域现状/趋势/空白 → 调研简报 |
| 选题 | `topic-selection` | 找空白、提假设、多棱镜打分（可选对抗式研究） |
| 写标书 | `grant-proposal` | 国自然 / NIH 结构 + 经费预算，起草与润色 |
| 写论文 | `write-paper` | 原创研究论文 IMRaD 全流程 + 投稿信 + 审稿回复 |
| 综述 | `literature-review` | 多路检索建证据表 → 有引用的综述 |
| 文献检索 | `search-lit` ᵛ | PubMed + Europe PMC（国内可达），API 核实，出 BibTeX |
| 文献下载 | `fulltext-retrieval` ᵛ | 按 DOI 从 OA 源(Unpaywall/PMC/OpenAlex) 下全文 PDF |
| 深度研究 | `deep-research` | 多源检索 + 交叉核实 + 带引用报告 |
| 数据分析 | `data-analysis` | pandas/scipy/statsmodels + 医学统计护栏 |
| 作图 | `nature-figure` ᵛ | Nature 级图工作流，matplotlib/seaborn，SVG/PDF/TIFF |
| 去 AI 味 | `humanize-academic` | 去机器腔（中英文）、数字/引用不变量校验 |
| 期刊排版(PDF) | `render-pdf-doc` ᵛ | Markdown→出版级 PDF（pandoc+xelatex，中文自动字体） |
| 投稿排版(Word) | `render-docx` | Markdown→Word .docx（pandoc，医学期刊多要 Word） |
| 论文/标书评审 | `peer-review` | 逐节剖析 + 报告规范(CONSORT/PRISMA…) + 审稿意见 |
| 文献真实性核查 | `reference-check` | 对 Crossref/Europe PMC 查假引用（不存在/张冠李戴/虚构） |

`ᵛ` = 直接引入的现成开源技能（vendored），来源与许可见 [THIRD_PARTY_SKILLS.md](THIRD_PARTY_SKILLS.md)；其余为适配自研。改进历史见 [docs/improvement-log.md](docs/improvement-log.md)。

## 实测注意

- **`render-pdf-doc` 排中文**要传 `--cjk-font "Microsoft YaHei"`（服务器 `Noto Sans CJK SC`），否则汉字漏字；MiKTeX 首次渲染先 `miktex packages update`。需先 `install.* -WithPdf/--with-pdf` 装 pandoc+xelatex。
- **`search-lit` 走 NCBI PubMed**，中国大陆网络常被墙；国内改用 `fulltext-retrieval`/`reference-check`（走 Europe PMC/Crossref，可达）。
- **`fulltext-retrieval --email`** 必须填真实邮箱（Unpaywall 拒 example.com）。

## 许可

自研技能可自由使用。vendored 技能保留上游许可（Apache-2.0 / MIT），全文见 [`licenses/`](licenses/)，改动说明见 [THIRD_PARTY_SKILLS.md](THIRD_PARTY_SKILLS.md)。
