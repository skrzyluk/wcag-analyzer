"""
test_markdown_report_generator.py - Testy jednostkowe dla MarkdownReportGenerator.

Uruchamianie:
    cd backend
    pytest tests/test_markdown_report_generator.py -v
"""

import pytest

from app.services.markdown_report_generator import (
    MarkdownReportGenerator,
    LEGAL_BASELINE_CRITERIA,
    CHECKED_CRITERIA,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_issue(criterion, severity="major", desc="Opis problemu", rec="Rekomendacja",
               tag="", before="", after=""):
    affected = []
    if tag or before or after:
        affected.append({"tag": tag, "html_snippet": before, "html_after": after})
    return {
        "wcag_criterion": criterion,
        "severity": severity,
        "description": desc,
        "recommendation": rec,
        "affected_elements": affected,
    }


def make_report(page_title="Kokpit", filename="kokpit.mhtml", page_url="https://x/my/",
                issues=None, summary=None):
    return {
        "filename": filename,
        "page_title": page_title,
        "page_url": page_url,
        "status": "completed",
        "summary": summary or {},
        "issues": issues or [],
    }


def gen(reports, meta=None):
    return MarkdownReportGenerator().generate(reports, meta=meta)


# ---------------------------------------------------------------------------
# Struktura dokumentu
# ---------------------------------------------------------------------------

class TestStructure:
    def test_all_sections_present(self):
        md = gen([make_report(issues=[make_issue("1.1.1 Treść nietekstowa", "critical")])])
        for heading in (
            "# 1. Streszczenie wykonawcze",
            "# 2. Cel i zakres audytu",
            "# 3. Stan dostępności cyfrowej i wyniki audytu",
            "## 3.1. Szczegółowe wyniki per kryterium sukcesu",
            "## 3.2. Elementy spełnione",
            "# 4. Rekomendacje i priorytety naprawcze",
            "# 5. Podsumowanie i wnioski",
            "## Obowiązki ustawowe",
        ):
            assert heading in md, f"Brak nagłówka: {heading}"

    def test_placeholders_present(self):
        md = gen([make_report()])
        assert "[DO UZUPEŁNIENIA" in md

    def test_meta_overrides_placeholder(self):
        md = gen([make_report()], meta={"entity": "Urząd Miasta Wrocławia"})
        assert "Urząd Miasta Wrocławia" in md

    def test_intro_block_for_claude(self):
        md = gen([make_report()])
        assert "INSTRUKCJA DLA MODELU (Claude)" in md


# ---------------------------------------------------------------------------
# Agregacja per kryterium
# ---------------------------------------------------------------------------

class TestAggregation:
    def test_same_criterion_multiple_pages_merges_areas(self):
        reports = [
            make_report(page_title="Kokpit", issues=[make_issue("1.1.1 Treść nietekstowa")]),
            make_report(page_title="Logowanie", filename="login.mhtml",
                        issues=[make_issue("1.1.1 Treść nietekstowa")]),
        ]
        md = gen(reports)
        # Jeden wiersz kryterium 1.1.1 z dwoma obszarami
        rows = [ln for ln in md.splitlines() if "1.1.1" in ln and "Kokpit" in ln]
        assert any("Kokpit" in r and "Logowanie" in r for r in rows)

    def test_area_dedup(self):
        # to samo kryterium dwa razy na tej samej stronie -> obszar raz
        reports = [make_report(page_title="Kokpit", issues=[
            make_issue("1.1.1 Treść nietekstowa"),
            make_issue("1.1.1 Treść nietekstowa", desc="Inny opis"),
        ])]
        md = gen(reports)
        row = [ln for ln in md.splitlines()
               if ln.startswith("| Postrzegalność") and "1.1.1" in ln][0]
        assert row.count("Kokpit") == 1


# ---------------------------------------------------------------------------
# Liczby ilościowe
# ---------------------------------------------------------------------------

class TestQuantitative:
    def test_violated_counts_a_and_aa(self):
        reports = [make_report(issues=[
            make_issue("1.1.1 Treść nietekstowa", "critical"),   # A
            make_issue("1.4.3 Kontrast (minimum)", "major"),     # AA
        ])]
        md = gen(reports)
        assert "| Kryteria NARUSZONE (poziom A) | 1 |" in md
        assert "| Kryteria NARUSZONE (poziom AA) | 1 |" in md
        assert "| Kryteria NARUSZONE ŁĄCZNIE | 2 |" in md

    def test_compliant_equals_baseline_minus_violated(self):
        reports = [make_report(issues=[make_issue("1.1.1 Treść nietekstowa", "critical")])]
        md = gen(reports)
        expected = LEGAL_BASELINE_CRITERIA - 1
        assert f"| Kryteria ZGODNE (potwierdzone) | {expected} |" in md

    def test_critical_issue_count(self):
        reports = [make_report(issues=[
            make_issue("1.1.1 Treść nietekstowa", "critical"),
            make_issue("4.1.2 Nazwa, rola, wartość", "critical"),
            make_issue("1.4.3 Kontrast (minimum)", "major"),
        ])]
        md = gen(reports)
        assert "| Błędy KRYTYCZNE (uniemożliwiające dostęp AT) | 2 |" in md


# ---------------------------------------------------------------------------
# Rozkład wg zasad
# ---------------------------------------------------------------------------

class TestPillars:
    def test_pillar_distribution(self):
        reports = [make_report(issues=[
            make_issue("1.1.1 Treść nietekstowa", "critical"),    # Postrzegalność
            make_issue("4.1.2 Nazwa, rola, wartość", "critical"), # Solidność
        ])]
        md = gen(reports)
        assert "**Postrzegalność**: 1 kryteriów" in md
        assert "**Solidność**: 1 kryteriów" in md
        assert "**Funkcjonalność**: 0 kryteriów" in md


# ---------------------------------------------------------------------------
# Dobre praktyki
# ---------------------------------------------------------------------------

class TestGoodPractices:
    def test_checked_but_not_violated_listed(self):
        # naruszamy 1.1.1 -> 2.4.1 (sprawdzane, niezaruszone) powinno trafić do 3.2
        reports = [make_report(issues=[make_issue("1.1.1 Treść nietekstowa", "critical")])]
        md = gen(reports)
        section = md.split("## 3.2. Elementy spełnione")[1]
        assert "2.4.1" in section
        assert "1.1.1" not in section.split("# 4.")[0]  # 1.1.1 nie jest dobrą praktyką

    def test_violated_excluded_from_good(self):
        reports = [make_report(issues=[make_issue("2.4.1 Możliwość pominięcia bloków", "major")])]
        md = gen(reports)
        section = md.split("## 3.2. Elementy spełnione")[1].split("# 4.")[0]
        # 2.4.1 jest naruszone -> nie powinno być w dobrych praktykach
        assert "| 2.4.1 |" not in section


# ---------------------------------------------------------------------------
# Rekomendacje wg priorytetów
# ---------------------------------------------------------------------------

class TestPriorities:
    def test_severity_maps_to_priority(self):
        reports = [make_report(issues=[
            make_issue("1.1.1 Treść nietekstowa", "critical", rec="Dodać alt"),
            make_issue("1.4.3 Kontrast (minimum)", "major", rec="Zwiększyć kontrast"),
            make_issue("1.3.2 Zrozumiała kolejność", "minor", rec="Popraw kolejność"),
        ])]
        md = gen(reports)
        p1 = md.split("Priorytet 1")[1].split("Priorytet 2")[0]
        p2 = md.split("Priorytet 2")[1].split("Priorytet 3")[0]
        p3 = md.split("Priorytet 3")[1].split("Rekomendacje systemowe")[0]
        assert "1.1.1" in p1
        assert "1.4.3" in p2
        assert "1.3.2" in p3


# ---------------------------------------------------------------------------
# Strony / zakres
# ---------------------------------------------------------------------------

class TestPages:
    def test_single_report_one_page_listed(self):
        md = gen([make_report(page_title="Kokpit użytkownika", page_url="https://x/my/")])
        scope = md.split("## Podstrony objęte audytem")[1].split("## Wyłączenia")[0]
        lines = [ln for ln in scope.splitlines() if ln.startswith("- ")]
        assert len(lines) == 1
        assert "Kokpit użytkownika" in lines[0]
        assert "https://x/my/" in lines[0]

    def test_fallback_label_from_filename(self):
        md = gen([make_report(page_title="", filename="raport_logowanie.mhtml")])
        assert "raport_logowanie" in md


# ---------------------------------------------------------------------------
# Kodowanie / wyjście
# ---------------------------------------------------------------------------

class TestOutput:
    def test_generate_bytes_is_utf8(self):
        data = MarkdownReportGenerator().generate_bytes([make_report()])
        assert isinstance(data, bytes)
        assert "dostępności".encode("utf-8") in data

    def test_generate_file_writes(self, tmp_path):
        path = str(tmp_path / "raport.md")
        returned = MarkdownReportGenerator().generate_file([make_report()], path)
        assert returned == path
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "RAPORT Z OCENY DOSTĘPNOŚCI CYFROWEJ" in content

    def test_empty_reports_no_crash(self):
        md = gen([])
        assert "# 1. Streszczenie wykonawcze" in md
        assert "Nie wykryto naruszeń" in md

    def test_table_pipe_escaping(self):
        # opis zawierający '|' nie może rozbić tabeli
        reports = [make_report(issues=[
            make_issue("1.1.1 Treść nietekstowa", "critical", desc="a | b | c")])]
        md = gen(reports)
        assert "a \\| b \\| c" in md


# ---------------------------------------------------------------------------
# Spójność danych referencyjnych
# ---------------------------------------------------------------------------

class TestReferenceData:
    def test_checked_criteria_count(self):
        assert len(CHECKED_CRITERIA) == 20
        assert len(set(CHECKED_CRITERIA)) == 20
