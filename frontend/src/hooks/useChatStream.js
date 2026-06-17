import { useState, useRef, useCallback } from 'react';

/**
 * Hook de gestion du streaming SSE pour le chat RAG.
 *
 * Ouvre une connexion SSE vers POST /api/chat/stream, accumule les fragments
 * reçus dans `response` et met à jour `sources` lors du dernier événement.
 *
 * @param {object} options
 * @param {Function} options.onError - callback en cas d'erreur réseau
 *
 * @returns {{
 *   response: string,    — texte accumulé jusqu'ici
 *   sources: string[],   — sources reçues dans le dernier fragment
 *   isStreaming: boolean,
 *   sendMessage: (question: string, courseId?: number) => void,
 *   cancel: () => void
 * }}
 */
export function useChatStream({ onError } = {}) {
  const [response, setResponse] = useState('');
  const [sources, setSources] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  // Référence vers le fetch en cours pour pouvoir l'annuler (AbortController)
  const abortRef = useRef(null);

  const sendMessage = useCallback(async (question, courseId = null) => {
    // TODO: créer un AbortController, stocker dans abortRef
    // TODO: fetch POST /api/chat/stream avec { question, courseId }
    // TODO: lire le ReadableStream ligne par ligne (text/event-stream)
    // TODO: parser chaque ligne JSON → ChatResponse
    // TODO: accumuler delta dans setResponse, extraire sources sur done=true
    setResponse('');
    setSources([]);
    setIsStreaming(true);
    throw new Error('sendMessage non implémenté');
  }, [onError]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { response, sources, isStreaming, sendMessage, cancel };
}
