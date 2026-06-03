<template>
  <!--
    HomeView.vue — Strona główna WCAG 2.1 AA Analyzer
    WCAG 2.1 AA:
      ✅ 1.3.1  — Semantyczne sekcje z aria-labelledby
      ✅ 1.4.3  — Kontrast tekstu >= 4.5:1 (tokeny CSS)
      ✅ 2.1.1  — Dostępność z klawiatury (natywne elementy)
      ✅ 2.4.1  — Skip link (w App.vue / layout)
      ✅ 2.4.6  — Nagłówki opisowe i informatywne
      ✅ 4.1.2  — role="status" dla komunikatów stanu
  -->
  <main class="home-view" id="home-main">

    <!-- ====================================================
         HERO SECTION
    ==================================================== -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero__content">
        <!-- Logo / Ikona -->
        <div class="hero__icon" aria-hidden="true">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false">
            <rect width="64" height="64" rx="16" fill="var(--color-primary)"/>
            <path d="M16 32h32M32 16v32" stroke="white" stroke-width="4" stroke-linecap="round"/>
            <circle cx="32" cy="32" r="10" stroke="white" stroke-width="3" fill="none"/>
          </svg>
        </div>

        <h1 id="hero-title" class="hero__title">WCAG 2.1 AA Analyzer</h1>

        <p class="hero__subtitle">
          Automatyczna analiza dostępności stron internetowych.<br>
          Lokalnie, offline, bez kosztów subskrypcji.
        </p>

        <!-- CTA Badge -->
        <div class="hero__badges" role="list" aria-label="Cechy aplikacji">
          <span class="hero__badge" role="listitem">🔒 Offline-first</span>
          <span class="hero__badge" role="listitem">🆓 Open-source</span>
          <span class="hero__badge" role="listitem">🇵🇱 Po polsku</span>
          <span class="hero__badge" role="listitem">⚡ < 30 sekund</span>
        </div>
      </div>
    </section>

    <!-- ====================================================
         UPLOADER SECTION
    ==================================================== -->
    <section class="uploader-section" aria-labelledby="uploader-title">
      <h2 id="uploader-title" class="section-title">Zacznij Analizę</h2>
      <p class="section-subtitle">
        Przeciągnij jeden lub wiele plików .mhtml (do 40 naraz) lub kliknij, aby wybrać ze swojego dysku.
      </p>

      <div class="uploader-wrapper">
        <FileUploader
          title="Wybierz pliki MHTML do analizy"
          :multiple="true"
          :max-files="40"
          :simulate-progress="false"
          @files-selected="handleFilesSelected"
          @file-selected="handleFileSelected"
          @upload-start="handleUploadStart"
          @file-cleared="handleFileCleared"
        />
      </div>

      <!-- Status uploadu / przejścia -->
      <div
        v-if="uploadStatus"
        class="upload-status"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        <span class="upload-status__icon" aria-hidden="true">
          {{ uploadStatus.icon }}
        </span>
        <span class="upload-status__text">{{ uploadStatus.message }}</span>
      </div>

      <!-- Error message -->
      <div
        v-if="uploadError"
        class="upload-error"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
      >
        <svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="8" stroke="currentColor" stroke-width="1.5"/>
          <path d="M9 5v5M9 12.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ uploadError }}</span>
      </div>
    </section>

    <!-- ====================================================
         WCZYTANE PLIKI — auto-analiza przy starcie
    ==================================================== -->
    <section
      v-if="preloadedAnalyses.length > 0"
      class="preloaded-section"
      aria-labelledby="preloaded-title"
    >
      <h2 id="preloaded-title" class="section-title">
        Wczytane pliki z katalogu audytu
      </h2>
      <p class="section-subtitle">
        Aplikacja automatycznie przeanalizowała pliki MHTML znalezione przy starcie.
        Kliknij plik, aby przejść do raportu.
      </p>

      <div
        v-if="isPollingPreloaded"
        class="preloaded-progress"
        role="status"
        aria-live="polite"
      >
        <span aria-hidden="true">⏳</span>
        Trwa analiza plików w tle…
      </div>

      <ul class="preloaded-list" role="list">
        <li
          v-for="entry in preloadedAnalyses"
          :key="entry.analysis_id"
          class="preloaded-item"
          :class="`preloaded-item--${entry.status}`"
        >
          <router-link
            v-if="entry.status === 'completed'"
            :to="{ name: 'analysis' }"
            class="preloaded-item__link"
            @click="goToReport(entry.analysis_id)"
            :aria-label="`Otwórz raport: ${entry.filename}`"
          >
            <span class="preloaded-item__icon" aria-hidden="true">📄</span>
            <span class="preloaded-item__name">{{ entry.filename }}</span>
            <span
              v-if="entry.summary"
              class="preloaded-item__badge"
              :class="entry.summary.critical_errors > 0 ? 'badge--error' : 'badge--ok'"
            >
              {{ entry.summary.compliance_percentage }}%
            </span>
            <span class="preloaded-item__arrow" aria-hidden="true">→</span>
          </router-link>

          <div v-else-if="entry.status === 'pending'" class="preloaded-item__row preloaded-item__row--pending">
            <span class="preloaded-item__icon" aria-hidden="true">⏳</span>
            <span class="preloaded-item__name">{{ entry.filename }}</span>
            <span class="preloaded-item__status-label">Analiza w toku…</span>
          </div>

          <div v-else-if="entry.status === 'error'" class="preloaded-item__row preloaded-item__row--error">
            <span class="preloaded-item__icon" aria-hidden="true">⚠️</span>
            <span class="preloaded-item__name">{{ entry.filename }}</span>
            <span class="preloaded-item__status-label">Błąd analizy</span>
          </div>
        </li>
      </ul>
    </section>

    <!-- ====================================================
         FEATURES SECTION
    ==================================================== -->
    <section class="features" aria-labelledby="features-title">
      <h2 id="features-title" class="section-title">Możliwości Analizatora</h2>
      <p class="section-subtitle">
        Sprawdzamy ~50 kryteriów WCAG 2.1 na poziomie AA — w czterech filarach dostępności.
      </p>

      <div class="features-grid" role="list">
        <article
          v-for="feature in features"
          :key="feature.id"
          class="feature-card"
          role="listitem"
          :aria-label="feature.title"
        >
          <div class="feature-card__icon" aria-hidden="true">{{ feature.icon }}</div>
          <h3 class="feature-card__title">{{ feature.title }}</h3>
          <p class="feature-card__desc">{{ feature.description }}</p>
        </article>
      </div>
    </section>

    <!-- ====================================================
         WCAG PILLARS SECTION
    ==================================================== -->
    <section class="pillars" aria-labelledby="pillars-title">
      <h2 id="pillars-title" class="section-title">4 Filary WCAG 2.1</h2>

      <ol class="pillars-list">
        <li
          v-for="pillar in wcagPillars"
          :key="pillar.code"
          class="pillar-item"
        >
          <div class="pillar-item__header">
            <span class="pillar-item__code" aria-label="`Filar ${pillar.code}`">
              {{ pillar.code }}
            </span>
            <strong class="pillar-item__name">{{ pillar.name }}</strong>
            <span class="pillar-item__count">{{ pillar.criteria }} kryteriów</span>
          </div>
          <p class="pillar-item__desc">{{ pillar.description }}</p>
        </li>
      </ol>
    </section>

    <!-- ====================================================
         HOW IT WORKS
    ==================================================== -->
    <section class="how-it-works" aria-labelledby="how-title">
      <h2 id="how-title" class="section-title">Jak To Działa</h2>

      <ol class="steps-list">
        <li
          v-for="(step, index) in steps"
          :key="index"
          class="step-item"
        >
          <div class="step-item__number" aria-hidden="true">{{ index + 1 }}</div>
          <div class="step-item__content">
            <strong class="step-item__title">{{ step.title }}</strong>
            <p class="step-item__desc">{{ step.description }}</p>
          </div>
        </li>
      </ol>
    </section>

  </main>
</template>

<script setup>
/**
 * HomeView.vue
 *
 * Strona główna aplikacji WCAG 2.1 AA Analyzer.
 * Prezentuje hero, uploader, features grid i opis działania.
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysisStore'
import FileUploader from '@/components/forms/FileUploader.vue'

/* ============================================================
   STAŁE — dane sekcji
============================================================ */

const features = [
  {
    id: 'offline',
    icon: '🔒',
    title: 'Offline-first',
    description: 'Działa całkowicie bez połączenia z internetem. Twoje pliki nie opuszczają komputera.'
  },
  {
    id: 'fast',
    icon: '⚡',
    title: 'Szybka Analiza',
    description: 'Kompletna weryfikacja ~50 kryteriów WCAG 2.1 AA w mniej niż 30 sekund.'
  },
  {
    id: 'detailed',
    icon: '📋',
    title: 'Szczegółowe Raporty',
    description: 'Każdy błąd zawiera opis, rekomendację i wskazanie konkretnego elementu HTML.'
  },
  {
    id: 'export',
    icon: '📤',
    title: 'Eksport Raportów',
    description: 'Generuj raporty w formatach HTML, PDF i JSON — gotowe do dołączenia do dokumentacji.'
  },
  {
    id: 'history',
    icon: '📊',
    title: 'Historia Analiz',
    description: 'Porównuj wyniki w czasie — śledź postęp w poprawie dostępności swojej strony.'
  },
  {
    id: 'free',
    icon: '🆓',
    title: 'Całkowicie Darmowy',
    description: 'Open-source, bez paywall, bez subskrypcji. Dla webdeveloperów i instytucji publicznych.'
  }
]

const wcagPillars = [
  {
    code: '1.',
    name: 'Postrzegalność',
    criteria: 18,
    description: 'Treść i interfejs muszą być dostrzegalne dla wszystkich użytkowników — tekst alternatywny, kontrast, napisy.'
  },
  {
    code: '2.',
    name: 'Funkcjonalność',
    criteria: 16,
    description: 'Interfejs musi być w pełni obsługiwany z klawiatury — brak pułapek na fokus, widoczny wskaźnik.'
  },
  {
    code: '3.',
    name: 'Zrozumiałość',
    criteria: 10,
    description: 'Treść i obsługa interfejsu muszą być zrozumiałe — język strony, czytelne etykiety, walidacja formularzy.'
  },
  {
    code: '4.',
    name: 'Solidność',
    criteria: 4,
    description: 'Treść musi być wystarczająco solidna, by mogły ją interpretować różne technologie wspomagające.'
  }
]

const steps = [
  {
    title: 'Zapisz stronę jako MHTML',
    description: 'W przeglądarce Chrome: Ctrl+S → format "Strona internetowa, jeden plik". Plik .mhtml zawiera cały HTML, CSS i zasoby.'
  },
  {
    title: 'Wgraj plik do Analizatora',
    description: 'Przeciągnij plik .mhtml na pole poniżej lub kliknij "Wybierz plik". Maksymalny rozmiar: 50 MB.'
  },
  {
    title: 'Uruchom Analizę',
    description: 'Kliknij "Analizuj" — backend sprawdzi ~50 kryteriów WCAG 2.1 AA. Wyniki pojawią się w ciągu 30 sekund.'
  },
  {
    title: 'Przejrzyj Raport i Eksportuj',
    description: 'Raport grupuje błędy według wagi i kryterium WCAG. Eksportuj do PDF lub HTML dla klienta / audytora.'
  }
]

/* ============================================================
   UPLOAD STATE
============================================================ */

const uploadStatus = ref(null)
const uploadError  = ref(null)

const router        = useRouter()
const analysisStore = useAnalysisStore()

const preloadedAnalyses = computed(() => analysisStore.preloadedAnalyses)
const isPollingPreloaded = computed(() => analysisStore.isPollingPreloaded)

const goToReport = (analysisId) => {
  const report = analysisStore.analyses.find(a => a.analysis_id === analysisId)
  if (report) analysisStore.setCurrentAnalysis(report)
}

/**
 * Wywoływany gdy użytkownik wybrał ≥1 plik (multi-file event).
 * Aktualizuje tylko status — faktyczny upload startuje z "upload-start".
 */
const handleFilesSelected = ({ files, count, totalSize }) => {
  uploadError.value  = null
  const totalMB = (totalSize / 1024 / 1024).toFixed(2)
  uploadStatus.value = {
    icon:    '📂',
    message: count === 1
      ? `Gotowy do analizy: "${files[0].name}" (${totalMB} MB)`
      : `Gotowe do analizy: ${count} pliki/plików (łącznie ${totalMB} MB)`
  }
}

/**
 * Backward-compat — wywoływany dla pojedynczego pliku.
 */
const handleFileSelected = ({ file, name, size }) => {
  uploadError.value  = null
  const sizeMB = (size / 1024 / 1024).toFixed(2)
  uploadStatus.value = {
    icon:    '📄',
    message: `Gotowy do analizy: "${name}" (${sizeMB} MB)`
  }
}

/**
 * Wywoływany po kliknięciu "Analizuj N plików".
 * Payload: File[] (tablica)
 */
const handleUploadStart = async (files) => {
  uploadError.value  = null

  // Normalizacja — może przyjść pojedynczy File lub File[]
  const fileArray = Array.isArray(files) ? files : [files]

  const count = fileArray.length
  uploadStatus.value = {
    icon:    '⏳',
    message: count === 1
      ? `Analizowanie "${fileArray[0].name}"…`
      : `Analizowanie ${count} plików…`
  }

  // Przejdź do widoku analizy
  await router.push('/analysis')

  if (count === 1) {
    // Pojedynczy plik — istniejący flow
    analysisStore.uploadAndAnalyze(fileArray[0])
  } else {
    // Batch — nowy flow
    analysisStore.uploadAndAnalyzeBatch(fileArray)
  }
}

const handleFileCleared = () => {
  uploadStatus.value = null
  uploadError.value  = null
}
</script>

<style scoped>
/* ============================================================
   LAYOUT BAZOWY
============================================================ */

.home-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3xl, 4rem);
}

/* ============================================================
   HERO
============================================================ */

.hero {
  text-align: center;
  padding: var(--spacing-3xl, 4rem) 0 var(--spacing-2xl, 2.5rem);
}

.hero__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-lg);
}

.hero__icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero__title {
  margin: 0;
  font-size: clamp(var(--font-size-2xl), 5vw, 3rem);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  letter-spacing: -0.02em;
}

.hero__subtitle {
  margin: 0;
  max-width: 56ch;
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

/* Badges */
.hero__badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  justify-content: center;
  margin-top: var(--spacing-sm);
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  background-color: var(--color-primary-light);
  color: var(--color-primary-dark);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

/* ============================================================
   TYTUŁY SEKCJI (wspólne)
============================================================ */

.section-title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.section-subtitle {
  margin: 0 0 var(--spacing-xl);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 72ch;
  line-height: var(--line-height-normal);
}

/* ============================================================
   UPLOADER SECTION
============================================================ */

.uploader-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--spacing-xl);
}

.uploader-wrapper {
  max-width: 640px;
}

/* Status uploadu */
.upload-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-background-alt);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.upload-status__icon { font-size: 1.1em; }

/* Error */
.upload-error {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-error-light);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-error);
}

/* ============================================================
   FEATURES GRID
============================================================ */

.features {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--spacing-xl);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-lg);
}

.feature-card {
  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}

.feature-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.feature-card__icon {
  font-size: 2rem;
  margin-bottom: var(--spacing-sm);
  line-height: 1;
}

.feature-card__title {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.feature-card__desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

/* ============================================================
   WCAG PILLARS
============================================================ */

.pillars {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--spacing-xl);
}

.pillars-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-md);
}

.pillar-item {
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.pillar-item__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
  flex-wrap: wrap;
}

.pillar-item__code {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  flex-shrink: 0;
}

.pillar-item__name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.pillar-item__count {
  margin-left: auto;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.pillar-item__desc {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

/* ============================================================
   HOW IT WORKS
============================================================ */

.how-it-works {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--spacing-xl);
}

.steps-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  counter-reset: steps;
}

.step-item {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.step-item__number {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  font-family: var(--font-family-mono);
}

.step-item__content {
  padding-top: var(--spacing-xs);
}

.step-item__title {
  display: block;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.step-item__desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

/* ============================================================
   WCZYTANE PLIKI — preloaded section
============================================================ */

.preloaded-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--spacing-xl);
}

.preloaded-progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-background-alt);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.preloaded-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.preloaded-item__link,
.preloaded-item__row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background-color: var(--color-background);
  text-decoration: none;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  transition: box-shadow var(--transition-fast);
}

.preloaded-item__link:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--color-primary);
}

.preloaded-item__link:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.preloaded-item__name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preloaded-item__icon {
  flex-shrink: 0;
  font-size: 1em;
}

.preloaded-item__badge {
  flex-shrink: 0;
  padding: 2px var(--spacing-xs);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.badge--ok    { background-color: var(--color-success-light, #d1fae5); color: var(--color-success, #065f46); }
.badge--error { background-color: var(--color-error-light, #fee2e2);   color: var(--color-error, #991b1b); }

.preloaded-item__arrow {
  flex-shrink: 0;
  color: var(--color-primary);
}

.preloaded-item__status-label {
  flex-shrink: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.preloaded-item__row--error {
  border-color: var(--color-error-light, #fee2e2);
  background-color: var(--color-error-light, #fee2e2);
}

/* ============================================================
   RESPONSYWNOŚĆ
============================================================ */

@media (max-width: 639px) {
  .home-view {
    padding: var(--spacing-lg) var(--spacing-md);
    gap: var(--spacing-2xl, 2.5rem);
  }

  .hero {
    padding: var(--spacing-xl) 0 var(--spacing-lg);
  }

  .hero__subtitle {
    font-size: var(--font-size-base);
  }

  .hero__badges {
    gap: var(--spacing-xs);
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .pillars-list {
    grid-template-columns: 1fr;
  }
}

/* ============================================================
   PREFERS-REDUCED-MOTION
============================================================ */

@media (prefers-reduced-motion: reduce) {
  .feature-card {
    transition: none;
  }

  .feature-card:hover {
    transform: none;
  }
}
</style>
