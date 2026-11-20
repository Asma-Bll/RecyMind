from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_password = pwd.hash
verify_password = pwd.verify


def create_token(user_id: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_MINUTES)
    return jwt.encode({"sub": user_id, "role": role, "exp": exp}, settings.SECRET_KEY, algorithm="HS256")
