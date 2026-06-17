"""
Vectorisation des chunks via le modèle d'embedding d'Ollama.

Toute l'inférence reste locale : aucun appel cloud.
Le modèle par défaut est ``nomic-embed-text`` (dimension 768),
mais tout modèle d'embedding disponible dans Ollama peut être utilisé.

Les appels sont groupés en batches pour minimiser les aller-retours HTTP.
"""

from __future__ import annotations

import numpy as np

from chunking.chunker import Chunk


def vectoriser_chunks(
    chunks: list[Chunk],
    modele: str = "nomic-embed-text",
    batch_size: int = 32,
) -> list[dict]:
    """
    Génère un vecteur d'embedding pour chaque chunk.

    Les chunks sont envoyés à Ollama par groupes de ``batch_size``
    pour éviter la surcharge mémoire sur de gros corpus.

    Args:
        chunks: Chunks produits par ``decouper_en_chunks()``.
        modele: Nom du modèle Ollama (doit être téléchargé localement).
        batch_size: Nombre de chunks par appel API.

    Returns:
        Liste de dicts ``{"chunk": Chunk, "embedding": np.ndarray}``
        dans le même ordre que ``chunks``.

    Raises:
        ConnectionError: Si l'API Ollama n'est pas joignable.
        ValueError: Si la dimension retournée est incohérente avec le modèle.
    """
    raise NotImplementedError


def vectoriser_requete(
    question: str,
    modele: str = "nomic-embed-text",
) -> np.ndarray:
    """
    Génère l'embedding d'une question posée par l'étudiant.

    Le modèle doit être identique à celui utilisé pour vectoriser les chunks,
    sinon la similarité cosinus n'a pas de sens.

    Args:
        question: Question en langage naturel.
        modele: Nom du modèle d'embedding Ollama.

    Returns:
        Vecteur d'embedding (``np.ndarray`` de dtype ``float32``).
    """
    raise NotImplementedError


def _appel_ollama_embed(textes: list[str], modele: str) -> list[list[float]]:
    """
    Appel HTTP brut à l'endpoint d'embedding d'Ollama.

    Endpoint : POST http://localhost:11434/api/embed
    Corps :    ``{"model": modele, "input": [texte1, texte2, ...]}``
    Réponse :  ``{"embeddings": [[...], [...]]}``

    Args:
        textes: Liste de chaînes à vectoriser.
        modele: Modèle Ollama à utiliser.

    Returns:
        Liste de vecteurs (liste de floats), dans le même ordre que ``textes``.
    """
    raise NotImplementedError


def normaliser_vecteur(vecteur: np.ndarray) -> np.ndarray:
    """
    Normalise un vecteur à la norme L2 (norme = 1).

    La normalisation est nécessaire pour que le produit scalaire
    soit équivalent à la similarité cosinus lors de la recherche.

    Args:
        vecteur: Vecteur à normaliser.

    Returns:
        Vecteur normalisé (même dimension).
    """
    raise NotImplementedError
