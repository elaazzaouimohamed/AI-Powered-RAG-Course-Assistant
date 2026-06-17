"""
Client pour le LLM local via l'API Ollama.

Supporte deux modes :
  - Génération complète (réponse buffée) : pour les cas où le texte complet
    est nécessaire avant traitement (ex: génération de quiz).
  - Streaming (token par token) : pour afficher la réponse progressivement
    dans l'interface Streamlit (meilleure expérience utilisateur).

Aucun appel cloud : tout passe par http://localhost:11434.
"""

from __future__ import annotations

from collections.abc import Generator


def generer_reponse(
    prompt: str,
    modele: str = "mistral",
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> str:
    """
    Génère une réponse complète depuis le LLM Ollama.

    Endpoint : POST http://localhost:11434/api/generate
    Corps     : ``{"model": modele, "prompt": prompt, "stream": false, ...}``

    Args:
        prompt: Prompt complet construit par ``prompts.py``.
        modele: Nom du modèle Ollama à utiliser.
        temperature: Contrôle la créativité (0 = déterministe, 1 = très créatif).
            Garder bas (0.1) pour les réponses factuelles de cours.
        max_tokens: Nombre maximum de tokens à générer.

    Returns:
        Réponse du LLM sous forme de chaîne.

    Raises:
        ConnectionError: Si Ollama n'est pas accessible.
        RuntimeError: Si le modèle retourne une erreur.
    """
    raise NotImplementedError


def streamer_reponse(
    prompt: str,
    modele: str = "mistral",
    temperature: float = 0.1,
) -> Generator[str, None, None]:
    """
    Génère une réponse en streaming, token par token.

    Utilise l'endpoint Ollama avec ``"stream": true``.
    Chaque ``yield`` émet un fragment de texte dès sa réception.

    Args:
        prompt: Prompt complet.
        modele: Modèle Ollama.
        temperature: Température de génération.

    Yields:
        Fragments de texte au fur et à mesure de la génération.

    Raises:
        ConnectionError: Si Ollama n'est pas accessible.
    """
    raise NotImplementedError


def verifier_disponibilite(
    modele: str,
    ollama_url: str = "http://localhost:11434",
) -> bool:
    """
    Vérifie qu'Ollama est lancé et que le modèle demandé est disponible.

    Endpoint : GET http://localhost:11434/api/tags

    Args:
        modele: Nom du modèle à vérifier.
        ollama_url: URL de base de l'API Ollama.

    Returns:
        True si Ollama répond et le modèle est dans la liste.
    """
    raise NotImplementedError
