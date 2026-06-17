"""
Structuration du contenu extrait d'un PDF en JSON via l'API NVIDIA (Kimi K2).

Pipeline :
  1. extraire_pdf() (pdf_extractor.py) produit le texte brut page par page.
  2. Ce module concatène ce texte (avec repères de page) et l'envoie au
     modèle Kimi K2 via l'API NVIDIA, accompagné d'un prompt qui décrit
     précisément la structure JSON attendue (titre, métadonnées, parties,
     concepts, formules, exemples, exercices, remarques, notes...).
  3. La réponse du modèle est parsée en dict Python et peut être sauvegardée
     sur disque.

Intégration NVIDIA :
  - Clé API lue UNIQUEMENT depuis la variable d'environnement NVIDIA_API_KEY.
  - La clé n'est jamais affichée dans les logs ni dans les messages d'erreur.

Sécurité :
  Placer NVIDIA_API_KEY dans le fichier .env local (jamais commité dans Git).
  Exemple de fichier .env :
      NVIDIA_API_KEY=nvapi-...
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # sans python-dotenv, définir NVIDIA_API_KEY manuellement dans le shell

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Modèle NVIDIA (surchargeable via variable d'environnement)
NVIDIA_MODEL: str = os.environ.get("NVIDIA_MODEL", "moonshotai/kimi-k2.6")

# Température basse : on veut une structuration fidèle, pas créative
NVIDIA_TEMPERATURE = 0.2
NVIDIA_TOP_P = 1.0
NVIDIA_MAX_TOKENS = 16384

# Délai d'attente pour l'appel API (en secondes) — les cours longs prennent du temps
NVIDIA_TIMEOUT = 600

# Nombre de pages envoyées par appel au modèle.
# NVIDIA_MAX_TOKENS limite la taille de la réponse : pour un cours dense
# (formules, exemples, exercices), 5 pages produisent déjà ~16k tokens de JSON.
# Découper en lots évite que la réponse soit tronquée et perde les dernières pages.
# Kimi K2.6 accepte jusqu'à 256K tokens de contexte : un cours de 25-30 pages
# (~13k tokens de prompt) tient largement dans un seul appel.
PAGES_PAR_LOT = 30

# Le flux SSE de l'API NVIDIA se coupe parfois prématurément (réponse vide,
# erreur réseau) sans raison liée au prompt. On retente automatiquement.
NVIDIA_MAX_TENTATIVES = 2
NVIDIA_DELAI_RETENTATIVE = 5  # secondes, multiplié par le numéro de la tentative

_PROMPT_STRUCTURATION = """TA MISSION : extraire et structurer le contenu du cours en JSON bien organisé. Utilise ta logique. Par exemple, essaie d'analyser et de comprendre à quel champ appartient un texte : est-ce une définition, une propriété, une méthode, un exemple, une formule, etc., même si la partie n'a pas de titre indiquant explicitement le champ auquel elle appartient. Ce JSON sera utilisé par un autre LLM local pour expliquer ce cours à un étudiant : il doit donc être fiable à 100%, fidèle au contenu source et structurellement homogène.

RÈGLES STRICTES (à respecter scrupuleusement) :
- Analyse TOUT le texte fourni, sans rien ignorer.
- Extrait TOUS les éléments (définitions, propriétés, méthodes, théorèmes, formules, preuves, remarques, exemples, exercices, notes) sans rien rater, modifier, résumer ou supprimer.
- N'INVENTE RIEN. N'ajoute AUCUNE information, AUCUN nom propre, AUCUN mot, AUCUNE formule, AUCUN exemple qui n'est pas explicitement présent dans le texte fourni — même si tu penses le savoir par ailleurs. Si une information est absente du texte, mets `null` (ou `[]` pour une liste). Ne complète JAMAIS avec tes connaissances générales.
- RÉPONDS UNIQUEMENT EN FRANÇAIS. N'insère aucun mot, sigle, nom ou caractère dans une autre langue (anglais, chinois, etc.), sauf s'il apparaît littéralement dans le texte source (ex : un terme technique anglais déjà présent dans le cours).
- Respecte EXACTEMENT les noms de clés JSON du schéma ci-dessous : pas de variante orthographique (ex : "formules" et non "formulas"), pas d'espace avant/après une clé (ex : "remarques" et non " remarques"), pas d'accent différent (ex : "année" et non "annee").
- Chaque objet "concept" DOIT contenir TOUTES les clés listées dans le schéma ci-dessous, dans cet ordre, même si leur valeur est `null` ou `[]`. Ne confonds pas les champs : une formule va dans "formules", une remarque dans "remarques", une démonstration dans "preuves", etc.
- Le champ "type" d'un concept doit être l'une de ces valeurs exactes : "definition", "propriete", "methode", "theoreme", "autre".
- "page_start" et "page_end" sont des nombres entiers correspondant aux numéros de page réels du PDF.
- "numero" est un entier représentant l'ordre de la partie dans le cours (1, 2, 3...).
- Chaque page peut être suivie d'une liste "Images de la page N : - chemin/vers/image.png".
  Si une image illustre une partie (graphique général), ajoute son chemin dans le champ "images" de la partie.
  Si une image illustre un concept, un exemple ou un exercice précis, ajoute son chemin dans le champ
  "images_associees" de l'élément correspondant. Sinon, laisse `[]`.

FORMAT JSON REQUIS (respecte exactement cette structure et ces noms de clés) :

{
  "titre_annale": "Titre du cours",
  "metadata": {
    "nombre_pages": 0,
    "auteur": null,
    "année": null,
    "niveau": null,
    "langue": "fr",
    "domaine": "Domaine du cours (ex : Statistique, Analyse, Algorithmique...)",
    "mots_cles": ["mot-clé 1", "mot-clé 2"]
  },
  "parties": [
    {
      "titre": "Titre chapitre/partie",
      "numero": 1,
      "page_start": 1,
      "page_end": 5,
      "introduction": "Résumé d'introduction de la partie, ou null si absent du cours",
      "synthese": null,
      "images": [],
      "concepts": [
        {
          "nom": "Nom concept",
          "type": "definition",
          "definition": "Définition détaillée telle qu'elle apparaît dans le cours",
          "formules": [
            {
              "nom": "Nom de la formule",
              "latex": "Formule en LaTeX",
              "brut": "Formule en notation simple (texte brut)",
              "explication": "Explication des variables/termes",
              "conditions": "Conditions d'application, ou null"
            }
          ],
          "preuves": [
            {
              "titre": "Titre de la démonstration",
              "contenu": "Contenu de la démonstration"
            }
          ],
          "remarques": ["Remarque 1"],
          "exemples": [
            {
              "titre": "Titre de l'exemple",
              "description": "Énoncé de l'exemple",
              "solution": "Solution détaillée, ou null si non résolue",
              "images_associees": []
            }
          ],
          "exercices": [
            {
              "titre": "Titre de l'exercice",
              "description": "Énoncé de l'exercice",
              "solution": null,
              "images_associees": []
            }
          ],
          "images_associees": [],
          "notes": ["Note 1"]
        }
      ]
    }
  ]
}

IMPORTANT : réponds UNIQUEMENT avec l'objet JSON final, sans aucun texte avant ou après, et sans bloc de code markdown (pas de ```)."""


# ── Fonction publique principale ──────────────────────────────────────────────

def structurer_pdf_en_json(
    pages: list[dict],
    titre_pdf: str,
    chemin_sortie: Optional[str] = None,
    afficher_progression: bool = False,
    pages_par_lot: int = PAGES_PAR_LOT,
) -> dict:
    """
    Envoie le texte extrait d'un PDF (sortie de extraire_pdf) au modèle Kimi K2
    via l'API NVIDIA pour le structurer en JSON selon le schéma du cours.

    Le PDF est traité par lots de ``pages_par_lot`` pages : un appel API par lot,
    les "parties" obtenues étant ensuite concaténées dans l'ordre. Ce découpage
    est nécessaire car la réponse d'un seul appel est limitée à NVIDIA_MAX_TOKENS
    tokens — au-delà, le modèle tronque sa réponse et les dernières pages
    du cours seraient perdues.

    Args:
        pages: Liste de dicts par page, telle que retournée par
            ``pdf_extractor.extraire_pdf`` (utilise les champs "page" et "text").
        titre_pdf: Nom du fichier PDF source, transmis au modèle comme indice
            pour le titre du cours.
        chemin_sortie: Si fourni, chemin du fichier .json où écrire le résultat
            (encodage UTF-8, indentation 2, caractères non-ASCII préservés).
        afficher_progression: Si True, affiche l'avancement (lot en cours,
            temps d'attente) pendant les appels à l'API NVIDIA (en mode
            non-streaming, la réponse n'arrive qu'une fois complète).
        pages_par_lot: Nombre de pages du PDF envoyées par appel API.

    Returns:
        Dict Python correspondant au JSON structuré complet (toutes les pages),
        avec une clé "parties" regroupant les parties détectées dans chaque lot.

    Raises:
        RuntimeError: Si NVIDIA_API_KEY est absente de l'environnement.
        requests.HTTPError: Si l'API NVIDIA répond avec un statut d'erreur.
        ValueError: Si la réponse du modèle n'est pas un JSON valide.
    """
    cle = os.environ.get("NVIDIA_API_KEY")
    if not cle:
        raise RuntimeError("NVIDIA_API_KEY absente de l'environnement (.env)")

    lots = [pages[i : i + pages_par_lot] for i in range(0, len(pages), pages_par_lot)]

    resultat: dict = {
        "titre_annale": None,
        "metadata": {
            "nombre_pages": len(pages),
            "auteur": None,
            "année": None,
            "niveau": None,
            "langue": None,
            "domaine": None,
            "mots_cles": [],
        },
        "parties": [],
    }

    for i, lot in enumerate(lots, start=1):
        if afficher_progression:
            print(
                f"  Lot {i}/{len(lots)} (pages {lot[0]['page']}-{lot[-1]['page']} "
                f"sur {len(pages)})..."
            )

        donnees = _traiter_lot(lot, titre_pdf, len(pages), cle, afficher_progression)
        _fusionner_resultat(resultat, donnees)

    for numero, partie in enumerate(resultat["parties"], start=1):
        if isinstance(partie, dict):
            partie["numero"] = numero

    if chemin_sortie:
        Path(chemin_sortie).write_text(
            json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("JSON structuré écrit dans %s", chemin_sortie)

    return resultat


def _appeler_nvidia(prompt: str, cle: str, afficher_progression: bool) -> str:
    """
    Envoie un prompt au modèle NVIDIA et retourne le texte de la réponse.

    Le flux SSE de l'API NVIDIA se coupe parfois prématurément (réponse vide
    sans erreur explicite, coupure réseau) sans rapport avec le contenu du
    prompt. On retente automatiquement jusqu'à NVIDIA_MAX_TENTATIVES fois.
    """
    for tentative in range(1, NVIDIA_MAX_TENTATIVES + 1):
        try:
            return _appeler_nvidia_une_fois(prompt, cle, afficher_progression)
        except (RuntimeError, requests.exceptions.RequestException) as exc:
            if tentative == NVIDIA_MAX_TENTATIVES:
                raise
            attente = NVIDIA_DELAI_RETENTATIVE * tentative
            print(
                f"\n  Erreur lors de l'appel à l'API ({exc}). "
                f"Nouvelle tentative {tentative + 1}/{NVIDIA_MAX_TENTATIVES} "
                f"dans {attente}s..."
            )
            time.sleep(attente)

    raise AssertionError("unreachable")  # pragma: no cover


def _traiter_lot(
    lot: list[dict],
    titre_pdf: str,
    nb_pages_total: int,
    cle: str,
    afficher_progression: bool,
) -> dict:
    """
    Structure un lot de pages en JSON, avec repli adaptatif en cas d'échec.

    Si l'appel API échoue malgré les tentatives de _appeler_nvidia() (flux SSE
    vide à répétition, erreur réseau, JSON invalide), le lot est divisé en
    deux sous-lots plus petits, traités récursivement puis fusionnés. Cela
    réduit le temps de génération par appel et permet de contourner les échecs
    liés à un gros volume de contenu, sans jamais perdre de pages.
    """
    prompt = _construire_prompt(lot, titre_pdf, nb_pages_total)
    try:
        contenu = _appeler_nvidia(prompt, cle, afficher_progression)
        return _extraire_json(contenu)
    except (RuntimeError, requests.exceptions.RequestException, ValueError) as exc:
        if len(lot) <= 1:
            raise

        milieu = len(lot) // 2
        if afficher_progression:
            print(
                f"\n  Échec sur le lot des pages {lot[0]['page']}-{lot[-1]['page']} "
                f"({exc}). Division en deux sous-lots de {milieu} et "
                f"{len(lot) - milieu} pages..."
            )

        gauche = _traiter_lot(lot[:milieu], titre_pdf, nb_pages_total, cle, afficher_progression)
        droite = _traiter_lot(lot[milieu:], titre_pdf, nb_pages_total, cle, afficher_progression)
        return _fusionner_donnees(gauche, droite)


def _fusionner_donnees(a: dict, b: dict) -> dict:
    """Fusionne deux résultats de sous-lots (utilisé par le repli adaptatif de _traiter_lot)."""
    a.setdefault("parties", []).extend(b.get("parties", []))

    meta_a = a.setdefault("metadata", {}) if "metadata" in a or "metadata" in b else None
    meta_b = b.get("metadata") or {}
    if meta_a is not None:
        for champ, valeur in meta_b.items():
            if champ == "mots_cles" and isinstance(valeur, list):
                existants = meta_a.setdefault("mots_cles", [])
                for mot in valeur:
                    if mot not in existants:
                        existants.append(mot)
            elif meta_a.get(champ) is None and valeur is not None:
                meta_a[champ] = valeur

    for champ, valeur in b.items():
        if champ in ("parties", "metadata"):
            continue
        if a.get(champ) is None and valeur is not None:
            a[champ] = valeur

    return a


def _appeler_nvidia_une_fois(prompt: str, cle: str, afficher_progression: bool) -> str:
    """
    Effectue un unique appel à l'API NVIDIA et retourne le texte de la réponse.

    Toujours en streaming (stream=True) : pour une génération longue (gros
    lot, beaucoup de concepts), une requête non-streaming peut dépasser le
    délai de la passerelle NVIDIA et renvoyer un 504 Gateway Timeout à corps
    vide. Le streaming maintient la connexion active pendant la génération.

    Le flux SSE se coupe parfois prématurément (un seul chunk vide reçu) sans
    rapport avec le contenu du prompt : dans ce cas on lève une RuntimeError,
    rattrapée par _appeler_nvidia() (retry) puis par _traiter_lot() (division
    du lot en sous-lots plus petits si les retries échouent aussi).
    """
    headers = {
        "Authorization": f"Bearer {cle}",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": NVIDIA_MAX_TOKENS,
        "temperature": NVIDIA_TEMPERATURE,
        "top_p": NVIDIA_TOP_P,
        "stream": True,
    }

    # Modèles DeepSeek V4 : désactiver le mode "thinking" pour limiter le temps
    # de réponse (un long raisonnement sur un gros prompt peut dépasser le
    # délai de la passerelle NVIDIA et provoquer un 504 Gateway Timeout).
    if "deepseek-v4" in NVIDIA_MODEL:
        payload["chat_template_kwargs"] = {"thinking": False}

    reponse = requests.post(
        NVIDIA_API_URL, headers=headers, json=payload,
        timeout=NVIDIA_TIMEOUT, stream=True,
    )
    if not reponse.ok:
        raise RuntimeError(
            f"Erreur API NVIDIA ({reponse.status_code}) pour le modèle "
            f"'{NVIDIA_MODEL}' : {reponse.text[:500]}"
        )

    contenu = _lire_flux_sse(reponse, afficher_progression)
    if afficher_progression:
        print()  # nouvelle ligne après la barre de progression
    return contenu


def _lire_flux_sse(reponse: requests.Response, afficher_progression: bool) -> str:
    """
    Lit une réponse en streaming (Server-Sent Events) de l'API NVIDIA et,
    si demandé, affiche la progression (nombre de caractères reçus).

    Retourne le contenu complet concaténé.
    """
    morceaux: list[str] = []
    total = 0
    tronque = False
    lignes_brutes: list[str] = []

    for ligne in reponse.iter_lines():
        if not ligne:
            continue
        ligne = ligne.decode("utf-8")
        lignes_brutes.append(ligne)

        if not ligne.startswith("data: "):
            continue

        donnees_brutes = ligne[len("data: "):]
        if donnees_brutes.strip() == "[DONE]":
            break

        try:
            morceau = json.loads(donnees_brutes)
        except json.JSONDecodeError:
            continue

        if "error" in morceau:
            raise RuntimeError(f"Erreur retournée par l'API NVIDIA : {morceau['error']}")

        try:
            choix = morceau["choices"][0]
            delta = choix["delta"].get("content", "")
            if choix.get("finish_reason") == "length":
                tronque = True
        except (KeyError, IndexError):
            continue

        if delta:
            morceaux.append(delta)
            total += len(delta)
            if afficher_progression:
                print(f"  Génération en cours... {total} caractères reçus", end="\r", flush=True)

    if tronque:
        print(
            f"\n  ATTENTION : la réponse a été coupée (limite de {NVIDIA_MAX_TOKENS} tokens "
            f"atteinte). Le JSON obtenu est probablement incomplet."
        )

    if not morceaux:
        apercu = "\n".join(lignes_brutes[:10])
        raise RuntimeError(
            "Réponse vide de l'API NVIDIA (aucun contenu généré). "
            f"Premières lignes brutes reçues :\n{apercu or '(aucune ligne reçue)'}"
        )

    return "".join(morceaux)


def _fusionner_resultat(resultat: dict, donnees: dict) -> None:
    """
    Fusionne le JSON obtenu pour un lot de pages dans le résultat global :
      - "titre_annale" et "metadata" : on garde la première valeur non-null trouvée.
      - "parties" : concaténées dans l'ordre des lots.
      - tout champ supplémentaire ajouté par le modèle est conservé dès sa
        première apparition.
    """
    if resultat["titre_annale"] is None and donnees.get("titre_annale"):
        resultat["titre_annale"] = donnees["titre_annale"]

    meta_lot = donnees.get("metadata") or {}
    for champ, valeur in meta_lot.items():
        if champ == "nombre_pages":
            continue
        if champ == "mots_cles":
            if isinstance(valeur, list):
                existants = resultat["metadata"].setdefault("mots_cles", [])
                for mot in valeur:
                    if mot not in existants:
                        existants.append(mot)
            continue
        if resultat["metadata"].get(champ) is None and valeur is not None:
            resultat["metadata"][champ] = valeur

    resultat["parties"].extend(donnees.get("parties", []))

    for champ, valeur in donnees.items():
        if champ not in resultat:
            resultat[champ] = valeur


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _construire_prompt(pages: list[dict], titre_pdf: str, nb_pages_total: int) -> str:
    """
    Construit le prompt complet envoyé pour un lot de pages : instructions de
    structuration + cours converti en Markdown.
    """
    markdown = _construire_markdown(pages)
    pages_str = (
        f"{pages[0]['page']}-{pages[-1]['page']}"
        if len(pages) > 1
        else str(pages[0]["page"])
    )

    return (
        f"{_PROMPT_STRUCTURATION}\n\n"
        f"---\n"
        f"NOM DU FICHIER SOURCE : {titre_pdf}\n"
        f"NOMBRE DE PAGES TOTAL DU COURS : {nb_pages_total}\n"
        f"PAGES TRAITÉES DANS CET APPEL : {pages_str}\n\n"
        f"COURS AU FORMAT MARKDOWN (une section par page) :\n\n{markdown}"
    )


def _construire_markdown(pages: list[dict]) -> str:
    """
    Convertit les pages extraites (sortie de extraire_pdf) en un document
    Markdown unique, plus compact et mieux structuré pour le modèle qu'un
    simple dump de texte brut séparé par des "--- Page N ---".

    Chaque page devient une section "## Page N". Si une formule LaTeX a été
    détectée sur la page (champ formule_latex), elle est ajoutée dans un bloc
    de code ```latex``` à la suite du texte.
    """
    sections: list[str] = []

    for p in pages:
        section = f"## Page {p['page']}\n\n{p['text'].strip()}"
        if p.get("formule_latex"):
            section += f"\n\n```latex\n{p['formule_latex'].strip()}\n```"
        if p.get("image_paths"):
            images = "\n".join(f"- {chemin}" for chemin in p["image_paths"])
            section += f"\n\nImages de la page {p['page']} :\n{images}"
        sections.append(section)

    return "\n\n".join(sections)


def _extraire_json(texte: str) -> dict:
    """
    Parse la réponse du modèle en dict JSON.

    Tolère plusieurs cas fréquents avec les modèles de raisonnement :
      - blocs ```json ... ``` autour du JSON ;
      - bloc <think>...</think> précédant la réponse ;
      - texte parasite avant/après l'objet JSON ("Extra data") ;
      - plusieurs objets JSON concaténés (on garde le plus pertinent,
        c'est-à-dire celui qui contient la clé "parties", sinon le plus grand).
    """
    texte = texte.strip()

    # Retire un éventuel bloc de raisonnement avant la réponse
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()

    if texte.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texte, re.DOTALL)
        if match:
            texte = match.group(1)

    objets = _extraire_objets_json(texte)
    if not objets:
        raise ValueError("Aucun objet JSON valide trouvé dans la réponse du modèle")

    candidats = [o for o in objets if "parties" in o]
    if candidats:
        return max(candidats, key=lambda o: len(json.dumps(o)))

    # Réponse tronquée : l'objet englobant {"parties": [...]} n'a pas pu être
    # parsé entièrement (seul un fragment, comme une "partie" isolée, a pu être
    # récupéré). On lève une erreur plutôt que de renvoyer ce fragment partiel :
    # _traiter_lot() rattrape cette erreur et redécoupe le lot en sous-lots plus
    # petits, ce qui a de bien meilleures chances de produire une réponse complète.
    raise ValueError(
        "Aucun objet JSON contenant une clé \"parties\" trouvé dans la réponse "
        "du modèle (réponse probablement tronquée)"
    )


def _extraire_objets_json(texte: str) -> list[dict]:
    """
    Recherche tous les objets JSON top-level ``{...}`` présents dans le texte
    et retourne ceux qui parsent correctement.

    Utilisé pour ignorer le texte parasite autour du JSON et pour gérer le
    cas où le modèle renvoie plusieurs objets JSON concaténés.
    """
    decoder = json.JSONDecoder()
    objets: list[dict] = []
    idx = 0
    n = len(texte)

    while idx < n:
        debut = texte.find("{", idx)
        if debut == -1:
            break
        try:
            obj, fin = decoder.raw_decode(texte, debut)
            if isinstance(obj, dict):
                objets.append(obj)
            idx = fin
        except json.JSONDecodeError:
            idx = debut + 1

    return objets


# ── Test manuel en ligne de commande ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    from pdf_extractor import extraire_pdf

    # Évite UnicodeEncodeError sur la console Windows (cp1252) lorsque le PDF
    # contient des caractères hors de ce jeu (symboles mathématiques, etc.).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("Usage: python structuration_json.py chemin/vers/fichier.pdf [sortie.json]")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    chemin_pdf = sys.argv[1]
    chemin_json = sys.argv[2] if len(sys.argv) > 2 else str(Path(chemin_pdf).with_suffix(".json"))

    print(f"[1/3] Extraction du texte depuis {chemin_pdf}...")
    # exclure_repetitions=True : retire les en-têtes/pieds de page répétés sur
    # la majorité des pages (titre du cours, numéro de page...), qui n'apportent
    # aucune information utile mais sont comptés à chaque page dans le prompt.
    pages = extraire_pdf(chemin_pdf, exclure_repetitions=True)

    print(f"[2/3] Envoi au modèle {NVIDIA_MODEL} via l'API NVIDIA "
          f"({len(pages)} pages, cela peut prendre plusieurs minutes)...")
    resultat = structurer_pdf_en_json(
        pages, Path(chemin_pdf).name, chemin_json, afficher_progression=True
    )

    print(f"[3/3] Terminé. JSON structuré écrit dans {chemin_json}")
