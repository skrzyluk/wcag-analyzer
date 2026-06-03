/**
 * analysisStore.js — Pinia Store dla analiz WCAG
 * Projekt: WCAG 2.1 AA Analyzer
 *
 * Odpowiedzialności:
 *   - Stan aplikacji: lista analiz, bieżąca analiza, loading, błędy
 *   - Orchestracja flow: upload → analyze → poll status → report
 *   - Cache wyników (nie odpytujemy API dwa razy dla tego samego raportu)
 *   - Persistence (opcjonalnie — localStorage dla historii)
 */

import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { analysisService, ApiError } from '@/services/api'

// ── Stałe ─────────────────────────────────────────────────────────────────

const POLLING_INTERVAL_MS = 2000   // Jak często odpytujemy status analizy
const POLLING_MAX_ATTEMPTS = 60    // Max 60 * 2s = 2 minuty
const STORAGE_KEY = 'wcag-analyzer-history'

// ── Store ─────────────────────────────────────────────────────────────────

export const useAnalysisStore = defineStore('analysis', () => {

  // ────────────────────────────────────────────────────────────────────────
  // STATE
  // ────────────────────────────────────────────────────────────────────────

  /** Lista wszystkich analiz (historia) */
  const analyses = ref([])

  /** Aktualnie wyświetlana/przetwarzana analiza */
  const currentAnalysis = ref(null)

  /** ID pliku po uploadzie — potrzebne do wywołania analyze */
  const uploadedFileId = ref(null)

  /** Nazwa wgranego pliku — dla UX */
  const uploadedFileName = ref(null)

  /** Globalny stan ładowania */
  const isLoading = ref(false)

  /** Szczegółowy stan: który krok trwa ('upload' | 'analyze' | 'fetch' | null) */
  const loadingStep = ref(null)

  /** Postęp analizy (0–100) — z pollingu lub WebSocket */
  const analysisProgress = ref(0)

  /** Globalny błąd (ostatni) */
  const error = ref(null)

  /** Typ błędu dla UX: 'network' | 'validation' | 'server' | null */
  const errorType = ref(null)

  /** Cache: analysisId → AnalysisReport (unika ponownych requestów) */
  const reportCache = ref(new Map())

  /** Czy backend jest dostępny (z health check) */
  const backendAvailable = ref(null)  // null = nieznany, true/false

  /** Lista analiz auto-wczytanych przy starcie backendu z katalogu lokalnego */
  const preloadedAnalyses = ref([])

  /** Czy trwa polling preloaded (oczekiwanie na pending analizy) */
  const isPollingPreloaded = ref(false)

  // ────────────────────────────────────────────────────────────────────────
  // GETTERS (computed)
  // ────────────────────────────────────────────────────────────────────────

  /** Liczba analiz w historii */
  const analysisCount = computed(() => analyses.value.length)

  /** Czy jest aktualny błąd */
  const hasError = computed(() => error.value !== null)

  /** Czy trwa jakakolwiek operacja async */
  const isBusy = computed(() => isLoading.value)

  /** Czy można uruchomić analizę (plik wgrany, nie trwa operacja) */
  const canAnalyze = computed(() =>
    uploadedFileId.value !== null && !isLoading.value
  )

  /** Statystyki z bieżącej analizy — wygodny skrót */
  const currentSummary = computed(() =>
    currentAnalysis.value?.summary ?? null
  )

  /** Posortowane problemy wg severity: critical → major → minor */
  const currentIssuesSorted = computed(() => {
    if (!currentAnalysis.value?.issues) return []
    const order = { critical: 0, major: 1, minor: 2 }
    return [...currentAnalysis.value.issues].sort(
      (a, b) => (order[a.severity] ?? 99) - (order[b.severity] ?? 99)
    )
  })

  /** Ile krytycznych błędów w bieżącej analizie */
  const criticalCount = computed(() =>
    currentAnalysis.value?.summary?.critical_errors ?? 0
  )

  /** Procent zgodności z WCAG */
  const compliancePercentage = computed(() =>
    currentAnalysis.value?.summary?.compliance_percentage ?? null
  )

  /** Ostatnie 10 analiz (dla paska historii) */
  const recentAnalyses = computed(() =>
    [...analyses.value]
      .sort((a, b) => new Date(b.analysis_date) - new Date(a.analysis_date))
      .slice(0, 10)
  )

  // ────────────────────────────────────────────────────────────────────────
  // HELPERS — wewnętrzne
  // ────────────────────────────────────────────────────────────────────────

  /** Ustaw stan ładowania */
  const setLoading = (step) => {
    isLoading.value  = step !== null
    loadingStep.value = step
  }

  /** Ustaw błąd z ApiError lub zwykłego Error */
  const setError = (err) => {
    if (err instanceof ApiError) {
      error.value    = err.message
      errorType.value = err.statusCode === 0 ? 'network'
                      : err.statusCode >= 500 ? 'server'
                      : 'validation'
    } else {
      error.value    = err?.message || 'Wystąpił nieoczekiwany błąd.'
      errorType.value = 'server'
    }
    console.error('[analysisStore]', err)
  }

  /** Dodaj lub zaktualizuj analizę w historii */
  const upsertAnalysis = (analysis) => {
    const idx = analyses.value.findIndex(a => a.analysis_id === analysis.analysis_id)
    if (idx >= 0) {
      analyses.value[idx] = analysis
    } else {
      analyses.value.unshift(analysis)  // Najnowsze na początku
    }
    // Aktualizuj cache
    reportCache.value.set(analysis.analysis_id, analysis)
  }

  /** Polling — odpytuje status co POLLING_INTERVAL_MS ms */
  const pollAnalysisStatus = async (analysisId) => {
    let attempts = 0
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        attempts++
        try {
          const status = await analysisService.getAnalysisStatus(analysisId)
          analysisProgress.value = status.progress ?? analysisProgress.value

          if (status.status === 'done' || status.status === 'completed') {
            clearInterval(interval)
            resolve(analysisId)
          } else if (status.status === 'error') {
            clearInterval(interval)
            reject(new ApiError(
              'Analiza zakończyła się błędem po stronie serwera.',
              500, `/api/analyze/${analysisId}/status`
            ))
          } else if (attempts >= POLLING_MAX_ATTEMPTS) {
            clearInterval(interval)
            reject(new ApiError(
              'Analiza trwa zbyt długo. Spróbuj ponownie.',
              408, `/api/analyze/${analysisId}/status`
            ))
          }
        } catch (err) {
          clearInterval(interval)
          reject(err)
        }
      }, POLLING_INTERVAL_MS)
    })
  }

  // ────────────────────────────────────────────────────────────────────────
  // ACTIONS — publiczne
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Wgraj plik MHTML na serwer.
   * Po sukcesie ustawia uploadedFileId i uploadedFileName.
   *
   * @param {File} file
   * @returns {Promise<boolean>} true = sukces
   */
  const uploadFile = async (file) => {
    clearError()
    setLoading('upload')
    uploadedFileId.value   = null
    uploadedFileName.value = null

    try {
      const result = await analysisService.uploadFile(file)
      uploadedFileId.value   = result.file_id
      uploadedFileName.value = result.filename || file.name
      return true
    } catch (err) {
      setError(err)
      return false
    } finally {
      setLoading(null)
    }
  }

  /**
   * Uruchom analizę WCAG dla wcześniej wgranego pliku.
   * Automatycznie polluje status, a po zakończeniu pobiera raport.
   *
   * @param {string|null} fileId  - Jeśli null, używa uploadedFileId ze stanu
   * @param {object}      options - { criteria: string[] } — filtry kryteriów
   * @returns {Promise<AnalysisReport|null>}
   */
  const analyzeFile = async (fileId = null, options = {}) => {
    const id = fileId || uploadedFileId.value
    if (!id) {
      setError(new ApiError('Brak ID pliku. Najpierw wgraj plik.', 400))
      return null
    }

    clearError()
    setLoading('analyze')
    analysisProgress.value = 0

    try {
      // 1. Uruchom analizę
      const { analysis_id } = await analysisService.analyzeFile(id, options)

      // 2. Poll status do zakończenia
      await pollAnalysisStatus(analysis_id)
      analysisProgress.value = 100

      // 3. Pobierz pełny raport
      setLoading('fetch')
      const report = await analysisService.getReport(analysis_id)

      // 4. Zapisz w stanie
      currentAnalysis.value = report
      upsertAnalysis(report)

      return report
    } catch (err) {
      setError(err)
      return null
    } finally {
      setLoading(null)
    }
  }

  /**
   * Kompletny flow: upload + analyze w jednym atomowym wywołaniu.
   * isLoading pozostaje TRUE przez cały czas (upload → analyze → poll → fetch).
   * Nie wywołuje uploadFile() (który resetuje loading w finally) — robi wszystko samodzielnie.
   *
   * @param {File} file
   * @returns {Promise<AnalysisReport|null>}
   */
  const uploadAndAnalyze = async (file) => {
    clearError()
    setLoading('upload')
    uploadedFileId.value   = null
    uploadedFileName.value = null
    analysisProgress.value = 0

    try {
      // ── KROK 1: Upload ──────────────────────────────────────────
      console.log('[store] uploadAndAnalyze: upload start →', file?.name)
      const uploadResult = await analysisService.uploadFile(file)
      uploadedFileId.value   = uploadResult.file_id
      uploadedFileName.value = uploadResult.filename || file.name
      console.log('[store] uploadAndAnalyze: upload OK — file_id:', uploadedFileId.value)

      // ── KROK 2: Uruchom analizę ─────────────────────────────────
      setLoading('analyze')
      console.log('[store] uploadAndAnalyze: analyze start — file_id:', uploadedFileId.value)
      const { analysis_id } = await analysisService.analyzeFile(uploadedFileId.value, {})
      console.log('[store] uploadAndAnalyze: analyze called — analysis_id:', analysis_id)

      // ── KROK 3: Polling statusu ─────────────────────────────────
      await pollAnalysisStatus(analysis_id)
      analysisProgress.value = 100
      console.log('[store] uploadAndAnalyze: poll complete — 100%')

      // ── KROK 4: Pobierz pełny raport ────────────────────────────
      setLoading('fetch')
      const report = await analysisService.getReport(analysis_id)
      console.log('[store] uploadAndAnalyze: report fetched —', Object.keys(report))

      currentAnalysis.value = report
      upsertAnalysis(report)

      return report

    } catch (err) {
      console.error('[store] uploadAndAnalyze: BŁĄD —', err?.message || err)
      setError(err)
      return null
    } finally {
      setLoading(null)
      console.log('[store] uploadAndAnalyze: zakończono (isLoading = false)')
    }
  }

  /**
   * Batch flow: wgraj i przeanalizuj wiele plików równolegle.
   * Każdy plik przechodzi przez: upload → analyze → poll → fetch.
   *
   * @param {File[]} files - tablica plików do analizy
   * @param {object} options - { onFileProgress(filename, pct) }
   * @returns {Promise<Array<{filename, report}|{filename, error}>>}
   */
  const uploadAndAnalyzeBatch = async (files, options = {}) => {
    if (!files || files.length === 0) return []

    clearError()
    setLoading('upload')
    analysisProgress.value = 0

    const { onFileProgress } = options

    /**
     * Przetwarza jeden plik: upload → analyze → poll → fetch.
     * Zwraca { filename, report } lub { filename, error }.
     */
    const processOne = async (file) => {
      const filename = file.name
      try {
        // 1. Upload
        const uploadResult = await analysisService.uploadFile(file)
        const fileId = uploadResult.file_id
        onFileProgress?.(filename, 20)

        // 2. Uruchom analizę
        const { analysis_id } = await analysisService.analyzeFile(fileId, {})
        onFileProgress?.(filename, 40)

        // 3. Polling statusu
        await new Promise((resolve, reject) => {
          let attempts = 0
          const interval = setInterval(async () => {
            attempts++
            try {
              const status = await analysisService.getAnalysisStatus(analysis_id)
              if (status.status === 'done' || status.status === 'completed') {
                clearInterval(interval)
                resolve()
              } else if (status.status === 'error') {
                clearInterval(interval)
                reject(new Error('Analiza zakończyła się błędem.'))
              } else if (attempts >= 60) {
                clearInterval(interval)
                reject(new Error('Analiza trwa zbyt długo.'))
              } else {
                onFileProgress?.(filename, 40 + Math.min(50, attempts * 2))
              }
            } catch (err) {
              clearInterval(interval)
              reject(err)
            }
          }, 2000)
        })
        onFileProgress?.(filename, 90)

        // 4. Pobierz raport
        const report = await analysisService.getReport(analysis_id)
        upsertAnalysis(report)
        onFileProgress?.(filename, 100)

        return { filename, report }

      } catch (err) {
        console.error(`[store] batch błąd dla "${filename}":`, err?.message)
        return { filename, error: err?.message || 'Nieznany błąd.' }
      }
    }

    // Uruchom równolegle (max 5 jednocześnie — throttling)
    const CONCURRENCY = 5
    const results = []

    for (let i = 0; i < files.length; i += CONCURRENCY) {
      const chunk = files.slice(i, i + CONCURRENCY)
      const chunkResults = await Promise.all(chunk.map(processOne))
      results.push(...chunkResults)

      // Aktualizuj globalny postęp na podstawie ukończonych
      analysisProgress.value = Math.round(
        (results.length / files.length) * 100
      )
    }

    const successfulReports = results
      .filter(r => r.report?.analysis_id)
      .map(r => r.report)

    if (successfulReports.length === 0) {
      setError(new ApiError('Nie udało się przeanalizować żadnego pliku.', 500))
      setLoading(null)
      return results
    }

    try {
      setLoading('fetch')
      const combinedReport = successfulReports.length === 1
        ? successfulReports[0]
        : await analysisService.combineReports(successfulReports.map(r => r.analysis_id))

      currentAnalysis.value = combinedReport
      upsertAnalysis(combinedReport)

      return {
        reports: results,
        combinedReport,
        failed: results.filter(r => r.error),
      }
    } catch (err) {
      setError(err)
      return results
    } finally {
      setLoading(null)
    }
  }

  /**
   * Pobierz raport z cache lub z API.
   * @param {string} analysisId
   */
  const fetchReport = async (analysisId) => {
    // Cache hit
    if (reportCache.value.has(analysisId)) {
      currentAnalysis.value = reportCache.value.get(analysisId)
      return currentAnalysis.value
    }

    clearError()
    setLoading('fetch')
    try {
      const report = await analysisService.getReport(analysisId)
      currentAnalysis.value = report
      upsertAnalysis(report)
      return report
    } catch (err) {
      setError(err)
      return null
    } finally {
      setLoading(null)
    }
  }

  /**
   * Pobierz listę wszystkich analiz z backendu.
   * @param {object} params - { page, limit, sort }
   */
  const fetchReports = async (params = {}) => {
    clearError()
    setLoading('fetch')
    try {
      const { reports, total } = await analysisService.listReports(params)
      analyses.value = reports
      // Wypełnij cache
      reports.forEach(r => reportCache.value.set(r.analysis_id, r))
      return { reports, total }
    } catch (err) {
      setError(err)
      return null
    } finally {
      setLoading(null)
    }
  }

  /**
   * Eksportuj raport (inicjuje download pliku).
   * @param {string} analysisId
   * @param {'pdf'|'html'|'json'} format
   */
  const exportReport = async (analysisId, format) => {
    clearError()
    setLoading('fetch')
    try {
      await analysisService.exportReport(analysisId, format)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(null)
    }
  }

  /**
   * Usuń raport (lokalnie i z backendu).
   * @param {string} analysisId
   */
  const deleteReport = async (analysisId) => {
    clearError()
    try {
      await analysisService.deleteReport(analysisId)
      analyses.value = analyses.value.filter(a => a.analysis_id !== analysisId)
      reportCache.value.delete(analysisId)
      if (currentAnalysis.value?.analysis_id === analysisId) {
        currentAnalysis.value = null
      }
      return true
    } catch (err) {
      setError(err)
      return false
    }
  }

  /**
   * Sprawdź dostępność backendu.
   * @returns {Promise<boolean>}
   */
  const checkBackend = async () => {
    try {
      await analysisService.healthCheck()
      backendAvailable.value = true
      return true
    } catch {
      backendAvailable.value = false
      return false
    }
  }

  /**
   * Pobierz i obserwuj analizy auto-wczytane przy starcie backendu.
   * Polluje /api/preloaded co 2s, póki istnieją wpisy ze statusem "pending".
   * Gotowe raporty dodaje do historii analiz.
   */
  const loadPreloaded = async () => {
    if (isPollingPreloaded.value) return

    const fetchAndUpdate = async () => {
      try {
        const { preloaded } = await analysisService.getPreloaded()
        preloadedAnalyses.value = preloaded

        for (const entry of preloaded) {
          if (entry.status === 'completed' && !reportCache.value.has(entry.analysis_id)) {
            try {
              const report = await analysisService.getReport(entry.analysis_id)
              upsertAnalysis(report)
            } catch {
              // nie blokuje reszty
            }
          }
        }

        return preloaded.some(e => e.status === 'pending')
      } catch {
        return false  // backend niedostępny — zatrzymaj polling
      }
    }

    isPollingPreloaded.value = true
    let hasPending = await fetchAndUpdate()

    while (hasPending) {
      await new Promise(r => setTimeout(r, 2000))
      hasPending = await fetchAndUpdate()
    }

    isPollingPreloaded.value = false
  }

  /** Ustaw analizę jako bieżącą (bez API) */
  const setCurrentAnalysis = (analysis) => {
    currentAnalysis.value = analysis
  }

  /** Wyczyść błąd */
  const clearError = () => {
    error.value     = null
    errorType.value = null
  }

  /** Reset całego stanu (np. przy wylogowaniu / nowej sesji) */
  const reset = () => {
    analyses.value         = []
    currentAnalysis.value  = null
    uploadedFileId.value   = null
    uploadedFileName.value = null
    isLoading.value        = false
    loadingStep.value      = null
    analysisProgress.value = 0
    error.value            = null
    errorType.value        = null
    reportCache.value      = new Map()
  }

  // ────────────────────────────────────────────────────────────────────────
  // PERSISTENCE — LocalStorage (opcjonalne, dla historii między sesjami)
  // ────────────────────────────────────────────────────────────────────────

  const persistHistory = () => {
    try {
      const toSave = analyses.value.slice(0, 50).map(a => ({
        analysis_id:   a.analysis_id,
        filename:      a.filename,
        analysis_date: a.analysis_date,
        summary:       a.summary,
        status:        a.status
      }))
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
    } catch {
      // localStorage może być niedostępny (prywatny tryb, brak miejsca)
    }
  }

  const loadHistory = () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const history = JSON.parse(raw)
      if (Array.isArray(history)) {
        analyses.value = history
      }
    } catch {
      // Zignoruj błędny JSON
    }
  }

  // Wczytaj historię przy inicjalizacji store
  loadHistory()

  // ────────────────────────────────────────────────────────────────────────
  // RETURN — API publiczne store'a
  // ────────────────────────────────────────────────────────────────────────

  return {
    // State (readonly dla bezpieczeństwa)
    analyses:          readonly(analyses),
    currentAnalysis:   readonly(currentAnalysis),
    uploadedFileId:    readonly(uploadedFileId),
    uploadedFileName:  readonly(uploadedFileName),
    isLoading:         readonly(isLoading),
    loadingStep:       readonly(loadingStep),
    analysisProgress:  readonly(analysisProgress),
    error:             readonly(error),
    errorType:         readonly(errorType),
    backendAvailable:  readonly(backendAvailable),
    preloadedAnalyses: readonly(preloadedAnalyses),
    isPollingPreloaded: readonly(isPollingPreloaded),

    // Getters
    analysisCount,
    hasError,
    isBusy,
    canAnalyze,
    currentSummary,
    currentIssuesSorted,
    criticalCount,
    compliancePercentage,
    recentAnalyses,

    // Actions
    uploadFile,
    analyzeFile,
    uploadAndAnalyze,
    uploadAndAnalyzeBatch,
    fetchReport,
    fetchReports,
    exportReport,
    deleteReport,
    checkBackend,
    loadPreloaded,
    setCurrentAnalysis,
    clearError,
    reset,
    persistHistory,
    loadHistory,
  }
})
