"""Exporte les images corrigees par les operateurs vers un dossier de reentrainement.

Resultat :  <sortie>/<type_corrige>/<tri_id>_<image>  +  <sortie>/manifest.csv
Ce n'est PAS un reentrainement automatique (hors MVP) : c'est un export manuel utilise par Personne 1/2.

Usage :  python export_corrections.py --sortie retraining
"""
import argparse
import csv
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from corrections.models import Correction  # noqa: E402
from database import SessionLocal  # noqa: E402
from tris.models import Tri  # noqa: E402

PREFIXE = "/images/"


def exporter(db, images_dir: Path, sortie: Path) -> int:
    """Copie les nouvelles images corrigees. Renvoie le nombre d'images copiees (idempotent)."""
    images_dir = images_dir.resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    manifest = sortie / "manifest.csv"
    nouveau = not manifest.exists()
    copiees = 0
    with open(manifest, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nouveau:
            w.writerow(["tri_id", "fichier", "type_ia", "confiance", "type_corrige", "date_correction"])
        for tri, corr in db.query(Tri, Correction).join(Correction, Correction.tri_id == Tri.id).all():
            if not tri.image_url.startswith(PREFIXE):
                print(f"Ignore (chemin inattendu) : {tri.image_url}")
                continue
            src = (images_dir / tri.image_url[len(PREFIXE):]).resolve()
            if not src.is_relative_to(images_dir):          # empeche la sortie du dossier images/
                print(f"Ignore (chemin dangereux) : {tri.image_url}")
                continue
            if not src.is_file():
                print(f"Ignore (image introuvable) : {src}")
                continue
            dest = sortie / corr.type_corrige / f"{tri.id}_{src.name}"
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            w.writerow([tri.id, dest.relative_to(sortie).as_posix(), tri.type, tri.confiance,
                        corr.type_corrige, corr.date_correction.isoformat()])
            copiees += 1
    return copiees


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--images", default="images", help="dossier des images du backend")
    p.add_argument("--sortie", default="retraining", help="dossier de sortie")
    a = p.parse_args()
    db = SessionLocal()
    try:
        print(f"{exporter(db, Path(a.images), Path(a.sortie))} image(s) exportee(s).")
    finally:
        db.close()
