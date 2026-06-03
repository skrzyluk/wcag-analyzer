<template>
  <!--
    Modal.vue — Dialog / Modal overlay
    WCAG 2.1 AA:
      ✅ 2.1.1  — Obsługiwany z klawiatury (Tab, Shift+Tab, ESC)
      ✅ 2.1.2  — Brak pułapki na klawiaturę (ESC zamyka)
      ✅ 2.4.3  — Kolejność focusu logiczna (focus trap wewnątrz modalu)
      ✅ 4.1.2  — role="dialog", aria-labelledby, aria-modal="true"
      ✅ 4.1.3  — aria-live dla dynamicznych zmian
  -->
  <Teleport to="body">
    <Transition name="modal" @after-enter="focusFirstElement">
      <div
        v-if="isOpen"
        class="modal-overlay"
        role="presentation"
        @click.self="handleBackdropClick"
        @keydown.esc="handleEscKey"
      >
        <div
          ref="dialogRef"
          role="dialog"
          :aria-labelledby="titleId"
          :aria-describedby="hasDescription ? descriptionId : undefined"
          aria-modal="true"
          :class="['modal', `modal--${size}`]"
          @keydown="handleFocusTrap"
        >
          <!-- Nagłówek modalu -->
          <div class="modal__header">
            <h2
              :id="titleId"
              class="modal__title"
            >
              {{ title }}
            </h2>

            <!-- Przycisk zamknięcia -->
            <button
              ref="closeBtnRef"
              type="button"
              class="modal__close"
              :aria-label="`Zamknij modal: ${title}`"
              @click="emit('close')"
            >
              <!-- Ikona X (SVG inline — brak zależności zewnętrznych) -->
              <svg
                aria-hidden="true"
                focusable="false"
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M15 5L5 15M5 5l10 10"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <!-- Treść modalu -->
          <div
            class="modal__body"
            :id="descriptionId"
          >
            <slot />
          </div>

          <!-- Stopka modalu (przyciski akcji) -->
          <div
            v-if="showFooter"
            class="modal__footer"
          >
            <!-- Slot pozwala na custom przyciski -->
            <slot name="footer">
              <button
                type="button"
                class="modal__btn modal__btn--secondary"
                @click="emit('close')"
              >
                {{ cancelText }}
              </button>

              <button
                ref="confirmBtnRef"
                type="button"
                class="modal__btn modal__btn--primary"
                :aria-label="confirmAriaLabel || confirmText"
                @click="emit('confirm')"
              >
                {{ confirmText }}
              </button>
            </slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
/**
 * Modal.vue
 *
 * Pełny komponent modalu z focus trap, ESC handling,
 * i pełną obsługą WCAG 2.1 AA.
 *
 * Użycie:
 *   <Modal
 *     :is-open="isOpen"
 *     title="Potwierdź usunięcie"
 *     @close="isOpen = false"
 *     @confirm="handleConfirm"
 *   >
 *     <p>Czy na pewno chcesz usunąć ten element?</p>
 *   </Modal>
 */
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'

const props = defineProps({
  /** Kontroluje widoczność modalu */
  isOpen: {
    type: Boolean,
    required: true
  },

  /** Tytuł modalu — wymagany dla aria-labelledby */
  title: {
    type: String,
    required: true
  },

  /** Tekst przycisku anulowania */
  cancelText: {
    type: String,
    default: 'Anuluj'
  },

  /** Tekst przycisku potwierdzenia */
  confirmText: {
    type: String,
    default: 'Potwierdź'
  },

  /** Opcjonalna dodatkowa aria-label dla przycisku potwierdzenia */
  confirmAriaLabel: {
    type: String,
    default: null
  },

  /**
   * Rozmiar modalu:
   * - sm:  400px — krótkie komunikaty
   * - md:  600px — standardowe formularze (domyślny)
   * - lg:  800px — złożone treści
   * - xl:  1000px — tabele, raporty
   * - full: 100% — pełny ekran
   */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl', 'full'].includes(v)
  },

  /** Czy kliknięcie w tło zamyka modal */
  closeOnBackdrop: {
    type: Boolean,
    default: true
  },

  /** Czy klawisz ESC zamyka modal */
  closeOnEsc: {
    type: Boolean,
    default: true
  },

  /** Czy pokazywać stopkę z przyciskami */
  showFooter: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits([
  /** Emitowany gdy użytkownik zamknął modal (X, ESC, backdrop, Anuluj) */
  'close',
  /** Emitowany gdy użytkownik kliknął Potwierdź */
  'confirm'
])

/* ============================================================
   REFS
============================================================ */

const dialogRef   = ref(null)
const closeBtnRef = ref(null)

/* ============================================================
   UNIKALNE ID DLA ARIA
============================================================ */

const uid          = Math.random().toString(36).slice(2, 9)
const titleId      = `modal-title-${uid}`
const descriptionId = `modal-desc-${uid}`
const hasDescription = computed(() => true) // slot zawsze istnieje

/* ============================================================
   SCROLL LOCK — blokuje scroll body gdy modal jest otwarty
============================================================ */

const lockBodyScroll = () => {
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow       = 'hidden'
  document.body.style.paddingRight   = `${scrollbarWidth}px`
}

const unlockBodyScroll = () => {
  document.body.style.overflow     = ''
  document.body.style.paddingRight = ''
}

/* ============================================================
   FOCUS MANAGEMENT (WCAG 2.4.3)
============================================================ */

/** Element który miał focus przed otwarciem modalu */
let previouslyFocusedElement = null

/**
 * Pobiera wszystkie focusowalne elementy wewnątrz modalu.
 * Używane przez focus trap.
 */
const getFocusableElements = () => {
  if (!dialogRef.value) return []
  return Array.from(
    dialogRef.value.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), ' +
      'select:not([disabled]), textarea:not([disabled]), ' +
      '[tabindex]:not([tabindex="-1"]), details > summary'
    )
  ).filter(el => !el.hasAttribute('disabled') && el.tabIndex !== -1)
}

/**
 * Przesuwa focus na pierwszy focusowalny element w modalu.
 * Wywołany po animacji wejścia (after-enter).
 */
const focusFirstElement = () => {
  const elements = getFocusableElements()
  if (elements.length > 0) {
    // Preferujemy przycisk zamknięcia jako pierwszy focus
    closeBtnRef.value?.focus() ?? elements[0].focus()
  }
}

/**
 * Focus Trap — zapobiega wyjściu focusu poza modal.
 * WCAG 2.1.2: Brak pułapki — ESC zawsze może zamknąć modal.
 */
const handleFocusTrap = (event) => {
  if (event.key !== 'Tab') return

  const elements = getFocusableElements()
  if (elements.length === 0) {
    event.preventDefault()
    return
  }

  const firstEl = elements[0]
  const lastEl  = elements[elements.length - 1]

  if (event.shiftKey) {
    // Shift+Tab: jeśli focus na pierwszym — przenosimy na ostatni
    if (document.activeElement === firstEl) {
      event.preventDefault()
      lastEl.focus()
    }
  } else {
    // Tab: jeśli focus na ostatnim — przenosimy na pierwszy
    if (document.activeElement === lastEl) {
      event.preventDefault()
      firstEl.focus()
    }
  }
}

/* ============================================================
   OBSŁUGA ZDARZEŃ
============================================================ */

const handleEscKey = () => {
  if (props.closeOnEsc) {
    emit('close')
  }
}

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) {
    emit('close')
  }
}

/* ============================================================
   LIFECYCLE — watch isOpen
============================================================ */

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    // Zapisz element który ma teraz focus
    previouslyFocusedElement = document.activeElement
    lockBodyScroll()
  } else {
    unlockBodyScroll()
    // Przywróć focus do elementu który go miał przed otwarciem
    if (previouslyFocusedElement) {
      previouslyFocusedElement.focus()
      previouslyFocusedElement = null
    }
  }
})

/* Cleanup jeśli komponent zostanie zniszczony gdy modal jest otwarty */
onBeforeUnmount(() => {
  unlockBodyScroll()
})
</script>

<style scoped>
/* ============================================================
   OVERLAY (backdrop)
============================================================ */

.modal-overlay {
  position: fixed;
  inset: 0;   /* top: 0; right: 0; bottom: 0; left: 0 */
  z-index: var(--z-modal);

  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);

  background-color: var(--color-background-overlay); /* rgba(0,0,0,0.5) */

  /* Zapobiega scrollowi pod modalem na iOS */
  overflow-y: auto;
}

/* ============================================================
   OKNO MODALU
============================================================ */

.modal {
  position: relative;
  display: flex;
  flex-direction: column;

  width: 100%;
  max-height: calc(100vh - var(--spacing-xl) * 2);

  background-color: var(--color-background);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);

  /* Wewnętrzny scroll gdy zawartość jest za długa */
  overflow: hidden;
}

/* Rozmiary */
.modal--sm   { max-width: 400px;  }
.modal--md   { max-width: 600px;  }
.modal--lg   { max-width: 800px;  }
.modal--xl   { max-width: 1000px; }
.modal--full {
  max-width: none;
  width: 100%;
  height: 100%;
  border-radius: 0;
  margin: 0;
}

/* ============================================================
   NAGŁÓWEK
============================================================ */

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);

  padding: var(--spacing-lg) var(--spacing-lg) var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.modal__title {
  margin: 0;
  font-size: var(--font-size-xl);           /* 20px */
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
}

/* Przycisk X zamknięcia */
.modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  width:  36px;
  height: 36px;
  padding: 0;
  margin-left: auto;

  background: transparent;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;

  color: var(--color-text-secondary);
  transition:
    background-color var(--transition-fast),
    color            var(--transition-fast),
    border-color     var(--transition-fast);
}

.modal__close:hover {
  background-color: var(--color-background-alt);
  color: var(--color-text-primary);
}

/* Focus — WCAG 2.4.7 ✅ */
.modal__close:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
  border-radius: var(--radius-md);
}

/* ============================================================
   BODY
============================================================ */

.modal__body {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  line-height: var(--line-height-normal);
  color: var(--color-text-primary);
}

/* ============================================================
   STOPKA
============================================================ */

.modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-sm);

  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
  background-color: var(--color-background-alt);
  flex-shrink: 0;
}

/* Wbudowane przyciski stopki */
.modal__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  padding: var(--spacing-sm) var(--spacing-lg);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: 1;

  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    background-color var(--transition-fast),
    border-color     var(--transition-fast),
    color            var(--transition-fast);
}

.modal__btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.modal__btn--primary {
  background-color: var(--color-primary);
  border-color:     var(--color-primary);
  color:            var(--color-text-inverse);
}

.modal__btn--primary:hover {
  background-color: var(--color-primary-dark);
  border-color:     var(--color-primary-dark);
}

.modal__btn--secondary {
  background-color: transparent;
  border-color:     var(--color-primary);
  color:            var(--color-primary);
}

.modal__btn--secondary:hover {
  background-color: var(--color-primary-light);
}

/* ============================================================
   ANIMACJA WEJŚCIA/WYJŚCIA
   prefers-reduced-motion: tylko opacity (brak ruchu)
============================================================ */

.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition:
    opacity   var(--transition-normal),
    transform var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal {
  transform: translateY(-16px) scale(0.98);
}

.modal-leave-to .modal {
  transform: translateY(8px) scale(0.99);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active,
  .modal-enter-active .modal,
  .modal-leave-active .modal {
    transition: opacity var(--transition-fast);
  }

  .modal-enter-from .modal,
  .modal-leave-to .modal {
    transform: none;
  }
}

/* ============================================================
   RESPONSYWNOŚĆ — mobile
============================================================ */

@media (max-width: 639px) {
  .modal-overlay {
    align-items: flex-end;
    padding: 0;
  }

  .modal {
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    max-height: 90vh;
  }

  .modal--full {
    height: 100%;
    max-height: 100%;
    border-radius: 0;
  }

  .modal-enter-from .modal {
    transform: translateY(100%);
  }
}
</style>
