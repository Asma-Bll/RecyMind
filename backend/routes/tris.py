
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from auth.deps import require_role
from database import get_db
from tris.models import Tri
from tris.serialization import tri_to_dict

router = APIRouter()

CLASSES = [
    "plastique",
    "papier_carton",
    "verre",
    "metal",
    "textile",
    "autre",
    "tapis_vide"
]

def filtres_dates(date_debut, date_fin):
    conditions = []
    if date_debut is not None:
        conditions.append(Tri.date >= date_debut)
    if date_fin is not None:
        conditions.append(Tri.date <= date_fin)
    return conditions


@router.get("/tris")
def lister_tris(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    type: str | None = None,
    statut: str | None = None,
    date_debut: datetime | None = None,
    date_fin: datetime | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("operator", "admin")),
):
    conditions = filtres_dates(date_debut, date_fin)

    if type:
        conditions.append(Tri.type == type)

    if statut:
        conditions.append(Tri.statut == statut)

    total = db.scalar(
        select(func.count(Tri.id)).where(*conditions)
    ) or 0

    tris = db.scalars(
        select(Tri)
        .where(*conditions)
        .order_by(Tri.date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {
        "items": [tri_to_dict(tri) for tri in tris],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/stats")
def statistiques(
    date_debut: datetime | None = None,
    date_fin: datetime | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("operator", "admin")),
):
    conditions = filtres_dates(date_debut, date_fin)

    total = db.scalar(
        select(func.count(Tri.id)).where(*conditions)
    ) or 0

    manuels = db.scalar(
        select(func.count(Tri.id)).where(
            *conditions,
            Tri.statut == "controle_manuel",
        )
    ) or 0

    a_traiter = db.scalar(
        select(func.count(Tri.id)).where(
            *conditions,
            Tri.statut == "controle_manuel",
            ~Tri.correction.has(),
        )
    ) or 0

    par_type = {classe: 0 for classe in CLASSES}

    resultats = db.execute(
        select(Tri.type, func.count(Tri.id))
        .where(*conditions)
        .group_by(Tri.type)
    ).all()

    for classe, nombre in resultats:
        if classe in par_type:
            par_type[classe] = nombre

    taux_incertitude = manuels / total if total else 0.0

    maintenant = datetime.now(timezone.utc)
    debut_debit = maintenant - timedelta(minutes=5)

    conditions_debit = [
        Tri.date >= debut_debit,
        Tri.date <= maintenant,
    ]

    if date_debut is not None:
        conditions_debit.append(Tri.date >= date_debut)

    if date_fin is not None:
        conditions_debit.append(Tri.date <= date_fin)

    nombre_recent = db.scalar(
        select(func.count(Tri.id)).where(*conditions_debit)
    ) or 0

    return {
        "total_tris": total,
        "nombre_a_traiter": a_traiter,
        "taux_incertitude": taux_incertitude,
        "debit_objets_minute": nombre_recent / 5,
        "par_type": par_type,
    }
