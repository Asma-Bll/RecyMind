"""Cree les trois comptes de depart. Les mots de passe viennent de l'environnement.

Usage (apres avoir rempli .env) :  python seed_users.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

from auth.models import Utilisateur  # noqa: E402
from auth.security import hash_password  # noqa: E402
from database import SessionLocal, Base, engine  # noqa: E402

Base.metadata.create_all(engine)

comptes = [
    ("operateur1", "operator", "SEED_OPERATOR_PWD"),
    ("admin1", "admin", "SEED_ADMIN_PWD"),
    ("simulateur", "simulateur", "SEED_SIMULATOR_PWD"),
]

db = SessionLocal()
for username, role, var in comptes:
    pwd = os.environ.get(var)
    if not pwd:
        raise SystemExit(f"Variable {var} manquante dans .env")
    if db.query(Utilisateur).filter_by(username=username).first():
        print(f"{username} existe deja, ignore.")
        continue
    db.add(Utilisateur(username=username, role=role, password_hash=hash_password(pwd)))
    print(f"{username} cree ({role}).")
db.commit()
db.close()
