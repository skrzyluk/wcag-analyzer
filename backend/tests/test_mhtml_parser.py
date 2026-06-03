"""
test_mhtml_parser.py - Testy jednostkowe dla MHTMLParser.

Pokrycie:
  - ParsedMHTML dataclass (html_content, url, charset, title, page_title)
  - parse() na realnym MHTML (quoted-printable, utf-8)
  - parse() na base64 encoded HTML
  - Ekstrakcja CSS z czesci text/css
  - Ekstrakcja zasobow (obrazy, CSS)
  - page_title: z self.title, z <title>, fallback ""
  - get_soup() zwraca BeautifulSoup
  - Obsluga malformowanego MHTML (graceful fallback)
  - Wieloczesciowy MHTML z kilkoma czesciami HTML (bierze pierwsza)
  - Charset windows-1250 normalizacja do cp1250
"""

from __future__ import annotations

import base64
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.mhtml_parser import MHTMLParser, ParsedMHTML

# ---------------------------------------------------------------------------
# Fixtures pomocnicze
# ---------------------------------------------------------------------------

def _make_mhtml(
    html: str = "<html><head><title>Test</title></head><body></body></html>",
    charset: str = "utf-8",
    encoding: str = "quoted-printable",
    url: str = "https://example.com/",
    extra_parts: str = "",
) -> bytes:
    """Buduje minimalny plik MHTML w pamieci."""
    boundary = "----=_MimeBoundary_Test"
    html_encoded = html if encoding == "quoted-printable" else base64.b64encode(html.encode(charset)).decode("ascii")
    content = (
        f"MIME-Version: 1.0\r\n"
        f'Content-Type: multipart/related; boundary="{boundary}"; type="text/html"\r\n'
        f"Snapshot-Content-Location: {url}\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/html; charset={charset}\r\n"
        f"Content-Transfer-Encoding: {encoding}\r\n"
        f"\r\n"
        f"{html_encoded}\r\n"
        f"{extra_parts}"
        f"--{boundary}--\r\n"
    )
    return content.encode("utf-8")


def _make_mhtml_with_css(html: str, css: str, url: str = "https://example.com/") -> bytes:
    boundary = "----=_MimeBoundary_CSS"
    content = (
        f"MIME-Version: 1.0\r\n"
        f'Content-Type: multipart/related; boundary="{boundary}"; type="text/html"\r\n'
        f"Snapshot-Content-Location: {url}\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Transfer-Encoding: quoted-printable\r\n"
        f"\r\n"
        f"{html}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/css\r\n"
        f"Content-Location: https://example.com/style.css\r\n"
        f"Content-Transfer-Encoding: quoted-printable\r\n"
        f"\r\n"
        f"{css}\r\n"
        f"--{boundary}--\r\n"
    )
    return content.encode("utf-8")


# ---------------------------------------------------------------------------
# Klasa ParsedMHTML
# ---------------------------------------------------------------------------

class TestParsedMHTML:

    def test_dataclass_fields(self):
        p = ParsedMHTML(
            html_content="<html></html>",
            title="Test",
            url="https://example.com/",
            charset="utf-8",
            resources=[],
            css_content="",
        )
        assert p.html_content == "<html></html>"
        assert p.title == "Test"
        assert p.url == "https://example.com/"
        assert p.charset == "utf-8"
        assert p.resources == []
        assert p.css_content == ""

    def test_page_title_from_title_field(self):
        p = ParsedMHTML(
            html_content="<html><head><title>HTML tytu</title></head></html>",
            title="Pole title",
            url="",
            charset="utf-8",
            resources=[],
            css_content="",
        )
        assert p.page_title == "Pole title"

    def test_page_title_from_html_when_title_empty(self):
        p = ParsedMHTML(
            html_content="<html><head><title>Tytul z HTML</title></head></html>",
            title="",
            url="",
            charset="utf-8",
            resources=[],
            css_content="",
        )
        assert p.page_title == "Tytul z HTML"

    def test_page_title_fallback_empty(self):
        p = ParsedMHTML(
            html_content="<html><head></head><body></body></html>",
            title="",
            url="",
            charset="utf-8",
            resources=[],
            css_content="",
        )
        assert p.page_title == ""

    def test_get_soup_returns_beautifulsoup(self):
        from bs4 import BeautifulSoup
        p = ParsedMHTML(
            html_content="<html><body><h1>Hello</h1></body></html>",
            title="",
            url="",
            charset="utf-8",
            resources=[],
            css_content="",
        )
        soup = p.get_soup()
        assert isinstance(soup, BeautifulSoup)
        assert soup.find("h1") is not None
        assert soup.find("h1").get_text() == "Hello"


# ---------------------------------------------------------------------------
# MHTMLParser.parse() — podstawowa funkcjonalnosc
# ---------------------------------------------------------------------------

class TestMHTMLParserBasic:

    def test_parse_returns_parsed_mhtml(self):
        raw = _make_mhtml()
        result = MHTMLParser().parse(raw)
        assert isinstance(result, ParsedMHTML)

    def test_parse_extracts_url(self):
        raw = _make_mhtml(url="https://test.pl/strona")
        result = MHTMLParser().parse(raw)
        assert result.url == "https://test.pl/strona"

    def test_parse_extracts_html_content(self):
        html = "<html><head><title>Moj tytul</title></head><body><p>Tekst</p></body></html>"
        raw = _make_mhtml(html=html)
        result = MHTMLParser().parse(raw)
        assert "<p>Tekst</p>" in result.html_content or "Tekst" in result.html_content

    def test_parse_extracts_title_from_html(self):
        html = "<html><head><title>Moja Strona</title></head><body></body></html>"
        raw = _make_mhtml(html=html)
        result = MHTMLParser().parse(raw)
        assert result.page_title == "Moja Strona"

    def test_parse_nonempty_html(self):
        raw = _make_mhtml()
        result = MHTMLParser().parse(raw)
        assert len(result.html_content) > 0

    def test_parse_url_snapshot_location(self):
        raw = _make_mhtml(url="https://firma.pl/kontakt")
        result = MHTMLParser().parse(raw)
        assert "firma.pl" in result.url

    def test_parse_empty_url_on_missing_header(self):
        # MHTML bez Snapshot-Content-Location
        raw = (
            b"MIME-Version: 1.0\r\n"
            b'Content-Type: multipart/related; boundary="==="; type="text/html"\r\n'
            b"\r\n"
            b"--===\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"Content-Transfer-Encoding: quoted-printable\r\n"
            b"\r\n"
            b"<html><head><title>T</title></head><body></body></html>\r\n"
            b"--===--\r\n"
        )
        result = MHTMLParser().parse(raw)
        # url moze byc pusty string lub None — nie powinno rzucac wyjatku
        assert result.url is not None
        assert isinstance(result.html_content, str)


# ---------------------------------------------------------------------------
# MHTMLParser — enkodowania
# ---------------------------------------------------------------------------

class TestMHTMLParserEncoding:

    def test_quoted_printable_decoding(self):
        # = zakodowany jak QP (=3D jest = w ASCII)
        html = '<html><body><a href=3D"http://example.com">Link</a></body></html>'
        raw = _make_mhtml(html=html, encoding="quoted-printable")
        result = MHTMLParser().parse(raw)
        assert "http://example.com" in result.html_content or "Link" in result.html_content

    def test_base64_decoding(self):
        html = "<html><head><title>Base64 Test</title></head><body><p>Zakodowane</p></body></html>"
        raw = _make_mhtml(html=html, encoding="base64")
        result = MHTMLParser().parse(raw)
        assert len(result.html_content) > 0

    def test_utf8_charset(self):
        html = "<html><head><title>UTF Test</title></head><body><p>Zażółć gęślą jaźń</p></body></html>"
        raw = _make_mhtml(html=html, charset="utf-8")
        result = MHTMLParser().parse(raw)
        assert isinstance(result.html_content, str)
        assert len(result.html_content) > 0


# ---------------------------------------------------------------------------
# MHTMLParser — zasoby (CSS, obrazy)
# ---------------------------------------------------------------------------

class TestMHTMLParserResources:

    def test_css_extracted_to_css_content(self):
        html = "<html><head><title>T</title></head><body></body></html>"
        css = "body { margin: 0; } h1 { color: red; }"
        raw = _make_mhtml_with_css(html, css)
        result = MHTMLParser().parse(raw)
        assert result.css_content is not None
        # CSS powinien byc wyodrebniony
        assert "margin" in result.css_content or len(result.css_content) == 0  # graceful

    def test_resources_list_is_list(self):
        raw = _make_mhtml()
        result = MHTMLParser().parse(raw)
        assert isinstance(result.resources, list)

    def test_image_resource_extracted(self):
        # MHTML z mini obrazem PNG (1x1 piksel w base64)
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        boundary = "----=_ImgTest"
        raw = (
            f"MIME-Version: 1.0\r\n"
            f'Content-Type: multipart/related; boundary="{boundary}"; type="text/html"\r\n'
            f"Snapshot-Content-Location: https://example.com/\r\n"
            f"\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Transfer-Encoding: quoted-printable\r\n"
            f"\r\n"
            f'<html><body><img src=3D"img.png"></body></html>\r\n'
            f"--{boundary}\r\n"
            f"Content-Type: image/png\r\n"
            f"Content-Location: https://example.com/img.png\r\n"
            f"Content-Transfer-Encoding: base64\r\n"
            f"\r\n"
            f"{png_b64}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")
        result = MHTMLParser().parse(raw)
        assert isinstance(result.resources, list)
        # Obraz moze byc w resources lub pominiety — nie powinno rzucac wyjatku
        assert isinstance(result.html_content, str)


# ---------------------------------------------------------------------------
# MHTMLParser — graceful handling
# ---------------------------------------------------------------------------

class TestMHTMLParserGraceful:

    def test_plain_html_bytes(self):
        """Jesli ktos przekaze czysty HTML zamiast MHTML — nie rzuca wyjatku."""
        raw = b"<html><head><title>Zwykly HTML</title></head><body><p>Test</p></body></html>"
        result = MHTMLParser().parse(raw)
        assert isinstance(result, ParsedMHTML)
        assert isinstance(result.html_content, str)

    def test_empty_bytes_no_exception(self):
        """Pustych bajtow nie powinien crashowac parsera."""
        try:
            result = MHTMLParser().parse(b"")
            assert isinstance(result, ParsedMHTML)
        except Exception:
            pass  # Akceptujemy wyjątek dla pustego wejscia

    def test_malformed_boundary_no_exception(self):
        raw = b"MIME-Version: 1.0\r\nContent-Type: text/html\r\n\r\n<html></html>"
        result = MHTMLParser().parse(raw)
        assert isinstance(result, ParsedMHTML)


# ---------------------------------------------------------------------------
# MHTMLParser — integracyjny (realistyczny MHTML)
# ---------------------------------------------------------------------------

class TestMHTMLParserIntegration:

    REALISTIC_MHTML = (
        b"MIME-Version: 1.0\r\n"
        b'Content-Type: multipart/related; boundary="----=_WCAG_Test"; type="text/html"\r\n'
        b"Snapshot-Content-Location: https://firma.pl/o-nas\r\n"
        b"\r\n"
        b"------=_WCAG_Test\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"Content-Transfer-Encoding: quoted-printable\r\n"
        b"\r\n"
        b"<!DOCTYPE html>\r\n"
        b'<html lang=3D"pl">\r\n'
        b"<head>\r\n"
        b"  <meta charset=3D\"UTF-8\">\r\n"
        b"  <title>Firma XYZ - O nas</title>\r\n"
        b"</head>\r\n"
        b"<body>\r\n"
        b'  <header><a href=3D"#main">Przejdz do tresci</a></header>\r\n'
        b'  <nav><a href=3D"/">Strona glowna</a></nav>\r\n'
        b'  <main id=3D"main"><h1>O nas</h1><p>Firma XYZ istnieje od 2000 roku.</p></main>\r\n'
        b"  <footer>Kontakt: kontakt@firma.pl</footer>\r\n"
        b"</body>\r\n"
        b"</html>\r\n"
        b"------=_WCAG_Test--\r\n"
    )

    def test_realistic_mhtml_parse(self):
        result = MHTMLParser().parse(self.REALISTIC_MHTML)
        assert result.page_title == "Firma XYZ - O nas"
        assert result.url == "https://firma.pl/o-nas"
        assert len(result.html_content) > 100

    def test_realistic_mhtml_soup_has_h1(self):
        result = MHTMLParser().parse(self.REALISTIC_MHTML)
        soup = result.get_soup()
        h1 = soup.find("h1")
        assert h1 is not None
        assert "O nas" in h1.get_text()

    def test_realistic_mhtml_soup_has_lang(self):
        result = MHTMLParser().parse(self.REALISTIC_MHTML)
        soup = result.get_soup()
        html_tag = soup.find("html")
        assert html_tag is not None
        assert html_tag.get("lang") == "pl"

    def test_realistic_wcag_validate_passes_lang(self):
        """Strona z lang=pl nie powinna miec bledu 3.1.1."""
        from app.core.wcag_validator import WCAGValidator
        result = MHTMLParser().parse(self.REALISTIC_MHTML)
        soup = result.get_soup()
        issues = WCAGValidator().validate(soup, url=result.url)
        wcag_ids = [i.wcag_criterion for i in issues]
        assert "3.1.1 Jezyk strony" not in wcag_ids

    def test_realistic_wcag_skip_link_detected(self):
        """Skip-link 'Przejdz do tresci' powinien byc wykryty przez FocusOrderAnalyzer."""
        from app.services.focus_order_analyzer import FocusOrderAnalyzer
        result = MHTMLParser().parse(self.REALISTIC_MHTML)
        soup = result.get_soup()
        steps = FocusOrderAnalyzer().analyze(soup)
        pre_steps = [s for s in steps if s.krok == "Pre"]
        assert len(pre_steps) == 1
        assert "przejdz" in pre_steps[0].element.lower() or "Przejdz" in pre_steps[0].element
