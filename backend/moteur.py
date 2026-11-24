
import asyncio
import logging
import random
from pathlib import Path

import numpy as np
from PIL import Image

from database import SessionLocal
from routes.ia import charger_modele
from tris.models import Tri
from tris.serialization import tri_to_dict
from ws_manager import manager

logger = logging.getLogger("recymind.simulation")

IMAGES_DIR = Path(__file__).resolve().parent / "images"
IMAGE_SIZE = (224, 224)

BACS = {
    "plastique": "bac_1",
    "papier_carton": "bac_2",
    "verre": "bac_3",
    "metal": "bac_4",
    "textile": "bac_5",
    "autre": "bac_6",
}

_etat = "arretee"
_tache = None


def traiter_image(image_path: Path) -> dict:
    """Effectue une prédiction V3 et enregistre le tri dans PostgreSQL."""

    # Préparation identique à l'endpoint /ia/predire
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img = img.resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
        tableau = np.asarray(img, dtype=np.float32)

    model, classes, seuil = charger_modele()

    entree = np.expand_dims(tableau, axis=0)
    probabilites = model.predict(entree, verbose=0)[0]

    index = int(np.argmax(probabilites))
    classe = classes[index]
    confiance = float(probabilites[index])

    # Décision de tri
    if classe == "tapis_vide" or confiance < seuil:
        bac = None
        statut = "controle_manuel"
    else:
        bac = BACS.get(classe)
        statut = "trie"

        if bac is None:
            statut = "controle_manuel"

    # Enregistrement dans PostgreSQL
    db = SessionLocal()

    try:
        tri = Tri(
            image_url=f"/images/{image_path.name}",
            type=classe,
            confiance=confiance,
            bac=bac,
            statut=statut,
        )

        db.add(tri)
        db.commit()
        db.refresh(tri)

        resultat = tri_to_dict(tri)
        return resultat

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


async def _boucle(cadence: int):
    global _etat

    attente = 60 / cadence

    try:
        while True:
            images = [
                p for p in IMAGES_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in
                (".jpg", ".jpeg", ".png", ".webp")
            ]

            if not images:
                logger.warning("Aucune image disponible dans backend/images.")
                break

            image = random.choice(images)

            # La prédiction et l'enregistrement sont exécutés hors de la boucle async
            tri = await asyncio.to_thread(traiter_image, image)

            # Notification des clients WebSocket connectés
            await manager.broadcast({
                "event": "nouveau_tri",
                "data": tri,
            })

            await asyncio.sleep(attente)

    except asyncio.CancelledError:
        logger.info("Simulation arrêtée.")
        raise

    except Exception:
        logger.exception("Erreur pendant la simulation.")

    finally:
        if _tache is asyncio.current_task():
            _etat = "arretee"


def etat():
    return {"etat": _etat}


def demarrer(cadence: int):
    global _etat, _tache

    if _tache is not None and not _tache.done():
        return {
            "etat": "en_cours",
            "message": "Simulation déjà en cours.",
        }

    _etat = "en_cours"
    _tache = asyncio.create_task(_boucle(cadence))

    return {
        "etat": "en_cours",
        "message": "Simulation démarrée.",
    }


def arreter():
    global _etat, _tache

    if _tache is not None and not _tache.done():
        _tache.cancel()

    _etat = "arretee"

    return {
        "etat": "arretee",
        "message": "Simulation arrêtée.",
    }
