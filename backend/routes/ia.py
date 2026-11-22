
import json
import logging
from io import BytesIO
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth.deps import require_role

router = APIRouter()
logger = logging.getLogger("recymind.ia")

# Chemins des fichiers du modèle v3
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "ia" / "modeles_v3" / "modele_v3.keras"
CLASSES_PATH = ROOT / "ia" / "modeles_v3" / "classes_v3.json"
THRESHOLD_PATH = ROOT / "ia" / "modeles_v3" / "seuil_v3.json"

IMAGE_SIZE = (224, 224)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

# Chargement unique du modèle
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
                raise ValueError("Le modèle doit avoir 7 classes.")

            _model = tf.keras.models.load_model(
                str(MODEL_PATH),
                compile=False
            )

            if _model.output_shape[-1] != len(_classes):
                raise ValueError("Les classes ne correspondent pas au modèle.")

            logger.info("Modèle RecyMind v3 chargé.")

        except Exception as exc:
            logger.exception("Impossible de charger le modèle v3.")
            raise HTTPException(
                status_code=503,
                detail="Le service IA est temporairement indisponible."
            ) from exc

    return _model, _classes, _threshold


@router.post("/ia/predire")
async def predire_dechet(
    image: UploadFile = File(...),
    user=Depends(require_role("operator", "admin"))
):
    # Vérifier le type de fichier
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=415,
            detail="Formats acceptés : JPEG, PNG et WEBP."
        )

    contenu = await image.read(MAX_IMAGE_SIZE + 1)

    if len(contenu) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image trop volumineuse. Maximum : 5 MB."
        )

    if not contenu:
        raise HTTPException(400, "Image vide.")

    # Préparer l'image
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

    # Charger le modèle et prédire
    model, classes, seuil = charger_modele()

    entree = np.expand_dims(tableau, axis=0)
    probabilites = model.predict(entree, verbose=0)[0]

    index = int(np.argmax(probabilites))
    classe = classes[index]
    confiance = float(probabilites[index])

    # Décision selon les règles RecyMind
    if classe == "tapis_vide":
        decision = "controle_manuel"
        raison = "Classe tapis_vide : aucun tri automatique."
    elif confiance >= seuil:
        decision = "tri_automatique"
        raison = "Confiance supérieure ou égale au seuil."
    else:
        decision = "controle_manuel"
        raison = "Confiance inférieure au seuil."

    return {
        "classe": classe,
        "confiance": round(confiance, 4),
        "decision": decision,
        "raison": raison,
        "seuil": seuil,
        "probabilites": {
            nom: round(float(p), 4)
            for nom, p in zip(classes, probabilites)
        }
    }
