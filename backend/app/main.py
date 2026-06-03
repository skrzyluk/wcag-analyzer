"""
main.py - FastAPI Backend dla WCAG 2.1 AA Analyzer
Port: 8000

Endpoints:
  GET  /api/health             - sprawdzenie stanu serwera
  POST /api/upload             - upload pojedynczego pliku MHTML
  POST /api/upload-batch       - upload wielu plikow MHTML naraz
  POST /api/analyze/{id}       - uruchom analize WCAG
  GET  /api/status/{id}        - status analizy (polling)
  GET  /api/report/{id}        - pobierz raport
  GET  /api/export/{id}/{fmt}  - eksport HTML/PDF/JSON/XLSX
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List
from urllib.parse import quote
import asyncio
import os
import re
import uuid, time, datetime
from pathlib import Path

from app.report_generator import generate_html_report, generate_pdf_report

app = FastAPI(
    title="WCAG 2.1 AA Analyzer API",
    description="Lokalna analiza dostepnosci plikow MHTML",
    version="1.0.0-dev"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

_store: dict = {}
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_BATCH_FILES = 40

LOCAL_FILES_DIR = Path(os.getenv("WCAG_FILES_DIR", r"C:\Users\Dell\Desktop\audyt06"))
OUTPUT_DIR      = Path(os.getenv("WCAG_OUTPUT_DIR", str(LOCAL_FILES_DIR / "raporty")))
_preloaded_analyses: list[str] = []
_autoloaded_filenames: set[str] = set()


def _download_headers(filename: str) -> dict:
    cleaned = re.sub(r"[\r\n\\/]+", "-", filename).strip().strip(".")
    cleaned = cleaned or "raport"
    ascii_fallback = cleaned.encode("ascii", "ignore").decode("ascii")
    ascii_fallback = re.sub(r"[^A-Za-z0-9._ -]+", "-", ascii_fallback).strip()
    ascii_fallback = ascii_fallback or "raport"
    return {
        "Content-Disposition": (
            f'attachment; filename="{ascii_fallback}"; '
            f"filename*=UTF-8''{quote(cleaned, safe='')}"
        )
    }


def _combine_analysis_reports(analysis_ids: List[str]) -> dict:
    reports = []
    for analysis_id in analysis_ids:
        report = _store.get(analysis_id)
        if not report or report.get("status") != "completed":
            raise HTTPException(
                status_code=404,
                detail=f"Raport {analysis_id} nie istnieje lub nie jest zakonczony."
            )
        reports.append(report)

    if not reports:
        raise HTTPException(status_code=400, detail="Brak raportow do polaczenia.")

    if len(reports) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Mozna polaczyc maksymalnie {MAX_BATCH_FILES} raportow."
        )

    combined_id = str(uuid.uuid4())
    combined_issues = []
    source_reports = []
    compliance_values = []

    summary = {
        "total_checks": 0,
        "total_issues": 0,
        "critical_errors": 0,
        "major_errors": 0,
        "minor_errors": 0,
        "warnings": 0,
        "passed_checks": 0,
        "compliance_percentage": 0,
    }

    for report_index, report in enumerate(reports, start=1):
        filename = report.get("filename", f"plik-{report_index}.mhtml")
        source_reports.append({
            "analysis_id": report.get("analysis_id"),
            "filename": filename,
            "summary": report.get("summary", {}),
        })

        report_summary = report.get("summary", {})
        for key in ("total_checks", "total_issues", "critical_errors",
                    "major_errors", "minor_errors", "warnings", "passed_checks"):
            summary[key] += int(report_summary.get(key, 0) or 0)
        compliance_values.append(float(report_summary.get("compliance_percentage", 0) or 0))

        for issue_index, issue in enumerate(report.get("issues", []), start=1):
            combined_issue = dict(issue)
            combined_issue["id"] = f"{report.get('analysis_id', report_index)}-{issue.get('id', issue_index)}"
            combined_issue["source_file"] = filename
            combined_issue["source_analysis_id"] = report.get("analysis_id")
            combined_issues.append(combined_issue)

    summary["total_issues"] = len(combined_issues)
    summary["compliance_percentage"] = round(sum(compliance_values) / len(compliance_values))

    combined_report = {
        "analysis_id": combined_id,
        "file_id": None,
        "filename": f"Raport zbiorczy - {len(reports)} plikow",
        "status": "completed",
        "progress": 100,
        "analysis_date": datetime.datetime.utcnow().isoformat() + "Z",
        "summary": summary,
        "issues": combined_issues,
        "source_reports": source_reports,
        "combined": True,
    }
    _store[combined_id] = combined_report
    return combined_report


def _build_summary(issues: list) -> dict:
    """Buduje slownik summary na podstawie listy Issue (dataclass lub dict)."""
    WCAG_TOTAL_CHECKS = 50  # ~50 kryteriow WCAG 2.1 A+AA

    def _sev(issue):
        if hasattr(issue, "severity"):
            return issue.severity
        return issue.get("severity", "")

    critical = sum(1 for i in issues if _sev(i) == "critical")
    major    = sum(1 for i in issues if _sev(i) == "major")
    minor    = sum(1 for i in issues if _sev(i) == "minor")
    warnings = sum(1 for i in issues if _sev(i) == "warning")
    total    = len(issues)
    passed   = max(0, WCAG_TOTAL_CHECKS - total)
    compliance = round(max(0.0, 100.0 * (WCAG_TOTAL_CHECKS - critical - major) / WCAG_TOTAL_CHECKS))

    return {
        "total_checks":          WCAG_TOTAL_CHECKS,
        "total_issues":          total,
        "critical_errors":       critical,
        "major_errors":          major,
        "minor_errors":          minor,
        "warnings":              warnings,
        "passed_checks":         passed,
        "compliance_percentage": compliance,
    }


def _issue_to_dict(issue) -> dict:
    """Konwertuje Issue dataclass do slownika kompatybilnego z API."""
    if isinstance(issue, dict):
        return issue

    affected = []
    for el in (issue.affected_elements or []):
        if isinstance(el, dict):
            affected.append(el)
        else:
            affected.append({
                "tag":          getattr(el, "tag", ""),
                "html_snippet": getattr(el, "html_snippet", ""),
                "html_after":   getattr(el, "html_after", ""),
            })

    return {
        "id":                issue.id,
        "wcag_criterion":    issue.wcag_criterion,
        "severity":          issue.severity,
        "description":       issue.description,
        "recommendation":    issue.recommendation,
        "affected_elements": affected,
    }


# ----------------------------------------------
# ANALIZA — sync helper (używany przez endpoint i autoload)
# ----------------------------------------------

def _run_analysis_sync(file_id: str, analysis_id: str) -> None:
    """Synchroniczna pipeline analizy WCAG. Zapisuje wynik do _store (bez HTTPException)."""
    try:
        from app.core.mhtml_parser import MHTMLParser
        from app.core.wcag_validator import WCAGValidator

        raw_content = _store[file_id]["content"]
        parsed = MHTMLParser().parse(raw_content)
        soup = parsed.get_soup()
        issues_raw = WCAGValidator().validate(soup, url=parsed.url)
        issues_dict = [_issue_to_dict(i) for i in issues_raw]
        summary = _build_summary(issues_raw)

        _store[analysis_id].update({
            "status":        "completed",
            "progress":      100,
            "analysis_date": datetime.datetime.utcnow().isoformat() + "Z",
            "summary":       summary,
            "issues":        issues_dict,
            "parsed_html":   parsed.html_content,
            "page_title":    parsed.page_title,
            "page_url":      parsed.url,
        })
    except Exception as exc:
        _store[analysis_id].update({
            "status":       "error",
            "progress":     0,
            "error_detail": str(exc),
        })


# ----------------------------------------------
# ZAPIS RAPORTÓW NA DYSK (XLSX + DOCX)
# ----------------------------------------------

def _save_reports_to_disk(analysis_id: str) -> None:
    """Po udanej analizie zapisuje XLSX i DOCX do OUTPUT_DIR."""
    r = _store.get(analysis_id)
    if not r or r.get("status") != "completed":
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename_base = r.get("filename", "raport").rsplit(".", 1)[0]
    safe_base = re.sub(r'[\\/:*?"<>|]+', "_", filename_base)[:80]

    # ── XLSX ──────────────────────────────────────────────────────────
    try:
        from app.services.issue_mapper import IssueMapper, resolve_page_prefix
        from app.services.xlsx_report_generator import XLSXReportGenerator
        from app.services.focus_order_analyzer import FocusOrderAnalyzer
        from bs4 import BeautifulSoup

        sheet_name = filename_base[:31] or "Analiza"
        prefix     = resolve_page_prefix(filename_base)

        focus_steps = None
        raw_html = r.get("parsed_html")
        if raw_html:
            try:
                soup = BeautifulSoup(raw_html, "lxml")
                focus_steps = FocusOrderAnalyzer().analyze(soup)
            except Exception:
                pass

        mapper = IssueMapper()
        page   = mapper.map_page(
            issues=r.get("issues", []),
            sheet_name=sheet_name,
            title=f"{sheet_name} — audyt WCAG 2.1 AA",
            description=f"Plik źródłowy: {r.get('filename', '')}",
            prefix=prefix,
        )
        xlsx_path = OUTPUT_DIR / f"{safe_base}_audyt.xlsx"
        XLSXReportGenerator().generate_file([page], str(xlsx_path), focus_steps=focus_steps)
        print(f"[autoload] Zapisano XLSX: {xlsx_path.name}")
    except Exception as exc:
        print(f"[autoload] Błąd XLSX dla {r.get('filename')}: {exc}")

    # ── DOCX ──────────────────────────────────────────────────────────
    try:
        from app.services.docx_report_generator import DOCXReportGenerator
        docx_path = OUTPUT_DIR / f"{safe_base}_audyt.docx"
        DOCXReportGenerator().generate_file(r, str(docx_path))
        print(f"[autoload] Zapisano DOCX: {docx_path.name}")
    except Exception as exc:
        print(f"[autoload] Błąd DOCX dla {r.get('filename')}: {exc}")


def _collect_completed_reports() -> list[dict]:
    """Zwraca wszystkie ukończone analizy z wynikami (pomija wpisy plików i zbiorcze)."""
    reports = []
    for entry in _store.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("status") != "completed" or entry.get("combined"):
            continue
        if "issues" not in entry:
            continue
        reports.append(entry)
    return reports


def _save_aggregate_md() -> None:
    """Buduje zbiorczy raport MD ze wszystkich ukończonych analiz i zapisuje do OUTPUT_DIR."""
    reports = _collect_completed_reports()
    if not reports:
        return
    try:
        from app.services.markdown_report_generator import MarkdownReportGenerator
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        md_path = OUTPUT_DIR / "raport_zbiorczy_WCAG.md"
        MarkdownReportGenerator().generate_file(reports, str(md_path))
        print(f"[autoload] Zapisano zbiorczy raport MD: {md_path.name} ({len(reports)} podstron)")
    except Exception as exc:
        print(f"[autoload] Błąd zbiorczego raportu MD: {exc}")


# ----------------------------------------------
# AUTOLOAD — wczytaj i analizuj pliki przy starcie
# ----------------------------------------------

async def _autoload_directory() -> None:
    """Skanuje LOCAL_FILES_DIR i analizuje znalezione pliki MHTML w tle."""
    if not LOCAL_FILES_DIR.exists() or not LOCAL_FILES_DIR.is_dir():
        print(f"[autoload] Katalog nie istnieje: {LOCAL_FILES_DIR}")
        return

    mhtml_files = [
        p for p in LOCAL_FILES_DIR.iterdir()
        if p.suffix.lower() in (".mhtml", ".mht") and p.is_file()
    ]
    if not mhtml_files:
        print("[autoload] Brak plików MHTML w katalogu.")
        return

    print(f"[autoload] Znaleziono {len(mhtml_files)} plików — rozpoczynam analizę.")
    semaphore = asyncio.Semaphore(3)

    async def _load_one(path: Path) -> None:
        filename = path.name
        if filename in _autoloaded_filenames:
            return
        _autoloaded_filenames.add(filename)

        try:
            content = path.read_bytes()
        except OSError as exc:
            print(f"[autoload] Nie można odczytać {filename}: {exc}")
            return

        if len(content) == 0 or len(content) > MAX_FILE_SIZE:
            print(f"[autoload] Pominięto {filename} — pusty lub za duży.")
            return

        file_id = str(uuid.uuid4())
        _store[file_id] = {
            "file_id":  file_id,
            "filename": filename,
            "size":     len(content),
            "content":  content,
            "status":   "uploaded",
        }

        analysis_id = str(uuid.uuid4())
        _store[analysis_id] = {
            "analysis_id": analysis_id,
            "file_id":     file_id,
            "filename":    filename,
            "status":      "pending",
            "progress":    0,
            "created_at":  time.time(),
            "preloaded":   True,
        }
        _preloaded_analyses.append(analysis_id)

        async with semaphore:
            print(f"[autoload] Analizowanie: {filename}")
            await asyncio.to_thread(_run_analysis_sync, file_id, analysis_id)
            status = _store[analysis_id]["status"]
            print(f"[autoload] {filename}: {status}")
            if status == "completed":
                await asyncio.to_thread(_save_reports_to_disk, analysis_id)

    await asyncio.gather(*[_load_one(p) for p in mhtml_files])
    completed = sum(1 for aid in _preloaded_analyses if _store.get(aid, {}).get("status") == "completed")
    print(f"[autoload] Zakończono. {completed}/{len(mhtml_files)} analiz ukończonych.")

    # Zbiorczy raport MD ze wszystkich ukończonych analiz (raz, bez wyścigu o plik)
    await asyncio.to_thread(_save_aggregate_md)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(_autoload_directory())


# ----------------------------------------------
# HEALTH CHECK
# ----------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0-dev", "timestamp": time.time()}


# ----------------------------------------------
# UPLOAD MHTML
# ----------------------------------------------

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ("mhtml", "mht"):
        raise HTTPException(status_code=400, detail="Dozwolone formaty: .mhtml, .mht")

    file_id = str(uuid.uuid4())
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Plik jest pusty.")

    if len(content) > MAX_FILE_SIZE:
        size_mb = len(content) / 1024 / 1024
        raise HTTPException(
            status_code=413,
            detail=f"Plik za duzy ({size_mb:.2f} MB). Maksimum: 50 MB."
        )

    _store[file_id] = {
        "file_id":  file_id,
        "filename": file.filename,
        "size":     len(content),
        "content":  content,
        "status":   "uploaded",
    }

    return {"file_id": file_id, "filename": file.filename, "size": len(content)}


# ----------------------------------------------
# UPLOAD BATCH
# ----------------------------------------------

@app.post("/api/upload-batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Brak plikow w zadaniu.")

    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Zbyt duzo plikow. Maksymalna liczba to {MAX_BATCH_FILES}."
        )

    results = []

    for upload in files:
        filename = upload.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in ("mhtml", "mht"):
            results.append({"filename": filename, "error": "Nieprawidlowy format pliku. Dozwolone: .mhtml, .mht"})
            continue

        content = await upload.read()

        if len(content) == 0:
            results.append({"filename": filename, "error": "Plik jest pusty."})
            continue

        if len(content) > MAX_FILE_SIZE:
            size_mb = len(content) / 1024 / 1024
            results.append({"filename": filename, "error": f"Plik za duzy ({size_mb:.2f} MB). Maksimum: 50 MB."})
            continue

        file_id = str(uuid.uuid4())
        _store[file_id] = {
            "file_id":  file_id,
            "filename": filename,
            "size":     len(content),
            "content":  content,
            "status":   "uploaded",
        }
        results.append({"file_id": file_id, "filename": filename, "size": len(content)})

    successful = [r for r in results if "file_id" in r]
    if not successful:
        raise HTTPException(
            status_code=400,
            detail={"message": "Zaden plik nie przeszedl walidacji.", "files": results}
        )

    return {"uploaded": len(successful), "total": len(results), "files": results}


# ----------------------------------------------
# ANALIZA WCAG — PELNY PIPELINE
# ----------------------------------------------

@app.post("/api/analyze/{file_id}")
async def analyze(file_id: str):
    if file_id not in _store:
        raise HTTPException(status_code=404, detail="Plik nie znaleziony")

    analysis_id = str(uuid.uuid4())
    _store[analysis_id] = {
        "analysis_id": analysis_id,
        "file_id":     file_id,
        "filename":    _store[file_id]["filename"],
        "status":      "pending",
        "progress":    0,
        "created_at":  time.time(),
    }

    await asyncio.to_thread(_run_analysis_sync, file_id, analysis_id)

    if _store[analysis_id]["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=f"Blad analizy WCAG: {_store[analysis_id].get('error_detail', '')}"
        )

    return {"analysis_id": analysis_id, "status": "completed"}


# ----------------------------------------------
# PRELOADED — lista analiz z auto-wczytania
# ----------------------------------------------

@app.get("/api/preloaded")
async def get_preloaded():
    """Zwraca listę analiz wczytanych automatycznie przy starcie z LOCAL_FILES_DIR."""
    result = []
    for analysis_id in _preloaded_analyses:
        r = _store.get(analysis_id)
        if not r:
            continue
        result.append({
            "analysis_id":   r["analysis_id"],
            "filename":      r.get("filename", ""),
            "status":        r.get("status", "pending"),
            "progress":      r.get("progress", 0),
            "analysis_date": r.get("analysis_date"),
            "summary":       r.get("summary"),
            "error_detail":  r.get("error_detail"),
        })
    return {"preloaded": result, "total": len(result)}


# ----------------------------------------------
# STATUS
# ----------------------------------------------

@app.get("/api/status/{analysis_id}")
async def get_status(analysis_id: str):
    if analysis_id not in _store or "analysis_id" not in _store[analysis_id]:
        raise HTTPException(status_code=404, detail="Analiza nie znaleziona")
    r = _store[analysis_id]
    return {
        "analysis_id": r["analysis_id"],
        "status":      r["status"],
        "progress":    r.get("progress", 0),
    }


# ----------------------------------------------
# RAPORT
# ----------------------------------------------

@app.get("/api/report/{analysis_id}")
async def get_report(analysis_id: str):
    r = _store.get(analysis_id)
    if not r or r.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Raport niedostepny")
    # Nie zwracamy surowego HTML do klienta (moze byc duzy)
    safe = {k: v for k, v in r.items() if k not in ("content", "parsed_html")}
    return safe


@app.post("/api/reports/combine")
async def combine_reports(payload: dict):
    analysis_ids = payload.get("analysis_ids") if isinstance(payload, dict) else None
    if not isinstance(analysis_ids, list):
        raise HTTPException(status_code=400, detail="Pole analysis_ids musi byc lista.")
    analysis_ids = [str(item) for item in analysis_ids if item]
    return _combine_analysis_reports(analysis_ids)


# ----------------------------------------------
# EKSPORT: html / pdf / json / xlsx
# ----------------------------------------------

@app.get("/api/export/{analysis_id}/{format}")
async def export_report(analysis_id: str, format: str):
    """
    Eksportuje raport z analizy WCAG jako:
      - html  - Deklaracja dostepnosci (HTML, embedded CSS)
      - pdf   - Deklaracja dostepnosci (PDF, ReportLab, A4)
      - json  - Surowe dane analizy (JSON)
      - xlsx  - Arkusz audytu WCAG 2.1 AA (Excel)
      - docx  - Raport audytu WCAG 2.1 AA (Word)
      - md    - Zbiorczy raport audytowy (Markdown, material do raportu Word)
    """
    if format not in ("html", "pdf", "json", "xlsx", "docx", "md"):
        raise HTTPException(status_code=400, detail="Dozwolone formaty: html, pdf, json, xlsx, docx, md")

    r = _store.get(analysis_id)
    if not r or r.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Analiza nie znaleziona lub nie zakonczona.")

    # JSON
    if format == "json":
        import json
        safe = {k: v for k, v in r.items() if k not in ("content", "parsed_html")}
        return Response(
            content=json.dumps(safe, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers=_download_headers(f"deklaracja-wcag-{analysis_id[:8]}.json")
        )

    # HTML
    if format == "html":
        try:
            html_bytes = generate_html_report(r)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Blad generowania HTML: {exc}")

        filename = r.get("filename", "raport").rsplit(".", 1)[0]
        return Response(
            content=html_bytes,
            media_type="text/html; charset=utf-8",
            headers=_download_headers(f"deklaracja-{filename[:40]}.html")
        )

    # PDF
    if format == "pdf":
        try:
            pdf_bytes = generate_pdf_report(r)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Blad generowania PDF: {exc}")

        filename = r.get("filename", "raport").rsplit(".", 1)[0]
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers=_download_headers(f"deklaracja-{filename[:40]}.pdf")
        )

    # XLSX
    if format == "xlsx":
        try:
            from app.services.issue_mapper import IssueMapper, resolve_page_prefix
            from app.services.xlsx_report_generator import XLSXReportGenerator
            from app.services.focus_order_analyzer import FocusOrderAnalyzer

            filename_base = r.get("filename", "raport").rsplit(".", 1)[0]
            sheet_name    = filename_base[:31] or "Analiza"
            prefix        = resolve_page_prefix(filename_base)

            # Analiza kolejnosci fokusa — wymaga HTML z pliku MHTML
            focus_steps = None
            raw_html = r.get("parsed_html")
            if raw_html:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(raw_html, "lxml")
                    focus_steps = FocusOrderAnalyzer().analyze(soup)
                except Exception:
                    focus_steps = None  # fokus nie blokuje generowania raportu

            mapper = IssueMapper()
            page   = mapper.map_page(
                issues=r.get("issues", []),
                sheet_name=sheet_name,
                title=f"{sheet_name} -- audyt WCAG 2.1 AA",
                description=f"Plik zrodlowy: {r.get('filename', '')}",
                prefix=prefix,
            )

            gen        = XLSXReportGenerator()
            xlsx_bytes = gen.generate_bytes([page], focus_steps=focus_steps)

        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Blad generowania XLSX: {exc}")

        filename_base = r.get("filename", "raport").rsplit(".", 1)[0]
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=_download_headers(f"Audyt_WCAG_{filename_base[:30]}.xlsx")
        )

    # DOCX
    if format == "docx":
        try:
            from app.services.docx_report_generator import DOCXReportGenerator
            docx_bytes = DOCXReportGenerator().generate_bytes(r)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Blad generowania DOCX: {exc}")

        filename_base = r.get("filename", "raport").rsplit(".", 1)[0]
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=_download_headers(f"Audyt_WCAG_{filename_base[:30]}.docx")
        )

    # MD (zbiorczy raport audytowy — dla pojedynczej analizy: lista [r])
    if format == "md":
        try:
            from app.services.markdown_report_generator import MarkdownReportGenerator
            md_bytes = MarkdownReportGenerator().generate_bytes([r])
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Blad generowania MD: {exc}")

        filename_base = r.get("filename", "raport").rsplit(".", 1)[0]
        return Response(
            content=md_bytes,
            media_type="text/markdown; charset=utf-8",
            headers=_download_headers(f"Audyt_WCAG_{filename_base[:30]}.md")
        )
