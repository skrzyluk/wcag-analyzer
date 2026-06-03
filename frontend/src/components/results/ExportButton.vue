<template>
  <!--
    ExportButton.vue — Dropdown menu eksportu raportu
    WCAG 2.1 AA:
      ✅ 1.4.3  — Kontrast tekstu >= 4.5:1 (tokeny CSS)
      ✅ 2.1.1  — Pełna obsługa klawiatury (Strzałki, ESC, Tab, Home/End)
      ✅ 2.4.7  — Focus visible na wszystkich elementach
      ✅ 4.1.2  — aria-haspopup="menu", aria-expanded, role="menu"/role="menuitem"
      ✅ 4.1.3  — aria-live="polite" dla statusu eksportu
  -->
  <div
    class="export-btn"
    ref="containerRef"
    @keydown.esc="closeMenu"
  >

    <!-- Przycisk główny — otwiera/zamyka menu -->
    <button
      ref="triggerRef"
      type="button"
      class="export-btn__trigger"
      :aria-expanded="isOpen ? 'true' : 'false'"
      aria-haspopup="menu"
      :aria-controls="menuId"
      :aria-label="`Eksportuj raport${filename ? ' — ' + filename : ''}`"
      :aria-busy="isExporting ? 'true' : undefined"
      :disabled="disabled"
      @click="toggleMenu"
    >
      <!-- Ikona eksportu -->
      <svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 1v9M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M1 12v2a1 1 0 001 1h12a1 1 0 001-1v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>

      <span>{{ isExporting ? 'Eksportowanie…' : 'Eksportuj' }}</span>

      <!-- Strzałka dropdown -->
      <svg
        class="export-btn__arrow"
        :class="{ 'export-btn__arrow--open': isOpen }"
        aria-hidden="true"
        focusable="false"
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="none"
      >
        <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <!-- Menu eksportu — otwierane przyciskiem -->
    <Transition name="menu-fade">
      <ul
        v-if="isOpen"
        :id="menuId"
        ref="menuRef"
        role="menu"
        class="export-btn__menu"
        :aria-label="`Formaty eksportu dla ${filename || 'raportu'}`"
        @keydown="handleMenuKeydown"
      >
        <li
          v-for="(option, index) in exportOptions"
          :key="option.format"
          role="none"
        >
          <button
            type="button"
            role="menuitem"
            class="export-btn__menu-item"
            :class="{ 'export-btn__menu-item--active': focusedIndex === index }"
            :disabled="isExporting"
            :aria-disabled="isExporting ? 'true' : undefined"
            :aria-label="`Eksportuj jako ${option.label}${option.desc ? ' — ' + option.desc : ''}`"
            :ref="el => { if (el) menuItemRefs[index] = el }"
            @click="handleExport(option.format)"
            @focus="focusedIndex = index"
          >
            <!-- Ikona formatu -->
            <span class="export-btn__menu-icon" aria-hidden="true">{{ option.icon }}</span>
            <span class="export-btn__menu-label">{{ option.label }}</span>
            <span
              v-if="option.desc"
              class="export-btn__menu-desc"
            >{{ option.desc }}</span>
          </button>
        </li>
      </ul>
    </Transition>

    <!-- Status eksportu — ogłaszany przez screen reader -->
    <div
      v-if="status"
      class="export-btn__status"
      :class="{
        'export-btn__status--success': statusType === 'success',
        'export-btn__status--error':   statusType === 'error'
      }"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      {{ status }}
    </div>

  </div>
</template>

<script setup>
/**
 * ExportButton.vue
 *
 * Dropdown menu do eksportu raportu WCAG w formatach HTML, PDF, JSON.
 * Integruje się z analysisService.exportReport() z api.js.
 *
 * Props:
 *   analysisId — ID analizy z backend API
 *   filename   — Nazwa pliku do pobrania (bez rozszerzenia)
 *   disabled   — Blokuje przycisk (np. gdy analiza nie jest gotowa)
 *
 * Emits:
 *   export-start(format)   — tuż przed wysłaniem żądania
 *   export-success(format) — po udanym pobraniu
 *   export-error(format, error) — po błędzie
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { analysisService } from '@/services/api'

/* ============================================================
   PROPS & EMITS
============================================================ */

const props = defineProps({
  analysisId: {
    type: String,
    required: true
  },
  filename: {
    type: String,
    default: 'raport-wcag'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['export-start', 'export-success', 'export-error'])

/* ============================================================
   STAŁE — opcje menu
============================================================ */

const exportOptions = [
  {
    format: 'html',
    icon:   '📄',
    label:  'HTML',
    desc:   'Interaktywny raport'
  },
  {
    format: 'pdf',
    icon:   '📕',
    label:  'PDF',
    desc:   'Do druku i archiwizacji'
  },
  {
    format: 'json',
    icon:   '🔧',
    label:  'JSON',
    desc:   'Surowe dane do integracji'
  }
]

/* ============================================================
   UID — unikalny ID dla aria-controls
============================================================ */

const uid    = Math.random().toString(36).slice(2, 8)
const menuId = `export-menu-${uid}`

/* ============================================================
   STATE
============================================================ */

const isOpen      = ref(false)
const isExporting = ref(false)
const status      = ref('')
const statusType  = ref('neutral') // 'success' | 'error' | 'neutral'
const focusedIndex = ref(-1)

/* ============================================================
   REFS
============================================================ */

const containerRef  = ref(null)
const triggerRef    = ref(null)
const menuRef       = ref(null)
const menuItemRefs  = ref([])

/* ============================================================
   MENU — otwieranie / zamykanie
============================================================ */

const openMenu = () => {
  isOpen.value      = true
  focusedIndex.value = 0
  // Przesuń focus na pierwszy element menu po wyrenderowaniu
  setTimeout(() => {
    menuItemRefs.value[0]?.focus()
  }, 50)
}

const closeMenu = () => {
  isOpen.value       = false
  focusedIndex.value = -1
  // Przywróć focus na przycisk triggera
  triggerRef.value?.focus()
}

const toggleMenu = () => {
  if (isOpen.value) {
    closeMenu()
  } else {
    openMenu()
  }
}

/* ============================================================
   KEYBOARD NAVIGATION — WCAG 2.1.1
   Implementacja wzorca ARIA "Menu Button" z W3C APG
   https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/
============================================================ */

const handleMenuKeydown = (event) => {
  const items  = menuItemRefs.value.filter(Boolean)
  const count  = items.length
  const current = focusedIndex.value

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      focusedIndex.value = (current + 1) % count
      items[focusedIndex.value]?.focus()
      break

    case 'ArrowUp':
      event.preventDefault()
      focusedIndex.value = (current - 1 + count) % count
      items[focusedIndex.value]?.focus()
      break

    case 'Home':
      event.preventDefault()
      focusedIndex.value = 0
      items[0]?.focus()
      break

    case 'End':
      event.preventDefault()
      focusedIndex.value = count - 1
      items[count - 1]?.focus()
      break

    case 'Tab':
      // Tab zamyka menu i pozwala na normalną nawigację
      closeMenu()
      break

    // ESC obsługuje @keydown.esc na kontenerze
  }
}

/* ============================================================
   CLICK POZA KOMPONENTEM — zamknij menu
============================================================ */

const handleClickOutside = (event) => {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    closeMenu()
    isOpen.value = false // bez przywracania focusu — kliknięto poza
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})

/* ============================================================
   EKSPORT
============================================================ */

/**
 * Pobiera plik eksportowanego raportu z backend API.
 * Używa analysisService.exportReport() który zwraca Blob.
 */
const handleExport = async (format) => {
  if (isExporting.value) return
  closeMenu()

  isExporting.value = true
  status.value      = `Eksportowanie jako ${format.toUpperCase()}…`
  statusType.value  = 'neutral'

  emit('export-start', format)

  try {
    // analysisService.exportReport() zwraca { blob, filename } lub inicjuje download
    await analysisService.exportReport(props.analysisId, format)

    status.value     = `✅ Pobrano raport ${format.toUpperCase()}`
    statusType.value = 'success'
    emit('export-success', format)
  } catch (err) {
    const msg = err?.summary ?? err?.message ?? 'Nieznany błąd eksportu'
    status.value     = `❌ Błąd: ${msg}`
    statusType.value = 'error'
    emit('export-error', format, err)
  } finally {
    isExporting.value = false
    // Wyczyść status po 5 sekundach
    setTimeout(() => {
      status.value     = ''
      statusType.value = 'neutral'
    }, 5000)
  }
}
</script>

<style scoped>
/* ============================================================
   KONTENER — pozycja względna dla dropdown
============================================================ */

.export-btn {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

/* ============================================================
   PRZYCISK GŁÓWNY
   Kontrast: biały (#fff) na primary (#0066cc) = 5.57:1 ✅
============================================================ */

.export-btn__trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);

  /* Touch target: min 44px */
  min-height: 44px;
  padding: var(--spacing-sm) var(--spacing-lg);

  background-color: var(--color-primary);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);

  color: var(--color-text-inverse);
  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  white-space: nowrap;

  transition:
    background-color var(--transition-fast),
    border-color     var(--transition-fast);
}

.export-btn__trigger:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  border-color:     var(--color-primary-dark);
}

.export-btn__trigger:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.export-btn__trigger:disabled {
  opacity: var(--disabled-opacity);
  cursor:  var(--disabled-cursor);
}

.export-btn__trigger[aria-busy="true"] {
  cursor: wait;
}

/* Strzałka — obraca się gdy menu otwarte */
.export-btn__arrow {
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.export-btn__arrow--open {
  transform: rotate(180deg);
}

/* ============================================================
   MENU DROPDOWN
   role="menu" — wzorzec z W3C APG Menu Button
============================================================ */

.export-btn__menu {
  position: absolute;
  top: calc(100% + var(--spacing-xs));
  left: 0;
  z-index: var(--z-dropdown);

  list-style: none;
  margin: 0;
  padding: var(--spacing-xs) 0;

  min-width: 200px;
  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);

  /* Zapobiegamy ucięciu focusu */
  overflow: visible;
}

/* ============================================================
   OPCJE MENU — role="menuitem"
============================================================ */

.export-btn__menu-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;

  /* Touch target: min 44px */
  min-height: 44px;
  padding: var(--spacing-sm) var(--spacing-md);

  background: transparent;
  border: none;
  border-radius: 0;
  cursor: pointer;

  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-normal);
  color: var(--color-text-primary);
  text-align: left;

  transition: background-color var(--transition-fast);
}

.export-btn__menu-item:hover:not(:disabled),
.export-btn__menu-item--active {
  background-color: var(--color-background-alt);
}

.export-btn__menu-item:focus,
.export-btn__menu-item:focus-visible {
  outline: none; /* Focus zarządzany przez focusedIndex i styl --active */
  background-color: var(--color-primary-light);
  color: var(--color-primary);
}

.export-btn__menu-item:disabled {
  opacity: var(--disabled-opacity);
  cursor:  var(--disabled-cursor);
}

.export-btn__menu-icon {
  font-size: 1.1em;
  flex-shrink: 0;
  width: 1.4em;
  text-align: center;
}

.export-btn__menu-label {
  font-weight: var(--font-weight-medium);
}

.export-btn__menu-desc {
  margin-left: auto;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

/* ============================================================
   ANIMACJA MENU
============================================================ */

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition:
    opacity   var(--transition-fast),
    transform var(--transition-fast);
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  .menu-fade-enter-active,
  .menu-fade-leave-active {
    transition: opacity var(--transition-fast);
  }

  .menu-fade-enter-from,
  .menu-fade-leave-to {
    transform: none;
  }

  .export-btn__arrow {
    transition: none;
  }
}

/* ============================================================
   STATUS — ogłaszany przez aria-live="polite"
============================================================ */

.export-btn__status {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: var(--line-height-tight);
  max-width: 220px;
}

.export-btn__status--success {
  color: var(--color-success);
}

.export-btn__status--error {
  color: var(--color-error);
}

/* ============================================================
   RESPONSYWNOŚĆ — na mobile menu idzie w prawo jeśli nie ma miejsca
============================================================ */

@media (max-width: 480px) {
  .export-btn__menu {
    left: auto;
    right: 0;
    min-width: 180px;
  }

  .export-btn__menu-desc {
    display: none; /* Za mało miejsca na opis */
  }
}
</style>
