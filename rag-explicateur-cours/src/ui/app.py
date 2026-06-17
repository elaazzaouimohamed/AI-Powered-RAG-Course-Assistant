"""
Interface Streamlit — RAG Explicateur de Cours.

Lancée avec : streamlit run src/ui/app.py
"""

import re
import sys
import json
import collections
from pathlib import Path

import streamlit as st

# ── Résolution des chemins ────────────────────────────────────────────────────
_src    = Path(__file__).resolve().parent.parent   # src/
_racine = _src.parent                              # rag-explicateur-cours/
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from chunking.chunker import charger_et_chunker

# ── Constantes ────────────────────────────────────────────────────────────────
CHROMA_DIR      = str(_racine / "data" / "chroma")
DATA_DIR        = _racine / "data" / "pdfs"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
TOP_K           = 15
TOP_RERANKED    = 5
RRF_K           = 60

COULEURS_TYPE = {
    "definition": "#4A90D9",
    "formule":    "#E67E22",
    "exemple":    "#27AE60",
    "exercice":   "#8E44AD",
    "preuve":     "#C0392B",
    "remarque":   "#16A085",
    "note":       "#7F8C8D",
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG — Explicateur de cours",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# Initialisation (une seule fois par session)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def charger_index(json_path: str):
    """Charge ChromaDB + BM25 depuis le JSON structuré (mis en cache)."""
    import chromadb
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer

    dataset, chunks = charger_et_chunker(json_path)
    textes = [c.texte for c in chunks]
    ids    = [c.chunk_id for c in chunks]

    # ChromaDB
    client     = chromadb.PersistentClient(path=CHROMA_DIR)
    nom_col    = f"cours_{Path(json_path).stem}"
    collection = client.get_collection(nom_col)

    # BM25
    def tokenizer(t: str) -> list:
        t = t.lower().replace("'", " ").replace("-", " ")
        return [w for w in re.sub(r"[^\w\s]", " ", t).split() if len(w) > 1]

    corpus_tok = [tokenizer(t) for t in textes]
    bm25       = BM25Okapi(corpus_tok)

    # Embedding model
    embed_model = SentenceTransformer(EMBEDDING_MODEL)

    return {
        "dataset":    dataset,
        "chunks":     chunks,
        "textes":     textes,
        "ids":        ids,
        "collection": collection,
        "bm25":       bm25,
        "tokenizer":  tokenizer,
        "embed":      embed_model,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Recherche hybride RRF
# ─────────────────────────────────────────────────────────────────────────────

INTENTIONS = {
    "formule":    ["formule", "equation", "calcul", "calculer", "expression"],
    "exemple":    ["exemple", "application", "illustrer", "concret"],
    "exercice":   ["exercice", "td", "probleme", "resoudre", "solution"],
    "preuve":     ["demonstration", "preuve", "demontrer", "justifier"],
    "definition": ["definition", "definir", "qu est ce que", "signifie", "expliquer"],
}


def detecter_intention(query: str) -> str | None:
    q = query.lower()
    scores = {i: sum(1 for kw in mots if kw in q) for i, mots in INTENTIONS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def recherche_hybride(query: str, idx: dict, top_k: int = TOP_K, filtre_type: str | None = None):
    rrf = collections.defaultdict(float)
    q_vec = idx["embed"].encode(query, normalize_embeddings=True).tolist()
    intention = detecter_intention(query)

    # A. Vectoriel général
    res = idx["collection"].query(query_embeddings=[q_vec], n_results=top_k,
                                   include=["distances"])
    for rang, cid in enumerate(res["ids"][0]):
        rrf[cid] += 1.0 / (RRF_K + rang + 1)

    # B. Vectoriel filtré (intention ou filtre manuel)
    filtre = filtre_type or intention
    if filtre and filtre != "tous":
        try:
            res_f = idx["collection"].query(
                query_embeddings=[q_vec], n_results=top_k,
                where={"type_chunk": filtre}, include=["distances"]
            )
            for rang, cid in enumerate(res_f["ids"][0]):
                rrf[cid] += 2.0 / (RRF_K + rang + 1)
        except Exception:
            pass

    # C. BM25
    tokens = idx["tokenizer"](query)
    scores_bm25 = idx["bm25"].get_scores(tokens)
    top_bm25 = sorted(range(len(scores_bm25)), key=lambda i: scores_bm25[i], reverse=True)[:top_k]
    for rang, i in enumerate(top_bm25):
        rrf[idx["ids"][i]] += 1.0 / (RRF_K + rang + 1)

    candidats = sorted(rrf, key=lambda x: rrf[x], reverse=True)[:top_k]
    return candidats, intention, rrf


def recuperer_details(cids: list, idx: dict, rrf_scores: dict) -> list[dict]:
    if not cids:
        return []
    res = idx["collection"].get(ids=cids, include=["documents", "metadatas"])
    details = []
    map_doc  = {cid: doc  for cid, doc  in zip(res["ids"], res["documents"])}
    map_meta = {cid: meta for cid, meta in zip(res["ids"], res["metadatas"])}
    for cid in cids:
        if cid in map_doc:
            details.append({
                "id":      cid,
                "texte":   map_doc[cid],
                "meta":    map_meta[cid],
                "score":   rrf_scores.get(cid, 0.0),
            })
    return details


# ─────────────────────────────────────────────────────────────────────────────
# Composants UI
# ─────────────────────────────────────────────────────────────────────────────

def badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:10px;font-size:12px;font-weight:600">{label}</span>'
    )


def afficher_chunk(chunk: dict, rang: int) -> None:
    meta   = chunk["meta"]
    texte  = chunk["texte"]
    type_c = meta.get("type_chunk", "?")
    color  = COULEURS_TYPE.get(type_c, "#888")

    with st.container():
        col1, col2 = st.columns([8, 1])
        with col1:
            st.markdown(
                f"**#{rang}** &nbsp;"
                + badge(type_c, color)
                + f"&nbsp;&nbsp; **{meta.get('concept','?')}**",
                unsafe_allow_html=True,
            )
            st.caption(f"📂 {meta.get('chapitre','?')}")
        with col2:
            score_pct = min(chunk["score"] * 600, 100)
            st.metric("Score", f"{score_pct:.0f}%")

        # Texte du chunk (sans le préfixe contextuel)
        texte_affiche = re.sub(r"^\[Chapitre:.*?\]\s*\[\w+\]\s*", "", texte)
        st.info(texte_affiche[:400] + ("…" if len(texte_affiche) > 400 else ""))

        with st.expander("Voir le contexte complet (parent)"):
            parent = meta.get("parent_content", "")
            st.text(parent)

        st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

def sidebar(idx: dict | None) -> tuple[str | None, int, str]:
    with st.sidebar:
        st.title("⚙️ Paramètres")

        # Sélection du fichier JSON
        jsons = sorted(DATA_DIR.glob("*.json"))
        noms  = [j.name for j in jsons]
        if not noms:
            st.error("Aucun JSON trouvé dans data/pdfs/")
            return None, TOP_K, "tous"

        choix = st.selectbox("📄 Cours", noms, index=0)
        json_path = str(DATA_DIR / choix)

        st.divider()

        # Filtre par type
        types = ["tous", "definition", "formule", "exemple", "exercice", "preuve", "remarque", "note"]
        filtre = st.selectbox("🔍 Filtrer par type", types)

        # Nombre de résultats
        top_k = st.slider("Nombre de résultats", 1, 20, TOP_RERANKED)

        st.divider()

        # Infos sur le cours chargé
        if idx:
            ds = idx["dataset"]
            st.markdown(f"**{ds.get('titre_annale','?')}**")
            meta = ds.get("metadata", {})
            if meta.get("domaine"):
                st.caption(f"Domaine : {meta['domaine']}")
            if meta.get("niveau"):
                st.caption(f"Niveau : {meta['niveau']}")
            st.caption(f"Chunks indexés : {len(idx['chunks'])}")
            parties = ds.get("parties", [])
            with st.expander(f"{len(parties)} chapitre(s)"):
                for p in parties:
                    nb = len(p.get("concepts", []))
                    st.write(f"• {p.get('titre','?')} ({nb} concepts)")

    return json_path, top_k, filtre


# ─────────────────────────────────────────────────────────────────────────────
# Page principale
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # En-tête
    st.markdown(
        "<h1 style='text-align:center'>📚 RAG — Explicateur de cours</h1>"
        "<p style='text-align:center;color:grey'>Recherche hybride · Contextual Retrieval · BM25 + Embeddings + RRF</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Sidebar (sans index encore)
    json_path, top_k, filtre = sidebar(None)
    if json_path is None:
        st.stop()

    # Chargement de l'index
    with st.spinner("Chargement de l'index…"):
        try:
            idx = charger_index(json_path)
        except Exception as e:
            st.error(
                f"Collection ChromaDB introuvable pour ce fichier.\n\n"
                f"Lancez d'abord :\n```\npython src/pipeline.py --depuis-json {json_path}\n```\n\n"
                f"Détail : {e}"
            )
            st.stop()

    # Mettre à jour la sidebar avec les infos du cours chargé
    sidebar(idx)

    # Zone de recherche
    col_input, col_btn = st.columns([6, 1])
    with col_input:
        query = st.text_input(
            "Posez votre question sur le cours :",
            placeholder="Ex: Qu'est-ce que la variance ? Comment calculer un intervalle de confiance ?",
            label_visibility="collapsed",
        )
    with col_btn:
        lancer = st.button("🔍 Rechercher", use_container_width=True)

    # Exemples de questions rapides
    st.markdown("**Questions rapides :**")
    cols = st.columns(4)
    exemples = [
        "Qu'est-ce que la variance ?",
        "Formule de la médiane",
        "Intervalle de confiance",
        "Maximum de vraisemblance",
    ]
    for col, ex in zip(cols, exemples):
        if col.button(ex, use_container_width=True):
            query = ex
            lancer = True

    # Résultats
    if lancer and query.strip():
        st.divider()

        with st.spinner("Recherche en cours…"):
            candidats, intention, rrf_scores = recherche_hybride(
                query, idx, top_k=TOP_K,
                filtre_type=filtre if filtre != "tous" else None
            )
            resultats = recuperer_details(candidats[:top_k], idx, rrf_scores)

        # En-tête des résultats
        col_titre, col_intention = st.columns([3, 1])
        with col_titre:
            st.markdown(f"### {len(resultats)} résultats pour *\"{query}\"*")
        with col_intention:
            if intention:
                st.markdown(
                    badge(f"Intention : {intention}", COULEURS_TYPE.get(intention, "#888")),
                    unsafe_allow_html=True,
                )

        # Répartition par type dans les résultats
        types_resultats = collections.Counter(r["meta"].get("type_chunk") for r in resultats)
        legende = " &nbsp;".join(
            badge(f"{t} ({n})", COULEURS_TYPE.get(t, "#888"))
            for t, n in types_resultats.most_common()
        )
        st.markdown(legende, unsafe_allow_html=True)
        st.markdown("")

        # Affichage des chunks
        for i, chunk in enumerate(resultats, 1):
            afficher_chunk(chunk, i)

    elif not query and lancer:
        st.warning("Entrez une question pour lancer la recherche.")


if __name__ == "__main__":
    main()
