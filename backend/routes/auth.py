from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.models import Utilisateur
from auth.security import verify_password, create_token
from database import get_db

router = APIRouter()


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    u = db.query(Utilisateur).filter_by(username=data.username).first()
    # Meme message pour un mauvais nom et un mauvais mot de passe (contrat v1.2, section 4.1)
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")
    return {
        "access_token": create_token(str(u.id), u.role),
        "token_type": "bearer",
        "user": {"id": str(u.id), "username": u.username, "role": u.role},
    }
