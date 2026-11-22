from fastapi import APIRouter

import stockage
from validation import nettoyer_date

router = APIRouter()


@router.get("/stats")
def statistiques(date_debut: str | None = None, date_fin: str | None = None):
    date_debut = nettoyer_date(date_debut, "date_debut")
    date_fin = nettoyer_date(date_fin, "date_fin")
    return stockage.stats(date_debut, date_fin)