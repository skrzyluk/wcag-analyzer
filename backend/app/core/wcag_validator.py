"""
wcag_validator.py - Silnik walidacji WCAG 2.1 AA.

Zawiera ~20 checkerow fazy 1 (poziom A i AA) sprawdzanych
statycznie na drzewie DOM (BeautifulSoup).

Uzycie:
    from bs4 import BeautifulSoup
    from app.core.wcag_validator import WCAGValidator

    soup = BeautifulSoup(html, "lxml")
    validator = WCAGValidator()
    issues = validator.validate(soup, url="https://example.com/")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup, Tag


# ---------------------------------------------------------------------------
# Dataclass Issue
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    id:               str
    wcag_criterion:   str     # np. "1.1.1 Tresc nietekstowa"
    severity:         str     # "critical" | "major" | "minor" | "warning"
    description:      str
    recommendation:   str
    affected_elements: list[dict] = field(default_factory=list)
    # affected_elements: [{"tag": str, "html_snippet": str, "html_after": str}]


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def _snippet(el: Tag, max_len: int = 200) -> str:
    """Zwraca skrocony HTML elementu (bez zawartosci potomnej)."""
    try:
        raw = str(el)
        # Usun zawartosc wewnetrzna dla dlugich elementow
        if len(raw) > max_len:
            # Otwarcie tagu
            m = re.match(r"(<[^>]+>)", raw)
            return (m.group(1) + "...") if m else raw[:max_len] + "..."
        return raw
    except Exception:
        return str(el.name)


def _has_accessible_name(el: Tag) -> bool:
    """Sprawdza czy element ma dostepna nazwe (aria-label, aria-labelledby, title lub tekst)."""
    if el.get("aria-label", "").strip():
        return True
    if el.get("aria-labelledby", "").strip():
        return True
    if el.get("title", "").strip():
        return True
    text = el.get_text(strip=True)
    return bool(text)


def _is_visible(el: Tag) -> bool:
    """Prosta heurystyka widocznosci (pomija display:none / visibility:hidden w atrybucie style)."""
    style = el.get("style", "").lower()
    if "display:none" in style.replace(" ", "") or "display: none" in style:
        return False
    if "visibility:hidden" in style.replace(" ", "") or "visibility: hidden" in style:
        return False
    if el.get("hidden") is not None:
        return False
    if el.get("aria-hidden", "").lower() == "true":
        return False
    return True


def _contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Oblicza wspolczynnik kontrastu wg WCAG (uproszczone, dla kanalow RGB)."""
    def relative_luminance(hex_color: str) -> float:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 3:
            hex_color = "".join(c * 2 for c in hex_color)
        if len(hex_color) != 6:
            return 0.0
        r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        def linearize(c: float) -> float:
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = linearize(r), linearize(g), linearize(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1 = relative_luminance(fg_hex)
    l2 = relative_luminance(bg_hex)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _extract_inline_colors(style: str) -> tuple[Optional[str], Optional[str]]:
    """
    Wyodrebnia color i background-color z atrybutu style.
    Zwraca (fg_hex, bg_hex) lub None jesli nie znaleziono.
    Obsluguje tylko wartosci hex (#rgb, #rrggbb) i named colors (podstawowe).
    """
    NAMED = {
        "black": "000000", "white": "ffffff", "red": "ff0000",
        "green": "008000", "blue": "0000ff", "yellow": "ffff00",
        "gray": "808080", "grey": "808080", "navy": "000080",
        "silver": "c0c0c0", "maroon": "800000", "purple": "800080",
        "lime": "00ff00", "aqua": "00ffff", "teal": "008080",
        "orange": "ffa500", "pink": "ffc0cb",
    }

    def parse_color(val: str) -> Optional[str]:
        val = val.strip().lower()
        if val.startswith("#"):
            return val[1:]
        return NAMED.get(val)

    fg = bg = None
    # color:
    m = re.search(r"(?:^|;)\s*color\s*:\s*([^;]+)", style, re.I)
    if m:
        fg = parse_color(m.group(1))
    # background-color:
    m = re.search(r"background(?:-color)?\s*:\s*([^;]+)", style, re.I)
    if m:
        val = m.group(1).strip()
        # Ignoruj gradienty i url()
        if not any(kw in val.lower() for kw in ("gradient", "url(", "none", "transparent")):
            bg = parse_color(val)
    return fg, bg


# ---------------------------------------------------------------------------
# WCAGValidator
# ---------------------------------------------------------------------------

class WCAGValidator:
    """
    Silnik walidacji WCAG 2.1 AA (faza 1 — ~20 checkerow).

    Kazdy checker zwraca liste Issue. Metoda validate() agreguje
    wyniki wszystkich checkerow i nadaje unikalny identyfikator.
    """

    # Linki z textem wskazujacym na brak opisu
    GENERIC_LINK_TEXTS = {
        "kliknij tutaj", "kliknij", "tutaj", "wiecej", "czytaj wiecej",
        "link", "kliknij tu", "click here", "here", "read more", "more",
        "dalej", "sprawdz", "pobierz", "download",
    }

    def validate(self, soup: BeautifulSoup, url: str = "") -> list[Issue]:
        """
        Uruchamia wszystkie checkery i zwraca liste Issues.
        Kazdy Issue ma unikalny id w formacie 'c{kryterium}-{n}'.
        """
        all_issues: list[Issue] = []

        checkers = [
            self.check_1_1_1_alt_text,
            self.check_1_3_1_info_relationships,
            self.check_1_3_2_meaningful_sequence,
            self.check_1_3_5_identify_input_purpose,
            self.check_1_4_1_use_of_color,
            self.check_1_4_3_contrast,
            self.check_2_1_1_keyboard,
            self.check_2_4_1_bypass_blocks,
            self.check_2_4_2_page_titled,
            self.check_2_4_4_link_purpose,
            self.check_2_4_6_headings_labels,
            self.check_3_1_1_language,
            self.check_3_1_2_language_of_parts,
            self.check_3_2_1_on_focus,
            self.check_3_3_1_error_identification,
            self.check_3_3_2_labels_instructions,
            self.check_4_1_1_parsing,
            self.check_4_1_2_name_role_value,
            self.check_1_3_4_orientation,
            self.check_2_4_3_focus_order,
        ]

        for checker in checkers:
            try:
                issues = checker(soup)
                all_issues.extend(issues)
            except Exception:
                pass  # Checker nie blokuje pozostalych

        # Numeracja
        for i, issue in enumerate(all_issues, 1):
            issue.id = f"i{i}"

        return all_issues

    # ------------------------------------------------------------------
    # 1.1.1 Tresc nietekstowa (A)
    # ------------------------------------------------------------------

    def check_1_1_1_alt_text(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        for img in soup.find_all("img"):
            if not _is_visible(img):
                continue
            alt = img.get("alt")
            src = img.get("src", "")
            role = img.get("role", "")

            # Obraz dekoracyjny: alt="" lub role="presentation"
            if role in ("presentation", "none"):
                continue

            if alt is None:
                # Brak atrybutu alt
                snippet = _snippet(img)
                html_after = str(img).replace(">", ' alt="[OPIS OBRAZU]">', 1) if "alt" not in str(img) else snippet
                issues.append(Issue(
                    id="",
                    wcag_criterion="1.1.1 Tresc nietekstowa",
                    severity="critical",
                    description=(
                        f"Obraz nie posiada atrybutu alt. "
                        f"Uzytkownicy czytnikow ekranu nie otrzymaja zadnej informacji o tym obrazie."
                        + (f" (src: {src[:60]})" if src else "")
                    ),
                    recommendation=(
                        "Dodaj atrybut alt z krotkim opisem obrazu. "
                        "Jesli obraz jest dekoracyjny, uzyj alt=\"\"."
                    ),
                    affected_elements=[{
                        "tag": "img",
                        "html_snippet": snippet,
                        "html_after": html_after,
                    }],
                ))
            elif alt.strip() == "" and src:
                # alt="" — sprawdz czy to nie jest obraz funkcjonalny (w linku)
                parent = img.parent
                if parent and parent.name == "a" and not parent.get_text(strip=True):
                    link_href = parent.get("href", "")
                    issues.append(Issue(
                        id="",
                        wcag_criterion="1.1.1 Tresc nietekstowa",
                        severity="critical",
                        description=(
                            "Obraz wewnatrz linku ma alt=\"\", ale link nie zawiera tekstu. "
                            "Czytnik ekranu nie powie uzytkownikowi dokad prowadzi ten link."
                        ),
                        recommendation=(
                            f"Dodaj opisowy tekst alt do obrazu wewnatrz linku "
                            f"(np. alt=\"Strona glowna\"). "
                            f"Cel linku: {link_href[:80]}"
                        ),
                        affected_elements=[{
                            "tag": "a",
                            "html_snippet": _snippet(parent),
                            "html_after": "",
                        }],
                    ))
        return issues

    # ------------------------------------------------------------------
    # 1.3.1 Informacje i relacje (A)
    # ------------------------------------------------------------------

    def check_1_3_1_info_relationships(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []

        # Sprawdz czy jest przynajmniej jeden naglowek
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not headings:
            issues.append(Issue(
                id="",
                wcag_criterion="1.3.1 Informacje i relacje",
                severity="major",
                description=(
                    "Strona nie zawiera zadnych naglowkow (h1-h6). "
                    "Struktura naglowkow jest kluczowa dla nawigacji czytnikami ekranu."
                ),
                recommendation=(
                    "Dodaj hierarchie naglowkow. Zacznij od jednego <h1> "
                    "z tytulem strony, nastepnie uzyj h2, h3 dla kolejnych sekcji."
                ),
                affected_elements=[],
            ))

        # Tabele danych bez naglowkow (<th> lub scope)
        for table in soup.find_all("table"):
            if not _is_visible(table):
                continue
            # Sprawdz czy ma naglowki kolumn lub wierszy
            has_th = bool(table.find("th"))
            has_caption = bool(table.find("caption"))
            has_role_presentation = table.get("role", "") in ("presentation", "none")
            if not has_th and not has_role_presentation:
                issues.append(Issue(
                    id="",
                    wcag_criterion="1.3.1 Informacje i relacje",
                    severity="major",
                    description=(
                        "Tabela danych nie zawiera komorek naglowkowych (<th>). "
                        "Czytniki ekranu nie beda w stanie skojarzyc danych z naglowkami."
                    ),
                    recommendation=(
                        "Dodaj <th> dla naglowkow kolumn i/lub wierszy. "
                        "Uzyj atrybutu scope=\"col\" lub scope=\"row\"."
                    ),
                    affected_elements=[{
                        "tag": "table",
                        "html_snippet": _snippet(table),
                        "html_after": "",
                    }],
                ))

        # Listy nieuporządkowane/uporzadkowane tworzone przez <p> lub <br>
        # (Heurystyka: wiele <p> z kresca lub myslnikiem na poczatku)
        paragraphs = soup.find_all("p")
        bullet_like = [
            p for p in paragraphs
            if re.match(r"^\s*[-–•▪▸]\s", p.get_text() or "")
        ]
        if len(bullet_like) >= 3:
            issues.append(Issue(
                id="",
                wcag_criterion="1.3.1 Informacje i relacje",
                severity="minor",
                description=(
                    f"Znaleziono {len(bullet_like)} akapity zaczynajace sie "
                    f"od znaku myslnika/punktu — mozliwe ze lista nie jest "
                    f"zakodowana semantycznie jako <ul>/<ol>."
                ),
                recommendation=(
                    "Uzyj semantycznego znacznika <ul> lub <ol> zamiast "
                    "akapitow z recznym formatowaniem punktow."
                ),
                affected_elements=[{
                    "tag": "p",
                    "html_snippet": _snippet(bullet_like[0]),
                    "html_after": "",
                }],
            ))

        return issues

    # ------------------------------------------------------------------
    # 1.3.2 Znaczaca kolejnosc (A)
    # ------------------------------------------------------------------

    def check_1_3_2_meaningful_sequence(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Sprawdz elementy z position:absolute bez ARIA (moze zaburzac kolejnosc)
        abs_elements = []
        for el in soup.find_all(True):
            style = el.get("style", "").lower()
            if "position:absolute" in style.replace(" ", "") or "position: absolute" in style:
                if not el.get("aria-label") and not el.get("role"):
                    abs_elements.append(el)

        if len(abs_elements) >= 3:
            issues.append(Issue(
                id="",
                wcag_criterion="1.3.2 Znaczaca kolejnosc",
                severity="warning",
                description=(
                    f"Znaleziono {len(abs_elements)} elementow z position:absolute "
                    f"bez atrybutow ARIA. Moze to zaburzac logiczna kolejnosc "
                    f"czytania dla technologii asystujacych."
                ),
                recommendation=(
                    "Upewnij sie, ze kolejnosc w kodzie HTML odzwierciedla "
                    "logiczna kolejnosc czytania. Rozważ dodanie role i aria-label "
                    "do elementow absolutnie pozycjonowanych."
                ),
                affected_elements=[{
                    "tag": abs_elements[0].name,
                    "html_snippet": _snippet(abs_elements[0]),
                    "html_after": "",
                }],
            ))
        return issues

    # ------------------------------------------------------------------
    # 1.3.4 Orientacja (AA)
    # ------------------------------------------------------------------

    def check_1_3_4_orientation(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Sprawdz czy CSS nie blokuje orientacji przez orientation media query
        # (Statyczna analiza — szukamy w style blokad)
        for style_tag in soup.find_all("style"):
            text = style_tag.get_text()
            if "orientation:portrait" in text.replace(" ", "") and "display:none" in text.replace(" ", ""):
                issues.append(Issue(
                    id="",
                    wcag_criterion="1.3.4 Orientacja",
                    severity="major",
                    description=(
                        "Wykryto potencjalne blokowanie orientacji ekranu w CSS. "
                        "Tresc nie powinna byc ograniczona do jednej orientacji (portrait/landscape)."
                    ),
                    recommendation=(
                        "Usun blokade orientacji z CSS. Tresc musi byc dostepna "
                        "zarówno w trybie pionowym jak i poziomym."
                    ),
                    affected_elements=[],
                ))
        return issues

    # ------------------------------------------------------------------
    # 1.3.5 Cel pola formularza (AA)
    # ------------------------------------------------------------------

    def check_1_3_5_identify_input_purpose(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Pola, ktore powinny miec autocomplete
        PURPOSE_MAP = {
            "name": "name", "email": "email", "tel": "tel",
            "address": "street-address", "city": "address-level2",
            "zip": "postal-code", "postcode": "postal-code",
            "password": "current-password", "username": "username",
        }
        for inp in soup.find_all("input"):
            if not _is_visible(inp):
                continue
            input_type = (inp.get("type") or "text").lower()
            if input_type in ("hidden", "submit", "button", "reset", "image", "file", "range", "color"):
                continue
            name = (inp.get("name") or inp.get("id") or inp.get("placeholder") or "").lower()
            autocomplete = inp.get("autocomplete", "")
            if autocomplete in ("off", "false"):
                continue
            for keyword, ac_val in PURPOSE_MAP.items():
                if keyword in name and not autocomplete:
                    issues.append(Issue(
                        id="",
                        wcag_criterion="1.3.5 Cel pola formularza",
                        severity="minor",
                        description=(
                            f"Pole '{name}' moze byc polem '{keyword}', ale nie ma "
                            f"atrybutu autocomplete. Brak autocomplete utrudnia "
                            f"uzywanie menedjera hasel i autouzupelniania."
                        ),
                        recommendation=(
                            f"Dodaj autocomplete=\"{ac_val}\" do tego pola formularza."
                        ),
                        affected_elements=[{
                            "tag": "input",
                            "html_snippet": _snippet(inp),
                            "html_after": str(inp).replace(">", f' autocomplete="{ac_val}">', 1),
                        }],
                    ))
                    break
        return issues

    # ------------------------------------------------------------------
    # 1.4.1 Uzycie koloru (A)
    # ------------------------------------------------------------------

    def check_1_4_1_use_of_color(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Linki bez podkreslenia i bez innej wizualnej cechy rozrózniajace od tekstu
        for a in soup.find_all("a", href=True):
            if not _is_visible(a):
                continue
            style = a.get("style", "").lower()
            # Sprawdz text-decoration:none bez innej cechy (border, outline, font-weight)
            if "text-decoration:none" in style.replace(" ", "") or "text-decoration: none" in style:
                has_other = any(k in style for k in ("border", "outline", "font-weight:bold", "background"))
                if not has_other:
                    issues.append(Issue(
                        id="",
                        wcag_criterion="1.4.1 Uzycie koloru",
                        severity="major",
                        description=(
                            "Link ma wylaczone podkreslenie (text-decoration:none) "
                            "bez zadnej innej wizualnej cechy odrozniajace go od "
                            "otaczajacego tekstu. Uzytkownicy z zaburzeniami percepcji "
                            "koloru nie beda mogli zidentyfikowac linku."
                        ),
                        recommendation=(
                            "Dodaj inne oznaczenie wizualne: podkreslenie, "
                            "obramowanie, pogrubienie lub ikone. "
                            "Sam kolor nie wystarczy jako jedyne oznaczenie."
                        ),
                        affected_elements=[{
                            "tag": "a",
                            "html_snippet": _snippet(a),
                            "html_after": "",
                        }],
                    ))
        return issues

    # ------------------------------------------------------------------
    # 1.4.3 Kontrast minimalny (AA)
    # ------------------------------------------------------------------

    def check_1_4_3_contrast(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        MIN_CONTRAST_NORMAL = 4.5
        MIN_CONTRAST_LARGE  = 3.0

        text_elements = soup.find_all(["p", "span", "div", "li", "td", "th",
                                       "h1", "h2", "h3", "h4", "h5", "h6",
                                       "a", "button", "label"])

        for el in text_elements:
            if not _is_visible(el):
                continue
            style = el.get("style", "")
            if not style:
                continue
            fg, bg = _extract_inline_colors(style)
            if fg is None or bg is None:
                continue

            try:
                ratio = _contrast_ratio(fg, bg)
            except Exception:
                continue

            # Duzy tekst: font-size >= 18pt lub 14pt bold
            is_large = False
            fs_match = re.search(r"font-size\s*:\s*([\d.]+)(pt|px|em|rem)", style, re.I)
            if fs_match:
                size_val = float(fs_match.group(1))
                unit = fs_match.group(2).lower()
                is_bold = "font-weight:bold" in style.replace(" ", "") or "font-weight: bold" in style
                if unit == "pt":
                    is_large = size_val >= 18 or (is_bold and size_val >= 14)
                elif unit == "px":
                    is_large = size_val >= 24 or (is_bold and size_val >= 18.67)

            threshold = MIN_CONTRAST_LARGE if is_large else MIN_CONTRAST_NORMAL
            if ratio < threshold:
                tag_name = el.name
                issues.append(Issue(
                    id="",
                    wcag_criterion="1.4.3 Kontrast (minimalny)",
                    severity="major",
                    description=(
                        f"Niewystarczajacy kontrast tekstu: {ratio:.2f}:1 "
                        f"(wymagane minimum: {threshold}:1). "
                        f"Kolor tekstu: #{fg}, tlo: #{bg}."
                    ),
                    recommendation=(
                        f"Zmien kolor tekstu lub tla tak, aby wspolczynnik "
                        f"kontrastu wynosil co najmniej {threshold}:1. "
                        f"Aktualny wspolczynnik: {ratio:.2f}:1."
                    ),
                    affected_elements=[{
                        "tag": tag_name,
                        "html_snippet": _snippet(el),
                        "html_after": "",
                    }],
                ))
        return issues

    # ------------------------------------------------------------------
    # 2.1.1 Klawiatura (A)
    # ------------------------------------------------------------------

    def check_2_1_1_keyboard(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []

        # Elementy interaktywne z onclick ale bez href/role/tabindex
        for el in soup.find_all(True):
            if not _is_visible(el):
                continue
            has_onclick = el.get("onclick") or el.get("ng-click") or el.get("@click")
            if not has_onclick:
                continue
            tag = el.name
            if tag in ("a", "button", "input", "select", "textarea", "summary"):
                continue  # Natywnie dostepne
            has_role = el.get("role") in (
                "button", "link", "menuitem", "option", "tab", "checkbox", "radio"
            )
            has_tabindex = el.get("tabindex") is not None
            if not has_role and not has_tabindex:
                issues.append(Issue(
                    id="",
                    wcag_criterion="2.1.1 Klawiatura",
                    severity="critical",
                    description=(
                        f"Element <{tag}> ma zdarzenie onclick, ale nie jest "
                        f"dostepny z klawiatury (brak role ani tabindex). "
                        f"Uzytkownicy bez myszy nie beda mogli go aktywowac."
                    ),
                    recommendation=(
                        f"Zamien <{tag}> na <button> lub dodaj "
                        f"role=\"button\" tabindex=\"0\" oraz obsluge "
                        f"zdarzen keydown (Enter, Spacja)."
                    ),
                    affected_elements=[{
                        "tag": tag,
                        "html_snippet": _snippet(el),
                        "html_after": "",
                    }],
                ))

        # Linki z href="javascript:void(0)" bez semantyki przycisku
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "javascript:" in href.lower() and not a.get("role"):
                issues.append(Issue(
                    id="",
                    wcag_criterion="2.1.1 Klawiatura",
                    severity="major",
                    description=(
                        "Link z href=\"javascript:void(0)\" bez roli i etykiety. "
                        "Moze byc niedostepny dla technologii asystujacych."
                    ),
                    recommendation=(
                        "Uzyj <button> zamiast <a href='javascript:'> "
                        "dla elementow aktywowanych JS."
                    ),
                    affected_elements=[{
                        "tag": "a",
                        "html_snippet": _snippet(a),
                        "html_after": "",
                    }],
                ))

        return issues

    # ------------------------------------------------------------------
    # 2.4.1 Mozliwosc pominiecia blokow (A)
    # ------------------------------------------------------------------

    def check_2_4_1_bypass_blocks(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Sprawdz czy jest skip-link lub landmark <main>
        has_skip_link = False
        for a in soup.find_all("a", href=True)[:15]:
            href = a.get("href", "")
            if href.startswith("#"):
                text = a.get_text(strip=True).lower()
                aria = a.get("aria-label", "").lower()
                if any(kw in text + aria for kw in (
                    "skip", "przejdz", "pomij", "tresc", "content", "main",
                )):
                    has_skip_link = True
                    break
                if href[1:].lower() in ("main", "content", "tresc", "main-content"):
                    has_skip_link = True
                    break

        has_main = bool(soup.find("main") or soup.find(attrs={"role": "main"}))
        has_nav  = bool(soup.find("nav")  or soup.find(attrs={"role": "navigation"}))

        if not has_skip_link and has_nav and not has_main:
            issues.append(Issue(
                id="",
                wcag_criterion="2.4.1 Mozliwosc pominiecia blokow",
                severity="major",
                description=(
                    "Brak mechanizmu pomijania nawigacji (skip-link lub <main>). "
                    "Uzytkownicy klawiatury i czytnikow ekranu sa zmuszeni "
                    "przechodzic przez cala nawigacje na kazdej stronie."
                ),
                recommendation=(
                    "Dodaj skip-link na poczatku strony: "
                    "<a href='#main-content'>Przejdz do tresci</a> "
                    "lub oznacz glowna tresc znacznikiem <main id='main-content'>."
                ),
                affected_elements=[],
            ))

        return issues

    # ------------------------------------------------------------------
    # 2.4.2 Tytul strony (A)
    # ------------------------------------------------------------------

    def check_2_4_2_page_titled(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        title_tag = soup.find("title")
        if not title_tag or not title_tag.get_text(strip=True):
            issues.append(Issue(
                id="",
                wcag_criterion="2.4.2 Tytul strony",
                severity="critical",
                description=(
                    "Strona nie ma tytulu (<title>) lub tytul jest pusty. "
                    "Tytul jest pierwsza informacja odczytywana przez czytnik ekranu "
                    "i jest kluczowy do identyfikacji zakladki przegladarki."
                ),
                recommendation=(
                    "Dodaj znacznik <title> w sekcji <head> z unikalnym, "
                    "opisowym tytulem strony, np. "
                    "<title>Nazwa strony — Nazwa serwisu</title>"
                ),
                affected_elements=[],
            ))
        return issues

    # ------------------------------------------------------------------
    # 2.4.3 Kolejnosc fokusu (A)
    # ------------------------------------------------------------------

    def check_2_4_3_focus_order(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Elementy z tabindex > 0 zaburzaja naturalna kolejnosc DOM
        positive_ti_elements = []
        for el in soup.find_all(True):
            ti = el.get("tabindex")
            if ti is not None:
                try:
                    if int(ti) > 0:
                        positive_ti_elements.append(el)
                except ValueError:
                    pass

        if positive_ti_elements:
            issues.append(Issue(
                id="",
                wcag_criterion="2.4.3 Kolejnosc fokusu",
                severity="major",
                description=(
                    f"Znaleziono {len(positive_ti_elements)} elementow "
                    f"z tabindex > 0 (np. tabindex=\"{positive_ti_elements[0].get('tabindex')}\"). "
                    f"Uzycie tabindex > 0 zaburza naturalna kolejnosc fokusa "
                    f"i moze byc mylacoce dla uzytkownikow klawiatury."
                ),
                recommendation=(
                    "Uzyj tabindex=\"0\" lub tabindex=\"-1\" zamiast wartosci > 0. "
                    "Kolejnosc fokusa powinna wynikac z kolejnosci elementow w kodzie HTML."
                ),
                affected_elements=[{
                    "tag": positive_ti_elements[0].name,
                    "html_snippet": _snippet(positive_ti_elements[0]),
                    "html_after": str(positive_ti_elements[0]).replace(
                        f'tabindex="{positive_ti_elements[0].get("tabindex")}"',
                        'tabindex="0"'
                    ),
                }],
            ))
        return issues

    # ------------------------------------------------------------------
    # 2.4.4 Cel linku (A)
    # ------------------------------------------------------------------

    def check_2_4_4_link_purpose(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        for a in soup.find_all("a", href=True):
            if not _is_visible(a):
                continue
            href = a.get("href", "")
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue

            # Pobierz etykiete dostepnosci
            aria_label = a.get("aria-label", "").strip()
            aria_desc  = a.get("aria-describedby", "").strip()
            title      = a.get("title", "").strip()
            text       = a.get_text(strip=True).lower()

            effective_label = (aria_label or title or text).lower()

            if not effective_label:
                # Pusty link
                has_img = bool(a.find("img"))
                has_svg = bool(a.find("svg"))
                if not has_img and not has_svg and not aria_desc:
                    issues.append(Issue(
                        id="",
                        wcag_criterion="2.4.4 Cel linku (w kontekscie)",
                        severity="critical",
                        description=(
                            f"Link jest pusty — nie ma tekstu ani etykiety ARIA. "
                            f"Czytnik ekranu poda tylko URL: {href[:80]}"
                        ),
                        recommendation=(
                            "Dodaj opisowy tekst do linku lub uzyj "
                            "aria-label=\"Opis celu linku\"."
                        ),
                        affected_elements=[{
                            "tag": "a",
                            "html_snippet": _snippet(a),
                            "html_after": str(a).replace(">", ' aria-label="[OPIS]">', 1),
                        }],
                    ))
            elif effective_label in self.GENERIC_LINK_TEXTS:
                issues.append(Issue(
                    id="",
                    wcag_criterion="2.4.4 Cel linku (w kontekscie)",
                    severity="major",
                    description=(
                        f"Link zawiera nieopisowy tekst: \"{text}\". "
                        f"Uzytkownicy czytnikow ekranu przegladajacy liste linkow "
                        f"nie beda wiedziec dokad prowadzi ten link."
                    ),
                    recommendation=(
                        f"Zastap tekst linku opisowym sformulowaniem, np. "
                        f"\"Czytaj wiecej o [temacie]\" lub dodaj "
                        f"aria-label=\"Opis celu linku\"."
                    ),
                    affected_elements=[{
                        "tag": "a",
                        "html_snippet": _snippet(a),
                        "html_after": "",
                    }],
                ))
        return issues

    # ------------------------------------------------------------------
    # 2.4.6 Naglowki i etykiety (AA)
    # ------------------------------------------------------------------

    def check_2_4_6_headings_labels(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []

        # Naglowki nie powinny byc puste
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if not h.get_text(strip=True) and not h.get("aria-label"):
                issues.append(Issue(
                    id="",
                    wcag_criterion="2.4.6 Naglowki i etykiety",
                    severity="major",
                    description=(
                        f"Pusty naglowek <{h.name}>. "
                        f"Puste naglowki myla uzytkownikow czytnikow ekranu "
                        f"przegladajacych strukture strony."
                    ),
                    recommendation=(
                        f"Usun pusty znacznik <{h.name}> lub dodaj "
                        f"opisowy tekst naglowka."
                    ),
                    affected_elements=[{
                        "tag": h.name,
                        "html_snippet": _snippet(h),
                        "html_after": "",
                    }],
                ))

        # Powinien byc tylko jeden <h1>
        h1_list = soup.find_all("h1")
        if len(h1_list) > 1:
            issues.append(Issue(
                id="",
                wcag_criterion="2.4.6 Naglowki i etykiety",
                severity="minor",
                description=(
                    f"Strona zawiera {len(h1_list)} naglowkow <h1>. "
                    f"Najlepsza praktyka: jeden <h1> jako glowny tytul strony."
                ),
                recommendation=(
                    "Zostaw jeden <h1> jako glowny tytul strony. "
                    "Pozostale naglowki zmien na <h2> lub nizszy poziom."
                ),
                affected_elements=[{
                    "tag": "h1",
                    "html_snippet": _snippet(h1_list[1]),
                    "html_after": "",
                }],
            ))

        # Sprawdz hierarchie naglowkow (nie pomijaj poziomow)
        heading_levels = [int(h.name[1]) for h in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        )]
        for i in range(1, len(heading_levels)):
            if heading_levels[i] - heading_levels[i - 1] > 1:
                issues.append(Issue(
                    id="",
                    wcag_criterion="2.4.6 Naglowki i etykiety",
                    severity="minor",
                    description=(
                        f"Hierarchia naglowkow ma pominiety poziom: "
                        f"h{heading_levels[i-1]} → h{heading_levels[i]}. "
                        f"Pomijanie poziomow naglowkow moze mylic uzytkownikow "
                        f"czytnikow ekranu."
                    ),
                    recommendation=(
                        f"Uzyj h{heading_levels[i-1]+1} zamiast h{heading_levels[i]}, "
                        f"lub dodaj brakujacy posredni naglowek."
                    ),
                    affected_elements=[],
                ))
                break  # Raportuj tylko pierwszy problem

        return issues

    # ------------------------------------------------------------------
    # 3.1.1 Jezyk strony (A)
    # ------------------------------------------------------------------

    def check_3_1_1_language(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        html_tag = soup.find("html")
        if html_tag:
            lang = html_tag.get("lang", "").strip()
            if not lang:
                issues.append(Issue(
                    id="",
                    wcag_criterion="3.1.1 Jezyk strony",
                    severity="critical",
                    description=(
                        "Element <html> nie ma atrybutu lang. "
                        "Czytniki ekranu nie beda wiedziec, w jakim jezyku "
                        "czytac zawartosc strony."
                    ),
                    recommendation=(
                        "Dodaj atrybut lang do elementu <html>, np. "
                        "<html lang=\"pl\"> dla jezyka polskiego."
                    ),
                    affected_elements=[{
                        "tag": "html",
                        "html_snippet": "<html>",
                        "html_after": "<html lang=\"pl\">",
                    }],
                ))
            elif not re.match(r"^[a-z]{2,3}(-[A-Za-z]{2,})?$", lang):
                issues.append(Issue(
                    id="",
                    wcag_criterion="3.1.1 Jezyk strony",
                    severity="major",
                    description=(
                        f"Atrybut lang ma niepoprawna wartosc: \"{lang}\". "
                        f"Wartosc powinna byc kodem BCP 47 (np. \"pl\", \"en\", \"en-US\")."
                    ),
                    recommendation=(
                        f"Zmien lang=\"{lang}\" na poprawny kod BCP 47, "
                        f"np. lang=\"pl\" dla jezyka polskiego."
                    ),
                    affected_elements=[{
                        "tag": "html",
                        "html_snippet": f"<html lang=\"{lang}\">",
                        "html_after": "<html lang=\"pl\">",
                    }],
                ))
        return issues

    # ------------------------------------------------------------------
    # 3.1.2 Jezyk czesci (AA)
    # ------------------------------------------------------------------

    def check_3_1_2_language_of_parts(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        html_lang = (soup.find("html") or {}).get("lang", "").lower()[:2] if soup.find("html") else ""

        for el in soup.find_all(True):
            lang = el.get("lang", "")
            if lang and el.name != "html":
                if not re.match(r"^[a-z]{2,3}(-[A-Za-z]{2,})?$", lang):
                    issues.append(Issue(
                        id="",
                        wcag_criterion="3.1.2 Jezyk czesci",
                        severity="minor",
                        description=(
                            f"Element <{el.name}> ma niepoprawny atrybut lang=\"{lang}\". "
                            f"Atrybuty lang musza byc poprawnymi kodami BCP 47."
                        ),
                        recommendation=(
                            f"Popraw lang=\"{lang}\" na poprawny kod BCP 47."
                        ),
                        affected_elements=[{
                            "tag": el.name,
                            "html_snippet": _snippet(el),
                            "html_after": "",
                        }],
                    ))
        return issues

    # ------------------------------------------------------------------
    # 3.2.1 Po otrzymaniu fokusu (A)
    # ------------------------------------------------------------------

    def check_3_2_1_on_focus(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Sprawdz elementy z onfocus powodujacym zmiane kontekstu
        DANGEROUS_PATTERNS = ("window.location", "window.open", "location.href", "submit()")
        for el in soup.find_all(True):
            onfocus = el.get("onfocus", "")
            if any(p in onfocus for p in DANGEROUS_PATTERNS):
                issues.append(Issue(
                    id="",
                    wcag_criterion="3.2.1 Po otrzymaniu fokusu",
                    severity="critical",
                    description=(
                        f"Element <{el.name}> ma zdarzenie onfocus, ktore moze "
                        f"powodowac zmiane kontekstu (nawigacja, submit). "
                        f"Otrzymanie fokusu nie powinno inicjowac zadnych akcji."
                    ),
                    recommendation=(
                        "Usun automatyczna akcje z onfocus. "
                        "Inicjowanie zmian (nawigacja, submit) powinno byc "
                        "wyzwalane tylko przez swiadoma akcje uzytkownika."
                    ),
                    affected_elements=[{
                        "tag": el.name,
                        "html_snippet": _snippet(el),
                        "html_after": "",
                    }],
                ))
        return issues

    # ------------------------------------------------------------------
    # 3.3.1 Identyfikacja bledow (A)
    # ------------------------------------------------------------------

    def check_3_3_1_error_identification(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        # Formularze z polami required bez aria-required lub aria-describedby
        for inp in soup.find_all(["input", "select", "textarea"]):
            if not _is_visible(inp):
                continue
            is_required = (
                inp.get("required") is not None
                or inp.get("aria-required") == "true"
            )
            if not is_required:
                continue
            input_type = (inp.get("type") or "text").lower()
            if input_type in ("hidden", "submit", "button", "reset"):
                continue
            has_error_handling = (
                inp.get("aria-describedby")
                or inp.get("aria-invalid")
                or inp.get("pattern")
            )
            if not has_error_handling:
                issues.append(Issue(
                    id="",
                    wcag_criterion="3.3.1 Identyfikacja bledow",
                    severity="major",
                    description=(
                        f"Pole obowiazkowe ({inp.name}) nie ma "
                        f"powiazanego komunikatu o bledzie (aria-describedby) "
                        f"ani mechanizmu identyfikacji niepoprawnych danych."
                    ),
                    recommendation=(
                        "Dodaj aria-describedby wskazujacy na element z komunikatem bledu. "
                        "Przy blednej wartosci ustaw aria-invalid=\"true\"."
                    ),
                    affected_elements=[{
                        "tag": inp.name,
                        "html_snippet": _snippet(inp),
                        "html_after": str(inp).replace(">",
                            ' aria-describedby="error-msg" aria-invalid="false">',
                            1
                        ),
                    }],
                ))
        return issues

    # ------------------------------------------------------------------
    # 3.3.2 Etykiety lub instrukcje (A)
    # ------------------------------------------------------------------

    def check_3_3_2_labels_instructions(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []
        for inp in soup.find_all(["input", "select", "textarea"]):
            if not _is_visible(inp):
                continue
            input_type = (inp.get("type") or "text").lower()
            if input_type in ("hidden", "submit", "button", "reset", "image"):
                continue

            has_label = False

            # aria-label
            if inp.get("aria-label", "").strip():
                has_label = True

            # aria-labelledby
            if not has_label and inp.get("aria-labelledby", "").strip():
                has_label = True

            # <label for="...">
            if not has_label:
                inp_id = inp.get("id")
                if inp_id:
                    label = soup.find("label", attrs={"for": inp_id})
                    if label and label.get_text(strip=True):
                        has_label = True

            # <label> otaczajacy element
            if not has_label:
                parent = inp.parent
                if parent and parent.name == "label" and parent.get_text(strip=True):
                    has_label = True

            # title jako ostatecznosc
            if not has_label and inp.get("title", "").strip():
                has_label = True
                # To jest dopuszczalne, ale nie optymalne
                issues.append(Issue(
                    id="",
                    wcag_criterion="3.3.2 Etykiety lub instrukcje",
                    severity="minor",
                    description=(
                        f"Pole ({inp.name}) ma etykiete tylko w atrybucie title=\"{inp.get('title')}\". "
                        f"Atrybut title nie jest zawsze prezentowany przez technologie asystujace."
                    ),
                    recommendation=(
                        "Uzyj <label for=\"...\"> lub aria-label zamiast "
                        "polegania wylacznie na atrybucie title."
                    ),
                    affected_elements=[{
                        "tag": inp.name,
                        "html_snippet": _snippet(inp),
                        "html_after": "",
                    }],
                ))
                continue

            if not has_label:
                placeholder = inp.get("placeholder", "")
                issues.append(Issue(
                    id="",
                    wcag_criterion="3.3.2 Etykiety lub instrukcje",
                    severity="critical",
                    description=(
                        f"Pole formularza ({inp.name}"
                        + (f", placeholder=\"{placeholder}\"" if placeholder else "")
                        + f") nie ma dostepnej etykiety. "
                        f"Uzytkownicy czytnikow ekranu nie beda wiedziec co wpisac."
                    ),
                    recommendation=(
                        "Dodaj <label for=\"id_pola\">Etykieta</label> lub "
                        "aria-label=\"Etykieta\" do pola formularza."
                    ),
                    affected_elements=[{
                        "tag": inp.name,
                        "html_snippet": _snippet(inp),
                        "html_after": str(inp).replace(">", ' aria-label="[ETYKIETA]">', 1),
                    }],
                ))
        return issues

    # ------------------------------------------------------------------
    # 4.1.1 Parsowanie (A)
    # ------------------------------------------------------------------

    def check_4_1_1_parsing(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []

        # Zduplikowane ID
        all_ids: list[str] = []
        duplicate_ids: set[str] = set()
        for el in soup.find_all(id=True):
            eid = el.get("id")
            if eid in all_ids:
                duplicate_ids.add(eid)
            else:
                all_ids.append(eid)

        for eid in list(duplicate_ids)[:5]:  # Max 5 reportow
            issues.append(Issue(
                id="",
                wcag_criterion="4.1.1 Parsowanie",
                severity="major",
                description=(
                    f"Zduplikowany atrybut id=\"{eid}\". "
                    f"Duplikaty ID powoduja nieoczekiwane zachowanie przy "
                    f"uzywaniu ARIA i JavaScript."
                ),
                recommendation=(
                    f"Upewnij sie, ze kazdy id jest unikalny w obrebie dokumentu. "
                    f"Zmien jedna z instancji id=\"{eid}\"."
                ),
                affected_elements=[{
                    "tag": el.name,
                    "html_snippet": _snippet(el),
                    "html_after": "",
                } for el in soup.find_all(id=eid)[:2]],
            ))

        return issues

    # ------------------------------------------------------------------
    # 4.1.2 Nazwa, rola, wartosc (A)
    # ------------------------------------------------------------------

    def check_4_1_2_name_role_value(self, soup: BeautifulSoup) -> list[Issue]:
        issues = []

        # Przyciski bez dostepnej nazwy
        for btn in soup.find_all("button"):
            if not _is_visible(btn):
                continue
            if not _has_accessible_name(btn):
                issues.append(Issue(
                    id="",
                    wcag_criterion="4.1.2 Nazwa, rola, wartosc",
                    severity="critical",
                    description=(
                        "Przycisk (<button>) nie ma dostepnej nazwy. "
                        "Czytnik ekranu powie jedynie \"przycisk\" bez zadnego opisu."
                    ),
                    recommendation=(
                        "Dodaj tekst wewnatrz przycisku, aria-label lub aria-labelledby."
                    ),
                    affected_elements=[{
                        "tag": "button",
                        "html_snippet": _snippet(btn),
                        "html_after": str(btn).replace(">", ' aria-label="[OPIS]">', 1),
                    }],
                ))

        # ARIA role bez wymaganych atrybutow
        REQUIRED_ARIA_PROPS = {
            "checkbox":  ["aria-checked"],
            "radio":     ["aria-checked"],
            "slider":    ["aria-valuenow", "aria-valuemin", "aria-valuemax"],
            "progressbar": ["aria-valuenow"],
            "combobox":  ["aria-expanded"],
            "listbox":   [],
            "option":    ["aria-selected"],
            "tab":       ["aria-selected"],
            "tabpanel":  [],
        }
        for el in soup.find_all(True):
            role = el.get("role", "")
            if role in REQUIRED_ARIA_PROPS:
                for required_prop in REQUIRED_ARIA_PROPS[role]:
                    if el.get(required_prop) is None:
                        issues.append(Issue(
                            id="",
                            wcag_criterion="4.1.2 Nazwa, rola, wartosc",
                            severity="major",
                            description=(
                                f"Element z role=\"{role}\" nie ma wymaganego "
                                f"atrybutu ARIA: {required_prop}."
                            ),
                            recommendation=(
                                f"Dodaj atrybut {required_prop} do elementu "
                                f"z role=\"{role}\"."
                            ),
                            affected_elements=[{
                                "tag": el.name,
                                "html_snippet": _snippet(el),
                                "html_after": str(el).replace(
                                    ">", f' {required_prop}="...">', 1
                                ),
                            }],
                        ))
                        break  # Jeden blad na element

        # input[type=image] bez alt
        for img_input in soup.find_all("input", type="image"):
            if not img_input.get("alt") and not img_input.get("aria-label"):
                issues.append(Issue(
                    id="",
                    wcag_criterion="4.1.2 Nazwa, rola, wartosc",
                    severity="critical",
                    description=(
                        "<input type=\"image\"> nie ma atrybutu alt. "
                        "Przycisk graficzny musi miec opis tekstowy."
                    ),
                    recommendation=(
                        "Dodaj alt=\"Opis funkcji przycisku\" do "
                        "<input type=\"image\">."
                    ),
                    affected_elements=[{
                        "tag": "input",
                        "html_snippet": _snippet(img_input),
                        "html_after": str(img_input).replace(">", ' alt="[OPIS]">', 1),
                    }],
                ))

        return issues
