"""
Inspection de la base vectorielle ChromaDB.

Usage :
    python src/inspect_chroma.py                          # résumé général
    python src/inspect_chroma.py --type formule           # filtrer par type
    python src/inspect_chroma.py --recherche "variance"   # recherche sémantique
    python src/inspect_chroma.py --tout                   # afficher tous les chunks
"""

import sys
import argparse
from pathlib import Path
from collections import Counter

# ── Résolution des chemins ────────────────────────────────────────────────────
_racine = Path(__file__).resolve().parent.parent
_chroma_dir = str(_racine / "data" / "chroma")

import chromadb

# ---------------------------------------------------------------------------
# Connexion
# ---------------------------------------------------------------------------

def connecter(nom_collection: str | None = None) -> chromadb.Collection:
    client = chromadb.PersistentClient(path=_chroma_dir)
    collections = client.list_collections()

    if not collections:
        sys.exit(f"Aucune collection dans {_chroma_dir}\nLancez d'abord : python src/pipeline.py ...")

    if nom_collection:
        return client.get_collection(nom_collection)

    if len(collections) == 1:
        col = client.get_collection(collections[0].name)
        print(f"Collection : {col.name}\n")
        return col

    print("Collections disponibles :")
    for i, c in enumerate(collections):
        print(f"  [{i}] {c.name}")
    choix = int(input("Choisir (numéro) : "))
    return client.get_collection(collections[choix].name)


# ---------------------------------------------------------------------------
# Affichage d'un chunk
# ---------------------------------------------------------------------------

def afficher_chunk(doc: str, meta: dict, index: int) -> None:
    print(f"\n{'─'*60}")
    print(f"  #{index:03d}  [{meta.get('type_chunk','?')}]  {meta.get('concept','?')}")
    print(f"  Chapitre : {meta.get('chapitre','?')}")
    print(f"  Source   : {meta.get('source','?')}")
    print(f"  Texte    : {doc[:300]}{'...' if len(doc) > 300 else ''}")


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------

def cmd_resume(col: chromadb.Collection) -> None:
    """Affiche le résumé général de la collection."""
    total = col.count()
    print(f"Total chunks : {total}")

    all_meta = col.get(include=["metadatas"])["metadatas"]

    types = Counter(m.get("type_chunk", "?") for m in all_meta)
    print("\nRépartition par type :")
    for t, n in types.most_common():
        barre = "█" * n
        print(f"  {t:12s}: {n:3d}  {barre}")

    chapitres = Counter(m.get("chapitre", "?") for m in all_meta)
    print("\nRépartition par chapitre :")
    for c, n in chapitres.most_common():
        print(f"  {n:3d}  {c[:65]}")

    concepts = Counter(m.get("concept", "?") for m in all_meta)
    print(f"\nNombre de concepts distincts : {len(concepts)}")

    print("\n5 premiers chunks :")
    res = col.get(limit=5, include=["documents", "metadatas"])
    for i, (doc, meta) in enumerate(zip(res["documents"], res["metadatas"])):
        afficher_chunk(doc, meta, i + 1)


def cmd_filtrer(col: chromadb.Collection, type_chunk: str) -> None:
    """Affiche tous les chunks d'un type donné (formule, exemple, exercice…)."""
    types_valides = ["definition", "formule", "exemple", "exercice",
                     "preuve", "remarque", "note"]
    if type_chunk not in types_valides:
        print(f"Type inconnu. Types disponibles : {', '.join(types_valides)}")
        return

    res = col.get(
        where={"type_chunk": type_chunk},
        include=["documents", "metadatas"],
    )
    nb = len(res["documents"])
    print(f"{nb} chunk(s) de type '{type_chunk}' :")
    for i, (doc, meta) in enumerate(zip(res["documents"], res["metadatas"])):
        afficher_chunk(doc, meta, i + 1)


def cmd_recherche(col: chromadb.Collection, query: str, top_k: int = 5) -> None:
    """Recherche sémantique dans la collection."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        sys.exit("sentence-transformers non installé : pip install sentence-transformers")

    modele_nom = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    print(f"Chargement du modèle d'embedding...")
    model = SentenceTransformer(modele_nom)

    vec = model.encode(query, normalize_embeddings=True).tolist()
    res = col.query(
        query_embeddings=[vec],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nTop {top_k} résultats pour : \"{query}\"")
    for i, (doc, meta, dist) in enumerate(zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    )):
        score = 1 - dist  # cosine distance → similarité
        print(f"\n{'─'*60}")
        print(f"  #{i+1}  Score : {score:.3f}  [{meta.get('type_chunk','?')}]  {meta.get('concept','?')}")
        print(f"  Chapitre : {meta.get('chapitre','?')}")
        print(f"  Texte    : {doc[:300]}{'...' if len(doc) > 300 else ''}")


def cmd_tout(col: chromadb.Collection) -> None:
    """Affiche tous les chunks de la collection."""
    res = col.get(include=["documents", "metadatas"])
    print(f"{len(res['documents'])} chunks au total :")
    for i, (doc, meta) in enumerate(zip(res["documents"], res["metadatas"])):
        afficher_chunk(doc, meta, i + 1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Inspection de ChromaDB")
    parser.add_argument("--collection", help="Nom de la collection (auto-détecté si absent)")
    parser.add_argument("--type", dest="type_chunk", help="Filtrer par type de chunk")
    parser.add_argument("--recherche", metavar="QUERY", help="Recherche sémantique")
    parser.add_argument("--tout", action="store_true", help="Afficher tous les chunks")
    args = parser.parse_args()

    col = connecter(args.collection)

    if args.type_chunk:
        cmd_filtrer(col, args.type_chunk)
    elif args.recherche:
        cmd_recherche(col, args.recherche)
    elif args.tout:
        cmd_tout(col)
    else:
        cmd_resume(col)


if __name__ == "__main__":
    main()
