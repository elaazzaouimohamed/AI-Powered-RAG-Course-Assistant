/**
 * Fonctions d'accès à l'API chat.
 *
 * Note : le streaming SSE est géré directement via fetch dans useChatStream.js
 * (axios ne supporte pas nativement les ReadableStream).
 * Ce module expose uniquement les appels non-streaming (historique, sessions).
 */

import apiClient from './client.js';

/**
 * Récupère l'historique de chat d'un utilisateur.
 *
 * @param {object} params
 * @param {number} params.page - numéro de page (0-based)
 * @param {number} params.size - taille de la page
 * @returns {Promise<PageResponse>} liste paginée des sessions de chat
 */
export async function fetchChatHistory({ page = 0, size = 20 } = {}) {
  // TODO: GET /api/chat/history?page=&size=
  const { data } = await apiClient.get('/chat/history', { params: { page, size } });
  return data;
}

/**
 * Supprime une session de chat.
 *
 * @param {string} sessionId identifiant de la session
 * @returns {Promise<void>}
 */
export async function deleteChatSession(sessionId) {
  // TODO: DELETE /api/chat/sessions/:sessionId
  await apiClient.delete(`/chat/sessions/${sessionId}`);
}
