import { useEffect, useRef } from 'react';

/**
 * Widget de visualisation de concepts extraits du cours.
 *
 * Affiche des représentations précalculées (ACP 2D, clustering K-Means)
 * des embeddings de documents. Les données sont chargées depuis une API
 * dédiée et rendues sur un canvas ou avec une bibliothèque SVG légère.
 *
 * NOTE : les calculs (ACP, K-Means) sont effectués côté backend/Python —
 * ce composant ne fait que visualiser les coordonnées pré-calculées.
 *
 * @param {object}   props
 * @param {number}   props.courseId  - cours dont visualiser les concepts
 * @param {'pca'|'kmeans'} props.mode - type de visualisation
 */
export default function ConceptVisualizer({ courseId, mode = 'pca' }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!courseId) return;
    // TODO: charger les données de visualisation depuis GET /api/visualizations?courseId=&mode=
    // TODO: projeter les points 2D sur le canvas avec des couleurs par cluster (K-Means)
    //       ou par distance à l'origine (ACP)
    // TODO: ajouter une interaction hover pour afficher le label du chunk
  }, [courseId, mode]);

  return (
    <div className="concept-visualizer">
      <div className="concept-visualizer__controls">
        {/* TODO: boutons pour basculer entre PCA et K-Means */}
      </div>

      <canvas
        ref={canvasRef}
        className="concept-visualizer__canvas"
        width={600}
        height={400}
        aria-label={`Visualisation ${mode.toUpperCase()} des concepts du cours`}
      />

      <p className="concept-visualizer__legend">
        {/* TODO: légende des clusters ou des axes */}
      </p>
    </div>
  );
}
