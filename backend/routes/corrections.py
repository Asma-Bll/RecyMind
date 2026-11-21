
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.deps import require_role
from corrections.models import Correction
from database import get_db
from tris.models import Tri
from tris.serialization import tri_to_dict

router = APIRouter()


class CorrectionIn(BaseModel):
    type_corrige: Literal[
        "plastique",
        "papier_carton",
        "verre",
        "metal",
        "textile",
        "autre"
    ]


# GET : liste des tris en attente de contrôle manuel
@router.get("/corrections/controle-manuel")
def lister_tris_a_controler(
    db: Session = Depends(get_db),
    user=Depends(require_role("operator", "admin")),
):
    tris = db.scalars(
        select(Tri)
        .where(Tri.statut == "controle_manuel")
        .order_by(Tri.date.desc())
    ).all()

    return [
        tri_to_dict(tri)
        for tri in tris
        if tri.correction is None
    ]


# POST : corriger un tri
@router.post("/tris/{tri_id}/correction")
def corriger_tri(
    tri_id: str,
    data: CorrectionIn,
    db: Session = Depends(get_db),
    user=Depends(require_role("operator", "admin")),
):
    try:
        tri = db.get(Tri, uuid.UUID(tri_id))
    except ValueError:
        tri = None

    if tri is None:
        raise HTTPException(404, "Tri introuvable.")

    if tri.statut != "controle_manuel":
        raise HTTPException(
            409,
            "Seuls les tris en controle manuel peuvent etre corriges."
        )

    if tri.correction is not None:
        raise HTTPException(409, "Ce tri a deja ete corrige.")

    db.add(
        Correction(
            tri_id=tri.id,
            type_corrige=data.type_corrige,
            utilisateur_id=user.id
        )
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ce tri a deja ete corrige.")

    db.refresh(tri)
    return tri_to_dict(tri)
