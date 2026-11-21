import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.deps import require_role
from corrections.models import Correction
from database import get_db
from tris.models import Tri
from tris.serialization import tri_to_dict

router = APIRouter()


class CorrectionIn(BaseModel):
    # tapis_vide est refuse : seules les 6 classes de dechets sont valides (contrat 7.5)
    type_corrige: Literal["plastique", "papier_carton", "verre", "metal", "textile", "autre"]


@router.post("/tris/{tri_id}/correction")
def corriger_tri(
    tri_id: str,
    data: CorrectionIn,                      # 422 si type_corrige est invalide (verifie en premier par FastAPI)
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
        raise HTTPException(409, "Seuls les tris en contrôle manuel peuvent être corrigés.")
    if tri.correction is not None:
        raise HTTPException(409, "Ce tri a déjà été corrigé.")

    db.add(Correction(tri_id=tri.id, type_corrige=data.type_corrige, utilisateur_id=user.id))
    try:
        db.commit()
    except IntegrityError:                   # deux corrections simultanees : la contrainte unique protege la base
        db.rollback()
        raise HTTPException(409, "Ce tri a déjà été corrigé.")
    db.refresh(tri)
    return tri_to_dict(tri)                  # type, confiance, bac et statut gardent la decision initiale
