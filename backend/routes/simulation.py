from fastapi import APIRouter, Query

import moteur

router = APIRouter()


@router.post("/simulation/start")
async def demarrer(cadence: int = Query(20, ge=1, le=120, description="Objets par minute")):
    return moteur.demarrer(cadence)


@router.post("/simulation/stop")
async def arreter():
    return moteur.arreter()


@router.get("/simulation/etat")
def etat():
    return moteur.etat()