import csv
import uuid

import pytest

from auth.models import Utilisateur
from auth.security import hash_password
from corrections.models import Correction
from database import Base, SessionLocal, engine
from export_corrections import exporter
from tris.models import Tri



@pytest.fixture()
def contexte(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    (images / "b.jpg").write_bytes(b"image-b")
    (tmp_path / "secret.txt").write_text("ne doit jamais etre copie")

    db = SessionLocal()

    db.query(Correction).delete()
    db.query(Tri).delete()
    db.commit()

    u = Utilisateur(
        username="op_" + uuid.uuid4().hex,
        role="operator",
        password_hash=hash_password("x"),
    )
    db.add(u)
    db.flush()

    tris = {
        "ok": Tri(image_url="/images/b.jpg", type="metal", confiance=0.28, bac=None, statut="controle_manuel"),
        "dangereux": Tri(image_url="/images/../secret.txt", type="metal", confiance=0.2, bac=None, statut="controle_manuel"),
        "absent": Tri(image_url="/images/inconnue.jpg", type="verre", confiance=0.3, bac=None, statut="controle_manuel"),
        "non_corrige": Tri(image_url="/images/b.jpg", type="verre", confiance=0.3, bac=None, statut="controle_manuel"),
    }

    for t in tris.values():
        db.add(t)

    db.flush()

    for k in ("ok", "dangereux", "absent"):
        db.add(Correction(
            tri_id=tris[k].id,
            type_corrige="papier_carton",
            utilisateur_id=u.id,
        ))

    db.commit()

    try:
        yield db, images, tmp_path / "retraining", tris["ok"].id
    finally:
        tri_ids = [t.id for t in tris.values()]
        db.query(Correction).filter(Correction.tri_id.in_(tri_ids)).delete(synchronize_session=False)
        db.query(Tri).filter(Tri.id.in_(tri_ids)).delete(synchronize_session=False)
        db.query(Utilisateur).filter(Utilisateur.id == u.id).delete(synchronize_session=False)
        db.commit()
        db.close()



def test_export_copie_et_manifest(contexte):
    db, images, sortie, tri_id = contexte
    assert exporter(db, images, sortie) == 1
    assert (sortie / "papier_carton" / f"{tri_id}_b.jpg").read_bytes() == b"image-b"
    lignes = list(csv.DictReader(open(sortie / "manifest.csv", encoding="utf-8")))
    assert len(lignes) == 1 and lignes[0]["type_ia"] == "metal" and lignes[0]["type_corrige"] == "papier_carton"


def test_export_ignore_chemin_dangereux_image_absente_et_tri_non_corrige(contexte):
    db, images, sortie, _ = contexte
    exporter(db, images, sortie)
    fichiers = [p.name for p in sortie.rglob("*") if p.is_file()]
    assert "secret.txt" not in str(fichiers) and len(fichiers) == 2   # 1 image + manifest.csv


def test_export_idempotent(contexte):
    db, images, sortie, _ = contexte
    assert exporter(db, images, sortie) == 1
    assert exporter(db, images, sortie) == 0
    assert len(list(csv.DictReader(open(sortie / "manifest.csv", encoding="utf-8")))) == 1
