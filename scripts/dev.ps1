#!/usr/bin/env pwsh
# AURA Development Startup Script
# Starts both the FastAPI backend and the Vite dev server.
# Run from the AURA root directory: .\scripts\dev.ps1

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$DesktopDir = Join-Path $Root "desktop"

Write-Host ""
Write-Host "  █████╗ ██╗   ██╗██████╗  █████╗" -ForegroundColor Blue
Write-Host " ██╔══██╗██║   ██║██╔══██╗██╔══██╗" -ForegroundColor Cyan
Write-Host " ███████║██║   ██║██████╔╝███████║" -ForegroundColor Blue
Write-Host " ██╔══██║██║   ██║██╔══██╗██╔══██║" -ForegroundColor Cyan
Write-Host " ██║  ██║╚██████╔╝██║  ██║██║  ██║" -ForegroundColor Blue
Write-Host " ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  AURA Development Environment" -ForegroundColor White
Write-Host ""

# Check .env
$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Warning ".env not found. Copying from .env.example..."
    Copy-Item (Join-Path $Root ".env.example") $EnvFile
    Write-Host "  → Edit .env and add your AI provider API key before continuing." -ForegroundColor Yellow
    Write-Host ""
}

# Check Python venv
$VenvDir = Join-Path $BackendDir ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "  Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv "$VenvDir"
    & "$VenvDir\Scripts\pip" install -r "$BackendDir\requirements.txt" --quiet
    Write-Host "  ✓ Python environment ready." -ForegroundColor Green
}

if (-not $FrontendOnly) {
    Write-Host "  Starting AURA backend on http://127.0.0.1:8765 ..." -ForegroundColor Cyan
    $BackendJob = Start-Job -ScriptBlock {
        param($dir, $venv)
        & "$venv\Scripts\python" -m uvicorn app.main:app `
            --host 127.0.0.1 `
            --port 8765 `
            --reload `
            --log-level info
    } -ArgumentList $BackendDir, $VenvDir -WorkingDirectory $BackendDir
    Write-Host "  ✓ Backend started (Job ID: $($BackendJob.Id))" -ForegroundColor Green
}

if (-not $BackendOnly) {
    # Check node_modules
    $NodeModules = Join-Path $DesktopDir "node_modules"
    if (-not (Test-Path $NodeModules)) {
        Write-Host "  Installing npm packages..." -ForegroundColor Yellow
        & npm install --prefix $DesktopDir --silent
        Write-Host "  ✓ npm packages installed." -ForegroundColor Green
    }

    Write-Host "  Starting Vite dev server on http://localhost:1420 ..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host "   Open AURA:  Run 'npm run tauri dev' in desktop/" -ForegroundColor White
    Write-Host "   Backend:    http://127.0.0.1:8765/docs" -ForegroundColor White
    Write-Host "  ─────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""

    Push-Location $DesktopDir
    npm run dev
    Pop-Location
}

Write-Host ""
Write-Host "  AURA dev environment stopped." -ForegroundColor Yellow
