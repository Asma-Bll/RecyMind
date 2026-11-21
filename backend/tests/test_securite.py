import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from auth.models import Utilisateur
from auth.security import create_token, hash_password
from config import settings
from database import Base, SessionLocal, engine
from main import app
from tris.models import Tri

TRI_TRIE = uuid.uuid4()
ROLES = {"operateur1": "operator", "admin1": "admin", "simulateur": "simulateur"}


@pytest.fixture(scope="module", autouse=True)
def base_de_test():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    for name, role in ROLES.items():
        db.add(Utilisateur(username=name, role=role, password_hash=hash_password("secret123")))
    db.add(Tri(id=TRI_TRIE, image_url="/images/a.jpg", type="plastique", confiance=0.9, bac="bac_1", statut="trie"))
    db.commit()
    db.close()


async def boom():
    raise ValueError("mot de passe interne secret")


app.add_api_route("/api/v1/_boom", boom, methods=["GET"])
client = TestClient(app)
client_500 = TestClient(app, raise_server_exceptions=False)


def login(name):
    return client.post("/api/v1/login", json={"username": name, "password": "secret123"}).json()


def bearer(name):
    return {"Authorization": "Bearer " + login(name)["access_token"]}


# ---- mots de passe et jetons ----
def test_mot_de_passe_stocke_en_hash_bcrypt():
    db = SessionLocal()
    u = db.query(Utilisateur).filter_by(username="admin1").first()
    assert u.password_hash != "secret123" and u.password_hash.startswith("$2")
    db.close()


def test_reponse_login_sans_hash_ni_mot_de_passe():
    texte = str(login("admin1"))
    assert "password" not in texte and "$2" not in texte


def test_jeton_expire_apres_la_duree_configuree():
    d = jwt.decode(login("admin1")["access_token"], settings.SECRET_KEY, algorithms=["HS256"])
    reste = d["exp"] - datetime.now(timezone.utc).timestamp()
    assert abs(reste - settings.TOKEN_MINUTES * 60) < 60


def test_jeton_signe_avec_une_autre_cle_refuse():
    faux = jwt.encode({"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "autre_cle", algorithm="HS256")
    r = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"}, headers={"Authorization": "Bearer " + faux})
    assert r.status_code == 401


def test_jeton_valide_mais_utilisateur_inexistant_401():
    jeton = create_token(str(uuid.uuid4()), "admin")
    r = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"}, headers={"Authorization": "Bearer " + jeton})
    assert r.status_code == 401


def test_schema_d_autorisation_incorrect_401():
    r = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"}, headers={"Authorization": "Token abc"})
    assert r.status_code == 401


def test_apres_expiration_un_nouveau_login_fonctionne():
    expire = jwt.encode({"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm="HS256")
    r = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"}, headers={"Authorization": "Bearer " + expire})
    assert r.status_code == 401
    assert client.post("/api/v1/login", json={"username": "admin1", "password": "secret123"}).status_code == 200


# ---- matrice des roles (contrat 4.4), route de correction ----
@pytest.mark.parametrize("qui,attendu", [("operateur1", "ok"), ("admin1", "ok"), ("simulateur", 403), (None, 401)])
def test_matrice_correction(qui, attendu):
    h = bearer(qui) if qui else {}
    r = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"}, headers=h)
    if attendu == "ok":
        assert r.status_code not in (401, 403)       # 409 car le tri est deja "trie" : l'acces est bien autorise
    else:
        assert r.status_code == attendu


# ---- format des erreurs (contrat section 10) ----
def test_401_et_403_ont_un_detail_texte():
    r401 = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"})
    r403 = client.post(f"/api/v1/tris/{TRI_TRIE}/correction", json={"type_corrige": "verre"}, headers=bearer("simulateur"))
    assert isinstance(r401.json()["detail"], str) and isinstance(r403.json()["detail"], str)


def test_422_liste_sans_valeurs_recues():
    r = client.post("/api/v1/login", json={"username": "admin1", "mot_de_passe_mal_nomme": "TRES_SECRET"})
    assert r.status_code == 422
    d = r.json()["detail"]
    assert isinstance(d, list) and all(set(e) == {"loc", "msg", "type"} for e in d)
    assert "TRES_SECRET" not in r.text and "admin1" not in r.text


def test_500_message_generique_sans_detail_interne():
    r = client_500.get("/api/v1/_boom")
    assert r.status_code == 500
    assert r.json() == {"detail": "Erreur interne du serveur."}
    assert "secret" not in r.text and "ValueError" not in r.text
