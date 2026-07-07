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
