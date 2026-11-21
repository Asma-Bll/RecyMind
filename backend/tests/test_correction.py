import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402
from starlette.websockets import WebSocketDisconnect  # noqa: E402

from auth.models import Utilisateur  # noqa: E402
from auth.security import hash_password  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from tris.models import Tri  # noqa: E402

TRI_TRIE, TRI_CTRL, TRI_CTRL2 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


@pytest.fixture(scope="module", autouse=True)
def base_de_test():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    for name, role in [("operateur1", "operator"), ("admin1", "admin"), ("simulateur", "simulateur")]:
        db.add(Utilisateur(username=name, role=role, password_hash=hash_password("secret123")))
    db.add(Tri(id=TRI_TRIE, image_url="/images/a.jpg", type="plastique", confiance=0.92, bac="bac_1", statut="trie"))
    db.add(Tri(id=TRI_CTRL, image_url="/images/b.jpg", type="metal", confiance=0.28, bac=None, statut="controle_manuel"))
    db.add(Tri(id=TRI_CTRL2, image_url="/images/c.jpg", type="verre", confiance=0.30, bac=None, statut="controle_manuel"))
    db.commit()
    db.close()


client = TestClient(app)


def token(name):
    r = client.post("/api/v1/login", json={"username": name, "password": "secret123"})
    return r.json()["access_token"]


def auth(name):
    return {"Authorization": "Bearer " + token(name)}


def post(tri_id, body, who="operateur1"):
    return client.post(f"/api/v1/tris/{tri_id}/correction", json=body, headers=auth(who))


# ---- authentification ----
def test_sans_jeton_401():
    assert client.post(f"/api/v1/tris/{TRI_CTRL}/correction", json={"type_corrige": "verre"}).status_code == 401


def test_jeton_invalide_401():
    h = {"Authorization": "Bearer nimportequoi"}
    assert client.post(f"/api/v1/tris/{TRI_CTRL}/correction", json={"type_corrige": "verre"}, headers=h).status_code == 401


def test_jeton_expire_401():
    exp = datetime.now(timezone.utc) - timedelta(minutes=1)
    expired = jwt.encode({"sub": str(uuid.uuid4()), "role": "admin", "exp": exp}, os.environ["SECRET_KEY"], algorithm="HS256")
    h = {"Authorization": "Bearer " + expired}
    assert client.post(f"/api/v1/tris/{TRI_CTRL}/correction", json={"type_corrige": "verre"}, headers=h).status_code == 401


def test_simulateur_403_sur_correction():
    assert post(TRI_CTRL, {"type_corrige": "verre"}, who="simulateur").status_code == 403


# ---- correction ----
def test_422_type_invalide_et_tapis_vide():
    assert post(TRI_CTRL, {"type_corrige": "banane"}).status_code == 422
    r = post(TRI_CTRL, {"type_corrige": "tapis_vide"})
    assert r.status_code == 422 and isinstance(r.json()["detail"], list)


def test_404_tri_inexistant_ou_id_invalide():
    assert post(uuid.uuid4(), {"type_corrige": "verre"}).status_code == 404
    assert post("pas-un-uuid", {"type_corrige": "verre"}).status_code == 404


def test_409_tri_deja_trie():
    r = post(TRI_TRIE, {"type_corrige": "verre"})
    assert r.status_code == 409 and isinstance(r.json()["detail"], str)


def test_correction_ok_puis_409_deuxieme_fois():
    r = post(TRI_CTRL, {"type_corrige": "papier_carton"})
    assert r.status_code == 200
    d = r.json()
    assert d["type"] == "metal" and d["confiance"] == 0.28 and d["bac"] is None and d["statut"] == "controle_manuel"
    assert d["correction"]["type_corrige"] == "papier_carton" and d["correction"]["date_correction"]
    assert post(TRI_CTRL, {"type_corrige": "verre"}, who="admin1").status_code == 409


def test_admin_peut_corriger():
    assert post(TRI_CTRL2, {"type_corrige": "textile"}, who="admin1").status_code == 200


# ---- websocket ----
def test_ws_sans_jeton_refuse():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws"):
            pass


def test_ws_jeton_invalide_refuse():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws?token=faux"):
            pass


def test_ws_simulateur_refuse():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws?token=" + token("simulateur")):
            pass


def test_ws_operateur_accepte():
    with client.websocket_connect("/api/v1/ws?token=" + token("operateur1")) as ws:
        ws.send_text("ping")
