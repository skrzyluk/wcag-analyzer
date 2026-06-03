# -*- coding: utf-8 -*-
"""
Słownik kryteriów sukcesu WCAG 2.1 — poziomy A i AA.

Źródło: Polskie tłumaczenie WCAG 2.1, W3C, 13 kwietnia 2021
URL: https://www.w3.org/Translations/WCAG21-pl-20210413/

Struktura każdego wpisu:
    name        — polska nazwa kryterium sukcesu
    level       — poziom zgodności: "A" lub "AA"
    pillar      — polska nazwa filara WCAG
    pillar_num  — numer filara (1–4)
    description — pełny cytat kryterium sukcesu z polskiego tłumaczenia W3C

Użycie:
    from backend.app.data.wcag_descriptions import WCAG_CRITERIA, get_criterion

    c = get_criterion("1.4.3")
    print(c["name"])        # "Kontrast (minimum)"
    print(c["level"])       # "AA"
    print(c["pillar"])      # "Postrzegalność"
    print(c["description"]) # pełny cytat...
"""

from __future__ import annotations
from typing import TypedDict, Literal


# ---------------------------------------------------------------------------
# Typy
# ---------------------------------------------------------------------------

Pillar = Literal["Postrzegalność", "Funkcjonalność", "Zrozumiałość", "Solidność"]
Level  = Literal["A", "AA"]


class WcagCriterion(TypedDict):
    name:        str
    level:       Level
    pillar:      Pillar
    pillar_num:  int
    description: str


# ---------------------------------------------------------------------------
# Słownik główny — 50 kryteriów (30 × A, 20 × AA)
# ---------------------------------------------------------------------------

WCAG_CRITERIA: dict[str, WcagCriterion] = {

    # ════════════════════════════════════════════════════════════════════════
    # FILAR 1 — POSTRZEGALNOŚĆ
    # ════════════════════════════════════════════════════════════════════════

    # ── Wytyczna 1.1: Alternatywa tekstowa ──────────────────────────────────
    "1.1.1": {
        "name":       "Treść nietekstowa",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Wszelkie treści nietekstowe przedstawione użytkownikowi mają swoją tekstową "
            "alternatywę, która służy tym samym celom, z wyjątkiem sytuacji opisanych poniżej: "
            "Kontrolki i wprowadzanie danych przez użytkownika — Jeśli treść nietekstowa jest "
            "kontrolką użytkownika lub polem wprowadzania danych, posiada wtedy nazwę opisującą "
            "jej przeznaczenie; "
            "Multimedia — Jeśli treścią nietekstową są media oparte na czasie, wtedy alternatywa "
            "tekstowa zawiera przynajmniej opisowe określenie treści nietekstowej; "
            "Test — Jeśli treść nietekstowa jest testem lub ćwiczeniem, które utraciłoby swój "
            "sens ze względu na przedstawienie tej samej treści w postaci tekstu, wtedy "
            "alternatywa w postaci tekstu podawać powinna przynajmniej opis pozwalający zrozumieć "
            "przeznaczenie treści nietekstowej; "
            "Odczucie zmysłowe — Jeśli treść nietekstowa ma za zadanie przede wszystkim tworzyć "
            "konkretne odczucie zmysłowe, wtedy alternatywa w postaci tekstu jest opisem "
            "pozwalającym zrozumieć przeznaczenie treści nietekstowej; "
            "CAPTCHA — Jeśli celem treści nietekstowej jest potwierdzenie, że do treści ma dostęp "
            "człowiek, a nie komputer, wtedy dostarcza się alternatywę w postaci tekstu, która "
            "identyfikuje oraz opisuje cel treści nietekstowej. Dostarcza się również "
            "alternatywnych zabezpieczeń typu CAPTCHA, dostosowanych do różnych możliwości "
            "percepcji użytkowników, uwzględniając różne rodzaje niepełnosprawności; "
            "Cele dekoracyjne, formatowanie, treść niewidoczna — Jeśli treść nietekstowa pełni "
            "funkcję czysto dekoracyjną, używana jest do formatowania wizualnego lub też nie jest "
            "przedstawiana użytkownikowi, powinna być wdrożona w sposób umożliwiający technologiom "
            "wspomagającym jej zignorowanie."
        ),
    },

    # ── Wytyczna 1.2: Multimedia ─────────────────────────────────────────────
    "1.2.1": {
        "name":       "Tylko audio lub tylko wideo (nagranie)",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Dla mediów nagranych w systemie tylko audio lub tylko wideo stosuje się następujące "
            "zasady, z wyjątkiem sytuacji, kiedy nagranie audio lub wideo jest alternatywą dla "
            "tekstu i w taki sposób jest oznaczone: "
            "Alternatywa dla audio — Zapewniona jest alternatywa tekstowa dla nagrań dźwiękowych "
            "przedstawiająca tę samą treść, co nagranie audio; "
            "Alternatywa dla wideo — Zapewniona jest alternatywa tekstowa albo audiodeskrypcja "
            "dla nagrań zawierających tylko wideo przedstawiająca tę samą treść, co nagranie wideo."
        ),
    },
    "1.2.2": {
        "name":       "Napisy rozszerzone (nagranie)",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Do wszystkich nagrań audio w multimediach zsynchronizowanych (dźwięk i obraz), "
            "z wyjątkiem sytuacji, kiedy są one alternatywami dla tekstu i w taki sposób są "
            "oznaczone, zapewnione są napisy rozszerzone."
        ),
    },
    "1.2.3": {
        "name":       "Audiodeskrypcja lub alternatywa tekstowa dla mediów (nagranie)",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Zapewniona jest alternatywa dla multimediów lub audiodeskrypcja dla nagrań wideo "
            "w multimediach zsynchronizowanych (dźwięk i obraz), z wyjątkiem sytuacji, kiedy "
            "są one alternatywami dla tekstu i w taki sposób są oznaczone."
        ),
    },
    "1.2.4": {
        "name":       "Napisy rozszerzone (na żywo)",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Do wszystkich treści audio w multimediach zsynchronizowanych (dźwięk i obraz) "
            "przekazywanych na żywo zapewnione są napisy rozszerzone."
        ),
    },
    "1.2.5": {
        "name":       "Audiodeskrypcja (nagranie)",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Zapewniona jest audiodeskrypcja dla wszystkich nagrań wideo "
            "w multimediach zsynchronizowanych."
        ),
    },

    # ── Wytyczna 1.3: Możliwość adaptacji ───────────────────────────────────
    "1.3.1": {
        "name":       "Informacje i relacje",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Informacje, struktura oraz relacje między treściami przekazywane poprzez prezentację "
            "mogą być odczytane przez program komputerowy lub istnieją w postaci tekstu."
        ),
    },
    "1.3.2": {
        "name":       "Zrozumiała kolejność",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Jeśli kolejność, w jakiej przedstawiona jest treść, ma znaczenie dla zrozumienia "
            "treści — prawidłowa kolejność odczytu musi być określona programowo."
        ),
    },
    "1.3.3": {
        "name":       "Właściwości zmysłowe",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Instrukcje co do zrozumienia i operowania treścią nie opierają się wyłącznie na "
            "właściwościach zmysłowych, takich jak: kształt, rozmiar, wzrokowa lokalizacja, "
            "orientacja w przestrzeni lub dźwięk."
        ),
    },
    "1.3.4": {
        "name":       "Orientacja",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Treść nie ogranicza swojego widoku i działania do jednej orientacji wyświetlania, "
            "takiej jak pionowa lub pozioma, chyba że określona orientacja wyświetlania jest istotna."
        ),
    },
    "1.3.5": {
        "name":       "Określenie pożądanej wartości",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Cel każdego pola zbierającego informacje o użytkowniku może być programowo określony, "
            "gdy: Pole zbierające dane służy celowi określonemu w sekcji Przeznaczenie pól danych "
            "w komponentach interfejsu użytkownika; oraz Treść jest implementowana za pomocą "
            "technologii obsługującej określanie w polach formularza typu oczekiwanych danych."
        ),
    },

    # ── Wytyczna 1.4: Możliwość rozróżnienia ────────────────────────────────
    "1.4.1": {
        "name":       "Użycie koloru",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Kolor nie jest wykorzystywany jako jedyny wizualny sposób przekazywania informacji, "
            "wskazywania czynności do wykonania lub oczekiwania na odpowiedź, "
            "czy też wyróżniania elementów wizualnych."
        ),
    },
    "1.4.2": {
        "name":       "Kontrola odtwarzania dźwięku",
        "level":      "A",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Jeśli jakieś nagranie audio włącza się automatycznie na danej stronie i jest "
            "odtwarzane przez okres dłuższy niż 3 sekundy, istnieje mechanizm umożliwiający "
            "przerwanie lub wyłączenie nagrania albo mechanizm kontrolujący poziom głośności "
            "niezależnie od poziomu głośności całego systemu."
        ),
    },
    "1.4.3": {
        "name":       "Kontrast (minimum)",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Wizualna prezentacja tekstu lub obrazu tekstu posiada współczynnik kontrastu "
            "wynoszący przynajmniej 4,5:1, poza następującymi wyjątkami: "
            "Duży tekst — Duży tekst oraz grafiki takiego tekstu posiadają kontrast przynajmniej 3:1; "
            "Incydentalne — Tekst lub obrazy tekstu, które są częścią nieaktywnego komponentu "
            "interfejsu użytkownika, które są czystą dekoracją, które nie są widoczne lub które "
            "są częścią obrazu zawierającego inne istotne treści wizualne, nie wymagają "
            "minimalnego kontrastu; "
            "Logotyp — Tekst, który jest częścią logo lub nazwy własnej produktu (marki), "
            "nie wymaga minimalnego kontrastu."
        ),
    },
    "1.4.4": {
        "name":       "Zmiana rozmiaru tekstu",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Oprócz napisów rozszerzonych oraz obrazów tekstu, rozmiar tekstu może zostać "
            "powiększony do 200% bez użycia technologii wspomagających oraz bez utraty "
            "treści lub funkcjonalności."
        ),
    },
    "1.4.5": {
        "name":       "Obrazy tekstu",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Jeśli wykorzystywane technologie mogą przedstawiać treść wizualnie, do przekazywania "
            "informacji wykorzystuje się tekst, a nie obraz tekstu, z wyjątkiem następujących "
            "sytuacji: "
            "Możliwy do dostosowania — Obraz tekstu może być dostosowany wizualnie do wymagań "
            "użytkownika; "
            "Istotny — Prezentacja tekstu w postaci graficznej jest istotna dla zrozumienia "
            "przekazywanej informacji."
        ),
    },
    "1.4.10": {
        "name":       "Dopasowanie do ekranu",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Treść może być prezentowana bez utraty informacji lub funkcjonalności, bez "
            "konieczności przewijania w dwóch wymiarach dla: "
            "Pionowego przewijania treści o szerokości odpowiadającej 320 pikselom CSS; "
            "Poziomego przewijania treści na wysokości odpowiadającej 256 pikselom CSS. "
            "Wyjątkiem są te części treści, które wymagają dwuwymiarowego układu ze względu "
            "na sposób używania lub znaczenie."
        ),
    },
    "1.4.11": {
        "name":       "Kontrast elementów nietekstowych",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Wizualna prezentacja następujących elementów ma współczynnik kontrastu co najmniej "
            "3:1 względem sąsiednich kolorów: "
            "Komponenty interfejsu użytkownika — Informacje wizualne wymagane do identyfikacji "
            "komponentów interfejsu użytkownika i ich stanów, z wyjątkiem nieaktywnych składników "
            "lub gdy wygląd komponentu jest określony przez agenta użytkownika i nie jest "
            "modyfikowany przez autora; "
            "Obiekty graficzne — Części grafiki wymagane do zrozumienia treści, z wyjątkiem "
            "sytuacji, gdy konkretna prezentacja grafiki ma istotne znaczenie dla "
            "przekazywanych informacji."
        ),
    },
    "1.4.12": {
        "name":       "Odstępy w tekście",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "W treściach tworzonych za pomocą języków znaczników, umożliwiających ustawienie "
            "poniższych właściwości stylu, nie następuje utrata żadnych treści lub "
            "funkcjonalności, gdy tekst ustawiony zostanie tak, aby uwzględniał wszystkie "
            "poniższe parametry oraz gdy wprowadzone zostaną zmiany w jakiejkolwiek innej "
            "właściwości stylu: "
            "Wysokość linii (odstęp między wierszami) do co najmniej 1,5-krotności rozmiaru czcionki; "
            "Odstęp między akapitami co najmniej 2 razy większy od rozmiaru czcionki; "
            "Odstępy między literami (tracking) do co najmniej 0,12-krotności rozmiaru czcionki; "
            "Odstępy między wyrazami do co najmniej 0,16 wielkości czcionki. "
            "Wyjątek: Języki naturalne i skrypty, które nie wykorzystują jednej lub więcej "
            "z tych właściwości stylu tekstowego w tekście pisanym, mogą być zgodne przy użyciu "
            "tylko tych właściwości, które istnieją dla tej kombinacji języka i skryptu."
        ),
    },
    "1.4.13": {
        "name":       "Treść spod kursora lub fokusu",
        "level":      "AA",
        "pillar":     "Postrzegalność",
        "pillar_num": 1,
        "description": (
            "Gdy jakaś treść staje się widoczna po otrzymaniu kursora lub fokusu klawiatury, "
            "a po ich usunięciu znika, spełnione są poniższe warunki: "
            "Odrzucone — Istnieje mechanizm umożliwiający odrzucenie dodatkowej treści bez "
            "przesuwania wskaźnika myszy lub fokusu klawiatury, chyba że dodatkowa treść "
            "przekazuje błąd wprowadzanych danych lub nie przesłania ani nie zastępuje innej treści; "
            "Wskazywane — Jeśli wskaźnik myszy (hover) może wyzwolić dodatkową treść, wówczas "
            "wskaźnik może zostać przeniesiony na dodatkową treść bez znikania dodatkowej treści; "
            "Trwałe — Dodatkowa treść pozostaje widoczna do momentu usunięcia wyzwalacza "
            "aktywacji lub fokusu, użytkownik odrzuca go lub jego informacje nie są już ważne. "
            "Wyjątek: Wizualna prezentacja dodatkowej treści jest kontrolowana przez program "
            "użytkownika i nie jest modyfikowana przez autora."
        ),
    },

    # ════════════════════════════════════════════════════════════════════════
    # FILAR 2 — FUNKCJONALNOŚĆ
    # ════════════════════════════════════════════════════════════════════════

    # ── Wytyczna 2.1: Dostępność z klawiatury ───────────────────────────────
    "2.1.1": {
        "name":       "Klawiatura",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Wszystkie funkcjonalności w treści są obsługiwane za pomocą interfejsu klawiatury, "
            "bez wymogu określonego czasu użycia poszczególnych klawiszy, z wyjątkiem sytuacji, "
            "kiedy dana funkcja wymaga wprowadzenia informacji przez użytkownika w oparciu "
            "o ścieżkę ruchów, a nie w oparciu o punkty końcowe wejścia."
        ),
    },
    "2.1.2": {
        "name":       "Bez pułapki na klawiaturę",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Jeśli fokus klawiatury można przemieścić do danego komponentu treści za pomocą "
            "interfejsu klawiatury, to może on być z niego usunięty również za pomocą interfejsu "
            "klawiatury, a jeśli wymagane jest użycie czegoś więcej niż tylko strzałek, "
            "tabulatora lub innych standardowych metod wyjścia, użytkownik musi otrzymać "
            "odpowiednią podpowiedź, w jaki sposób usunąć fokus z danego komponentu."
        ),
    },
    "2.1.4": {
        "name":       "Jednoznakowe skróty klawiaturowe",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Jeśli skrót klawiaturowy jest zaimplementowany w treści tylko przy użyciu jednego "
            "znaku (litery, w tym wielkiej i małej, cyfry lub symbolu), to przynajmniej jedno "
            "z poniższych jest prawdziwe: "
            "Wyłączanie — Istnieje mechanizm wyłączania skrótu; "
            "Mapowanie — Istnieje mechanizm zmiany mapowania skrótu w celu użycia jednego lub "
            "więcej niedrukowalnych znaków klawiatury (np. Ctrl, Alt, itp.); "
            "Aktywny tylko po otrzymaniu fokusu — Skrót klawiaturowy dla komponentu interfejsu "
            "użytkownika jest aktywny tylko wtedy, gdy ten komponent ma fokus."
        ),
    },

    # ── Wytyczna 2.2: Wystarczająca ilość czasu ─────────────────────────────
    "2.2.1": {
        "name":       "Dostosowanie czasu",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Gdy czas korzystania z treści jest ograniczany, spełniony jest przynajmniej jeden "
            "z poniższych warunków: "
            "Wyłączenie — Użytkownik może wyłączyć limit czasowy, zanim czas upłynie; "
            "Dostosowanie — Użytkownik może swobodnie dostosować limit czasowy (przynajmniej "
            "o wartość 10 razy większą od wartości domyślnej), zanim czas upłynie; "
            "Wydłużenie — Użytkownik jest ostrzegany przed upłynięciem limitu czasowego i ma "
            "przynajmniej 20 sekund na wydłużenie limitu za pomocą prostej czynności (np. "
            "„wciśnij klawisz spacji”) oraz może wydłużyć limit przynajmniej dziesięciokrotnie; "
            "Wyjątek dotyczący czasu rzeczywistego — Limit czasowy jest wymaganym komponentem "
            "jakiejś czynności w czasie rzeczywistym (np. aukcji) i nie ma możliwości zmiany limitu; "
            "Wyjątek dotyczący istoty czynności — Limit czasowy jest istotny i wydłużenie go "
            "anulowałoby lub zaburzałoby daną czynność; "
            "Wyjątek 20 godzin — Limit czasowy przekracza 20 godzin."
        ),
    },
    "2.2.2": {
        "name":       "Pauza, zatrzymanie, ukrycie",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Gdy treść się porusza, migocze, przesuwa lub jest automatycznie aktualizowana, "
            "spełnione są wszystkie poniższe warunki: "
            "Poruszanie się, przesuwanie, migotanie — Każdą informację, która porusza się, "
            "przesuwa lub miga, a takie działanie (1) włącza się automatycznie, (2) jest widoczne "
            "dłużej niż 5 sekund, (3) jest przedstawiane równolegle z inną treścią — użytkownik "
            "może wstrzymać, zatrzymać lub ukryć za pomocą dostępnego mechanizmu, chyba że "
            "poruszanie się, przesuwanie lub migotanie jest częścią czynności, w której takie "
            "działanie jest istotne; "
            "Automatyczna aktualizacja — Każdą automatycznie aktualizującą się informację, która "
            "(1) włącza się automatycznie oraz (2) jest przedstawiana równolegle z inną treścią — "
            "użytkownik może wstrzymać, zatrzymać lub kontrolować częstotliwość aktualizacji za "
            "pomocą dostępnego mechanizmu, chyba że automatyczna aktualizacja jest częścią takiej "
            "czynności, w której takie działanie jest niezbędne."
        ),
    },

    # ── Wytyczna 2.3: Napady padaczkowe i odczucia fizyczne ─────────────────
    "2.3.1": {
        "name":       "Trzy błyski lub wartości poniżej progu",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Strony internetowe nie zawierają w swojej treści niczego, co błyska częściej niż "
            "trzy razy w ciągu jednej sekundy, lub też błysk nie przekracza wartości granicznych "
            "dla błysków ogólnych i czerwonych."
        ),
    },

    # ── Wytyczna 2.4: Możliwość nawigacji ───────────────────────────────────
    "2.4.1": {
        "name":       "Możliwość pominięcia bloków",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Istnieje mechanizm, który umożliwia pominięcie bloków treści powtarzanych "
            "na wielu stronach internetowych."
        ),
    },
    "2.4.2": {
        "name":       "Tytuł strony",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Strony internetowe mają tytuły, które opisują ich cel lub przedstawiają ich temat."
        ),
    },
    "2.4.3": {
        "name":       "Kolejność fokusu",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Jeśli strona internetowa może być nawigowana sekwencyjnie, a kolejność nawigacji "
            "wpływa na zrozumienie lub funkcjonalność strony, komponenty przyjmują fokus "
            "w kolejności, dzięki której zachowany jest sens i funkcjonalność treści."
        ),
    },
    "2.4.4": {
        "name":       "Cel łącza (w kontekście)",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Cel każdego łącza może wynikać z samej treści łącza lub z treści tekstu powiązanego "
            "z kontekstem łącza określonym programowo, poza tymi przypadkami, kiedy cel łącza "
            "i tak byłby niejasny dla użytkowników."
        ),
    },
    "2.4.5": {
        "name":       "Wiele dróg",
        "level":      "AA",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Istnieje więcej niż jeden sposób umożliwiający zlokalizowanie strony internetowej "
            "w zestawie stron internetowych, z wyjątkiem sytuacji, kiedy dana strona jest "
            "wynikiem jakiejś procedury lub jednym z jej etapów."
        ),
    },
    "2.4.6": {
        "name":       "Nagłówki i etykiety",
        "level":      "AA",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Nagłówki i etykiety opisują temat lub cel treści."
        ),
    },
    "2.4.7": {
        "name":       "Widoczny fokus",
        "level":      "AA",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Każdy interfejs posiadający możliwość obsługi przy pomocy klawiatury ma tryb obsługi, "
            "w którym fokus klawiatury jest stale widoczny."
        ),
    },

    # ── Wytyczna 2.5: Sposoby wprowadzania danych ───────────────────────────
    "2.5.1": {
        "name":       "Gesty dotykowe",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Wszystkie funkcjonalności wykorzystujące do obsługi gesty wielopunktowe lub oparte "
            "na ścieżkach mogą być obsługiwane za pomocą dotyku jednopunktowego bez gestu "
            "opartego na ścieżce, chyba że istotny jest gest wielopunktowy lub oparty na ścieżce."
        ),
    },
    "2.5.2": {
        "name":       "Rezygnacja ze wskazania",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "W przypadku funkcjonalności, które są wywoływane za pomocą dotyku jednopunktowego, "
            "co najmniej jedno z poniższych twierdzeń jest prawdziwe: "
            "Brak zdarzenia — Naciskanie nie wywołuje jakiejkolwiek części zdarzenia; "
            "Przerwanie lub cofnięcie — Zdarzenie jest zależne od zwolnienia nacisku i istnieje "
            "mechanizm, którym można je przerwać lub cofnąć po zwolnieniu nacisku; "
            "Odwrócenie zdarzenia — Zwolnienie nacisku cofa wywołane zdarzenie i przywraca stan "
            "sprzed zdarzenia; "
            "Istotne — Wciśnięcie jest niezbędne do wywołania zdarzenia."
        ),
    },
    "2.5.3": {
        "name":       "Etykieta w nazwie",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "W przypadku komponentów interfejsu użytkownika z etykietami zawierającymi tekst "
            "lub obrazy tekstu, nazwa zawiera tekst, który jest prezentowany wizualnie."
        ),
    },
    "2.5.4": {
        "name":       "Aktywowanie ruchem",
        "level":      "A",
        "pillar":     "Funkcjonalność",
        "pillar_num": 2,
        "description": (
            "Funkcjonalność, którą można obsługiwać za pomocą ruchu urządzenia lub ruchu "
            "użytkownika, można również obsługiwać za pomocą komponentów interfejsu użytkownika, "
            "a reagowanie na ruch można wyłączyć, aby zapobiec przypadkowemu uruchomieniu, "
            "z wyjątkiem sytuacji, gdy: "
            "Obsługiwany interfejs — Ruch służy do obsługi funkcjonalności poprzez interfejs "
            "obsługiwany przez dostępność; "
            "Istotny — Ruch jest niezbędny dla funkcji, a to spowodowałoby unieważnienie działania."
        ),
    },

    # ════════════════════════════════════════════════════════════════════════
    # FILAR 3 — ZROZUMIAŁOŚĆ
    # ════════════════════════════════════════════════════════════════════════

    # ── Wytyczna 3.1: Czytelność ─────────────────────────────────────────────
    "3.1.1": {
        "name":       "Język strony",
        "level":      "A",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Domyślny język naturalny każdej strony internetowej może zostać odczytany "
            "przez program komputerowy."
        ),
    },
    "3.1.2": {
        "name":       "Język części",
        "level":      "AA",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Język naturalny każdej części lub frazy zawartej w treści może zostać odczytany "
            "przez program komputerowy, z wyjątkiem nazw własnych, wyrażeń technicznych, słów "
            "w nieokreślonym języku oraz słów i fraz, które stanowią część żargonu "
            "w bezpośrednio otaczającym je tekście."
        ),
    },

    # ── Wytyczna 3.2: Przewidywalność ───────────────────────────────────────
    "3.2.1": {
        "name":       "Po otrzymaniu fokusu",
        "level":      "A",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Przyjęcie fokusu przez dowolny komponent interfejsu użytkownika nie powoduje "
            "nieoczekiwanej zmiany kontekstu."
        ),
    },
    "3.2.2": {
        "name":       "Podczas wprowadzania danych",
        "level":      "A",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Zmiana ustawień jakiegokolwiek komponentu interfejsu użytkownika nie powoduje "
            "automatycznej zmiany kontekstu, chyba że użytkownik został poinformowany "
            "o takim działaniu, zanim zaczął korzystać z komponentu."
        ),
    },
    "3.2.3": {
        "name":       "Spójna nawigacja",
        "level":      "AA",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Mechanizmy nawigacji, które powtarzają się na wielu stronach internetowych w ramach "
            "jednego zestawu stron internetowych, występują w tej samej względnej kolejności "
            "za każdym razem, gdy są powtarzane, chyba że zmiana jest inicjowana przez użytkownika."
        ),
    },
    "3.2.4": {
        "name":       "Spójna identyfikacja",
        "level":      "AA",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Komponenty, które mają tę samą funkcjonalność w ramach jednego zestawu stron "
            "internetowych, są w taki sam sposób zidentyfikowane."
        ),
    },

    # ── Wytyczna 3.3: Pomoc przy wprowadzaniu danych ────────────────────────
    "3.3.1": {
        "name":       "Identyfikacja błędu",
        "level":      "A",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Jeśli automatycznie zostanie wykryty błąd wprowadzania danych, system wskazuje "
            "błędny element, a użytkownik otrzymuje opis błędu w postaci tekstu."
        ),
    },
    "3.3.2": {
        "name":       "Etykiety lub instrukcje",
        "level":      "A",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Gdy w treści wymagane jest wprowadzenie danych przez użytkownika, "
            "zapewnione są etykiety lub instrukcje."
        ),
    },
    "3.3.3": {
        "name":       "Sugestie korekty błędów",
        "level":      "AA",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "Jeśli automatycznie zostanie wykryty błąd wprowadzania danych i znane są sugestie "
            "korekty, wtedy użytkownik otrzymuje takie sugestie, chyba że zagrażałoby to "
            "bezpieczeństwu treści lub zmieniło jej cel."
        ),
    },
    "3.3.4": {
        "name":       "Zapobieganie błędom (prawnym, finansowym, w danych)",
        "level":      "AA",
        "pillar":     "Zrozumiałość",
        "pillar_num": 3,
        "description": (
            "W przypadku stron internetowych, które powodują zobowiązania prawne, albo na których "
            "użytkownik przeprowadza transakcje finansowe, modyfikuje lub usuwa dane w systemach "
            "przechowywania danych, nad którymi ma kontrolę, albo udziela odpowiedzi na testy, "
            "co najmniej jedna z poniższych informacji jest prawdziwa: "
            "Odwracalność — Wprowadzenie danych jest odwracalne; "
            "Sprawdzanie — Dane wprowadzone przez użytkownika są sprawdzane pod kątem błędów, "
            "a użytkownik ma możliwość wprowadzenia poprawek; "
            "Potwierdzenie — Istnieje mechanizm sprawdzania, potwierdzania oraz korekty informacji "
            "przed jej ostatecznym wysłaniem."
        ),
    },

    # ════════════════════════════════════════════════════════════════════════
    # FILAR 4 — SOLIDNOŚĆ
    # ════════════════════════════════════════════════════════════════════════

    # ── Wytyczna 4.1: Kompatybilność ────────────────────────────────────────
    "4.1.1": {
        "name":       "Poprawność kodu",
        "level":      "A",
        "pillar":     "Solidność",
        "pillar_num": 4,
        "description": (
            "W treści wprowadzonej przy użyciu języka znaczników, elementy posiadają kompletne "
            "znaczniki początkowe i końcowe, elementy są zagnieżdżane według swoich specyfikacji, "
            "nie posiadają zduplikowanych atrybutów, a wszystkie ID są unikalne, z wyjątkiem "
            "przypadków, kiedy specyfikacja zezwala na wyżej wymienione cechy."
        ),
    },
    "4.1.2": {
        "name":       "Nazwa, rola, wartość",
        "level":      "A",
        "pillar":     "Solidność",
        "pillar_num": 4,
        "description": (
            "Dla wszystkich komponentów interfejsu użytkownika (w tym, ale nie tylko, elementów "
            "formularzy, łączy oraz komponentów wygenerowanych przez skrypty) nazwa oraz rola "
            "mogą być określone programowo; stan, właściwości oraz wartości, które mogą być "
            "ustawione przez użytkownika, mogą również być ustawione programowo; powiadomienie "
            "o zmianach w tych elementach dostępne jest dla programów użytkownika, "
            "w tym technologii wspomagających."
        ),
    },
    "4.1.3": {
        "name":       "Komunikaty o stanie",
        "level":      "AA",
        "pillar":     "Solidność",
        "pillar_num": 4,
        "description": (
            "W treści wprowadzonej przy użyciu języka znaczników komunikaty o stanie mogą być "
            "programowo określane poprzez role lub właściwości, dzięki czemu mogą być "
            "prezentowane użytkownikowi za pomocą technologii wspomagających "
            "bez uzyskiwania fokusu."
        ),
    },
}


# ---------------------------------------------------------------------------
# Funkcje pomocnicze
# ---------------------------------------------------------------------------

def get_criterion(criterion_id: str) -> WcagCriterion:
    """
    Zwraca słownik kryterium na podstawie jego numeru.

    Raises:
        KeyError: jeśli podany numer kryterium nie istnieje w słowniku.

    Przykład:
        >>> c = get_criterion("1.4.3")
        >>> c["name"]
        'Kontrast (minimum)'
    """
    if criterion_id not in WCAG_CRITERIA:
        raise KeyError(
            f"Nieznane kryterium WCAG: '{criterion_id}'. "
            f"Dostępne: {sorted(WCAG_CRITERIA.keys())}"
        )
    return WCAG_CRITERIA[criterion_id]


def get_pillar_name(criterion_id: str) -> str:
    """Zwraca nazwę filara dla danego kryterium."""
    return get_criterion(criterion_id)["pillar"]


def get_criteria_by_level(level: Level) -> dict[str, WcagCriterion]:
    """Zwraca wszystkie kryteria danego poziomu (A lub AA)."""
    return {k: v for k, v in WCAG_CRITERIA.items() if v["level"] == level}


def get_criteria_by_pillar(pillar_num: int) -> dict[str, WcagCriterion]:
    """Zwraca wszystkie kryteria danego filara (1–4)."""
    return {k: v for k, v in WCAG_CRITERIA.items() if v["pillar_num"] == pillar_num}


# ---------------------------------------------------------------------------
# Stałe pomocnicze
# ---------------------------------------------------------------------------

#: Mapowanie numeru filara na jego polską nazwę
PILLAR_NAMES: dict[int, str] = {
    1: "Postrzegalność",
    2: "Funkcjonalność",
    3: "Zrozumiałość",
    4: "Solidność",
}

#: Mapowanie pierwszej cyfry numeru kryterium na filar (dla szybkiego lookup)
CRITERION_PREFIX_TO_PILLAR: dict[str, str] = {
    "1": "Postrzegalność",
    "2": "Funkcjonalność",
    "3": "Zrozumiałość",
    "4": "Solidność",
}
