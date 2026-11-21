
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from .image_service import valider_image_url

from .database import get_db
from .models import Tri
from .schemas import (
    ActionResponse,
    TriCreate,
    TriListRead,
    TriRead,
)

app = FastAPI(title="RecyMind API", version="1.2.0")
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"

app.mount(
    "/images",
    StaticFiles(directory=str(IMAGES_DIR)),
    name="images"
)

BACS = {
    "plastique": "bac_1",
    "papier_carton": "bac_2",
    "verre": "bac_3",
    "metal": "bac_4",
    "textile": "bac_5",
    "autre": "bac_6",
}

SEUIL_CONFIANCE = 0.4


@app.get("/")
def accueil():
    return {"message": "RecyMind API opérationnelle"}



@app.post(
    "/api/v1/tris",
    response_model=TriRead,
    status_code=201,
    responses={200: {"model": ActionResponse}},
)
def creer_tri(
    donnees: TriCreate,
    db: Session = Depends(get_db),
):
    # 1. Vérifier que l'image existe et que son chemin est valide.
    valider_image_url(donnees.image_url)

    # 2. Cas particulier : tapis vide.
    # Aucun enregistrement et aucun événement WebSocket.
    if donnees.type == "tapis_vide":
        return JSONResponse(
            status_code=200,
            content={
                "action": "aucune",
                "message": "Aucun déchet détecté.",
            },
        )

    # 3. Déterminer le bac et le statut.
    if donnees.confiance < SEUIL_CONFIANCE:
        statut = "controle_manuel"
        bac = None
    else:
        statut = "trie"
        bac = BACS[donnees.type]

    # 4. Construire l'enregistrement.
    tri = Tri(
        date=donnees.date,
        image_url=donnees.image_url,
        type=donnees.type,
        confiance=donnees.confiance,
        bac=bac,
        statut=statut,
    )

    # 5. Enregistrer dans PostgreSQL.
    try:
        db.add(tri)
        db.commit()
        db.refresh(tri)

        return tri

    except Exception as e:
        db.rollback()

        print("ERREUR POSTGRESQL :", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement du tri.",
        )



@app.get("/api/v1/tris", response_model=TriListRead)
def lister_tris(
    date_debut: str | None = None,
    date_fin: str | None = None,
    type: str | None = None,
    statut: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Tri)

    if date_debut:
        from datetime import datetime
        try:
            debut = datetime.fromisoformat(date_debut.replace("Z", "+00:00"))
            query = query.filter(Tri.date >= debut)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="date_debut doit être une date ISO 8601 valide.",
            )

    if date_fin:
        from datetime import datetime
        try:
            fin = datetime.fromisoformat(date_fin.replace("Z", "+00:00"))
            query = query.filter(Tri.date <= fin)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="date_fin doit être une date ISO 8601 valide.",
            )

    types_valides = set(BACS.keys())
    statuts_valides = {"trie", "controle_manuel"}

    if type is not None:
        if type not in types_valides:
            raise HTTPException(
                status_code=422,
                detail="Type de déchet invalide.",
            )
        query = query.filter(Tri.type == type)

    if statut is not None:
        if statut not in statuts_valides:
            raise HTTPException(
                status_code=422,
                detail="Statut invalide.",
            )
        query = query.filter(Tri.statut == statut)

    total = query.count()

    items = (
        query.order_by(Tri.date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
    }
