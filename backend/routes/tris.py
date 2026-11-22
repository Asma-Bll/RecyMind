from typing import Literal
from fastapi import APIRouter, Query

import stockage
from validation import nettoyer_date

router = APIRouter()

TypeDechet = Literal["plastique", "papier_carton", "verre", "metal", "textile", "autre"]
Statut = Literal["trie", "controle_manuel"]


@router.get("/tris")
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