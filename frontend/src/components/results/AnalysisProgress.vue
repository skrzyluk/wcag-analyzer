<template>
  <!--
    AnalysisProgress.vue — Wskaźnik postępu analizy WCAG
    WCAG 2.1 AA:
      ✅ 1.4.3  — Kontrast tekstu >= 4.5:1 (tokeny CSS)
      ✅ 2.1.1  — Przycisk Anuluj dostępny z klawiatury
      ✅ 2.4.7  — Focus visible na przycisku Anuluj
      ✅ 4.1.2  — role="progressbar" z aria-valuenow/min/max
      ✅ 4.1.3  — aria-live="polite" + aria-atomic dla zmian statusu
  -->
  <div
    class="analysis-progress"
    aria-label="Postęp analizy WCAG"
  >

    <!-- Nagłówek: tytuł + aktualny krok -->
    <header class="analysis-progress__header">
      <h3 class="analysis-progress__title" id="progress-label">
        Analiza w toku…
      </h3>

      <!-- Status - ogłaszany przez screen reader przy każdej zmianie -->
      <p
        class="analysis-progress__step"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {{ currentStep }}
      </p>
    </header>

    <!-- Progress bar -->
    <div class="analysis-progress__bar-wrapper">
      <div
        class="analysis-progress__bar"
        role="progressbar"
        :aria-valuenow="progress"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Postęp analizy: ${progress}%`"
        :aria-labelledby="undefined"
      >
        <div
          class="analysis-progress__bar-fill"
          :style="{ width: `${progress}%` }"
        />
      </div>
    </div>

    <!-- Szczegóły postępu: % + szacowany czas -->
    <div
      class="analysis-progress__details"
      aria-live="polite"
      aria-atomic="true"
    >
      <span class="analysis-progress__percent">
        <strong>{{ progress }}%</strong> ukończono
      </span>
      <span
        v-if="estimatedTime !== null && estimatedTime > 0"
        class="analysis-progress__eta"
      >
        <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.5"/>
          <path d="M7 4v3.5l2.5 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        ok. {{ estimatedTime }} s pozostało
      </span>
      <span
        v-else-if="progress === 100"
        class="analysis-progress__eta analysis-progress__eta--done"
      >
        ✅ Gotowe — generowanie raportu…
      </span>
    </div>

    <!-- Lista kroków analizy -->
    <ol
      v-if="steps && steps.length > 0"
      class="analysis-progress__steps"
      aria-label="Kroki analizy"
    >
      <li
        v-for="step in steps"
        :key="step.id"
        class="analysis-progress__step-item"
        :class="{
          'analysis-progress__step-item--done':    step.status === 'done',
          'analysis-progress__step-item--active':  step.status === 'active',
          'analysis-progress__step-item--pending': step.status === 'pending'
        }"
        :aria-current="step.status === 'active' ? 'step' : undefined"
      >
        <!-- Ikona statusu -->
        <span class="analysis-progress__step-icon" aria-hidden="true">
          {{ step.status === 'done'   ? '✅'
           : step.status === 'active' ? '⏳'
           : '○'
          }}
        </span>
        <!-- Etykieta kroku + czas trwania (opcjonalny) -->
        <span class="analysis-progress__step-label">{{ step.label }}</span>
        <span
          v-if="step.duration !== undefined"
          class="analysis-progress__step-duration"
          aria-label="`Czas: ${step.duration} ms`"
        >
          {{ step.duration }} ms
        </span>
      </li>
    </ol>

    <!-- Przycisk Anuluj -->
    <div class="analysis-progress__footer">
      <button
        type="button"
        class="analysis-progress__cancel"
        :aria-label="`Anuluj analizę pliku ${filename || ''}`"
        @click="emit('cancel')"
      >
        <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Anuluj analizę
      </button>
    </div>

  </div>
</template>

<script setup>
/**
 * AnalysisProgress.vue
 *
 * Wskaźnik postępu analizy WCAG. Używany w AnalysisView.vue.
 *
 * Props:
 *   progress      — 0..100, aktualny procent ukończenia
 *   currentStep   — opis aktualnie wykonywanego kroku (tekst)
 *   estimatedTime — szacowany czas pozostały w sekundach (null = nieznany)
 *   steps         — lista kroków [{ id, label, status: 'pending'|'active'|'done', duration? }]
 *   filename      — nazwa analizowanego pliku (dla aria-label)
 *
 * Emits:
 *   cancel — użytkownik kliknął "Anuluj analizę"
 */
defineProps({
  /** Procent ukończenia (0–100) */
  progress: {
    type: Number,
    default: 0,
    validator: (v) => v >= 0 && v <= 100
  },

  /** Opis bieżącego kroku — ogłaszany przez aria-live="polite" */
  currentStep: {
    type: String,
    default: 'Uruchamianie analizy…'
  },

  /**
   * Szacowany czas pozostały w sekundach.
   * null = nie wiadomo (nie wyświetla sekcji ETA)
   */
  estimatedTime: {
    type: Number,
    default: null
  },

  /**
   * Lista kroków analizy.
   * Każdy krok: { id: String, label: String, status: 'pending'|'active'|'done', duration?: Number }
   */
  steps: {
    type: Array,
    default: () => []
  },

  /** Nazwa pliku — używana w aria-label przycisku Anuluj */
  filename: {
    type: String,
    default: null
  }
})

const emit = defineEmits([
  /** Emitowany gdy użytkownik klika "Anuluj analizę" */
  'cancel'
])
</script>

<style scoped>
/* ============================================================
   KONTENER
============================================================ */

.analysis-progress {
  padding: var(--spacing-xl);
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* ============================================================
   NAGŁÓWEK
============================================================ */

.analysis-progress__header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.analysis-progress__title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
}

.analysis-progress__step {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
  min-height: 1.4em; /* Zapobiega skokowi layoutu gdy tekst się zmienia */
}

/* ============================================================
   PROGRESS BAR
   WCAG 4.1.2: role="progressbar", aria-valuenow, aria-valuemin, aria-valuemax
============================================================ */

.analysis-progress__bar-wrapper {
  /* Wrapper — etykiety powyżej/poniżej jeśli potrzeba */
}

.analysis-progress__bar {
  width: 100%;
  height: 10px;
  background-color: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.analysis-progress__bar-fill {
  height: 100%;
  background-color: var(--color-primary);
  border-radius: inherit;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: width;
}

/* ============================================================
   SZCZEGÓŁY — % i ETA
============================================================ */

.analysis-progress__details {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.analysis-progress__percent {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.analysis-progress__percent strong {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.analysis-progress__eta {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
}

.analysis-progress__eta--done {
  color: var(--color-success);
  font-family: var(--font-family-base);
}

/* ============================================================
   LISTA KROKÓW
============================================================ */

.analysis-progress__steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;

  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm);
}

.analysis-progress__step-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  transition: background-color var(--transition-fast);
}

.analysis-progress__step-item--done {
  color: var(--color-success);
}

.analysis-progress__step-item--active {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
}

.analysis-progress__step-item--pending {
  color: var(--color-text-disabled);
}

.analysis-progress__step-icon {
  flex-shrink: 0;
  width: 1.4em;
  text-align: center;
  font-size: 0.9em;
}

.analysis-progress__step-label {
  flex: 1;
}

.analysis-progress__step-duration {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-xs);
  color: var(--color-text-disabled);
  flex-shrink: 0;
}

/* ============================================================
   PRZYCISK ANULUJ
   Touch target: min 44x44px — WCAG 2.5.5 (AAA zalecane)
   Focus visible — WCAG 2.4.7
============================================================ */

.analysis-progress__footer {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--spacing-xs);
  border-top: 1px solid var(--color-border-light);
}

.analysis-progress__cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);

  /* Touch target — min 44px wysokości */
  min-height: 44px;
  padding: var(--spacing-sm) var(--spacing-lg);

  background-color: transparent;
  border: 2px solid var(--color-error);
  border-radius: var(--radius-md);
  color: var(--color-error);
  cursor: pointer;

  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);

  transition:
    background-color var(--transition-fast),
    color            var(--transition-fast);
}

.analysis-progress__cancel:hover {
  background-color: var(--color-error);
  color: var(--color-text-inverse);
}

/* Focus visible — WCAG 2.4.7 */
.analysis-progress__cancel:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

/* ============================================================
   RESPONSYWNOŚĆ
============================================================ */

@media (max-width: 480px) {
  .analysis-progress {
    padding: var(--spacing-md);
  }

  .analysis-progress__details {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }

  .analysis-progress__footer {
    justify-content: stretch;
  }

  .analysis-progress__cancel {
    width: 100%;
    justify-content: center;
  }
}

/* ============================================================
   PREFERS-REDUCED-MOTION
============================================================ */

@media (prefers-reduced-motion: reduce) {
  .analysis-progress__bar-fill,
  .analysis-progress__step-item {
    transition: none;
  }
}
</style>
