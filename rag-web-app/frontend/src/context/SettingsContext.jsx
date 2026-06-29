import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const SettingsContext = createContext(null)

const DEFAULTS = {
  // Apparence — défaut validé : sombre + accent bleu
  theme:  'dark',      // 'dark' | 'light'
  accent: 'blue',      // indigo | emerald | blue | violet | rose
  fontSize: 'base',    // 'sm' | 'base' | 'lg'
  // Préférences de chat
  defaultCourse:  '',
  defaultBackend: 'lmstudio',
  defaultModel:   '',
  temperature:    0.3,
  sendOnEnter:    true,
  _v: 3,
}

const STORAGE_KEY = 'app_settings'
// Incrémenté lors de la refonte visuelle : ré-applique une fois le thème/accent
// par défaut aux utilisateurs ayant d'anciens réglages, sans perdre leurs autres
// préférences (cours, modèle, etc.).
const APPEARANCE_VERSION = 3

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULTS }
    const stored = JSON.parse(raw)
    const merged = { ...DEFAULTS, ...stored }
    if (stored._v !== APPEARANCE_VERSION) {
      merged.theme = DEFAULTS.theme
      merged.accent = DEFAULTS.accent
      merged._v = APPEARANCE_VERSION
    }
    return merged
  } catch {
    return { ...DEFAULTS, _v: APPEARANCE_VERSION }
  }
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(load)

  // Applique le thème / l'accent / la taille de police au <html> et persiste.
  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', settings.theme)
    root.setAttribute('data-accent', settings.accent)
    root.style.fontSize = settings.fontSize === 'sm' ? '14px'
                        : settings.fontSize === 'lg' ? '18px' : '16px'
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  }, [settings])

  const update = useCallback((patch) => {
    setSettings(s => ({ ...s, ...patch }))
  }, [])

  const reset = useCallback(() => setSettings({ ...DEFAULTS }), [])

  const toggleTheme = useCallback(() => {
    setSettings(s => ({ ...s, theme: s.theme === 'dark' ? 'light' : 'dark' }))
  }, [])

  return (
    <SettingsContext.Provider value={{ settings, update, reset, toggleTheme }}>
      {children}
    </SettingsContext.Provider>
  )
}

export const useSettings = () => useContext(SettingsContext)

export const ACCENTS = [
  { id: 'indigo',  label: 'Indigo',  swatch: '#6366f1' },
  { id: 'emerald', label: 'Émeraude', swatch: '#10b981' },
  { id: 'blue',    label: 'Bleu',    swatch: '#3b82f6' },
  { id: 'violet',  label: 'Violet',  swatch: '#8b5cf6' },
  { id: 'rose',    label: 'Rose',    swatch: '#f43f5e' },
]
