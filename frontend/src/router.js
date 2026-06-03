/**
 * router.js — Konfiguracja Vue Router 4
 * Projekt: WCAG 2.1 AA Analyzer
 *
 * WCAG 2.4.2 — Każda strona ma unikalny tytuł (document.title)
 * WCAG 2.4.5 — Wiele sposobów nawigacji (nav + skip-link)
 */
import { createRouter, createWebHistory } from 'vue-router'

// Lazy-loaded views — mniejszy initial bundle
const HomeView     = () => import('@/views/HomeView.vue')
const AnalysisView = () => import('@/views/AnalysisView.vue')

/** @type {import('vue-router').RouteRecordRaw[]} */
const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {
      title: 'WCAG 2.1 AA Analyzer — Strona główna',
      description: 'Automatyczna analiza dostępności plików MHTML zgodna z WCAG 2.1 AA.'
    }
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisView,
    meta: {
      title: 'Nowa Analiza — WCAG 2.1 AA Analyzer',
      description: 'Wgraj plik MHTML i uruchom analizę zgodności z WCAG 2.1 AA.'
    }
  },
  {
    // Catch-all — przekierowanie do strony głównej
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: { name: 'home' }
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,

  /**
   * Przywróć scroll na górę przy każdej zmianie trasy.
   * WCAG 2.4.3 — Logiczna kolejność focusu (nowa strona zaczyna się od góry).
   */
  scrollBehavior (to, from, savedPosition) {
    if (savedPosition) {
      // Powrót (przycisk Wstecz) — przywróć poprzednią pozycję
      return savedPosition
    }
    if (to.hash) {
      // Anchor link — przeskocz do sekcji
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0, behavior: 'instant' }
  }
})

/* ============================================================
   GUARD GLOBALNY — document.title + meta description
   WCAG 2.4.2 — Każda strona ma opisowy tytuł
============================================================ */
router.beforeEach((to) => {
  // Tytuł zakładki
  document.title = to.meta.title ?? 'WCAG 2.1 AA Analyzer'

  // Meta description (SEO + screen reader preview)
  const metaDesc = document.querySelector('meta[name="description"]')
  if (metaDesc && to.meta.description) {
    metaDesc.setAttribute('content', to.meta.description)
  }
})
