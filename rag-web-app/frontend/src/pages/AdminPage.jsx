import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Users, Cpu, BarChart3, Trash2, Edit2, Plus, Shield, CheckCircle, XCircle, Save, X, BookOpen, Upload, Loader2, AlertCircle } from 'lucide-react'
import api from '../services/api'

const TABS = [
  { id: 'stats',   label: 'Tableau de bord', icon: BarChart3 },
  { id: 'users',   label: 'Utilisateurs',    icon: Users     },
  { id: 'llms',    label: 'Modèles LLM',     icon: Cpu       },
  { id: 'courses', label: 'Cours',           icon: BookOpen  },
]

function StatCard({ label, value, color = 'indigo', delay = 1 }) {
  const colors = { indigo: 'bg-indigo-500/10 text-indigo-400', emerald: 'bg-emerald-500/10 text-emerald-400', blue: 'bg-blue-500/10 text-blue-400', purple: 'bg-purple-500/10 text-purple-400', amber: 'bg-amber-500/10 text-amber-400' }
  return (
    <div className={`lift rounded-xl p-5 animate-fade-up delay-${delay} ${colors[color]}`}>
      <p className="text-sm opacity-70 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}

export default function AdminPage() {
  const navigate = useNavigate()
  const [tab, setTab]     = useState('stats')
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [llms,  setLlms]  = useState([])
  const [editLlm, setEditLlm]   = useState(null)
  const [newLlm, setNewLlm]     = useState(null)
  const [llmForm, setLlmForm]   = useState({})

  const [courses, setCourses]     = useState([])
  const [courseName, setCourseName] = useState('')
  const [pdfFile, setPdfFile]     = useState(null)
  const [uploadJob, setUploadJob] = useState(null) // { jobId, status, step, error }
  const fileInputRef = useRef(null)
  const pollRef = useRef(null)

  const load = () => {
    api.get('/admin/stats').then(r => setStats(r.data)).catch(() => {})
    api.get('/admin/users').then(r => setUsers(r.data)).catch(() => {})
    api.get('/admin/llms').then(r => setLlms(r.data)).catch(() => {})
    api.get('/admin/courses').then(r => setCourses(r.data)).catch(() => {})
  }
  useEffect(load, [])
  useEffect(() => () => clearInterval(pollRef.current), [])

  const handleErr = (e) => alert(e.response?.data?.error || 'Action impossible.')

  const toggleUser = async (u) => {
    try { await api.put(`/admin/users/${u.id}`, { active: !u.active, role: u.role }); load() }
    catch (e) { handleErr(e) }
  }
  const changeRole = async (u, role) => {
    try { await api.put(`/admin/users/${u.id}`, { active: u.active, role }); load() }
    catch (e) { handleErr(e) }
  }
  const deleteUser = async (id) => {
    if (!confirm('Supprimer cet utilisateur ?')) return
    try { await api.delete(`/admin/users/${id}`); load() }
    catch (e) { handleErr(e) }
  }

  const saveLlm = async () => {
    if (!llmForm.name?.trim() || !llmForm.model?.trim()) { alert('Nom et modèle requis.'); return }
    try {
      if (editLlm?.id) await api.put(`/admin/llms/${editLlm.id}`, llmForm)
      else await api.post('/admin/llms', llmForm)
      setEditLlm(null); setNewLlm(null); load()
    } catch (e) { handleErr(e) }
  }
  const deleteLlm = async (id) => {
    if (!confirm('Supprimer ce modèle ?')) return
    try { await api.delete(`/admin/llms/${id}`); load() }
    catch (e) { handleErr(e) }
  }

  const uploadCourse = async () => {
    const name = courseName.trim()
    if (!name) { alert('Indiquez un nom de cours.'); return }
    if (!/^[A-Za-z0-9_-]{1,80}$/.test(name)) { alert('Le nom ne doit contenir que lettres, chiffres, "_" et "-".'); return }
    if (!pdfFile) { alert('Choisissez un fichier PDF.'); return }

    const form = new FormData()
    form.append('courseName', name)
    form.append('file', pdfFile)

    try {
      // Ne pas fixer Content-Type ici : le navigateur doit calculer lui-même
      // le boundary du multipart/form-data à partir du FormData.
      const { data } = await api.post('/admin/courses/upload', form)
      setUploadJob({ jobId: data.job_id, status: 'pending', step: 'en attente', error: null })
      pollRef.current = setInterval(() => pollJob(data.job_id), 2000)
    } catch (e) { handleErr(e) }
  }

  const pollJob = async (jobId) => {
    try {
      const { data } = await api.get(`/admin/courses/jobs/${jobId}`)
      setUploadJob({ jobId, status: data.status, step: data.step, error: data.error })
      if (data.status === 'done' || data.status === 'error') {
        clearInterval(pollRef.current)
        if (data.status === 'done') {
          setCourseName(''); setPdfFile(null)
          if (fileInputRef.current) fileInputRef.current.value = ''
          load()
        }
      }
    } catch {
      clearInterval(pollRef.current)
      setUploadJob(j => j && ({ ...j, status: 'error', error: 'Connexion au job perdue.' }))
    }
  }

  const deleteCourse = async (name) => {
    if (!confirm(`Supprimer le cours "${name}" et son index ?`)) return
    try { await api.delete(`/admin/courses/${name}`); load() }
    catch (e) { handleErr(e) }
  }

  const openEdit = (llm) => { setEditLlm(llm); setLlmForm({...llm, apiKey: ''}); setNewLlm(null) }
  const openNew  = ()    => { setNewLlm(true); setLlmForm({ name: '', backend: 'lmstudio', model: '', baseUrl: '', temperature: 0.3, maxTokens: 2048, enabled: true, isDefault: false }); setEditLlm(null) }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-50 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <Shield className="w-6 h-6 text-indigo-400" />
        <h1 className="text-lg font-semibold text-gray-50">Administration</h1>
      </div>

      <div className="flex h-[calc(100vh-65px)]">
        {/* Side nav */}
        <nav className="w-52 bg-gray-900 border-r border-gray-800 p-3 space-y-1 flex-shrink-0">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                tab === t.id ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-50'
              }`}>
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">

          {/* Stats */}
          {tab === 'stats' && stats && (
            <div>
              <h2 className="text-xl font-semibold text-gray-50 mb-6">Tableau de bord</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <StatCard label="Utilisateurs" value={stats.totalUsers} color="indigo" delay={1} />
                <StatCard label="Actifs" value={stats.activeUsers} color="emerald" delay={2} />
                <StatCard label="Conversations" value={stats.totalConversations} color="blue" delay={3} />
                <StatCard label="Messages" value={stats.totalMessages} color="purple" delay={4} />
                <StatCard label="LLMs actifs" value={stats.enabledLlms} color="amber" delay={5} />
              </div>
            </div>
          )}

          {/* Users */}
          {tab === 'users' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-50 mb-6">Utilisateurs ({users.length})</h2>
              <div className="space-y-2">
                {users.map(u => (
                  <div key={u.id} className="card lift flex items-center gap-4">
                    <div className="w-9 h-9 bg-indigo-600/30 rounded-full flex items-center justify-center text-indigo-300 font-semibold text-sm flex-shrink-0">
                      {u.username[0].toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-50 font-medium truncate">{u.username}</p>
                      <p className="text-gray-500 text-xs truncate">{u.email} · {u.conversationCount} conv.</p>
                    </div>
                    <select value={u.role} onChange={e => changeRole(u, e.target.value)}
                      className="bg-gray-800 border border-gray-700 text-gray-300 text-xs rounded px-2 py-1">
                      <option value="USER">USER</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                    <button onClick={() => toggleUser(u)} title={u.active ? 'Désactiver' : 'Activer'}
                      className={`transition-colors ${u.active ? 'text-emerald-400 hover:text-red-400' : 'text-gray-600 hover:text-emerald-400'}`}>
                      {u.active ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                    </button>
                    <button onClick={() => deleteUser(u.id)} className="text-gray-600 hover:text-red-400 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* LLMs */}
          {tab === 'llms' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-50">Modèles LLM ({llms.length})</h2>
                <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm">
                  <Plus className="w-4 h-4" /> Ajouter
                </button>
              </div>

              {(newLlm || editLlm) && (
                <div className="card mb-4 border border-indigo-500/40">
                  <h3 className="text-gray-50 font-medium mb-4">{editLlm ? 'Modifier' : 'Nouveau modèle'}</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <label className="text-xs text-gray-400 mb-1 block">Nom affiché</label>
                      <input className="input text-sm" value={llmForm.name || ''} onChange={e => setLlmForm(f => ({...f, name: e.target.value}))} placeholder="LM Studio — gemma3:4b" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Backend</label>
                      <select className="input text-sm" value={llmForm.backend || 'lmstudio'} onChange={e => setLlmForm(f => ({...f, backend: e.target.value}))}>
                        <option value="lmstudio">LM Studio</option>
                        <option value="ollama">Ollama</option>
                        <option value="nvidia">NVIDIA</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Modèle</label>
                      <input className="input text-sm" value={llmForm.model || ''} onChange={e => setLlmForm(f => ({...f, model: e.target.value}))} placeholder="gemma3:4b" />
                    </div>
                    <div className="col-span-2">
                      <label className="text-xs text-gray-400 mb-1 block">URL de base (optionnel)</label>
                      <input className="input text-sm" value={llmForm.baseUrl || ''} onChange={e => setLlmForm(f => ({...f, baseUrl: e.target.value}))} placeholder="http://localhost:1234/v1" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Température ({(llmForm.temperature ?? 0.3)})</label>
                      <input type="range" min="0" max="1" step="0.1"
                        value={llmForm.temperature ?? 0.3}
                        onChange={e => setLlmForm(f => ({...f, temperature: parseFloat(e.target.value)}))}
                        className="w-full accent-indigo-500" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 mb-1 block">Max tokens</label>
                      <input className="input text-sm" type="number" min="128" max="8192" step="128"
                        value={llmForm.maxTokens ?? 2048}
                        onChange={e => setLlmForm(f => ({...f, maxTokens: parseInt(e.target.value) || 2048}))} />
                    </div>
                    {llmForm.backend === 'nvidia' && (
                      <div className="col-span-2">
                        <label className="text-xs text-gray-400 mb-1 block">Clé API {editLlm && <span className="text-gray-600">(laisser vide pour conserver)</span>}</label>
                        <input className="input text-sm" type="password" value={llmForm.apiKey || ''} onChange={e => setLlmForm(f => ({...f, apiKey: e.target.value}))} placeholder="nvapi-…" />
                      </div>
                    )}
                    <label className="flex items-center gap-2 cursor-pointer col-span-2">
                      <input type="checkbox" checked={llmForm.enabled ?? true} onChange={e => setLlmForm(f => ({...f, enabled: e.target.checked}))} className="rounded" />
                      <span className="text-sm text-gray-300">Activé</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer col-span-2">
                      <input type="checkbox" checked={llmForm.isDefault ?? false} onChange={e => setLlmForm(f => ({...f, isDefault: e.target.checked}))} className="rounded" />
                      <span className="text-sm text-gray-300">Modèle par défaut</span>
                    </label>
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button onClick={saveLlm} className="btn-primary flex items-center gap-1.5 text-sm"><Save className="w-3.5 h-3.5" /> Sauvegarder</button>
                    <button onClick={() => { setEditLlm(null); setNewLlm(null) }} className="btn-ghost text-sm flex items-center gap-1.5"><X className="w-3.5 h-3.5" /> Annuler</button>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                {llms.map(llm => (
                  <div key={llm.id} className={`card lift flex items-center gap-4 ${!llm.enabled ? 'opacity-50' : ''}`}>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-gray-50 font-medium truncate">{llm.name}</p>
                        {llm.isDefault && <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full">défaut</span>}
                        {!llm.enabled && <span className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded-full">désactivé</span>}
                      </div>
                      <p className="text-gray-500 text-xs mt-0.5">{llm.backend} · {llm.model} · temp {llm.temperature} · {llm.maxTokens} tok{llm.baseUrl ? ` · ${llm.baseUrl}` : ''}</p>
                    </div>
                    <button onClick={() => openEdit(llm)} className="text-gray-500 hover:text-gray-50 transition-colors"><Edit2 className="w-4 h-4" /></button>
                    <button onClick={() => deleteLlm(llm.id)} className="text-gray-500 hover:text-red-400 transition-colors"><Trash2 className="w-4 h-4" /></button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cours */}
          {tab === 'courses' && (
            <div>
              <h2 className="text-xl font-semibold text-gray-50 mb-6">Cours ({courses.length})</h2>

              <div className="card mb-4 border border-indigo-500/40">
                <h3 className="text-gray-50 font-medium mb-4">Ajouter un cours (PDF)</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="text-xs text-gray-400 mb-1 block">Nom du cours</label>
                    <input className="input text-sm" value={courseName}
                      onChange={e => setCourseName(e.target.value)}
                      placeholder="ex: Probabilites_cours" disabled={uploadJob?.status === 'running' || uploadJob?.status === 'pending'} />
                    <p className="text-xs text-gray-600 mt-1">Lettres, chiffres, "_" et "-" uniquement.</p>
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs text-gray-400 mb-1 block">Fichier PDF</label>
                    <input ref={fileInputRef} type="file" accept="application/pdf"
                      onChange={e => setPdfFile(e.target.files?.[0] || null)}
                      disabled={uploadJob?.status === 'running' || uploadJob?.status === 'pending'}
                      className="block w-full text-sm text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-gray-800 file:text-gray-300 hover:file:bg-gray-700 file:cursor-pointer" />
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-4">
                  <button onClick={uploadCourse}
                    disabled={uploadJob?.status === 'running' || uploadJob?.status === 'pending'}
                    className="btn-primary flex items-center gap-1.5 text-sm disabled:opacity-50">
                    <Upload className="w-3.5 h-3.5" /> Lancer l'indexation
                  </button>

                  {uploadJob && (uploadJob.status === 'pending' || uploadJob.status === 'running') && (
                    <span className="flex items-center gap-2 text-sm text-indigo-300">
                      <Loader2 className="w-4 h-4 animate-spin" /> {uploadJob.step}…
                    </span>
                  )}
                  {uploadJob?.status === 'done' && (
                    <span className="flex items-center gap-2 text-sm text-emerald-400">
                      <CheckCircle className="w-4 h-4" /> Cours indexé avec succès.
                    </span>
                  )}
                  {uploadJob?.status === 'error' && (
                    <span className="flex items-center gap-2 text-sm text-red-400">
                      <AlertCircle className="w-4 h-4" /> {uploadJob.error || 'Échec de l\'indexation.'}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-3">
                  L'extraction (analyse LLM du PDF) puis l'indexation (embeddings + ChromaDB) peuvent
                  prendre plusieurs minutes selon la taille du document.
                </p>
              </div>

              <div className="space-y-2">
                {courses.length === 0 && (
                  <p className="text-gray-600 text-sm">Aucun cours indexé pour le moment.</p>
                )}
                {courses.map(c => (
                  <div key={c} className="card lift flex items-center gap-4">
                    <BookOpen className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                    <p className="flex-1 text-gray-50 font-medium truncate">{c.replace(/_/g, ' ')}</p>
                    <button onClick={() => deleteCourse(c)} className="text-gray-500 hover:text-red-400 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
