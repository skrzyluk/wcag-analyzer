@echo off
REM ============================================================================
REM WCAG 2.1 AA Analyzer — Uruchamianie aplikacji (Backend + Frontend)
REM ============================================================================
REM
REM Skrypt uruchamia:
REM   - Backend FastAPI (port 8000)
REM   - Frontend Vue.js/Vite (port 5173)
REM   - Otwiera przeglądarkę na localhost:5173
REM
REM Opcje:
REM   start.bat              — uruchomi aplikację
REM   start.bat --no-browser — uruchomi bez otwierania przeglądarki
REM ============================================================================

setlocal enabledelayedexpansion

REM Kolory w console (dla komunikatów)
for /f %%A in ('copy /Z "%~f0" nul') do set "BS=%%A"

echo.
echo %BS%[1;32m=== WCAG Analyzer ===%BS%[0m
echo.

REM Katalog root aplikacji
set ROOT=%~dp0
set BACKEND_DIR=%ROOT%backend
set FRONTEND_DIR=%ROOT%frontend

REM Zmienne środowiskowe (opcjonalne — można zmienić)
if not defined WCAG_FILES_DIR (
    set WCAG_FILES_DIR=C:\wcag
)
if not defined WCAG_OUTPUT_DIR (
    set WCAG_OUTPUT_DIR=%WCAG_FILES_DIR%\raporty
)

echo WCAG_FILES_DIR=%WCAG_FILES_DIR%
echo WCAG_OUTPUT_DIR=%WCAG_OUTPUT_DIR%
echo.

REM ============================================================================
REM Uruchomienie Backend
REM ============================================================================
echo %BS%[1;33m[Backend]%BS%[0m Uruchamianie FastAPI na http://localhost:8000...
echo.
start "WCAG Analyzer — Backend (FastAPI)" cmd /k ^
    cd /d "%BACKEND_DIR%" ^& ^
    venv\Scripts\activate.bat ^& ^
    set WCAG_FILES_DIR=%WCAG_FILES_DIR% ^& ^
    set WCAG_OUTPUT_DIR=%WCAG_OUTPUT_DIR% ^& ^
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

REM Czekaj 3 sekundy na uruchomienie backend
timeout /t 3 /nobreak > nul

REM ============================================================================
REM Uruchomienie Frontend
REM ============================================================================
echo %BS%[1;33m[Frontend]%BS%[0m Uruchamianie Vite na http://localhost:5173...
echo.
start "WCAG Analyzer — Frontend (Vite)" cmd /k ^
    cd /d "%FRONTEND_DIR%" ^& ^
    npm run dev

REM Czekaj 2 sekundy na uruchomienie frontend dev server
timeout /t 2 /nobreak > nul

REM ============================================================================
REM Otwórz przeglądarkę
REM ============================================================================
if "%~1"=="--no-browser" (
    echo %BS%[1;34m[Info]%BS%[0m Aplikacja uruchomiona bez otwierania przeglądarki.
) else (
    echo %BS%[1;34m[Browser]%BS%[0m Otwieranie http://localhost:5173...
    start "" http://localhost:5173
)

echo.
echo %BS%[1;32m[OK]%BS%[0m Aplikacja jest uruchomiona!
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo Aby zatrzymać aplikację, zamknij oba okna terminala.
echo.

endlocal
