"""
Service FastAPI léger — expose la recherche RAG (ChromaDB + BM25)
utilisée par le backend Spring Boot.

Démarrage : uvicorn main:app --host 0.0.0.0 --port 8001
"""

import os
import re
import sys
import shutil
import threading
import traceback
import uuid
import collections
from pathlib import Path
from typing import List

# pipeline.py (et les modules qu'il appelle) impriment des caractères Unicode (ex. "→").
# Sur Windows, le codepage par défaut de la console (cp1252) ne les supporte pas et lève
# une UnicodeEncodeError dès qu'on importe/exécute ce code en dehors d'un terminal UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Réutilise le code existant du projet Python.
# Par défaut : rag-web-app et rag-explicateur-cours sont deux dossiers frères sous Project_ML
# (dev local). Surchargeable via RAG_PROJECT_ROOT pour les déploiements où cette disposition
# en dossiers frères n'est pas reproduite (ex: VM avec tout sous /opt/).
_service_dir = Path(__file__).resolve().parent
_project_root = (Path(os.environ["RAG_PROJECT_ROOT"]) if os.environ.get("RAG_PROJECT_ROOT")
                 else _service_dir.parent.parent / "rag-explicateur-cours")
_src = _project_root / "src"
_pdfs = _project_root / "data" / "pdfs"
_chroma_dir = str(_project_root / "data" / "chroma")

if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

try:
    from dotenv import load_dotenv
    load_dotenv(_project_root / ".env")
except ImportError:
    pass

app = FastAPI(title="RAG Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
RRF_K  = 60
TOP_K  = 12
TOP_PARENTS = 3

# Détection d'intention : booste la recherche vectorielle vers les chunks dont
# le type_chunk correspond au type de question posée (formule, exemple, exercice,
# preuve, definition). Méthode reprise de rag-explicateur-cours/src/demo_rag.py.
INTENTIONS = {
    "formule":    ["formule", "equation", "calculer", "calcul", "expression"],
    "exemple":    ["exemple", "illustrer", "concret", "application"],
    "exercice":   ["exercice", "td", "resoudre", "probleme", "solution"],
    "preuve":     ["demonstration", "preuve", "demontrer", "justifier"],
    "definition": ["definition", "qu est ce que", "signifie", "expliquer"],
}


def _detecter_intention(question: str) -> str | None:
    q = question.lower()
    scores = {i: sum(1 for kw in mots if kw in q) for i, mots in INTENTIONS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None

_index_cache: dict = {}


def _load_index(course: str) -> dict:
    if course in _index_cache:
        return _index_cache[course]

    json_path = _pdfs / f"{course}.json"
    if not json_path.exists():
        raise HTTPException(404, f"Course '{course}' not found. Run pipeline.py first.")

    import chromadb
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer
    from chunking.chunker import charger_et_chunker

    dataset, chunks = charger_et_chunker(str(json_path))
    client = chromadb.PersistentClient(path=_chroma_dir)
    collection = client.get_collection(f"cours_{course}")

    def tokenizer(t: str) -> list:
        t = t.lower().replace("'", " ").replace("-", " ")
        return [w for w in re.sub(r"[^\w\s]", " ", t).split() if len(w) > 1]

    textes = [c.texte for c in chunks]
    ids    = [c.chunk_id for c in chunks]
    bm25   = BM25Okapi([tokenizer(t) for t in textes])
    embed  = SentenceTransformer(EMBEDDING_MODEL)

    idx = {"collection": collection, "bm25": bm25, "tokenizer": tokenizer,
           "textes": textes, "ids": ids, "embed": embed, "dataset": dataset}
    _index_cache[course] = idx
    return idx


def _retrieve(question: str, idx: dict) -> List[dict]:
    rrf   = collections.defaultdict(float)
    q_vec = idx["embed"].encode(question, normalize_embeddings=True).tolist()

    # Pas de seuil de similarité ici : comme dans demo_rag.py, on renvoie toujours
    # les meilleurs candidats au LLM, même pour une salutation ou une question hors
    # cours — c'est le prompt (côté Spring Boot) qui guide le LLM pour répondre
    # normalement ou signaler que l'info n'est pas dans le cours.
    res = idx["collection"].query(query_embeddings=[q_vec], n_results=TOP_K,
                                   include=["distances"])
    for rank, cid in enumerate(res["ids"][0]):
        rrf[cid] += 1.0 / (RRF_K + rank + 1)

    # Boost par intention : si la question correspond à un type de contenu identifiable
    # (formule, exemple, exercice, preuve, definition), une 2e recherche vectorielle
    # filtrée sur ce type_chunk renforce (poids ×2) les chunks de ce type dans le score RRF.
    intention = _detecter_intention(question)
    if intention:
        try:
            res_filtre = idx["collection"].query(
                query_embeddings=[q_vec], n_results=TOP_K,
                where={"type_chunk": intention}, include=["distances"])
            for rank, cid in enumerate(res_filtre["ids"][0]):
                rrf[cid] += 2.0 / (RRF_K + rank + 1)
        except Exception:
            pass

    tokens     = idx["tokenizer"](question)
    bm25_scores = idx["bm25"].get_scores(tokens)
    top_bm25   = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:TOP_K]
    for rank, i in enumerate(top_bm25):
        rrf[idx["ids"][i]] += 1.0 / (RRF_K + rank + 1)

    candidats = sorted(rrf, key=lambda x: rrf[x], reverse=True)[:TOP_K]

    res2 = idx["collection"].get(ids=candidats, include=["metadatas"])
    map_meta = {cid: m for cid, m in zip(res2["ids"], res2["metadatas"])}

    vus, contextes = set(), []
    for cid in candidats:
        meta = map_meta.get(cid)
        if not meta:
            continue
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


class RetrieveRequest(BaseModel):
    question: str
    course: str


@app.post("/retrieve")
def retrieve(req: RetrieveRequest):
    idx = _load_index(req.course)
    contexts = _retrieve(req.question, idx)
    return {"contexts": contexts}


@app.get("/courses")
def list_courses():
    courses = [p.stem for p in sorted(_pdfs.glob("*.json"))]
    return {"courses": courses}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Ingestion d'un nouveau cours (upload PDF → JSON → ChromaDB), en tâche de fond
# ---------------------------------------------------------------------------

_COURSE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

# État des jobs en mémoire : {job_id: {status, step, error}}
# Suffisant pour ce projet (process unique, pas de scaling horizontal).
_jobs: dict = {}
_jobs_lock = threading.Lock()


def _set_job(job_id: str, **fields) -> None:
    with _jobs_lock:
        _jobs[job_id].update(fields)


def _run_ingestion(job_id: str, course_name: str, chemin_pdf: Path) -> None:
    try:
        import pipeline

        _set_job(job_id, status="running", step="extraction")
        chemin_json = pipeline.pdf_vers_json(chemin_pdf, afficher_progression=False)

        _set_job(job_id, step="indexation")
        pipeline.indexer(chemin_json, reinitialiser=True)

        _index_cache.pop(course_name, None)
        _set_job(job_id, status="done", step="terminé")
    except Exception as exc:
        traceback.print_exc()
        _set_job(job_id, status="error", error=str(exc))


@app.post("/ingest")
def ingest(course_name: str = Form(...), file: UploadFile = File(...)):
    course_name = course_name.strip()
    if not _COURSE_NAME_RE.match(course_name):
        raise HTTPException(400, "Nom de cours invalide (lettres, chiffres, '_' et '-' uniquement).")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Seuls les fichiers PDF sont acceptés.")

    chemin_pdf = _pdfs / f"{course_name}.pdf"
    _pdfs.mkdir(parents=True, exist_ok=True)
    with chemin_pdf.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {"status": "pending", "step": "en attente", "error": None, "course": course_name}

    thread = threading.Thread(target=_run_ingestion, args=(job_id, course_name, chemin_pdf), daemon=True)
    thread.start()

    return {"job_id": job_id}


@app.get("/ingest/{job_id}")
def ingest_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job introuvable.")
    return job


def _assert_safe_course_name(course_name: str) -> None:
    """Empêche toute tentative de traversée de chemin (../, /, \\) sans imposer
    la convention de nommage stricte de l'upload — la suppression doit pouvoir
    cibler des cours existants nommés avant l'introduction de cette règle."""
    if not course_name or course_name in (".", "..") or "/" in course_name or "\\" in course_name:
        raise HTTPException(400, "Nom de cours invalide.")
    resolu = (_pdfs / f"{course_name}.json").resolve()
    if _pdfs.resolve() not in resolu.parents:
        raise HTTPException(400, "Nom de cours invalide.")


@app.delete("/courses/{course_name}")
def delete_course(course_name: str):
    _assert_safe_course_name(course_name)

    import chromadb
    client = chromadb.PersistentClient(path=_chroma_dir)
    try:
        client.delete_collection(f"cours_{course_name}")
    except Exception:
        pass

    for suffix in (".json", ".pdf"):
        chemin = _pdfs / f"{course_name}{suffix}"
        if chemin.exists():
            chemin.unlink()

    _index_cache.pop(course_name, None)
    return {"deleted": course_name}
