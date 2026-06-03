<template>
  <!--
    AnalysisView.vue — Widok analizy MHTML
    WCAG 2.1 AA:
      ✅ 1.3.1  — Semantyczna struktura (main, sections, h1/h2)
      ✅ 2.4.6  — Opisowe nagłówki dla każdego stanu widoku
      ✅ 3.3.1  — Komunikaty błędów z role="alert"
      ✅ 4.1.3  — aria-live="polite" dla statusu postępu
      ✅ 4.1.2  — aria-busy na kontenerze podczas ładowania
  -->
  <main
    class="analysis-view"
    :aria-busy="isLoading ? 'true' : undefined"
  >

    <!--
      DEV STATUS BAR — widoczny bez DevTools (wewnątrz main = jeden root = Transition działa).
      Można usunąć po potwierdzeniu że flow działa poprawnie.
    -->
    <div
      v-if="isLoading || hasError"
      class="dev-status-bar"
      :class="hasError ? 'dev-status-bar--error' : 'dev-status-bar--loading'"
      role="status"
      aria-live="polite"
    >
      <span v-if="isLoading">
        ⏳ <strong>{{ loadingStepLabel }}</strong>
        <span v-if="analysisProgress > 0"> — {{ analysisProgress }}%</span>
      </span>
      <span v-else-if="hasError">
        ❌ <strong>Błąd:</strong> {{ error }}
      </span>
    </div>

    <!-- ====================================================
         STAN 1: BRAK PLIKU — upload + ewentualny raport
    ==================================================== -->
    <div v-if="!currentReport" class="analysis-view__upload">

      <!-- Nagłówek sekcji uploadu -->
      <section class="upload-section" aria-labelledby="upload-title">
        <header class="upload-section__header">
          <h1 id="upload-title" class="upload-section__title">
            {{ isLoading ? 'Analiza w toku…' : 'Nowa Analiza' }}
          </h1>
          <p class="upload-section__subtitle">
            {{ isLoading
              ? `${loadingStep || 'Przetwarzanie pliku — proszę czekać.'}`
              : 'Wgraj plik .mhtml, aby rozpocząć weryfikację WCAG 2.1 AA.'
            }}
          </p>
        </header>

        <!-- FileUploader — wyłączony podczas analizy -->
        <div class="upload-section__uploader">
          <FileUploader
            title="Wybierz pliki MHTML do analizy"
            :simulate-progress="false"
            :disabled-override="isLoading"
            :multiple="true"
            :max-files="40"
            @files-selected="handleFilesSelected"
            @file-selected="handleFileSelected"
            @upload-start="handleUploadStart"
            @file-cleared="handleFileCleared"
          />
        </div>

        <!-- Przycisk Analizuj — widoczny gdy plik wybrany i nie trwa analiza -->
        <div
          v-if="selectedFiles.length > 0 && !isLoading"
          class="upload-section__actions"
        >
          <Button
            variant="primary"
            size="lg"
            :loading="false"
            @click="startAnalysis"
          >
            {{ selectedFiles.length === 1 ? 'Analizuj plik' : `Analizuj ${selectedFiles.length} plików` }}
          </Button>
          <Button
            variant="ghost"
            size="lg"
            @click="clearFile"
          >
            Wyczyść
          </Button>
        </div>
      </section>

      <!-- ====================================================
           SEKCJA: POSTĘP ANALIZY — AnalysisProgress komponent
      ==================================================== -->
      <AnalysisProgress
        v-if="isLoading"
        :progress="analysisProgress"
        :current-step="loadingStep || 'Przetwarzanie pliku…'"
        :estimated-time="estimatedSeconds"
        :steps="progressSteps"
        :filename="selectedFiles.length > 1 ? `${selectedFiles.length} plików` : selectedFile ? selectedFile.name : undefined"
        @cancel="handleCancel"
      />

      <!-- ====================================================
           SEKCJA: BŁĄD ANALIZY
      ==================================================== -->
      <section
        v-if="hasError && !isLoading"
        class="error-section"
        aria-labelledby="error-title"
      >
        <div
          class="error-alert"
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          <!-- Ikona -->
          <svg class="error-alert__icon" aria-hidden="true" focusable="false" width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v5M12 15.5v.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>

          <div class="error-alert__content">
            <strong id="error-title" class="error-alert__title">Błąd analizy</strong>
            <p class="error-alert__message">{{ error }}</p>
          </div>
        </div>

        <!-- Akcje po błędzie -->
        <div class="error-section__actions">
          <Button variant="primary" @click="retryAnalysis">
            Spróbuj ponownie
          </Button>
          <Button variant="ghost" @click="clearAll">
            Zacznij od nowa
          </Button>
        </div>
      </section>

    </div>

    <!-- ====================================================
         STAN 2: RAPORT — wyświetlanie wyników
    ==================================================== -->
    <div v-if="currentReport" class="analysis-view__report">

      <!-- Breadcrumb / nawigacja powrotna -->
      <nav class="report-nav" aria-label="Nawigacja w analizie">
        <Button
          variant="ghost"
          size="sm"
          :aria-label="`Wróć do uploadu i wykonaj nową analizę`"
          @click="handleNewAnalysis"
        >
          <template #icon-start>
            <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M9 2L4 7l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </template>
          Nowa Analiza
        </Button>

        <span class="report-nav__filename" aria-label="Analizowany plik">
          {{ currentReport.filename }}
        </span>
      </nav>

      <!-- Fallback gdy ReportViewer crashuje (onErrorCaptured) -->
      <div v-if="childError" style="padding:20px;background:#fef2f2;border:2px solid #dc2626;border-radius:8px;color:#991b1b;font-size:14px;">
        <strong>⚠️ Błąd renderowania raportu:</strong> {{ childError }}<br>
        <small>Sprawdź konsolę F12 → Console po szczegóły.</small>
      </div>

      <!-- Szybki podgląd danych (widoczny zawsze gdy jest raport — do diagnostyki) -->
      <div style="padding:12px 16px;background:#f0fdf4;border:1px solid #86efac;border-radius:8px;font-size:13px;color:#166534;margin-bottom:8px;">
        ✅ Raport gotowy: <strong>{{ currentReport.filename }}</strong> —
        zgodność: <strong>{{ currentReport.summary?.compliance_percentage }}%</strong> —
        problemów: <strong>{{ currentReport.issues?.length ?? 0 }}</strong>
      </div>

      <!-- ReportViewer — główny widok raportu -->
      <ReportViewer
        v-if="!childError"
        :report="currentReport"
        @export="handleExport"
      />

      <!-- Akcje raportu (duplikat dla wygody — na dole) -->
      <footer class="report-actions" aria-label="Akcje raportu">
        <Button
          variant="secondary"
          @click="handleNewAnalysis"
        >
          Nowa Analiza
        </Button>

        <div class="report-actions__export">
          <ExportButton
            :analysis-id="currentReport.id || currentReport.analysis_id || 'mock'"
            :filename="currentReport.filename || 'raport-wcag'"
            @export-start="onExportStart"
            @export-success="onExportSuccess"
            @export-error="onExportError"
          />
        </div>
      </footer>
    </div>

  </main>
</template>

<script setup>
/**
 * AnalysisView.vue
 *
 * Główny widok analizy MHTML. Obsługuje 3 stany:
 *  1. Upload + wybór pliku
 *  2. Analiza w toku (progress bar, kroki)
 *  3. Wyświetlenie raportu (ReportViewer)
 *
 * Integruje się z analysisStore przez Pinia.
 */
import { ref, computed, watch, onErrorCaptured } from 'vue'
import { useAnalysisStore }     from '@/stores/analysisStore'
import FileUploader             from '@/components/forms/FileUploader.vue'
import ReportViewer             from '@/components/results/ReportViewer.vue'
import Button                   from '@/components/ui/Button.vue'
import AnalysisProgress         from '@/components/results/AnalysisProgress.vue'
import ExportButton             from '@/components/results/ExportButton.vue'

/* ============================================================
   STORE
============================================================ */

const analysisStore  = useAnalysisStore()

const currentReport  = computed(() => analysisStore.currentAnalysis)

// ── Debug: śledź zmianę raportu ────────────────────────────────
watch(currentReport, (val) => {
  console.log('[AnalysisView] currentReport changed →', val ? `OK (${val.filename})` : 'null')
}, { immediate: true })

// ── Łap błędy z komponentów potomnych (np. ReportViewer) ───────
const childError = ref(null)
onErrorCaptured((err, instance, info) => {
  console.error('[AnalysisView] ❌ Błąd w komponencie potomnym:', err?.message, info)
  childError.value = `${err?.message || err} (${info})`
  return false  // nie propaguj wyżej
})
const isLoading      = computed(() => analysisStore.isLoading)
const loadingStep    = computed(() => analysisStore.loadingStep)
const analysisProgress = computed(() => analysisStore.analysisProgress ?? 0)
const hasError       = computed(() => analysisStore.hasError)
const error          = computed(() => analysisStore.error)

/* ============================================================
   LOKALNY STAN
============================================================ */

/** Plik wybrany przez FileUploader (File object) */
const selectedFile = ref(null)
const selectedFiles = ref([])

/* ============================================================
   KROKI POSTĘPU — symulacja UI (real data z backend w v2)
============================================================ */

const STEPS = [
  { id: 'parse',     label: 'Parsowanie pliku MHTML' },
  { id: 'extract',   label: 'Ekstrakcja zasobów HTML/CSS' },
  { id: 'wcag1',     label: 'Sprawdzanie — Postrzegalność' },
  { id: 'wcag2',     label: 'Sprawdzanie — Funkcjonalność' },
  { id: 'wcag3',     label: 'Sprawdzanie — Zrozumiałość' },
  { id: 'wcag4',     label: 'Sprawdzanie — Solidność' },
  { id: 'report',    label: 'Generowanie raportu' }
]

const progressSteps = computed(() => {
  const pct = analysisProgress.value
  return STEPS.map((step, index) => {
    const stepPct = ((index + 1) / STEPS.length) * 100
    const prevPct = (index / STEPS.length) * 100
    return {
      ...step,
      status: pct >= stepPct ? 'done'
            : pct >  prevPct ? 'active'
            : 'pending'
    }
  })
})

/* ============================================================
   OBSŁUGA ZDARZEŃ FileUploader
============================================================ */

const handleFileSelected = ({ file, name, size }) => {
  selectedFile.value = file ?? null
  selectedFiles.value = file ? [file] : []
  console.log('[AnalysisView] Plik wybrany:', name, `(${(size/1024/1024).toFixed(2)} MB)`)
}

const handleFilesSelected = ({ files }) => {
  selectedFiles.value = Array.isArray(files) ? files : []
  selectedFile.value = selectedFiles.value[0] ?? null
}

const handleUploadStart = async (fileOrFiles) => {
  const files = Array.isArray(fileOrFiles) ? fileOrFiles : [fileOrFiles]
  selectedFiles.value = files.filter(Boolean)
  selectedFile.value = selectedFiles.value[0] ?? null
  await startAnalysis()
}

const handleFileCleared = () => {
  selectedFile.value = null
  selectedFiles.value = []
  analysisStore.clearError?.()
}

/* ============================================================
   AKCJE ANALIZY
============================================================ */

/**
 * Uruchamia upload + analizę przez store.
 * Store sam zarządza polling i stanem progress.
 */
const startAnalysis = async () => {
  if (selectedFiles.value.length === 0) {
    console.warn('[AnalysisView] startAnalysis: brak plików')
    return
  }
  const result = selectedFiles.value.length === 1
    ? await analysisStore.uploadAndAnalyze(selectedFiles.value[0])
    : await analysisStore.uploadAndAnalyzeBatch(selectedFiles.value)
  console.log('[AnalysisView] Wynik analizy:', result ? 'OK' : 'BŁĄD', analysisStore.error || '')
}

/** Czytelna nazwa bieżącego kroku dla paska statusu */
const loadingStepLabel = computed(() => {
  const map = {
    upload:  'Przesyłanie pliku do serwera…',
    analyze: 'Analiza WCAG w toku…',
    fetch:   'Pobieranie raportu…',
  }
  return map[loadingStep.value] || 'Przetwarzanie…'
})

/** Szacowany czas (uproszczony — 2% = ~1s, max 60s) */
const estimatedSeconds = computed(() => {
  const pct = analysisProgress.value
  if (pct >= 100 || pct === 0) return null
  const remaining = Math.round(((100 - pct) / 2))
  return Math.min(remaining, 60)
})

/** Anulowanie analizy */
const handleCancel = () => {
  // Resetujemy cały store — $patch nie działa na readonly refs
  analysisStore.reset()
  selectedFile.value = null
  selectedFiles.value = []
}

const retryAnalysis = async () => {
  if (selectedFiles.value.length === 0) return
  if (selectedFiles.value.length === 1) {
    await analysisStore.uploadAndAnalyze(selectedFiles.value[0])
  } else {
    await analysisStore.uploadAndAnalyzeBatch(selectedFiles.value)
  }
}

const clearFile = () => {
  selectedFile.value = null
  selectedFiles.value = []
}

const clearAll = () => {
  selectedFile.value = null
  selectedFiles.value = []
  analysisStore.clearError?.()
}

/* ============================================================
   NOWA ANALIZA — reset stanu
============================================================ */

const handleNewAnalysis = () => {
  selectedFile.value = null
  selectedFiles.value = []
  // Reset store do stanu początkowego (reset() działa na wewnętrznych ref-ach, bez $patch)
  analysisStore.reset()
}

/* ============================================================
   EKSPORT RAPORTU
============================================================ */

/**
 * Callbacki dla ExportButton — opcjonalne logowanie / toast
 */
const onExportStart = (format) => {
  console.info(`[AnalysisView] Export start: ${format}`)
}

const onExportSuccess = (format) => {
  console.info(`[AnalysisView] Export success: ${format}`)
  // Tu można wywołać uiStore.showToast({ type: 'success', message: ... })
}

const onExportError = (format, err) => {
  console.error(`[AnalysisView] Export error (${format}):`, err)
}

// Zachowane dla @export emit z ReportViewer (deleguje do ExportButton)
const handleExport = (format) => {
  console.info('[AnalysisView] handleExport delegated:', format)
}
</script>

<style scoped>
/* ============================================================
   LAYOUT
============================================================ */

.analysis-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
  min-height: 60vh;
  display: flex;
  flex-direction: column;
}

/* ============================================================
   UPLOAD STATE
============================================================ */

.analysis-view__upload {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  max-width: 720px;
}

/* Nagłówek sekcji upload */
.upload-section {}

.upload-section__header {
  margin-bottom: var(--spacing-xl);
}

.upload-section__title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.upload-section__subtitle {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

.upload-section__uploader {
  /* Kontenery FileUploader */
}

/* Akcje po wybraniu pliku */
.upload-section__actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  flex-wrap: wrap;
}

/* ============================================================
   PROGRESS SECTION
============================================================ */

.progress-section {
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Progress bar */
.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.progress-bar {
  flex: 1;
  height: 12px;
  background-color: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background-color: var(--color-primary);
  border-radius: inherit;
  transition: width 0.4s ease;
}

.progress-bar__label {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  min-width: 40px;
  text-align: right;
}

/* Kroki analizy */
.progress-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.progress-steps__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  transition: background-color var(--transition-fast);
}

.progress-steps__item--done {
  color: var(--color-success);
  background-color: var(--color-success-light);
}

.progress-steps__item--active {
  color: var(--color-primary);
  background-color: var(--color-primary-light);
  font-weight: var(--font-weight-medium);
}

.progress-steps__item--pending {
  color: var(--color-text-disabled);
}

.progress-steps__icon {
  font-size: 1em;
  flex-shrink: 0;
  width: 1.2em;
  text-align: center;
}

/* ============================================================
   ERROR SECTION
============================================================ */

.error-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.error-alert {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
  padding: var(--spacing-lg);
  background-color: var(--color-error-light);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-lg);
  color: var(--color-error);
}

.error-alert__icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.error-alert__title {
  display: block;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-xs);
}

.error-alert__message {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: var(--line-height-normal);
}

.error-section__actions {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

/* ============================================================
   REPORT STATE
============================================================ */

.analysis-view__report {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Nawigacja raportu */
.report-nav {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
  flex-wrap: wrap;
}

.report-nav__filename {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 40ch;
}

/* Akcje stopki raportu */
.report-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.report-actions__export {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

/* ============================================================
   VISUALLY HIDDEN
============================================================ */

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ============================================================
   RESPONSYWNOŚĆ
============================================================ */

@media (max-width: 639px) {
  .analysis-view {
    padding: var(--spacing-lg) var(--spacing-md);
  }

  .upload-section__title {
    font-size: var(--font-size-xl);
  }

  .upload-section__actions {
    flex-direction: column;
  }

  .report-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .report-actions__export {
    flex-direction: column;
  }

  .report-nav__filename {
    max-width: 20ch;
  }
}

/* ============================================================
   PREFERS-REDUCED-MOTION
============================================================ */

@media (prefers-reduced-motion: reduce) {
  .progress-bar__fill,
  .progress-steps__item {
    transition: none;
  }
}

/* ============================================================
   DEV STATUS BAR — diagnostyczny pasek stanu (można usunąć po debugowaniu)
============================================================ */

.dev-status-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  gap: var(--spacing-xs);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.dev-status-bar--loading {
  background-color: #1e40af;   /* ciemny niebieski — kontrast na biały tekst 7:1 */
  color: #ffffff;
}

.dev-status-bar--error {
  background-color: #991b1b;   /* ciemny czerwony — kontrast na biały tekst 7:1 */
  color: #ffffff;
}
</style>
