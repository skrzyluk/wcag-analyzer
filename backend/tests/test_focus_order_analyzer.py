"""
test_focus_order_analyzer.py - Testy jednostkowe dla FocusOrderAnalyzer.

Uruchamianie:
    cd backend
    pytest tests/test_focus_order_analyzer.py -v
"""

import pytest
from bs4 import BeautifulSoup
from app.services.focus_order_analyzer import FocusOrderAnalyzer, FocusStep


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


@pytest.fixture
def analyzer() -> FocusOrderAnalyzer:
    return FocusOrderAnalyzer()


# ---------------------------------------------------------------------------
# FocusStep dataclass
# ---------------------------------------------------------------------------

class TestFocusStep:
    def test_fields(self):
        s = FocusStep(krok="1", obszar_strony="Nawigacja",
                      element="Link: Home", uzasadnienie="WCAG 2.4.4")
        assert s.krok == "1"
        assert s.obszar_strony == "Nawigacja"
        assert s.element == "Link: Home"
        assert s.uzasadnienie == "WCAG 2.4.4"


# ---------------------------------------------------------------------------
# Skip-link
# ---------------------------------------------------------------------------

class TestSkipLink:
    def test_skip_link_detected_by_href_main(self, analyzer):
        html = '<html><body><a href="#main">Skip</a><main id="main"></main></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].krok == "Pre"

    def test_skip_link_detected_by_keyword_in_text(self, analyzer):
        html = '<html><body><a href="#c">Przejdz do tresci</a></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].krok == "Pre"

    def test_skip_link_not_detected_without_hash(self, analyzer):
        html = '<html><body><a href="/inny">Link zewnetrzny</a><button>OK</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert all(s.krok != "Pre" for s in steps)

    def test_skip_link_landmark_region(self, analyzer):
        html = '<html><body><header><a href="#main">Przejdz do tresci</a></header><main id="main"></main></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].krok == "Pre"
        assert steps[0].obszar_strony == "Naglowek strony"

    def test_skip_link_counted_once(self, analyzer):
        html = '<html><body><a href="#main">Przejdz do tresci</a><nav><a href="/">Home</a></nav><main id="main"></main></body></html>'
        steps = analyzer.analyze(soup(html))
        pre_steps = [s for s in steps if s.krok == "Pre"]
        assert len(pre_steps) == 1


# ---------------------------------------------------------------------------
# Focusable elements
# ---------------------------------------------------------------------------

class TestFocusableElements:
    def test_link_with_href_is_focusable(self, analyzer):
        html = '<html><body><a href="/page">Link</a></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 1
        assert "Link" in steps[0].element

    def test_link_without_href_not_focusable(self, analyzer):
        html = '<html><body><a>Anchor without href</a></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 0

    def test_button_is_focusable(self, analyzer):
        html = '<html><body><button>Click me</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 1
        assert "Przycisk" in steps[0].element

    def test_input_text_is_focusable(self, analyzer):
        html = '<html><body><input type="text" aria-label="Email"></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 1
        assert "Pole text" in steps[0].element

    def test_input_hidden_not_focusable(self, analyzer):
        html = '<html><body><input type="hidden" name="token"></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 0

    def test_select_is_focusable(self, analyzer):
        html = '<html><body><select aria-label="Kraj"><option>Polska</option></select></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 1
        assert "Lista wyboru" in steps[0].element

    def test_textarea_is_focusable(self, analyzer):
        html = '<html><body><textarea aria-label="Komentarz"></textarea></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 1
        assert "Obszar tekstowy" in steps[0].element

    def test_disabled_input_not_focusable(self, analyzer):
        html = '<html><body><button disabled>Zablokowany</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 0

    def test_aria_hidden_not_focusable(self, analyzer):
        html = '<html><body><button aria-hidden="true">Ukryty</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 0

    def test_tabindex_minus1_not_focusable(self, analyzer):
        html = '<html><body><button tabindex="-1">Wykluczone</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 0

    def test_tabindex_zero_is_focusable(self, analyzer):
        html = '<html><body><div tabindex="0" role="button">Klikalne</div></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps) == 1

    def test_empty_page_no_steps(self, analyzer):
        steps = analyzer.analyze(soup("<html><body></body></html>"))
        assert steps == []


# ---------------------------------------------------------------------------
# Tabindex ordering
# ---------------------------------------------------------------------------

class TestTabindexOrdering:
    def test_positive_tabindex_before_natural_order(self, analyzer):
        html = '<html><body><a href="/last">Ostatni w DOM</a><button tabindex="1">Pierwszy</button></body></html>'
        steps = analyzer.analyze(soup(html))
        # button z tabindex=1 powinien byc przed linkiem
        elements = [s.element for s in steps]
        btn_idx = next(i for i, e in enumerate(elements) if "Pierwszy" in e)
        link_idx = next(i for i, e in enumerate(elements) if "Ostatni" in e)
        assert btn_idx < link_idx

    def test_tabindex_sorted_ascending(self, analyzer):
        html = '<html><body><a href="/c" tabindex="3">C</a><a href="/a" tabindex="1">A</a><a href="/b" tabindex="2">B</a></body></html>'
        steps = analyzer.analyze(soup(html))
        labels = [s.element for s in steps]
        idx_a = next(i for i, e in enumerate(labels) if ">A<" in e or "A" in e)
        idx_b = next(i for i, e in enumerate(labels) if ">B<" in e or "B" in e)
        idx_c = next(i for i, e in enumerate(labels) if ">C<" in e or "C" in e)
        assert idx_a < idx_b < idx_c


# ---------------------------------------------------------------------------
# Landmark regions
# ---------------------------------------------------------------------------

class TestLandmarkRegions:
    def test_link_in_nav_gets_nawigacja(self, analyzer):
        html = '<html><body><nav><a href="/">Home</a></nav></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Nawigacja"

    def test_button_in_main_gets_glowna_tresc(self, analyzer):
        html = '<html><body><main><button>OK</button></main></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Glowna tresc"

    def test_link_in_footer(self, analyzer):
        html = '<html><body><footer><a href="/regulamin">Regulamin</a></footer></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Stopka"

    def test_link_in_header(self, analyzer):
        html = '<html><body><header><a href="/logo">Logo</a></header></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Naglowek strony"

    def test_element_outside_landmark_gets_strona(self, analyzer):
        html = '<html><body><div><a href="/x">Link poza landmark</a></div></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Strona"

    def test_aria_role_navigation(self, analyzer):
        html = '<html><body><div role="navigation"><a href="/">Home</a></div></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Nawigacja"

    def test_aria_role_main(self, analyzer):
        html = '<html><body><div role="main"><button>Go</button></div></body></html>'
        steps = analyzer.analyze(soup(html))
        assert steps[0].obszar_strony == "Glowna tresc"


# ---------------------------------------------------------------------------
# Accessible label
# ---------------------------------------------------------------------------

class TestAccessibleLabel:
    def test_aria_label_used(self, analyzer):
        html = '<html><body><button aria-label="Zamknij okno">X</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert "Zamknij okno" in steps[0].element

    def test_title_used_as_fallback(self, analyzer):
        html = '<html><body><button title="Zapisz">💾</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert "Zapisz" in steps[0].element

    def test_inner_text_used(self, analyzer):
        html = '<html><body><button>Zaloguj sie</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert "Zaloguj sie" in steps[0].element

    def test_long_text_truncated(self, analyzer):
        long_text = "A" * 80
        html = f'<html><body><button>{long_text}</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert len(steps[0].element) < 120  # skrocony
        assert "..." in steps[0].element


# ---------------------------------------------------------------------------
# Uzasadnienia
# ---------------------------------------------------------------------------

class TestUzasadnienia:
    def test_link_mentions_wcag_244(self, analyzer):
        html = '<html><body><a href="/x">Link</a></body></html>'
        steps = analyzer.analyze(soup(html))
        assert "2.4.4" in steps[0].uzasadnienie

    def test_positive_tabindex_warns_243(self, analyzer):
        html = '<html><body><button tabindex="5">Btn</button></body></html>'
        steps = analyzer.analyze(soup(html))
        assert "2.4.3" in steps[0].uzasadnienie

    def test_input_without_label_warns(self, analyzer):
        html = '<html><body><input type="text"></body></html>'
        steps = analyzer.analyze(soup(html))
        assert any("1.3.1" in s.uzasadnienie or "4.1.2" in s.uzasadnienie for s in steps)


# ---------------------------------------------------------------------------
# Full HTML page
# ---------------------------------------------------------------------------

class TestFullPage:
    FULL_HTML = """
    <html>
    <body>
      <a href="#main">Przejdz do tresci</a>
      <header>
        <nav>
          <a href="/">Strona glowna</a>
          <a href="/o-nas">O nas</a>
          <a href="/kontakt">Kontakt</a>
        </nav>
      </header>
      <main id="main">
        <h1>Witaj</h1>
        <input type="text" aria-label="Szukaj">
        <button>Szukaj</button>
      </main>
      <footer>
        <a href="/regulamin">Regulamin</a>
      </footer>
    </body>
    </html>
    """

    def test_step_count(self, analyzer):
        steps = analyzer.analyze(soup(self.FULL_HTML))
        assert len(steps) == 7  # Pre + 3 nav + input + button + regulamin

    def test_first_step_is_skip(self, analyzer):
        steps = analyzer.analyze(soup(self.FULL_HTML))
        assert steps[0].krok == "Pre"

    def test_nav_steps_have_nawigacja_region(self, analyzer):
        steps = analyzer.analyze(soup(self.FULL_HTML))
        nav_steps = [s for s in steps if s.obszar_strony == "Nawigacja"]
        assert len(nav_steps) == 3

    def test_main_steps_have_glowna_tresc(self, analyzer):
        steps = analyzer.analyze(soup(self.FULL_HTML))
        main_steps = [s for s in steps if s.obszar_strony == "Glowna tresc"]
        assert len(main_steps) == 2  # input + button

    def test_footer_step_present(self, analyzer):
        steps = analyzer.analyze(soup(self.FULL_HTML))
        footer_steps = [s for s in steps if s.obszar_strony == "Stopka"]
        assert len(footer_steps) == 1

    def test_krok_numbers_sequential(self, analyzer):
        steps = analyzer.analyze(soup(self.FULL_HTML))
        numeric_steps = [s for s in steps if s.krok != "Pre"]
        for i, step in enumerate(numeric_steps, start=1):
            assert step.krok == str(i)
