import { useState, useEffect } from 'react'
import { X, KeyRound, User, Mail, Shield, Palette, SlidersHorizontal, Sun, Moon,
         Check, Type, RotateCcw } from 'lucide-react'
import api from '../services/api'
import { useSettings, ACCENTS } from '../context/SettingsContext'

const TABS = [
  { id: 'profil',  label: 'Profil',      icon: User },
  { id: 'prefs',   label: 'Préférences', icon: SlidersHorizontal },
  { id: 'theme',   label: 'Apparence',   icon: Palette },
]

const FONT_SIZES = [
  { id: 'sm',   label: 'Compact' },
  { id: 'base', label: 'Normal' },
  { id: 'lg',   label: 'Grand' },
]

export default function SettingsModal({ user, onClose }) {
  const { settings, update, reset, toggleTheme } = useSettings()
  const [tab, setTab] = useState('profil')

  const [courses, setCourses] = useState([])
  const [llms, setLlms]       = useState([])

  // Changement de mot de passe
  const [form, setForm] = useState({ currentPassword: '', newPassword: '', confirm: '' })
  const [msg, setMsg]   = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.get('/courses').then(r => setCourses(r.data)).catch(() => {})
    api.get('/llms').then(r => setLlms(r.data)).catch(() => {})
  }, [])

  const submitPassword = async e => {
    e.preventDefault()
    setMsg(null)
    if (form.newPassword !== form.confirm) {
      setMsg({ type: 'err', text: 'Les mots de passe ne correspondent pas.' }); return
    }
    if (form.newPassword.length < 6) {
      setMsg({ type: 'err', text: 'Le nouveau mot de passe doit faire au moins 6 caractères.' }); return
    }
    setBusy(true)
    try {
      await api.post('/auth/change-password', {
        currentPassword: form.currentPassword, newPassword: form.newPassword
      })
      setMsg({ type: 'ok', text: 'Mot de passe modifié avec succès.' })
      setForm({ currentPassword: '', newPassword: '', confirm: '' })
    } catch (err) {
      setMsg({ type: 'err', text: err.response?.data?.error || 'Échec de la modification.' })
    } finally {
      setBusy(false)
    }
  }

  const currentModelValue = `${settings.defaultBackend}|${settings.defaultModel}`
  const onSelectModel = e => {
    const [backend, ...rest] = e.target.value.split('|')
    update({ defaultBackend: backend, defaultModel: rest.join('|') })
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-lg max-h-[90vh] flex flex-col overflow-hidden"
           onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800 flex-shrink-0">
          <h2 className="text-gray-50 font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-400" /> Paramètres
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-50 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-3 pt-3 border-b border-gray-800 flex-shrink-0">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t-lg transition-colors ${
                tab === t.id ? 'bg-gray-800 text-gray-50 border-b-2 border-indigo-500'
                             : 'text-gray-400 hover:text-gray-50'
              }`}>
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-5 space-y-5 overflow-y-auto">

          {/* ---- Profil ---- */}
          {tab === 'profil' && (
            <>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <User className="w-4 h-4 text-gray-500" /> {user?.username}
                </div>
                {user?.email && (
                  <div className="flex items-center gap-2 text-sm text-gray-300">
                    <Mail className="w-4 h-4 text-gray-500" /> {user.email}
                  </div>
                )}
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <Shield className="w-4 h-4 text-gray-500" />
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    user?.role === 'ADMIN' ? 'bg-indigo-500/20 text-indigo-300' : 'bg-gray-700 text-gray-300'
                  }`}>{user?.role}</span>
                </div>
              </div>

              <hr className="border-gray-800" />

              <form onSubmit={submitPassword} className="space-y-3">
                <h3 className="text-sm font-medium text-gray-50 flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-indigo-400" /> Changer le mot de passe
                </h3>
                {msg && (
                  <div className={`rounded-lg px-3 py-2 text-sm border ${
                    msg.type === 'ok'
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : 'bg-red-500/10 border-red-500/30 text-red-400'
                  }`}>{msg.text}</div>
                )}
                <input type="password" className="input text-sm" placeholder="Mot de passe actuel"
                  value={form.currentPassword}
                  onChange={e => setForm(f => ({ ...f, currentPassword: e.target.value }))} required />
                <input type="password" className="input text-sm" placeholder="Nouveau mot de passe"
                  value={form.newPassword}
                  onChange={e => setForm(f => ({ ...f, newPassword: e.target.value }))} required />
                <input type="password" className="input text-sm" placeholder="Confirmer le nouveau mot de passe"
                  value={form.confirm}
                  onChange={e => setForm(f => ({ ...f, confirm: e.target.value }))} required />
                <button type="submit" disabled={busy} className="btn-primary w-full text-sm">
                  {busy ? 'Modification…' : 'Modifier le mot de passe'}
                </button>
              </form>
            </>
          )}

          {/* ---- Préférences de chat ---- */}
          {tab === 'prefs' && (
            <div className="space-y-5">
              <div>
                <label className="text-sm font-medium text-gray-50 block mb-1.5">Cours par défaut</label>
                <select className="input text-sm" value={settings.defaultCourse}
                  onChange={e => update({ defaultCourse: e.target.value })}>
                  <option value="">— Aucun —</option>
                  {courses.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
                </select>
                <p className="text-xs text-gray-500 mt-1">Sélectionné automatiquement à l'ouverture du chat.</p>
              </div>

              {llms.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-50 block mb-1.5">Modèle par défaut</label>
                  <select className="input text-sm" value={currentModelValue} onChange={onSelectModel}>
                    {llms.map(l => <option key={l.id} value={`${l.backend}|${l.model}`}>{l.name}</option>)}
                  </select>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-gray-50 block mb-1.5">
                  Température : <span className="text-indigo-400">{settings.temperature.toFixed(1)}</span>
                </label>
                <input type="range" min="0" max="1" step="0.1" value={settings.temperature}
                  onChange={e => update({ temperature: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-500" />
                <div className="flex justify-between text-xs text-gray-500 mt-0.5">
                  <span>Précis</span><span>Créatif</span>
                </div>
              </div>

              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-gray-300">Envoyer avec <kbd className="px-1.5 py-0.5 bg-gray-800 rounded text-xs">Entrée</kbd></span>
                <input type="checkbox" checked={settings.sendOnEnter}
                  onChange={e => update({ sendOnEnter: e.target.checked })}
                  className="w-4 h-4 accent-indigo-500" />
              </label>
            </div>
          )}

          {/* ---- Apparence ---- */}
          {tab === 'theme' && (
            <div className="space-y-6">
              <div>
                <label className="text-sm font-medium text-gray-50 block mb-2">Thème</label>
                <div className="grid grid-cols-2 gap-3">
                  {[{ id: 'dark', label: 'Sombre', icon: Moon }, { id: 'light', label: 'Clair', icon: Sun }].map(t => (
                    <button key={t.id} onClick={() => update({ theme: t.id })}
                      className={`flex items-center gap-2 justify-center px-4 py-3 rounded-lg border text-sm transition-colors ${
                        settings.theme === t.id
                          ? 'border-indigo-500 bg-indigo-500/10 text-gray-50'
                          : 'border-gray-700 text-gray-400 hover:text-gray-50'
                      }`}>
                      <t.icon className="w-4 h-4" /> {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-50 block mb-2">Couleur d'accent</label>
                <div className="flex gap-3">
                  {ACCENTS.map(a => (
                    <button key={a.id} onClick={() => update({ accent: a.id })} title={a.label}
                      className={`w-9 h-9 rounded-full flex items-center justify-center transition-transform hover:scale-110 ${
                        settings.accent === a.id ? 'ring-2 ring-offset-2 ring-offset-gray-900 ring-gray-300' : ''
                      }`}
                      style={{ backgroundColor: a.swatch }}>
                      {settings.accent === a.id && <Check className="w-4 h-4 text-white" />}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-50 block mb-2 flex items-center gap-2">
                  <Type className="w-4 h-4 text-gray-500" /> Taille du texte
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {FONT_SIZES.map(f => (
                    <button key={f.id} onClick={() => update({ fontSize: f.id })}
                      className={`px-3 py-2 rounded-lg border text-sm transition-colors ${
                        settings.fontSize === f.id
                          ? 'border-indigo-500 bg-indigo-500/10 text-gray-50'
                          : 'border-gray-700 text-gray-400 hover:text-gray-50'
                      }`}>{f.label}</button>
                  ))}
                </div>
              </div>

              <button onClick={reset}
                className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-50 transition-colors">
                <RotateCcw className="w-4 h-4" /> Réinitialiser les paramètres
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
