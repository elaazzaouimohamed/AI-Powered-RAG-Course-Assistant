import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble.jsx';
import StreamingResponse from './StreamingResponse.jsx';
import './ChatWindow.css';

/**
 * Zone de messages du chat.
 *
 * Affiche la liste des messages échangés et la réponse en cours
 * de streaming. Défile automatiquement vers le dernier message.
 *
 * @param {object} props
 * @param {Array<{role: 'user'|'assistant', content: string}>} props.messages - historique
 * @param {string} props.streamingText  - fragment en cours de réception (SSE)
 * @param {boolean} props.isStreaming   - true si une réponse est en cours
 */
export default function ChatWindow({ messages = [], streamingText = '', isStreaming = false }) {
  const bottomRef = useRef(null);

  // Défilement automatique lors d'un nouveau message ou d'un nouveau fragment
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  return (
    <div className="chat-window">
      {messages.length === 0 && !isStreaming && (
        /* Écran vide : invitation à poser une question */
        <div className="chat-window__empty">
          {/* TODO: illustration + message d'accueil */}
          <p>Posez une question sur vos cours pour commencer.</p>
        </div>
      )}

      {/* Liste des messages précédents */}
      {messages.map((msg, index) => (
        <MessageBubble key={index} role={msg.role} content={msg.content} />
      ))}

      {/* Réponse en cours de streaming */}
      {isStreaming && <StreamingResponse text={streamingText} />}

      {/* Ancre pour le scroll automatique */}
      <div ref={bottomRef} />
    </div>
  );
}
