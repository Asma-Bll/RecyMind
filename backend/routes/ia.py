
import json
import logging
import uuid
from io import BytesIO
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from auth.deps import require_role
from database import get_db
from tris.models import Tri
from tris.serialization import tri_to_dict

router = APIRouter()
logger = logging.getLogger("recymind.ia")

# Chemins des fichiers du modele v3
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "ia" / "modeles_v3" / "modele_v3.keras"
CLASSES_PATH = ROOT / "ia" / "modeles_v3" / "classes_v3.json"
THRESHOLD_PATH = ROOT / "ia" / "modeles_v3" / "seuil_v3.json"

# Dossier de stockage des images
IMAGES_DIR = Path(__file__).resolve().parents[1] / "images"

IMAGE_SIZE = (224, 224)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

# Chargement unique du modele
_model = None
_classes = None
_threshold = None


def charger_modele():
    global _model, _classes, _threshold

    if _model is None:
        try:
            with open(CLASSES_PATH, encoding="utf-8") as f:
                _classes = json.load(f)

            with open(THRESHOLD_PATH, encoding="utf-8") as f:
                config = json.load(f)

            _threshold = float(config["seuil"])

            if len(_classes) != 7:
                raise ValueError("Le modele doit avoir 7 classes.")

            _model = tf.keras.models.load_model(
                str(MODEL_PATH),
                compile=False
            )

            if _model.output_shape[-1] != len(_classes):
                raise ValueError(
                    "Les classes ne correspondent pas au modele."
                )

            logger.info("Modele RecyMind v3 charge.")

        except Exception as exc:
            logger.exception("Impossible de charger le modele v3.")
            raise HTTPException(
                status_code=503,
                detail="Le service IA est temporairement indisponible."
            ) from exc

    return _model, _classes, _threshold


@router.post("/ia/predire")
async def predire_dechet(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("operator", "admin"))
):
    # 1. Verifier le type de fichier
    if image.content_type not in (
        "image/jpeg",
        "image/png",
        "image/webp"
    ):
        raise HTTPException(
            status_code=415,
            detail="Formats acceptes : JPEG, PNG et WEBP."
        )

    # 2. Lire l'image
    contenu = await image.read(MAX_IMAGE_SIZE + 1)

    if len(contenu) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image trop volumineuse. Maximum : 5 MB."
        )

    if not contenu:
        raise HTTPException(
            status_code=400,
            detail="Image vide."
        )

    # 3. Preparer l'image pour le modele
    try:
        with Image.open(BytesIO(contenu)) as img:
            img = img.convert("RGB")
            img = img.resize(
                IMAGE_SIZE,
                Image.Resampling.BILINEAR
            )
            tableau = np.asarray(img, dtype=np.float32)

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Image invalide ou illisible."
        )

    # 4. Charger le modele et effectuer la prediction
    model, classes, seuil = charger_modele()

    entree = np.expand_dims(tableau, axis=0)
    probabilites = model.predict(entree, verbose=0)[0]

    index = int(np.argmax(probabilites))
    classe = classes[index]
    confiance = float(probabilites[index])

    # 5. Prendre la decision
    if classe == "tapis_vide":
        decision = "controle_manuel"
        raison = "Classe tapis_vide : aucun tri automatique."

    elif confiance >= seuil:
        decision = "tri_automatique"
        raison = "Confiance superieure ou egale au seuil."

    else:
        decision = "controle_manuel"
        raison = "Confiance inferieure au seuil."

    # 6. Preparer le nom et le chemin de l'image
    extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }[image.content_type]

    image_name = f"{uuid.uuid4()}{extension}"
    image_path = IMAGES_DIR / image_name
    image_url = f"/images/{image_name}"

    # 7. Enregistrer l'image et le tri dans PostgreSQL
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(contenu)

        # Le modele Tri utilise "trie" et non "tri_automatique"
        statut_db = (
            "controle_manuel"
            if decision == "controle_manuel"
            else "trie"
        )

        tri = Tri(
            image_url=image_url,
            type=classe,
            confiance=confiance,
            bac=None,
            statut=statut_db
        )

        db.add(tri)
        db.commit()
        db.refresh(tri)

    except (SQLAlchemyError, OSError) as exc:
        db.rollback()

        # Supprimer l'image si la sauvegarde echoue
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Impossible de supprimer l'image.")

        logger.exception("Erreur lors de l'enregistrement du tri.")

        raise HTTPException(
            status_code=500,
            detail="Impossible d'enregistrer le tri dans la base de donnees."
        ) from exc

    # 8. Retourner le resultat
    return {
        "id_tri": str(tri.id),
        "image_url": image_url,
        "statut_base": statut_db,
        "classe": classe,
        "confiance": round(confiance, 4),
        "decision": decision,
        "raison": raison,
        "seuil": seuil,
        "probabilites": {
            nom: round(float(p), 4)
            for nom, p in zip(classes, probabilites)
        },
        "tri": tri_to_dict(tri)
    }
