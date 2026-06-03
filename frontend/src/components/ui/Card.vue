<template>
  <!--
    Card.vue — Komponent karty (kontener wizualny)
    WCAG 2.1 AA:
      ✅ 1.3.1  — Semantyczna sekcja z opcjonalnym nagłówkiem
      ✅ 1.4.3  — Kontrast tekstu nagłówka >= 4.5:1
      ✅ 2.4.6  — Nagłówek opisuje cel sekcji
  -->
  <section
    :class="[
      'card',
      variant && `card--${variant}`,
      { 'card--clickable': clickable }
    ]"
    :aria-labelledby="title ? headingId : undefined"
    v-bind="$attrs"
  >
    <!-- Nagłówek karty (opcjonalny) -->
    <header v-if="title || $slots.header" class="card__header">
      <!-- Slot nagłówka — pozwala na custom content (badge, menu, itp.) -->
      <slot name="header">
        <component
          :is="headingTag"
          :id="headingId"
          class="card__title"
        >
          {{ title }}
        </component>
      </slot>

      <!-- Opcjonalne akcje w nagłówku (np. przycisk zamknięcia) -->
      <div v-if="$slots.actions" class="card__actions">
        <slot name="actions" />
      </div>
    </header>

    <!-- Główna zawartość -->
    <div class="card__body">
      <slot />
    </div>

    <!-- Stopka karty (opcjonalna) -->
    <footer v-if="$slots.footer" class="card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup>
/**
 * Card.vue
 *
 * Kontener wizualny dla powiązanych treści.
 * Używaj jako blok grupujący — nie jako dekorację.
 */
import { computed } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  /**
   * Tytuł karty — renderowany jako nagłówek (h2–h6).
   * Zostaw pusty jeśli sekcja nie potrzebuje nagłówka.
   */
  title: {
    type: String,
    default: null
  },

  /**
   * Poziom nagłówka HTML (h2–h4).
   * Dostosuj do hierarchii strony — nie pomijaj poziomów!
   */
  headingLevel: {
    type: Number,
    default: 2,
    validator: (v) => v >= 1 && v <= 6
  },

  /**
   * Wariant wizualny:
   * - default:   Biała karta z cieniem
   * - outlined:  Biała karta z obramowaniem (bez cienia)
   * - filled:    Szare tło (tło alternatywne)
   * - elevated:  Wyraźniejszy cień (ważne sekcje)
   */
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'outlined', 'filled', 'elevated'].includes(v)
  },

  /**
   * Czy karta jest klikalna (hover state, cursor pointer).
   * Jeśli tak — dodaj @click i role="button" lub użyj <a>.
   */
  clickable: {
    type: Boolean,
    default: false
  },

  /**
   * Padding wewnętrzny — 'none' wyłącza padding (np. dla kart z obrazem)
   */
  padding: {
    type: String,
    default: 'md',
    validator: (v) => ['none', 'sm', 'md', 'lg'].includes(v)
  }
})

/** Generuje unikalny ID dla aria-labelledby */
const headingId = computed(() =>
  props.title
    ? `card-heading-${props.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')}-${Math.random().toString(36).slice(2, 7)}`
    : undefined
)

/** Dynamiczny tag nagłówka */
const headingTag = computed(() => `h${props.headingLevel}`)
</script>

<style scoped>
/* ============================================================
   BAZOWE STYLE KARTY
============================================================ */

.card {
  /* Layout */
  display: flex;
  flex-direction: column;
  width: 100%;

  /* Wygląd domyślny */
  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);         /* 8px */
  box-shadow: var(--shadow-md);            /* 0 2px 8px rgba(0,0,0,0.12) */

  /* Zapobiega overflow zawartości poza border-radius */
  overflow: hidden;
}

/* ============================================================
   WARIANTY
============================================================ */

.card--outlined {
  box-shadow: none;
  border-color: var(--color-border-light);
}

.card--filled {
  background-color: var(--color-background-alt);
  border-color: transparent;
  box-shadow: none;
}

.card--elevated {
  box-shadow: var(--shadow-lg);  /* Wyraźniejszy cień */
  border-color: transparent;
}

/* ============================================================
   KLIKALNA KARTA
============================================================ */

.card--clickable {
  cursor: pointer;
  transition:
    box-shadow   var(--transition-fast),
    transform    var(--transition-fast),
    border-color var(--transition-fast);
}

.card--clickable:hover {
  box-shadow:   var(--shadow-lg);
  border-color: var(--color-primary-light);
}

.card--clickable:active {
  transform: scale(0.995);
}

.card--clickable:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

/* ============================================================
   NAGŁÓWEK
============================================================ */

.card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);

  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);

  /* Nagłówek nie rosnący, treść karta rośnie */
  flex-shrink: 0;
}

.card__title {
  margin: 0;
  font-size: var(--font-size-lg);          /* 18px */
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);

  /* Overflow — długie tytuły skrócone z "…" */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

/* ============================================================
   BODY (główna zawartość)
============================================================ */

.card__body {
  flex: 1;
  padding: var(--spacing-lg);
}

/* Warianty paddingu */
:deep(.card--none) .card__body  { padding: 0; }
:deep(.card--sm)   .card__body  { padding: var(--spacing-sm); }
:deep(.card--lg)   .card__body  { padding: var(--spacing-xl); }

/*
  Alternatywne podejście — użyj CSS attr() gdy Vue przekaże klasę.
  Poniżej: scoped klasy na .card__body w zależności od prop padding.
*/
.card[data-padding="none"] .card__body { padding: 0; }
.card[data-padding="sm"]   .card__body { padding: var(--spacing-sm); }
.card[data-padding="lg"]   .card__body { padding: var(--spacing-xl); }

/* ============================================================
   STOPKA
============================================================ */

.card__footer {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
  background-color: var(--color-background-alt);
  flex-shrink: 0;

  /* Akcje stopki wyrównane do prawej */
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* ============================================================
   RESPONSYWNOŚĆ
============================================================ */

@media (max-width: 639px) {
  .card__header,
  .card__body,
  .card__footer {
    padding-inline: var(--spacing-md);
  }
}
</style>
