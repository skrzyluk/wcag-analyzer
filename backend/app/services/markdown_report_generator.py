"""
markdown_report_generator.py - Zbiorczy raport audytowy WCAG 2.1 AA w formacie Markdown.

Agreguje wyniki ze wszystkich przeanalizowanych podstron i buduje jeden, bardzo
szczegolowy dokument Markdown odwzorowujacy strukture formalnego raportu z oceny
dostepnosci cyfrowej (wg ustawy z 4 kwietnia 2019 r. + WCAG 2.1 AA). Dokument jest
przeznaczony jako material zrodlowy do odtworzenia raportu Word przy pomocy czatu Claude.

API (spojne z pozostalymi generatorami):
    MarkdownReportGenerator().generate(reports, meta=None) -> str
    MarkdownReportGenerator().generate_bytes(reports, meta=None) -> bytes
    MarkdownReportGenerator().generate_file(reports, path, meta=None) -> str

`reports` = lista slownikow analizy (kształt z _store): filename, page_title,
page_url, summary, issues[]. Dla pojedynczej analizy przekazuje sie [r].
"""

from __future__ import annotations

import datetime
import re
from typing import Iterable

from app.data.wcag_descriptions import WCAG_CRITERIA, PILLAR_NAMES

# ---------------------------------------------------------------------------
# Stale
# ---------------------------------------------------------------------------

_CRITERION_ID_RE = re.compile(r"(\d+\.\d+\.\d+)")

#: Baseline kryteriow wg zalacznika do ustawy o dostepnosci cyfrowej (WCAG 2.1 A+AA).
#: We wzorze raportu uzyto 49; dataset WCAG_CRITERIA zawiera 50 kryteriow A+AA.
LEGAL_BASELINE_CRITERIA = 49

#: Ranking severity (wyzszy = powazniejszy) — do wyznaczania priorytetu i sortowania.
_SEVERITY_RANK = {"critical": 3, "major": 2, "minor": 1, "warning": 0}
_SEVERITY_LABEL = {
    "critical": "KRYTYCZNY",
    "major":    "POWAZNY",
    "minor":    "DROBNY",
    "warning":  "OSTRZEZENIE",
}

#: Kryteria faktycznie sprawdzane przez WCAGValidator (metody check_* w validate()).
#: Sluzy do wyznaczenia sekcji "dobre praktyki" = sprawdzone bez naruszen.
CHECKED_CRITERIA = [
    "1.1.1", "1.3.1", "1.3.2", "1.3.4", "1.3.5", "1.4.1", "1.4.3",
    "2.1.1", "2.4.1", "2.4.2", "2.4.3", "2.4.4", "2.4.6",
    "3.1.1", "3.1.2", "3.2.1", "3.3.1", "3.3.2",
    "4.1.1", "4.1.2",
]

#: Pelne nazwy wytycznych WCAG 2.1 (poziom "x.y"). Dataset nie ma pola guideline.
GUIDELINE_NAMES = {
    "1.1": "Alternatywa tekstowa",
    "1.2": "Multimedia",
    "1.3": "Możliwość adaptacji",
    "1.4": "Rozróżnialność",
    "2.1": "Dostępność z klawiatury",
    "2.2": "Wystarczająca ilość czasu",
    "2.3": "Ataki padaczki i reakcje fizyczne",
    "2.4": "Możliwość nawigacji",
    "2.5": "Sposoby wprowadzania danych",
    "3.1": "Możliwość odczytania",
    "3.2": "Przewidywalność",
    "3.3": "Pomoc przy wprowadzaniu informacji",
    "4.1": "Kompatybilność",
}

# --- Statyczne szablony tresci prawnej (boilerplate) ----------------------

STANDARDS_LIST = [
    "Wytyczne WCAG 2.1 na poziomie AA (https://www.w3.org/Translations/WCAG21-pl-20210413/)",
    "Ustawa z dnia 4 kwietnia 2019 r. o dostępności cyfrowej stron internetowych i aplikacji "
    "mobilnych podmiotów publicznych (Dz.U. 2023 poz. 1440)",
    "Norma EN 301 549 V2.1.2 (pkt 9, 10, 11)",
    "Metodologia WCAG-EM (Website Accessibility Conformance Evaluation Methodology)",
]

EXCLUSIONS_LIST = [
    "Treści dostarczone przez podmiot trzeci, niefinansowane ani nieopracowane przez podmiot "
    "publiczny i niepozostające pod jego kontrolą (art. 3 ust. 2 pkt 5).",
    "Dokumenty tekstowe i prezentacje opublikowane przed 23 września 2018 r. (art. 3 ust. 2 pkt 3).",
    "Multimedia nadawane na żywo (art. 3 ust. 2 pkt 1).",
    "[DO UZUPEŁNIENIA: ewentualne dalsze wyłączenia specyficzne dla audytowanego systemu]",
]

TOOLS_LIST = [
    "Przeglądarka Google Chrome (najnowsza wersja stabilna)",
    "Czytnik ekranu: NVDA (Windows)",
    "Narzędzia automatyczne: aplikacja WCAG 2.1 AA Analyzer (analiza statyczna MHTML), "
    "kontroler kontrastu WCAG, Chrome DevTools Accessibility Inspector",
    "Testowanie manualne z nawigacją klawiaturą",
    "Inspekcja kodu HTML/CSS/ARIA",
]

SYSTEMIC_RECOMMENDATIONS = [
    "Wprowadzić regułę lintera HTML/A11y do CI/CD: każdy `label for=` musi mieć odpowiadające "
    "`id=` w tym samym dokumencie.",
    "Wdrożyć automatyczne testy dostępności (axe-core) jako etap pipeline CI/CD — blokujący "
    "wdrożenie przy błędach krytycznych.",
    "Stworzyć jeden komponent tabeli danych z wbudowanym `scope=\"col\"`, `<caption>` i obsługą "
    "`aria-sort` — zastąpić nim wszystkie tabele w aplikacji.",
    "Opracować wewnętrzny Design System z komponentami dostępnymi cyfrowo jako jedynym "
    "standardem wdrożeń.",
]

STATUTORY_OBLIGATIONS = [
    "Na podstawie art. 10 ustawy podmiot publiczny jest zobowiązany do niezwłocznego "
    "sporządzenia i opublikowania deklaracji dostępności, opisującej stan zgodności oraz "
    "alternatywne sposoby dostępu.",
    "Na podstawie art. 11 ustawy podmiot publiczny jest zobowiązany do corocznego przeglądu "
    "deklaracji dostępności (do 31 marca każdego roku) oraz jej niezwłocznej aktualizacji.",
    "Na podstawie art. 7 ustawy podmiot publiczny jest zobowiązany do zapewnienia "
    "alternatywnych sposobów dostępu do niedostępnych elementów — w szczególności kontaktu.",
    "Stosownie do art. 19 ustawy, za nieuzasadnione i uporczywe niewywiązywanie się z obowiązku "
    "zapewnienia dostępności cyfrowej grozi kara pieniężna do 10 000 zł.",
]


# ---------------------------------------------------------------------------
# Pomocnicze: ekstrakcja i formatowanie
# ---------------------------------------------------------------------------

def _criterion_id(wcag_criterion: str) -> str:
    m = _CRITERION_ID_RE.search(wcag_criterion or "")
    return m.group(1) if m else ""


def _guideline_id(criterion_id: str) -> str:
    return criterion_id.rsplit(".", 1)[0] if criterion_id else ""


def _severity_of(issue: dict) -> str:
    return (issue.get("severity") or "").lower()


def _report_label(report: dict) -> str:
    """Czytelna etykieta podstrony: page_title -> stem filename -> 'Podstrona'."""
    title = (report.get("page_title") or "").strip()
    if title:
        return title
    fname = (report.get("filename") or "").strip()
    if fname:
        return fname.rsplit(".", 1)[0]
    return "Podstrona"


def _cell(text: str) -> str:
    """Bezpieczna komorka tabeli Markdown: escape '|' i zamiana nowych linii na <br>."""
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("|", "\\|").replace("\n", "<br>")
    return s.strip()


def _dedup(seq: Iterable[str]) -> list[str]:
    """Usuwa duplikaty zachowując kolejnosc; pomija puste."""
    seen: set[str] = set()
    out: list[str] = []
    for item in seq:
        item = (item or "").strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Silnik agregacji
# ---------------------------------------------------------------------------

def _aggregate(reports: list[dict]) -> dict:
    """Buduje strukture zagregowana ze wszystkich raportow."""
    # criterion_id -> dane zagregowane
    crit: dict[str, dict] = {}
    pages: list[dict] = []
    critical_issue_count = 0

    for report in reports:
        label = _report_label(report)
        pages.append({
            "label": label,
            "url": (report.get("page_url") or "").strip(),
            "filename": report.get("filename", ""),
            "summary": report.get("summary", {}) or {},
        })

        for issue in report.get("issues", []) or []:
            sev = _severity_of(issue)
            if sev == "critical":
                critical_issue_count += 1

            cid = _criterion_id(issue.get("wcag_criterion", ""))
            if not cid:
                continue
            meta = WCAG_CRITERIA.get(cid)

            entry = crit.setdefault(cid, {
                "id": cid,
                "name": meta["name"] if meta else (issue.get("wcag_criterion") or cid),
                "level": meta["level"] if meta else "",
                "pillar": meta["pillar"] if meta else "",
                "pillar_num": meta["pillar_num"] if meta else 0,
                "description": meta["description"] if meta else "",
                "guideline_id": _guideline_id(cid),
                "areas": [],
                "problems": [],
                "recommendations": [],
                "code_before": [],
                "code_after": [],
                "max_severity": "warning",
                "issue_count": 0,
            })

            entry["areas"].append(label)
            entry["problems"].append(issue.get("description", ""))
            entry["recommendations"].append(issue.get("recommendation", ""))
            entry["issue_count"] += 1
            if _SEVERITY_RANK.get(sev, 0) > _SEVERITY_RANK.get(entry["max_severity"], 0):
                entry["max_severity"] = sev

            for el in issue.get("affected_elements", []) or []:
                before = el.get("html_snippet", "") if isinstance(el, dict) else getattr(el, "html_snippet", "")
                after = el.get("html_after", "") if isinstance(el, dict) else getattr(el, "html_after", "")
                if before:
                    entry["code_before"].append(before)
                if after:
                    entry["code_after"].append(after)

    # Normalizacja list (dedup) i sortowanie kryteriow wg ID
    for entry in crit.values():
        entry["areas"] = _dedup(entry["areas"])
        entry["problems"] = _dedup(entry["problems"])
        entry["recommendations"] = _dedup(entry["recommendations"])
        entry["code_before"] = _dedup(entry["code_before"])
        entry["code_after"] = _dedup(entry["code_after"])

    def _sort_key(cid: str) -> tuple:
        parts = cid.split(".")
        return tuple(int(p) if p.isdigit() else 0 for p in parts)

    violated = [crit[cid] for cid in sorted(crit.keys(), key=_sort_key)]
    violated_ids = {e["id"] for e in violated}

    a_violated = sum(1 for e in violated if e["level"] == "A")
    aa_violated = sum(1 for e in violated if e["level"] == "AA")
    total_violated = len(violated)
    compliant = max(0, LEGAL_BASELINE_CRITERIA - total_violated)
    compliant_pct = round(100.0 * compliant / LEGAL_BASELINE_CRITERIA) if LEGAL_BASELINE_CRITERIA else 0

    # Stan dostepnosci
    if total_violated == 0:
        stan = "ZGODNA"
    elif critical_issue_count == 0 and compliant_pct >= 80:
        stan = "CZĘŚCIOWO ZGODNA"
    else:
        stan = "NIEZGODNA"

    # Rozklad wg zasad (pillar_num 1..4)
    pillars = []
    for num in (1, 2, 3, 4):
        ids = sorted((e["id"] for e in violated if e["pillar_num"] == num), key=_sort_key)
        pillars.append({
            "num": num,
            "name": PILLAR_NAMES.get(num, ""),
            "count": len(ids),
            "ids": ids,
        })

    # Dobre praktyki: sprawdzone bez naruszen
    good = []
    for cid in sorted(CHECKED_CRITERIA, key=_sort_key):
        if cid in violated_ids:
            continue
        meta = WCAG_CRITERIA.get(cid)
        if not meta:
            continue
        good.append({"id": cid, "name": meta["name"], "level": meta["level"]})

    # Rekomendacje wg priorytetu (severity -> P1/P2/P3)
    prio = {1: [], 2: [], 3: []}
    for e in violated:
        sev = e["max_severity"]
        p = 1 if sev == "critical" else (2 if sev == "major" else 3)
        prio[p].append(e)

    return {
        "pages": pages,
        "violated": violated,
        "a_violated": a_violated,
        "aa_violated": aa_violated,
        "total_violated": total_violated,
        "compliant": compliant,
        "compliant_pct": compliant_pct,
        "critical_issue_count": critical_issue_count,
        "stan": stan,
        "pillars": pillars,
        "good": good,
        "priorities": prio,
    }


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class MarkdownReportGenerator:
    """Buduje zbiorczy raport audytowy WCAG 2.1 AA w formacie Markdown."""

    def generate(self, reports: list[dict], *, meta: dict | None = None) -> str:
        meta = meta or {}
        agg = _aggregate(reports or [])
        date_str = meta.get("date") or self._today()
        ph = lambda key, hint: meta.get(key) or f"[DO UZUPEŁNIENIA: {hint}]"

        out: list[str] = []
        w = out.append

        # --- Instrukcja dla modelu (Claude) ---
        w(self._intro_block())

        # --- Naglowek + metadane ---
        w("# RAPORT Z OCENY DOSTĘPNOŚCI CYFROWEJ")
        w(f"### {ph('subject', 'nazwa / opis audytowanego systemu')}")
        w("zgodnie z wymaganiami WCAG 2.1 na poziomie AA")
        w(f"**Data sporządzenia:** {date_str}")
        w("")
        w("| Pozycja | Wartość |")
        w("|---------|---------|")
        w(f"| Wykonawca / Audytor | {_cell(ph('auditor', 'nazwa i adres wykonawcy audytu'))} |")
        w(f"| Przedmiot oceny | {_cell(ph('subject', 'nazwa / opis audytowanego systemu'))} |")
        w(f"| Podmiot publiczny | {_cell(ph('entity', 'nazwa podmiotu publicznego'))} |")
        w(f"| URL systemu | {_cell(ph('url', 'adres URL audytowanego systemu'))} |")
        w(f"| Data sporządzenia | {_cell(date_str)} |")
        w("| Standard odniesienia | WCAG 2.1 poziom AA (załącznik do ustawy z 4 kwietnia 2019 r.) |")
        w("| Metodologia | WCAG-EM (Website Accessibility Conformance Evaluation Methodology) |")
        w(f"| Stan dostępności | **{agg['stan']}** z załącznikiem do ustawy |")
        w("")

        # --- §1 Streszczenie wykonawcze ---
        w("# 1. Streszczenie wykonawcze")
        w(f"**Stan dostępności cyfrowej: {agg['stan']}** z załącznikiem do ustawy z dnia "
          "4 kwietnia 2019 r. o dostępności cyfrowej stron internetowych i aplikacji mobilnych "
          "podmiotów publicznych.")
        w("")
        w(self._exec_summary_narrative(agg))
        w("")

        w("## Wyniki ilościowe")
        w("| Kryterium sukcesu WCAG 2.1 AA | Liczba | Udział |")
        w("|-------------------------------|--------|--------|")
        w(f"| Kryteria OGÓŁEM (załącznik do ustawy) | {LEGAL_BASELINE_CRITERIA} | 100% |")
        w(f"| Kryteria NARUSZONE (poziom A) | {agg['a_violated']} | "
          f"{self._pct(agg['a_violated'])} |")
        w(f"| Kryteria NARUSZONE (poziom AA) | {agg['aa_violated']} | "
          f"{self._pct(agg['aa_violated'])} |")
        w(f"| Kryteria NARUSZONE ŁĄCZNIE | {agg['total_violated']} | "
          f"{self._pct(agg['total_violated'])} |")
        w(f"| Kryteria ZGODNE (potwierdzone) | {agg['compliant']} | "
          f"{agg['compliant_pct']}% |")
        w(f"| Błędy KRYTYCZNE (uniemożliwiające dostęp AT) | {agg['critical_issue_count']} | — |")
        w("")

        w("## Kluczowe wnioski")
        for i, line in enumerate(self._key_findings(agg), 1):
            w(f"{i}. {line}")
        w("")

        w("## Rozkład błędów według zasad WCAG")
        for p in agg["pillars"]:
            ids = ", ".join(p["ids"]) if p["ids"] else "brak naruszeń"
            w(f"- **{p['name']}**: {p['count']} kryteriów z naruszeniami ({ids}).")
        w("")

        # --- §2 Cel i zakres ---
        w("# 2. Cel i zakres audytu")
        w("Niniejszy raport stanowi wynik audytu dostępności cyfrowej audytowanego systemu "
          "przeprowadzonego zgodnie z wymaganiami WCAG 2.1 na poziomie AA oraz ustawą "
          "o dostępności cyfrowej. [DO UZUPEŁNIENIA: kontekst i cel audytu]")
        w("")
        w("## Standardy i normy")
        for s in STANDARDS_LIST:
            w(f"- {s}")
        w("")
        w("## Podstrony objęte audytem")
        for pg in agg["pages"]:
            url = f" — {pg['url']}" if pg["url"] else ""
            w(f"- {pg['label']}{url}")
        w("")
        w("## Wyłączenia")
        w("Zgodnie z art. 3 ust. 2 ustawy o dostępności cyfrowej, następujące treści nie są "
          "objęte niniejszym audytem:")
        for s in EXCLUSIONS_LIST:
            w(f"- {s}")
        w("")
        w("## Narzędzia i środowisko testowe")
        for s in TOOLS_LIST:
            w(f"- {s}")
        w("")

        # --- §3 Stan dostepnosci i wyniki ---
        w("# 3. Stan dostępności cyfrowej i wyniki audytu")
        w(f"Na podstawie przeprowadzonego badania stwierdza się, że audytowany system jest "
          f"**{agg['stan'].lower()}** z załącznikiem do ustawy. Stwierdzono naruszenia w "
          f"{agg['total_violated']} z {LEGAL_BASELINE_CRITERIA} kryteriów "
          f"({self._pct(agg['total_violated'])}); poziom zgodności wynosi co najmniej "
          f"{agg['compliant_pct']}%.")
        w("")

        w("## 3.1. Szczegółowe wyniki per kryterium sukcesu")
        if agg["violated"]:
            w("| Zasada | Wytyczna | Kryterium sukcesu | Poz. | Dotknięty obszar | Opis błędu |")
            w("|--------|----------|-------------------|------|------------------|------------|")
            for e in agg["violated"]:
                guideline = f"{e['guideline_id']} {GUIDELINE_NAMES.get(e['guideline_id'], '')}".strip()
                kryterium = f"{e['id']} {e['name']}".strip()
                areas = ", ".join(e["areas"])
                opis = "; ".join(e["problems"])[:400]
                w(f"| {_cell(e['pillar'])} | {_cell(guideline)} | {_cell(kryterium)} | "
                  f"{_cell(e['level'])} | {_cell(areas)} | {_cell(opis)} |")
            w("")

            # Zalacznik szczegolowy
            w("### Załącznik 3.1 — szczegóły naruszeń (opis, naprawa, kod)")
            for e in agg["violated"]:
                w(f"#### {e['id']} {e['name']} ({e['level']}) — {e['pillar']}")
                w(f"- **Dotknięte obszary:** {', '.join(e['areas'])}")
                w(f"- **Liczba wystąpień:** {e['issue_count']} | "
                  f"**Najwyższa severity:** {_SEVERITY_LABEL.get(e['max_severity'], e['max_severity'])}")
                if e["description"]:
                    w(f"- **Opis ze standardu:** {e['description']}")
                if e["problems"]:
                    w("- **Problem:**")
                    for p in e["problems"]:
                        w(f"  - {p}")
                if e["recommendations"]:
                    w("- **Naprawa:**")
                    for rcm in e["recommendations"]:
                        w(f"  - {rcm}")
                if e["code_before"]:
                    w("- **Fragment kodu (przed):**")
                    w("  ```html")
                    for c in e["code_before"][:5]:
                        w(f"  {c}")
                    w("  ```")
                if e["code_after"]:
                    w("- **Fragment kodu (po naprawie):**")
                    w("  ```html")
                    for c in e["code_after"][:5]:
                        w(f"  {c}")
                    w("  ```")
                w("")
        else:
            w("Nie wykryto naruszeń kryteriów sukcesu WCAG 2.1 AA w analizowanych podstronach.")
            w("")

        w("## 3.2. Elementy spełnione — dobre praktyki")
        w("Poniższe kryteria zostały sprawdzone i nie wykryto w nich naruszeń — stanowią "
          "wzorce do replikacji przy naprawie pozostałych komponentów.")
        if agg["good"]:
            w("| Kryterium | Nazwa | Poz. | Komentarz |")
            w("|-----------|-------|------|-----------|")
            for g in agg["good"]:
                w(f"| {g['id']} | {_cell(g['name'])} | {g['level']} | "
                  "Sprawdzone automatycznie — brak naruszeń |")
        else:
            w("_Brak kryteriów sprawdzonych bez naruszeń._")
        w("")

        # --- §4 Rekomendacje ---
        w("# 4. Rekomendacje i priorytety naprawcze")
        labels = {
            1: ("Priorytet 1 — Błędy krytyczne (termin: do 3 miesięcy)",
                "Błędy blokujące dostęp technologii wspomagających (AT) do kluczowych funkcji. "
                "Wymagają natychmiastowej naprawy."),
            2: ("Priorytet 2 — Błędy poważne (termin: do 6 miesięcy)",
                "Błędy istotnie ograniczające dostęp, ale nie blokujące go całkowicie."),
            3: ("Priorytet 3 — Błędy do refaktoryzacji (termin: do 12 miesięcy)",
                "Błędy o niższym wpływie lub wymagające większych zmian architektonicznych."),
        }
        for p in (1, 2, 3):
            heading, desc = labels[p]
            w(f"## {heading}")
            w(desc)
            entries = agg["priorities"][p]
            if entries:
                for e in entries:
                    recs = "; ".join(e["recommendations"]) or "[DO UZUPEŁNIENIA: rekomendacja]"
                    w(f"- **{e['id']} {e['name']}** ({', '.join(e['areas'])}): {recs}")
            else:
                w("- _Brak pozycji w tym priorytecie._")
            w("")
        w("## Rekomendacje systemowe")
        for s in SYSTEMIC_RECOMMENDATIONS:
            w(f"- {s}")
        w("")

        # --- §5 Podsumowanie ---
        w("# 5. Podsumowanie i wnioski")
        w(self._conclusion_narrative(agg))
        w("")
        w("## Obowiązki ustawowe")
        for s in STATUTORY_OBLIGATIONS:
            w(f"- {s}")
        w("")
        w("## Dane osoby sporządzającej raport")
        w("| Pozycja | Wartość |")
        w("|---------|---------|")
        w(f"| Imię i nazwisko | {_cell(ph('author_name', 'imię i nazwisko audytora'))} |")
        w(f"| Stanowisko | {_cell(ph('author_role', 'stanowisko'))} |")
        w(f"| Firma | {_cell(ph('auditor', 'nazwa firmy audytora'))} |")
        w(f"| Data | {_cell(date_str)} |")
        w("")
        w("___________________________________")
        w("(podpis osoby sporządzającej raport)")
        w("")

        return "\n".join(out).rstrip() + "\n"

    # -- API plikowe / bajtowe ------------------------------------------

    def generate_bytes(self, reports: list[dict], *, meta: dict | None = None) -> bytes:
        return self.generate(reports, meta=meta).encode("utf-8")

    def generate_file(self, reports: list[dict], path: str, *, meta: dict | None = None) -> str:
        text = self.generate(reports, meta=meta)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    # -- Fragmenty narracyjne -------------------------------------------

    @staticmethod
    def _today() -> str:
        return datetime.date.today().strftime("%d.%m.%Y r.")

    @staticmethod
    def _pct(violated: int) -> str:
        if not LEGAL_BASELINE_CRITERIA:
            return "—"
        return f"{round(100.0 * violated / LEGAL_BASELINE_CRITERIA, 1)}%".replace(".", ",")

    @staticmethod
    def _intro_block() -> str:
        return (
            "<!-- INSTRUKCJA DLA MODELU (Claude) — można usunąć po wygenerowaniu raportu Word.\n"
            "Ten plik to zbiorczy, automatycznie wygenerowany materiał źródłowy z audytu WCAG 2.1 AA.\n"
            "Na jego podstawie odtwórz formalny raport w dokumencie Word o strukturze:\n"
            "  1. Streszczenie wykonawcze (z tabelą wyników ilościowych),\n"
            "  2. Cel i zakres audytu, 3. Stan dostępności i wyniki (tabela per kryterium +\n"
            "  dobre praktyki), 4. Rekomendacje (Priorytet 1/2/3), 5. Podsumowanie i obowiązki ustawowe.\n"
            "Zachowaj wszystkie dane liczbowe i tabele. Pola [DO UZUPEŁNIENIA: ...] zastąp danymi\n"
            "podmiotu/audytora. Rozwiń narrację prawną i wnioski w oparciu o przedstawione dane.\n"
            "-->\n"
        )

    @staticmethod
    def _exec_summary_narrative(agg: dict) -> str:
        n_pages = len(agg["pages"])
        return (
            f"Audyt dostępności cyfrowej objął {n_pages} "
            f"{'podstronę' if n_pages == 1 else 'podstron'} i wykazał naruszenia w "
            f"{agg['total_violated']} z {LEGAL_BASELINE_CRITERIA} kryteriów sukcesu WCAG 2.1 AA "
            f"({MarkdownReportGenerator._pct(agg['total_violated'])}). Zidentyfikowano "
            f"{agg['critical_issue_count']} błędów krytycznych, uniemożliwiających użytkownikom "
            "technologii wspomagających (czytniki ekranu, nawigacja klawiaturą) korzystanie "
            "z kluczowych funkcji. [DO UZUPEŁNIENIA: rozwinięcie kontekstu i skutków biznesowych]"
        )

    @staticmethod
    def _key_findings(agg: dict) -> list[str]:
        findings = [
            f"System narusza {agg['total_violated']} z {LEGAL_BASELINE_CRITERIA} kryteriów "
            f"sukcesu WCAG 2.1 ({MarkdownReportGenerator._pct(agg['total_violated'])}). "
            f"Poziom zgodności wynosi co najmniej {agg['compliant_pct']}%.",
            f"Zidentyfikowano {agg['critical_issue_count']} błędów krytycznych, blokujących "
            "dostęp dla użytkowników technologii wspomagających.",
        ]
        top = [p for p in agg["pillars"] if p["count"] > 0]
        top.sort(key=lambda p: p["count"], reverse=True)
        if top:
            worst = top[0]
            findings.append(
                f"Najwięcej naruszeń dotyczy zasady „{worst['name']}” "
                f"({worst['count']} kryteriów: {', '.join(worst['ids'])})."
            )
        if agg["good"]:
            findings.append(
                "Pozytywnym elementem są poprawnie wdrożone kryteria: "
                f"{', '.join(g['id'] for g in agg['good'])} — wzorce te należy replikować."
            )
        findings.append(
            "[DO UZUPEŁNIENIA: wnioski jakościowe — np. systemowy charakter błędów, "
            "priorytety naprawcze, ryzyka prawne]"
        )
        return findings

    @staticmethod
    def _conclusion_narrative(agg: dict) -> str:
        return (
            f"Audytowany system wykazuje stan dostępności: **{agg['stan']}**. Stwierdzone błędy "
            f"({agg['total_violated']} naruszonych kryteriów, w tym {agg['critical_issue_count']} "
            "krytycznych) mają w znacznej części charakter systemowy — naprawa w szablonie "
            "aplikacji pozwoli usunąć problem na wielu podstronach jednocześnie. System wymaga "
            "prac naprawczych zgodnie z priorytetami z rozdziału 4. "
            "[DO UZUPEŁNIENIA: ocena końcowa, harmonogram, rekomendacja dla podmiotu]"
        )
