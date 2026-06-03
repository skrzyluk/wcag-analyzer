# WCAG 2.1 AA Analyzer

**Aplikacja lokalna do analizy plików MHTML pod względem zgodności z normą dostępności WCAG 2.1 na poziomie AA** 🎯

---

## 📋 Spis Treści

1. [Przegląd](#przegląd)
2. [Wymagania](#wymagania)
3. [Instalacja](#instalacja)
4. [Uruchomienie](#uruchomienie)
5. [Użytkowanie](#użytkowanie)
6. [Architektura](#architektura)
7. [Zasoby](#zasoby)

---

## 🎯 Przegląd

### Czym jest ta aplikacja?

WCAG 2.1 AA Analyzer to narzędzie do automatycznej analizy dostępności cyfrowej stron internetowych (MHTML). Pozwala szybko zidentyfikować problemy dostępu i otrzymać konkretne rekomendacje napraw.

### Główne cechy

✅ **Upload plików MHTML** — Przesyłanie stron do analizy  
✅ **Automatyczna analiza** — Sprawdzenie ~50 kryteriów WCAG 2.1 AA  
✅ **Szczegółowe raporty** — Informacje o każdym znalezionym błędzie  
✅ **Export** — HTML, PDF, JSON  
✅ **Historia analiz** — Przeglądanie poprzednich wyników  
✅ **Porównanie** — Analiza postępu między wersjami  
✅ **Interfejs webowy** — Dostęp przez przeglądarkę (localhost)  
✅ **Offline** — Działa bez internetu

### Kto to potrzebuje?

- 👨‍💻 **Webdeveloperowie** — Automatyczne sprawdzanie dostępności
- 🎨 **UX/UI Designerzy** — Weryfikacja dostępności designu
- 📊 **QA Engineers** — Testing dostępności
- 👤 **Właściciele produktów** — Compliance z WCAG
- 🏢 **Zespoły prawne** — Dokumentacja dostępności

---

## 📦 Wymagania

### Systemowe

- **Windows 10+** (Cross-platform compatible: macOS, Linux)
- **Python 3.10+** — Backend
- **Node.js 18+** — Frontend
- **8 GB RAM** (minimum), **16 GB** (zalecane)
- **1 GB wolnego miejsca** (na pliki i raporty)

### Sieciowe

- **Port 8000** — Backend API (FastAPI)
- **Port 5173** — Frontend (Vite development server)
- Brak wymogów dostępu do internetu

### Przeglądarki

✅ Chrome 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Edge 90+

---

## 🛠️ Instalacja

### 1. Klonowanie Repozytorium

```bash
git clone https://github.com/yourusername/wcag-analyzer.git
cd wcag-analyzer
```

### 2. Backend Setup (Python)

```bash
# Przejdź do folderu backend
cd backend

# Utwórz virtual environment
python -m venv venv

# Aktywuj venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt

# Sprawdź instalację
python -m pytest
```

### 3. Frontend Setup (Node.js)

```bash
# Przejdź do folderu frontend
cd frontend

# Zainstaluj dependencies
npm install

# Sprawdź Build
npm run build
```

### 4. Konfiguracja Zmiennych Środowiska

**Backend (.env)**

```env
# backend/.env
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
DEBUG=true
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
MAX_FILE_SIZE=50MB
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

**Frontend (.env)**

```env
# frontend/.env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=WCAG Analyzer
```

---

## 🚀 Uruchomienie

### Development Mode

**Terminal 1 — Backend**

```bash
cd backend
source venv/bin/activate  # lub: venv\Scripts\activate na Windows
python run_backend.py

# Backend dostępny na: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev

# Frontend dostępny na: http://localhost:5173
```

Otwórz w przeglądarce: **http://localhost:5173** 🎉

### Production Build

```bash
# Frontend build
cd frontend
npm run build
# Wynik w: frontend/dist/

# Backend run
cd backend
python run_backend.py --prod
```

---

## 📖 Użytkowanie

### Krok 1: Upload Pliku

1. Przejdź na stronę główną
2. Kliknij na "Upload MHTML File" lub przeciągnij plik
3. Wybierz plik `.mhtml` lub `.mht`
4. Kliknij "Upload & Analyze"

### Krok 2: Czekaj na Wyniki

- Aplikacja automatycznie przeanalizuje plik
- Postęp będzie widoczny na ekranie
- Analiza zajmuje zwykle 10-30 sekund

### Krok 3: Przeglądaj Raport

**Summary Tab** — Ogólna statystyka
- % Compliance
- Liczba błędów (krytyczne, ważne, drobne)
- Status WCAG (A, AA, AAA)

**Details Tab** — Każdy błąd z kontekstem
- WCAG Criterion (np. 1.4.3)
- Opis problemu
- Rekomendacja naprawy
- HTML snippet z błędem

**Statistics Tab** — Analiza głęboká
- Błędy wg kryteriów
- Błędy wg typów (kontrast, alt text, etc.)

### Krok 4: Export & Udostępnianie

Kliknij "Export" i wybierz format:
- **HTML** — Full report z stylami
- **PDF** — Drukowane raporty
- **JSON** — Dane dla integracji

---

## 🏗️ Architektura

### Struktura Plików

```
wcag-analyzer/
├── backend/                    # FastAPI + Python
│   ├── app/
│   │   ├── main.py            # Entry point
│   │   ├── api/               # REST endpoints
│   │   ├── core/              # WCAG logic
│   │   └── services/          # Business logic
│   ├── requirements.txt
│   └── run_backend.py
│
├── frontend/                   # Vue.js 3 + Vite
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── views/             # Pages
│   │   ├── services/          # API calls
│   │   └── stores/            # State (Pinia)
│   ├── package.json
│   └── vite.config.js
│
├── docs/                       # Dokumentacja
│   ├── API.md                 # REST API spec
│   ├── WCAG_RULES.md          # WCAG 2.1 AA details
│   └── USER_GUIDE.md          # Instrukcja użytkownika
│
└── README.md                   # Ten plik
```

### Flow Danych

```
┌─────────────────────────────────────────────────┐
│       User Interface (Vue.js)                   │
│  - FileUploader                                 │
│  - ReportViewer                                 │
│  - ExportButton                                 │
└──────────────────┬──────────────────────────────┘
                   │
                   │ HTTP/REST
                   │
┌──────────────────▼──────────────────────────────┐
│      Backend API (FastAPI)                      │
│  - POST /api/upload                             │
│  - POST /api/analyze/{file_id}                  │
│  - GET /api/report/{analysis_id}                │
│  - GET /api/export/{id}/{format}                │
└──────────────────┬──────────────────────────────┘
                   │
                   │ Processing
                   │
┌──────────────────▼──────────────────────────────┐
│   Core Logic (Python)                           │
│  - MHTMLParser                                  │
│  - WCAGValidator                                │
│  - ReportGenerator                              │
└──────────────────┬──────────────────────────────┘
                   │
                   │ File I/O
                   │
┌──────────────────▼──────────────────────────────┐
│       Local Storage                             │
│  - uploads/                                     │
│  - reports/                                     │
│  - temp/                                        │
└─────────────────────────────────────────────────┘
```

---

## 📚 Zasoby

### Dokumentacja

📖 [ARCHITEKTURA_WCAG_ANALYZER.md](./ARCHITEKTURA_WCAG_ANALYZER.md) — Pełny technical design  
🎨 [DESIGN_FRONTEND.md](./DESIGN_FRONTEND.md) — Frontend best practices  
🔌 [API.md](./docs/API.md) — REST API specification  
📋 [WCAG_RULES.md](./docs/WCAG_RULES.md) — Szczegółowe kryteria WCAG 2.1 AA  
👤 [USER_GUIDE.md](./docs/USER_GUIDE.md) — Instrukcja użytkownika

### Externe Zasoby

🌐 [W3C WCAG 2.1 (English)](https://www.w3.org/WAI/WCAG21/quickref/)  
🌐 [W3C WCAG 2.1 (Polski)](https://www.w3.org/Translations/WCAG21-pl-20210413/)  
📖 [Vue.js 3 Documentation](https://vuejs.org/)  
⚡ [FastAPI Documentation](https://fastapi.tiangolo.com/)  
🎯 [WebAIM Resources](https://webaim.org/)

### Narzędzia

🧪 **Testing Accessibility**
- [WAVE Browser Extension](https://wave.webaim.org/)
- [Axe DevTools](https://www.deque.com/axe/devtools/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

🎨 **Color Contrast**
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Contrast Ratio Tool](https://contrast-ratio.com/)

---

## 🤝 Contributing

Znalazłeś bug lub masz pomysł na feature?

1. Utwórz Issue na GitHubie
2. Forkuj projekt
3. Utwórz branch (`git checkout -b feature/amazing-feature`)
4. Commituj zmiany (`git commit -m 'Add amazing feature'`)
5. Push do branch'a (`git push origin feature/amazing-feature`)
6. Otwórz Pull Request

---

## 📄 Licencja

Projekt licencjonowany na [MIT License](./LICENSE)

---

## 📞 Support

Pytania? Problemy?

- 📧 Email: skrzyluk@gmail.com
- 🐛 Issue Tracker: GitHub Issues
- 💬 Dokumentacja: [docs/](./docs/)

---

## 🎯 Roadmap

### v1.0 (Current)
- ✅ Podstawowa analiza WCAG 2.1 AA
- ✅ Export do HTML/PDF/JSON
- ✅ Historia analiz
- ✅ Interfejs webowy

### v1.1 (Q2 2026)
- 🔲 Porównanie wersji
- 🔲 Batch analysis
- 🔲 Integracja z CI/CD
- 🔲 Dashboard z metrykamietrics

### v2.0 (Q3 2026)
- 🔲 Automatyczne crawling
- 🔲 Web scraper dla HTML stron
- 🔲 Team collaboration
- 🔲 Cloud storage (AWS S3)

---

## 📊 Statystyki Projektu

| Metryka | Wartość |
|---------|---------|
| Kryteria WCAG 2.1 AA | ~50 |
| Komponenty Frontend | 15+ |
| API Endpoints | 8+ |
| Linie kodu (Backend) | ~3000 |
| Linie kodu (Frontend) | ~2000 |
| Test Coverage | 80%+ |

---

## ✨ Credits

Stworzony z ❤️ przez zespół dostępności cyfrowej.

**Wersja:** 1.0.0  
**Status:** Stabilna  
**Ostatnia aktualizacja:** 2026-05-14

---

**Gotowy do uruchomienia?** 🚀 [Przejdź do Instalacji](#-instalacja)
