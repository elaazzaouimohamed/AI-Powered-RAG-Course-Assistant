import axios from 'axios';

/**
 * Instance axios préconfigurée pour toutes les requêtes vers le backend.
 *
 * Intercepteurs :
 *   - requête  : injecte automatiquement le header Authorization: Bearer <token>
 *   - réponse  : redirige vers /login si le serveur retourne 401
 */
const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Injecte le JWT à chaque requête
apiClient.interceptors.request.use((config) => {
  // TODO: lire le token depuis localStorage et l'ajouter au header Authorization
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Gestion globale des erreurs 401 (session expirée)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // TODO: supprimer le token expiré et rediriger vers /login
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// Export séparé pour les appels d'authentification (sans token)
export const authApi = axios.create({
  baseURL: '/api/auth',
  headers: { 'Content-Type': 'application/json' },
});
