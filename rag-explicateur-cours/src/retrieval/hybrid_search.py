"""
Recherche hybride combinant score dense (FAISS) et score sparse (BM25).

La recherche hybride améliore la précision en combinant :
  - la recherche dense (similarité sémantique, bonne pour les paraphrases)
  - la recherche sparse BM25 (correspondance lexicale exacte, bonne pour
    les termes techniques ou les noms propres peu représentés dans les embeddings)

La fusion est réalisée par la méthode Reciprocal Rank Fusion (RRF) ou
par une combinaison linéaire pondérée (paramètre ``alpha``).
"""

from __future__ import annotations

import numpy as np

from chunking.chunker import Chunk
from retrieval.vector_store import IndexVectoriel


def recherche_hybride(
    question: str,
    vecteur_requete: np.ndarray,
    index: IndexVectoriel,
    corpus_chunks: list[Chunk],
    top_k: int = 5,
    alpha: float = 0.5,
) -> list[dict]:
    """
    Effectue une recherche hybride et retourne les ``top_k`` chunks pertinents.

    Algorithme :
      1. Recherche dense sur l'index FAISS → scores de similarité cosinus.
      2. Recherche BM25 sur le corpus textuel → scores BM25.
      3. Fusion des deux classements par combinaison linéaire pondérée :
         ``score_final = alpha * score_dense + (1 - alpha) * score_sparse``
      4. Tri final et retour des ``top_k`` meilleurs résultats.

    Args:
        question: Question en langage naturel (utilisée pour BM25).
        vecteur_requete: Embedding de la question (utilisé pour FAISS).
        index: Index vectoriel chargé.
        corpus_chunks: Liste complète des chunks (pour BM25).
        top_k: Nombre de résultats à retourner.
        alpha: Poids du score dense (0 = BM25 pur, 1 = FAISS pur, 0.5 = équilibré).

    Returns:
        Liste de dicts ``{"chunk": Chunk, "score": float, "rank_dense": int, "rank_sparse": int}``
        triée par score final décroissant.
    """
    raise NotImplementedError


def _recherche_bm25(
    question: str,
    corpus: list[Chunk],
    top_k: int,
) -> list[dict]:
    """
    Recherche BM25 sur le corpus de chunks.

    Construit un index BM25 à la volée sur ``corpus`` via la bibliothèque
    ``rank-bm25``. Pour un corpus statique, l'index devrait être pré-calculé
    et mis en cache.

    Args:
        question: Tokens de la question (après tokenisation basique).
        corpus: Liste de chunks sur lesquels chercher.
        top_k: Nombre de résultats à retourner.

    Returns:
        Liste de dicts ``{"chunk": Chunk, "score": float}``.
    """
    raise NotImplementedError


def _fusion_scores(
    resultats_dense: list[dict],
    resultats_sparse: list[dict],
    alpha: float,
    top_k: int,
) -> list[dict]:
    """
    Fusionne les classements dense et sparse par combinaison linéaire pondérée.

    Les scores sont normalisés (min-max) avant fusion pour les rendre comparables.

    Args:
        resultats_dense: Résultats FAISS avec scores.
        resultats_sparse: Résultats BM25 avec scores.
        alpha: Poids du score dense dans la fusion.
        top_k: Nombre de résultats à retourner.

    Returns:
        Liste de dicts fusionnés et triés par score final.
    """
    raise NotImplementedError
