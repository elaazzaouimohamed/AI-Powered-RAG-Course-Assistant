"""
Démonstration RAG complète : question → recherche hybride → réponse NVIDIA.

Usage :
    python src/demo_rag.py                        # lance les 5 exemples
    python src/demo_rag.py --question "ta question"  # pose ta propre question
    python src/demo_rag.py --exemples             # affiche la liste des exemples
"""

import sys
import re
import json
import argparse
import collections
from pathlib import Path

from dotenv import load_dotenv
import os
import requests

# ── Chemins ──────────────────────────────────────────────────────────────────
_src    = Path(__file__).resolve().parent
_racine = _src.parent
sys.path.insert(0, str(_src))
load_dotenv(_racine / ".env")

from chunking.chunker import charger_et_chunker

CHROMA_DIR      = str(_racine / "data" / "chroma")
JSON_PATH       = str(_racine / "data" / "pdfs" / "Statistique_cours.json")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
NVIDIA_API_URL  = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL    = os.environ.get("NVIDIA_MODEL", "moonshotai/kimi-k2.6")
RRF_K           = 60
TOP_K           = 12
TOP_PARENTS     = 3

# ── Questions exemples (typiques d'un étudiant) ───────────────────────────────
EXEMPLES = [
    {
        "id": 1,
        "theme": "Définition fondamentale",
        "question": "Qu'est-ce que la variance et comment l'interpréter ?",
    },
    {
        "id": 2,
        "theme": "Formule à appliquer",
        "question": "Quelle est la formule de l'intervalle de confiance de la moyenne ?",
    },
    {
        "id": 3,
        "theme": "Compréhension d'un concept",
        "question": "Qu'est-ce qu'un estimateur sans biais ? Donner un exemple.",
    },
    {
        "id": 4,
        "theme": "Méthode / algorithme",
        "question": "Comment calculer l'estimateur du maximum de vraisemblance ?",
    },
    {
        "id": 5,
        "theme": "Exercice TD",
        "question": "Résoudre l'exercice du poste de péage : calculer la moyenne et la variance.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Chargement de l'index (une seule fois)
# ─────────────────────────────────────────────────────────────────────────────

def charger_index():
    import chromadb
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer

    print("Chargement de l'index...", end=" ", flush=True)
    dataset, chunks = charger_et_chunker(JSON_PATH)

    client     = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(f"cours_{Path(JSON_PATH).stem}")

    def tokenizer(t):
        t = t.lower().replace("'", " ").replace("-", " ")
        return [w for w in re.sub(r"[^\w\s]", " ", t).split() if len(w) > 1]

    textes     = [c.texte for c in chunks]
    ids        = [c.chunk_id for c in chunks]
    bm25       = BM25Okapi([tokenizer(t) for t in textes])
    embed      = SentenceTransformer(EMBEDDING_MODEL)
    print("OK")

    return {
        "dataset": dataset, "chunks": chunks, "textes": textes,
        "ids": ids, "collection": collection, "bm25": bm25,
        "tokenizer": tokenizer, "embed": embed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Recherche hybride RRF
# ─────────────────────────────────────────────────────────────────────────────

INTENTIONS = {
    "formule":    ["formule", "equation", "calculer", "calcul", "expression"],
    "exemple":    ["exemple", "illustrer", "concret", "application"],
    "exercice":   ["exercice", "td", "resoudre", "probleme", "solution"],
    "preuve":     ["demonstration", "preuve", "demontrer", "justifier"],
    "definition": ["definition", "qu est ce que", "signifie", "expliquer"],
}


def detecter_intention(query):
    q = query.lower()
    scores = {i: sum(1 for kw in mots if kw in q) for i, mots in INTENTIONS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def recherche_hybride(query, idx):
    rrf   = collections.defaultdict(float)
    q_vec = idx["embed"].encode(query, normalize_embeddings=True).tolist()
    intention = detecter_intention(query)

    res = idx["collection"].query(query_embeddings=[q_vec], n_results=TOP_K,
                                   include=["distances"])
    for rang, cid in enumerate(res["ids"][0]):
        rrf[cid] += 1.0 / (RRF_K + rang + 1)

    if intention:
        try:
            res_f = idx["collection"].query(
                query_embeddings=[q_vec], n_results=TOP_K,
                where={"type_chunk": intention}, include=["distances"]
            )
            for rang, cid in enumerate(res_f["ids"][0]):
                rrf[cid] += 2.0 / (RRF_K + rang + 1)
        except Exception:
            pass

    tokens      = idx["tokenizer"](query)
    scores_bm25 = idx["bm25"].get_scores(tokens)
    top_bm25    = sorted(range(len(scores_bm25)), key=lambda i: scores_bm25[i], reverse=True)[:TOP_K]
    for rang, i in enumerate(top_bm25):
        rrf[idx["ids"][i]] += 1.0 / (RRF_K + rang + 1)

    candidats = sorted(rrf, key=lambda x: rrf[x], reverse=True)[:TOP_K]
    return candidats, intention


def extraire_parents(candidats, idx):
    res = idx["collection"].get(ids=candidats, include=["metadatas"])
    vus, contextes = set(), []
    for meta in res["metadatas"]:
        parent = meta.get("parent_content", "")
        if parent not in vus:
            vus.add(parent)
            contextes.append({
                "concept":  meta.get("concept", ""),
                "chapitre": meta.get("chapitre", ""),
                "contenu":  parent,
            })
        if len(contextes) >= TOP_PARENTS:
            break
    return contextes


# ─────────────────────────────────────────────────────────────────────────────
# Génération via NVIDIA / Kimi K2.6
# ─────────────────────────────────────────────────────────────────────────────

def generer_reponse(question, contextes, titre_cours):
    cle = os.environ.get("NVIDIA_API_KEY", "")
    if not cle:
        return "[ERREUR] NVIDIA_API_KEY manquante dans .env"

    contexte_llm = ""
    for i, ctx in enumerate(contextes, 1):
        contexte_llm += (
            f"\n\n=== Contexte {i} : {ctx['concept']} "
            f"(Chapitre : {ctx['chapitre']}) ===\n{ctx['contenu']}"
        )

    prompt = f"""Tu es un professeur expert en "{titre_cours}" pour des étudiants universitaires.
Réponds à la question de l'étudiant de façon claire, rigoureuse et pédagogique,
en te basant UNIQUEMENT sur le contenu du cours fourni ci-dessous.
Si une information n'est pas dans le contexte, dis-le clairement plutôt que d'inventer.

[CONTENU DU COURS]
{contexte_llm}

[QUESTION DE L'ÉTUDIANT]
{question}

[CONSIGNES]
- Utilise les formules exactes du cours
- Structure ta réponse avec des titres clairs si nécessaire
- Sois précis, complet mais concis
- N'invente aucune information absente du contexte

Réponse du Professeur :"""

    headers = {
        "Authorization": f"Bearer {cle}",
        "Accept": "text/event-stream",
    }
    payload = {
        "model":       NVIDIA_MODEL,
        "messages":    [{"role": "user", "content": prompt}],
        "max_tokens":  2048,
        "temperature": 0.3,
        "top_p":       1.0,
        "stream":      True,
    }

    reponse_texte = ""
    try:
        resp = requests.post(NVIDIA_API_URL, headers=headers, json=payload,
                             timeout=120, stream=True)
        resp.raise_for_status()
        for ligne in resp.iter_lines():
            if not ligne:
                continue
            ligne_str = ligne.decode("utf-8") if isinstance(ligne, bytes) else ligne
            if not ligne_str.startswith("data: "):
                continue
            data = ligne_str[6:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
                choix = obj.get("choices", [])
                if not choix:
                    continue
                delta = choix[0].get("delta", {}).get("content", "")
                if delta:
                    reponse_texte += delta
                    print(delta, end="", flush=True)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
    except Exception as e:
        if reponse_texte:          # stream partiel reçu → retourner quand même
            print(f"\n  [avertissement] {e}", flush=True)
        else:
            return f"[ERREUR API] {e}"

    print()
    return reponse_texte


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline complet pour une question
# ─────────────────────────────────────────────────────────────────────────────

def repondre(question, idx, verbose=True):
    titre = idx["dataset"].get("titre_annale", "Statistique")

    if verbose:
        print(f"\n{'='*65}")
        print(f"  QUESTION : {question}")
        print(f"{'='*65}")

    candidats, intention = recherche_hybride(question, idx)
    contextes = extraire_parents(candidats, idx)

    if verbose:
        print(f"  Intention détectée : {intention or 'générale'}")
        print(f"\n{'─'*65}")
        print(f"  CHUNKS RÉCUPÉRÉS DEPUIS LA BASE DE DONNÉES ({len(contextes)} contextes)")
        print(f"{'─'*65}")
        for i, ctx in enumerate(contextes, 1):
            print(f"\n  [{i}] Concept  : {ctx['concept']}")
            print(f"       Chapitre : {ctx['chapitre']}")
            print(f"       Contenu  :")
            for ligne in ctx["contenu"].split("\n"):
                print(f"         {ligne}")
        print(f"\n{'─'*65}")
        print(f"  → Envoi au LLM ({NVIDIA_MODEL})...")
        print(f"{'─'*65}")
        print(f"\n  RÉPONSE GÉNÉRÉE :\n{'─'*65}")

    reponse = generer_reponse(question, contextes, titre)

    if verbose:
        print(f"{'─'*65}\n")

    return reponse


# ─────────────────────────────────────────────────────────────────────────────
# Sauvegarde
# ─────────────────────────────────────────────────────────────────────────────

def sauvegarder(question: str, reponse: str, theme: str = "") -> None:
    """Sauvegarde la question et la réponse dans data/qa/ avec un horodatage."""
    from datetime import datetime

    dossier = _racine / "data" / "qa"
    dossier.mkdir(parents=True, exist_ok=True)

    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Nom de fichier sécurisé depuis les 40 premiers caractères de la question
    slug = re.sub(r"[^\w\s-]", "", question[:40]).strip().replace(" ", "_").lower()
    chemin = dossier / f"{horodatage}_{slug}.txt"

    contenu = f"""Date    : {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Cours   : {Path(JSON_PATH).stem}
Theme   : {theme or "-"}

QUESTION
{'='*65}
{question}

RÉPONSE
{'='*65}
{reponse}
"""
    chemin.write_text(contenu, encoding="utf-8")
    print(f"\n  Sauvegardé : {chemin.relative_to(_racine)}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Démo RAG — Explicateur de cours")
    parser.add_argument("--question", "-q", help="Pose ta propre question")
    parser.add_argument("--exemples", "-e", action="store_true",
                        help="Afficher la liste des questions exemples")
    parser.add_argument("--id", type=int, help="Lancer seulement l'exemple N (1-5)")
    parser.add_argument("--save", "-s", action="store_true",
                        help="Sauvegarder la question et la réponse dans data/qa/")
    args = parser.parse_args()

    if args.exemples:
        print("\nQuestions exemples disponibles :\n")
        for ex in EXEMPLES:
            print(f"  [{ex['id']}] {ex['theme']}")
            print(f"      {ex['question']}\n")
        print("Lancer un exemple : python src/demo_rag.py --id 2")
        return

    idx = charger_index()

    if args.question:
        reponse = repondre(args.question, idx)
        if args.save:
            sauvegarder(args.question, reponse)
    elif args.id:
        ex = next((e for e in EXEMPLES if e["id"] == args.id), None)
        if not ex:
            sys.exit(f"Exemple {args.id} introuvable (1-{len(EXEMPLES)})")
        print(f"\n── Thème : {ex['theme']}")
        reponse = repondre(ex["question"], idx)
        if args.save:
            sauvegarder(ex["question"], reponse, theme=ex["theme"])
    else:
        # Lancer tous les exemples
        print(f"\n{'#'*65}")
        print("  DÉMO RAG — {len(EXEMPLES)} questions d'étudiants")
        print(f"{'#'*65}")
        for ex in EXEMPLES:
            print(f"\n── Thème : {ex['theme']}")
            repondre(ex["question"], idx)
            input("\n  [Entrée pour la question suivante...]")


if __name__ == "__main__":
    main()
