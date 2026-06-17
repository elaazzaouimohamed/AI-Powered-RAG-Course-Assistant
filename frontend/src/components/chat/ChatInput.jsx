import { useState, useRef } from 'react';

/**
 * Zone de saisie du message utilisateur.
 *
 * - Textarea qui s'étire automatiquement en hauteur (auto-resize)
 * - Envoi par clic ou par Entrée (Shift+Entrée = saut de ligne)
 * - Bouton de stop visible uniquement pendant le streaming
 *
 * @param {object}   props
 * @param {Function} props.onSend       - appelé avec la question quand l'utilisateur envoie
 * @param {Function} props.onCancel     - appelé quand l'utilisateur arrête le streaming
 * @param {boolean}  props.isStreaming  - désactive l'envoi pendant un streaming actif
 * @param {boolean}  props.disabled     - désactive entièrement le champ
 */
export default function ChatInput({ onSend, onCancel, isStreaming = false, disabled = false }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
    setValue('');
    // TODO: réinitialiser la hauteur du textarea après l'envoi
  }

  function handleInput(e) {
    setValue(e.target.value);
    // TODO: ajuster la hauteur du textarea dynamiquement (auto-resize)
  }

  return (
    <div className="chat-input">
      <textarea
        ref={textareaRef}
        className="chat-input__textarea"
        value={value}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder="Posez votre question…"
        rows={1}
        disabled={disabled}
        aria-label="Zone de saisie du message"
      />

      {isStreaming ? (
        <button className="chat-input__btn chat-input__btn--stop" onClick={onCancel} type="button">
          Arrêter
        </button>
      ) : (
        <button
          className="chat-input__btn chat-input__btn--send"
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          type="button"
        >
          Envoyer
        </button>
      )}
    </div>
  );
}
