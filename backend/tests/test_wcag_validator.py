"""
test_wcag_validator.py - Testy jednostkowe dla WCAGValidator.

Pokrycie:
  - 20 checkerow WCAG 2.1 A+AA
  - Issue dataclass (id, wcag_criterion, severity, description, recommendation, affected_elements)
  - Numerowanie issues (i1, i2, ...)
  - Przypadki pozytywne (brak bledow gdy kryterium spelnione)
  - Przypadki negatywne (wykrycie konkretnego naruszenia)
"""

from __future__ import annotations

import sys
import os

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.wcag_validator import WCAGValidator, Issue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _validate(html: str, url: str = "") -> list[Issue]:
    return WCAGValidator().validate(_soup(html), url=url)


def _has_criterion(issues: list[Issue], criterion_prefix: str) -> bool:
    return any(i.wcag_criterion.startswith(criterion_prefix) for i in issues)


def _issues_for(issues: list[Issue], criterion_prefix: str) -> list[Issue]:
    return [i for i in issues if i.wcag_criterion.startswith(criterion_prefix)]


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------

class TestIssueDataclass:

    def test_issue_fields(self):
        i = Issue(
            id="i1",
            wcag_criterion="1.1.1 Tresc",
            severity="critical",
            description="Opis",
            recommendation="Naprawa",
            affected_elements=[],
        )
        assert i.id == "i1"
        assert i.severity == "critical"
        assert isinstance(i.affected_elements, list)

    def test_issue_numbering(self):
        html = (
            '<html><head></head><body>'
            '<img src="a.jpg"><img src="b.jpg">'
            '</body></html>'
        )
        issues = _validate(html)
        ids = [i.id for i in issues]
        for idx, id_ in enumerate(ids, 1):
            assert id_ == f"i{idx}"

    def test_no_duplicate_ids(self):
        html = (
            '<html><head></head><body>'
            '<img src="a.jpg"><button></button><a href="#">kliknij tutaj</a>'
            '</body></html>'
        )
        issues = _validate(html)
        ids = [i.id for i in issues]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 1.1.1 Alt text
# ---------------------------------------------------------------------------

class TestCheck111AltText:

    def test_missing_alt_detected(self):
        html = '<html><body><img src="photo.jpg"></body></html>'
        issues = _validate(html)
        assert _has_criterion(issues, "1.1.1")

    def test_missing_alt_is_critical(self):
        html = '<html><body><img src="photo.jpg"></body></html>'
        issues = _issues_for(_validate(html), "1.1.1")
        assert any(i.severity == "critical" for i in issues)

    def test_with_alt_no_issue(self):
        html = '<html><body><img src="photo.jpg" alt="Zdjecie firmowe"></body></html>'
        assert not _has_criterion(_validate(html), "1.1.1")

    def test_empty_alt_decorative_no_issue(self):
        html = '<html><body><img src="dekoracja.jpg" alt=""></body></html>'
        assert not _has_criterion(_validate(html), "1.1.1")

    def test_linked_image_empty_alt_detected(self):
        html = '<html><body><a href="/"><img src="logo.png" alt=""></a></body></html>'
        issues = _issues_for(_validate(html), "1.1.1")
        # Link z obrazem bez alt jest problemem
        assert any(i.severity == "critical" for i in issues)


# ---------------------------------------------------------------------------
# 1.3.1 Info and relationships
# ---------------------------------------------------------------------------

class TestCheck131InfoRelationships:

    def test_no_headings_detected(self):
        html = '<html lang="pl"><head><title>T</title></head><body><p>Tekst</p></body></html>'
        issues = _issues_for(_validate(html), "1.3.1")
        assert len(issues) > 0

    def test_table_without_th_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "1.3.1")
        assert len(issues) > 0

    def test_table_with_th_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<table><tr><th>Kol A</th><th>Kol B</th></tr><tr><td>1</td><td>2</td></tr></table>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "1.3.1")
        assert len(issues) == 0

    def test_page_with_proper_headings_no_1_3_1(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>Glowny naglowek</h1>'
            '<h2>Podsekcja</h2>'
            '<p>Tekst</p>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "1.3.1")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 1.4.3 Contrast
# ---------------------------------------------------------------------------

class TestCheck143Contrast:

    def test_low_contrast_detected(self):
        # Szary tekst na bialym tle — contrast < 4.5:1
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<p style="color: #cccccc; background-color: #ffffff;">Slaby kontrast</p>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "1.4.3")
        assert len(issues) > 0

    def test_high_contrast_no_issue(self):
        # Czarny tekst na bialym tle — contrast 21:1
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<p style="color: #000000; background-color: #ffffff;">Dobry kontrast</p>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "1.4.3")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 2.1.1 Keyboard
# ---------------------------------------------------------------------------

class TestCheck211Keyboard:

    def test_onclick_without_keyboard_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<div onclick="doSomething()">Kliknij mnie</div>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.1.1")
        assert len(issues) > 0

    def test_onclick_on_button_no_issue(self):
        # button jest natywnie focusable
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button onclick="doSomething()">Kliknij</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.1.1")
        assert len(issues) == 0

    def test_javascript_href_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<a href="javascript:void(0)">Link JS</a>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.1.1")
        assert len(issues) > 0


# ---------------------------------------------------------------------------
# 2.4.1 Bypass blocks
# ---------------------------------------------------------------------------

class TestCheck241BypassBlocks:

    def test_no_skip_link_no_main_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<nav><a href="/">Home</a></nav>'
            '<div><p>Tresc</p></div>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.1")
        assert len(issues) > 0

    def test_skip_link_present_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<a href="#main">Przejdz do tresci</a>'
            '<h1>OK</h1>'
            '<nav><a href="/">Home</a></nav>'
            '<main id="main"><p>Glowna tresc</p></main>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.1")
        assert len(issues) == 0

    def test_main_landmark_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<main><p>Tresc</p></main>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.1")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 2.4.2 Page titled
# ---------------------------------------------------------------------------

class TestCheck242PageTitled:

    def test_missing_title_detected(self):
        html = '<html lang="pl"><head></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "2.4.2")
        assert len(issues) > 0

    def test_empty_title_detected(self):
        html = '<html lang="pl"><head><title></title></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "2.4.2")
        assert len(issues) > 0

    def test_valid_title_no_issue(self):
        html = '<html lang="pl"><head><title>Strona glowna</title></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "2.4.2")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 2.4.3 Focus order
# ---------------------------------------------------------------------------

class TestCheck243FocusOrder:

    def test_positive_tabindex_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button tabindex="3">Przycisk</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.3")
        assert len(issues) > 0

    def test_tabindex_zero_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button tabindex="0">Przycisk</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.3")
        assert len(issues) == 0

    def test_no_tabindex_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button>Przycisk</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.3")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 2.4.4 Link purpose
# ---------------------------------------------------------------------------

class TestCheck244LinkPurpose:

    def test_empty_link_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<a href="/strona"></a>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.4")
        assert len(issues) > 0

    def test_generic_link_text_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<a href="/czytaj">czytaj wiecej</a>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.4")
        assert len(issues) > 0

    def test_descriptive_link_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<a href="/raport-2024">Pobierz raport roczny 2024</a>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.4")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 2.4.6 Headings and labels
# ---------------------------------------------------------------------------

class TestCheck246HeadingsLabels:

    def test_empty_heading_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1></h1>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.6")
        assert len(issues) > 0

    def test_multiple_h1_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>Naglowek 1</h1>'
            '<h1>Naglowek 2</h1>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.6")
        assert len(issues) > 0

    def test_skipped_heading_level_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>Naglowek 1</h1>'
            '<h3>Naglowek 3 (pominiety h2)</h3>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.6")
        assert len(issues) > 0

    def test_proper_headings_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>Glowny</h1><h2>Sekcja A</h2><h3>Podsekcja</h3>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "2.4.6")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 3.1.1 Language
# ---------------------------------------------------------------------------

class TestCheck311Language:

    def test_missing_lang_detected(self):
        html = '<html><head><title>T</title></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "3.1.1")
        assert len(issues) > 0

    def test_missing_lang_is_critical(self):
        html = '<html><head><title>T</title></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "3.1.1")
        assert any(i.severity == "critical" for i in issues)

    def test_valid_lang_no_issue(self):
        html = '<html lang="pl"><head><title>T</title></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "3.1.1")
        assert len(issues) == 0

    def test_invalid_lang_detected(self):
        html = '<html lang="xyz-INVALID-CODE"><head><title>T</title></head><body><h1>OK</h1></body></html>'
        issues = _issues_for(_validate(html), "3.1.1")
        assert len(issues) > 0


# ---------------------------------------------------------------------------
# 3.2.1 On focus
# ---------------------------------------------------------------------------

class TestCheck321OnFocus:

    def test_onfocus_navigation_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<select onfocus="window.location.href=this.value">'
            '<option value="/a">A</option>'
            '</select>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.2.1")
        assert len(issues) > 0

    def test_no_onfocus_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button>Kliknij</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.2.1")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 3.3.1 Error identification
# ---------------------------------------------------------------------------

class TestCheck331ErrorIdentification:

    def test_required_without_describedby_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form>'
            '<label for="name">Imie</label>'
            '<input type="text" id="name" required>'
            '</form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.3.1")
        assert len(issues) > 0

    def test_required_with_describedby_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form>'
            '<label for="name">Imie</label>'
            '<input type="text" id="name" required aria-describedby="name-err">'
            '<span id="name-err">Imie jest wymagane.</span>'
            '</form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.3.1")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 3.3.2 Labels or instructions
# ---------------------------------------------------------------------------

class TestCheck332LabelsInstructions:

    def test_input_without_label_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form><input type="text" name="search"></form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.3.2")
        assert len(issues) > 0

    def test_input_without_label_is_critical(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form><input type="text" name="search"></form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.3.2")
        assert any(i.severity == "critical" for i in issues)

    def test_input_with_label_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form>'
            '<label for="q">Szukaj</label>'
            '<input type="text" id="q" name="search">'
            '</form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.3.2")
        assert len(issues) == 0

    def test_input_with_aria_label_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form>'
            '<input type="text" aria-label="Szukaj w serwisie">'
            '</form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "3.3.2")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# 4.1.1 Parsing
# ---------------------------------------------------------------------------

class TestCheck411Parsing:

    def test_duplicate_id_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<div id="box">A</div>'
            '<div id="box">B</div>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.1")
        assert len(issues) > 0

    def test_duplicate_id_is_major(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<span id="dup">X</span><span id="dup">Y</span>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.1")
        assert any(i.severity == "major" for i in issues)

    def test_unique_ids_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<div id="box1">A</div>'
            '<div id="box2">B</div>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.1")
        assert len(issues) == 0

    def test_max_5_duplicate_reports(self):
        # Dodaj 10 duplikatow — nie powinno byc wiecej niz 5 issues
        divs = ''.join(f'<div id="dup">Element {i}</div>' for i in range(10))
        html = f'<html lang="pl"><head><title>T</title></head><body><h1>OK</h1>{divs}</body></html>'
        issues = _issues_for(_validate(html), "4.1.1")
        assert len(issues) <= 5


# ---------------------------------------------------------------------------
# 4.1.2 Name, role, value
# ---------------------------------------------------------------------------

class TestCheck412NameRoleValue:

    def test_empty_button_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button></button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.2")
        assert len(issues) > 0

    def test_empty_button_is_critical(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button></button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.2")
        assert any(i.severity == "critical" for i in issues)

    def test_button_with_text_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button>Zapisz</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.2")
        assert len(issues) == 0

    def test_button_with_aria_label_no_issue(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<button aria-label="Zamknij okno">X</button>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.2")
        assert len(issues) == 0

    def test_input_image_without_alt_detected(self):
        html = (
            '<html lang="pl"><head><title>T</title></head><body>'
            '<h1>OK</h1>'
            '<form><input type="image" src="submit.png"></form>'
            '</body></html>'
        )
        issues = _issues_for(_validate(html), "4.1.2")
        assert len(issues) > 0


# ---------------------------------------------------------------------------
# Pelna strona — scenariusz integracyjny
# ---------------------------------------------------------------------------

class TestFullPageIntegration:

    GOOD_HTML = '''<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <title>Dobra strona dostepna</title>
</head>
<body>
  <a href="#main">Przejdz do tresci</a>
  <nav>
    <a href="/">Strona glowna</a>
    <a href="/kontakt">Kontakt</a>
  </nav>
  <main id="main">
    <h1>Witamy na stronie</h1>
    <img src="banner.jpg" alt="Baner powitalny">
    <form>
      <label for="email">Adres e-mail</label>
      <input type="email" id="email" name="email" autocomplete="email">
      <button type="submit">Wyslij</button>
    </form>
    <a href="/szczegoly-oferty">Sprawdz oferte</a>
  </main>
  <footer>Kontakt: info@firma.pl</footer>
</body>
</html>'''

    BAD_HTML = '''<!DOCTYPE html>
<html>
<head></head>
<body>
  <img src="photo.jpg">
  <div onclick="go()">Kliknij</div>
  <button></button>
  <a href="#">kliknij tutaj</a>
  <input type="text">
  <p style="color:#cccccc;background-color:#ffffff">Slaby tekst</p>
  <div id="dup">A</div>
  <div id="dup">B</div>
  <button tabindex="5">Zly kolejnosc</button>
</body>
</html>'''

    def test_good_html_few_issues(self):
        issues = _validate(self.GOOD_HTML)
        # Dobra strona powinna miec 0 lub bardzo malo bledow
        critical = [i for i in issues if i.severity == "critical"]
        assert len(critical) == 0, f"Nieoczekiwane krytyczne bledy: {[i.wcag_criterion for i in critical]}"

    def test_bad_html_many_issues(self):
        issues = _validate(self.BAD_HTML)
        assert len(issues) >= 5, f"Oczekiwano min. 5 bledow, znaleziono: {len(issues)}"

    def test_bad_html_has_critical(self):
        issues = _validate(self.BAD_HTML)
        assert any(i.severity == "critical" for i in issues)

    def test_bad_html_missing_lang(self):
        issues = _validate(self.BAD_HTML)
        assert _has_criterion(issues, "3.1.1")

    def test_bad_html_missing_title(self):
        issues = _validate(self.BAD_HTML)
        assert _has_criterion(issues, "2.4.2")

    def test_bad_html_missing_alt(self):
        issues = _validate(self.BAD_HTML)
        assert _has_criterion(issues, "1.1.1")

    def test_bad_html_keyboard_issue(self):
        issues = _validate(self.BAD_HTML)
        assert _has_criterion(issues, "2.1.1")

    def test_bad_html_empty_button(self):
        issues = _validate(self.BAD_HTML)
        assert _has_criterion(issues, "4.1.2")

    def test_bad_html_duplicate_id(self):
        issues = _validate(self.BAD_HTML)
        assert _has_criterion(issues, "4.1.1")

    def test_affected_elements_populated(self):
        issues = _validate(self.BAD_HTML)
        # Przynajmniej jeden issue powinien miec affected_elements
        issues_with_elements = [i for i in issues if i.affected_elements]
        assert len(issues_with_elements) > 0

    def test_affected_elements_have_html_snippet(self):
        html = '<html><body><img src="a.jpg"></body></html>'
        issues = _validate(html)
        img_issues = _issues_for(issues, "1.1.1")
        assert len(img_issues) > 0
        el = img_issues[0].affected_elements[0]
        assert "html_snippet" in el
        assert "<img" in el["html_snippet"]
