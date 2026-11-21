import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import stockage

app = FastAPI(title="RecyMind API (semaine 2, stockage provisoire)")

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

TypeDechet = Literal["plastique", "papier_carton", "verre", "metal", "textile", "autre"]
Statut = Literal["trie", "controle_manuel"]


def nettoyer_date(valeur, nom):
    """Vérifie qu'une date est au format ISO 8601. Renvoie la date nettoyée."""
    if valeur is None:
        return None
    valeur = valeur.replace(" ", "+")   # dans une URL, le "+" du fuseau devient un espace
    try:
        datetime.fromisoformat(valeur)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{nom} invalide : format ISO 8601 attendu")
    return valeur


def faux_tri():
    """Fabrique un faux tri au format du contrat (pour tester)."""
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


# ---------- WebSocket : diffusion des nouveaux tris ----------
clients = set()


async def diffuser(message):
    for c in list(clients):
        try:
            await c.send_json(message)
        except Exception:
            clients.discard(c)


@app.websocket("/api/v1/ws")
async def ws(websocket: WebSocket):
    # La vérification du jeton sera ajoutée plus tard
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()   # garde la connexion ouverte
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(websocket)


# ---------- Routes REST ----------
@app.get("/api/v1/tris")
def historique(
    date_debut: str | None = None,
    date_fin: str | None = None,
    type: TypeDechet | None = None,
    statut: Statut | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    date_debut = nettoyer_date(date_debut, "date_debut")
    date_fin = nettoyer_date(date_fin, "date_fin")
    items, total = stockage.lister_tris(date_debut, date_fin, type, statut, page, limit)
    return {"items": items, "page": page, "limit": limit, "total": total}


@app.get("/api/v1/stats")
def statistiques(date_debut: str | None = None, date_fin: str | None = None):
    date_debut = nettoyer_date(date_debut, "date_debut")
    date_fin = nettoyer_date(date_fin, "date_fin")
    return stockage.stats(date_debut, date_fin)


# ---------- Route TEMPORAIRE pour tester (à supprimer à l'intégration) ----------
@app.post("/api/v1/test/faux-tri", status_code=201)
async def creer_faux_tri():
    tri = stockage.ajouter_tri(faux_tri())
    await diffuser({"event": "nouveau_tri", "data": tri})
    return tri