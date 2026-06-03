"""
test_issue_mapper.py — Testy jednostkowe dla modułu IssueMapper.

Uruchamianie:
    cd backend
    pytest tests/test_issue_mapper.py -v
"""

import pytest
from app.services.issue_mapper import (
    AffectedElement,
    ExcelRow,
    Issue,
    IssueMapper,
    PageResult,
    SeparatorRow,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mapper() -> IssueMapper:
    return IssueMapper()


@pytest.fixture
def issue_critical() -> Issue:
    return Issue(
        id="i1",
        wcag_criterion="1.1.1 Treść nietekstowa",
        severity="critical",
        description="Obraz bez atrybutu alt.",
        recommendation='Dodaj alt="" lub opisowy tekst alternatywny.',
        affected_elements=[
            AffectedElement(
                tag="img",
                html_snippet="<img src='logo.png'>",
                html_after='<img src="logo.png" alt="Logo firmy">',
            )
        ],
    )


@pytest.fixture
def issue_major() -> Issue:
    return Issue(
        id="i2",
        wcag_criterion="2.4.7 Widoczność fokusu",
        severity="major",
        description="Brak widocznego wskaźnika fokusu.",
        recommendation="Usuń outline:none lub dodaj styl :focus-visible.",
        affected_elements=[],
    )


@pytest.fixture
def issue_minor() -> Issue:
    return Issue(
        id="i3",
        wcag_criterion="3.1.1 Język strony",
        severity="minor",
        description="Brak atrybutu lang na elemencie <html>.",
        recommendation='Dodaj <html lang="pl">.',
        affected_elements=[
            AffectedElement(tag="html", html_snippet="<html>")
        ],
    )


@pytest.fixture
def issue_aa() -> Issue:
    """Kryterium poziomu AA."""
    return Issue(
        id="i4",
        wcag_criterion="1.4.3 Kontrast (minimalny)",
        severity="major",
        description="Niewystarczający kontrast tekstu.",
        recommendation="Zapewnij współczynnik kontrastu co najmniej 4,5:1.",
        affected_elements=[
            AffectedElement(tag="p", html_snippet='<p style="color:#aaa">Tekst</p>')
        ],
    )


# ---------------------------------------------------------------------------
# Testy: Issue.from_dict
# ---------------------------------------------------------------------------

class TestIssueFromDict:
    def test_basic_fields(self):
        d = {
            "id": "i1",
            "wcag_criterion": "1.1.1 Treść nietekstowa",
            "severity": "critical",
            "description": "Obraz bez alt.",
            "recommendation": "Dodaj alt.",
            "affected_elements": [{"tag": "img", "html_snippet": "<img>"}],
        }
        issue = Issue.from_dict(d)
        assert issue.id == "i1"
        assert issue.severity == "critical"
        assert len(issue.affected_elements) == 1
        assert issue.affected_elements[0].tag == "img"

    def test_missing_elements(self):
        d = {
            "id": "x",
            "wcag_criterion": "2.1.1 Klawiatura",
            "severity": "minor",
            "description": "Opis",
            "recommendation": "Naprawa",
        }
        issue = Issue.from_dict(d)
        assert issue.affected_elements == []

    def test_html_after_field(self):
        d = {
            "id": "x",
            "wcag_criterion": "1.1.1 Treść",
            "severity": "critical",
            "description": "d",
            "recommendation": "r",
            "affected_elements": [
                {"tag": "img", "html_snippet": "<img>", "html_after": '<img alt="ok">'}
            ],
        }
        issue = Issue.from_dict(d)
        assert issue.affected_elements[0].html_after == '<img alt="ok">'


# ---------------------------------------------------------------------------
# Testy: classify_status
# ---------------------------------------------------------------------------

class TestClassifyStatus:
    def test_critical_maps_to_krytyczne(self, mapper):
        assert mapper.classify_status("critical") == "KRYTYCZNE"

    def test_major_maps_to_nowe(self, mapper):
        assert mapper.classify_status("major") == "NOWE"

    def test_minor_maps_to_nowe(self, mapper):
        assert mapper.classify_status("minor") == "NOWE"

    def test_warning_maps_to_nowe(self, mapper):
        assert mapper.classify_status("warning") == "NOWE"


# ---------------------------------------------------------------------------
# Testy: generate_id
# ---------------------------------------------------------------------------

class TestGenerateId:
    def test_format_r1(self, mapper):
        assert mapper.generate_id("LOG1", "R1", 1) == "LOG1-R1-001"

    def test_format_r2_zero_padding(self, mapper):
        assert mapper.generate_id("KPLT", "R2", 42) == "KPLT-R2-042"

    def test_three_digit_counter(self, mapper):
        assert mapper.generate_id("STR1", "R1", 100) == "STR1-R1-100"


# ---------------------------------------------------------------------------
# Testy: _extract_criterion_id
# ---------------------------------------------------------------------------

class TestExtractCriterionId:
    @pytest.mark.parametrize("criterion,expected", [
        ("1.1.1 Treść nietekstowa", "1.1.1"),
        ("2.4.7 Widoczność fokusu", "2.4.7"),
        ("3.1.1 Język strony",      "3.1.1"),
        ("1.4.3",                   "1.4.3"),
        ("SC 2.1.1",                "2.1.1"),
        ("",                        ""),
        ("brak ID",                 ""),
    ])
    def test_extraction(self, criterion, expected):
        assert IssueMapper._extract_criterion_id(criterion) == expected


# ---------------------------------------------------------------------------
# Testy: map_page — wynik ogólny
# ---------------------------------------------------------------------------

class TestMapPage:
    def test_returns_page_result(self, mapper, issue_critical):
        result = mapper.map_page(
            issues=[issue_critical],
            sheet_name="Test",
            prefix="TST1",
        )
        assert isinstance(result, PageResult)
        assert result.sheet_name == "Test"
        assert result.prefix == "TST1"

    def test_empty_issues_returns_empty_rows(self, mapper):
        result = mapper.map_page(issues=[], prefix="TST1")
        assert result.rows == []

    def test_row_count_matches_issues(self, mapper, issue_critical, issue_major, issue_minor):
        result = mapper.map_page(
            issues=[issue_critical, issue_major, issue_minor],
            prefix="TST1",
        )
        data_rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert len(data_rows) == 3

    def test_issue_count_property(self, mapper, issue_critical, issue_major):
        result = mapper.map_page(issues=[issue_critical, issue_major], prefix="X")
        assert result.issue_count == 2

    def test_critical_count_property(self, mapper, issue_critical, issue_major):
        result = mapper.map_page(issues=[issue_critical, issue_major], prefix="X")
        assert result.critical_count == 1


# ---------------------------------------------------------------------------
# Testy: map_page — separatory sekcji
# ---------------------------------------------------------------------------

class TestSeparators:
    def test_separator_added_for_level_a(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        separators = [r for r in result.rows if isinstance(r, SeparatorRow)]
        assert any(r.section_id == "R1" for r in separators)

    def test_separator_added_for_level_aa(self, mapper, issue_aa):
        result = mapper.map_page(issues=[issue_aa], prefix="TST1")
        separators = [r for r in result.rows if isinstance(r, SeparatorRow)]
        assert any(r.section_id == "R2" for r in separators)

    def test_no_separator_for_empty_section(self, mapper, issue_critical):
        # issue_critical to kryterium A — nie powinno być separatora R2
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        separators = [r for r in result.rows if isinstance(r, SeparatorRow)]
        assert not any(r.section_id == "R2" for r in separators)

    def test_r1_before_r2(self, mapper, issue_critical, issue_aa):
        result = mapper.map_page(issues=[issue_aa, issue_critical], prefix="TST1")
        sep_ids = [r.section_id for r in result.rows if isinstance(r, SeparatorRow)]
        assert sep_ids == ["R1", "R2"]


# ---------------------------------------------------------------------------
# Testy: ExcelRow — pola
# ---------------------------------------------------------------------------

class TestExcelRow:
    def test_critical_issue_status(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].status == "KRYTYCZNE"

    def test_major_issue_status(self, mapper, issue_major):
        result = mapper.map_page(issues=[issue_major], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].status == "NOWE"

    def test_kryterium_field(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].kryterium == "1.1.1 Treść nietekstowa"

    def test_element_tag_with_brackets(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].element == "<img>"

    def test_element_empty_when_no_affected(self, mapper, issue_major):
        result = mapper.map_page(issues=[issue_major], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].element == ""

    def test_fragment_kodu(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].fragment_kodu == "<img src='logo.png'>"

    def test_fragment_kodu_po(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].fragment_kodu_po == '<img src="logo.png" alt="Logo firmy">'

    def test_obszar_format(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        # kryterium 1.1.1 → Filar 1 → "1. Postrzegalność"
        assert rows[0].obszar.startswith("1.")
        assert "Postrzegalno" in rows[0].obszar

    def test_poziom_a_for_criterion_111(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].poziom == "A"

    def test_poziom_aa_for_criterion_143(self, mapper, issue_aa):
        result = mapper.map_page(issues=[issue_aa], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].poziom == "AA"

    def test_opis_ze_standardu_not_empty_for_known_criterion(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert len(rows[0].opis_ze_standardu) > 10

    def test_id_format(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="LOG1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert rows[0].id == "LOG1-R1-001"

    def test_id_increments_within_section(self, mapper, issue_critical, issue_minor):
        # Oba kyteria (1.1.1 i 3.1.1) są poziom A → oba w R1
        result = mapper.map_page(issues=[issue_critical, issue_minor], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        ids = [r.id for r in rows]
        assert "TST1-R1-001" in ids
        assert "TST1-R1-002" in ids

    def test_as_tuple_returns_11_elements(self, mapper, issue_critical):
        result = mapper.map_page(issues=[issue_critical], prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        t = rows[0].as_tuple()
        assert len(t) == 11


# ---------------------------------------------------------------------------
# Testy: from_dict — integracja z map_page
# ---------------------------------------------------------------------------

class TestFromDictIntegration:
    def test_map_page_accepts_dicts(self, mapper):
        raw_issues = [
            {
                "id": "i1",
                "wcag_criterion": "1.1.1 Treść nietekstowa",
                "severity": "critical",
                "description": "Brak alt.",
                "recommendation": "Dodaj alt.",
                "affected_elements": [{"tag": "img", "html_snippet": "<img>"}],
            }
        ]
        result = mapper.map_page(issues=raw_issues, prefix="TST1")
        rows = [r for r in result.rows if isinstance(r, ExcelRow)]
        assert len(rows) == 1
        assert rows[0].status == "KRYTYCZNE"

    def test_mixed_dicts_and_dataclasses(self, mapper, issue_major):
        raw = {
            "id": "x",
            "wcag_criterion": "1.1.1 Treść",
            "severity": "critical",
            "description": "d",
            "recommendation": "r",
            "affected_elements": [],
        }
        result = mapper.map_page(issues=[raw, issue_major], prefix="M")
        assert result.issue_count == 2
