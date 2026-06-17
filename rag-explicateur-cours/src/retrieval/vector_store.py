"""
Index vectoriel dense pour la recherche sémantique des chunks.

Utilise FAISS (``faiss-cpu``) comme moteur de similarité.
L'index est persisté sur disque (répertoire ``data/index/``) pour ne pas
avoir à re-vectoriser l'intégralité du corpus à chaque démarrage.

L'API publique expose uniquement ``ajouter_chunks`` et ``rechercher``,
ce qui facilite le remplacement futur de FAISS par ChromaDB ou Qdrant.
"""

from __future__ import annotations

import numpy as np

from chunking.chunker import Chunk


class IndexVectoriel:
    """
    Encapsule un index FAISS et la liste des chunks associés.

    Attributes:
        dimension: Dimension des vecteurs (doit correspondre au modèle d'embedding).
        chemin_persistence: Dossier où l'index et les métadonnées sont sauvegardés.
    """

    def __init__(self, dimension: int, chemin_persistence: str = "data/index"):
        """
        Initialise ou charge un index existant depuis le disque.

        Args:
            dimension: Dimension des vecteurs d'embedding.
            chemin_persistence: Dossier de sauvegarde de l'index.
        """
        raise NotImplementedError

    def ajouter_chunks(self, embeddings: list[dict]) -> None:
        """
        Ajoute des chunks et leurs embeddings à l'index.

        Les métadonnées (texte, source, page, image_path) sont stockées
        séparément dans une liste ordonnée parallèle à l'index FAISS.

        Args:
            embeddings: Liste de dicts ``{"chunk": Chunk, "embedding": np.ndarray}``
                produits par ``vectoriser_chunks()``.
        """
        raise NotImplementedError

    def rechercher(
        self,
        vecteur_requete: np.ndarray,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retourne les ``top_k`` chunks les plus proches de la requête.

        Args:
            vecteur_requete: Embedding de la question (même dimension que l'index).
            top_k: Nombre de résultats à retourner.

        Returns:
            Liste de dicts ``{"chunk": Chunk, "score": float}``
            triée par score décroissant (score = similarité cosinus, 0–1).
        """
        raise NotImplementedError

    def sauvegarder(self) -> None:
        """
        Persiste l'index FAISS et les métadonnées sur le disque.

        Fichiers créés dans ``chemin_persistence/`` :
          - ``index.faiss`` : index binaire FAISS
          - ``chunks.pkl``  : liste des Chunk sérialisés
        """
        raise NotImplementedError

    def charger(self) -> None:
        """
        Charge un index précédemment sauvegardé depuis le disque.

        Raises:
            FileNotFoundError: Si les fichiers d'index n'existent pas.
        """
        raise NotImplementedError

    def vider(self) -> None:
        """
        Vide l'index et supprime les fichiers de persistance.

        Utile pour réindexer un corpus depuis zéro.
        """
        raise NotImplementedError
