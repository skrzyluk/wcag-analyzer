"""
mhtml_parser.py - Parsowanie plikow MHTML.

MHTML (MIME HTML) to archiwum MIME zawierajace strone HTML
wraz z osadzonymi zasobami (CSS, obrazy, JS).

Uzycie:
    from app.core.mhtml_parser import MHTMLParser

    parser = MHTMLParser()
    result = parser.parse(raw_bytes)
    print(result.title, result.url)
    soup = result.get_soup()
"""

from __future__ import annotations

import email
import email.policy
import quopri
import base64
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MHTMLResource:
    """Pojedynczy zasob (CSS, obraz, JS) z archiwum MHTML."""
    content_type: str
    content_id:   str
    location:     str          # URL lub Content-Location
    content:      bytes


@dataclass
class ParsedMHTML:
    """Wynik parsowania pliku MHTML."""
    html_content: str                        # Glowny HTML (zdekodowany)
    title:        str = ""                   # Tytul strony (<title>)
    url:          str = ""                   # URL zrodlowy (Snapshot-Content-Location)
    charset:      str = "utf-8"
    resources:    list[MHTMLResource] = field(default_factory=list)
    css_content:  str = ""                   # Polaczone style CSS

    def get_soup(self) -> "BeautifulSoup":
        """Zwraca obiekt BeautifulSoup dla glownego HTML."""
        if not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 nie jest zainstalowany")
        return BeautifulSoup(self.html_content, "lxml")

    @property
    def page_title(self) -> str:
        """Pobiera tytul z HTML jesli nie byl ustawiony przy parsowaniu."""
        if self.title:
            return self.title
        if BS4_AVAILABLE:
            soup = BeautifulSoup(self.html_content[:4096], "lxml")
            tag = soup.find("title")
            if tag:
                return tag.get_text(strip=True)
        return ""


# ---------------------------------------------------------------------------
# MHTMLParser
# ---------------------------------------------------------------------------

class MHTMLParser:
    """
    Parsuje plik MHTML (raw bytes) i zwraca ParsedMHTML.

    Obsluguje:
      - Content-Transfer-Encoding: quoted-printable, base64, 7bit, 8bit
      - Charset: UTF-8, ISO-8859-1, Windows-1250/1252
      - Wieloczescowe archiwum MIME
      - Naglorek Snapshot-Content-Location (URL strony)
    """

    def parse(self, raw: bytes) -> ParsedMHTML:
        """Glowna metoda parsowania. Przyjmuje surowe bajty pliku MHTML."""
        msg = self._parse_message(raw)
        return self._extract(msg)

    def parse_str(self, text: str, charset: str = "utf-8") -> ParsedMHTML:
        return self.parse(text.encode(charset))

    # ------------------------------------------------------------------
    # Parsowanie wiadomosci MIME
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_message(raw: bytes) -> email.message.Message:
        """Parsuje surowe bajty jako wiadomosc MIME."""
        # Uzyj lenient policy — toleruje malformed headers
        try:
            return email.message_from_bytes(raw, policy=email.policy.compat32)
        except Exception:
            # Fallback: zamien na string i parsuj ponownie
            text = raw.decode("utf-8", errors="replace")
            return email.message_from_string(text)

    def _extract(self, msg: email.message.Message) -> ParsedMHTML:
        """Wyodrebnia zawartosc z wiadomosci MIME."""
        result = ParsedMHTML(html_content="")

        # Pobierz URL zrodlowy ze specjalnego naglowka
        result.url = (
            msg.get("Snapshot-Content-Location", "")
            or msg.get("Content-Location", "")
            or ""
        )

        parts = list(msg.walk())

        html_part = None
        css_chunks: list[str] = []
        resources: list[MHTMLResource] = []

        for part in parts:
            ct = (part.get_content_type() or "").lower()
            cte = (part.get("Content-Transfer-Encoding") or "").lower().strip()
            loc = (
                part.get("Content-Location", "")
                or part.get("Content-ID", "")
            )

            payload = self._decode_part(part, cte)
            if payload is None:
                continue

            if ct == "text/html" and html_part is None:
                charset = self._get_charset(part)
                result.charset = charset
                if isinstance(payload, bytes):
                    result.html_content = payload.decode(charset, errors="replace")
                else:
                    result.html_content = payload
                html_part = part

            elif ct == "text/css":
                charset = self._get_charset(part)
                if isinstance(payload, bytes):
                    css_chunks.append(payload.decode(charset, errors="replace"))
                else:
                    css_chunks.append(str(payload))

            elif ct.startswith("image/") or ct in (
                "application/javascript", "text/javascript",
                "application/json", "font/woff", "font/woff2",
                "font/ttf", "application/font-woff",
            ):
                resources.append(MHTMLResource(
                    content_type=ct,
                    content_id=part.get("Content-ID", ""),
                    location=loc,
                    content=payload if isinstance(payload, bytes) else payload.encode("utf-8"),
                ))

        result.css_content = "\n".join(css_chunks)
        result.resources  = resources

        # Wyodrebnij tytul strony z HTML
        if result.html_content and BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(result.html_content[:8192], "lxml")
                title_tag = soup.find("title")
                if title_tag:
                    result.title = title_tag.get_text(strip=True)
            except Exception:
                pass

        return result

    # ------------------------------------------------------------------
    # Dekodowanie czesci MIME
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_part(part: email.message.Message, cte: str) -> bytes | str | None:
        """Dekoduje payload czesci MIME wedlug Content-Transfer-Encoding."""
        try:
            payload = part.get_payload(decode=True)
            if payload is not None:
                return payload  # email.message juz zdekodowal (decode=True)
        except Exception:
            pass

        # Fallback: reczne dekodowanie
        raw_payload = part.get_payload(decode=False)
        if raw_payload is None:
            return None
        if isinstance(raw_payload, list):
            return None  # multipart — pomijamy

        raw_str = str(raw_payload)

        if "quoted-printable" in cte:
            try:
                return quopri.decodestring(raw_str.encode("ascii", errors="replace"))
            except Exception:
                return raw_str.encode("utf-8", errors="replace")

        if "base64" in cte:
            try:
                cleaned = re.sub(r"\s+", "", raw_str)
                return base64.b64decode(cleaned + "==")
            except Exception:
                return raw_str.encode("utf-8", errors="replace")

        return raw_str.encode("utf-8", errors="replace")

    # ------------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------------

    @staticmethod
    def _get_charset(part: email.message.Message) -> str:
        """Pobiera charset z naglowka Content-Type. Domyslnie utf-8."""
        charset = part.get_content_charset()
        if not charset:
            return "utf-8"
        # Normalizacja znanych aliasow
        charset = charset.lower().strip()
        aliases = {
            "windows-1250": "cp1250",
            "windows-1252": "cp1252",
            "iso-8859-2":   "iso-8859-2",
            "iso8859-1":    "iso-8859-1",
            "iso8859-2":    "iso-8859-2",
        }
        return aliases.get(charset, charset)
