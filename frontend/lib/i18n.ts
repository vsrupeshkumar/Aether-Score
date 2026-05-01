/**
 * Internationalization setup for multi-language support
 * Using next-intl for Next.js App Router
 */

export const locales = ["en", "es", "zh", "ja", "fr"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "en";

export const localeNames: Record<Locale, string> = {
  en: "English",
  es: "EspaÃ±ol",
  zh: "ä¸­æ–‡",
  ja: "æ—¥æœ¬èªž",
  fr: "FranÃ§ais",
};

// Translation keys - in production, these would be in separate JSON files
export const translations: Record<Locale, Record<string, string>> = {
  en: {
    "common.wallet": "Wallet",
    "common.score": "Score",
    "common.loans": "Loans",
    "common.dashboard": "Dashboard",
    "common.settings": "Settings",
    "common.connect": "Connect Wallet",
    "common.disconnect": "Disconnect",
    "score.title": "Credit Score",
    "score.generate": "Generate Score",
    "score.history": "Score History",
    "loans.title": "Loan Management",
    "loans.create": "Create Loan",
    "loans.active": "Active Loans",
    "dashboard.welcome": "Welcome to AETHER-SCORE",
    "dashboard.description": "Your AI-powered credit passport",
  },
  es: {
    "common.wallet": "Cartera",
    "common.score": "PuntuaciÃ³n",
    "common.loans": "PrÃ©stamos",
    "common.dashboard": "Panel",
    "common.settings": "ConfiguraciÃ³n",
    "common.connect": "Conectar Cartera",
    "common.disconnect": "Desconectar",
    "score.title": "PuntuaciÃ³n de CrÃ©dito",
    "score.generate": "Generar PuntuaciÃ³n",
    "score.history": "Historial de PuntuaciÃ³n",
    "loans.title": "GestiÃ³n de PrÃ©stamos",
    "loans.create": "Crear PrÃ©stamo",
    "loans.active": "PrÃ©stamos Activos",
    "dashboard.welcome": "Bienvenido a AETHER-SCORE",
    "dashboard.description": "Tu pasaporte de crÃ©dito impulsado por IA",
  },
  zh: {
    "common.wallet": "é’±åŒ…",
    "common.score": "åˆ†æ•°",
    "common.loans": "è´·æ¬¾",
    "common.dashboard": "ä»ªè¡¨æ¿",
    "common.settings": "è®¾ç½®",
    "common.connect": "è¿žæŽ¥é’±åŒ…",
    "common.disconnect": "æ–­å¼€è¿žæŽ¥",
    "score.title": "ä¿¡ç”¨åˆ†æ•°",
    "score.generate": "ç”Ÿæˆåˆ†æ•°",
    "score.history": "åˆ†æ•°åŽ†å²",
    "loans.title": "è´·æ¬¾ç®¡ç†",
    "loans.create": "åˆ›å»ºè´·æ¬¾",
    "loans.active": "æ´»è·ƒè´·æ¬¾",
    "dashboard.welcome": "æ¬¢è¿Žä½¿ç”¨ AETHER-SCORE",
    "dashboard.description": "æ‚¨çš„ AI é©±åŠ¨çš„ä¿¡ç”¨æŠ¤ç…§",
  },
  ja: {
    "common.wallet": "ã‚¦ã‚©ãƒ¬ãƒƒãƒˆ",
    "common.score": "ã‚¹ã‚³ã‚¢",
    "common.loans": "ãƒ­ãƒ¼ãƒ³",
    "common.dashboard": "ãƒ€ãƒƒã‚·ãƒ¥ãƒœãƒ¼ãƒ‰",
    "common.settings": "è¨­å®š",
    "common.connect": "ã‚¦ã‚©ãƒ¬ãƒƒãƒˆã‚’æŽ¥ç¶š",
    "common.disconnect": "åˆ‡æ–­",
    "score.title": "ä¿¡ç”¨ã‚¹ã‚³ã‚¢",
    "score.generate": "ã‚¹ã‚³ã‚¢ã‚’ç”Ÿæˆ",
    "score.history": "ã‚¹ã‚³ã‚¢å±¥æ­´",
    "loans.title": "ãƒ­ãƒ¼ãƒ³ç®¡ç†",
    "loans.create": "ãƒ­ãƒ¼ãƒ³ã‚’ä½œæˆ",
    "loans.active": "ã‚¢ã‚¯ãƒ†ã‚£ãƒ–ãƒ­ãƒ¼ãƒ³",
    "dashboard.welcome": "AETHER-SCOREã¸ã‚ˆã†ã“ã",
    "dashboard.description": "AI é§†å‹•ã®ä¿¡ç”¨ãƒ‘ã‚¹ãƒãƒ¼ãƒˆ",
  },
  fr: {
    "common.wallet": "Portefeuille",
    "common.score": "Score",
    "common.loans": "PrÃªts",
    "common.dashboard": "Tableau de bord",
    "common.settings": "ParamÃ¨tres",
    "common.connect": "Connecter le portefeuille",
    "common.disconnect": "DÃ©connecter",
    "score.title": "Score de crÃ©dit",
    "score.generate": "GÃ©nÃ©rer le score",
    "score.history": "Historique du score",
    "loans.title": "Gestion des prÃªts",
    "loans.create": "CrÃ©er un prÃªt",
    "loans.active": "PrÃªts actifs",
    "dashboard.welcome": "Bienvenue sur AETHER-SCORE",
    "dashboard.description": "Votre passeport de crÃ©dit alimentÃ© par l'IA",
  },
};

export function getTranslation(locale: Locale, key: string): string {
  return translations[locale]?.[key] || translations[defaultLocale][key] || key;
}

export function useTranslation(locale: Locale = defaultLocale) {
  return (key: string) => getTranslation(locale, key);
}

// Client-side locale management
export const supportedLocales: Locale[] = [...locales];

export function getLocale(): Locale {
  if (typeof window === 'undefined') return defaultLocale;
  const stored = localStorage.getItem('locale') as Locale | null;
  return stored && locales.includes(stored) ? stored : defaultLocale;
}

export function setLocale(locale: Locale): void {
  if (typeof window === 'undefined') return;
  if (locales.includes(locale)) {
    localStorage.setItem('locale', locale);
    window.dispatchEvent(new Event('localechange'));
  }
}

