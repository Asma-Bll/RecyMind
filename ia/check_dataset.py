
from pathlib import Path

DATASET_DIR = Path("dataset/processed")

SPLITS = ["train", "test", "validation"]

CLASSES = [
    "plastique",
    "papier_carton",
    "verre",
    "metal",
    "textile",
    "autre",
    "tapis_vide",
]

EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

total_general = 0

print("\n========== VERIFICATION DU DATASET ==========")

for class_name in CLASSES:

    print(f"\nClasse : {class_name}")

    total_class = 0

    for split in SPLITS:

        folder = DATASET_DIR / split / class_name

        if not folder.exists():
            print(f"ERREUR : dossier manquant : {folder}")
            continue

        count = sum(
            1 for file in folder.iterdir()
            if file.is_file()
            and file.suffix.lower() in EXTENSIONS
        )

        total_class += count

        print(f"{split:12} : {count:5} images")

    print(f"{'TOTAL':12} : {total_class:5} images")

    total_general += total_class

print("\n==============================================")
print("TOTAL GENERAL :", total_general)
