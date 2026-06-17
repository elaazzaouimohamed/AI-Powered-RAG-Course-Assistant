import { useQuery } from '@tanstack/react-query';
import { fetchDocumentsByCourse, deleteDocument } from '../../api/documentApi.js';

/**
 * Liste les documents d'un cours avec leur statut d'ingestion.
 *
 * Affiche :
 *   - nom du fichier
 *   - statut coloré (PENDING / PROCESSING / DONE / FAILED)
 *   - bouton de suppression (réservé PROFESSOR/ADMIN)
 *
 * @param {object}  props
 * @param {number}  props.courseId  - cours dont afficher les documents
 * @param {boolean} props.canDelete - true si l'utilisateur a le droit de supprimer
 */
export default function DocumentList({ courseId, canDelete = false }) {
  const { data: documents = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['documents', courseId],
    queryFn: () => fetchDocumentsByCourse(courseId),
    enabled: !!courseId,
  });

  async function handleDelete(documentId) {
    if (!confirm('Supprimer ce document et tous ses fragments ?')) return;
    await deleteDocument(documentId);
    refetch();
  }

  if (isLoading) return <p>Chargement des documents…</p>;
  if (isError)   return <p className="doc-list__error">Erreur lors du chargement.</p>;
  if (documents.length === 0) return <p className="doc-list__empty">Aucun document pour ce cours.</p>;

  return (
    <ul className="doc-list">
      {documents.map((doc) => (
        <li key={doc.id} className="doc-list__item">
          <span className="doc-list__filename">{doc.filename}</span>
          <span className={`doc-list__status doc-list__status--${doc.status.toLowerCase()}`}>
            {doc.status}
          </span>
          {canDelete && (
            <button className="doc-list__delete-btn" onClick={() => handleDelete(doc.id)}>
              Supprimer
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
