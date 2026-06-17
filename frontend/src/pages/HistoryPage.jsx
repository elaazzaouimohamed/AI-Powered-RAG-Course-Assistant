import { useQuery } from '@tanstack/react-query';
import { fetchChatHistory, deleteChatSession } from '../api/chatApi.js';

/**
 * Page d'historique des conversations.
 *
 * Affiche les sessions de chat précédentes de l'utilisateur connecté,
 * triées par date décroissante. Permet de supprimer une session.
 */
export default function HistoryPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['chat-history'],
    queryFn: () => fetchChatHistory({ page: 0, size: 50 }),
  });

  async function handleDelete(sessionId) {
    if (!confirm('Supprimer cette conversation ?')) return;
    await deleteChatSession(sessionId);
    refetch();
  }

  if (isLoading) return <div className="history-page"><p>Chargement…</p></div>;
  if (isError)   return <div className="history-page"><p>Erreur lors du chargement de l'historique.</p></div>;

  const sessions = data?.content ?? [];

  return (
    <main className="history-page">
      <h2>Historique des conversations</h2>

      {sessions.length === 0 ? (
        <p className="history-page__empty">Aucune conversation enregistrée.</p>
      ) : (
        <ul className="history-page__list">
          {sessions.map((session) => (
            <li key={session.id} className="history-page__item">
              {/* TODO: afficher le premier message / un résumé de la session */}
              <div className="history-page__item-info">
                <p className="history-page__item-date">
                  {new Date(session.createdAt).toLocaleString('fr-FR')}
                </p>
                <p className="history-page__item-preview">{session.preview ?? 'Conversation'}</p>
              </div>
              <button
                className="history-page__delete-btn"
                onClick={() => handleDelete(session.id)}
              >
                Supprimer
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
