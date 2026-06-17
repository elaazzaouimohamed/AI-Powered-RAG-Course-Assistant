# RAG Explicateur de Cours

Système RAG (Retrieval-Augmented Generation) pour l'explication de cours
universitaires, fonctionnant **100 % en local** via [Ollama](https://ollama.com/).
Présenté à la Journée de l'Intelligence Artificielle — FSBM.

## Architecture du pipeline

```
PDFs ──► Extraction ──► Chunking ──► Embeddings ──► Index vectoriel
                                                          │
Question ──────────────────────────────────► Retrieval ──┘
                                                │
                                         Génération LLM (Ollama)
                                                │
                                          Réponse + Quiz
```

| Étape | Module | État |
|---|---|---|
| 1. Extraction PDF | `src/extraction/pdf_extractor.py` | ✅ Implémenté |
| 2. Chunking | `src/chunking/chunker.py` | 🔲 Squelette |
| 3. Embeddings | `src/embeddings/embedder.py` | 🔲 Squelette |
| 4. Retrieval | `src/retrieval/` | 🔲 Squelette |
| 5. Génération | `src/generation/` | 🔲 Squelette |
| 6. Quiz | `src/quiz/quiz_generator.py` | 🔲 Squelette |
| 7. Interface | `src/ui/app.py` | 🔲 Squelette |

## Prérequis

### Tesseract OCR (pour les PDFs image-only)

```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr tesseract-ocr-fra

# macOS
brew install tesseract tesseract-lang

# Windows — télécharger l'installeur :
# https://github.com/UB-Mannheim/tesseract/wiki
```

### Python

```bash
pip install -r requirements.txt
```

## Utilisation rapide — module d'extraction

```bash
python src/extraction/pdf_extractor.py data/pdfs/mon_cours.pdf
```

Sortie page par page dans la console, PNG des pages avec images dans `data/images/`.

Pour exclure les en-têtes/pieds de page répétés, utiliser le paramètre dans le code :

```python
from src.extraction.pdf_extractor import extraire_pdf

pages = extraire_pdf("data/pdfs/cours.pdf", exclure_repetitions=True)
for p in pages:
    print(p["text"])
```

## Format de sortie de l'extraction

Chaque page est un dictionnaire :

```python
{
    "source": "cours_clustering.pdf",
    "page": 3,
    "text": "...",
    "methode_extraction": "natif",   # ou "ocr" ou "erreur"
    "contient_image": True,
    "image_path": "data/images/cours_clustering_page_3.png",
    "alerte_formule_complexe": False,
    "est_entete_pied_page_repete": ["Cours de Clustering | Module 2"],
}
```

## Configuration

Toutes les valeurs sont dans `config.yaml`.
