"""
Découpage du JSON structuré (produit par structuration_json.py) en chunks
indexables pour la recherche hybride.

Stratégie : Contextual Retrieval — chaque chunk atomique (définition, formule,
exemple, exercice…) porte un préfixe [Chapitre: X | Concept: Y] qui réduit
les erreurs de retrieval de ~49 % par rapport aux chunks sans contexte.

Deux niveaux hiérarchiques :
  PARENT  : contexte complet du concept  → envoyé au LLM pour la réponse
  CHILD   : item atomique avec préfixe   → utilisé pour la recherche vectorielle
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """
    Unité de texte indexable produite depuis le JSON structuré.

    Attributes:
        texte:           Contenu du chunk child (avec préfixe contextuel).
        chunk_id:        Identifiant unique.
        chapitre:        Titre du chapitre/partie d'origine.
        concept:         Nom du concept d'origine.
        type_concept:    Type du concept (theoreme, definition, algorithme…).
        type_chunk:      Type d'item atomique (definition, formule, exemple…).
        parent_content:  Contexte complet du concept — envoyé au LLM.
        source:          Stem du fichier JSON d'origine.
        image_path:      Chemin image associé (optionnel).
        metadata:        Métadonnées supplémentaires.
    """

    texte: str
    chunk_id: str
    chapitre: str
    concept: str
    type_concept: str
    type_chunk: str
    parent_content: str
    source: str = ""
    image_path: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        """Retourne les métadonnées ChromaDB (valeurs scalaires uniquement)."""
        return {
            "chapitre":       self.chapitre,
            "concept":        self.concept,
            "type_concept":   self.type_concept,
            "type_chunk":     self.type_chunk,
            "parent_content": self.parent_content,
            "source":         self.source,
        }


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _texte_formule(f) -> str:
    """Convertit une formule (dict ou str) en texte lisible."""
    if isinstance(f, dict):
        cond = f' | Conditions: {f["conditions"]}' if f.get("conditions") else ""
        return f'{f.get("nom", "")}: {f.get("brut", "")}. {f.get("explication", "")}{cond}'
    return str(f)


def _construire_parent(partie: dict, concept: dict) -> str:
    """Construit le texte PARENT complet (contexte LLM) pour un concept."""
    p_titre = partie.get("titre", "General")
    p_intro = partie.get("introduction") or ""
    nom     = concept.get("nom") or concept.get("titre") or "General"
    type_c  = concept.get("type", "autre")

    lignes = [
        f"Chapitre: {p_titre}",
        f"Concept: {nom} (type: {type_c})",
    ]
    if p_intro:
        lignes.append(f"Introduction: {p_intro}")
    if concept.get("definition"):
        lignes.append(f'Definition: {concept["definition"]}')
    for f in concept.get("formules", []):
        lignes.append(f"Formule: {_texte_formule(f)}")
    for p in concept.get("preuves", []):
        if isinstance(p, dict):
            lignes.append(f'Preuve [{p.get("titre", "")}]: {p.get("contenu", "")}')
    for r in concept.get("remarques", []):
        lignes.append(f"Remarque: {r}")
    for ex in concept.get("exemples", []):
        if isinstance(ex, dict):
            sol = f' Solution: {ex["solution"]}' if ex.get("solution") else ""
            lignes.append(f'Exemple [{ex.get("titre", "")}]: {ex.get("description", "")}{sol}')
    for ex in concept.get("exercices", []):
        if isinstance(ex, dict):
            donnees = ex.get("description") or json.dumps(
                ex.get("donnees", {}), ensure_ascii=False
            )
            sol = ""
            if ex.get("solution_detaillee"):
                sol = f' Solution: {json.dumps(ex["solution_detaillee"], ensure_ascii=False)}'
            elif ex.get("solution"):
                sol = f' Solution: {ex["solution"]}'
            lignes.append(f'Exercice [{ex.get("titre", "")}]: {donnees}{sol}')
    for n in concept.get("notes", []):
        lignes.append(f"Note: {n}")
    for champ in ("theoremes", "methodes"):
        for item in concept.get(champ, []):
            if isinstance(item, dict):
                lignes.append(
                    f'{champ.capitalize()[:-1]}: {item.get("nom", "")} — {item.get("explication", "")}'
                )
    return "\n".join(lignes)


def _chunks_concept(concept: dict, prefixe: str, meta_base: dict, global_counter: list) -> list[Chunk]:
    """Génère tous les chunks CHILD pour un concept donné."""
    chunks: list[Chunk] = []

    def _ajout(texte: str, type_chunk: str) -> None:
        cid = f'{meta_base["source"]}::chunk_{global_counter[0]}'
        chunks.append(Chunk(
            texte=texte,
            chunk_id=cid,
            chapitre=meta_base["chapitre"],
            concept=meta_base["concept"],
            type_concept=meta_base["type_concept"],
            type_chunk=type_chunk,
            parent_content=meta_base["parent_content"],
            source=meta_base["source"],
        ))
        global_counter[0] += 1

    if concept.get("definition"):
        _ajout(f'{prefixe} [definition] {concept["definition"]}', "definition")

    for f in concept.get("formules", []):
        _ajout(f"{prefixe} [formule] {_texte_formule(f)}", "formule")

    for p in concept.get("preuves", []):
        if isinstance(p, dict):
            _ajout(
                f'{prefixe} [preuve] {p.get("titre", "")}: {p.get("contenu", "")}',
                "preuve",
            )

    for r in concept.get("remarques", []):
        _ajout(f"{prefixe} [remarque] {r}", "remarque")

    for ex in concept.get("exemples", []):
        if isinstance(ex, dict):
            sol = f' Solution: {ex["solution"]}' if ex.get("solution") else ""
            _ajout(
                f'{prefixe} [exemple] {ex.get("titre", "")}: {ex.get("description", "")}{sol}',
                "exemple",
            )

    for ex in concept.get("exercices", []):
        if isinstance(ex, dict):
            donnees = ex.get("description") or json.dumps(
                ex.get("donnees", {}), ensure_ascii=False
            )
            sol = ""
            if ex.get("solution_detaillee"):
                sol = f' Solution: {json.dumps(ex["solution_detaillee"], ensure_ascii=False)}'
            elif ex.get("solution"):
                sol = f' Solution: {ex["solution"]}'
            _ajout(
                f'{prefixe} [exercice] {ex.get("titre", "")}: {donnees}{sol}',
                "exercice",
            )

    for n in concept.get("notes", []):
        _ajout(f"{prefixe} [note] {n}", "note")

    for champ in ("theoremes", "methodes"):
        for item in concept.get(champ, []):
            if isinstance(item, dict):
                _ajout(
                    f'{prefixe} [{champ[:-1]}] {item.get("nom", "")} — {item.get("explication", "")}',
                    champ[:-1],
                )

    return chunks


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def construire_chunks(dataset: dict, source: str = "") -> list[Chunk]:
    """
    Construit la liste de chunks depuis le JSON structuré produit par
    ``structuration_json.py``.

    Chaque chunk porte :
    - Un préfixe contextuel ``[Chapitre: X | Concept: Y]``
    - Un tag de type (``[definition]``, ``[formule]``, ``[exemple]``…)
    - Le contexte parent complet dans ``parent_content``

    Args:
        dataset: Contenu JSON chargé depuis le fichier produit par structuration_json.
        source:  Nom du fichier source pour la traçabilité des chunk_id.

    Returns:
        Liste de :class:`Chunk` prêts pour l'indexation ChromaDB/BM25.
    """
    chunks: list[Chunk] = []
    global_counter = [0]  # compteur unique partagé entre tous les concepts

    for partie in dataset.get("parties", []):
        p_titre = partie.get("titre", "General")

        for concept in partie.get("concepts", []):
            nom    = concept.get("nom") or concept.get("titre") or "General"
            type_c = concept.get("type", "autre")

            parent_content = _construire_parent(partie, concept)
            prefixe        = f"[Chapitre: {p_titre} | Concept: {nom}]"

            meta_base = {
                "chapitre":       p_titre,
                "concept":        nom,
                "type_concept":   type_c,
                "parent_content": parent_content,
                "source":         source,
            }

            chunks.extend(_chunks_concept(concept, prefixe, meta_base, global_counter))

    return chunks


def charger_et_chunker(chemin_json: str) -> tuple[dict, list[Chunk]]:
    """
    Charge un fichier JSON produit par ``structuration_json.py`` et retourne
    le dataset brut et la liste de chunks indexables.

    Args:
        chemin_json: Chemin vers le fichier .json.

    Returns:
        ``(dataset, chunks)`` — dataset pour les métadonnées du cours,
        chunks pour l'indexation.
    """
    path = Path(chemin_json)
    with path.open(encoding="utf-8") as fh:
        dataset = json.load(fh)
    chunks = construire_chunks(dataset, source=path.stem)
    return dataset, chunks


# ---------------------------------------------------------------------------
# Ancienne interface (pages brutes depuis extraire_pdf) — non implémentée
# ---------------------------------------------------------------------------

def decouper_en_chunks(
    pages: list[dict],
    taille_max: int = 512,
    chevauchement: int = 50,
    strategie: str = "semantique",
) -> list[Chunk]:
    """
    Découpe les pages brutes de ``extraire_pdf()`` en chunks.

    Préférer ``construire_chunks()`` qui opère sur le JSON structuré produit
    par ``structuration_json.py`` et donne de bien meilleurs résultats.
    """
    raise NotImplementedError(
        "Utilisez construire_chunks(dataset) sur le JSON structuré de "
        "structuration_json.py plutôt que decouper_en_chunks() sur les pages brutes."
    )
