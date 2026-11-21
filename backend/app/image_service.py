from pathlib import Path
from urllib.parse import unquote

from fastapi import HTTPException


# backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# backend/images/
IMAGES_DIR = BASE_DIR / "images"


def valider_image_url(image_url: str) -> Path:
    """
    Vérifie que image_url :
    - commence par /images/
    - ne contient pas de chemin dangereux
    - pointe vers un fichier existant dans backend/images/
    - ne permet pas de sortir du dossier images/
    
    Retourne le chemin absolu du fichier.
    """

    if not isinstance(image_url, str) or not image_url.strip():
        raise HTTPException(
            status_code=422,
            detail="Le chemin de l'image est obligatoire."
        )

    chemin = unquote(image_url.strip())

    if not chemin.startswith("/images/"):
        raise HTTPException(
            status_code=422,
            detail="Le chemin doit commencer par /images/."
        )

    if "\\" in chemin or "\x00" in chemin:
        raise HTTPException(
            status_code=422,
            detail="Chemin d'image invalide."
        )

    if "?" in chemin or "#" in chemin:
        raise HTTPException(
            status_code=422,
            detail="Le chemin ne doit pas contenir de paramètres."
        )

    nom_fichier = chemin.removeprefix("/images/")

    if not nom_fichier or nom_fichier.startswith("/"):
        raise HTTPException(
            status_code=422,
            detail="Nom de fichier invalide."
        )

    dossier_images = IMAGES_DIR.resolve()
    fichier = (dossier_images / nom_fichier).resolve()

    # Empêche les chemins ../ et les liens symboliques vers l'extérieur.
    try:
        fichier.relative_to(dossier_images)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Accès au fichier interdit."
        )

    if not fichier.exists() or not fichier.is_file():
        raise HTTPException(
            status_code=422,
            detail="L'image indiquée n'existe pas."
        )

    return fichier
