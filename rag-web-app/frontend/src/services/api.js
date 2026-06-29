import axios from 'axios'

// Configurable au build (.env : VITE_API_BASE) pour les déploiements sous un sous-chemin
// (ex: /rag-explicateur/api) où plusieurs apps partagent le même domaine — '/api' par défaut
// pour le développement local, inchangé.
export const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({ baseURL: API_BASE })

// Réutilisé par l'intercepteur axios et par les appels fetch() bruts (ex. SSE)
// qui n'ont pas de retry automatique sur token expiré.
// "Single-flight" : si plusieurs appels échouent en 401 en même temps (ex. axios + SSE),
// ils partagent le même refresh au lieu d'en déclencher un chacun (qui se marcheraient dessus).
let refreshPromise = null

export function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

async function doRefresh() {
  const refresh = localStorage.getItem('refreshToken')
  const { data } = await axios.post(`${API_BASE}/auth/refresh`, { refreshToken: refresh })
  localStorage.setItem('accessToken', data.accessToken)
  localStorage.setItem('refreshToken', data.refreshToken)
  const stored = localStorage.getItem('auth')
  if (stored) {
    const auth = JSON.parse(stored)
    auth.accessToken = data.accessToken
    localStorage.setItem('auth', JSON.stringify(auth))
  }
  return data.accessToken
}

api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const accessToken = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${accessToken}`
        return api(original)
      } catch (refreshErr) {
        // Ne déconnecter que si le serveur a explicitement rejeté le refresh token
        // (invalide/expiré). Une simple erreur réseau ou un 5xx transitoire ne doit
        // pas effacer la session : l'utilisateur pourra réessayer une fois le serveur revenu.
        const status = refreshErr.response?.status
        if (status === 400 || status === 401) {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

export default api
