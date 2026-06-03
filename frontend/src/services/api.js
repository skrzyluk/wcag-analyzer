/**
 * api.js — HTTP Client & Service Layer
 * Projekt: WCAG 2.1 AA Analyzer
 *
 * Architektura dwuwarstwowa:
 *   1. apiClient  — niskopoziomowy klient HTTP (fetch wrapper)
 *   2. *Service   — wysokopoziomowe metody domenowe
 *
 * Konwencje:
 *   - Wszystkie metody async, zwracają dane lub rzucają ApiError
 *   - FormData dla file upload, JSON dla reszty
 *   - Timeout 30s dla normalnych requestów, 120s dla analizy
 */

// ── Stałe ─────────────────────────────────────────────────────────────────

const DEFAULT_TIMEOUT_MS  = 30_000   // 30 sekund
const ANALYSIS_TIMEOUT_MS = 120_000  // 2 minuty (analiza WCAG może trwać)
const MAX_RETRIES         = 2        // Liczba ponowień przy błędach sieciowych

// ── Klasa błędu API ────────────────────────────────────────────────────────

/**
 * ApiError — rozszerzony Error z informacjami HTTP.
 * Pozwala odróżnić błąd sieciowy od błędu serwera w store'ach.
 */
export class ApiError extends Error {
  /**
   * @param {string}  message    - Komunikat dla użytkownika (po polsku)
   * @param {number}  statusCode - HTTP status (0 = błąd sieci/timeout)
   * @param {string}  endpoint   - Endpoint który zawiódł
   * @param {any}     detail     - Surowe dane z serwera (do logów)
   */
  constructor(message, statusCode = 0, endpoint = '', detail = null) {
    super(message)
    this.name       = 'ApiError'
    this.statusCode = statusCode
    this.endpoint   = endpoint
    this.detail     = detail
    this.isApiError = true
  }

  /** Czy błąd jest tymczasowy (warto spróbować ponownie) */
  get isRetryable() {
    return this.statusCode === 0       // błąd sieci / timeout
        || this.statusCode === 429     // too many requests
        || this.statusCode >= 500      // błąd serwera
  }

  /** Krótki opis dla logów */
  get summary() {
    return `[ApiError ${this.statusCode}] ${this.endpoint}: ${this.message}`
  }
}

// ── Mapowanie statusów HTTP → komunikaty PL ───────────────────────────────

const HTTP_ERROR_MESSAGES = {
  400: 'Nieprawidłowe żądanie. Sprawdź przesyłane dane.',
  401: 'Brak autoryzacji. Zaloguj się ponownie.',
  403: 'Brak uprawnień do wykonania tej operacji.',
  404: 'Nie znaleziono zasobu. Sprawdź czy URL jest poprawny.',
  408: 'Serwer nie odpowiedział w wyznaczonym czasie (timeout).',
  409: 'Konflikt — zasób już istnieje.',
  413: 'Plik jest za duży. Maksymalny rozmiar to 50 MB.',
  415: 'Nieobsługiwany format pliku.',
  422: 'Dane nie przeszły walidacji po stronie serwera.',
  429: 'Zbyt wiele żądań. Poczekaj chwilę i spróbuj ponownie.',
  500: 'Błąd wewnętrzny serwera. Spróbuj ponownie za chwilę.',
  502: 'Serwer jest niedostępny (bad gateway).',
  503: 'Serwer tymczasowo niedostępny. Spróbuj ponownie za chwilę.',
  504: 'Serwer nie odpowiedział (gateway timeout).',
}

/**
 * Normalizuje komunikat błędu z serwera do stringa.
 * FastAPI może zwrócić:
 *   - string   → używamy bezpośrednio
 *   - array    → Pydantic validation errors: [{loc, msg, type}]
 *   - object   → niestandardowy format { message, detail }
 */
const normalizeServerMessage = (raw) => {
  if (!raw) return null
  if (typeof raw === 'string') return raw
  if (Array.isArray(raw)) {
    // Pydantic: bierzemy pierwsze 'msg' lub serialzujemy skrótowo
    return raw.map(e => e.msg || e.message || JSON.stringify(e)).join(' | ')
  }
  if (typeof raw === 'object') {
    return raw.message || raw.detail || raw.msg || JSON.stringify(raw)
  }
  return String(raw)
}

const getErrorMessage = (status, serverMessage = null) => {
  const normalized = normalizeServerMessage(serverMessage)
  return normalized || HTTP_ERROR_MESSAGES[status] || `Błąd HTTP ${status}.`
}

// ── Pomocnicze — timeout via AbortController ───────────────────────────────

const fetchWithTimeout = (url, options, timeoutMs) => {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  return fetch(url, { ...options, signal: controller.signal })
    .finally(() => clearTimeout(timer))
}

// ── Pomocnicze — sleep dla retry ───────────────────────────────────────────

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const getFilenameFromDisposition = (disposition) => {
  if (!disposition) return null

  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1].replace(/['"]/g, ''))
    } catch {
      return utf8Match[1]
    }
  }

  const asciiMatch = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/i)
  return asciiMatch?.[1]?.replace(/['"]/g, '') || null
}

// ── apiClient ─────────────────────────────────────────────────────────────

export const apiClient = {
  /** Bazowy URL z .env; fallback na localhost */
  get baseURL() {
    return (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL)
      || 'http://localhost:8000'
  },

  /**
   * Główna metoda request — obsługuje retry, timeout, parsowanie błędów.
   *
   * @param {string} endpoint   - Ścieżka API (np. '/api/upload')
   * @param {object} options    - Opcje fetch
   * @param {number} timeoutMs  - Timeout w ms
   * @param {number} attempt    - Numer próby (wewnętrzny, dla retry)
   * @returns {Promise<any>}    - Dane JSON z serwera
   * @throws  {ApiError}
   */
  async request(endpoint, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS, attempt = 1) {
    const url = `${this.baseURL}${endpoint}`

    // Domyślne nagłówki — NIE ustawiamy Content-Type dla FormData
    // (przeglądarka sama dodaje boundary)
    const isFormData = options.body instanceof FormData
    const defaultHeaders = isFormData
      ? {}
      : { 'Content-Type': 'application/json', 'Accept': 'application/json' }

    const fetchOptions = {
      ...options,
      headers: { ...defaultHeaders, ...options.headers }
    }

    let response
    try {
      response = await fetchWithTimeout(url, fetchOptions, timeoutMs)
    } catch (err) {
      // Błąd sieci lub AbortError (timeout)
      const isTimeout = err.name === 'AbortError'
      const message = isTimeout
        ? `Przekroczono czas oczekiwania (${timeoutMs / 1000}s). Sprawdź połączenie z serwerem.`
        : 'Nie można połączyć się z serwerem. Sprawdź czy backend jest uruchomiony.'

      // Retry dla błędów sieciowych
      if (attempt <= MAX_RETRIES) {
        await sleep(attempt * 1000) // 1s, 2s
        return this.request(endpoint, options, timeoutMs, attempt + 1)
      }

      throw new ApiError(message, 0, endpoint, err.message)
    }

    // Spróbuj odczytać JSON z odpowiedzi (może nie istnieć przy 204)
    let data = null
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      try {
        data = await response.json()
      } catch {
        // Odpowiedź nie jest JSON — ignorujemy
      }
    }

    // Obsługa błędów HTTP
    if (!response.ok) {
      // Wyciągnij komunikat z serwera — detail może być stringiem, tablicą (Pydantic) lub obiektem
      const rawServerMessage = data?.detail ?? data?.message ?? data?.error ?? null
      const message = getErrorMessage(response.status, rawServerMessage)

      // Retry dla błędów serwera (5xx) i 429
      if ((response.status >= 500 || response.status === 429) && attempt <= MAX_RETRIES) {
        const delay = response.status === 429
          ? parseInt(response.headers.get('retry-after') || '5', 10) * 1000
          : attempt * 2000
        await sleep(delay)
        return this.request(endpoint, options, timeoutMs, attempt + 1)
      }

      throw new ApiError(message, response.status, endpoint, data)
    }

    return data
  },

  /** GET request */
  get(endpoint, options = {}) {
    return this.request(endpoint, { method: 'GET', ...options })
  },

  /** POST request z JSON body */
  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options
    })
  },

  /** POST request z FormData (file upload) */
  postForm(endpoint, formData, options = {}) {
    return this.request(
      endpoint,
      { method: 'POST', body: formData, ...options },
      ANALYSIS_TIMEOUT_MS  // upload + analiza = więcej czasu
    )
  },

  /** DELETE request */
  delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options })
  },

  /**
   * Pobierz plik binarny (blob) — dla eksportu PDF/HTML.
   * Zwraca { blob, filename } zamiast JSON.
   */
  async getBlob(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    let response
    try {
      response = await fetchWithTimeout(url, { method: 'GET', ...options }, DEFAULT_TIMEOUT_MS)
    } catch (err) {
      const isTimeout = err.name === 'AbortError'
      throw new ApiError(
        isTimeout
          ? 'Przekroczono czas pobierania pliku. Spróbuj ponownie.'
          : 'Nie można pobrać pliku. Sprawdź czy backend działa i odśwież stronę.',
        0, endpoint, err.message
      )
    }

    if (!response.ok) {
      let serverMessage = null
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        try {
          const data = await response.json()
          serverMessage = data?.detail ?? data?.message ?? data?.error ?? null
        } catch {
          serverMessage = null
        }
      }

      throw new ApiError(
        getErrorMessage(response.status, serverMessage),
        response.status, endpoint
      )
    }

    const blob = await response.blob()
    // Wyciągnij nazwę pliku z nagłówka Content-Disposition
    const disposition = response.headers.get('content-disposition') || ''
    const filename = getFilenameFromDisposition(disposition) || 'raport'

    return { blob, filename }
  }
}

// ── analysisService ────────────────────────────────────────────────────────

/**
 * analysisService — operacje domenowe dla analiz WCAG.
 *
 * Każda metoda mapuje się 1:1 na endpoint backendu FastAPI.
 * Dokumentacja endpointów: http://localhost:8000/docs (Swagger)
 */
export const analysisService = {

  /**
   * Wgraj plik MHTML na serwer.
   * @param   {File}    file - Obiekt File z input/drag&drop
   * @returns {Promise<{ file_id: string, filename: string, size: number }>}
   */
  uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.postForm('/api/upload', formData)
  },

  /**
   * Uruchom analizę WCAG dla wgranego pliku.
   * @param   {string}  fileId  - ID z uploadFile()
   * @param   {object}  options - Opcjonalne: { criteria: string[] }
   * @returns {Promise<{ analysis_id: string, status: string }>}
   */
  analyzeFile(fileId, options = {}) {
    // Używamy request() bezpośrednio, żeby przekazać ANALYSIS_TIMEOUT_MS
    return apiClient.request(
      `/api/analyze/${fileId}`,
      { method: 'POST', body: JSON.stringify(options), headers: { 'Content-Type': 'application/json' } },
      ANALYSIS_TIMEOUT_MS
    )
  },

  /**
   * Pobierz status trwającej analizy (polling).
   * @param   {string}  analysisId
   * @returns {Promise<{ status: string, progress: number, analysis_id: string }>}
   */
  getAnalysisStatus(analysisId) {
    return apiClient.get(`/api/status/${analysisId}`)
  },

  /**
   * Pobierz pełny raport po zakończeniu analizy.
   * @param   {string}  analysisId
   * @returns {Promise<AnalysisReport>}
   */
  getReport(analysisId) {
    return apiClient.get(`/api/report/${analysisId}`)
  },

  /**
   * Połącz wiele raportów backendu w jeden raport zbiorczy.
   * @param {string[]} analysisIds
   * @returns {Promise<AnalysisReport>}
   */
  combineReports(analysisIds) {
    return apiClient.post('/api/reports/combine', { analysis_ids: analysisIds })
  },

  /**
   * Lista wszystkich zapisanych raportów.
   * @param   {object}  params - { page, limit, sort }
   * @returns {Promise<{ reports: AnalysisReport[], total: number }>}
   */
  listReports(params = {}) {
    const query = new URLSearchParams(params).toString()
    return apiClient.get(`/api/reports/list${query ? '?' + query : ''}`)
  },

  /**
   * Eksportuj raport w wybranym formacie.
   * Pobiera plik binarny i inicjuje download w przeglądarce.
   * @param   {string}  analysisId
   * @param   {'pdf'|'html'|'json'}  format
   */
  async exportReport(analysisId, format) {
    const { blob, filename } = await apiClient.getBlob(
      `/api/export/${analysisId}/${format}`
    )
    // Wyzwól download bez otwierania nowej karty
    const url = URL.createObjectURL(blob)
    const a   = document.createElement('a')
    a.href     = url
    a.download = filename || `raport-wcag-${analysisId}.${format}`
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  /**
   * Usuń raport i powiązane dane.
   * @param   {string}  analysisId
   * @returns {Promise<{ deleted: boolean }>}
   */
  deleteReport(analysisId) {
    return apiClient.delete(`/api/report/${analysisId}`)
  },

  /**
   * Porównaj dwa raporty side-by-side.
   * @param   {string}  idA
   * @param   {string}  idB
   * @returns {Promise<ComparisonResult>}
   */
  compareReports(idA, idB) {
    return apiClient.post('/api/reports/compare', { analysis_id_a: idA, analysis_id_b: idB })
  },

  /**
   * Sprawdź dostępność backendu (health check).
   * @returns {Promise<{ status: 'ok' | 'degraded' | 'down' }>}
   */
  healthCheck() {
    return apiClient.get('/api/health')
  },

  /**
   * Pobierz listę analiz wczytanych automatycznie przy starcie ze wskazanego katalogu.
   * @returns {Promise<{ preloaded: object[], total: number }>}
   */
  getPreloaded() {
    return apiClient.get('/api/preloaded')
  }
}

// ── JSDoc typy pomocnicze ────────────────────────────────────────────────────

/**
 * @typedef {object} AnalysisReport
 * @property {string}   analysis_id
 * @property {string}   filename
 * @property {string}   analysis_date
 * @property {Summary}  summary
 * @property {Issue[]}  issues
 * @property {string}   status  - 'pending' | 'processing' | 'done' | 'error'
 */

/**
 * @typedef {object} Summary
 * @property {number} compliance_percentage
 * @property {number} total_checks
 * @property {number} passed_checks
 * @property {number} critical_errors
 * @property {number} major_errors
 * @property {number} minor_errors
 */

/**
 * @typedef {object} Issue
 * @property {string}   id
 * @property {string}   wcag_criterion   - np. "1.4.3"
 * @property {string}   wcag_level       - 'A' | 'AA'
 * @property {string}   title
 * @property {string}   description
 * @property {string}   recommendation
 * @property {string}   severity         - 'critical' | 'major' | 'minor'
 * @property {Element[]} affected_elements
 */

/**
 * @typedef {object} Element
 * @property {string} html
 * @property {string} selector
 * @property {string} context
 */
