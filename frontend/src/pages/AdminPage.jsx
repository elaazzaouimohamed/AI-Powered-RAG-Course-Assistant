import { useAuth } from '../hooks/useAuth.js';
import { Navigate } from 'react-router-dom';
import DocumentUploader from '../components/documents/DocumentUploader.jsx';
import DocumentList from '../components/documents/DocumentList.jsx';

/**
 * Page d'administration réservée au rôle ADMIN.
 *
 * Sections :
 *   1. Gestion des documents (upload, liste, suppression par cours)
 *   2. TODO: gestion des utilisateurs
 *   3. TODO: génération de quiz
 *   4. TODO: visualisations ACP / K-Means
 */
export default function AdminPage() {
  const { user } = useAuth();

  // Garde côté client (la garde principale est dans le backend via @PreAuthorize)
  if (user?.role !== 'ADMIN' && user?.role !== 'PROFESSOR') {
    return <Navigate to="/chat" replace />;
  }

  return (
    <main className="admin-page">
      <h2>Administration</h2>

      <section className="admin-page__section">
        <h3>Gestion des documents</h3>
        {/* TODO: sélecteur de cours pour filtrer les documents */}
        <DocumentUploader courseId={null /* TODO: relier au cours sélectionné */} />
        <DocumentList courseId={null /* TODO: relier au cours sélectionné */} canDelete />
      </section>

      <section className="admin-page__section">
        <h3>Gestion des utilisateurs</h3>
        {/* TODO: liste des utilisateurs avec changement de rôle */}
      </section>

      <section className="admin-page__section">
        <h3>Génération de quiz</h3>
        {/* TODO: formulaire de génération de quiz par cours */}
      </section>
    </main>
  );
}
