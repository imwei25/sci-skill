# sci-skill 导航（给 agent 的常驻索引）

医学科研 Agent 技能套件，19 个技能在 `skills/`。**完整科研目标**（写综述/论文/标书、深度研究、"继续上次那个课题"）→ 先用 **`sci-pilot`** 技能，它会选流水线、逐步调用下列单项技能、在 `workspace/` 维护状态。**单步明确任务**直接用下表对应技能，不必经 sci-pilot。

## 技能路由 + 消歧
| 需求 | 用哪个 | 别用 |
|---|---|---|
| 上传患者数据前去标识化 | `deidentify` | — |
| 领域全貌快扫（简报） | `research-scan` | 不是成文综述→literature-review；不是单问题→deep-research |
| 单个具体问题跨源求证 | `deep-research` | 不是领域全貌→research-scan |
| 成文有引用的综述 | `literature-review` | 只要清单→search-lit；只摸底→research-scan |
| 文献清单 / BibTeX | `search-lit`（国内走 Europe PMC epmc_*） | — |
| 按 DOI 下全文 PDF | `fulltext-retrieval` | — |
| 查假引用（真伪，非"是否支持论断"） | `reference-check` | — |
| 找空白、提假设、选题打分 | `topic-selection` | — |
| 写国自然/NIH 标书 | `grant-proposal` | 评审→peer-review |
| 写原创研究论文 IMRaD | `write-paper` | 综述→literature-review |
| 通用数据分析/建模 | `data-analysis` | Table1/样本量→clinical-stats |
| Table 1 基线表 / 样本量把握度 | `clinical-stats` | — |
| 投稿级图（森林图/KM/火山图） | `nature-figure` | 探索性看数→data-analysis |
| 去 AI 味 / 学术润色（中英文） | `humanize-academic` | — |
| 出版级 PDF | `render-pdf-doc`（中文字体自动） | 要 Word→render-docx |
| Word .docx 投稿版 | `render-docx` | 要 PDF→render-pdf-doc |
| 论文/标书评审、投稿前自查 | `peer-review` | 改/写标书→grant-proposal |
| 建/修复运行环境 | `env-setup` | — |
| 完整科研目标总控 | `sci-pilot` | 单步任务不用它 |

用户只说"排版"没指明格式 → 先问 PDF 还是 Word。

## 约定
- Python 解释器：`.venv/Scripts/python.exe`（Windows）/ `.venv/bin/python`（Linux/macOS），正斜杠 bash/PowerShell 通用。没有 `.venv` 先跑 `env-setup` 或仓库根 `install.ps1`/`install.sh`。
- 中国大陆网络：文献检索/核查默认走 Europe PMC / Crossref / OpenAlex（可达），NCBI 仅境外/代理时用。
- 项目产物写 `workspace/<课题slug>/`（sci-pilot 维护，见其 references/workspace-protocol.md）；单独用某技能时回退仓库根 `outputs/`。
- 患者数据先 `deidentify`；绝不虚构数据/引用/预算/伦理号。

改进历史见 `docs/improvement-log.md`。
