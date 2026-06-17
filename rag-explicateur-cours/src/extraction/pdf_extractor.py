"""
Extraction hybride de texte depuis des PDFs de cours universitaires.

Stratégie de routage (priorité décroissante pour chaque page) :
  1. Texte natif + tri spatial                  → local
  2. Aucun texte natif → OCR Tesseract          → local
     OCR de mauvaise qualité                    → Claude
  3. Formule mathématique en image détectée     → Claude
  4. Mise en page trop fragmentée               → Claude
  5. Page avec graphique/schéma                 → extraction des images embarquées (indépendant du routage texte)
  6. En-têtes / pieds de page répétés           → détection et exclusion locale

Intégration Claude (API Anthropic) :
  - Clé API lue UNIQUEMENT depuis la variable d'environnement ANTHROPIC_API_KEY.
  - Si la variable est absente, ou si le package anthropic n'est pas installé,
    le module fonctionne en mode 100 % local sans lever d'exception.
    Les pages qui auraient nécessité Claude sont marquées avec
    claude_necessaire_mais_indisponible = True.
  - La clé API n'est jamais affichée dans les logs ni dans les messages d'erreur.

Sécurité :
  Placer ANTHROPIC_API_KEY dans un fichier .env local (jamais commité dans Git).
  Ajouter .env au .gitignore du projet.
  Exemple de fichier .env :
      ANTHROPIC_API_KEY=sk-ant-...
"""

import base64
import io
import os
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Chargement automatique du fichier .env situé à la racine du projet
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # sans python-dotenv, définir ANTHROPIC_API_KEY manuellement dans le shell

try:
    import anthropic
    _ANTHROPIC_DISPONIBLE = True
except ImportError:
    _ANTHROPIC_DISPONIBLE = False

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

# Modèle Claude (surchargeable via variable d'environnement)
# claude-haiku-4-5-20251001 = rapide et économique pour l'extraction de texte
CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

# OCR : qualité minimale acceptable
OCR_MIN_CHARS = 20           # longueur minimale du texte extrait
OCR_SEUIL_NORMALITE = 0.40   # ratio min de caractères "normaux" (lettres, chiffres, ponctuation courante)

# Rendu PNG pour Claude et pour l'export page entière
RENDER_SCALE = 2.0            # ×2 résolution native ≈ 144 DPI

# Tri spatial des blocs de texte
LINE_TOLERANCE = 10           # tolérance verticale (pts PDF) pour regrouper une même ligne logique

# Détection des répétitions (en-têtes / pieds de page)
SEUIL_REPETITION = 0.5        # fraction de pages au-delà de laquelle une ligne est considérée répétée

# Heuristique formule mathématique en image
SEUIL_RATIO_IMAGE = 0.15      # ratio surface_images / surface_page
SEUIL_TEXTE_SPARSE = 100      # en dessous : texte considéré "sparse"

# Heuristique mise en page complexe
MAX_BLOCS_COMPLEXE = 30       # au-delà de ce nombre de blocs : layout trop fragmenté

# Symboles Unicode mathématiques isolés qui signalent une formule partiellement rendue
SYMBOLES_MATH = frozenset(
    'χ∑∫√ΣΠΔαβγδεζηθλμνξπρστφψω'
    '≤≥≠≈∞∂∇∈∉∩∪⊂⊃∝∀∃'
    '²³₀₁₂₃₄₅₆₇₈₉'
)

# Prompts Claude
_PROMPT_FORMULE = (
    "Extrait le texte complet de cette page de cours universitaire en français. "
    "Pour toute formule mathématique visible, transcris-la en LaTeX entre "
    "balises $$...$$ (formule en display) ou $...$ (formule en ligne). "
    "Respecte l'ordre de lecture naturel (haut → bas, gauche → droite). "
    "Retourne uniquement le texte et les formules, sans commentaire."
)
_PROMPT_TEXTE = (
    "Extrait le texte complet de cette page de cours universitaire en respectant "
    "l'ordre de lecture naturel (haut → bas, gauche → droite). "
    "Retourne uniquement le texte extrait, sans commentaire."
)

# ── Client Claude (initialisation paresseuse) ─────────────────────────────────

_claude_client: Optional[object] = None
_claude_init_tentee: bool = False


def _obtenir_client_claude() -> Optional[object]:
    """
    Retourne le client Anthropic prêt à l'emploi, ou None si indisponible.

    L'initialisation n'est tentée qu'une seule fois. La clé API n'est
    jamais transmise aux logs, même en cas d'erreur.
    """
    global _claude_client, _claude_init_tentee

    if _claude_init_tentee:
        return _claude_client

    _claude_init_tentee = True
    cle = os.environ.get("ANTHROPIC_API_KEY")

    if not cle:
        logger.info("ANTHROPIC_API_KEY absente — mode 100%s local activé", "%")
        return None

    if not _ANTHROPIC_DISPONIBLE:
        logger.warning(
            "Package anthropic non installé. "
            "Installer avec : pip install anthropic"
        )
        return None

    try:
        _claude_client = anthropic.Anthropic(api_key=cle)
        logger.info("Client Claude initialisé (modèle : %s)", CLAUDE_MODEL)
    except Exception as exc:
        logger.error("Échec d'initialisation du client Claude : %s", exc)

    return _claude_client


# ── Appel à l'API Claude vision ───────────────────────────────────────────────

def _appeler_claude(client: object, prompt: str, img: Image.Image) -> str:
    """
    Envoie une image PIL + prompt à l'API Claude vision et retourne le texte.

    Convertit l'image en base64 PNG avant l'envoi.
    """
    tampon = io.BytesIO()
    img.save(tampon, format="PNG")
    img_b64 = base64.standard_b64encode(tampon.getvalue()).decode("utf-8")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )
    return message.content[0].text


# ── Fonction publique principale ──────────────────────────────────────────────

def extraire_pdf(
    chemin_pdf: str,
    dossier_images: str = "data/images",
    exclure_repetitions: bool = False,
) -> list[dict]:
    """
    Extrait le texte et les métadonnées d'un PDF page par page.

    Args:
        chemin_pdf: Chemin vers le fichier PDF.
        dossier_images: Dossier de sortie pour les PNG des pages contenant des images.
        exclure_repetitions: Si True, retire les en-têtes/pieds répétés du champ text
            tout en les conservant dans est_entete_pied_page_repete.

    Returns:
        Liste de dicts (un par page) avec les champs :
            source, page, text, methode_extraction,
            contient_image, image_path,
            alerte_formule_complexe, formule_latex,
            claude_necessaire_mais_indisponible,
            est_entete_pied_page_repete.

    Raises:
        FileNotFoundError: Si chemin_pdf n'existe pas sur le disque.

    Notes:
        Un PDF corrompu ou une page illisible ne lève pas d'exception :
        l'erreur est loggée et le traitement continue sur les pages suivantes.
    """
    chemin = Path(chemin_pdf)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin_pdf}")

    Path(dossier_images).mkdir(parents=True, exist_ok=True)
    dossier_imgs = Path(dossier_images)
    resultats: list[dict] = []

    try:
        doc = fitz.open(str(chemin))
    except Exception as exc:
        logger.error("Impossible d'ouvrir %s : %s", chemin.name, exc)
        return []

    nb_pages = len(doc)
    with doc:
        for idx in range(nb_pages):
            print(f"  Extraction page {idx + 1}/{nb_pages}...", end="\r", flush=True)
            try:
                donnees = _traiter_page(doc[idx], chemin.name, idx + 1, dossier_imgs)
                resultats.append(donnees)
            except Exception as exc:
                logger.error("Erreur page %d de %s : %s", idx + 1, chemin.name, exc)
                resultats.append(_page_en_erreur(chemin.name, idx + 1))
    print(f"  Extraction terminée : {nb_pages}/{nb_pages} pages.")

    _marquer_repetitions(resultats, exclure=exclure_repetitions)
    return resultats


# ── Routage par page ──────────────────────────────────────────────────────────

def _traiter_page(
    page: fitz.Page,
    nom_source: str,
    num_page: int,
    dossier_imgs: Path,
) -> dict:
    """
    Analyse la page et applique la méthode d'extraction appropriée.

    L'export PNG (cas 5) est systématique dès qu'une image est détectée,
    indépendamment de la méthode utilisée pour le texte.
    """
    images = page.get_images(full=True)
    contient_image = len(images) > 0

    # get_text("blocks") → [(x0, y0, x1, y1, texte, bloc_no, type), ...]
    # type 0 = texte, type 1 = image
    blocs = page.get_text("blocks")
    blocs_texte = [b for b in blocs if b[6] == 0]

    # Cas 5 : extraction des images embarquées, indépendant du routage texte
    image_paths: list[str] = []
    if contient_image:
        image_paths = _sauvegarder_images_page(page, images, nom_source, num_page, dossier_imgs)

    base = _dict_base(nom_source, num_page, contient_image, image_paths)

    if not blocs_texte:
        # Cas 2 : aucun texte natif → OCR puis Claude si OCR insuffisant
        return _extraire_sans_texte_natif(page, base)

    if _detecter_formule_image(page, blocs_texte, images):
        # Cas 3 : formule mathématique rendue en image
        base["alerte_formule_complexe"] = True
        return _extraire_via_claude(page, blocs_texte, base, raison="formule")

    if _detecter_mise_en_page_complexe(blocs_texte):
        # Cas 4 : mise en page trop fragmentée pour le tri spatial seul
        return _extraire_via_claude(page, blocs_texte, base, raison="layout")

    # Cas 1 : extraction native avec tri spatial (majorité des pages)
    base["text"] = _nettoyer_texte(_extraire_texte_spatialise(blocs_texte))
    base["methode_extraction"] = "natif"
    return base


# ── Extraction texte natif avec tri spatial ───────────────────────────────────

def _extraire_texte_spatialise(blocs: list) -> str:
    """
    Reconstitue l'ordre de lecture naturel en triant les blocs par (y arrondi, x).

    Arrondir y0 à LINE_TOLERANCE points près regroupe les blocs qui partagent
    la même ligne logique malgré de légères différences d'alignement vertical,
    typiques des PDFs créés avec Word ou Canva.
    """
    tries = sorted(blocs, key=lambda b: (round(b[1] / LINE_TOLERANCE), b[0]))
    return "\n".join(b[4].strip() for b in tries if b[4].strip())


# ── Extraction sans texte natif (OCR → Claude) ───────────────────────────────

def _extraire_sans_texte_natif(page: fitz.Page, result: dict) -> dict:
    """
    Cas 2 : la page ne contient aucun texte natif (slides exportées en image, etc.).

    Séquence :
      1. OCR Tesseract.
      2. Si qualité OCR acceptable → retour OCR local.
      3. Sinon → Claude si disponible.
      4. Si Claude indisponible → conserver l'OCR dégradé (mieux que rien),
         marquer claude_necessaire_mais_indisponible.
    """
    texte_ocr = _ocr_page(page)

    if _ocr_qualite_acceptable(texte_ocr):
        result["text"] = _nettoyer_texte(texte_ocr)
        result["methode_extraction"] = "ocr_local"
        return result

    # OCR de mauvaise qualité → tenter Claude
    client = _obtenir_client_claude()

    if client is None:
        result["claude_necessaire_mais_indisponible"] = True
        if texte_ocr.strip():
            result["text"] = _nettoyer_texte(texte_ocr)
            result["methode_extraction"] = "ocr_local"
        return result

    try:
        img = _page_en_image_pil(page)
        texte = _appeler_claude(client, _PROMPT_TEXTE, img)
        result["text"] = _nettoyer_texte(texte)
        result["methode_extraction"] = "claude"
    except Exception as exc:
        logger.error(
            "Erreur Claude page %d (%s) : %s", result["page"], result["source"], exc
        )
        result["methode_extraction"] = "echec"
        if texte_ocr.strip():
            result["text"] = _nettoyer_texte(texte_ocr)

    return result


# ── Fallback Claude (cas 3 & 4) ───────────────────────────────────────────────

def _extraire_via_claude(
    page: fitz.Page,
    blocs_texte: list,
    result: dict,
    raison: str,
) -> dict:
    """
    Cas 3 (formule) et cas 4 (layout complexe) : extraction via Claude vision.

    Dégradation gracieuse :
      - Si Claude indisponible → tri spatial local, marquer la page.
      - Si l'appel API échoue → marquer "echec", conserver le texte local.
    """
    client = _obtenir_client_claude()

    if client is None:
        result["claude_necessaire_mais_indisponible"] = True
        if blocs_texte:
            result["text"] = _nettoyer_texte(_extraire_texte_spatialise(blocs_texte))
            result["methode_extraction"] = "natif"
        return result

    prompt = _PROMPT_FORMULE if raison == "formule" else _PROMPT_TEXTE

    try:
        img = _page_en_image_pil(page)
        texte = _appeler_claude(client, prompt, img)

        result["text"] = _nettoyer_texte(texte)
        result["methode_extraction"] = "claude"

        if raison == "formule":
            result["formule_latex"] = _extraire_latex(texte)

    except Exception as exc:
        logger.error(
            "Erreur Claude page %d (%s) : %s", result["page"], result["source"], exc
        )
        result["methode_extraction"] = "echec"
        if blocs_texte:
            result["text"] = _nettoyer_texte(_extraire_texte_spatialise(blocs_texte))

    return result


# ── OCR Tesseract ─────────────────────────────────────────────────────────────

def _ocr_page(page: fitz.Page) -> str:
    """OCR Tesseract, tentative 'fra' puis 'fra+eng' en fallback."""
    img = _page_en_image_pil(page)

    for lang in ("fra", "fra+eng"):
        try:
            texte = pytesseract.image_to_string(img, lang=lang)
            if lang != "fra":
                logger.warning("Tesseract 'fra' indisponible, utilisation de '%s'", lang)
            return texte
        except pytesseract.TesseractError:
            continue

    logger.warning("Langues Tesseract fr indisponibles, utilisation du modèle par défaut")
    return pytesseract.image_to_string(img)


def _ocr_qualite_acceptable(texte: str) -> bool:
    """
    Valide la qualité du résultat OCR selon deux critères combinés :
      - Longueur minimale (OCR_MIN_CHARS).
      - Ratio de caractères "normaux" >= OCR_SEUIL_NORMALITE.
        "Normal" = alphanumérique, espace, ponctuation courante (y compris accents).
    """
    texte_net = texte.strip()
    if len(texte_net) < OCR_MIN_CHARS:
        return False
    normaux = sum(
        1 for c in texte_net
        if c.isalnum() or c.isspace()
        or c in '.,;:!?()-\'"«»éèêëàâùûüîïôçÉÈÊÀÂÙÛÜÎÏÔÇœŒæÆ'
    )
    return normaux / len(texte_net) >= OCR_SEUIL_NORMALITE


# ── Détection des cas spéciaux ────────────────────────────────────────────────

def _detecter_formule_image(
    page: fitz.Page,
    blocs_texte: list,
    images: list,
) -> bool:
    """
    Heuristique : formule mathématique rendue en image (non récupérable nativement).

    Conditions simultanées requises :
      1. Au moins une image sur la page.
      2. Texte natif sparse (< SEUIL_TEXTE_SPARSE caractères).
      3. Au moins un symbole mathématique Unicode isolé dans le texte natif.
      4. Surface des images > SEUIL_RATIO_IMAGE de la surface totale de la page.
    """
    if not images:
        return False

    texte_total = " ".join(b[4] for b in blocs_texte).strip()

    if len(texte_total) >= SEUIL_TEXTE_SPARSE:
        return False

    if not any(c in SYMBOLES_MATH for c in texte_total):
        return False

    rect_page = page.rect
    surface_page = rect_page.width * rect_page.height
    if surface_page == 0:
        return False

    surface_images = 0.0
    for img_info in images:
        xref = img_info[0]
        if not xref:
            continue
        try:
            for rect_img in page.get_image_rects(xref):
                surface_images += rect_img.width * rect_img.height
        except Exception:
            pass

    return (surface_images / surface_page) > SEUIL_RATIO_IMAGE


def _detecter_mise_en_page_complexe(blocs: list) -> bool:
    """
    Heuristique : mise en page trop fragmentée pour que le tri spatial seul
    produise un texte cohérent.

    Trois indicateurs détectés :
      1. Nombre excessif de blocs (> MAX_BLOCS_COMPLEXE) → tableaux, formulaires.
      2. Majorité de blocs très courts (< 15 caractères) → labels de formulaire.
      3. Blocs dont les bounding boxes se chevauchent → colonnes ou superpositions.
    """
    if len(blocs) < 8:
        return False

    if len(blocs) > MAX_BLOCS_COMPLEXE:
        return True

    blocs_courts = sum(1 for b in blocs if len(b[4].strip()) < 15)
    if blocs_courts / len(blocs) > 0.70:
        return True

    return _compter_chevauchements(blocs[:25]) > 3


def _compter_chevauchements(blocs: list) -> int:
    """
    Compte les paires de blocs voisins dont les bounding boxes se chevauchent
    à la fois en x et en y.

    Limité aux 5 voisins suivants de chaque bloc pour rester O(n).
    """
    count = 0
    for i, b1 in enumerate(blocs):
        for b2 in blocs[i + 1 : min(i + 6, len(blocs))]:
            x_overlap = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
            y_overlap = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
            if x_overlap > 5 and y_overlap > 5:
                count += 1
    return count


# ── Extraction des images embarquées ─────────────────────────────────────────

def _sauvegarder_images_page(
    page: fitz.Page,
    images: list,
    nom_source: str,
    num_page: int,
    dossier_imgs: Path,
) -> list[str]:
    """
    Extrait chaque image embarquée dans la page et la sauvegarde sur disque.

    Utilise page.parent.extract_image(xref) pour récupérer les octets bruts
    de l'image (JPEG, PNG, etc.) tels qu'ils sont stockés dans le PDF,
    sans ré-encoder ni rendre toute la page.

    Les images de moins de 10×10 pixels sont ignorées (pixels de mise en page,
    séparateurs invisibles fréquents dans les PDFs générés par Word).

    Convention de nommage : {nom_pdf}_page_{N}_img_{I}.{ext}
    Retourne la liste des chemins sauvegardés (peut être vide si toutes
    les images étaient trop petites ou illisibles).
    """
    doc = page.parent
    chemins: list[str] = []

    for i, img_info in enumerate(images):
        xref = img_info[0]
        if not xref:
            continue
        try:
            img_data = doc.extract_image(xref)
            if not img_data:
                continue

            largeur = img_data.get("width", 0)
            hauteur = img_data.get("height", 0)
            if largeur < 10 or hauteur < 10:
                continue  # pixel de mise en page, on ignore

            ext = img_data.get("ext", "png")
            donnees: bytes = img_data["image"]

            nom_fichier = f"{Path(nom_source).stem}_page_{num_page}_img_{i + 1}.{ext}"
            chemin_sortie = dossier_imgs / nom_fichier
            chemin_sortie.write_bytes(donnees)
            chemins.append(str(chemin_sortie))

        except Exception as exc:
            logger.warning(
                "Impossible d'extraire l'image %d page %d (%s) : %s",
                i + 1, num_page, nom_source, exc,
            )

    return chemins


# ── Détection des en-têtes / pieds de page répétés ───────────────────────────

def _marquer_repetitions(pages: list[dict], exclure: bool) -> None:
    """
    Détecte les lignes présentes sur plus de SEUIL_REPETITION des pages
    et met à jour est_entete_pied_page_repete dans chaque dict.

    Si exclure=True, retire ces lignes du champ text tout en les conservant
    dans les métadonnées pour traçabilité.
    """
    if len(pages) < 2:
        return

    seuil = len(pages) * SEUIL_REPETITION
    compteur: Counter = Counter()

    for page_data in pages:
        lignes_uniques = {
            l.strip() for l in page_data["text"].splitlines() if l.strip()
        }
        for ligne in lignes_uniques:
            compteur[ligne] += 1

    repetitions = {
        l for l, count in compteur.items()
        if count >= seuil and len(l) < 200
    }

    for page_data in pages:
        lignes_repetes = [
            l.strip()
            for l in page_data["text"].splitlines()
            if l.strip() in repetitions
        ]
        page_data["est_entete_pied_page_repete"] = lignes_repetes

        if exclure and lignes_repetes:
            texte_filtre = "\n".join(
                l for l in page_data["text"].splitlines()
                if l.strip() not in repetitions
            )
            page_data["text"] = _nettoyer_texte(texte_filtre)


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _page_en_image_pil(page: fitz.Page) -> Image.Image:
    """Rend la page PyMuPDF en image PIL haute résolution (partagé par OCR et Claude)."""
    matrice = fitz.Matrix(RENDER_SCALE, RENDER_SCALE)
    pixmap = page.get_pixmap(matrix=matrice)
    return Image.open(io.BytesIO(pixmap.tobytes("png")))


def _nettoyer_texte(texte: str) -> str:
    """
    Normalise le texte extrait :
      - Supprime les espaces en fin de ligne.
      - Réduit les séquences de lignes vides consécutives à une seule.
    """
    lignes = [l.rstrip() for l in texte.splitlines()]
    resultat: list[str] = []
    prev_vide = False
    for ligne in lignes:
        vide = not ligne.strip()
        if vide and prev_vide:
            continue
        resultat.append(ligne)
        prev_vide = vide
    return "\n".join(resultat).strip()


def _extraire_latex(texte: str) -> Optional[str]:
    """
    Extrait les formules LaTeX depuis la réponse Claude.

    Cherche d'abord les formules en display ($$...$$), puis en ligne ($...$).
    """
    display = re.findall(r'\$\$(.+?)\$\$', texte, re.DOTALL)
    if display:
        return "\n\n".join(m.strip() for m in display)
    inline = re.findall(r'(?<!\$)\$([^$\n]+?)\$(?!\$)', texte)
    return "\n".join(m.strip() for m in inline) if inline else None


def _dict_base(
    nom_source: str,
    num_page: int,
    contient_image: bool,
    image_paths: list[str],
) -> dict:
    """Crée le dictionnaire de résultat avec toutes les clés à leur valeur par défaut."""
    return {
        "source": nom_source,
        "page": num_page,
        "text": "",
        "methode_extraction": "natif",
        "contient_image": contient_image,
        "image_paths": image_paths,        # liste des images extraites de cette page
        "alerte_formule_complexe": False,
        "formule_latex": None,
        "claude_necessaire_mais_indisponible": False,
        "est_entete_pied_page_repete": [],
    }


def _page_en_erreur(nom_source: str, num_page: int) -> dict:
    """Dict complet pour une page dont le traitement a levé une exception non interceptée."""
    d = _dict_base(nom_source, num_page, False, [])
    d["methode_extraction"] = "echec"
    return d


# ── Statistiques ──────────────────────────────────────────────────────────────

def afficher_statistiques(pages: list[dict], nom_fichier: str) -> None:
    """
    Affiche un résumé synthétique du traitement d'un PDF.

    Conçu pour être appelé après extraire_pdf() afin de documenter
    la répartition réelle entre traitement local et appels Claude.
    """
    nb = len(pages)
    compteurs = Counter(p["methode_extraction"] for p in pages)
    nb_images = sum(1 for p in pages if p["image_paths"])
    nb_images_total = sum(len(p["image_paths"]) for p in pages)
    nb_formules = sum(1 for p in pages if p["alerte_formule_complexe"])
    nb_claude_absent = sum(1 for p in pages if p["claude_necessaire_mais_indisponible"])

    print(f"\nFichier : {Path(nom_fichier).name} ({nb} pages)")
    print(f"  - Extraction native             : {compteurs.get('natif', 0)} pages")
    print(f"  - OCR local                     : {compteurs.get('ocr_local', 0)} pages")
    print(f"  - Fallback Claude               : {compteurs.get('claude', 0)} pages")
    print(f"  - Échecs                        : {compteurs.get('echec', 0)} pages")
    print(f"  - Pages avec image(s)           : {nb_images}")
    print(f"  - Images extraites (total)      : {nb_images_total}")
    print(f"  - Formules complexes détectées  : {nb_formules}")
    if nb_claude_absent:
        print(f"  - Claude requis mais indisponible : {nb_claude_absent} pages")


# ── Test manuel en ligne de commande ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py chemin/vers/fichier.pdf")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    resultat = extraire_pdf(sys.argv[1])

    for page in resultat:
        print(f"--- Page {page['page']} (méthode: {page['methode_extraction']}) ---")
        print(f"Images extraites : {len(page['image_paths'])} — {page['image_paths']}")
        print(f"Alerte formule complexe : {page['alerte_formule_complexe']}")
        if page["formule_latex"]:
            print(f"LaTeX détecté : {page['formule_latex']}")
        print(page["text"][:300])
        print()

    afficher_statistiques(resultat, sys.argv[1])
