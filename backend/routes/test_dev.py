import random
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

import stockage
from routes.ws import diffuser

router = APIRouter()

IMAGES = Path(__file__).resolve().parent.parent / "images"
BACS = {"plastique": "bac_1", "papier_carton": "bac_2", "verre": "bac_3",
        "metal": "bac_4", "textile": "bac_5", "autre": "bac_6"}


def faux_tri():
    classe = random.choice(list(BACS))
    confiance = round(random.uniform(0.2, 0.99), 2)
    if confiance < 0.40:
        bac, statut = None, "controle_manuel"
    else:
        bac, statut = BACS[classe], "trie"
    images = list(IMAGES.glob("*.jpg"))
    nom = random.choice(images).name if images else "dechet_001.jpg"
    return {
        "id": str(uuid.uuid4()),
        "date": datetime.now().astimezone().isoformat(timespec="seconds"),
        "image_url": f"/images/{nom}",
        "type": classe, "confiance": confiance,
        "bac": bac, "statut": statut, "correction": None,
    }


@router.post("/test/faux-tri", status_code=201)
async def creer_faux_tri():
    tri = stockage.ajouter_tri(faux_tri())
    await diffuser({"event": "nouveau_tri", "data": tri})
    return tri