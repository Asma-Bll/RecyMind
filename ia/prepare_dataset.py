
from pathlib import Path
from PIL import Image
import random
import shutil

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

# Dataset Kaggle déjà extrait
SOURCE_KAGGLE = Path(
    r"C:\Users\assma\Downloads\Mini-projet en Intelligence Artificielle\archive\original"
)

# Images de tapis vide téléchargées depuis Internet
SOURCE_TAPIS = Path("dataset/raw/tapis_vide")

# Destination du dataset organisé
OUTPUT_DIR = Path("dataset/processed")

# Pour obtenir toujours la même répartition
RANDOM_SEED = 42

# Répartition souhaitée
TRAIN_RATIO = 0.70
TEST_RATIO = 0.20
VALIDATION_RATIO = 0.10

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}

# Regroupement des classes Kaggle
CLASS_MAPPING = {
    "plastic": "plastique",
    "paper": "papier_carton",
    "cardboard": "papier_carton",
    "glass": "verre",
    "metal": "metal",
    "clothes": "textile",
    "shoes": "autre",
    "biological": "autre",
    "battery": "autre",
    "trash": "autre",
}

FINAL_CLASSES = [
    "plastique",
    "papier_carton",
    "verre",
    "metal",
    "textile",
    "autre",
    "tapis_vide",
]

SPLITS = ["train", "test", "validation"]


# --------------------------------------------------
# 2. VERIFIER LES IMAGES
# --------------------------------------------------

def is_valid_image(image_path):
    """Vérifie qu'une image peut être ouverte."""
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def get_images(folder):
    """Récupère les images valides d'un dossier."""
    if not folder.exists():
        return []

    images = []

    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            if is_valid_image(path):
                images.append(path)

    return images


# --------------------------------------------------
# 3. REGROUPER LES IMAGES PAR CLASSE
# --------------------------------------------------

def collect_images():
    grouped_images = {
        class_name: [] for class_name in FINAL_CLASSES
    }

    print("\n===== REGROUPEMENT DES CLASSES =====")

    for kaggle_class, final_class in CLASS_MAPPING.items():

        source_folder = SOURCE_KAGGLE / kaggle_class

        if not source_folder.exists():
            raise FileNotFoundError(
                f"Dossier introuvable : {source_folder}"
            )

        images = get_images(source_folder)

        grouped_images[final_class].extend(images)

        print(
            f"{kaggle_class:12} -> {final_class:15} : "
            f"{len(images)} images"
        )

    # Ajouter les images de tapis vide
    tapis_images = get_images(SOURCE_TAPIS)

    if not tapis_images:
        raise ValueError(
            "Aucune image valide trouvée dans "
            f"{SOURCE_TAPIS.resolve()}"
        )

    grouped_images["tapis_vide"] = tapis_images

    print(
        f"{'Internet':12} -> {'tapis_vide':15} : "
        f"{len(tapis_images)} images"
    )

    return grouped_images


# --------------------------------------------------
# 4. DIVISER LES IMAGES
# --------------------------------------------------

def split_images(images):
    images = images.copy()
    random.shuffle(images)

    total = len(images)

    train_count = int(total * TRAIN_RATIO)
    test_count = int(total * TEST_RATIO)

    # Le reste va dans validation
    validation_count = total - train_count - test_count

    train_images = images[:train_count]

    test_images = images[
        train_count:train_count + test_count
    ]

    validation_images = images[
        train_count + test_count:
    ]

    return {
        "train": train_images,
        "test": test_images,
        "validation": validation_images,
    }


# --------------------------------------------------
# 5. COPIER LES IMAGES
# --------------------------------------------------

def copy_images(split_data, class_name):

    for split_name, images in split_data.items():

        destination_folder = (
            OUTPUT_DIR / split_name / class_name
        )

        destination_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        for index, source_path in enumerate(images):

            # Nom unique dans la classe de destination
            extension = source_path.suffix.lower()

            destination_path = (
                destination_folder /
                f"{class_name}_{index:06d}{extension}"
            )

            shutil.copy2(
                source_path,
                destination_path
            )


# --------------------------------------------------
# 6. PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():

    random.seed(RANDOM_SEED)

    if not SOURCE_KAGGLE.exists():
        raise FileNotFoundError(
            f"Dataset Kaggle introuvable : {SOURCE_KAGGLE}"
        )

    # Eviter de mélanger les résultats d'une ancienne exécution
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.rglob("*")):
        raise FileExistsError(
            f"Le dossier {OUTPUT_DIR} n'est pas vide. "
            "Déplace ou supprime son ancien contenu avant "
            "de relancer le script."
        )

    grouped_images = collect_images()

    print("\n===== SPLIT DU DATASET =====")

    for class_name in FINAL_CLASSES:

        images = grouped_images[class_name]

        if not images:
            raise ValueError(
                f"La classe {class_name} ne contient aucune image."
            )

        split_data = split_images(images)

        copy_images(split_data, class_name)

        print(f"\nClasse : {class_name}")
        print(f"Total : {len(images)}")
        print(f"Train : {len(split_data['train'])}")
        print(f"Test : {len(split_data['test'])}")
        print(
            f"Validation : {len(split_data['validation'])}"
        )

    print("\n===== TERMINÉ =====")
    print("Dataset créé dans :", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
