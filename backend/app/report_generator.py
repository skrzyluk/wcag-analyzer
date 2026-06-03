"""
report_generator.py — Generator raportów WCAG 2.1 AA
Projekt: WCAG 2.1 AA Analyzer

Generuje Deklarację dostępności zgodną ze strukturą opisaną w:
  "Warunki techniczne publikacji i struktura dokumentu elektronicznego
   deklaracji dostępności" (Ministerstwo Cyfryzacji, wersja 2.0, 2024)

Formaty:
  - HTML  (self-contained, embedded CSS, wszystkie wymagane id HTML)
  - PDF   (ReportLab — profesjonalny układ do druku)
"""

import io
import os
import datetime
from typing import Any

# ── Ścieżka do katalogu z czcionkami (bundle w projekcie) ─────────────────────
_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")


def _register_fonts():
    """
    Rejestruje czcionki DejaVu Sans w ReportLab.
    DejaVu obsługuje pełny zakres Unicode, w tym polskie litery (ą ę ś ó ć ź ż ń ł).
    Funkcja jest idempotentna — bezpieczna do wielokrotnego wywołania.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Sprawdź czy już zarejestrowane
    try:
        pdfmetrics.getFont("DejaVu")
        return  # już zarejestrowane — nic nie rób
    except Exception:
        pass  # nie ma — rejestrujemy

    font_files = {
        "DejaVu":             "DejaVuSans.ttf",
        "DejaVu-Bold":        "DejaVuSans-Bold.ttf",
        "DejaVu-Oblique":     "DejaVuSans-Oblique.ttf",
        "DejaVu-BoldOblique": "DejaVuSans-BoldOblique.ttf",
        "DejaVuMono":         "DejaVuSansMono.ttf",
        "DejaVuMono-Bold":    "DejaVuSansMono-Bold.ttf",
    }

    for name, filename in font_files.items():
        path = os.path.join(_FONTS_DIR, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"Czcionka '{filename}' nie znaleziona w {_FONTS_DIR}. "
                "Sprawdz czy katalog backend/app/fonts/ zawiera pliki DejaVu."
            )
        pdfmetrics.registerFont(TTFont(name, path))

    # Rejestracja rodziny — umozliwia dzialanie tagow <b> i <i> w Paragraph
    pdfmetrics.registerFontFamily(
        "DejaVu",
        normal="DejaVu",
        bold="DejaVu-Bold",
        italic="DejaVu-Oblique",
        boldItalic="DejaVu-BoldOblique",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compliance_status(summary: dict) -> str:
    """Zwraca: 'full' | 'partial' | 'none'"""
    critical = summary.get("critical_errors", 0)
    major    = summary.get("major_errors", 0)
    pct      = summary.get("compliance_percentage", 0)
    if critical == 0 and major == 0:
        return "full"
    if pct >= 50:
        return "partial"
    return "none"


def _status_phrase(status: str) -> str:
    return {
        "full":    "w pelni zgodna",
        "partial": "czesciowo zgodna",
        "none":    "niezgodna",
    }.get(status, "czesciowo zgodna")


def _status_phrase_pl(status: str) -> str:
    """Polska wersja z diakrytykami — do HTML (UTF-8 OK)."""
    return {
        "full":    "w pełni zgodna",
        "partial": "częściowo zgodna",
        "none":    "niezgodna",
    }.get(status, "częściowo zgodna")


def _format_date_pl(dt_str) -> str:
    MONTHS = [
        "", "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "wrzesnia", "pazdziernika", "listopada", "grudnia"
    ]
    MONTHS_PL = [
        "", "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "września", "października", "listopada", "grudnia"
    ]
    try:
        if not dt_str:
            raise ValueError
        dt = datetime.datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        return f"{dt.day} {MONTHS_PL[dt.month]} {dt.year} r."
    except Exception:
        today = datetime.date.today()
        return f"{today.day} {MONTHS_PL[today.month]} {today.year} r."


def _format_date_pl_ascii(dt_str) -> str:
    """Wersja bez diakrytykow — do PDF (bezpieczna)."""
    MONTHS = [
        "", "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "wrzesnia", "pazdziernika", "listopada", "grudnia"
    ]
    try:
        if not dt_str:
            raise ValueError
        dt = datetime.datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        return f"{dt.day} {MONTHS[dt.month]} {dt.year} r."
    except Exception:
        today = datetime.date.today()
        return f"{today.day} {MONTHS[today.month]} {today.year} r."


def _format_date_iso(dt_str) -> str:
    try:
        if not dt_str:
            raise ValueError
        dt = datetime.datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return datetime.date.today().isoformat()


def _severity_label(severity: str) -> str:
    return {"critical": "Krytyczny", "major": "Powazny", "minor": "Drobny"}.get(severity, severity)


def _severity_label_pl(severity: str) -> str:
    """Z diakrytykami — dla HTML."""
    return {"critical": "Krytyczny", "major": "Poważny", "minor": "Drobny"}.get(severity, severity)


def _severity_color_html(severity: str) -> str:
    return {"critical": "#c0392b", "major": "#e67e22", "minor": "#2980b9"}.get(severity, "#555")


# ── HTML REPORT ───────────────────────────────────────────────────────────────

_HTML_CSS = """
:root {
    --primary:   #1a5276;
    --success:   #1e8449;
    --warning:   #d35400;
    --danger:    #922b21;
    --minor:     #1a5276;
    --bg:        #ffffff;
    --bg-alt:    #f4f6f8;
    --border:    #d5d8dc;
    --text:      #212529;
    --text-muted:#6c757d;
    --radius:    6px;
}
*, *::before, *::after { box-sizing: border-box; }
body {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.65;
    color: var(--text);
    background: var(--bg);
    margin: 0;
    padding: 0;
}
.page { max-width: 900px; margin: 0 auto; padding: 2rem 2rem 4rem; }
.doc-header {
    background: var(--primary);
    color: #fff;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 0;
    border-radius: var(--radius) var(--radius) 0 0;
}
.doc-header h1 { margin: 0 0 .5rem; font-size: 2rem; font-weight: 700; }
.doc-header .meta { font-size: .9rem; opacity: .85; margin: 0; }
.compliance-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.1rem 2rem;
    font-weight: 600;
    font-size: 1.05rem;
    margin-bottom: 2rem;
    border-radius: 0 0 var(--radius) var(--radius);
}
.compliance-bar.full    { background: #d5f5e3; color: var(--success); border: 1px solid #a9dfbf; }
.compliance-bar.partial { background: #fef9e7; color: var(--warning); border: 1px solid #f9e79f; }
.compliance-bar.none    { background: #fadbd8; color: var(--danger);  border: 1px solid #f1948a; }
.compliance-bar .icon   { font-size: 1.5rem; }
.compliance-bar .pct    { margin-left: auto; font-size: .9rem; }
section { margin-bottom: 2.5rem; }
h2 {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--primary);
    border-bottom: 2px solid var(--primary);
    padding-bottom: .4rem;
    margin: 2rem 0 1rem;
}
h3 { font-size: 1.05rem; font-weight: 700; color: var(--text); margin: 1.5rem 0 .6rem; }
p  { margin: .5rem 0 1rem; }
ul, ol { padding-left: 1.5rem; }
li { margin-bottom: .4rem; }
#a11y-wstep {
    background: var(--bg-alt);
    border-left: 4px solid var(--primary);
    padding: 1.2rem 1.5rem;
    border-radius: 0 var(--radius) var(--radius) 0;
    margin-bottom: 1.5rem;
}
.issues-table { width: 100%; border-collapse: collapse; font-size: .9rem; margin-top: 1rem; }
.issues-table th {
    background: var(--primary);
    color: #fff;
    text-align: left;
    padding: .7rem 1rem;
    font-weight: 600;
}
.issues-table td { padding: .7rem 1rem; vertical-align: top; border-bottom: 1px solid var(--border); }
.issues-table tr:nth-child(even) td { background: var(--bg-alt); }
.badge {
    display: inline-block;
    padding: .2rem .6rem;
    border-radius: 20px;
    font-size: .78rem;
    font-weight: 700;
    color: #fff;
}
.badge-critical { background: var(--danger); }
.badge-major    { background: var(--warning); }
.badge-minor    { background: var(--minor); }
.html-snippet {
    font-family: "Courier New", monospace;
    font-size: .82rem;
    background: #2c3e50;
    color: #ecf0f1;
    padding: .4rem .7rem;
    border-radius: var(--radius);
    word-break: break-all;
    margin-top: .3rem;
    display: block;
}
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin: 1.2rem 0;
}
.stat-box {
    background: var(--bg-alt);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    text-align: center;
}
.stat-box .number { font-size: 2rem; font-weight: 800; line-height: 1.1; }
.stat-box .label  { font-size: .82rem; color: var(--text-muted); margin-top: .2rem; }
.stat-box.critical .number { color: var(--danger); }
.stat-box.major    .number { color: var(--warning); }
.stat-box.minor    .number { color: var(--minor); }
.stat-box.passed   .number { color: var(--success); }
.stat-box.total    .number { color: var(--primary); }
.doc-footer {
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    font-size: .82rem;
    color: var(--text-muted);
    text-align: center;
}
.placeholder {
    background: #fffde7;
    border: 1px dashed #f9a825;
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    font-size: .88rem;
    color: #795548;
    margin: .5rem 0 1rem;
}
.placeholder strong { color: #e65100; }
@media print {
    .doc-header { border-radius: 0; }
    .compliance-bar { border-radius: 0; }
    h2 { page-break-after: avoid; }
    .issues-table tr { page-break-inside: avoid; }
}
"""


def generate_html_report(data: dict) -> bytes:
    """Generuje Deklarację dostępności w formacie HTML. Zwraca bajty UTF-8."""
    filename      = data.get("filename", "—")
    analysis_date = data.get("analysis_date", "")
    summary       = data.get("summary", {})
    issues        = data.get("issues", [])

    date_pl  = _format_date_pl(analysis_date)
    date_iso = _format_date_iso(analysis_date)

    status       = _compliance_status(summary)
    status_label = _status_phrase_pl(status)
    status_class = status

    compliance_pct  = summary.get("compliance_percentage", 0)
    total_checks    = summary.get("total_checks", 0)
    passed_checks   = summary.get("passed_checks", 0)
    critical_errors = summary.get("critical_errors", 0)
    major_errors    = summary.get("major_errors", 0)
    minor_errors    = summary.get("minor_errors", 0)

    critical_issues = [i for i in issues if i.get("severity") == "critical"]
    major_issues    = [i for i in issues if i.get("severity") == "major"]
    minor_issues    = [i for i in issues if i.get("severity") == "minor"]

    status_icon = {"full": "✅", "partial": "⚠️", "none": "❌"}.get(status, "⚠️")

    if status == "full":
        status_paragraph = (
            "Ta strona internetowa jest <strong>w pełni zgodna</strong> "
            "z załącznikiem do ustawy o dostępności cyfrowej z dnia 4 kwietnia 2019 r. "
            "o dostępności cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych."
        )
    elif status == "partial":
        status_paragraph = (
            "Ta strona internetowa jest <strong>częściowo zgodna</strong> "
            "z załącznikiem do ustawy o dostępności cyfrowej z dnia 4 kwietnia 2019 r. "
            "o dostępności cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych "
            "z powodu niezgodności wymienionych poniżej."
        )
    else:
        status_paragraph = (
            "Ta strona internetowa jest <strong>niezgodna</strong> "
            "z załącznikiem do ustawy z dnia 4 kwietnia 2019 r. "
            "o dostępności cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych "
            "z powodu niezgodności wymienionych poniżej."
        )

    def issues_rows(issue_list):
        if not issue_list:
            return ""
        rows = []
        for iss in issue_list:
            criterion = iss.get("wcag_criterion", "—")
            severity  = iss.get("severity", "")
            desc      = iss.get("description", "—")
            rec       = iss.get("recommendation", "—")
            source    = iss.get("source_file")
            if source:
                import html as htmlmod
                desc = f"<strong>Plik:</strong> {htmlmod.escape(source)}<br>{desc}"
            elements  = iss.get("affected_elements", [])
            elems_html = ""
            for el in elements[:3]:
                snippet = el.get("html_snippet", el.get("html", ""))
                if snippet:
                    import html as htmlmod
                    elems_html += f'<code class="html-snippet">{htmlmod.escape(snippet)}</code>'
            badge_cls = f"badge-{severity}" if severity in ("critical", "major", "minor") else "badge-minor"
            rows.append(
                f"<tr>"
                f"<td><strong>{criterion}</strong></td>"
                f"<td><span class='badge {badge_cls}'>{_severity_label_pl(severity)}</span></td>"
                f"<td>{desc}</td>"
                f"<td>{rec}{elems_html}</td>"
                f"</tr>"
            )
        return "\n".join(rows)

    def issues_table(issue_list):
        rows = issues_rows(issue_list)
        if not rows:
            return "<p>Brak błędów w tej kategorii.</p>"
        return f"""
        <table class="issues-table" role="table" aria-label="Lista błędów dostępności">
          <thead>
            <tr>
              <th scope="col">Kryterium WCAG</th>
              <th scope="col">Waga</th>
              <th scope="col">Opis problemu</th>
              <th scope="col">Rekomendacja / element</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""

    niezgodnosci_section = ""
    if status in ("partial", "none") and (critical_issues or major_issues or minor_issues):
        niezgodnosci_html = ""
        if critical_issues or major_issues:
            all_nonconform = critical_issues + major_issues
            niezgodnosci_html += f"""
            <h3>Niezgodność z załącznikiem</h3>
            <p>Poniższe elementy strony nie spełniają wymagań zawartych w załączniku
               do ustawy o dostępności cyfrowej:</p>
            {issues_table(all_nonconform)}
            """
        if minor_issues:
            niezgodnosci_html += f"""
            <h3>Pozostałe uchybienia</h3>
            <p>Elementy wymagające poprawy, które nie blokują korzystania ze strony:</p>
            {issues_table(minor_issues)}
            """
        niezgodnosci_section = f"""
        <section aria-labelledby="h-niedostepne">
          <h2 id="h-niedostepne">Niedostępne treści</h2>
          {niezgodnosci_html}
        </section>
        """

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Deklaracja dostępności — {filename}</title>
  <style>{_HTML_CSS}</style>
</head>
<body>
<div class="page">

  <div class="doc-header">
    <h1>Deklaracja dostępności</h1>
    <p class="meta">
      Wygenerowano przez WCAG 2.1 AA Analyzer &nbsp;|&nbsp;
      <time datetime="{date_iso}">{date_pl}</time>
    </p>
  </div>

  <div class="compliance-bar {status_class}" role="status" aria-label="Stan zgodności: {status_label}">
    <span class="icon" aria-hidden="true">{status_icon}</span>
    <span>Strona jest <strong>{status_label}</strong> z wymogami WCAG 2.1 AA</span>
    <span class="pct">{compliance_pct}% kryteriów spełnionych</span>
  </div>

  <div class="stats-grid" role="list" aria-label="Podsumowanie wyników analizy">
    <div class="stat-box total" role="listitem">
      <div class="number">{total_checks}</div>
      <div class="label">Sprawdzonych kryteriów</div>
    </div>
    <div class="stat-box passed" role="listitem">
      <div class="number">{passed_checks}</div>
      <div class="label">Spełnionych</div>
    </div>
    <div class="stat-box critical" role="listitem">
      <div class="number">{critical_errors}</div>
      <div class="label">Błędów krytycznych</div>
    </div>
    <div class="stat-box major" role="listitem">
      <div class="number">{major_errors}</div>
      <div class="label">Błędów poważnych</div>
    </div>
    <div class="stat-box minor" role="listitem">
      <div class="number">{minor_errors}</div>
      <div class="label">Uchybień drobnych</div>
    </div>
  </div>

  <section id="a11y-wstep" aria-labelledby="h-wstep">
    <h2 id="h-wstep">Deklaracja dostępności</h2>
    <p>
      <span id="a11y-podmiot" class="placeholder"><strong>[UZUPEŁNIJ: Nazwa podmiotu publicznego]</strong></span>
      zobowiązuje się zapewnić dostępność swojej
      <span id="a11y-zakres">strony internetowej</span>
      zgodnie z ustawą z dnia 4 kwietnia 2019 r. o dostępności cyfrowej stron internetowych
      i aplikacji mobilnych podmiotów publicznych.
    </p>
    <p>
      Deklaracja dostępności dotyczy strony
      <a href="#" id="a11y-url"><strong>{filename}</strong></a>.
    </p>
    <ul>
      <li>Data publikacji strony internetowej:
        <span class="placeholder"><strong>[UZUPEŁNIJ: data pierwszej publikacji]</strong></span>
      </li>
      <li>Data ostatniej istotnej aktualizacji:
        <time id="a11y-data-aktualizacja" datetime="{date_iso}">{date_pl}</time> (data analizy)
      </li>
    </ul>
  </section>

  <section aria-labelledby="h-stan">
    <h2 id="h-stan">Stan dostępności cyfrowej</h2>
    <p id="a11y-status">{status_paragraph}</p>
  </section>

  {niezgodnosci_section}

  <section aria-labelledby="h-przygotowanie">
    <h2 id="h-przygotowanie">Przygotowanie deklaracji dostępności</h2>
    <ul>
      <li>Data sporządzenia deklaracji:
        <time id="a11y-data-sporzadzenie" datetime="{date_iso}">{date_pl}</time>
      </li>
      <li>Data ostatniego przeglądu deklaracji:
        <time id="a11y-data-przeglad" datetime="{date_iso}">{date_pl}</time>
      </li>
    </ul>
    <p>
      Deklarację sporządzono na podstawie automatycznej analizy przeprowadzonej przez
      narzędzie <strong>WCAG 2.1 AA Analyzer</strong> (weryfikacja {total_checks} kryteriów WCAG 2.1 AA).
    </p>
  </section>

  <section aria-labelledby="h-kontakt">
    <h2 id="h-kontakt">Informacje zwrotne i dane kontaktowe</h2>
    <div class="placeholder">
      <strong>⚠ Do uzupełnienia przez podmiot publiczny:</strong><br>
      Poniższe dane kontaktowe należy uzupełnić zgodnie z wymaganiami art. 10 ustawy
      o dostępności cyfrowej.
    </div>
    <p>
      Wszystkie problemy z dostępnością cyfrową tej strony możesz zgłosić do
      <span id="a11y-kontakt"><strong>[Imię i nazwisko / nazwa komórki]</strong></span> —
      mejlowo <a id="a11y-email" href="mailto:[email]"><strong>[adres e-mail]</strong></a>
      lub telefonicznie <a id="a11y-telefon" href="tel:[telefon]"><strong>[numer telefonu]</strong></a>.
    </p>
    <p>Każdy ma prawo wystąpić z żądaniem zapewnienia dostępności cyfrowej tej strony lub jej elementów.</p>
    <p>Zgłaszając takie żądanie podaj:</p>
    <ul>
      <li>swoje imię i nazwisko,</li>
      <li>swoje dane kontaktowe (np. numer telefonu, e-mail),</li>
      <li>dokładny adres strony internetowej, na której jest niedostępny cyfrowo element lub treść,</li>
      <li>opis na czym polega problem i jaki sposób jego rozwiązania byłby dla Ciebie najwygodniejszy.</li>
    </ul>
    <p>Na Twoje zgłoszenie odpowiemy najszybciej jak to możliwe, nie później niż w ciągu 7 dni.</p>
    <p>Jeżeli ten termin będzie dla nas zbyt krótki poinformujemy Cię o tym.
       Nowy termin nie będzie dłuższy niż 2 miesiące.</p>
    <p>Jeżeli nie będziemy w stanie zapewnić dostępności cyfrowej strony wskazanej w Twoim żądaniu,
       zaproponujemy Ci dostęp do nich w alternatywny sposób.</p>
  </section>

  <section id="a11y-procedura" aria-labelledby="h-procedura">
    <h2 id="h-procedura">Obsługa wniosków i skarg związanych z dostępnością</h2>
    <p>Jeżeli w odpowiedzi na Twój wniosek o zapewnienie dostępności cyfrowej odmówimy
       zapewnienia żądanej dostępności, a Ty nie zgadzasz się z tą odmową, masz prawo złożyć skargę.</p>
    <p>Skargę masz prawo złożyć także, jeśli nie zgadzasz się na skorzystanie z alternatywnego
       sposobu dostępu, który zaproponowaliśmy.</p>
    <div class="placeholder">
      <strong>⚠ Do uzupełnienia:</strong> dane kierownictwa urzędu (adres, e-mail do skargi).
    </div>
    <p>Możesz także poinformować o tej sytuacji
       <a href="https://bip.brpo.gov.pl/">Rzecznika Praw Obywatelskich</a>
       i poprosić o interwencję w Twojej sprawie.</p>
  </section>

  <section aria-labelledby="h-pozostale">
    <h2 id="h-pozostale">Pozostałe informacje</h2>
    <section id="a11y-architektura" aria-labelledby="h-architektura">
      <h3 id="h-architektura">Dostępność architektoniczna</h3>
      <div class="placeholder">
        <strong>⚠ Do uzupełnienia:</strong> opis dostępności architektonicznej siedziby głównej podmiotu.
      </div>
    </section>
    <section id="a11y-komunikacja" aria-labelledby="h-komunikacja">
      <h3 id="h-komunikacja">Dostępność komunikacyjno-informacyjna</h3>
      <div class="placeholder">
        <strong>⚠ Do uzupełnienia:</strong> informacje o tłumaczu języka migowego
        oraz inne informacje o dostępności komunikacyjno-informacyjnej.
      </div>
    </section>
  </section>

  <footer class="doc-footer" role="contentinfo">
    <p>
      Raport wygenerowany przez <strong>WCAG 2.1 AA Analyzer</strong> &nbsp;|&nbsp;
      <time datetime="{date_iso}">{date_pl}</time>
      &nbsp;|&nbsp; Plik: <em>{filename}</em>
    </p>
    <p>
      Dokument zgodny ze strukturą <em>Warunki techniczne publikacji i struktura dokumentu
      elektronicznego deklaracji dostępności</em> (Ministerstwo Cyfryzacji, wersja 2.0, 2024).
    </p>
  </footer>

</div>
</body>
</html>"""

    return html.encode("utf-8")


# ── PDF REPORT ────────────────────────────────────────────────────────────────

def generate_pdf_report(data: dict) -> bytes:
    """
    Generuje Deklarację dostępności w formacie PDF (ReportLab, A4).
    Używa czcionek DejaVu Sans dla pełnej obsługi polskich znaków Unicode.
    Zwraca bajty PDF.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    # Rejestracja czcionek Unicode (polskie znaki)
    _register_fonts()
    F  = "DejaVu"             # regular
    FB = "DejaVu-Bold"        # bold
    FI = "DejaVu-Oblique"     # italic
    FM = "DejaVuMono"         # monospace

    # ── Dane ──
    filename      = data.get("filename", "-")
    analysis_date = data.get("analysis_date", "")
    summary       = data.get("summary", {})
    issues        = data.get("issues", [])

    # Daty — używamy wersji ASCII (bez diakrytykow w nazwach miesiecy)
    # bo daty sa liczbowe: "16 maja 2026 r." — "maja" jest ASCII-safe
    date_pl  = _format_date_pl_ascii(analysis_date)
    date_iso = _format_date_iso(analysis_date)

    status      = _compliance_status(summary)
    status_txt  = _status_phrase(status)  # bez diakrytykow (bezpieczne)

    compliance_pct  = summary.get("compliance_percentage", 0)
    total_checks    = summary.get("total_checks", 0)
    passed_checks   = summary.get("passed_checks", 0)
    critical_errors = summary.get("critical_errors", 0)
    major_errors    = summary.get("major_errors", 0)
    minor_errors    = summary.get("minor_errors", 0)

    critical_issues = [i for i in issues if i.get("severity") == "critical"]
    major_issues    = [i for i in issues if i.get("severity") == "major"]
    minor_issues    = [i for i in issues if i.get("severity") == "minor"]

    # ── Kolory ──
    C_PRIMARY = colors.HexColor("#1a5276")
    C_SUCCESS = colors.HexColor("#1e8449")
    C_WARNING = colors.HexColor("#d35400")
    C_DANGER  = colors.HexColor("#922b21")
    C_MINOR   = colors.HexColor("#1a5276")
    C_BG_ALT  = colors.HexColor("#f4f6f8")
    C_BORDER  = colors.HexColor("#d5d8dc")
    C_TEXT    = colors.HexColor("#212529")
    C_MUTED   = colors.HexColor("#6c757d")

    STATUS_COLORS = {"full": C_SUCCESS, "partial": C_WARNING, "none": C_DANGER}
    STATUS_BG = {
        "full":    colors.HexColor("#d5f5e3"),
        "partial": colors.HexColor("#fef9e7"),
        "none":    colors.HexColor("#fadbd8"),
    }
    SEVERITY_COLORS = {"critical": C_DANGER, "major": C_WARNING, "minor": C_MINOR}

    # ── Style — unikalne nazwy (ReportLab ma globalny rejestr stylów) ──
    _uid = str(id(data))

    def S(name, **kw):
        return ParagraphStyle(f"rg_{name}_{_uid}", **kw)

    title_s    = S("title",    fontName=FB, fontSize=20, textColor=colors.white, leading=26, spaceAfter=4)
    subtitle_s = S("subtitle", fontName=F,  fontSize=10, textColor=colors.HexColor("#b2d8f7"), spaceAfter=0)
    h2_s       = S("h2",       fontName=FB, fontSize=14, textColor=C_PRIMARY, spaceBefore=16, spaceAfter=6, leading=18)
    h3_s       = S("h3",       fontName=FB, fontSize=11, textColor=C_TEXT, spaceBefore=10, spaceAfter=4)
    body_s     = S("body",     fontName=F,  fontSize=9.5, textColor=C_TEXT, leading=14, spaceAfter=6)
    small_s    = S("small",    fontName=F,  fontSize=8.5, textColor=C_MUTED, leading=12, spaceAfter=4)
    status_s   = S("status",   fontName=FB, fontSize=11,
                               textColor=STATUS_COLORS.get(status, C_WARNING), spaceBefore=4, spaceAfter=4)
    ph_s       = S("ph",       fontName=FI, fontSize=9, textColor=colors.HexColor("#795548"), leading=13, spaceAfter=4)
    li_s       = S("li",       fontName=F,  fontSize=9.5, textColor=C_TEXT, leading=14, spaceAfter=3,
                               leftIndent=14, bulletIndent=0)
    footer_s   = S("footer",   fontName=F,  fontSize=8, textColor=C_MUTED, alignment=TA_CENTER, leading=11)
    hdr_s      = S("hdr",      fontName=FB, fontSize=8.5, textColor=colors.white, alignment=TA_CENTER)
    sev_crit_s = S("sev_c",    fontName=FB, fontSize=8, textColor=C_DANGER)
    sev_maj_s  = S("sev_m",    fontName=FB, fontSize=8, textColor=C_WARNING)
    sev_min_s  = S("sev_n",    fontName=FB, fontSize=8, textColor=C_MINOR)

    SEV_STYLES = {"critical": sev_crit_s, "major": sev_maj_s, "minor": sev_min_s}

    # ── Buffer i dokument ──
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2.5*cm,
        title=f"Deklaracja dostepnosci - {filename}",
        author="WCAG 2.1 AA Analyzer",
    )

    story = []

    # ── Nagłówek ──
    header_table = Table(
        [[Paragraph("Deklaracja dostepnosci", title_s),
          Paragraph(f"WCAG 2.1 AA Analyzer<br/>{date_pl}", subtitle_s)]],
        colWidths=[None, 5*cm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_PRIMARY),
        ("PADDING",    (0,0), (-1,-1), 12),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # ── Pasek stanu zgodności ──
    status_icon = {"full": "[OK]", "partial": "[!]", "none": "[X]"}.get(status, "[!]")
    status_bg   = STATUS_BG.get(status, STATUS_BG["partial"])
    status_bar  = Table(
        [[Paragraph(
            f"<b>{status_icon} Strona jest {status_txt} z wymogami WCAG 2.1 AA"
            f" ({compliance_pct}% kryteriow spelnionych)</b>",
            S("sb", fontName=FB, fontSize=10, textColor=STATUS_COLORS.get(status, C_WARNING))
        )]],
        colWidths=["100%"],
    )
    status_bar.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), status_bg),
        ("PADDING",    (0,0), (-1,-1), 10),
        ("BOX",        (0,0), (-1,-1), 0.5, STATUS_COLORS.get(status, C_WARNING)),
    ]))
    story.append(status_bar)
    story.append(Spacer(1, 12))

    # ── Statystyki ──
    stats_data = [
        [str(total_checks), str(passed_checks), str(critical_errors), str(major_errors), str(minor_errors)],
        ["Sprawdzonych\nkryteriow", "Spelnionych", "Krytycznych\nbladow", "Powaznych\nbladow", "Drobnych\nuchybien"],
    ]
    stat_colors_row = [C_PRIMARY, C_SUCCESS, C_DANGER, C_WARNING, C_MINOR]
    stats_table = Table(stats_data, colWidths=["20%"]*5)
    stats_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), C_BG_ALT),
        ("FONTNAME",    (0,0), (-1,0), FB),
        ("FONTSIZE",    (0,0), (-1,0), 18),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("FONTNAME",    (0,1), (-1,1), F),
        ("FONTSIZE",    (0,1), (-1,1), 8),
        ("TEXTCOLOR",   (0,1), (-1,1), C_MUTED),
        ("PADDING",     (0,0), (-1,-1), 8),
        ("BOX",         (0,0), (-1,-1), 0.5, C_BORDER),
        ("INNERGRID",   (0,0), (-1,-1), 0.5, C_BORDER),
    ] + [
        ("TEXTCOLOR", (i, 0), (i, 0), c) for i, c in enumerate(stat_colors_row)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 16))

    # ── Helpers ──
    def section(txt):
        story.append(HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceAfter=4))
        story.append(Paragraph(txt, h2_s))

    def subsection(txt):
        story.append(Paragraph(txt, h3_s))

    def body(txt):
        story.append(Paragraph(txt, body_s))

    def bullet(items):
        for item in items:
            story.append(Paragraph(f"&#8226; {item}", li_s))
        story.append(Spacer(1, 4))

    def placeholder(txt):
        ph = Table(
            [[Paragraph(f"[!] {txt}", ph_s)]],
            colWidths=["100%"]
        )
        ph.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#fffde7")),
            ("BOX",        (0,0), (-1,-1), 0.5, colors.HexColor("#f9a825")),
            ("PADDING",    (0,0), (-1,-1), 8),
        ]))
        story.append(ph)
        story.append(Spacer(1, 6))

    # ── ① Deklaracja dostepnosci ──
    section("Deklaracja dostepnosci")
    placeholder("Uzupelnij: Nazwa podmiotu publicznego")
    body("Podmiot zobowiazuje sie zapewnic dostepnosc swojej <b>strony internetowej</b> "
         "zgodnie z ustawa z dnia 4 kwietnia 2019 r. o dostepnosci cyfrowej stron "
         "internetowych i aplikacji mobilnych podmiotow publicznych.")
    body(f"Deklaracja dostepnosci dotyczy strony: <b>{filename}</b>")
    bullet([
        "Data publikacji strony internetowej: [UZUPELNIJ]",
        f"Data ostatniej istotnej aktualizacji: {date_pl} (data analizy WCAG)",
    ])

    # ── ② Stan dostepnosci cyfrowej ──
    section("Stan dostepnosci cyfrowej")
    if status == "full":
        body("Ta strona internetowa jest <b>w pelni zgodna</b> z zalacznikiem do ustawy "
             "o dostepnosci cyfrowej z dnia 4 kwietnia 2019 r.")
    elif status == "partial":
        body("Ta strona internetowa jest <b>czesciowo zgodna</b> z zalacznikiem do ustawy "
             "o dostepnosci cyfrowej z dnia 4 kwietnia 2019 r. "
             "z powodu niezgodnosci wymienionych ponizej.")
    else:
        body("Ta strona internetowa jest <b>niezgodna</b> z zalacznikiem do ustawy "
             "z dnia 4 kwietnia 2019 r. o dostepnosci cyfrowej "
             "z powodu niezgodnosci wymienionych ponizej.")

    # ── ③ Niedostepne tresci ──
    if status in ("partial", "none") and issues:
        section("Niedostepne tresci")

        all_noncompliant = critical_issues + major_issues
        if all_noncompliant:
            subsection("Niezgodnosc z zalacznikiem")
            body("Ponizsze elementy strony nie spelniaja wymagan WCAG 2.1 AA:")

            issue_rows = [[
                Paragraph("Kryterium WCAG", hdr_s),
                Paragraph("Waga", hdr_s),
                Paragraph("Opis problemu", hdr_s),
                Paragraph("Rekomendacja", hdr_s),
            ]]
            for iss in all_noncompliant:
                sev = iss.get("severity", "")
                desc = iss.get("description", "-")
                if iss.get("source_file"):
                    desc = f"<b>Plik:</b> {iss.get('source_file')}<br/>{desc}"
                issue_rows.append([
                    Paragraph(iss.get("wcag_criterion", "-"), small_s),
                    Paragraph(f"<b>{_severity_label(sev)}</b>",
                              SEV_STYLES.get(sev, small_s)),
                    Paragraph(desc, small_s),
                    Paragraph(iss.get("recommendation", "-"), small_s),
                ])

            issues_t = Table(issue_rows, colWidths=[4*cm, 2*cm, 6*cm, 5*cm], repeatRows=1)
            issues_t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), C_PRIMARY),
                ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
                ("FONTNAME",      (0,0), (-1,0), FB),
                ("FONTSIZE",      (0,0), (-1,0), 8.5),
                ("ALIGN",         (0,0), (-1,0), "CENTER"),
                ("VALIGN",        (0,0), (-1,-1), "TOP"),
                ("PADDING",       (0,0), (-1,-1), 6),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, C_BG_ALT]),
                ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
                ("INNERGRID",     (0,0), (-1,-1), 0.3, C_BORDER),
            ]))
            story.append(issues_t)
            story.append(Spacer(1, 8))

        if minor_issues:
            subsection("Pozostale uchybienia")
            body("Elementy wymagajace poprawy, ktore nie blokuja korzystania ze strony:")
            for iss in minor_issues:
                source = f" [{iss.get('source_file')}]" if iss.get("source_file") else ""
                body(f"&#8226; <b>{iss.get('wcag_criterion', '-')}</b>{source}: {iss.get('description', '-')}")

    # ── ④ Przygotowanie deklaracji ──
    section("Przygotowanie deklaracji dostepnosci")
    bullet([
        f"Data sporzadzenia deklaracji: {date_pl}",
        f"Data ostatniego przegladu deklaracji: {date_pl}",
    ])
    body(f"Deklaracje sporzadzono na podstawie automatycznej analizy przeprowadzonej przez "
         f"narzedzie <b>WCAG 2.1 AA Analyzer</b> (weryfikacja {total_checks} kryteriow WCAG 2.1 AA).")

    # ── ⑤ Informacje zwrotne i dane kontaktowe ──
    section("Informacje zwrotne i dane kontaktowe")
    placeholder("Uzupelnij: imie i nazwisko / komorka organizacyjna, e-mail, telefon.")
    body("Wszystkie problemy z dostepnoscia cyfrow tej strony mozesz zglosic do "
         "<b>[Imie i nazwisko / komorka]</b> - mejlowo <b>[e-mail]</b> lub telefonicznie <b>[telefon]</b>.")
    body("Kazdy ma prawo wystapic z zadaniem zapewnienia dostepnosci cyfrowej tej strony lub jej elementow.")
    bullet([
        "swoje imie i nazwisko,",
        "swoje dane kontaktowe (np. numer telefonu, e-mail),",
        "dokladny adres strony internetowej z problemem,",
        "opis problemu i preferowany sposob jego rozwiazania.",
    ])
    body("Odpowiemy nie pozniej niz w ciagu 7 dni od otrzymania zgloszenia.")

    # ── ⑥ Obsluga wnioskow i skarg ──
    section("Obsluga wnioskow i skarg zwiazanych z dostepnoscia")
    body("Jezeli nie zgadzasz sie z odmowa zapewnienia dostepnosci cyfrowej lub "
         "z zaproponowanym alternatywnym sposobem dostepu, masz prawo zlozyc skarge.")
    placeholder("Uzupelnij: dane kierownictwa urzedu (adres, e-mail) do zlozenia skargi.")
    body("Mozesz takze poinformowac o tej sytuacji Rzecznika Praw Obywatelskich "
         "(https://bip.brpo.gov.pl/) i poprosic o interwencje.")

    # ── ⑦ Pozostale informacje ──
    section("Pozostale informacje")
    subsection("Dostepnosc architektoniczna")
    placeholder("Uzupelnij: opis dostepnosci architektonicznej siedziby glownej podmiotu.")
    subsection("Dostepnosc komunikacyjno-informacyjna")
    placeholder("Uzupelnij: informacje o tlumaczu jezyka migowego i dostepnosci komunikacyjnej.")

    # ── Stopka ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Raport wygenerowany przez WCAG 2.1 AA Analyzer | {date_pl} | Plik: {filename}",
        footer_s
    ))
    story.append(Paragraph(
        "Struktura dokumentu zgodna z: Warunki techniczne publikacji i struktura "
        "dokumentu elektronicznego deklaracji dostepnosci "
        "(Ministerstwo Cyfryzacji, wersja 2.0, 2024).",
        footer_s
    ))

    doc.build(story)
    return buf.getvalue()
