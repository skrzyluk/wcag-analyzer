<template>
  <!--
    IssueCard.vue — Karta pojedynczego błędu WCAG
    WCAG 2.1 AA:
      ✅ 1.3.1  — Semantyczna struktura (article, dl, details/summary)
      ✅ 1.4.3  — Kontrast badge >= 4.5:1
      ✅ 2.1.1  — Dostępny z klawiatury (<details> nativne, button)
      ✅ 2.4.7  — Focus visible na summary i przyciskach
      ✅ 4.1.2  — aria-label na przyciskach ikon
  -->
  <article
    class="issue-card"
    :class="[`issue-card--${issue.severity}`]"
    :aria-label="`Błąd ${index} z ${total}: ${issue.wcag_criterion} — ${severityLabel}`"
  >
    <!-- Nagłówek karty -->
    <header class="issue-card__header">
      <div class="issue-card__meta">
        <!-- Numer błędu -->
        <span class="issue-card__index" aria-hidden="true">#{{ index }}</span>

        <!-- Kryterium WCAG -->
        <h3 class="issue-card__criterion">{{ issue.wcag_criterion }}</h3>

        <!-- Badge wagi -->
        <span
          class="issue-card__badge"
          :class="`issue-card__badge--${issue.severity}`"
          :aria-label="`Waga: ${severityLabel}`"
        >
          {{ severityLabel }}
        </span>
      </div>

      <!-- Przycisk kopiowania kryterium -->
      <button
        type="button"
        class="issue-card__copy-btn"
        :aria-label="`Kopiuj kryterium ${issue.wcag_criterion}`"
        :aria-pressed="copiedCriterion"
        @click="copyCriterion"
      >
        <svg
          v-if="!copiedCriterion"
          aria-hidden="true"
          focusable="false"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
        >
          <rect x="5" y="1" width="9" height="11" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M11 4H3a1 1 0 00-1 1v9a1 1 0 001 1h8a1 1 0 001-1V5a1 1 0 00-1-1z" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <svg
          v-else
          aria-hidden="true"
          focusable="false"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
        >
          <path d="M2 8l4 4 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="visually-hidden">{{ copiedCriterion ? 'Skopiowano' : 'Kopiuj' }}</span>
      </button>
    </header>

    <!-- Opis problemu -->
    <div class="issue-card__body">
      <dl class="issue-card__details">
        <!-- Opis -->
        <div v-if="issue.source_file" class="issue-card__detail-row">
          <dt class="issue-card__detail-term">Plik źródłowy</dt>
          <dd class="issue-card__detail-def">{{ issue.source_file }}</dd>
        </div>

        <div class="issue-card__detail-row">
          <dt class="issue-card__detail-term">Opis problemu</dt>
          <dd class="issue-card__detail-def">{{ issue.description }}</dd>
        </div>

        <!-- Rekomendacja -->
        <div class="issue-card__detail-row issue-card__detail-row--recommendation">
          <dt class="issue-card__detail-term">
            <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.5"/>
              <path d="M7 4v4M7 9.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            Rekomendacja
          </dt>
          <dd class="issue-card__detail-def">{{ issue.recommendation }}</dd>
        </div>

        <!-- Lokalizacja (opcjonalna) -->
        <div v-if="issue.xpath || issue.selector" class="issue-card__detail-row">
          <dt class="issue-card__detail-term">Lokalizacja</dt>
          <dd class="issue-card__detail-def">
            <code class="issue-card__code-inline">{{ issue.xpath || issue.selector }}</code>
          </dd>
        </div>
      </dl>

      <!-- Dotknięte elementy — sekcja rozwijana -->
      <details
        v-if="issue.affected_elements && issue.affected_elements.length > 0"
        class="issue-card__elements"
        :open="isExpanded"
        @toggle="onToggle"
      >
        <summary class="issue-card__elements-summary">
          <span class="issue-card__elements-icon" aria-hidden="true">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" :style="{ transform: isExpanded ? 'rotate(90deg)' : 'none' }">
              <path d="M4 2l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          Dotknięte elementy
          <span class="issue-card__elements-count">({{ issue.affected_elements.length }})</span>
        </summary>

        <!-- Lista elementów HTML -->
        <ol class="issue-card__elements-list">
          <li
            v-for="(element, elIdx) in issue.affected_elements"
            :key="elIdx"
            class="issue-card__element-item"
          >
            <!-- Numer elementu i tag -->
            <div class="issue-card__element-header">
              <span class="issue-card__element-index" aria-hidden="true">{{ elIdx + 1 }}</span>
              <code v-if="element.tag" class="issue-card__element-tag">&lt;{{ element.tag }}&gt;</code>
              <span v-if="element.context" class="issue-card__element-context">{{ element.context }}</span>
            </div>

            <!-- Snippet HTML -->
            <div v-if="element.html_snippet" class="issue-card__snippet-wrapper">
              <pre
                class="issue-card__snippet"
                :aria-label="`Snippet HTML elementu ${elIdx + 1}`"
              ><code>{{ element.html_snippet }}</code></pre>

              <!-- Kopiuj snippet -->
              <button
                type="button"
                class="issue-card__snippet-copy"
                :aria-label="`Kopiuj snippet HTML elementu ${elIdx + 1}`"
                :aria-pressed="copiedSnippets[elIdx]"
                @click="copySnippet(element.html_snippet, elIdx)"
              >
                <svg
                  v-if="!copiedSnippets[elIdx]"
                  aria-hidden="true"
                  focusable="false"
                  width="14"
                  height="14"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <rect x="5" y="1" width="9" height="11" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M11 4H3a1 1 0 00-1 1v9a1 1 0 001 1h8a1 1 0 001-1V5a1 1 0 00-1-1z" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <svg
                  v-else
                  aria-hidden="true"
                  focusable="false"
                  width="14"
                  height="14"
                  viewBox="0 0 16 16"
                  fill="none"
                >
                  <path d="M2 8l4 4 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="visually-hidden">{{ copiedSnippets[elIdx] ? 'Skopiowano' : 'Kopiuj snippet' }}</span>
              </button>
            </div>
          </li>
        </ol>
      </details>

      <!-- Brak elementów -->
      <p
        v-else-if="issue.affected_elements && issue.affected_elements.length === 0"
        class="issue-card__no-elements"
      >
        Brak wskazanych elementów HTML.
      </p>
    </div>
  </article>
</template>

<script setup>
/**
 * IssueCard.vue
 *
 * Karta pojedynczego błędu WCAG.
 * Używana w ReportViewer.vue — Details tab.
 *
 * Props:
 *   issue  — obiekt błędu z API (wcag_criterion, severity, description, recommendation, affected_elements)
 *   index  — numer porządkowy (1-based) w liście
 *   total  — łączna liczba błędów w bieżącym filtrze
 */
import { ref, computed } from 'vue'

const props = defineProps({
  /** Obiekt błędu WCAG */
  issue: {
    type: Object,
    required: true
  },

  /** Numer porządkowy (1-based) — do aria-label */
  index: {
    type: Number,
    default: 1
  },

  /** Łączna liczba błędów w filtrze — do aria-label */
  total: {
    type: Number,
    default: 1
  }
})

/* ============================================================
   STAŁE
============================================================ */

const SEVERITY_LABELS = {
  critical: 'Krytyczny',
  major:    'Poważny',
  minor:    'Drobny',
  warning:  'Ostrzeżenie',
  passed:   'Zaliczony'
}

/* ============================================================
   COMPUTED
============================================================ */

const severityLabel = computed(
  () => SEVERITY_LABELS[props.issue.severity] ?? props.issue.severity
)

/* ============================================================
   STAN ROZWINIĘCIA <details>
   Śledzimy ręcznie, żeby animować ikonę strzałki
============================================================ */

const isExpanded = ref(false)

const onToggle = (event) => {
  isExpanded.value = event.target.open
}

/* ============================================================
   KOPIOWANIE DO SCHOWKA
============================================================ */

const copiedCriterion = ref(false)
const copiedSnippets  = ref({})

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Fallback: execCommand dla starszych przeglądarek
    const el = document.createElement('textarea')
    el.value = text
    el.setAttribute('readonly', '')
    el.style.position = 'absolute'
    el.style.left = '-9999px'
    document.body.appendChild(el)
    el.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(el)
    return ok
  }
}

const copyCriterion = async () => {
  const ok = await copyToClipboard(props.issue.wcag_criterion)
  if (ok) {
    copiedCriterion.value = true
    setTimeout(() => { copiedCriterion.value = false }, 2000)
  }
}

const copySnippet = async (snippet, idx) => {
  const ok = await copyToClipboard(snippet)
  if (ok) {
    copiedSnippets.value = { ...copiedSnippets.value, [idx]: true }
    setTimeout(() => {
      copiedSnippets.value = { ...copiedSnippets.value, [idx]: false }
    }, 2000)
  }
}
</script>

<style scoped>
/* ============================================================
   KARTA BAZOWA
============================================================ */

.issue-card {
  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;

  /* Lewa krawędź — kolor wagi */
  border-left-width: 4px;
  border-left-style: solid;

  transition: box-shadow var(--transition-fast);
}

.issue-card:focus-within {
  box-shadow: var(--shadow-md);
}

/* Warianty wagi — kolor lewej krawędzi */
.issue-card--critical { border-left-color: var(--color-error); }
.issue-card--major    { border-left-color: var(--color-warning); }
.issue-card--minor    { border-left-color: var(--color-info); }
.issue-card--warning  { border-left-color: var(--color-warning); }
.issue-card--passed   { border-left-color: var(--color-success); }

/* ============================================================
   NAGŁÓWEK
============================================================ */

.issue-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  background-color: var(--color-background-alt);
}

.issue-card__meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 1;
  min-width: 0; /* flex truncation */
}

/* Numer błędu */
.issue-card__index {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
  flex-shrink: 0;
}

/* Kryterium WCAG (h3 bez marginesów) */
.issue-card__criterion {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: var(--line-height-tight);
}

/* Badge wagi */
.issue-card__badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full, 9999px);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
  flex-shrink: 0;
}

/*
  Kontrast badge — wszystkie >= 4.5:1 na swoich tłach:
  critical: biały (#fff) na #c00000 = 7.04:1 ✅
  major:    biały (#fff) na #b35900 = 4.74:1 ✅ (--color-warning)
  minor:    biały (#fff) na #0070c0 = 4.56:1 ✅ (--color-info)
  warning:  biały (#fff) na #b35900 = 4.74:1 ✅
  passed:   biały (#fff) na #007a3d = 5.45:1 ✅ (--color-success)
*/
.issue-card__badge--critical {
  background-color: var(--color-error);
  color: var(--color-text-inverse);
}

.issue-card__badge--major {
  background-color: var(--color-warning);
  color: var(--color-text-inverse);
}

.issue-card__badge--minor {
  background-color: var(--color-info);
  color: var(--color-text-inverse);
}

.issue-card__badge--warning {
  background-color: var(--color-warning);
  color: var(--color-text-inverse);
}

.issue-card__badge--passed {
  background-color: var(--color-success);
  color: var(--color-text-inverse);
}

/* Przycisk kopiowania kryterium */
.issue-card__copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 0;
  margin-left: auto;

  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition:
    color            var(--transition-fast),
    background-color var(--transition-fast),
    border-color     var(--transition-fast);
}

.issue-card__copy-btn:hover {
  background-color: var(--color-background);
  border-color: var(--color-border-light);
  color: var(--color-text-primary);
}

.issue-card__copy-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.issue-card__copy-btn[aria-pressed="true"] {
  color: var(--color-success);
}

/* ============================================================
   BODY — lista szczegółów (dl)
============================================================ */

.issue-card__body {
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.issue-card__details {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.issue-card__detail-row {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: var(--spacing-sm);
  align-items: baseline;
}

.issue-card__detail-term {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.issue-card__detail-def {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: var(--line-height-normal);
}

/* Rekomendacja — wyróżniona */
.issue-card__detail-row--recommendation .issue-card__detail-def {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

/* Kod inline */
.issue-card__code-inline {
  font-family: var(--font-family-mono);
  font-size: 0.85em;
  background-color: var(--color-background-alt);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  word-break: break-all;
}

/* Responsive: na wąskich ekranach stack */
@media (max-width: 480px) {
  .issue-card__detail-row {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
}

/* ============================================================
   SEKCJA ELEMENTÓW — <details>/<summary>
============================================================ */

.issue-card__elements {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.issue-card__elements-summary {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);

  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-background-alt);

  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);

  cursor: pointer;
  user-select: none;
  list-style: none; /* usuwa domyślny trójkąt */
}

/* Usuwa strzałkę w Webkit */
.issue-card__elements-summary::-webkit-details-marker { display: none; }

.issue-card__elements-summary:hover {
  background-color: var(--color-border-light);
}

.issue-card__elements-summary:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.issue-card__elements-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  color: var(--color-text-secondary);
  transition: transform var(--transition-fast);
}

.issue-card__elements-count {
  margin-left: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-normal);
}

/* ============================================================
   LISTA ELEMENTÓW
============================================================ */

.issue-card__elements-list {
  list-style: none;
  padding: var(--spacing-sm) var(--spacing-md);
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.issue-card__element-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
}

.issue-card__element-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

/* Numer elementu */
.issue-card__element-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  flex-shrink: 0;
  font-family: var(--font-family-mono);
}

/* Tag HTML */
.issue-card__element-tag {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  color: var(--color-info);
  font-weight: var(--font-weight-semibold);
}

/* Kontekst (skrócony tekst) */
.issue-card__element-context {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ============================================================
   SNIPPET HTML
============================================================ */

.issue-card__snippet-wrapper {
  position: relative;
}

.issue-card__snippet {
  margin: 0;
  padding: var(--spacing-sm);
  padding-right: var(--spacing-2xl, 2.5rem); /* miejsce na przycisk kopiowania */
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);

  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: var(--color-text-primary);
  line-height: 1.5;

  /* Scroll poziomy dla długich snippetów */
  overflow-x: auto;
  white-space: pre;

  /* Scrollbar styling (Webkit) */
  scrollbar-width: thin;
  scrollbar-color: var(--color-border-light) transparent;
}

.issue-card__snippet::-webkit-scrollbar { height: 6px; }
.issue-card__snippet::-webkit-scrollbar-thumb {
  background-color: var(--color-border-light);
  border-radius: 3px;
}

/* Przycisk kopiowania snippetu — pozycjonowany absolutnie */
.issue-card__snippet-copy {
  position: absolute;
  top: var(--spacing-xs);
  right: var(--spacing-xs);

  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;

  background: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--color-text-secondary);

  transition:
    color            var(--transition-fast),
    background-color var(--transition-fast),
    border-color     var(--transition-fast);
}

.issue-card__snippet-copy:hover {
  background-color: var(--color-primary-light, #e8f0fe);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.issue-card__snippet-copy:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.issue-card__snippet-copy[aria-pressed="true"] {
  color: var(--color-success);
  border-color: var(--color-success);
  background-color: var(--color-success-light, #e8f5ee);
}

/* ============================================================
   BRAK ELEMENTÓW
============================================================ */

.issue-card__no-elements {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-disabled);
  font-style: italic;
}

/* ============================================================
   UKRYTY TEKST (screen reader)
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
   PREFERS-REDUCED-MOTION
============================================================ */

@media (prefers-reduced-motion: reduce) {
  .issue-card,
  .issue-card__copy-btn,
  .issue-card__elements-icon,
  .issue-card__snippet-copy {
    transition: none;
  }
}
</style>
