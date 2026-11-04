
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import random

# ==========================================
# 1. CONFIGURATION
# ==========================================

# Images originales : uniquement celles de train
SOURCE_DIR = Path("dataset/processed/train/tapis_vide")

# Destination des images augmentées
OUTPUT_DIR = Path("dataset/augmented/train/tapis_vide")

# Nombre de nouvelles images par image originale
AUGMENTATIONS_PER_IMAGE = 8

# Pour obtenir des résultats reproductibles
RANDOM_SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


# ==========================================
# 2. AUGMENTATION D'UNE IMAGE
# ==========================================

def augment_image(image, rng):
    """
    Applique des transformations légères et réalistes
    à une image de tapis roulant vide.
    """

    # Rotation légère : entre -4 et +4 degrés
    angle = rng.uniform(-4, 4)

    image = image.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=False
    )

    # Variation de luminosité
    brightness = rng.uniform(0.80, 1.20)

    image = ImageEnhance.Brightness(image).enhance(
        brightness
    )

    # Variation du contraste
    contrast = rng.uniform(0.85, 1.15)

    image = ImageEnhance.Contrast(image).enhance(
        contrast
    )

    # Variation légère des couleurs
    color = rng.uniform(0.90, 1.10)

    image = ImageEnhance.Color(image).enhance(
        color
    )

    # Flou léger sur certaines images
    if rng.random() < 0.30:
        radius = rng.uniform(0.2, 0.5)

        image = image.filter(
            ImageFilter.GaussianBlur(radius=radius)
        )

    return image


# ==========================================
# 3. PROGRAMME PRINCIPAL
# ==========================================

def main():

    # Vérifier le dossier source
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Dossier introuvable : {SOURCE_DIR.resolve()}"
        )

    # Eviter de mélanger plusieurs exécutions
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise FileExistsError(
            f"Le dossier {OUTPUT_DIR} contient déjà des fichiers. "
            "Videz-le ou renommez-le avant de relancer."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Récupérer les images originales
    images = sorted([
        file for file in SOURCE_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not images:
        raise ValueError(
            "Aucune image trouvée dans le dossier train/tapis_vide."
        )

    print("========== DATA AUGMENTATION ==========")
    print("Classe : tapis_vide")
    print("Images originales :", len(images))
    print(
        "Augmentations par image :",
        AUGMENTATIONS_PER_IMAGE
    )

    total_augmented = 0
    invalid_images = []

    for image_index, image_path in enumerate(images):

        try:
            with Image.open(image_path) as img:
                original = img.convert("RGB")

            for aug_index in range(AUGMENTATIONS_PER_IMAGE):

                # Générateur aléatoire propre à chaque variation
                rng = random.Random(
                    RANDOM_SEED
                    + image_index * 100
                    + aug_index
                )

                augmented = augment_image(
                    original.copy(),
                    rng
                )

                output_name = (
                    f"{image_path.stem}_aug_{aug_index + 1}.jpg"
                )

                output_path = OUTPUT_DIR / output_name

                augmented.save(
                    output_path,
                    format="JPEG",
                    quality=95
                )

                total_augmented += 1

        except Exception as error:
            invalid_images.append(image_path.name)
            print(
                f"Erreur avec {image_path.name} : {error}"
            )

    # ======================================
    # 4. AFFICHER LES RESULTATS
    # ======================================

    print("\n========== RESULTAT ==========")
    print("Images originales valides :", len(images) - len(invalid_images))
    print("Images augmentées :", total_augmented)
    print(
        "Total train disponible :",
        (len(images) - len(invalid_images)) + total_augmented
    )

    print("Images invalides :", len(invalid_images))

    if invalid_images:
        print("Fichiers concernés :", invalid_images)

    print("\nDossier de sortie :", OUTPUT_DIR.resolve())
    print("\nAugmentation terminée !")


if __name__ == "__main__":
    main()
