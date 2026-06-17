import { useState, useRef } from 'react';
import { uploadDocument } from '../../api/documentApi.js';

/**
 * Zone de dépôt (drag & drop) et d'upload de fichiers PDF.
 *
 * Affiche une barre de progression pendant l'upload et
 * un indicateur de statut (PENDING / PROCESSING / DONE / FAILED).
 *
 * @param {object}   props
 * @param {number}   props.courseId   - cours auquel rattacher le document
 * @param {Function} props.onUploaded - appelé avec le Document créé après succès
 */
export default function DocumentUploader({ courseId, onUploaded }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  async function handleFiles(files) {
    const file = files[0];
    if (!file || file.type !== 'application/pdf') {
      setError('Seuls les fichiers PDF sont acceptés.');
      return;
    }
    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const doc = await uploadDocument(file, courseId, setProgress);
      onUploaded?.(doc);
    } catch {
      setError('Erreur lors de l\'upload. Veuillez réessayer.');
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div
      className={`doc-uploader${isDragOver ? ' doc-uploader--drag-over' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-label="Zone de dépôt de fichier PDF"
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="visually-hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {/* TODO: icône upload */}
      <p className="doc-uploader__label">
        {uploading
          ? `Envoi en cours… ${progress}%`
          : 'Glissez un PDF ici ou cliquez pour parcourir'}
      </p>

      {/* Barre de progression */}
      {uploading && (
        <div className="doc-uploader__progress-bar">
          <div className="doc-uploader__progress-fill" style={{ width: `${progress}%` }} />
        </div>
      )}

      {error && <p className="doc-uploader__error">{error}</p>}
    </div>
  );
}
