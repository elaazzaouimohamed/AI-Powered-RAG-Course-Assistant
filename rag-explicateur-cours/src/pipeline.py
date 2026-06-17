"""
Pipeline complet : PDF → JSON structuré → Chunks → ChromaDB + BM25.

Usage :
    python src/pipeline.py data/pdfs/Statistique_cours.pdf
    python src/pipeline.py data/pdfs/Statistique_cours.pdf --json-seulement
    python src/pipeline.py --depuis-json data/pdfs/Statistique_cours.json

Étapes :
  1. Extraction PDF   (pdf_extractor.py)
  2. Structuration    (structuration_json.py) → {nom}.json dans data/pdfs/
  3. Chunking         (chunker.py)            → list[Chunk] contextuel
  4. Indexation       ChromaDB persistant     → data/chroma/
  5. Rapport          statistiques + test de recherche
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import collections
from pathlib import Path

# ── Résolution de la racine du projet ────────────────────────────────────────
# Le script peut être lancé depuis n'importe quel répertoire.
_ici = Path(__file__).resolve().parent          # src/
_racine = _ici.parent                           # rag-explicateur-cours/
sys.path.insert(0, str(_ici))                   # pour: from chunking.chunker import ...
sys.path.insert(0, str(_ici / "extraction"))    # pour: from structuration_json import ...

from chunking.chunker import construire_chunks, charger_et_chunker


# ---------------------------------------------------------------------------
# Étape 1+2 : PDF → JSON
# ---------------------------------------------------------------------------

def pdf_vers_json(chemin_pdf: Path, afficher_progression: bool = True) -> Path:
    """
    Extrait le PDF et le structure en JSON via l'API NVIDIA Kimi K2.6.
    Retourne le chemin du fichier JSON produit.
    """
    from extraction.pdf_extractor import extraire_pdf
    from extraction.structuration_json import structurer_pdf_en_json

    chemin_json = chemin_pdf.with_suffix(".json")
    pages = extraire_pdf(str(chemin_pdf), exclure_repetitions=True)
    print(f"  {len(pages)} pages extraites depuis {chemin_pdf.name}")

    dataset = structurer_pdf_en_json(
        pages,
        titre_pdf=chemin_pdf.stem,
        afficher_progression=afficher_progression,
    )
    chemin_json.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  JSON écrit : {chemin_json}")
    return chemin_json


# ---------------------------------------------------------------------------
# Étape 3+4 : Chunks → ChromaDB persistant
# ---------------------------------------------------------------------------

def indexer(chemin_json: Path, reinitialiser: bool = False) -> dict:
    """
    Charge le JSON, construit les chunks et les indexe dans ChromaDB (persistant)
    + BM25 (en mémoire).

    Retourne un dictionnaire avec les objets nécessaires à la recherche.
    """
    try:
        import chromadb
        from rank_bm25 import BM25Okapi
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        sys.exit(
            f"Dépendances manquantes : {exc}\n"
            "Lancez : pip install chromadb sentence-transformers rank-bm25"
        )

    dataset, chunks = charger_et_chunker(str(chemin_json))
    print(f"  {len(chunks)} chunks construits")

    textes    = [c.texte for c in chunks]
    metadatas = [c.as_dict() for c in chunks]
    ids       = [c.chunk_id for c in chunks]

    # Statistiques
    type_counts = collections.Counter(c.type_chunk for c in chunks)
    print("  Répartition des types :")
    for t, nb in type_counts.most_common():
        print(f"    {t:12s}: {nb}")

    # ChromaDB persistant
    chroma_dir = str(_racine / "data" / "chroma")
    client = chromadb.PersistentClient(path=chroma_dir)
    nom_collection = f"cours_{chemin_json.stem}"

    if reinitialiser:
        try:
            client.delete_collection(nom_collection)
            print(f"  Collection '{nom_collection}' réinitialisée")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=nom_collection,
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() > 0 and not reinitialiser:
        print(f"  Collection '{nom_collection}' déjà indexée ({collection.count()} chunks) — ignoré")
        print("  (utilisez --reinit pour forcer la réindexation)")
    else:
        modele_nom = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        print(f"  Chargement du modèle d'embedding : {modele_nom}")
        embed_model = SentenceTransformer(modele_nom)

        print(f"  Vectorisation de {len(textes)} chunks...")
        embeddings = embed_model.encode(
            textes,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
        ).tolist()

        # Ajout par lots pour éviter les limites de taille ChromaDB
        LOT = 500
        for debut in range(0, len(textes), LOT):
            collection.add(
                embeddings=embeddings[debut:debut + LOT],
                documents=textes[debut:debut + LOT],
                metadatas=metadatas[debut:debut + LOT],
                ids=ids[debut:debut + LOT],
            )
        print(f"  ChromaDB : {collection.count()} chunks indexés → {chroma_dir}")

    # BM25
    def tokenizer(texte: str) -> list[str]:
        if not texte:
            return []
        texte = texte.lower().replace("'", " ").replace("-", " ")
        texte = re.sub(r"[^\w\s]", " ", texte)
        return [w for w in texte.split() if len(w) > 1]

    corpus_tokenise = [tokenizer(t) for t in textes]
    bm25 = BM25Okapi(corpus_tokenise)
    print("  BM25 indexé")

    return {
        "dataset":    dataset,
        "chunks":     chunks,
        "textes":     textes,
        "ids":        ids,
        "collection": collection,
        "bm25":       bm25,
        "tokenizer":  tokenizer,
    }


# ---------------------------------------------------------------------------
# Étape 5 : Test de recherche rapide
# ---------------------------------------------------------------------------

def tester_recherche(index: dict, question: str = "Qu'est-ce que la variance ?") -> None:
    """Lance une recherche BM25 simple pour vérifier que l'index fonctionne."""
    from rank_bm25 import BM25Okapi
    bm25: BM25Okapi = index["bm25"]
    ids: list[str]  = index["ids"]
    tokens = index["tokenizer"](question)
    scores = bm25.get_scores(tokens)
    top3   = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
    print(f'\n  Test BM25 — question : "{question}"')
    for rang, idx in enumerate(top3, 1):
        chunk = index["chunks"][idx]
        print(f"    {rang}. [{chunk.type_chunk}] {chunk.concept} ({chunk.chapitre[:40]})")
        print(f"       {chunk.texte[:120]}...")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline PDF → JSON → Chunks → ChromaDB"
    )
    groupe = parser.add_mutually_exclusive_group(required=True)
    groupe.add_argument("pdf", nargs="?", help="Chemin vers le PDF à traiter")
    groupe.add_argument(
        "--depuis-json",
        metavar="JSON",
        help="Passer directement un JSON déjà structuré (ignore l'étape PDF→JSON)",
    )
    parser.add_argument(
        "--json-seulement",
        action="store_true",
        help="S'arrêter après la génération du JSON (ne pas indexer)",
    )
    parser.add_argument(
        "--reinit",
        action="store_true",
        help="Forcer la réindexation même si la collection ChromaDB existe déjà",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Pipeline RAG — explicateur de cours")
    print("=" * 60)

    # ── Étapes 1+2 : PDF → JSON ──────────────────────────────────────────────
    if args.depuis_json:
        chemin_json = Path(args.depuis_json)
        if not chemin_json.exists():
            sys.exit(f"Fichier JSON introuvable : {chemin_json}")
        print(f"\n[Étape 1/2] JSON fourni directement : {chemin_json}")
    else:
        chemin_pdf = Path(args.pdf)
        if not chemin_pdf.exists():
            sys.exit(f"Fichier PDF introuvable : {chemin_pdf}")
        print(f"\n[Étape 1/2] Extraction + structuration : {chemin_pdf.name}")
        chemin_json = pdf_vers_json(chemin_pdf)

    if args.json_seulement:
        print("\nTerminé (--json-seulement).")
        return

    # ── Étapes 3+4 : Chunks + indexation ─────────────────────────────────────
    print(f"\n[Étape 2/2] Chunking + indexation : {chemin_json.name}")
    index = indexer(chemin_json, reinitialiser=args.reinit)

    # ── Étape 5 : Test rapide ─────────────────────────────────────────────────
    tester_recherche(index)

    print("\n" + "=" * 60)
    print("Pipeline terminé avec succès.")
    print(f"  JSON        : {chemin_json}")
    print(f"  ChromaDB    : {_racine / 'data' / 'chroma'}")
    print(f"  Chunks      : {len(index['chunks'])}")
    print("=" * 60)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
