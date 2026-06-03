<#
.SYNOPSIS
    WCAG 2.1 AA Analyzer — uruchamianie aplikacji (Backend + Frontend)

.DESCRIPTION
    Skrypt uruchamia:
    - Backend FastAPI (port 8000)
    - Frontend Vue.js/Vite (port 5173)
    - Otwiera przeglądarkę na localhost:5173

.PARAMETER NoBrowser
    Jeśli podane, nie otwiera przeglądarki

.EXAMPLE
    .\start.ps1                    # Uruchomi z otwarciem przeglądarki
    .\start.ps1 -NoBrowser         # Uruchomi bez przeglądarki
#>

param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND_DIR = Join-Path $ROOT "backend"
$FRONTEND_DIR = Join-Path $ROOT "frontend"

# Zmienne środowiskowe (opcjonalne)
if (-not $env:WCAG_FILES_DIR) {
    $env:WCAG_FILES_DIR = "C:\Users\Dell\Desktop\audyt06"
}
if (-not $env:WCAG_OUTPUT_DIR) {
    $env:WCAG_OUTPUT_DIR = Join-Path $env:WCAG_FILES_DIR "raporty"
}

Write-Host ""
Write-Host "=== WCAG Analyzer ===" -ForegroundColor Green
Write-Host ""
Write-Host "WCAG_FILES_DIR=$($env:WCAG_FILES_DIR)"
Write-Host "WCAG_OUTPUT_DIR=$($env:WCAG_OUTPUT_DIR)"
Write-Host ""

# ============================================================================
# Uruchomienie Backend
# ============================================================================
Write-Host "[Backend] Uruchamianie FastAPI na http://localhost:8000..." -ForegroundColor Yellow
Write-Host ""

$backendScript = @"
cd "$BACKEND_DIR"
& .\venv\Scripts\Activate.ps1
`$env:WCAG_FILES_DIR = "$($env:WCAG_FILES_DIR)"
`$env:WCAG_OUTPUT_DIR = "$($env:WCAG_OUTPUT_DIR)"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"@

$backendProcess = Start-Process pwsh -ArgumentList @("-NoExit", "-Command", $backendScript) -WindowStyle Normal -PassThru
$backendProcess | Rename-Process "WCAG Analyzer — Backend (FastAPI)" -ErrorAction SilentlyContinue

# Czekaj na uruchomienie backend
Start-Sleep -Seconds 3

# ============================================================================
# Uruchomienie Frontend
# ============================================================================
Write-Host "[Frontend] Uruchamianie Vite na http://localhost:5173..." -ForegroundColor Yellow
Write-Host ""

$frontendScript = @"
cd "$FRONTEND_DIR"
npm run dev
"@

$frontendProcess = Start-Process pwsh -ArgumentList @("-NoExit", "-Command", $frontendScript) -WindowStyle Normal -PassThru
$frontendProcess | Rename-Process "WCAG Analyzer — Frontend (Vite)" -ErrorAction SilentlyContinue

# Czekaj na uruchomienie frontend
Start-Sleep -Seconds 2

# ============================================================================
# Otwórz przeglądarkę
# ============================================================================
if ($NoBrowser) {
    Write-Host "[Info] Aplikacja uruchomiona bez otwierania przeglądarki." -ForegroundColor Cyan
} else {
    Write-Host "[Browser] Otwieranie http://localhost:5173..." -ForegroundColor Cyan
    Start-Process "http://localhost:5173"
}

Write-Host ""
Write-Host "[OK] Aplikacja jest uruchomiona!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:5173"
Write-Host "  Backend:   http://localhost:8000"
Write-Host "  API Docs:  http://localhost:8000/docs"
Write-Host ""
Write-Host "Aby zatrzymać aplikację, zamknij oba okna terminala."
Write-Host ""

# Czekaj na procesy (aby okno nie zamknęło się)
Wait-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
Wait-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
