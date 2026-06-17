import './MessageBubble.css';

/**
 * Affiche la réponse du LLM au fur et à mesure de son arrivée via SSE.
 *
 * Réutilise les styles de MessageBubble pour la cohérence visuelle,
 * et ajoute un curseur clignotant indiquant que la réponse est en cours.
 *
 * @param {object} props
 * @param {string} props.text - texte accumulé jusqu'ici
 */
export default function StreamingResponse({ text }) {
  return (
    <div className="message-bubble message-bubble--assistant">
      <div className="message-bubble__avatar">AI</div>
      <div className="message-bubble__content streaming-response__content">
        {/* TODO: rendu Markdown du texte accumulé */}
        <p>
          {text}
          {/* Curseur clignotant pendant le streaming */}
          <span className="streaming-response__cursor" aria-hidden="true" />
        </p>
      </div>
    </div>
  );
}
