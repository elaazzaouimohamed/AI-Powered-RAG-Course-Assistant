import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Plus, Trash2, LogOut, Shield, BookOpen, ChevronDown, Loader2,
         Pencil, Check, X, Settings, Square, Copy, CopyCheck, Search, Download, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import { useAuth } from '../context/AuthContext'
import { useSettings } from '../context/SettingsContext'
import api, { refreshAccessToken, API_BASE } from '../services/api'
import SettingsModal from '../components/SettingsModal'

const BACKENDS = [
  { value: 'lmstudio', label: 'LM Studio (GPU)', color: 'text-emerald-400' },
  { value: 'ollama',   label: 'Ollama (CPU)',    color: 'text-blue-400'   },
  { value: 'nvidia',   label: 'NVIDIA Cloud',    color: 'text-purple-400' },
]

const SUGGESTIONS = [
  "Qu'est-ce que la variance ?",
  "Formule de l'intervalle de confiance",
  "Comment fonctionne K-means ?",
]

// Autorise le rendu des balises HTML que le LLM utilise pour les formules (<sup>, <sub>...),
// tout en filtrant tout le reste (scripts, attributs d'évènements, etc.) — déjà inclus dans
// le schéma par défaut de rehype-sanitize, donc pas besoin de l'étendre.
const markdownRehypePlugins = [rehypeRaw, [rehypeSanitize, defaultSchema]]

// Le backend ajoute ce marqueur discret à la fin des réponses de cours pour indiquer les
// chapitres/concepts utilisés (cf. ChatService.appendSourcesMarker côté serveur). On l'extrait
// ici pour l'afficher en chips séparées plutôt qu'en texte brut dans la réponse.
const SOURCES_MARKER_RE = /\n\n<!--SOURCES:(.*?)-->\s*$/s
function splitSources(content) {
  const m = content?.match(SOURCES_MARKER_RE)
  if (!m) return { text: content, sources: [] }
  try {
    return { text: content.slice(0, m.index), sources: JSON.parse(m[1]) }
  } catch {
    return { text: content, sources: [] }
  }
}

// Même seuil que ChatService.appendSourcesMarker côté backend : une réponse courte
// (salutation, refus...) n'a généralement pas vraiment exploité le contexte récupéré,
// même si celui-ci a bien été cherché — on n'affiche donc pas de sources pour elle.
const SOURCES_MIN_LENGTH = 60
const relevantSources = (text, sources) => (text?.length >= SOURCES_MIN_LENGTH ? sources : [])

function SourcesChips({ sources }) {
  if (!sources || sources.length === 0) return null
  return (
    <div className="flex flex-wrap items-center gap-1.5 mt-2 pt-2 border-t border-gray-700/50">
      <span className="text-[11px] text-gray-500">Sources :</span>
      {sources.map((s, i) => (
        <span key={i} className="text-[11px] bg-gray-700/60 text-gray-300 px-2 py-0.5 rounded-full">
          {[s.chapitre, s.concept].filter(Boolean).join(' — ')}
        </span>
      ))}
    </div>
  )
}

export default function ChatPage() {
  const { user, logout } = useAuth()
  const { settings } = useSettings()
  const navigate = useNavigate()

  const [conversations, setConversations] = useState([])
  const [activeConv, setActiveConv]       = useState(null)
  const [messages, setMessages]           = useState([])
  const [courses, setCourses]             = useState([])
  const [llms, setLlms]                   = useState([])

  const [input, setInput]     = useState('')
  const [sending, setSending] = useState(false)
  const [streamText, setStreamText] = useState('')
  const [showSettings, setShowSettings] = useState(false)

  const [editingId, setEditingId]   = useState(null)
  const [editTitle, setEditTitle]   = useState('')

  // Édition d'un message déjà envoyé
  const [editingMsgId, setEditingMsgId] = useState(null)
  const [editMsgContent, setEditMsgContent] = useState('')
  const [copiedId, setCopiedId] = useState(null)

  // Sources (chapitre/concept) de la réponse en cours de streaming — reçues via l'événement
  // SSE 'sources', avant même le premier token de la réponse.
  const [liveSources, setLiveSources] = useState([])

  // Indicateur de génération façon Claude : durée écoulée, nombre de tokens, étape en cours.
  // `tick` ne sert qu'à forcer un nouveau rendu chaque seconde (le calcul réel de la durée
  // se fait à partir de `startTime`, pas de `tick` lui-même).
  const [genStats, setGenStats] = useState(null) // { startTime, tokenCount, step } | null
  const [, setTick] = useState(0)
  const genIntervalRef = useRef(null)

  // Recherche dans les conversations
  const [convSearch, setConvSearch] = useState('')
  const normalize = s => (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  const filteredConversations = convSearch.trim()
    ? conversations.filter(c => normalize(c.title).includes(normalize(convSearch)))
    : conversations

  const [selectedCourse,  setSelectedCourse]  = useState(settings.defaultCourse || '')
  const [selectedBackend, setSelectedBackend] = useState(settings.defaultBackend || 'lmstudio')
  const [selectedModel,   setSelectedModel]   = useState(settings.defaultModel || '')

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const abortControllerRef = useRef(null)

  const formatTime = iso => {
    if (!iso) return ''
    try {
      return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    } catch { return '' }
  }

  useEffect(() => {
    api.get('/conversations').then(r => setConversations(r.data)).catch(() => {})
    api.get('/courses').then(r => {
      setCourses(r.data)
      // Préférence utilisateur si valide, sinon premier cours disponible
      if (settings.defaultCourse && r.data.includes(settings.defaultCourse))
        setSelectedCourse(settings.defaultCourse)
      else if (r.data.length > 0) setSelectedCourse(r.data[0])
    }).catch(() => setCourses(['Statistique_cours']))
    api.get('/llms').then(r => {
      setLlms(r.data)
      // Préférence utilisateur, sinon modèle par défaut admin, sinon premier
      const pref = settings.defaultModel
        ? r.data.find(l => l.backend === settings.defaultBackend && l.model === settings.defaultModel)
        : null
      const def = pref || r.data.find(l => l.isDefault) || r.data[0]
      if (def) { setSelectedBackend(def.backend); setSelectedModel(def.model) }
    }).catch(() => {})
  }, [])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, streamText])

  const loadConversation = async conv => {
    setActiveConv(conv)
    setStreamText('')
    try {
      const { data } = await api.get(`/conversations/${conv.id}`)
      setMessages(data.messages || [])
      setSelectedCourse(conv.course || selectedCourse)
      setSelectedBackend(conv.backend || selectedBackend)
      setSelectedModel(conv.model || '')
    } catch {}
  }

  const newConversation = async () => {
    try {
      const { data } = await api.post('/conversations', {
        course: selectedCourse, backend: selectedBackend, model: selectedModel || null
      })
      setConversations(c => [data, ...c])
      setActiveConv(data)
      setMessages([])
      setStreamText('')
    } catch {}
  }

  const deleteConversation = async (e, id) => {
    e.stopPropagation()
    await api.delete(`/conversations/${id}`)
    setConversations(c => c.filter(x => x.id !== id))
    if (activeConv?.id === id) { setActiveConv(null); setMessages([]) }
  }

  const deleteAll = async () => {
    if (!confirm('Supprimer toutes les conversations ?')) return
    await api.delete('/conversations')
    setConversations([]); setActiveConv(null); setMessages([])
  }

  const startRename = (e, conv) => {
    e.stopPropagation()
    setEditingId(conv.id); setEditTitle(conv.title)
  }
  const commitRename = async (e) => {
    e?.stopPropagation()
    const id = editingId, title = editTitle.trim()
    setEditingId(null)
    if (!title) return
    setConversations(c => c.map(x => x.id === id ? { ...x, title } : x))
    try { await api.patch(`/conversations/${id}`, { title }) } catch {}
  }

  // Sélecteur de modèles configurés (admin) ou repli sur backend + saisie libre
  const onSelectLlm = e => {
    const [backend, ...rest] = e.target.value.split('|')
    setSelectedBackend(backend)
    setSelectedModel(rest.join('|'))
  }
  const currentLlmValue = `${selectedBackend}|${selectedModel}`
  const backendColor = BACKENDS.find(b => b.value === selectedBackend)?.color || 'text-gray-400'

  /**
   * Lance le streaming SSE de la réponse assistant pour `question` dans `conv`.
   * Réutilisé par l'envoi normal et par la régénération après édition d'un message.
   * `tempUserId` (optionnel) : id client temporaire du message user à remplacer par
   * le vrai id renvoyé par le backend via l'événement SSE 'meta'.
   */
  const streamAssistantResponse = async (conv, question, { tempUserId } = {}) => {
    setSending(true)
    setStreamText('')
    setLiveSources([])
    setGenStats({ startTime: Date.now(), tokenCount: 0, step: 'recherche' })
    genIntervalRef.current = setInterval(() => setTick(t => t + 1), 1000)
    let tokenCount = 0
    const controller = new AbortController()
    abortControllerRef.current = controller
    let fullText = ''
    // Variable locale (pas le state React) : `liveSources` (state) est asynchrone et figé
    // dans la fermeture de cette fonction au moment de l'appel — on a besoin de la valeur
    // à jour ICI pour l'attacher au message final une fois le streaming terminé.
    let sourcesForThisTurn = []
    // Doit être libéré (cancel) dans le finally même en cas de sortie anticipée
    // (break/exception) : sinon le navigateur peut garder la connexion HTTP sous-jacente
    // "à moitié ouverte" et finir par épuiser la limite de connexions simultanées par
    // origine (6 en HTTP/1.1) — les requêtes suivantes restent alors en file d'attente
    // côté navigateur indéfiniment, sans même atteindre le serveur.
    let reader = null

    try {
      const streamBody = JSON.stringify({
        question, course: selectedCourse, backend: selectedBackend,
        model: selectedModel || null, temperature: settings.temperature
      })
      const callStream = token => fetch(`${API_BASE}/conversations/${conv.id}/stream`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          // On accepte AUSSI le JSON : si le backend renvoie une erreur (et non un flux),
          // elle reste sérialisable et son vrai message/status remonte au lieu d'un 401 trompeur.
          'Accept': 'text/event-stream, application/json',
        },
        body: streamBody
      })

      let token = localStorage.getItem('accessToken')
      if (!token) {
        // Le token a disparu du localStorage (déconnexion concurrente dans un autre onglet,
        // purge après un refresh raté ailleurs...) : pas la peine d'envoyer une requête
        // qu'on sait condamnée, on tente directement un refresh.
        console.warn('[chat] accessToken absent du localStorage avant le stream, tentative de refresh préalable')
        try { token = await refreshAccessToken() } catch (e) { console.warn('[chat] refresh préalable échoué', e) }
      }

      let response = await callStream(token)

      // Le token a pu expirer entre le chargement de la page et l'envoi du message :
      // ce fetch() n'a pas le retry automatique de l'intercepteur axios, donc on le fait ici.
      if (response.status === 401 || response.status === 403) {
        console.warn(`[chat] stream refusé (${response.status}), tentative de refresh + retry`)
        try {
          const freshToken = await refreshAccessToken()
          response = await callStream(freshToken)
          if (response.status === 401 || response.status === 403) {
            console.warn(`[chat] toujours refusé (${response.status}) après refresh — refreshToken probablement invalide/expiré`)
          }
        } catch (e) {
          console.warn('[chat] refresh après 401/403 a échoué', e)
        }
      }

      if (!response.ok || !response.body) {
        let msg = `Erreur serveur (${response.status})`
        try { msg = (await response.json()).error || msg } catch {}
        throw new Error(msg)
      }

      reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = '', errored = null, stopped = false, currentEvent = 'message'

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()   // garde la dernière ligne (potentiellement incomplète)

        for (const raw of lines) {
          const line = raw.replace(/\r$/, '')
          if (line === '') { currentEvent = 'message'; continue }
          if (line.startsWith('event:')) { currentEvent = line.slice(6).trim(); continue }
          if (!line.startsWith('data:')) continue

          // Le backend encode chaque payload en JSON avant de l'envoyer (cf. ChatService côté
          // serveur) : un token contenant un saut de ligne brut casserait le cadrage SSE (une
          // ligne vide signale la fin d'un événement), tronquant silencieusement la suite du
          // texte. Le JSON échappe "\n" en deux caractères, donc on décode ici pour le restituer.
          const raw5 = line.slice(5)
          let data
          try { data = JSON.parse(raw5) } catch { data = raw5 }

          // Le tout premier événement renvoie l'id réel (DB) du message user qu'on vient
          // d'envoyer, pour pouvoir l'éditer plus tard sans recharger la conversation.
          if (currentEvent === 'meta') {
            if (tempUserId) {
              const realId = Number(data)
              setMessages(m => m.map(x => x.id === tempUserId ? { ...x, id: realId } : x))
            }
            continue
          }
          // Chapitres/concepts du cours utilisés pour la réponse à venir — affichés en chips
          // sous la bulle pendant le streaming (cf. SourcesChips), avant le premier token.
          if (currentEvent === 'sources') {
            if (Array.isArray(data)) { sourcesForThisTurn = data; setLiveSources(data) }
            continue
          }
          if (currentEvent === 'done' || data === '[DONE]') break outer
          if (currentEvent === 'stopped' || data === '[STOPPED]') { stopped = true; break outer }
          if (currentEvent === 'error') { errored = data; break outer }
          fullText += data
          setStreamText(fullText)
          tokenCount++
          setGenStats(g => g ? { ...g, tokenCount, step: 'génération' } : g)
        }
      }

      if (errored) {
        setMessages(m => [...m, { id: `tmp-${Date.now()}`, role: 'assistant',
          content: `⚠️ ${errored}`, createdAt: new Date().toISOString() }])
      } else {
        const content = stopped ? fullText + '\n\n*(réponse interrompue)*' : fullText
        setMessages(m => [...m, { id: `tmp-${Date.now()}`, role: 'assistant', content,
          createdAt: new Date().toISOString(), sources: relevantSources(fullText, sourcesForThisTurn) }])
        const title = question.length > 50 ? question.slice(0, 50) + '…' : question
        setConversations(c => c.map(x => x.id === conv.id && x.title === 'Nouvelle conversation'
          ? { ...x, title, updatedAt: new Date().toISOString() } : x))
      }
      setStreamText('')
    } catch (err) {
      if (err.name === 'AbortError') {
        // Arrêt initié côté client (bouton Stop) : on garde le texte déjà reçu.
        if (fullText) {
          setMessages(m => [...m, { id: `tmp-${Date.now()}`, role: 'assistant',
            content: fullText + '\n\n*(réponse interrompue)*', createdAt: new Date().toISOString(),
            sources: relevantSources(fullText, sourcesForThisTurn) }])
        }
        setStreamText('')
      } else {
        setMessages(m => [...m, { id: `tmp-${Date.now()}`, role: 'assistant',
          content: `⚠️ ${err.message}`, createdAt: new Date().toISOString() }])
      }
    } finally {
      // Libère systématiquement la connexion sous-jacente, qu'on ait fini normalement,
      // interrompu (break outer) ou échoué — voir le commentaire à la déclaration de `reader`.
      if (reader) { try { await reader.cancel() } catch {} }
      if (genIntervalRef.current) { clearInterval(genIntervalRef.current); genIntervalRef.current = null }
      setGenStats(null)
      setSending(false)
      abortControllerRef.current = null
    }
  }

  const send = async () => {
    if (!input.trim() || sending) return
    let conv = activeConv
    if (!conv) {
      try {
        const { data } = await api.post('/conversations', {
          course: selectedCourse, backend: selectedBackend, model: selectedModel || null
        })
        conv = data
        setConversations(c => [data, ...c])
        setActiveConv(data)
      } catch { return }
    }

    const question = input.trim()
    setInput('')
    const tempUserId = `tmp-${Date.now()}`
    setMessages(m => [...m, { id: tempUserId, role: 'user', content: question,
      createdAt: new Date().toISOString() }])
    await streamAssistantResponse(conv, question, { tempUserId })
  }

  /** Arrête la génération en cours : annule le fetch côté client et notifie le backend. */
  const stopGeneration = async () => {
    abortControllerRef.current?.abort()
    if (activeConv) {
      try { await api.post(`/conversations/${activeConv.id}/stream/stop`) } catch {}
    }
  }

  const isEditableMessageId = id => typeof id === 'number'

  const startEditMessage = msg => {
    if (sending || !isEditableMessageId(msg.id)) return
    setEditingMsgId(msg.id)
    setEditMsgContent(msg.content)
  }
  const cancelEditMessage = () => { setEditingMsgId(null); setEditMsgContent('') }

  const saveEditMessage = async msg => {
    const newContent = editMsgContent.trim()
    if (!newContent || sending) return
    try {
      await api.put(`/conversations/${activeConv.id}/messages/${msg.id}`, { content: newContent })
    } catch (err) {
      alert(err.response?.data?.error || 'Impossible de modifier ce message.')
      return
    }
    const idx = messages.findIndex(m => m.id === msg.id)
    const truncated = idx >= 0 ? messages.slice(0, idx) : messages
    setEditingMsgId(null)
    setEditMsgContent('')
    setMessages([...truncated, { ...msg, content: newContent }])
    await streamAssistantResponse(activeConv, newContent)
  }

  const copyMessage = async (id, content) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedId(id)
      setTimeout(() => setCopiedId(c => (c === id ? null : c)), 1500)
    } catch {}
  }

  /** Exporte une conversation en Markdown téléchargeable (.md). */
  const exportConversation = async (e, conv) => {
    e.stopPropagation()
    try {
      const { data } = await api.get(`/conversations/${conv.id}`)
      const lines = [`# ${conv.title}`, '']
      for (const m of (data.messages || [])) {
        const who = m.role === 'user' ? '**Vous**' : '**Assistant**'
        const time = formatTime(m.createdAt)
        lines.push(`${who}${time ? ` _(${time})_` : ''} :`, '', m.content, '')
      }
      const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${conv.title.replace(/[^\w\- ]/g, '').slice(0, 60) || 'conversation'}.md`
      a.click()
      URL.revokeObjectURL(url)
    } catch {}
  }

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey && settings.sendOnEnter) { e.preventDefault(); send() }
  }

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800 flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-4 h-4 text-gray-50" />
          </div>
          <span className="font-semibold text-gray-50 truncate">RAG Explicateur</span>
        </div>

        <div className="p-3">
          <button onClick={newConversation}
            className="group w-full flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium shadow-sm shadow-indigo-600/20 transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-indigo-600/30 active:translate-y-0">
            <Plus className="w-4 h-4 transition-transform group-hover:rotate-90" /> Nouvelle conversation
          </button>
        </div>

        {/* Recherche de conversation */}
        <div className="px-3 pb-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" />
            <input value={convSearch} onChange={e => setConvSearch(e.target.value)}
              placeholder="Rechercher une conversation…"
              className="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg pl-8 pr-7 py-2 placeholder-gray-500 focus:outline-none focus:border-indigo-500" />
            {convSearch && (
              <button onClick={() => setConvSearch('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-50">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
          {filteredConversations.length === 0 && (
            <p className="text-center text-gray-600 text-xs py-4">
              {convSearch ? 'Aucun résultat' : 'Aucune conversation'}
            </p>
          )}
          {filteredConversations.map(conv => (
            <div key={conv.id}
              onClick={() => loadConversation(conv)}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors animate-slide-in ${
                activeConv?.id === conv.id ? 'bg-gray-700 text-gray-50' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-50'
              }`}>
              {editingId === conv.id ? (
                <input autoFocus value={editTitle}
                  onClick={e => e.stopPropagation()}
                  onChange={e => setEditTitle(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') commitRename(e); if (e.key === 'Escape') setEditingId(null) }}
                  onBlur={commitRename}
                  className="flex-1 bg-gray-800 border border-indigo-500 rounded px-1.5 py-0.5 text-xs text-gray-50 focus:outline-none" />
              ) : (
                <>
                  <span className="flex-1 truncate">{conv.title}</span>
                  <button onClick={e => exportConversation(e, conv)} title="Exporter en Markdown"
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-emerald-400 transition-all flex-shrink-0">
                    <Download className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={e => startRename(e, conv)} title="Renommer"
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-indigo-400 transition-all flex-shrink-0">
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={e => deleteConversation(e, conv.id)} title="Supprimer"
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all flex-shrink-0">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        <div className="p-3 border-t border-gray-800 space-y-1">
          {conversations.length > 0 && (
            <button onClick={deleteAll}
              className="w-full flex items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-500/10 rounded-lg text-sm transition-colors">
              <Trash2 className="w-4 h-4" /> Tout supprimer
            </button>
          )}
          <button onClick={() => setShowSettings(true)}
            className="w-full flex items-center gap-2 px-3 py-2 text-gray-400 hover:bg-gray-800 hover:text-gray-50 rounded-lg text-sm transition-colors">
            <Settings className="w-4 h-4" /> Paramètres
          </button>
          {user?.role === 'ADMIN' && (
            <button onClick={() => navigate('/admin')}
              className="w-full flex items-center gap-2 px-3 py-2 text-gray-400 hover:bg-gray-800 hover:text-gray-50 rounded-lg text-sm transition-colors">
              <Shield className="w-4 h-4" /> Administration
            </button>
          )}
          <div className="flex items-center justify-between px-3 py-2">
            <span className="text-gray-500 text-xs truncate">{user?.username}</span>
            <button onClick={logout} className="text-gray-600 hover:text-red-400 transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800 bg-gray-900 flex-shrink-0 flex-wrap">
          {/* Course selector */}
          <div className="relative">
            <select value={selectedCourse} onChange={e => setSelectedCourse(e.target.value)}
              className="appearance-none bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 pr-8 focus:outline-none focus:border-indigo-500 cursor-pointer">
              {courses.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
            </select>
            <ChevronDown className="absolute right-2 top-2 w-4 h-4 text-gray-500 pointer-events-none" />
          </div>

          {/* LLM selector: configured models if available, else backend + free model
              — masqué (display:none) : le modèle par défaut admin reste utilisé en arrière-plan */}
          {llms.length > 0 ? (
            <div className="relative" style={{ display: 'none' }}>
              <select value={currentLlmValue} onChange={onSelectLlm}
                className={`appearance-none bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-1.5 pr-8 focus:outline-none focus:border-indigo-500 cursor-pointer ${backendColor}`}>
                {llms.map(l => (
                  <option key={l.id} value={`${l.backend}|${l.model}`}>{l.name}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-2 w-4 h-4 text-gray-500 pointer-events-none" />
            </div>
          ) : (
            <div style={{ display: 'none' }}>
              <div className="relative">
                <select value={selectedBackend} onChange={e => setSelectedBackend(e.target.value)}
                  className={`appearance-none bg-gray-800 border border-gray-700 text-sm rounded-lg px-3 py-1.5 pr-8 focus:outline-none focus:border-indigo-500 cursor-pointer ${backendColor}`}>
                  {BACKENDS.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
                </select>
                <ChevronDown className="absolute right-2 top-2 w-4 h-4 text-gray-500 pointer-events-none" />
              </div>
              <input value={selectedModel} onChange={e => setSelectedModel(e.target.value)}
                placeholder="modèle (optionnel)"
                className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 w-44 focus:outline-none focus:border-indigo-500 placeholder-gray-600" />
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.length === 0 && !streamText && (
            <div className="flex flex-col items-center justify-center h-full text-center animate-fade-up">
              <div className="w-16 h-16 bg-indigo-600/20 rounded-2xl flex items-center justify-center mb-4 animate-glow">
                <BookOpen className="w-8 h-8 text-indigo-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-50 mb-2">Posez votre question</h2>
              <p className="text-gray-500 max-w-md text-sm">
                Sélectionnez un cours et un modèle LLM, puis posez votre question.
                Le RAG trouvera les passages pertinents automatiquement.
              </p>
              <div className="mt-6 flex flex-wrap gap-2 justify-center">
                {SUGGESTIONS.map((q, i) => (
                  <button key={q} onClick={() => setInput(q)}
                    className={`lift text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-full border border-gray-700 transition-colors animate-fade-up delay-${i + 1}`}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => {
            const { text: displayText, sources: displaySources } = msg.role === 'assistant'
              ? (msg.sources ? { text: msg.content, sources: msg.sources } : splitSources(msg.content))
              : { text: msg.content, sources: [] }
            return (
            <div key={msg.id} className={`group flex animate-pop-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl ${msg.role === 'user' ? 'flex flex-col items-end' : 'flex flex-col items-start'}`}>
                {editingMsgId === msg.id ? (
                  <div className="w-full min-w-[20rem] bg-gray-800 border border-indigo-500 rounded-2xl px-4 py-3">
                    <textarea autoFocus value={editMsgContent}
                      onChange={e => setEditMsgContent(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Escape') cancelEditMessage() }}
                      rows={Math.min(8, Math.max(2, editMsgContent.split('\n').length))}
                      className="w-full bg-transparent text-gray-100 text-sm resize-none focus:outline-none" />
                    <div className="flex justify-end gap-2 mt-2">
                      <button onClick={cancelEditMessage}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs text-gray-400 hover:text-gray-50 hover:bg-gray-700 rounded-lg transition-colors">
                        <X className="w-3.5 h-3.5" /> Annuler
                      </button>
                      <button onClick={() => saveEditMessage(msg)}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors">
                        <Check className="w-3.5 h-3.5" /> Enregistrer &amp; régénérer
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className={`rounded-2xl px-5 py-3 ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-sm shadow-sm shadow-indigo-600/20'
                        : 'bg-gray-800 text-gray-100 rounded-bl-sm'
                    }`}>
                      {msg.role === 'assistant' ? (
                        <>
                          <div className="prose-chat"><ReactMarkdown rehypePlugins={markdownRehypePlugins}>{displayText}</ReactMarkdown></div>
                          <SourcesChips sources={displaySources} />
                        </>
                      ) : <p className="text-sm whitespace-pre-wrap">{displayText}</p>}
                    </div>
                    <div className="flex items-center gap-2 mt-1 px-1 h-5">
                      <span className="text-[11px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                        {formatTime(msg.createdAt)}
                      </span>
                      <button onClick={() => copyMessage(msg.id, displayText)} title="Copier"
                        className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-gray-50 transition-all">
                        {copiedId === msg.id ? <CopyCheck className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                      {msg.role === 'user' && isEditableMessageId(msg.id) && !sending && (
                        <button onClick={() => startEditMessage(msg)} title="Modifier"
                          className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-indigo-400 transition-all">
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          )})}

          {sending && genStats && (
            <div className="flex justify-start">
              <div className="inline-flex items-center gap-2 bg-gray-800/80 border border-gray-700/50 text-gray-400 text-xs px-3 py-1.5 rounded-full">
                <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                <span>
                  {Math.floor((Date.now() - genStats.startTime) / 1000)}s
                  {' · '}{genStats.tokenCount} tokens
                  {' · '}{genStats.step === 'génération' ? 'génération en cours…' : 'recherche dans le cours…'}
                </span>
              </div>
            </div>
          )}

          {streamText && (
            <div className="flex justify-start">
              <div className="max-w-3xl bg-gray-800 rounded-2xl rounded-bl-sm px-5 py-3">
                <div className="prose-chat"><ReactMarkdown rehypePlugins={markdownRehypePlugins}>{streamText}</ReactMarkdown></div>
                <SourcesChips sources={relevantSources(streamText, liveSources)} />
                <span className="inline-block w-1.5 h-4 bg-indigo-400 animate-pulse ml-0.5" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-4 border-t border-gray-800 bg-gray-900 flex-shrink-0">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Posez votre question… (Entrée pour envoyer, Maj+Entrée pour saut de ligne)"
              rows={1}
              disabled={sending}
              className="flex-1 resize-none bg-gray-800 border border-gray-700 text-gray-100 rounded-xl px-4 py-3 text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50 max-h-32 overflow-y-auto"
              style={{height: 'auto'}}
              onInput={e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px' }}
            />
            {sending ? (
              <button onClick={stopGeneration} title="Arrêter la génération"
                className="flex-shrink-0 w-11 h-11 bg-red-600 hover:bg-red-500 text-white rounded-xl flex items-center justify-center transition-colors self-end">
                <Square className="w-4 h-4" fill="currentColor" />
              </button>
            ) : (
              <button onClick={send} disabled={!input.trim()}
                className="flex-shrink-0 w-11 h-11 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition-colors self-end">
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </main>

      {showSettings && <SettingsModal user={user} onClose={() => setShowSettings(false)} />}
    </div>
  )
}
