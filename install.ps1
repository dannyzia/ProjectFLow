# Project Flow — one-command installer for Windows (PowerShell)
# Usage: irm https://projectflow.digital-papyrus.xyz/install.ps1 | iex

$ErrorActionPreference = "Stop"
$REPO = "git+https://github.com/dannyzia/ProjectFLow.git"
$VENV_DIR = "$env:USERPROFILE\.project-flow-env"

Write-Host ""
Write-Host "  Project Flow - Installer" -ForegroundColor Cyan
Write-Host "  ------------------------" -ForegroundColor Cyan
Write-Host ""

# ── 1. Require Python 3.11+ (but exclude 3.14 on Windows due to venv bug) ──
$python = $null
$pyVerInfo = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $ver = & $candidate -c "import sys; print(sys.version_info >= (3,11) and sys.version_info < (3,14))" 2>$null
        if ($ver -eq "True") {
            $python = $candidate
            $pyVerInfo = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Host "  Python 3.11-3.13 is required." -ForegroundColor Red
    Write-Host "  Python 3.14 is not supported on Windows due to venv bugs." -ForegroundColor Yellow
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Make sure to check 'Add Python to PATH' during install." -ForegroundColor Yellow
    exit 1
}

Write-Host "  Using Python $pyVerInfo" -ForegroundColor Green

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
