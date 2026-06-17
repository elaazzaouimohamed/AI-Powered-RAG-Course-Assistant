"""
Construction des prompts envoyés au LLM.

Chaque prompt est adapté à son cas d'usage :
  - Explication RAG : inclut le contexte documentaire et la question.
  - Génération de quiz : inclut un extrait de cours et les consignes de format.
  - Résumé : condense un ensemble de chunks en un résumé structuré.

Principes appliqués :
  - Instructions en français, claires et directes.
  - Le contexte documentaire est délimité explicitement pour éviter les hallucinations.
  - Température basse recommandée pour les prompts RAG (réponses factuelles).
"""

from __future__ import annotations

from chunking.chunker import Chunk


def construire_prompt_rag(
    question: str,
    chunks_contexte: list[Chunk],
    historique: list[dict] | None = None,
) -> str:
    """
    Construit le prompt RAG principal : contexte documentaire + question.

    Structure du prompt :
      [Instruction système] Tu es un assistant pédagogique...
      [Contexte] Voici des extraits de cours pertinents :
        --- Extrait 1 (source: ..., page: ...) ---
        {texte du chunk}
        ...
      [Question] {question}
      [Instruction] Réponds en français, uniquement à partir du contexte fourni.

    Args:
        question: Question posée par l'étudiant.
        chunks_contexte: Chunks récupérés par la recherche hybride.
        historique: Messages précédents de la conversation (optionnel),
            format ``[{"role": "user"|"assistant", "content": "..."}]``.

    Returns:
        Prompt complet prêt à être envoyé au LLM.
    """
    raise NotImplementedError


def construire_prompt_quiz(
    contenu_cours: str,
    nb_questions: int = 5,
    difficulte: str = "moyen",
) -> str:
    """
    Construit un prompt pour générer des questions à choix multiple depuis un texte.

    Le prompt demande au LLM de retourner un JSON structuré :
    ``[{"question": "...", "choix": ["A", "B", "C", "D"], "reponse": "A", "explication": "..."}]``

    Args:
        contenu_cours: Extrait de cours source (texte de plusieurs chunks concaténés).
        nb_questions: Nombre de questions à générer.
        difficulte: ``"facile"``, ``"moyen"`` ou ``"difficile"``.
            Influence la profondeur des questions demandée dans le prompt.

    Returns:
        Prompt complet pour la génération de quiz.
    """
    raise NotImplementedError


def construire_prompt_resume(
    chunks: list[Chunk],
    style: str = "paragraphe",
) -> str:
    """
    Construit un prompt pour résumer un ensemble de chunks de cours.

    Args:
        chunks: Chunks à résumer.
        style: ``"paragraphe"`` pour un texte continu,
               ``"points"`` pour une liste à puces.

    Returns:
        Prompt de résumé.
    """
    raise NotImplementedError


def _formater_contexte(chunks: list[Chunk]) -> str:
    """
    Formate les chunks en un bloc de contexte lisible pour le LLM.

    Chaque chunk est séparé par un délimiteur et annoté de sa source/page
    pour faciliter la citation et réduire les hallucinations.

    Args:
        chunks: Chunks à inclure dans le contexte.

    Returns:
        Chaîne formatée prête à être insérée dans un prompt.
    """
    raise NotImplementedError
