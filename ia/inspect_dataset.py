
from pathlib import Path
from collections import Counter
from PIL import Image

# MODIFIE ce chemin pour pointer vers le dossier extrait.
# Il doit s'agir du dossier qui contient les 10 dossiers de classes.
DATASET_ROOT = Path(r"C:\Users\assma\Downloads\Mini-projet en Intelligence Artificielle\archive\original")

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

if not DATASET_ROOT.exists():
    raise FileNotFoundError(
        f"Dossier introuvable : {DATASET_ROOT}\n"
        "Corrige DATASET_ROOT dans le script."
    )

print("Dossier inspecté :", DATASET_ROOT)
print("\nSous-dossiers :")

for folder in sorted(DATASET_ROOT.iterdir()):
    if folder.is_dir():
        print(" -", folder.name)

print("\nComptage des images :")
total = 0
invalides = []

for folder in sorted(DATASET_ROOT.iterdir()):
    if not folder.is_dir():
        continue

    files = [
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONS
    ]

    total += len(files)
    print(f"{folder.name:20} : {len(files)} images")

    for path in files:
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception:
            invalides.append(path)

print("\nTOTAL :", total)
print("Images illisibles :", len(invalides))

for path in invalides:
    print("IMAGE INVALIDE :", path)
