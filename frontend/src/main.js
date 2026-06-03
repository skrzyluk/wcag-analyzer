/**
 * main.js — Punkt startowy aplikacji Vue.js 3
 * Projekt: WCAG 2.1 AA Analyzer
 */

import { createApp }   from 'vue'
import { createPinia } from 'pinia'
import { router }      from '@/router'

// --- Style globalne (kolejność importu ma znaczenie) ---
import './styles/variables.css'   // 1. CSS custom properties (design tokens)
import './styles/main.css'        // 2. Reset + globalne style
import './styles/utilities.css'   // 3. Klasy pomocnicze

// --- Root Component ---
import App from './App.vue'

// --- Tworzenie aplikacji ---
const app   = createApp(App)
const pinia = createPinia()

// --- Pluginy ---
app.use(pinia)
app.use(router)

// --- Montowanie ---
app.mount('#app')
