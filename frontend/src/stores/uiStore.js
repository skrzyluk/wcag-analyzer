/**
 * uiStore.js — Pinia Store dla stanu UI
 * Projekt: WCAG 2.1 AA Analyzer
 *
 * Odpowiedzialności:
 *   - Toast notifications (sukces, błąd, info, ostrzeżenie)
 *   - Globalny overlay ładowania
 *   - Stan sidebaru (otwarty/zamknięty)
 *   - Aktywna zakładka / widok
 *   - Preferencje użytkownika (dark mode, język)
 */

import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'

// ── Stałe ─────────────────────────────────────────────────────────────────

const TOAST_DURATION_MS = 5000   // Domyślny czas wyświetlania toastu
const MAX_TOASTS        = 5      // Maks. jednoczesnych toastów

let toastIdCounter = 0

// ── Store ─────────────────────────────────────────────────────────────────

export const useUiStore = defineStore('ui', () => {

  // ────────────────────────────────────────────────────────────────────────
  // STATE
  // ────────────────────────────────────────────────────────────────────────

  /** Lista aktywnych powiadomień toast */
  const toasts = ref([])

  /** Czy sidebar jest otwarty (na mobilnych — hamburger menu) */
  const sidebarOpen = ref(false)

  /** Globalny overlay ładowania (np. podczas inicjalizacji) */
  const globalLoading = ref(false)
  const globalLoadingMessage = ref('')

  /** Aktualnie aktywny widok / route name (dla nawigacji) */
  const activeView = ref('home')

  /** Dark mode */
  const darkMode = ref(
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false
  )

  /** Preferencje dostępności użytkownika */
  const reduceMotion = ref(
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false
  )

  // ────────────────────────────────────────────────────────────────────────
  // GETTERS
  // ────────────────────────────────────────────────────────────────────────

  const hasToasts      = computed(() => toasts.value.length > 0)
  const isSidebarOpen  = computed(() => sidebarOpen.value)
  const isGlobalLoading = computed(() => globalLoading.value)

  // ────────────────────────────────────────────────────────────────────────
  // TOAST ACTIONS
  // ────────────────────────────────────────────────────────────────────────

  /**
   * Wyświetl powiadomienie toast.
   *
   * @param {object} options
   * @param {'success'|'error'|'warning'|'info'} options.type
   * @param {string}  options.message   - Treść powiadomienia (wymagane)
   * @param {string}  [options.title]   - Opcjonalny tytuł
   * @param {number}  [options.duration] - Czas w ms (0 = nie znika)
   * @param {boolean} [options.closable] - Czy można zamknąć ręcznie
   * @returns {number} ID toastu (do późniejszego zamknięcia)
   */
  const showToast = ({ type = 'info', message, title = null, duration = TOAST_DURATION_MS, closable = true }) => {
    const id = ++toastIdCounter

    // Ogranicz liczbę jednoczesnych toastów
    if (toasts.value.length >= MAX_TOASTS) {
      toasts.value.shift()
    }

    toasts.value.push({ id, type, message, title, closable })

    // Auto-close po duration ms (0 = bez auto-close)
    if (duration > 0) {
      setTimeout(() => closeToast(id), duration)
    }

    return id
  }

  /** Skróty dla poszczególnych typów */
  const success = (message, options = {}) =>
    showToast({ type: 'success', message, ...options })

  const error = (message, options = {}) =>
    showToast({ type: 'error', message, duration: 8000, ...options })

  const warning = (message, options = {}) =>
    showToast({ type: 'warning', message, ...options })

  const info = (message, options = {}) =>
    showToast({ type: 'info', message, ...options })

  /** Zamknij konkretny toast */
  const closeToast = (id) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  /** Zamknij wszystkie toasty */
  const clearToasts = () => {
    toasts.value = []
  }

  // ────────────────────────────────────────────────────────────────────────
  // SIDEBAR ACTIONS
  // ────────────────────────────────────────────────────────────────────────

  const openSidebar  = () => { sidebarOpen.value = true }
  const closeSidebar = () => { sidebarOpen.value = false }
  const toggleSidebar = () => { sidebarOpen.value = !sidebarOpen.value }

  // ────────────────────────────────────────────────────────────────────────
  // GLOBAL LOADING
  // ────────────────────────────────────────────────────────────────────────

  const showGlobalLoading = (message = 'Ładowanie...') => {
    globalLoading.value        = true
    globalLoadingMessage.value = message
  }

  const hideGlobalLoading = () => {
    globalLoading.value        = false
    globalLoadingMessage.value = ''
  }

  // ────────────────────────────────────────────────────────────────────────
  // DARK MODE
  // ────────────────────────────────────────────────────────────────────────

  const toggleDarkMode = () => {
    darkMode.value = !darkMode.value
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute(
        'data-theme',
        darkMode.value ? 'dark' : 'light'
      )
    }
  }

  // ────────────────────────────────────────────────────────────────────────
  // RETURN
  // ────────────────────────────────────────────────────────────────────────

  return {
    // State (readonly)
    toasts:               readonly(toasts),
    sidebarOpen:          readonly(sidebarOpen),
    globalLoading:        readonly(globalLoading),
    globalLoadingMessage: readonly(globalLoadingMessage),
    activeView:           readonly(activeView),
    darkMode:             readonly(darkMode),
    reduceMotion:         readonly(reduceMotion),

    // Getters
    hasToasts,
    isSidebarOpen,
    isGlobalLoading,

    // Toast actions
    showToast, success, error, warning, info,
    closeToast, clearToasts,

    // Sidebar
    openSidebar, closeSidebar, toggleSidebar,

    // Loading
    showGlobalLoading, hideGlobalLoading,

    // Dark mode
    toggleDarkMode,
  }
})
