#!/usr/bin/env pwsh
# AURA First-Time Setup Script
# Run from the AURA root directory: .\scripts\setup.ps1

$Root = Split-Path -Parent $PSScriptRoot

Write-Host "AURA Setup" -ForegroundColor Cyan
Write-Host "==========" -ForegroundColor Cyan
Write-Host ""

# ── 1. Python version check ───────────────────────────────────────────────────
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    if ($pyVer -match "Python 3\.(\d+)") {
        $minor = [int]$Matches[1]
        if ($minor -lt 12) {
            Write-Warning "Python 3.12+ required. Found: $pyVer"
            Write-Host "Download: https://python.org/downloads" -ForegroundColor Cyan
            exit 1
        }
    }
    Write-Host "  ✓ $pyVer" -ForegroundColor Green
} catch {
    Write-Error "Python not found. Install Python 3.12+ from https://python.org/downloads"
    exit 1
}

# ── 2. Node.js check ──────────────────────────────────────────────────────────
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVer = node --version 2>&1
    Write-Host "  ✓ Node $nodeVer" -ForegroundColor Green
} catch {
    Write-Error "Node.js not found. Install from https://nodejs.org"
    exit 1
}

# ── 3. Rust check ─────────────────────────────────────────────────────────────
Write-Host "Checking Rust (required for Tauri)..." -ForegroundColor Yellow
try {
    $rustVer = rustc --version 2>&1
    Write-Host "  ✓ $rustVer" -ForegroundColor Green
} catch {
    Write-Warning "Rust not found."
    Write-Host "  Install Rust from: https://rustup.rs" -ForegroundColor Cyan
    Write-Host "  After installing, restart your terminal and run this script again." -ForegroundColor Yellow
    Write-Host "  (Backend and frontend can still run without Rust — only Tauri build requires it)" -ForegroundColor Gray
}

# ── 4. .env file ──────────────────────────────────────────────────────────────
$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $Root ".env.example") $EnvFile
    Write-Host "  ✓ .env created from template. Edit it to add your API keys." -ForegroundColor Green
} else {
    Write-Host "  ✓ .env exists." -ForegroundColor Green
}

# ── 5. Python venv ────────────────────────────────────────────────────────────
$BackendDir = Join-Path $Root "backend"
$VenvDir = Join-Path $BackendDir ".venv"
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
python -m venv "$VenvDir"
& "$VenvDir\Scripts\pip" install --upgrade pip --quiet
& "$VenvDir\Scripts\pip" install -r "$BackendDir\requirements.txt"
Write-Host "  ✓ Python environment ready." -ForegroundColor Green

# ── 6. npm install ────────────────────────────────────────────────────────────
$DesktopDir = Join-Path $Root "desktop"
Write-Host "Installing npm packages..." -ForegroundColor Yellow
npm install --prefix $DesktopDir
Write-Host "  ✓ npm packages installed." -ForegroundColor Green

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  AURA setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "  1. Edit .env and add your AI provider API key" -ForegroundColor White
Write-Host "  2. Start the backend:" -ForegroundColor White
Write-Host "     cd backend" -ForegroundColor Cyan
Write-Host "     .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload" -ForegroundColor Cyan
Write-Host "  3. Start the frontend (in a second terminal):" -ForegroundColor White
Write-Host "     cd desktop && npm run dev  (browser only)" -ForegroundColor Cyan
Write-Host "     cd desktop && npm run tauri dev  (Tauri window, requires Rust)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
