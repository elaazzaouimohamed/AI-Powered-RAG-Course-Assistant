import { useAuth } from '../../hooks/useAuth.js';
import './Header.css';

/**
 * Barre de navigation supérieure.
 *
 * Affiche :
 *   - le titre de la page courante (passé en prop ou déduit de la route)
 *   - le nom de l'utilisateur connecté et son rôle
 *   - le bouton de déconnexion
 *
 * @param {object} props
 * @param {string} [props.title] - titre affiché dans la barre (facultatif)
 */
export default function Header({ title }) {
  const { user, logout } = useAuth();

  return (
    <header className="header">
      {/* Titre de la page courante */}
      <h1 className="header__title">{title ?? 'RAG Explicateur'}</h1>

      {/* Zone utilisateur */}
      <div className="header__user">
        {/* TODO: afficher l'avatar ou les initiales de l'utilisateur */}
        <span className="header__user-name">{user?.fullName}</span>
        <span className="header__user-role">{user?.role}</span>
        <button className="header__logout-btn" onClick={logout}>
          Déconnexion
        </button>
      </div>
    </header>
  );
}
