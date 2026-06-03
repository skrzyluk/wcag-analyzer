#!/usr/bin/env python3
"""
run_backend.py — Uruchamia backend FastAPI przez uvicorn.
Alternatywa dla start.bat gdy chcesz uruchomić tylko backend.

Użycie:
    python run_backend.py
    python run_backend.py --port 8001
"""
import sys, subprocess, pathlib

ROOT = pathlib.Path(__file__).parent
VENV_PYTHON = ROOT / "backend" / "venv" / "Scripts" / "python.exe"

if not VENV_PYTHON.exists():
    # Fallback na systemowe python (Linux/Mac)
    VENV_PYTHON = ROOT / "backend" / "venv" / "bin" / "python"

if not VENV_PYTHON.exists():
    print("[BLAD] Nie znaleziono venv. Uruchom:")
    print("  cd backend && python -m venv venv && venv/Scripts/pip install -r requirements.txt")
    sys.exit(1)

port = "8000"
if "--port" in sys.argv:
    port = sys.argv[sys.argv.index("--port") + 1]

print(f"  Backend: http://localhost:{port}")
print(f"  API Docs: http://localhost:{port}/docs")
print()

subprocess.run([
    str(VENV_PYTHON), "-m", "uvicorn",
    "app.main:app",
    "--host", "127.0.0.1",
    "--port", port,
    "--reload"
], cwd=str(ROOT / "backend"))
