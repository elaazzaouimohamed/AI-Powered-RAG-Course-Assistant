import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth.js';
import './Sidebar.css';

/**
 * Barre latérale de navigation principale.
 *
 * Affiche les liens vers :
 *   - Chat (/chat)
 *   - Historique (/history)
 *   - Administration (/admin) — visible uniquement pour ADMIN
 *
 * Utilise NavLink pour appliquer automatiquement la classe active
 * sur le lien de la page courante.
 */
export default function Sidebar() {
  const { user } = useAuth();

  return (
    <aside className="sidebar">
      {/* Logo / titre de l'application */}
      <div className="sidebar__brand">
        {/* TODO: remplacer par un vrai logo SVG */}
        <span className="sidebar__brand-icon">📚</span>
        <span className="sidebar__brand-name">RAG Explicateur</span>
      </div>

      <nav className="sidebar__nav">
        <NavLink to="/chat" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
          {/* TODO: icône Chat */}
          Chat
        </NavLink>

        <NavLink to="/history" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
          {/* TODO: icône Historique */}
          Historique
        </NavLink>

        {user?.role === 'ADMIN' && (
          <NavLink to="/admin" className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}>
            {/* TODO: icône Admin */}
            Administration
          </NavLink>
        )}
      </nav>

      {/* Infos utilisateur en bas de la sidebar */}
      <div className="sidebar__footer">
        <span className="sidebar__footer-text">{user?.fullName}</span>
      </div>
    </aside>
  );
}
