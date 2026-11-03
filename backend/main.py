import asyncio
import random
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="RecyMind API (squelette)")

# CORS : pour que le frontend (autre port) puisse appeler le backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dossier d'images, servi sous /images (sans /api/v1)
IMAGES = Path(__file__).parent / "images"
IMAGES.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=IMAGES), name="images")

CLASSES = ["plastique", "papier_carton", "verre", "metal", "textile", "autre"]
BACS = {"plastique": "bac_1", "papier_carton": "bac_2", "verre": "bac_3",
        "metal": "bac_4", "textile": "bac_5", "autre": "bac_6"}


def faux_tri():
    """Fabrique un faux tri, au format exact du contrat d'API."""
    classe = random.choice(CLASSES)
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
        "type": classe,
        "confiance": confiance,
        "bac": bac,
        "statut": statut,
        "correction": None,
    }


@app.get("/api/v1/stats")
def stats():
    # Données fictives (sans filtre, donc periode = null)
    return {
        "periode": None,
        "total_tris": 120,
        "par_type": {"plastique": 30, "papier_carton": 25, "verre": 20,
                     "metal": 15, "textile": 10, "autre": 20},
        "nombre_controle_manuel": 12,
        "nombre_a_traiter": 8,
        "taux_incertitude": 0.10,
        "debit_objets_minute": 4.2,
    }


@app.websocket("/api/v1/ws")
async def ws(websocket: WebSocket):
    # La vérification du jeton sera ajoutée plus tard
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"event": "nouveau_tri", "data": faux_tri()})
            await asyncio.sleep(3)   # un faux tri toutes les 3 secondes
    except WebSocketDisconnect:
        pass