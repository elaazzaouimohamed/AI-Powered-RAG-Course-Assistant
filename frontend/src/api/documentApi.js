import apiClient from './client.js';

/**
 * Fonctions d'accès à l'API documents (upload, liste, suppression).
 */

/**
 * Upload un PDF et déclenche l'ingestion côté serveur.
 *
 * @param {File} file     fichier PDF
 * @param {number} courseId identifiant du cours
 * @param {Function} onProgress callback de progression (optionnel)
 * @returns {Promise<Document>} entité document créée (statut PENDING)
 */
export async function uploadDocument(file, courseId, onProgress) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('courseId', courseId);

  const { data } = await apiClient.post('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return data;
}

/**
 * Récupère les documents d'un cours.
 *
 * @param {number} courseId identifiant du cours
 * @returns {Promise<Document[]>}
 */
export async function fetchDocumentsByCourse(courseId) {
  const { data } = await apiClient.get('/documents', { params: { courseId } });
  return data;
}

/**
 * Supprime un document et tous ses chunks associés.
 *
 * @param {number} documentId identifiant du document
 * @returns {Promise<void>}
 */
export async function deleteDocument(documentId) {
  await apiClient.delete(`/documents/${documentId}`);
}
