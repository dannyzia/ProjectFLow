# Project Flow — one-command installer for Windows (PowerShell)
# Usage: irm https://projectflow.digital-papyrus.xyz/install.ps1 | iex

$ErrorActionPreference = "Stop"
$REPO = "git+https://github.com/dannyzia/ProjectFLow.git"
$VENV_DIR = "$env:USERPROFILE\.project-flow-env"

Write-Host ""
Write-Host "  Project Flow - Installer" -ForegroundColor Cyan
Write-Host "  ------------------------" -ForegroundColor Cyan
Write-Host ""

# ── 1. Require Python 3.11+ ──────────────────────────────────────────────────
$python = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $ver = & $candidate -c "import sys; print(sys.version_info >= (3,11))" 2>$null
        if ($ver -eq "True") { $python = $candidate; break }
    } catch {}
}

if (-not $python) {
    Write-Host "  Python 3.11+ is required." -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Make sure to check 'Add Python to PATH' during install." -ForegroundColor Yellow
    exit 1
}

$pyVer = & $python --version
Write-Host "  Using $pyVer" -ForegroundColor Green

# ── 2. Create venv ───────────────────────────────────────────────────────────
Write-Host "  Installing project-flow into $VENV_DIR ..." -ForegroundColor Green
& $python -m venv $VENV_DIR
& "$VENV_DIR\Scripts\python.exe" -m pip install -q --no-warn-script-location --disable-pip-version-check $REPO

# ── 3. Add to user PATH ───────────────────────────────────────────────────────
$BinPath = "$VENV_DIR\Scripts"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinPath", "User")
}
$env:Path = "$env:Path;$BinPath"

# ── 4. Verify ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  OK  project-flow installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Starting project-flow serve ..." -ForegroundColor White
Write-Host ""

& "$VENV_DIR\Scripts\project-flow.exe" serve
