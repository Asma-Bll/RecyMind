
from pathlib import Path
import json

# ==========================================
# 1. CONFIGURATION
# ==========================================

PROCESSED_DIR = Path("dataset/processed")
AUGMENTED_DIR = Path("dataset/augmented")

CLASSES = [
    "plastique",
    "papier_carton",
    "verre",
    "metal",
    "textile",
    "autre",
    "tapis_vide",
]

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


# ==========================================
# 2. COMPTER LES IMAGES
# ==========================================

def count_images(folder):

    if not folder.exists():
        return 0

    return sum(
        1 for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in IMAGE_EXTENSIONS
    )


def main():

    train_counts = {}

    print("\n========== TRAIN DATASET ==========")

    for class_name in CLASSES:

        # Images originales
        original_folder = (
            PROCESSED_DIR / "train" / class_name
        )

        original_count = count_images(original_folder)

        # Images augmentées
        augmented_folder = (
            AUGMENTED_DIR / "train" / class_name
        )

        augmented_count = count_images(augmented_folder)

        # Total utilisé pour l'entraînement
        total = original_count + augmented_count

        train_counts[class_name] = total

        print(f"\nClasse : {class_name}")
        print("Images originales :", original_count)
        print("Images augmentées :", augmented_count)
        print("Total train :", total)

    # ======================================
    # 3. CALCULER LES CLASS WEIGHTS
    # ======================================

    total_images = sum(train_counts.values())
    number_classes = len(CLASSES)

    if total_images == 0:
        raise ValueError("Aucune image trouvée.")

    class_weights = {}

    for class_name, count in train_counts.items():

        if count == 0:
            raise ValueError(
                f"La classe {class_name} est vide."
            )

        weight = total_images / (
            number_classes * count
        )

        class_weights[class_name] = round(weight, 4)

    # ======================================
    # 4. AFFICHER LES RESULTATS
    # ======================================

    print("\n========== CLASS WEIGHTS ==========")

    for class_name, weight in class_weights.items():

        print(f"{class_name:15} : {weight}")

    print("\nTotal images train :", total_images)

    # ======================================
    # 5. SAUVEGARDER LES RESULTATS
    # ======================================

    output = {
        "classes": CLASSES,
        "train_counts": train_counts,
        "class_weights": class_weights,
    }

    output_path = Path("dataset/class_weights.json")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nFichier créé :", output_path.resolve())


if __name__ == "__main__":
    main()
