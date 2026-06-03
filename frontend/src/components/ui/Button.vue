<template>
  <!--
    Button.vue — Bazowy komponent przycisku
    WCAG 2.1 AA:
      ✅ 1.4.3  — Kontrast tekstu >= 4.5:1
      ✅ 2.1.1  — Dostępny z klawiatury (natywny <button>)
      ✅ 2.4.7  — Focus visible (outline 3px)
      ✅ 4.1.2  — aria-label gdy brak widocznego tekstu
  -->
  <!-- type="button" jest domyślny (prop type default: 'button') -->
  <button
    :type="type"
    :class="[
      'btn',
      `btn--${variant}`,
      size !== 'md' && `btn--${size}`,
      { 'btn--icon-only': iconOnly }
    ]"
    :disabled="disabled"
    :aria-label="ariaLabel || undefined"
    :aria-disabled="disabled ? 'true' : undefined"
    :aria-busy="loading ? 'true' : undefined"
    v-bind="$attrs"
  >
    <!-- Spinner podczas ładowania -->
    <span
      v-if="loading"
      class="btn__spinner"
      aria-hidden="true"
    />

    <!-- Ikona wiodąca (opcjonalna) -->
    <span
      v-if="$slots['icon-start'] && !loading"
      class="btn__icon btn__icon--start"
      aria-hidden="true"
    >
      <slot name="icon-start" />
    </span>

    <!-- Treść przycisku -->
    <span class="btn__label">
      <slot>{{ label }}</slot>
    </span>

    <!-- Ikona kończąca (opcjonalna) -->
    <span
      v-if="$slots['icon-end']"
      class="btn__icon btn__icon--end"
      aria-hidden="true"
    >
      <slot name="icon-end" />
    </span>

    <!-- Ukryty tekst ładowania dla screen readerów -->
    <span
      v-if="loading"
      class="visually-hidden"
      role="status"
      aria-live="polite"
    >
      Ładowanie…
    </span>
  </button>
</template>

<script setup>
/**
 * Button.vue
 *
 * Bazowy komponent przycisku. Używany w całej aplikacji.
 * Nigdy nie zastępuj go <div @click> — zachowaj semantykę.
 */

defineOptions({ inheritAttrs: false })

const props = defineProps({
  /**
   * Wariant wizualny przycisku.
   * - primary:   Główna akcja (niebieski)
   * - secondary: Drugorzędna akcja (szary obrys)
   * - danger:    Destrukcyjna akcja (czerwony)
   * - ghost:     Subtelny (tylko tekst z hover)
   * - link:      Wygląda jak link
   */
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'danger', 'ghost', 'link'].includes(v)
  },

  /** Rozmiar przycisku */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },

  /** Typ HTML atrybutu — zawsze podawaj explicite */
  type: {
    type: String,
    default: 'button',
    validator: (v) => ['button', 'submit', 'reset'].includes(v)
  },

  /** Wyłącza przycisk (niedostępny, wyszarzony) */
  disabled: {
    type: Boolean,
    default: false
  },

  /**
   * Etykieta ARIA — wymagana gdy slot nie zawiera tekstu.
   * Np. przyciski z samą ikoną: <Button aria-label="Zamknij">✕</Button>
   */
  ariaLabel: {
    type: String,
    default: null
  },

  /** Fallback tekst gdy slot jest pusty */
  label: {
    type: String,
    default: ''
  },

  /** Stan ładowania — blokuje kliknięcia i pokazuje spinner */
  loading: {
    type: Boolean,
    default: false
  },

  /** Przycisk zawiera wyłącznie ikonę (kwadratowy padding) */
  iconOnly: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
/* ============================================================
   BAZOWE STYLE PRZYCISKU
============================================================ */

.btn {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);

  /* Typografia */
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  white-space: nowrap;
  text-decoration: none;

  /* Padding domyślny (md) */
  padding: var(--spacing-sm) var(--spacing-md);

  /* Wygląd */
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  user-select: none;

  /* Przejście — respektujemy prefers-reduced-motion */
  transition:
    background-color var(--transition-fast),
    border-color     var(--transition-fast),
    color            var(--transition-fast),
    opacity          var(--transition-fast),
    transform        var(--transition-fast),
    box-shadow       var(--transition-fast);

  /* Zapobiegamy "podwójnemu" focusowi gdy button jest w <a> */
  position: relative;
}

/* ============================================================
   FOCUS (WCAG 2.4.7 — Focus Visible)
   outline musi mieć kontrast >= 3:1 względem tła.
   primary outline: #0066cc = 5.57:1 na białym ✅
============================================================ */

.btn:focus-visible {
  outline: var(--focus-outline);         /* 3px solid #0066cc */
  outline-offset: var(--focus-outline-offset); /* 2px */
}

/* ============================================================
   WARIANTY
============================================================ */

/* --- Primary (główna akcja) --- */
.btn--primary {
  background-color: var(--color-primary);
  border-color:     var(--color-primary);
  color:            var(--color-text-inverse);
}

.btn--primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  border-color:     var(--color-primary-dark);
}

.btn--primary:active:not(:disabled) {
  transform: scale(var(--active-scale));
  background-color: var(--color-primary-dark);
}

/* --- Secondary (drugorzędna akcja) --- */
.btn--secondary {
  background-color: transparent;
  border-color:     var(--color-primary);
  color:            var(--color-primary);
}

.btn--secondary:hover:not(:disabled) {
  background-color: var(--color-primary-light);
}

.btn--secondary:active:not(:disabled) {
  transform: scale(var(--active-scale));
  background-color: var(--color-primary-light);
}

/* --- Danger (destrukcyjna akcja) --- */
.btn--danger {
  background-color: var(--color-error);
  border-color:     var(--color-error);
  color:            var(--color-text-inverse);
}

.btn--danger:hover:not(:disabled) {
  /* Przyciemniamy o ~15% — #a30000 */
  background-color: #a30000;
  border-color:     #a30000;
}

.btn--danger:active:not(:disabled) {
  transform: scale(var(--active-scale));
}

.btn--danger:focus-visible {
  outline-color: var(--color-error);
}

/* --- Ghost (subtelny) --- */
.btn--ghost {
  background-color: transparent;
  border-color:     transparent;
  color:            var(--color-text-primary);
}

.btn--ghost:hover:not(:disabled) {
  background-color: var(--color-background-alt);
}

/* --- Link (wygląda jak <a>) --- */
.btn--link {
  background-color: transparent;
  border-color:     transparent;
  color:            var(--color-primary);
  padding-inline:   var(--spacing-xs);
  text-decoration:  underline;
  text-underline-offset: 3px;
}

.btn--link:hover:not(:disabled) {
  color: var(--color-primary-dark);
}

/* ============================================================
   ROZMIARY
============================================================ */

.btn--sm {
  font-size: var(--font-size-sm);
  padding:   var(--spacing-xs) var(--spacing-sm);
  gap:       calc(var(--spacing-xs) / 2);
}

.btn--lg {
  font-size: var(--font-size-lg);
  padding:   var(--spacing-md) var(--spacing-xl);
}

/* Kwadratowy padding dla przycisków z samą ikoną */
.btn--icon-only {
  padding: var(--spacing-sm);
  aspect-ratio: 1;
}

/* ============================================================
   STAN DISABLED
   WCAG: nie używaj pointer-events:none — to ukrywa cursor feedback
============================================================ */

.btn:disabled,
.btn[aria-disabled="true"] {
  opacity: var(--disabled-opacity);
  cursor:  var(--disabled-cursor);
}

/* ============================================================
   STAN LOADING
============================================================ */

.btn[aria-busy="true"] {
  cursor: wait;
  pointer-events: none; /* OK tu — stan tymczasowy, nie trwałe ukrycie */
}

/* ============================================================
   SPINNER
============================================================ */

.btn__spinner {
  display: block;
  width:  1em;
  height: 1em;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: btn-spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes btn-spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .btn__spinner {
    animation: none;
    border-top-color: currentColor;
    opacity: 0.6;
  }
}

/* ============================================================
   IKONY
============================================================ */

.btn__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 1em;
  height: 1em;
}

/* Ukryty tekst (screen reader) */
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
</style>
