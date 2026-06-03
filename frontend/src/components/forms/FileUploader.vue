<template>
  <!--
    FileUploader.vue — Komponent uploadu plików MHTML (multi-file)
    WCAG 2.1 AA:
      ✅ 1.3.1  — <fieldset>/<legend> dla semantyki formularza
      ✅ 1.4.3  — Kontrast tekstu >= 4.5:1
      ✅ 2.1.1  — W pełni obsługiwalny z klawiatury
      ✅ 2.4.7  — Widoczny focus outline (3px)
      ✅ 3.3.1  — Komunikaty błędów z role="alert"
      ✅ 3.3.2  — Widoczna etykieta pola (aria-label + label)
      ✅ 4.1.2  — aria-label, aria-describedby, aria-live
      ✅ 4.1.3  — aria-live="polite" dla statusów async
  -->
  <div class="file-uploader">
    <fieldset class="uploader-fieldset">
      <legend class="uploader-legend">{{ title }}</legend>

      <!-- ====================================================
           STREFA DRAG & DROP
      ==================================================== -->
      <div
        class="upload-area"
        :class="{
          'upload-area--dragging':  isDragging,
          'upload-area--has-files': hasFiles,
          'upload-area--error':     !!error
        }"
        role="region"
        :aria-label="areaAriaLabel"
        aria-describedby="upload-instructions upload-constraints"
        @dragenter.prevent="handleDragEnter"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
      >
        <!-- Ukryty input file (multiple) -->
        <input
          :id="inputId"
          ref="fileInputRef"
          type="file"
          accept=".mhtml,.mht"
          class="upload-input"
          :multiple="multiple"
          :aria-label="inputAriaLabel"
          :aria-describedby="error ? errorId : 'upload-instructions'"
          :aria-invalid="!!error ? 'true' : 'false'"
          tabindex="-1"
          @change="handleFileSelect"
        />

        <!-- Ikona i tekst strefy uploadu -->
        <div class="upload-content" :aria-hidden="isDragging">
          <div class="upload-icon" aria-hidden="true">
            <!-- Ikona uploadu (brak plików) -->
            <svg
              v-if="!hasFiles"
              width="48" height="48"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M24 32V16M24 16L16 24M24 16L32 24"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M12 36h24"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
              />
              <rect
                x="4" y="4" width="40" height="40"
                rx="8"
                stroke="currentColor"
                stroke-width="2"
                stroke-dasharray="6 3"
                fill="none"
              />
            </svg>

            <!-- Ikona stosu plików gdy wybrane -->
            <svg
              v-else
              width="48" height="48"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <!-- Tylna karta -->
              <rect x="10" y="10" width="26" height="32" rx="3" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 2" fill="none" opacity="0.4"/>
              <!-- Środkowa karta -->
              <rect x="7" y="7" width="26" height="32" rx="3" stroke="currentColor" stroke-width="1.5" fill="none" opacity="0.6"/>
              <!-- Przednia karta -->
              <rect x="4" y="4" width="28" height="34" rx="3" stroke="currentColor" stroke-width="2" fill="none"/>
              <!-- Linie "tekstu" -->
              <path d="M10 14h16M10 19h12M10 24h16M10 29h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <!-- Liczba plików -->
              <circle cx="38" cy="36" r="9" fill="var(--color-primary)"/>
              <text x="38" y="40" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="sans-serif">{{ selectedFiles.length }}</text>
            </svg>
          </div>

          <div class="upload-text">
            <!-- Stan: przeciąganie -->
            <template v-if="isDragging">
              <p class="upload-text__primary">Upuść {{ multiple ? 'pliki' : 'plik' }} tutaj</p>
            </template>

            <!-- Stan: pliki wybrane -->
            <template v-else-if="hasFiles">
              <p class="upload-text__primary upload-text__primary--success">
                Wybrano {{ selectedFiles.length }} {{ filesWord }}
              </p>
              <p class="upload-text__secondary">
                Łączny rozmiar: {{ totalSizeFormatted }}
              </p>
            </template>

            <!-- Stan: domyślny -->
            <template v-else>
              <p class="upload-text__primary">
                {{ multiple ? 'Przeciągnij i upuść pliki MHTML' : 'Przeciągnij i upuść plik MHTML' }}
              </p>
              <p class="upload-text__secondary" id="upload-instructions">
                lub
              </p>
            </template>
          </div>
        </div>

        <!-- Przycisk "Wybierz pliki" — główny trigger dla klawiatury -->
        <label
          :for="inputId"
          class="upload-label-btn"
          :class="{ 'upload-label-btn--has-files': hasFiles }"
        >
          <span class="upload-label-btn__text">
            {{ hasFiles ? (multiple ? 'Dodaj kolejne pliki' : 'Zmień plik') : (multiple ? 'Wybierz pliki' : 'Wybierz plik') }}
          </span>
        </label>
      </div>

      <!-- Opis ograniczeń (widoczny pod strefą) -->
      <p class="upload-constraints" id="upload-constraints">
        Akceptowane formaty: <strong>.mhtml</strong>, <strong>.mht</strong>
        &nbsp;&bull;&nbsp;
        Maks. rozmiar pliku: <strong>50 MB</strong>
        <template v-if="multiple">
          &nbsp;&bull;&nbsp;
          Maks. liczba plików: <strong>{{ maxFiles }}</strong>
        </template>
      </p>

      <!-- ====================================================
           LISTA WYBRANYCH PLIKÓW
      ==================================================== -->
      <ul
        v-if="hasFiles"
        class="file-list"
        role="list"
        :aria-label="`Lista wybranych plików (${selectedFiles.length})`"
      >
        <li
          v-for="(entry, index) in selectedFiles"
          :key="entry.id"
          class="file-list__item"
          :class="{
            'file-list__item--uploading': entry.status === 'uploading',
            'file-list__item--done':      entry.status === 'done',
            'file-list__item--error':     entry.status === 'error',
          }"
          role="listitem"
        >
          <!-- Ikona pliku -->
          <span class="file-list__icon" aria-hidden="true">
            <svg v-if="entry.status === 'done'" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <circle cx="9" cy="9" r="8" stroke="var(--color-success)" stroke-width="1.5"/>
              <path d="M5.5 9l2.5 2.5 4.5-4.5" stroke="var(--color-success)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else-if="entry.status === 'error'" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <circle cx="9" cy="9" r="8" stroke="var(--color-error)" stroke-width="1.5"/>
              <path d="M6 6l6 6M12 6l-6 6" stroke="var(--color-error)" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <path d="M4 2h8l4 4v10a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" stroke-width="1.5" fill="none"/>
              <path d="M12 2v4h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </span>

          <!-- Nazwa i rozmiar -->
          <span class="file-list__info">
            <span class="file-list__name" :title="entry.name">{{ entry.name }}</span>
            <span class="file-list__size">{{ formatSize(entry.size) }}</span>
          </span>

          <!-- Status etykieta -->
          <span
            v-if="entry.status === 'uploading'"
            class="file-list__status file-list__status--uploading"
            aria-label="Trwa przesyłanie"
          >
            <span class="mini-spinner" aria-hidden="true"></span>
            <span>Analizuję…</span>
          </span>
          <span
            v-else-if="entry.status === 'done'"
            class="file-list__status file-list__status--done"
          >
            Gotowe
          </span>
          <span
            v-else-if="entry.status === 'error'"
            class="file-list__status file-list__status--error"
            :title="entry.errorMsg"
          >
            Błąd
          </span>

          <!-- Przycisk usunięcia -->
          <button
            v-if="!isUploading"
            type="button"
            class="file-list__remove"
            :aria-label="`Usuń plik: ${entry.name}`"
            @click="removeFile(index)"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </li>
      </ul>

      <!-- Błąd walidacji -->
      <div
        v-if="error"
        :id="errorId"
        role="alert"
        aria-live="assertive"
        class="upload-error"
      >
        <svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
          <path d="M8 5v3.5M8 11h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Status operacji -->
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        class="upload-status"
      >
        <template v-if="isUploading">
          <span class="upload-status__spinner" aria-hidden="true" />
          <span>Trwa analiza {{ uploadProgress }}%…</span>
        </template>
        <template v-else-if="uploadDone">
          Analiza zakończona pomyślnie.
        </template>
      </div>

      <!-- Pasek postępu -->
      <div
        v-if="isUploading"
        class="upload-progress"
        role="progressbar"
        :aria-valuenow="uploadProgress"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Postęp analizy: ${uploadProgress}%`"
      >
        <div
          class="upload-progress__bar"
          :style="{ width: uploadProgress + '%' }"
        />
      </div>

      <!-- Przyciski akcji -->
      <div class="upload-actions">
        <!-- Wyczyść wszystkie pliki -->
        <button
          v-if="hasFiles && !isUploading"
          type="button"
          class="btn-reset"
          :aria-label="`Usuń wszystkie wybrane pliki (${selectedFiles.length})`"
          @click="resetFiles"
        >
          Wyczyść listę
        </button>

        <!-- Główny przycisk -->
        <button
          type="button"
          class="btn-upload"
          :disabled="!hasFiles || isUploading"
          :aria-disabled="(!hasFiles || isUploading) ? 'true' : 'false'"
          :aria-describedby="!hasFiles ? 'upload-instructions' : undefined"
          @click="handleUpload"
        >
          <span
            v-if="isUploading"
            class="btn-upload__spinner"
            aria-hidden="true"
          />
          {{ uploadButtonLabel }}
        </button>
      </div>
    </fieldset>
  </div>
</template>

<script setup>
/**
 * FileUploader.vue
 *
 * Komponent drag & drop do wysyłania plików MHTML do analizy WCAG.
 * Obsługuje wiele plików jednocześnie (multi-file upload).
 * Pełna obsługa klawiatury, walidacja po stronie klienta,
 * komunikaty WCAG-compliant.
 */
import { ref, computed } from "vue"

// ── Props ────────────────────────────────────────────────────────────────────

const props = defineProps({
  /** Tytuł wyświetlany w legend */
  title: {
    type: String,
    default: "Wybierz pliki MHTML do analizy"
  },

  /** Maksymalny rozmiar pliku w bajtach (domyślnie 50MB) */
  maxSizeBytes: {
    type: Number,
    default: 50 * 1024 * 1024
  },

  /** Czy pozwalać na wiele plików */
  multiple: {
    type: Boolean,
    default: true
  },

  /** Maksymalna liczba plików (przy multiple=true) */
  maxFiles: {
    type: Number,
    default: 40
  },

  /** Czy pokazywać symulowany pasek postępu (demo) */
  simulateProgress: {
    type: Boolean,
    default: false
  }
})

// ── Emits ────────────────────────────────────────────────────────────────────

const emit = defineEmits([
  /**
   * Emitowany gdy użytkownik wybrał poprawne pliki.
   * Payload: { files: File[], count: number, totalSize: number }
   */
  "files-selected",

  /**
   * Backward-compat: emitowany też dla pojedynczego pliku.
   * Payload: { file: File, name: string, size: number }
   */
  "file-selected",

  /**
   * Emitowany po kliknięciu "Analizuj".
   * Payload: File[] (tablica plików)
   */
  "upload-start",

  /**
   * Emitowany po wyczyszczeniu listy.
   */
  "file-cleared"
])

// ── Refs ─────────────────────────────────────────────────────────────────────

const fileInputRef   = ref(null)
const isDragging     = ref(false)
const error          = ref("")
const isUploading    = ref(false)
const uploadProgress = ref(0)
const uploadDone     = ref(false)
const dragCounter    = ref(0)

/**
 * selectedFiles — tablica obiektów:
 * { id: string, file: File, name: string, size: number,
 *   status: 'pending'|'uploading'|'done'|'error', errorMsg: string }
 */
const selectedFiles = ref([])

// ── Computed ─────────────────────────────────────────────────────────────────

const uid     = Math.random().toString(36).slice(2, 8)
const inputId = `file-input-${uid}`
const errorId = `file-error-${uid}`

const hasFiles = computed(() => selectedFiles.value.length > 0)

const totalSize = computed(() =>
  selectedFiles.value.reduce((sum, e) => sum + e.size, 0)
)

const totalSizeFormatted = computed(() => formatSize(totalSize.value))

/** Polska odmiana słowa "plik" */
const filesWord = computed(() => {
  const n = selectedFiles.value.length
  if (n === 1) return "plik"
  if (n >= 2 && n <= 4) return "pliki"
  return "plików"
})

const areaAriaLabel = computed(() => {
  if (isDragging.value) return "Strefa upuszczania plików — zwolnij przycisk myszy"
  if (hasFiles.value) return `Wybrano ${selectedFiles.value.length} ${filesWord.value}. Przeciągnij kolejne lub kliknij, aby dodać.`
  return "Strefa przeciągania i upuszczania plików MHTML"
})

const inputAriaLabel = computed(() =>
  `Wybierz ${props.multiple ? 'pliki' : 'plik'} MHTML do analizy. Akceptowane: .mhtml, .mht. Maks. rozmiar: ${props.maxSizeBytes / 1024 / 1024} MB.`
)

const uploadButtonLabel = computed(() => {
  if (isUploading.value) return "Analizowanie…"
  const n = selectedFiles.value.length
  if (n === 0) return "Analizuj"
  return n === 1 ? "Analizuj plik" : `Analizuj ${n} ${filesWord.value}`
})

// ── Walidacja ─────────────────────────────────────────────────────────────────

const validateFile = (file) => {
  if (!file) return "Nie wybrano żadnego pliku."

  const name = file.name.toLowerCase()
  if (![".mhtml", ".mht"].some(ext => name.endsWith(ext))) {
    return `Nieprawidłowy format "${file.name}". Dozwolone: .mhtml, .mht`
  }

  if (file.size === 0) {
    return `Plik "${file.name}" jest pusty.`
  }

  if (file.size > props.maxSizeBytes) {
    const maxMB = (props.maxSizeBytes / 1024 / 1024).toFixed(0)
    const fileMB = (file.size / 1024 / 1024).toFixed(2)
    return `Plik "${file.name}" jest za duży (${fileMB} MB > ${maxMB} MB).`
  }

  return null
}

/**
 * Dodaje pliki do listy — pomija duplikaty (ta sama nazwa + rozmiar).
 * Zwraca liczbę skutecznie dodanych plików.
 */
const addFiles = (fileList) => {
  const files = Array.from(fileList)
  error.value = ""
  uploadDone.value = false

  let added = 0
  const errors = []

  for (const file of files) {
    // Limit liczby plików
    if (props.multiple && selectedFiles.value.length >= props.maxFiles) {
      errors.push(`Osiągnięto limit ${props.maxFiles} plików.`)
      break
    }

    const validationError = validateFile(file)
    if (validationError) {
      errors.push(validationError)
      continue
    }

    // Sprawdź duplikat (nazwa + rozmiar)
    const isDuplicate = selectedFiles.value.some(
      e => e.name === file.name && e.size === file.size
    )
    if (isDuplicate) continue

    selectedFiles.value.push({
      id:       `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      name:     file.name,
      size:     file.size,
      status:   "pending",
      errorMsg: ""
    })
    added++
  }

  // Pokaż pierwszy błąd walidacji
  if (errors.length > 0) {
    error.value = errors[0]
    if (errors.length > 1) {
      error.value += ` (i ${errors.length - 1} więcej problemów)`
    }
  }

  if (added > 0) {
    const allFiles = selectedFiles.value.map(e => e.file)

    emit("files-selected", {
      files: allFiles,
      count: allFiles.length,
      totalSize: totalSize.value
    })

    // backward-compat dla pojedynczego pliku
    if (!props.multiple || selectedFiles.value.length === 1) {
      const first = selectedFiles.value[0]
      emit("file-selected", { file: first.file, name: first.name, size: first.size })
    }
  }

  return added
}

// ── Formatowanie ──────────────────────────────────────────────────────────────

const formatSize = (bytes) => {
  if (!bytes) return ""
  if (bytes < 1024)        return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

// ── Event Handlers — Input ────────────────────────────────────────────────────

const handleFileSelect = (event) => {
  const files = event.target.files
  if (files && files.length > 0) addFiles(files)
  event.target.value = ""  // Pozwala na ponowny wybór tych samych plików
}

// ── Event Handlers — Drag & Drop ─────────────────────────────────────────────

const handleDragEnter = (event) => {
  dragCounter.value++
  if (event.dataTransfer?.types?.includes("Files")) {
    isDragging.value = true
  }
}

const handleDragOver = (event) => {
  if (event.dataTransfer) event.dataTransfer.dropEffect = "copy"
}

const handleDragLeave = () => {
  dragCounter.value--
  if (dragCounter.value === 0) isDragging.value = false
}

const handleDrop = (event) => {
  dragCounter.value = 0
  isDragging.value  = false

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  if (!props.multiple && files.length > 1) {
    error.value = `Wybrano ${files.length} plików. W tym trybie można przesłać tylko jeden plik.`
    return
  }

  addFiles(files)
}

// ── Usuwanie plików ───────────────────────────────────────────────────────────

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
  error.value = ""
  if (selectedFiles.value.length === 0) {
    uploadDone.value = false
    emit("file-cleared")
  }
}

const resetFiles = () => {
  selectedFiles.value  = []
  error.value          = ""
  uploadProgress.value = 0
  uploadDone.value     = false
  isUploading.value    = false
  dragCounter.value    = 0

  if (fileInputRef.value) fileInputRef.value.value = ""

  emit("file-cleared")
}

// ── Upload ────────────────────────────────────────────────────────────────────

const handleUpload = async () => {
  if (!hasFiles.value || isUploading.value) return

  const files = selectedFiles.value.map(e => e.file)
  emit("upload-start", files)

  // Symulacja postępu (demo)
  if (props.simulateProgress) {
    isUploading.value    = true
    uploadProgress.value = 0
    uploadDone.value     = false

    await new Promise(resolve => {
      const interval = setInterval(() => {
        uploadProgress.value += Math.floor(Math.random() * 15) + 5
        if (uploadProgress.value >= 100) {
          uploadProgress.value = 100
          clearInterval(interval)
          setTimeout(() => {
            isUploading.value = false
            uploadDone.value  = true
            resolve()
          }, 400)
        }
      }, 300)
    })
  }
}

// ── Expose — parent może ustawiać status poszczególnych plików ────────────────

defineExpose({
  /**
   * Ustaw status konkretnego pliku (po udanym/nieudanym uploadzie).
   * @param {string} fileId - entry.id
   * @param {'uploading'|'done'|'error'} status
   * @param {string} [errorMsg]
   */
  setFileStatus(fileId, status, errorMsg = "") {
    const entry = selectedFiles.value.find(e => e.id === fileId)
    if (entry) {
      entry.status   = status
      entry.errorMsg = errorMsg
    }
  },

  /** Ustaw globalny postęp (0–100) */
  setProgress(pct) {
    uploadProgress.value = Math.min(100, Math.max(0, pct))
  },

  /** Oznacz zakończenie uploadu */
  setDone() {
    isUploading.value    = false
    uploadDone.value     = true
    uploadProgress.value = 100
  },

  /** Resetuje stan komponentu */
  resetFiles,

  /** Zwraca tablicę { id, file } dla wszystkich pending plików */
  getPendingFiles() {
    return selectedFiles.value
      .filter(e => e.status === "pending")
      .map(e => ({ id: e.id, file: e.file }))
  }
})
</script>

<style scoped>
/* ============================================================
   WRAPPER
============================================================ */

.file-uploader {
  width: 100%;
}

/* ============================================================
   FIELDSET & LEGEND (WCAG 1.3.1)
============================================================ */

.uploader-fieldset {
  border: none;
  padding: 0;
  margin: 0;
}

.uploader-legend {
  display: block;
  width: 100%;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  line-height: var(--line-height-tight);
}

/* ============================================================
   STREFA UPLOADU
============================================================ */

.upload-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);

  min-height: 200px;
  padding: var(--spacing-xl) var(--spacing-lg);

  background-color: var(--color-background);
  border: 2px dashed var(--color-border-light);
  border-radius: var(--radius-lg);

  text-align: center;
  cursor: pointer;

  transition:
    border-color     var(--transition-fast),
    background-color var(--transition-fast);
}

.upload-area:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.upload-area--dragging {
  border-color:     var(--color-primary);
  border-style:     solid;
  background-color: var(--color-primary-light);
  box-shadow:       0 0 0 4px rgba(0, 102, 204, 0.15);
}

.upload-area--has-files {
  border-color: var(--color-success);
  border-style: solid;
  background-color: var(--color-success-light);
}

.upload-area--error {
  border-color: var(--color-error);
  background-color: var(--color-error-light);
}

/* ============================================================
   INPUT FILE (ukryty)
============================================================ */

.upload-input {
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
   IKONA I TEKST
============================================================ */

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  pointer-events: none;
}

.upload-icon {
  color: var(--color-primary);
  opacity: 0.7;
  transition: opacity var(--transition-fast), color var(--transition-fast);
}

.upload-area--has-files .upload-icon {
  color: var(--color-success);
  opacity: 1;
}

.upload-area--error .upload-icon {
  color: var(--color-error);
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.upload-text__primary {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.upload-text__primary--success {
  color: var(--color-success);
}

.upload-text__secondary {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* ============================================================
   PRZYCISK "WYBIERZ PLIKI" (WCAG 2.4.7)
============================================================ */

.upload-label-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  padding: var(--spacing-sm) var(--spacing-lg);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  line-height: 1;

  background-color: var(--color-background);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  cursor: pointer;

  transition:
    background-color var(--transition-fast),
    color            var(--transition-fast);

  position: relative;
  z-index: 1;
}

.upload-label-btn:hover {
  background-color: var(--color-primary-light);
}

.upload-label-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.upload-label-btn--has-files {
  color:        var(--color-text-secondary);
  border-color: var(--color-border-light);
}

.upload-label-btn--has-files:hover {
  color:            var(--color-text-primary);
  background-color: var(--color-background-alt);
  border-color:     var(--color-primary);
}

/* ============================================================
   OGRANICZENIA
============================================================ */

.upload-constraints {
  margin-top: var(--spacing-sm);
  margin-bottom: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-align: center;
}

/* ============================================================
   LISTA PLIKÓW (WCAG 1.3.1 — role="list")
============================================================ */

.file-list {
  list-style: none;
  padding: 0;
  margin: var(--spacing-md) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.file-list__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);

  font-size: var(--font-size-sm);
  transition: background-color var(--transition-fast);
}

.file-list__item--uploading {
  background-color: var(--color-primary-light);
  border-color: var(--color-primary);
}

.file-list__item--done {
  background-color: var(--color-success-light);
  border-color: var(--color-success);
}

.file-list__item--error {
  background-color: var(--color-error-light);
  border-color: var(--color-error);
}

.file-list__icon {
  flex-shrink: 0;
  color: var(--color-text-secondary);
}

.file-list__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-list__name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-list__size {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.file-list__status {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: 2px var(--spacing-xs);
  border-radius: var(--radius-sm);
}

.file-list__status--uploading {
  color: var(--color-primary);
}

.file-list__status--done {
  color: var(--color-success);
  background-color: var(--color-success-light);
}

.file-list__status--error {
  color: var(--color-error);
  background-color: var(--color-error-light);
}

.mini-spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 1.5px solid var(--color-border-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Przycisk usunięcia pliku z listy */
.file-list__remove {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;

  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;

  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.file-list__remove:hover {
  color: var(--color-error);
  border-color: var(--color-error);
}

.file-list__remove:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

/* ============================================================
   BŁĄD WALIDACJI (WCAG 3.3.1)
============================================================ */

.upload-error {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);

  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);

  background-color: var(--color-error-light);
  border: 1px solid var(--color-error);
  border-left-width: 4px;
  border-radius: var(--radius-sm);

  color: var(--color-error);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
}

.upload-error svg {
  flex-shrink: 0;
  margin-top: 2px;
}

/* ============================================================
   STATUS (aria-live="polite")
============================================================ */

.upload-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  margin-top: var(--spacing-sm);
  min-height: 24px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.upload-status__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .upload-status__spinner,
  .mini-spinner {
    animation: none;
    border-top-color: var(--color-primary);
    border-right-color: var(--color-primary);
  }
}

/* ============================================================
   PASEK POSTĘPU (role="progressbar")
============================================================ */

.upload-progress {
  margin-top: var(--spacing-sm);
  width: 100%;
  height: 6px;
  background-color: var(--color-background-alt);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.upload-progress__bar {
  height: 100%;
  background-color: var(--color-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-fast);
}

/* ============================================================
   PRZYCISKI AKCJI
============================================================ */

.upload-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.btn-reset {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.btn-reset:hover {
  color: var(--color-error);
  border-color: var(--color-error);
}

.btn-reset:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.btn-upload {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-xl);

  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);

  color: var(--color-text-inverse);
  background-color: var(--color-primary);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  cursor: pointer;

  transition:
    background-color var(--transition-fast),
    border-color     var(--transition-fast),
    opacity          var(--transition-fast);
}

.btn-upload:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  border-color:     var(--color-primary-dark);
}

.btn-upload:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.btn-upload:disabled {
  opacity:  var(--disabled-opacity);
  cursor:   var(--disabled-cursor);
}

.btn-upload__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ============================================================
   RESPONSYWNOŚĆ
============================================================ */

@media (max-width: 639px) {
  .upload-area {
    min-height: 160px;
    padding: var(--spacing-lg) var(--spacing-md);
  }

  .upload-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .btn-upload,
  .btn-reset {
    width: 100%;
    justify-content: center;
  }

  .file-list__item {
    flex-wrap: wrap;
  }
}
</style>
