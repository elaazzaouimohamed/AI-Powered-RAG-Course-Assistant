"""
Génération de quiz depuis le contenu des cours.

Le LLM reçoit un extrait de cours et un prompt structuré lui demandant
de produire des QCM en JSON. Le module valide la sortie JSON et
la transforme en objets Python utilisables par l'interface.

Limites connues :
  - La qualité des questions dépend du modèle LLM choisi.
  - Les formules mathématiques en image (cas 4 de l'extraction) ne sont
    pas transmises au LLM, donc aucune question sur ces formules ne sera générée.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Question:
    """
    Question à choix multiple générée par le LLM.

    Attributes:
        enonce: Texte de la question.
        choix: Liste de 4 propositions (étiquetées A, B, C, D).
        bonne_reponse: Étiquette de la bonne réponse (``"A"``, ``"B"``, etc.).
        explication: Justification de la bonne réponse, générée par le LLM.
        difficulte: Niveau de difficulté estimé.
        source_chunks: Identifiants des chunks utilisés pour générer la question.
    """

    enonce: str
    choix: list[str]
    bonne_reponse: str
    explication: str = ""
    difficulte: str = "moyen"
    source_chunks: list[str] = field(default_factory=list)


@dataclass
class Quiz:
    """
    Quiz complet associé à un cours.

    Attributes:
        titre: Titre du quiz.
        source: Nom du fichier PDF source.
        questions: Liste de :class:`Question`.
        nb_questions: Nombre de questions (égal à ``len(questions)``).
    """

    titre: str
    source: str
    questions: list[Question] = field(default_factory=list)

    @property
    def nb_questions(self) -> int:
        return len(self.questions)


def generer_quiz(
    chunks: list,
    nb_questions: int = 5,
    difficulte: str = "moyen",
    modele: str = "mistral",
) -> Quiz:
    """
    Génère un quiz depuis une liste de chunks de cours.

    Étapes :
      1. Sélectionner les chunks les plus denses en information
         (longueur, absence de répétitions).
      2. Construire le prompt via ``construire_prompt_quiz()``.
      3. Appeler le LLM via ``generer_reponse()``.
      4. Parser la réponse JSON et instancier les objets :class:`Question`.
      5. Retourner un objet :class:`Quiz` validé.

    Args:
        chunks: Liste de chunks (objets ``Chunk``) du cours cible.
        nb_questions: Nombre de questions souhaitées.
        difficulte: Niveau cible (``"facile"``, ``"moyen"``, ``"difficile"``).
        modele: Modèle Ollama à utiliser.

    Returns:
        Quiz généré avec ses questions.

    Raises:
        ValueError: Si le LLM retourne un JSON invalide après 3 tentatives.
    """
    raise NotImplementedError


def _selectionner_chunks_pertinents(
    chunks: list,
    nb_max: int = 10,
) -> list:
    """
    Sélectionne les chunks les plus adaptés à la génération de quiz.

    Heuristique : privilégier les chunks avec le plus de contenu textuel
    et exclure les chunks issus de pages avec alerte formule complexe
    (le LLM ne peut pas "voir" les formules en image).

    Args:
        chunks: Tous les chunks du cours.
        nb_max: Nombre maximum de chunks à sélectionner.

    Returns:
        Sous-liste de chunks sélectionnés.
    """
    raise NotImplementedError


def _parser_reponse_llm(reponse_json: str) -> list[Question]:
    """
    Parse la réponse JSON du LLM en objets :class:`Question`.

    Valide :
      - Présence des champs ``question``, ``choix``, ``reponse``, ``explication``.
      - Exactement 4 choix.
      - La bonne réponse correspond à l'une des étiquettes (A, B, C, D).

    Args:
        reponse_json: Chaîne JSON retournée par le LLM.

    Returns:
        Liste de :class:`Question` validées.

    Raises:
        ValueError: Si le JSON est malformé ou les champs requis sont absents.
    """
    raise NotImplementedError


def calculer_score(
    quiz: Quiz,
    reponses_etudiant: dict[int, str],
) -> dict:
    """
    Calcule le score d'un étudiant sur un quiz.

    Args:
        quiz: Quiz passé.
        reponses_etudiant: Dict ``{index_question: étiquette_choisie}``.

    Returns:
        Dict avec ``score`` (0–100), ``nb_correct``, ``nb_total``,
        et ``detail`` (liste de dicts par question avec résultat et explication).
    """
    raise NotImplementedError
