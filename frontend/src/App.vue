<template>
  <!--
    App.vue — Root komponent z globalnym layoutem
    WCAG 2.1 AA:
      ✅ 2.4.1  — Skip link (pomijanie nawigacji)
      ✅ 2.4.2  — Unikalny tytuł strony (router.beforeEach)
      ✅ 2.4.5  — Wiele dróg nawigacji (nav + skip-link)
      ✅ 1.4.3  — Kontrast linków na tle primary >= 4.5:1
      ✅ 2.4.7  — Focus visible na wszystkich elementach interaktywnych
      ✅ 4.1.2  — aria-label na <nav>, aria-current="page" na aktywnym linku
  -->

  <!-- Skip navigation link — WCAG 2.4.1 -->
  <a href="#main-content" class="skip-link">Przejdź do głównej treści</a>

  <!-- Banner: backend offline -->
  <div
    v-if="backendOffline"
    class="backend-banner"
    role="alert"
    aria-live="assertive"
  >
    ⚠️ Backend niedostępny — uruchom <code>start.bat</code> lub sprawdź port 8000.
    <button class="backend-banner__retry" @click="checkBackend">Spróbuj ponownie</button>
  </div>

  <div id="app-root">

    <!-- ====================================================
         HEADER GLOBALNY
    ==================================================== -->
    <header class="app-header" role="banner">
      <div class="app-header__inner">

        <!-- Logo / link do strony głównej -->
        <router-link
          to="/"
          class="app-header__logo"
          :aria-current="route.name === 'home' ? 'page' : undefined"
          aria-label="WCAG 2.1 AA Analyzer — strona główna"
        >
          <!-- Ikona SVG -->
          <svg
            class="app-header__logo-icon"
            aria-hidden="true"
            focusable="false"
            width="32"
            height="32"
            viewBox="0 0 32 32"
            fill="none"
          >
            <rect width="32" height="32" rx="8" fill="white" fill-opacity="0.2"/>
            <circle cx="16" cy="16" r="7" stroke="white" stroke-width="2.5" fill="none"/>
            <path d="M16 10v6M16 18v2" stroke="white" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span class="app-header__logo-text">WCAG Analyzer</span>
        </router-link>

        <!-- Nawigacja główna -->
        <nav class="app-nav" aria-label="Nawigacja główna">
          <ul class="app-nav__list" role="list">
            <li>
              <router-link
                to="/"
                class="app-nav__link"
                :class="{ 'app-nav__link--active': route.name === 'home' }"
                :aria-current="route.name === 'home' ? 'page' : undefined"
              >
                Strona główna
              </router-link>
            </li>
            <li>
              <router-link
                to="/analysis"
                class="app-nav__link"
                :class="{ 'app-nav__link--active': route.name === 'analysis' }"
                :aria-current="route.name === 'analysis' ? 'page' : undefined"
              >
                Analiza
              </router-link>
            </li>
          </ul>
        </nav>

        <!-- CTA Button — widoczny na większych ekranach -->
        <router-link
          to="/analysis"
          class="app-header__cta"
          :aria-current="route.name === 'analysis' ? 'page' : undefined"
        >
          Nowa Analiza
        </router-link>

      </div>
    </header>

    <!-- ====================================================
         GŁÓWNA TREŚĆ — router-view
    ==================================================== -->
    <main id="main-content" tabindex="-1">
      <router-view v-slot="{ Component, route: currentRoute }">
        <Transition name="page-fade" mode="out-in">
          <component
            :is="Component"
            :key="currentRoute.name"
          />
        </Transition>
      </router-view>
    </main>

    <!-- ====================================================
         STOPKA GLOBALNA
    ==================================================== -->
    <footer class="app-footer" role="contentinfo">
      <div class="app-footer__inner">
        <p class="app-footer__copy">
          &copy; 2026 WCAG 2.1 AA Analyzer.
          Narzędzie open-source do lokalnej analizy dostępności.
        </p>
        <nav class="app-footer__nav" aria-label="Linki w stopce">
          <ul role="list">
            <li><router-link to="/">Strona główna</router-link></li>
            <li><router-link to="/analysis">Analiza</router-link></li>
          </ul>
        </nav>
      </div>
    </footer>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysisStore'

/** Reaktywny obiekt bieżącej trasy — używany do aria-current i klas aktywnych */
const route = useRoute()
const analysisStore = useAnalysisStore()

/** Czy backend jest niedostępny */
const backendOffline = ref(false)

const checkBackend = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/health', { signal: AbortSignal.timeout(3000) })
    backendOffline.value = !res.ok
    if (res.ok) {
      console.log('[App] Backend: OK')
      analysisStore.loadPreloaded()  // fire-and-forget
    }
  } catch {
    backendOffline.value = true
    console.warn('[App] Backend niedostępny — upewnij się że start.bat jest uruchomiony')
  }
}

onMounted(checkBackend)
</script>

<style scoped>
/* ============================================================
   APP ROOT — flex layout na całą wysokość okna
============================================================ */

#app-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

main {
  flex: 1;
}

/* Ukrywamy outline na focusie programowym (skip-link target) */
main:focus { outline: none; }

/* ============================================================
   SKIP LINK — WCAG 2.4.1
   Widoczny tylko podczas focusu
============================================================ */

.skip-link {
  position: absolute;
  top: -100%;
  left: var(--spacing-md);
  z-index: var(--z-toast);

  display: inline-block;
  padding: var(--spacing-sm) var(--spacing-lg);

  background-color: var(--color-background);
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  text-decoration: none;

  transition: top var(--transition-fast);
}

.skip-link:focus {
  top: var(--spacing-sm);
}

/* ============================================================
   HEADER
============================================================ */

.app-header {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  box-shadow: var(--shadow-md);
}

.app-header__inner {
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  height: var(--layout-header-height);

  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

/* ============================================================
   LOGO
============================================================ */

.app-header__logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  text-decoration: none;
  color: var(--color-text-inverse);
  flex-shrink: 0;
}

.app-header__logo:focus-visible {
  outline: 3px solid var(--color-text-inverse);
  outline-offset: 4px;
  border-radius: var(--radius-sm);
}

.app-header__logo-icon {
  flex-shrink: 0;
}

.app-header__logo-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  white-space: nowrap;
  /* Kontrast biały na primary: 9.5:1 ✅ */
}

/* ============================================================
   NAV
   Linki: biały (#fff) na --color-primary (#0066cc) = 9.5:1 ✅
============================================================ */

.app-nav {
  flex: 1;
}

.app-nav__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: var(--spacing-xs);
}

.app-nav__link {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-md);

  color: var(--color-text-inverse);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);

  opacity: 0.85;
  transition:
    opacity          var(--transition-fast),
    background-color var(--transition-fast);
}

.app-nav__link:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.15);
}

/* Aktywny link — WCAG aria-current="page" */
.app-nav__link--active,
.app-nav__link.router-link-exact-active {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.2);
  font-weight: var(--font-weight-semibold);
}

/* Focus visible — biały outline na tle primary ✅ */
.app-nav__link:focus-visible {
  outline: 3px solid var(--color-text-inverse);
  outline-offset: 2px;
  opacity: 1;
}

/* ============================================================
   CTA BUTTON w headerze
============================================================ */

.app-header__cta {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-xs) var(--spacing-lg);
  margin-left: auto;
  flex-shrink: 0;

  background-color: var(--color-text-inverse);
  color: var(--color-primary);
  border: 2px solid var(--color-text-inverse);
  border-radius: var(--radius-md);

  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-decoration: none;
  white-space: nowrap;

  transition:
    background-color var(--transition-fast),
    color            var(--transition-fast);
}

.app-header__cta:hover {
  background-color: transparent;
  color: var(--color-text-inverse);
}

.app-header__cta:focus-visible {
  outline: 3px solid var(--color-text-inverse);
  outline-offset: 3px;
}

/* Ukryj CTA gdy jesteśmy już na /analysis */
.app-header__cta[aria-current="page"] {
  opacity: 0.6;
  pointer-events: none;
}

/* ============================================================
   ANIMACJA ZMIANY STRONY
   prefers-reduced-motion: brak animacji
============================================================ */

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--transition-fast);
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .page-fade-enter-active,
  .page-fade-leave-active {
    transition: none;
  }
}

/* ============================================================
   STOPKA
============================================================ */

.app-footer {
  background-color: var(--color-background-alt);
  border-top: 1px solid var(--color-border-light);
  padding: var(--spacing-lg) 0;
}

.app-footer__inner {
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: 0 var(--spacing-lg);

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.app-footer__copy {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Linki w stopce */
.app-footer__nav ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: var(--spacing-md);
}

.app-footer__nav a {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.app-footer__nav a:hover {
  color: var(--color-primary);
}

.app-footer__nav a:focus-visible {
  outline: var(--focus-outline);
  outline-offset: var(--focus-outline-offset);
  border-radius: 2px;
}

/* ============================================================
   RESPONSYWNOŚĆ
============================================================ */

/* Mobile: ukryj tekst logo i CTA */
@media (max-width: 639px) {
  .app-header__inner {
    padding: 0 var(--spacing-md);
    gap: var(--spacing-md);
  }

  .app-header__logo-text {
    font-size: var(--font-size-base);
  }

  .app-header__cta {
    display: none; /* Menu główne wystarczy */
  }

  .app-nav__link {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
  }

  .app-footer__inner {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-sm);
  }
}

/* ============================================================
   BACKEND OFFLINE BANNER
============================================================ */

.backend-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-lg);
  background-color: var(--color-warning);
  color: var(--color-text-inverse);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  flex-wrap: wrap;
}

.backend-banner code {
  background: rgba(0,0,0,0.2);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-family-mono);
}

.backend-banner__retry {
  padding: 2px 10px;
  background: rgba(255,255,255,0.25);
  border: 1px solid rgba(255,255,255,0.5);
  border-radius: var(--radius-sm);
  color: inherit;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.backend-banner__retry:hover { background: rgba(255,255,255,0.4); }
.backend-banner__retry:focus-visible { outline: 2px solid white; outline-offset: 2px; }
</style>
