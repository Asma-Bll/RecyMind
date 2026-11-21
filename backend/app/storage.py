
from pathlib import Path
from uuid import uuid4
from io import BytesIO

from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError


# Dossier de stockage
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "tris"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo

ALLOWED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png"
}


async def save_tri_image(file: UploadFile) -> str:
    """
    Valide et enregistre une image reçue.
    Retourne le chemin relatif du fichier.
    """

    if not file:
        raise HTTPException(
            status_code=400,
            detail="Image obligatoire."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Le fichier est vide."
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image trop volumineuse. Maximum : 5 Mo."
        )

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()

            image_format = image.format

    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Le fichier fourni n'est pas une image valide."
        )

    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Format accepté : JPEG ou PNG."
        )

    extension = ALLOWED_FORMATS[image_format]
    filename = f"{uuid4().hex}{extension}"

    file_path = UPLOAD_DIR / filename

    file_path.write_bytes(content)

    return f"uploads/tris/{filename}"
