import os

os.environ.setdefault("SECRET_KEY", "cle_de_test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_login.db")

from fastapi.testclient import TestClient  # noqa: E402

from auth.models import Utilisateur  # noqa: E402
from auth.security import hash_password  # noqa: E402
from database import SessionLocal, Base, engine  # noqa: E402
from main import app  # noqa: E402

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
db = SessionLocal()
for name, role in [("operateur1", "operator"), ("admin1", "admin"), ("simulateur", "simulateur")]:
    db.add(Utilisateur(username=name, role=role, password_hash=hash_password("secret123")))
db.commit()
db.close()

client = TestClient(app)


def test_sante():
    assert client.get("/api/v1/sante").json() == {"etat": "ok"}


def test_login_ok_pour_chaque_role():
    for name, role in [("operateur1", "operator"), ("admin1", "admin"), ("simulateur", "simulateur")]:
        r = client.post("/api/v1/login", json={"username": name, "password": "secret123"})
        assert r.status_code == 200
        d = r.json()
        assert d["token_type"] == "bearer" and d["access_token"]
        assert d["user"]["role"] == role and d["user"]["username"] == name


def test_login_mauvais_mot_de_passe_et_mauvais_nom_meme_erreur():
    a = client.post("/api/v1/login", json={"username": "admin1", "password": "faux"})
    b = client.post("/api/v1/login", json={"username": "inconnu", "password": "faux"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() == {"detail": "Identifiants incorrects."}


def test_login_champs_manquants_renvoie_422():
    assert client.post("/api/v1/login", json={"username": "admin1"}).status_code == 422


def test_cors_autorise_le_frontend():
    r = client.options("/api/v1/login", headers={
        "Origin": "http://localhost:5500", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5500"


def test_cors_refuse_une_autre_origine():
    r = client.options("/api/v1/login", headers={
        "Origin": "http://autre-site.com", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
