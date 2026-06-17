import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';

/**
 * Page de connexion.
 *
 * Formulaire e-mail / mot de passe. En cas de succès, redirige vers /chat.
 * Affiche les erreurs de l'API (credentials invalides, serveur indisponible).
 */
export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/chat', { replace: true });
    } catch {
      setError('Identifiants incorrects. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-page__card">
        {/* TODO: logo FSBM + nom de l'application */}
        <h1 className="login-page__title">Connexion</h1>
        <p className="login-page__subtitle">RAG Explicateur — Cours universitaires</p>

        <form onSubmit={handleSubmit} className="login-page__form" noValidate>
          <div className="login-page__field">
            <label htmlFor="email">Adresse e-mail</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="login-page__field">
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {error && <p className="login-page__error" role="alert">{error}</p>}

          <button type="submit" className="login-page__submit-btn" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
}
