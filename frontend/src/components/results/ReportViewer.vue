<template>
  <!--
    ReportViewer.vue — Glowny komponent wyswietlania raportu WCAG
    WCAG 2.1 AA:
      ✅ 1.3.1  — Semantyczne sekcje z aria-labelledby
      ✅ 2.1.1  — Taby dostepne z klawiatury (strzalki + Tab)
      ✅ 2.4.3  — Logiczna kolejnosc focusu
      ✅ 2.4.6  — Opisowe naglowki sekcji
      ✅ 2.4.7  — Widoczny focus outline
      ✅ 4.1.2  — role=tablist, role=tab, aria-selected, aria-controls
  -->
  <article class="report-viewer" aria-label="Raport analizy WCAG">

    <!-- ====================================================
         NAGLOWEK RAPORTU
    ==================================================== -->
    <header class="report-header">
      <div class="report-header__meta">
        <h1 class="report-header__title">
          <span class="report-header__icon" aria-hidden="true">📄</span>
          {{ report.filename }}
        </h1>
        <div class="report-header__details">
          <time
            :datetime="report.analysis_date"
            class="report-header__date"
          >
            Analiza: {{ formatDate(report.analysis_date) }}
          </time>
          <span
            class="report-header__status"
            :class="`report-header__status--${report.status || 'done'}`"
            :aria-label="`Status: ${statusLabel}`"
          >
            {{ statusLabel }}
          </span>
        </div>
      </div>

      <!-- Pasek compliance na gorze -->
      <div
        class="compliance-bar"
        role="meter"
        :aria-valuenow="report.summary.compliance_percentage"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Zgodnosc z WCAG: ${report.summary.compliance_percentage}%`"
      >
        <div class="compliance-bar__track">
          <div
            class="compliance-bar__fill"
            :style="{
              width: report.summary.compliance_percentage + '%',
              backgroundColor: complianceColor
            }"
          />
        </div>
        <span
          class="compliance-bar__label"
          :style="{ color: complianceColor }"
          aria-hidden="true"
        >
          {{ report.summary.compliance_percentage }}%
        </span>
      </div>

      <div
        v-if="report.source_reports?.length"
        class="combined-report"
        role="note"
        :aria-label="`Raport zbiorczy z ${report.source_reports.length} plików`"
      >
        <strong>Raport zbiorczy:</strong>
        {{ report.source_reports.length }} plików,
        {{ report.summary.total_issues ?? totalIssues }} problemów łącznie.
      </div>
    </header>

    <!-- ====================================================
         TABLIST (WCAG 4.1.2 — role=tablist, role=tab)
    ==================================================== -->
    <div
      class="report-tabs"
      role="tablist"
      :aria-label="`Widoki raportu dla ${report.filename}`"
    >
      <button
        v-for="(tab, index) in tabs"
        :key="tab.id"
        :id="`tab-${tab.id}`"
        role="tab"
        :aria-selected="activeTab === tab.id ? 'true' : 'false'"
        :aria-controls="`tabpanel-${tab.id}`"
        :tabindex="activeTab === tab.id ? 0 : -1"
        :class="['report-tab', { 'report-tab--active': activeTab === tab.id }]"
        @click="setTab(tab.id)"
        @keydown="handleTabKeydown($event, index)"
      >
        <span class="report-tab__icon" aria-hidden="true">{{ tab.icon }}</span>
        <span class="report-tab__label">{{ tab.label }}</span>
        <span
          v-if="tab.count !== undefined"
          class="report-tab__badge"
          :aria-label="`${tab.count} elementow`"
        >
          {{ tab.count }}
        </span>
      </button>
    </div>

    <!-- ====================================================
         TAB PANEL: SUMMARY
    ==================================================== -->
    <section
      v-show="activeTab === 'summary'"
      id="tabpanel-summary"
      role="tabpanel"
      :aria-labelledby="`tab-summary`"
      tabindex="0"
      class="report-panel"
    >
      <h2 id="summary-heading" class="sr-only">Podsumowanie zgodnosci</h2>

      <!-- Karty statystyk -->
      <div class="stats-grid" aria-label="Statystyki analizy">

        <!-- Compliance -->
        <div class="stat-card stat-card--compliance">
          <div
            class="stat-card__value"
            :style="{ color: complianceColor }"
            aria-label="`Zgodnosc: ${report.summary.compliance_percentage} procent`"
          >
            {{ report.summary.compliance_percentage }}<span class="stat-card__unit" aria-hidden="true">%</span>
          </div>
          <div class="stat-card__label">Zgodnosc z WCAG AA</div>
          <div class="stat-card__sub" :style="{ color: complianceColor }">
            {{ complianceLevel }}
          </div>
        </div>

        <!-- Bledow krytycznych -->
        <div class="stat-card stat-card--critical">
          <div class="stat-card__value stat-card__value--critical">
            {{ report.summary.critical_errors }}
          </div>
          <div class="stat-card__label">Bledy krytyczne</div>
          <div class="stat-card__sub">Poziom A — wymagane</div>
        </div>

        <!-- Bledow glownych -->
        <div class="stat-card stat-card--major">
          <div class="stat-card__value stat-card__value--major">
            {{ report.summary.major_errors }}
          </div>
          <div class="stat-card__label">Bledy glowne</div>
          <div class="stat-card__sub">Poziom AA — wymagane</div>
        </div>

        <!-- Ostrzezen -->
        <div class="stat-card stat-card--minor">
          <div class="stat-card__value stat-card__value--minor">
            {{ report.summary.minor_warnings ?? report.summary.minor_errors ?? 0 }}
          </div>
          <div class="stat-card__label">Ostrzezenia</div>
          <div class="stat-card__sub">Poziom AAA — zalecane</div>
        </div>

        <!-- Checks zaliczonych -->
        <div class="stat-card stat-card--passed">
          <div class="stat-card__value stat-card__value--passed">
            {{ report.summary.passed_checks ?? passedChecks }}
          </div>
          <div class="stat-card__label">Kryteria spelnione</div>
          <div class="stat-card__sub">z {{ report.summary.total_checks ?? totalChecks }} sprawdzanych</div>
        </div>

        <!-- Ogolna ocena -->
        <div class="stat-card stat-card--grade">
          <div class="stat-card__value" :style="{ color: complianceColor }">
            {{ complianceGrade }}
          </div>
          <div class="stat-card__label">Ocena WCAG</div>
          <div class="stat-card__sub">{{ complianceDescription }}</div>
        </div>
      </div>

      <!-- Rozklad wedlug filarow WCAG -->
      <section class="wcag-pillars" aria-labelledby="pillars-heading">
        <h3 id="pillars-heading" class="section-subheading">Filary WCAG</h3>
        <div class="pillars-grid">
          <div
            v-for="pillar in wcagPillars"
            :key="pillar.id"
            class="pillar-card"
          >
            <div class="pillar-card__header">
              <span class="pillar-card__num" aria-hidden="true">{{ pillar.num }}</span>
              <h4 class="pillar-card__name">{{ pillar.name }}</h4>
            </div>
            <div
              class="pillar-card__bar"
              role="meter"
              :aria-valuenow="pillar.score"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-label="`${pillar.name}: ${pillar.score}%`"
            >
              <div
                class="pillar-card__fill"
                :style="{ width: pillar.score + '%', backgroundColor: getPillarColor(pillar.score) }"
              />
            </div>
            <span class="pillar-card__score">{{ pillar.score }}%</span>
          </div>
        </div>
      </section>
    </section>

    <!-- ====================================================
         TAB PANEL: DETAILS
    ==================================================== -->
    <section
      v-show="activeTab === 'details'"
      id="tabpanel-details"
      role="tabpanel"
      :aria-labelledby="`tab-details`"
      tabindex="0"
      class="report-panel"
    >
      <div class="details-toolbar">
        <h2 id="details-heading" class="details-toolbar__heading">
          Znalezione problemy
          <span class="details-toolbar__count">({{ filteredIssues.length }})</span>
        </h2>

        <!-- Filtry severity -->
        <div class="filters" role="group" aria-label="Filtruj problemy wg severity">
          <button
            v-for="filter in severityFilters"
            :key="filter.value"
            type="button"
            :class="[
              'filter-btn',
              `filter-btn--${filter.value}`,
              { 'filter-btn--active': activeSeverityFilter === filter.value }
            ]"
            :aria-pressed="activeSeverityFilter === filter.value ? 'true' : 'false'"
            @click="activeSeverityFilter = filter.value"
          >
            {{ filter.label }}
            <span class="filter-btn__count" aria-hidden="true">({{ filter.count }})</span>
          </button>
        </div>
      </div>

      <!-- Brak bledow -->
      <div
        v-if="filteredIssues.length === 0"
        class="no-issues"
        role="status"
      >
        <span class="no-issues__icon" aria-hidden="true">✅</span>
        <p class="no-issues__text">
          {{ activeSeverityFilter === 'all'
            ? 'Brak problemow — strona spelnia kryterium WCAG AA!'
            : `Brak problemow o severity: ${activeSeverityFilter}` }}
        </p>
      </div>

      <!-- Lista bledow -->
      <ol
        v-else
        class="issues-list"
        :aria-label="`Lista ${filteredIssues.length} problemow dostepnosci`"
      >
        <li v-for="(issue, index) in filteredIssues" :key="issue.id">
          <IssueCard
            :issue="issue"
            :index="index + 1"
            :total="filteredIssues.length"
          />
        </li>
      </ol>
    </section>

    <!-- ====================================================
         TAB PANEL: STATISTICS
    ==================================================== -->
    <section
      v-show="activeTab === 'statistics'"
      id="tabpanel-statistics"
      role="tabpanel"
      :aria-labelledby="`tab-statistics`"
      tabindex="0"
      class="report-panel"
    >
      <h2 id="stats-heading" class="sr-only">Szczegolowe statystyki</h2>

      <!-- Rozklad wedlug kryterium WCAG -->
      <section class="stat-section" aria-labelledby="criteria-heading">
        <h3 id="criteria-heading" class="section-subheading">Top problemy wg kryterium</h3>
        <table class="criteria-table">
          <caption class="sr-only">Tabela problemow WCAG posortowanych wg liczby wystapien</caption>
          <thead>
            <tr>
              <th scope="col">Kryterium WCAG</th>
              <th scope="col">Severity</th>
              <th scope="col" class="text-right">Wystapienia</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in criteriaStats"
              :key="row.criterion"
            >
              <td>{{ row.criterion }}</td>
              <td>
                <span :class="['severity-badge', `severity-badge--${row.severity}`]">
                  {{ row.severity }}
                </span>
              </td>
              <td class="text-right">{{ row.count }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Rozklad wedlug typu elementu HTML -->
      <section class="stat-section" aria-labelledby="elements-heading">
        <h3 id="elements-heading" class="section-subheading">Problematyczne elementy HTML</h3>
        <ul class="element-stats" aria-label="Lista elementow HTML z problemami">
          <li
            v-for="el in elementStats"
            :key="el.tag"
            class="element-stat"
          >
            <code class="element-stat__tag">{{ el.tag }}</code>
            <div
              class="element-stat__bar"
              role="meter"
              :aria-valuenow="el.count"
              :aria-valuemax="maxElementCount"
              aria-valuemin="0"
              :aria-label="`${el.tag}: ${el.count} problemow`"
            >
              <div
                class="element-stat__fill"
                :style="{ width: (el.count / maxElementCount * 100) + '%' }"
              />
            </div>
            <span class="element-stat__count">{{ el.count }}</span>
          </li>
        </ul>
      </section>

      <!-- Akcje eksportu -->
      <section class="export-section" aria-labelledby="export-heading">
        <h3 id="export-heading" class="section-subheading">Eksport raportu</h3>
        <div class="export-buttons">
          <button
            v-for="fmt in exportFormats"
            :key="fmt.value"
            type="button"
            class="export-btn"
            :aria-label="`Eksportuj raport jako ${fmt.label}`"
            @click="$emit('export', { analysisId: report.analysis_id, format: fmt.value })"
          >
            <span aria-hidden="true">{{ fmt.icon }}</span>
            {{ fmt.label }}
          </button>
        </div>
      </section>
    </section>

  </article>
</template>

<script setup>
import { ref, computed } from "vue"
import IssueCard from "@/components/results/IssueCard.vue"

// ── Props & Emits ──────────────────────────────────────────────────────────

const props = defineProps({
  report: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(["export", "close", "compare"])

// ── Tabs ──────────────────────────────────────────────────────────────────

const activeTab = ref("summary")

const tabs = computed(() => [
  { id: "summary",    label: "Podsumowanie", icon: "📊", count: undefined },
  { id: "details",   label: "Problemy",     icon: "🔍", count: totalIssues.value },
  { id: "statistics",label: "Statystyki",   icon: "📈", count: undefined },
])

/** Zmiana taba — kliknieciem lub Enter/Space */
const setTab = (tabId) => {
  activeTab.value = tabId
}

/**
 * Nawigacja klawiatura po tablist (WCAG 2.1.1):
 *   ArrowRight / ArrowLeft — kolejny / poprzedni tab
 *   Home / End             — pierwszy / ostatni tab
 */
const handleTabKeydown = (event, currentIndex) => {
  const tabCount = tabs.value.length
  let newIndex = currentIndex

  switch (event.key) {
    case "ArrowRight":
      newIndex = (currentIndex + 1) % tabCount
      break
    case "ArrowLeft":
      newIndex = (currentIndex - 1 + tabCount) % tabCount
      break
    case "Home":
      newIndex = 0
      break
    case "End":
      newIndex = tabCount - 1
      break
    default:
      return
  }

  event.preventDefault()
  setTab(tabs.value[newIndex].id)

  // Przesuniecie focusu na nowy tab button
  const tabButtons = document.querySelectorAll("[role=tab]")
  tabButtons[newIndex]?.focus()
}

// ── Compliance ────────────────────────────────────────────────────────────

/** Kolor compliance wg wartosci procentowej */
const complianceColor = computed(() => {
  const pct = props.report.summary.compliance_percentage
  if (pct >= 80) return "var(--color-success)"   // 5.45:1 ✅
  if (pct >= 60) return "var(--color-warning)"   // 4.83:1 ✅
  return "var(--color-error)"                    // 5.89:1 ✅
})

/** Slowny opis poziomu zgodnosci */
const complianceLevel = computed(() => {
  const pct = props.report.summary.compliance_percentage
  if (pct >= 90) return "Doskonala zgodnosc"
  if (pct >= 80) return "Dobra zgodnosc"
  if (pct >= 60) return "Czesciowa zgodnosc"
  if (pct >= 40) return "Niska zgodnosc"
  return "Krytyczna niezgodnosc"
})

/** Ocena literowa */
const complianceGrade = computed(() => {
  const pct = props.report.summary.compliance_percentage
  if (pct >= 90) return "A"
  if (pct >= 80) return "B"
  if (pct >= 70) return "C"
  if (pct >= 60) return "D"
  return "F"
})

const complianceDescription = computed(() => {
  const grade = complianceGrade.value
  return {
    A: "Wysoki standard dostepnosci",
    B: "Dobry poziom dostepnosci",
    C: "Wymaga poprawy",
    D: "Poważne braki",
    F: "Niezgodnosc z WCAG AA",
  }[grade]
})

// ── Status ────────────────────────────────────────────────────────────────

const statusLabel = computed(() => ({
  done:       "Zakonczona",
  processing: "W trakcie",
  pending:    "Oczekuje",
  error:      "Blad",
}[props.report.status] ?? "Zakonczona"))

// ── Statystyki — computed ─────────────────────────────────────────────────

const totalIssues = computed(() => props.report.issues?.length ?? 0)

const passedChecks = computed(() => {
  const s = props.report.summary
  return (s.total_checks ?? 50) - (s.critical_errors + s.major_errors + (s.minor_warnings ?? s.minor_errors ?? 0))
})

const totalChecks = computed(() => props.report.summary.total_checks ?? 50)

/** Filary WCAG z przyblizonym score (bez danych z backendu — estymacja) */
const wcagPillars = computed(() => {
  const issues = props.report.issues ?? []
  const pillarMap = {
    "1.": { id: "perceivable",    name: "Postrzegalnosc", num: "1", count: 0 },
    "2.": { id: "operable",      name: "Funkcjonalnosc", num: "2", count: 0 },
    "3.": { id: "understandable",name: "Zrozumialosc",   num: "3", count: 0 },
    "4.": { id: "robust",        name: "Solidnosc",      num: "4", count: 0 },
  }
  issues.forEach(issue => {
    const prefix = (issue.wcag_criterion || "").substring(0, 2)
    if (pillarMap[prefix]) pillarMap[prefix].count++
  })
  return Object.values(pillarMap).map(p => ({
    ...p,
    score: Math.max(0, Math.round(100 - (p.count / Math.max(totalIssues.value, 1)) * 100 * 0.7))
  }))
})

const getPillarColor = (score) => {
  if (score >= 80) return "var(--color-success)"
  if (score >= 60) return "var(--color-warning)"
  return "var(--color-error)"
}

// ── Filtry Details ────────────────────────────────────────────────────────

const activeSeverityFilter = ref("all")

const issuesBySeverity = computed(() => {
  const issues = props.report.issues ?? []
  return {
    all:      issues.length,
    critical: issues.filter(i => i.severity === "critical").length,
    major:    issues.filter(i => i.severity === "major").length,
    minor:    issues.filter(i => i.severity === "minor").length,
  }
})

const severityFilters = computed(() => [
  { value: "all",      label: "Wszystkie",  count: issuesBySeverity.value.all },
  { value: "critical", label: "Krytyczne",  count: issuesBySeverity.value.critical },
  { value: "major",    label: "Glowne",     count: issuesBySeverity.value.major },
  { value: "minor",    label: "Drobne",     count: issuesBySeverity.value.minor },
])

const filteredIssues = computed(() => {
  const issues = props.report.issues ?? []
  if (activeSeverityFilter.value === "all") return issues
  return issues.filter(i => i.severity === activeSeverityFilter.value)
})

// ── Statistics ────────────────────────────────────────────────────────────

/** Grupowanie problemow wg kryterium WCAG */
const criteriaStats = computed(() => {
  const map = new Map()
  ;(props.report.issues ?? []).forEach(issue => {
    const key = issue.wcag_criterion
    if (map.has(key)) {
      map.get(key).count++
    } else {
      map.set(key, { criterion: key, severity: issue.severity, count: 1 })
    }
  })
  return [...map.values()].sort((a, b) => b.count - a.count)
})

/** Grupowanie problemow wg tagu HTML */
const elementStats = computed(() => {
  const map = new Map()
  ;(props.report.issues ?? []).forEach(issue => {
    ;(issue.affected_elements ?? []).forEach(el => {
      const match = (el.html_snippet || el.html || "").match(/^<(\w+)/)
      const tag = match ? `<${match[1]}>` : "<unknown>"
      map.set(tag, (map.get(tag) || 0) + 1)
    })
  })
  return [...map.entries()]
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const maxElementCount = computed(() =>
  Math.max(...elementStats.value.map(e => e.count), 1)
)

// ── Export formats ────────────────────────────────────────────────────────

const exportFormats = [
  { value: "pdf",  label: "PDF",  icon: "📄" },
  { value: "html", label: "HTML", icon: "🌐" },
  { value: "json", label: "JSON", icon: "📋" },
]

// ── Helpers ───────────────────────────────────────────────────────────────

const formatDate = (dateString) => {
  if (!dateString) return "brak daty"
  return new Date(dateString).toLocaleDateString("pl-PL", {
    year:  "numeric",
    month: "long",
    day:   "numeric",
    hour:  "2-digit",
    minute:"2-digit",
  })
}
</script>

<style scoped>
/* ============================================================
   WRAPPER
============================================================ */

.report-viewer {
  background-color: var(--color-background);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

/* ============================================================
   NAGLOWEK
============================================================ */

.report-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  background-color: var(--color-background-alt);
}

.report-header__meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-md);
}

.report-header__title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  word-break: break-all;
}

.report-header__icon {
  flex-shrink: 0;
}

.report-header__details {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

.report-header__date {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.report-header__status {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: 2px var(--spacing-sm);
  border-radius: var(--radius-full);
  text-transform: uppercase;
}

.report-header__status--done       { background: var(--color-success-light); color: var(--color-success); }
.report-header__status--processing { background: var(--color-info-light);    color: var(--color-info); }
.report-header__status--error      { background: var(--color-error-light);   color: var(--color-error); }
.report-header__status--pending    { background: var(--color-background-alt); color: var(--color-text-secondary); }

/* Pasek compliance */
.compliance-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.compliance-bar__track {
  flex: 1;
  height: 8px;
  background-color: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.compliance-bar__fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
}

.compliance-bar__label {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  min-width: 48px;
  text-align: right;
}

.combined-report {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-primary-light);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

/* ============================================================
   TABLIST (WCAG 4.1.2)
============================================================ */

.report-tabs {
  display: flex;
  border-bottom: 2px solid var(--color-border-light);
  background-color: var(--color-background-alt);
  padding: 0 var(--spacing-md);
}

.report-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md) var(--spacing-md);
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  white-space: nowrap;
  transition:
    color            var(--transition-fast),
    border-color     var(--transition-fast),
    background-color var(--transition-fast);
}

.report-tab:hover {
  color: var(--color-primary);
  background-color: var(--color-primary-light);
}

/* WCAG 2.4.7 — focus-visible ✅ */
.report-tab:focus-visible {
  outline: var(--focus-outline);
  outline-offset: -2px;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}

.report-tab--active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.report-tab__icon { font-size: 1em; }

.report-tab__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background-color: var(--color-border-light);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
}

.report-tab--active .report-tab__badge {
  background-color: var(--color-primary);
  color: white;
}

/* ============================================================
   TAB PANEL (wspolny)
============================================================ */

.report-panel {
  padding: var(--spacing-lg);
  min-height: 300px;
}

.report-panel:focus {
  outline: none;
}

.report-panel:focus-visible {
  outline: var(--focus-outline);
  outline-offset: -4px;
}

/* ============================================================
   SUMMARY — statystyki
============================================================ */

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.stat-card {
  padding: var(--spacing-lg);
  background-color: var(--color-background-alt);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  text-align: center;
}

.stat-card__value {
  font-size: var(--font-size-5xl);
  font-weight: var(--font-weight-bold);
  line-height: 1;
  margin-bottom: var(--spacing-xs);
}

.stat-card__unit {
  font-size: var(--font-size-2xl);
}

.stat-card__value--critical { color: var(--color-error); }
.stat-card__value--major    { color: var(--color-warning); }
.stat-card__value--minor    { color: var(--color-info); }
.stat-card__value--passed   { color: var(--color-success); }

.stat-card__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.stat-card__sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

/* Filary WCAG */
.section-subheading {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  margin-top: 0;
}

.pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.pillar-card {
  padding: var(--spacing-md);
  background: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
}

.pillar-card__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.pillar-card__num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pillar-card__name {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.pillar-card__bar {
  height: 6px;
  background: var(--color-background-alt);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--spacing-xs);
}

.pillar-card__fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
}

.pillar-card__score {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
}

/* ============================================================
   DETAILS — toolbar i filtry
============================================================ */

.details-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-lg);
}

.details-toolbar__heading {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.details-toolbar__count {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  color: var(--color-text-secondary);
}

/* Filtry */
.filters {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: var(--color-background);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }

.filter-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

.filter-btn--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.filter-btn__count {
  font-size: var(--font-size-xs);
  opacity: 0.75;
}

/* Brak bledow */
.no-issues {
  text-align: center;
  padding: var(--spacing-3xl) var(--spacing-xl);
  color: var(--color-text-secondary);
}

.no-issues__icon { font-size: 3rem; display: block; margin-bottom: var(--spacing-md); }
.no-issues__text { font-size: var(--font-size-lg); }

/* Lista bledow */
.issues-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* ============================================================
   STATISTICS — tabela i slupki
============================================================ */

.stat-section {
  margin-bottom: var(--spacing-xl);
}

.criteria-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.criteria-table th {
  background: var(--color-background-alt);
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  border-bottom: 2px solid var(--color-border-light);
}

.criteria-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
  vertical-align: middle;
}

.criteria-table tr:hover td {
  background: var(--color-primary-light);
}

.text-right { text-align: right !important; }

.severity-badge {
  display: inline-flex;
  padding: 2px var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
}

.severity-badge--critical { background: var(--color-error-light);   color: var(--color-error); }
.severity-badge--major    { background: var(--color-warning-light);  color: var(--color-warning); }
.severity-badge--minor    { background: var(--color-info-light);     color: var(--color-info); }

/* Element stats */
.element-stats {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.element-stat {
  display: grid;
  grid-template-columns: 80px 1fr 40px;
  align-items: center;
  gap: var(--spacing-sm);
}

.element-stat__tag {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  color: var(--color-primary);
}

.element-stat__bar {
  height: 8px;
  background: var(--color-background-alt);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.element-stat__fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
}

.element-stat__count {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-align: right;
  color: var(--color-text-secondary);
}

/* Export */
.export-buttons {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.export-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  font-family: var(--font-family-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
  background: var(--color-background);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.export-btn:hover {
  background: var(--color-primary);
  color: white;
}

.export-btn:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
}

/* ============================================================
   SR-ONLY
============================================================ */

.sr-only {
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
   RESPONSYWNOSC
============================================================ */

@media (max-width: 639px) {
  .report-header__meta { flex-direction: column; }
  .report-tabs { padding: 0; overflow-x: auto; }
  .report-tab  { padding: var(--spacing-sm); font-size: var(--font-size-xs); }
  .stats-grid  { grid-template-columns: repeat(2, 1fr); }
  .report-panel { padding: var(--spacing-md); }
  .details-toolbar { flex-direction: column; }
  .element-stat { grid-template-columns: 60px 1fr 30px; }
}
</style>
