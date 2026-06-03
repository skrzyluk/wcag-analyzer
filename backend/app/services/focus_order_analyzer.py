"""
focus_order_analyzer.py - Analiza kolejnosci Tab-order w HTML.

Wyodrebnia elementy interaktywne z drzewa DOM i buduje rekomendowana
kolejnosc fokusa (Tab-order) wraz z uzasadnieniami dostepnosci.

Uzycie:
    from bs4 import BeautifulSoup
    from app.services.focus_order_analyzer import FocusOrderAnalyzer

    soup = BeautifulSoup(html_content, "lxml")
    analyzer = FocusOrderAnalyzer()
    steps = analyzer.analyze(soup)
    for step in steps:
        print(step.krok, step.element, step.uzasadnienie)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from bs4 import BeautifulSoup, Tag
    BS4_AVAILABLE = True
except ImportError:  # pragma: no cover
    BS4_AVAILABLE = False


# ---------------------------------------------------------------------------
# Stale — landmark regions
# ---------------------------------------------------------------------------

LANDMARK_MAP: dict[str, str] = {
    "header":  "Naglowek strony",
    "nav":     "Nawigacja",
    "main":    "Glowna tresc",
    "footer":  "Stopka",
    "aside":   "Panel boczny",
    "form":    "Formularz",
    "section": "Sekcja",
    "article": "Artykul",
    "dialog":  "Okno dialogowe",
    "search":  "Wyszukiwanie",
}

ARIA_LANDMARK_MAP: dict[str, str] = {
    "banner":         "Naglowek strony",
    "navigation":     "Nawigacja",
    "main":           "Glowna tresc",
    "contentinfo":    "Stopka",
    "complementary":  "Panel boczny",
    "search":         "Wyszukiwanie",
    "form":           "Formularz",
    "dialog":         "Okno dialogowe",
    "alertdialog":    "Okno dialogowe (alert)",
    "region":         "Region",
    "application":    "Aplikacja",
}

# Elementy natywnie focusable (bez tabindex)
FOCUSABLE_TAGS = {"a", "button", "input", "select", "textarea", "details", "summary"}

# Typy input wykluczajace z fokusa
INPUT_EXCLUDE_TYPES = {"hidden", "image"}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class FocusStep:
    krok:          str   # "Pre" dla skip-link, "1", "2", ... dla pozostalych
    obszar_strony: str   # Landmark region, np. "Nawigacja", "Glowna tresc"
    element:       str   # Opis elementu, np. "Link: Przejdz do tresci"
    uzasadnienie:  str   # Dlaczego taka kolejnosc (WCAG, ARIA)


# ---------------------------------------------------------------------------
# FocusOrderAnalyzer
# ---------------------------------------------------------------------------

class FocusOrderAnalyzer:
    """
    Analizuje kolejnosc Tab-order elementow interaktywnych w HTML.

    Algorytm:
      1. Znajdz skip-link (krok "Pre") jesli istnieje.
      2. Zbierz wszystkie focusable elementy:
         a) tabindex > 0  (posortowane rosnaco wg wartosci)
         b) natywnie focusable (a, button, input...) bez tabindex lub tabindex=0
      3. Dla kazdego elementu wyznacz landmark region i uzasadnienie.
      4. Zwroc liste FocusStep.
    """

    def analyze(self, soup: "BeautifulSoup") -> list[FocusStep]:
        """Glowna metoda analizy. Przyjmuje sparsowany HTML (BeautifulSoup)."""
        steps: list[FocusStep] = []

        # --- Krok Pre: skip-link ---
        skip = self._find_skip_link(soup)
        if skip:
            steps.append(FocusStep(
                krok="Pre",
                obszar_strony=self._get_landmark_region(skip),
                element=self._describe_element(skip),
                uzasadnienie=(
                    "WCAG 2.4.1 — Mozliwosc pominiecia blokow: "
                    "Skip-link umozliwia pomin nawigacji i przejscie "
                    "bezposrednio do glownej tresci strony."
                ),
            ))

        # --- Elementy z tabindex > 0 (posortowane) ---
        positive_tabindex: list[tuple[int, Tag]] = []
        for el in soup.find_all(True):
            ti = self._get_tabindex(el)
            if ti is not None and ti > 0:
                positive_tabindex.append((ti, el))
        positive_tabindex.sort(key=lambda x: x[0])

        # Numeracja krokow zawsze zaczyna sie od 1 (niezaleznie od Pre)
        counter = 0

        for _, el in positive_tabindex:
            if skip and el is skip:
                continue
            counter += 1
            steps.append(self._make_step(str(counter), el))

        # --- Elementy natywnie focusable (DOM order) ---
        for el in self._get_focusable_elements(soup):
            if skip and el is skip:
                continue
            # Pomijamy juz dodane (tabindex > 0)
            if any(el is s_el for _, s_el in positive_tabindex):
                continue
            counter += 1
            steps.append(self._make_step(str(counter), el))

        return steps

    # ------------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------------

    def _get_focusable_elements(self, soup: "BeautifulSoup") -> list["Tag"]:
        """
        Zwraca elementy focusable w kolejnosci DOM (z wylaczeniem:
        tabindex=-1, disabled, type=hidden, [aria-hidden=true]).
        """
        result: list[Tag] = []

        for el in soup.find_all(True):
            tag_name = el.name if el.name else ""

            # Sprawdz tabindex
            ti = self._get_tabindex(el)
            if ti is not None and ti < 0:
                continue  # tabindex="-1" wykluczone

            # Skip-link zostanie obsluzone osobno
            # Nie pomijamy tutaj — filtrowanie w analyze()

            # Natywnie focusable?
            if tag_name in FOCUSABLE_TAGS:
                # Wyklucz <a> bez href
                if tag_name == "a" and not el.get("href"):
                    continue
                # Wyklucz input[type=hidden] i input[type=image]
                if tag_name == "input":
                    input_type = (el.get("type") or "text").lower()
                    if input_type in INPUT_EXCLUDE_TYPES:
                        continue
                # Wyklucz disabled
                if el.get("disabled") is not None:
                    continue
                # Wyklucz aria-hidden
                if el.get("aria-hidden", "").lower() == "true":
                    continue
                result.append(el)
                continue

            # Nie-natywne z tabindex >= 0
            if ti is not None and ti >= 0:
                if el.get("aria-hidden", "").lower() == "true":
                    continue
                result.append(el)

        return result

    def _get_landmark_region(self, element: "Tag") -> str:
        """
        Przeszukuje przodkow elementu i zwraca nazwe landmark region.
        Sprawdza: role ARIA, znacznik HTML5, domyslnie 'Strona'.
        """
        # Przeszukaj przodkow (od najblizszego)
        for ancestor in element.parents:
            if not isinstance(ancestor, Tag):
                continue

            # 1. role ARIA
            role = (ancestor.get("role") or "").lower()
            if role in ARIA_LANDMARK_MAP:
                return ARIA_LANDMARK_MAP[role]

            # 2. Znacznik HTML5 semantyczny
            tag_name = ancestor.name or ""
            if tag_name in LANDMARK_MAP:
                return LANDMARK_MAP[tag_name]

        return "Strona"

    def _find_skip_link(self, soup: "BeautifulSoup") -> Optional["Tag"]:
        """
        Szuka skip-linka — pierwszego linka prowadzacego do kotwy na tej samej stronie
        (href zaczyna sie od '#'), ktory jest pierwszym lub jednym z pierwszych elementow.
        Takze sprawdza aria-label / text zawierajacy slowa kluczowe.
        """
        SKIP_KEYWORDS = (
            "skip", "przejdz", "przejscie", "pominiecie", "pomijanie",
            "tresc", "nawigacja", "content", "main", "glowna",
        )
        candidates = soup.find_all("a", href=True)
        for link in candidates[:10]:  # sprawdzamy tylko pierwsze 10 linkow
            href = str(link.get("href", ""))
            if not href.startswith("#"):
                continue
            text = (link.get_text() or "").lower()
            aria = (link.get("aria-label") or "").lower()
            combined = text + " " + aria
            if any(kw in combined for kw in SKIP_KEYWORDS):
                return link
            # Jesli href wskazuje na #main, #content, #tresc — to skip-link
            target = href[1:].lower()
            if target in ("main", "content", "tresc", "glowna-tresc", "main-content"):
                return link
        return None

    def _make_step(self, krok: str, el: "Tag") -> FocusStep:
        return FocusStep(
            krok=krok,
            obszar_strony=self._get_landmark_region(el),
            element=self._describe_element(el),
            uzasadnienie=self._generate_uzasadnienie(el),
        )

    def _describe_element(self, el: "Tag") -> str:
        """Generuje czytelny opis elementu dla kolumny 'Element / kontrolka'."""
        tag = el.name or "element"
        tag_upper = tag.upper()

        # Pobierz etykiete dostepnosci
        label = self._get_accessible_label(el)

        if tag == "a":
            href = el.get("href", "")
            return f"Link: {label}" if label else f"Link ({href})"

        if tag == "button":
            return f"Przycisk: {label}" if label else "Przycisk (bez etykiety)"

        if tag == "input":
            input_type = (el.get("type") or "text").lower()
            name = el.get("name") or el.get("id") or ""
            if label:
                return f"Pole {input_type}: {label}"
            return f"Pole {input_type} [{name}]" if name else f"Pole {input_type}"

        if tag == "select":
            return f"Lista wyboru: {label}" if label else "Lista wyboru"

        if tag == "textarea":
            return f"Obszar tekstowy: {label}" if label else "Obszar tekstowy"

        if tag == "details":
            summary = el.find("summary")
            summary_text = summary.get_text(strip=True) if summary else ""
            return f"Rozwijany blok: {summary_text}" if summary_text else "Rozwijany blok"

        if tag == "summary":
            text = el.get_text(strip=True)
            return f"Naglowek rozwijanego bloku: {text}" if text else "Naglowek rozwijanego bloku"

        # Generyczny element z tabindex
        role = el.get("role", "")
        if role:
            return f"{tag_upper}[role={role}]: {label}" if label else f"{tag_upper}[role={role}]"
        return f"{tag_upper}: {label}" if label else tag_upper

    def _get_accessible_label(self, el: "Tag") -> str:
        """Wyznacza etykiete dostepnosci: aria-label > aria-labelledby > title > tekst."""
        # aria-label
        aria_label = (el.get("aria-label") or "").strip()
        if aria_label:
            return aria_label

        # aria-labelledby
        labelledby = (el.get("aria-labelledby") or "").strip()
        if labelledby and el.parent:
            soup_root = self._get_soup_root(el)
            if soup_root:
                ref = soup_root.find(id=labelledby)
                if ref:
                    return ref.get_text(strip=True)

        # title
        title = (el.get("title") or "").strip()
        if title:
            return title

        # Tekst wewnetrzny (max 60 znakow)
        text = el.get_text(strip=True)
        if text:
            return text[:60] + ("..." if len(text) > 60 else "")

        return ""

    @staticmethod
    def _get_soup_root(el: "Tag") -> Optional["BeautifulSoup"]:
        """Zwraca korzen dokumentu BeautifulSoup dla danego elementu."""
        node = el
        while node.parent:
            node = node.parent
        return node if hasattr(node, "find") else None

    @staticmethod
    def _get_tabindex(el: "Tag") -> Optional[int]:
        """Zwraca wartosc tabindex jako int lub None jesli brak atrybutu."""
        raw = el.get("tabindex")
        if raw is None:
            return None
        try:
            return int(str(raw).strip())
        except (ValueError, TypeError):
            return None

    def _generate_uzasadnienie(self, el: "Tag") -> str:
        """Generuje uzasadnienie WCAG dla danego elementu."""
        tag = el.name or ""
        ti = self._get_tabindex(el)
        role = el.get("role", "")
        parts: list[str] = []

        # Tabindex niestandardowy
        if ti is not None and ti > 0:
            parts.append(
                f"UWAGA: tabindex={ti} — element ma niestandardowa kolejnosc fokusa. "
                f"WCAG 2.4.3 zaleca naturalna kolejnosc DOM (tabindex=0 lub brak)."
            )
        elif ti == 0:
            parts.append("tabindex=0 — element dodany do naturalnej kolejnosci fokusa.")

        # Etykieta dostepnosci
        label = self._get_accessible_label(el)
        if not label and tag in ("button", "input", "select", "textarea"):
            parts.append(
                "WCAG 1.3.1 / 4.1.2 — brak dostepnej etykiety elementu interaktywnego."
            )

        # Specyficzne uzasadnienia wg tagu
        if tag == "a":
            parts.append("WCAG 2.4.4 — Cel linku powinien byc jasny z samego tekstu linku.")
        elif tag == "button":
            parts.append("WCAG 4.1.2 — Przycisk musi miec dostepna nazwe.")
        elif tag == "input":
            input_type = (el.get("type") or "text").lower()
            if input_type == "text":
                parts.append("WCAG 1.3.1 — Pole tekstowe wymaga etykiety (label lub aria-label).")
            elif input_type == "checkbox":
                parts.append("WCAG 1.3.1 — Pole wyboru wymaga etykiety.")
            elif input_type == "radio":
                parts.append("WCAG 1.3.1 — Przycisk radiowy wymaga etykiety i grupowania (fieldset/legend).")
            elif input_type in ("submit", "reset", "button"):
                parts.append("WCAG 4.1.2 — Przycisk formularza musi miec czytelna etykiete.")
        elif tag == "select":
            parts.append("WCAG 1.3.1 — Lista wyboru wymaga etykiety (label lub aria-label).")
        elif tag == "textarea":
            parts.append("WCAG 1.3.1 — Obszar tekstowy wymaga etykiety.")

        if role:
            parts.append(f"Rola ARIA: {role} — element semantycznie oznaczony dla technologii asystujacych.")

        if not parts:
            parts.append("Element interaktywny — dostepny z klawiatury zgodnie z WCAG 2.1.1.")

        return " ".join(parts)
