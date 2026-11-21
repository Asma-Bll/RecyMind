"""Dependances d'authentification (contrat v1.2, sections 4.2 a 4.5)."""
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from auth.models import Utilisateur
from config import settings
from database import get_db

bearer = HTTPBearer(auto_error=False)  # auto_error=False : on renvoie nous-memes un 401 (pas un 403)


def user_from_token(token: str, db: Session):
    """Renvoie l'utilisateur correspondant au jeton, ou None si le jeton est invalide ou expire."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
    return db.get(Utilisateur, user_id)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Utilisateur:
    if creds is None or not creds.credentials:
        raise HTTPException(401, "Jeton absent.", headers={"WWW-Authenticate": "Bearer"})
    user = user_from_token(creds.credentials, db)
    if user is None:
        raise HTTPException(401, "Jeton invalide ou expiré.", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_role(*roles: str):
    """Exemple : Depends(require_role("operator", "admin")). Renvoie 403 si le role n'est pas autorise."""
    def checker(user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if user.role not in roles:
            raise HTTPException(403, "Accès refusé pour ce rôle.")
        return user
    return checker
