import './MessageBubble.css';

/**
 * Bulle de message individuelle.
 *
 * Alignement :
 *   - 'user'      → droite (fond bleu, texte blanc)
 *   - 'assistant' → gauche (fond gris clair, texte sombre)
 *
 * @param {object} props
 * @param {'user'|'assistant'} props.role    - expéditeur du message
 * @param {string}             props.content - texte du message (peut contenir du Markdown)
 */
export default function MessageBubble({ role, content }) {
  const isUser = role === 'user';

  return (
    <div className={`message-bubble message-bubble--${role}`}>
      {!isUser && (
        /* Avatar / icône du bot */
        <div className="message-bubble__avatar">
          {/* TODO: remplacer par une vraie icône */}
          AI
        </div>
      )}

      <div className="message-bubble__content">
        {/* TODO: utiliser une bibliothèque légère de rendu Markdown (ex: marked, micromark) */}
        <p>{content}</p>
      </div>
    </div>
  );
}
