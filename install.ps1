<#
  One-command install for the sci-skill suite (Windows).
  - Builds a project-root .venv and installs all Python deps.
  - Optional: -WithPdf also installs pandoc + xelatex (needed only by render-pdf-doc).
  ASCII-only on purpose: PowerShell 5.1 reads BOM-less UTF-8 scripts as ANSI and would garble non-ASCII.

  Usage:
    powershell -ExecutionPolicy Bypass -File install.ps1
    powershell -ExecutionPolicy Bypass -File install.ps1 -WithPdf
#>
param([switch] $WithPdf)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$Py = Join-Path $Venv "Scripts\python.exe"
$Req = Join-Path $Root "scripts\requirements-skills.txt"

Write-Host "== sci-skill install (Windows) ==" -ForegroundColor Cyan

# 1) venv
if (-not (Test-Path $Py)) {
  $base = $null
  foreach ($c in @("py", "python", "python3")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $base = $cmd.Source; break }
  }
  if (-not $base) { throw "Python not found. Install Python 3.10+ first: winget install -e --id Python.Python.3.12" }
  Write-Host "Creating .venv ..." -ForegroundColor Cyan
  if ($base -match "py\.exe$") { & $base -3 -m venv $Venv } else { & $base -m venv $Venv }
}
& $Py --version

# 2) deps
Write-Host "Installing Python deps (first run ~3-8 min) ..." -ForegroundColor Cyan
& $Py -m pip install -U pip -q
& $Py -m pip install -r $Req

# 3) optional PDF toolchain
if ($WithPdf) {
  Write-Host "Installing pandoc + MiKTeX (for render-pdf-doc) ..." -ForegroundColor Cyan
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    if (-not (Get-Command pandoc -ErrorAction SilentlyContinue)) { winget install --id JohnMacFarlane.Pandoc --scope user --silent --accept-source-agreements --accept-package-agreements }
    if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) { winget install --id MiKTeX.MiKTeX --scope user --silent --accept-source-agreements --accept-package-agreements }
  } else {
    Write-Host "  ! winget missing; install pandoc + MiKTeX manually for PDF output." -ForegroundColor Yellow
  }
}

# 4) validate
& $Py (Join-Path $Root "scripts\validate_skills.py")

Write-Host "`nDone." -ForegroundColor Green
Write-Host "Interpreter: $Py"
Write-Host "Skills dir : $(Join-Path $Root 'skills')"
Write-Host "Load them: point your agent framework at the skills\ folder (see README)."
if (-not $WithPdf) { Write-Host "PDF (render-pdf-doc)? re-run with -WithPdf." -ForegroundColor DarkGray }
