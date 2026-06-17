import { createContext, useState, useCallback } from 'react';
import { authApi } from '../api/client.js';

/**
 * Contexte d'authentification partagé dans toute l'application.
 *
 * Expose :
 *   - user          : objet { id, email, fullName, role } ou null
 *   - isAuthenticated : booléen dérivé
 *   - login(email, password) : appelle l'API, stocke le token, met à jour user
 *   - logout()      : efface le token et remet user à null
 */
export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // TODO: initialiser depuis localStorage si un token valide existe déjà
  const [user, setUser] = useState(null);

  const login = useCallback(async (email, password) => {
    // TODO: appeler authApi.login(), stocker le JWT dans localStorage
    // TODO: décoder le payload JWT pour extraire { id, email, fullName, role }
    // TODO: mettre à jour setUser avec les données décodées
    throw new Error('login non implémenté');
  }, []);

  const logout = useCallback(() => {
    // TODO: supprimer le token de localStorage
    // TODO: réinitialiser l'état user
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: user !== null, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
