import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext.jsx';

/**
 * Hook d'accès au contexte d'authentification.
 *
 * @returns {{ user, isAuthenticated, login, logout }}
 * @throws {Error} si utilisé en dehors d'un <AuthProvider>
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth doit être utilisé à l'intérieur d\'un <AuthProvider>');
  }
  return context;
}
