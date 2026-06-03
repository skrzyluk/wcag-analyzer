"""
issue_mapper.py - Mapowanie wynikow WCAGValidator na wiersze raportu Excel.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.data.wcag_descriptions import WCAG_CRITERIA

Severity = Literal["critical", "major", "minor", "warning"]
Status   = Literal["KRYTYCZNE", "NOWE", "WSPOLNE", "OK"]


@dataclass
class AffectedElement:
    tag:          str = ""
    html_snippet: str = ""
    html_after:   str = ""


@dataclass
class Issue:
    id:               str
    wcag_criterion:   str
    severity:         str
    description:      str
    recommendation:   str
    affected_elements: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Issue":
        elements = [
            AffectedElement(
                tag=e.get("tag", ""),
                html_snippet=e.get("html_snippet", ""),
                html_after=e.get("html_after", ""),
            )
            for e in d.get("affected_elements", [])
        ]
        return cls(
            id=str(d.get("id", "")),
            wcag_criterion=d.get("wcag_criterion", ""),
            severity=d.get("severity", "minor"),
            description=d.get("description", ""),
            recommendation=d.get("recommendation", ""),
            affected_elements=elements,
        )


@dataclass
class ExcelRow:
    id:                str
    status:            str
    obszar:            str
    element:           str
    kryterium:         str
    poziom:            str
    opis_ze_standardu: str
    problem:           str
    naprawa:           str
    fragment_kodu:     str = ""
    fragment_kodu_po:  str = ""

    def as_tuple(self) -> tuple:
        return (
            self.id,
            self.status,
            self.obszar,
            self.element,
            self.kryterium,
            self.poziom,
            self.opis_ze_standardu,
            self.problem,
            self.naprawa,
            self.fragment_kodu,
            self.fragment_kodu_po,
        )


@dataclass
class SeparatorRow:
    section_name: str
    section_id:   str


@dataclass
class PageResult:
    sheet_name:  str
    title:       str
    description: str
    prefix:      str
    rows:        list = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        return sum(1 for r in self.rows if isinstance(r, ExcelRow))

    @property
    def critical_count(self) -> int:
        return sum(1 for r in self.rows if isinstance(r, ExcelRow) and r.status == "KRYTYCZNE")


_CRITERION_ID_RE = re.compile(r"(\d+\.\d+\.\d+)")


# ---------------------------------------------------------------------------
# Prefiksy ID — stale mapowanie per-podstrona (decyzja projektowa, §4.5)
# ---------------------------------------------------------------------------
#: Identyfikator podstrony (fragment nazwy pliku / sciezki, lowercase)
#: -> 4-znakowy, unikalny prefiks ID. Dopisuj kolejne podstrony tutaj.
PAGE_PREFIXES: dict[str, str] = {
    "my":         "KPLT",   # Kokpit uzytkownika (/my/)
    "kokpit":     "KPLT",
    "dashboard":  "KPLT",
    "login":      "LOG1",   # Strona logowania (/login/)
    "logowanie":  "LOG1",
}


def resolve_page_prefix(page_key: str, *, mapping: dict | None = None) -> str:
    """
    Zwraca prefiks ID dla podstrony wg stalego mapowania (PAGE_PREFIXES).

    Dopasowanie po fragmencie `page_key` (np. nazwa pliku, sciezka) —
    case-insensitive. Gdy brak wpisu w mapowaniu, generowany jest
    deterministyczny prefiks zastepczy z nazwy (aby auto-generowanie raportow
    dla dowolnych plikow pozostalo odporne); takie podstrony nalezy docelowo
    dopisac do PAGE_PREFIXES, by ID bylo trwale i jednoznaczne.
    """
    mapping = mapping if mapping is not None else PAGE_PREFIXES
    key = (page_key or "").lower()
    for needle, code in mapping.items():
        if needle and needle in key:
            return code
    derived = re.sub(r"[^A-Za-z0-9]", "", page_key or "")[:4].upper()
    return derived or "STR1"


class IssueMapper:

    SECTIONS = {"A": "R1", "AA": "R2"}

    SECTION_LABELS = {
        "R1": "Poziom A",
        "R2": "Poziom AA",
    }

    def map_page(self, issues, *, page_url="", sheet_name="Strona",
                 title="", description="", prefix="STR1"):
        normalized = [
            Issue.from_dict(i) if isinstance(i, dict) else i
            for i in issues
        ]
        buckets = {"R1": [], "R2": []}
        for issue in normalized:
            crit_id = self._extract_criterion_id(issue.wcag_criterion)
            level   = self._get_level(crit_id)
            section = self.SECTIONS.get(level, "R1")
            buckets[section].append(issue)

        rows = []
        counters = {"R1": 0, "R2": 0}
        for section_key in ("R1", "R2"):
            if not buckets[section_key]:
                continue
            rows.append(SeparatorRow(
                section_name=self.SECTION_LABELS[section_key],
                section_id=section_key,
            ))
            for issue in buckets[section_key]:
                counters[section_key] += 1
                rows.append(self._map_issue(issue, prefix, section_key, counters[section_key]))

        return PageResult(
            sheet_name=sheet_name,
            title=title or sheet_name,
            description=description or page_url,
            prefix=prefix,
            rows=rows,
        )

    def _map_issue(self, issue, prefix, section, counter):
        crit_id   = self._extract_criterion_id(issue.wcag_criterion)
        criterion = WCAG_CRITERIA.get(crit_id)
        poziom    = criterion["level"] if criterion else ""
        obszar    = self._format_obszar(criterion) if criterion else ""
        opis      = criterion["description"] if criterion else ""
        return ExcelRow(
            id=self.generate_id(prefix, section, counter),
            status=self.classify_status(issue.severity),
            obszar=obszar,
            element=self._extract_element(issue),
            kryterium=issue.wcag_criterion,
            poziom=poziom,
            opis_ze_standardu=opis,
            problem=issue.description,
            naprawa=issue.recommendation,
            fragment_kodu=self._extract_snippet(issue),
            fragment_kodu_po=self._extract_snippet_after(issue),
        )

    @staticmethod
    def classify_status(severity: str) -> str:
        return "KRYTYCZNE" if severity == "critical" else "NOWE"

    @staticmethod
    def generate_id(prefix: str, section: str, counter: int) -> str:
        return f"{prefix}-{section}-{counter:03d}"

    @staticmethod
    def _extract_criterion_id(wcag_criterion: str) -> str:
        m = _CRITERION_ID_RE.search(wcag_criterion or "")
        return m.group(1) if m else ""

    @staticmethod
    def _safe_get_criterion(criterion_id: str):
        if not criterion_id:
            return None
        return WCAG_CRITERIA.get(criterion_id)

    @staticmethod
    def _get_level(criterion_id: str) -> str:
        c = WCAG_CRITERIA.get(criterion_id)
        return c["level"] if c else "A"

    @staticmethod
    def _format_obszar(criterion: dict) -> str:
        num  = criterion.get("pillar_num", "")
        name = criterion.get("pillar", "")
        if num and name:
            return f"{num}. {name}"
        return name or ""

    @staticmethod
    def _extract_element(issue) -> str:
        if issue.affected_elements:
            tag = issue.affected_elements[0].tag
            if tag:
                return f"<{tag}>"
        return ""

    @staticmethod
    def _extract_snippet(issue) -> str:
        if issue.affected_elements:
            return issue.affected_elements[0].html_snippet or ""
        return ""

    @staticmethod
    def _extract_snippet_after(issue) -> str:
        if issue.affected_elements:
            return issue.affected_elements[0].html_after or ""
        return ""
