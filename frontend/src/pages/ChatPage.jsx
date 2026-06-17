import { useState } from 'react';
import ChatWindow from '../components/chat/ChatWindow.jsx';
import ChatInput from '../components/chat/ChatInput.jsx';
import { useChatStream } from '../hooks/useChatStream.js';

/**
 * Page principale du chat RAG.
 *
 * Orchestre :
 *   1. la liste des messages déjà échangés (state local)
 *   2. le streaming SSE via useChatStream
 *   3. la zone de saisie
 *   4. un sélecteur de cours (optionnel, filtre la recherche vectorielle)
 */
export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(null);

  const { response, sources, isStreaming, sendMessage, cancel } = useChatStream({
    onError: (err) => console.error('Erreur de streaming:', err),
  });

  async function handleSend(question) {
    // Ajouter le message utilisateur à l'historique local
    setMessages((prev) => [...prev, { role: 'user', content: question }]);

    await sendMessage(question, selectedCourseId);

    // Quand le stream est terminé, ajouter la réponse complète à l'historique
    // TODO: écouter l'état "done" de useChatStream et appeler setMessages
  }

  return (
    <main className="chat-page">
      {/* TODO: sélecteur de cours (dropdown chargé via /api/courses) */}

      <ChatWindow
        messages={messages}
        streamingText={response}
        isStreaming={isStreaming}
      />

      {/* Sources affichées après la réponse */}
      {sources.length > 0 && (
        <div className="chat-page__sources">
          <p>Sources : {sources.join(', ')}</p>
        </div>
      )}

      <ChatInput
        onSend={handleSend}
        onCancel={cancel}
        isStreaming={isStreaming}
      />
    </main>
  );
}
