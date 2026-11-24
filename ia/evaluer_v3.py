
import json
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# --------------------------------------------------
# 1. CHEMINS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "ia" / "modeles_v3" / "modele_v3.keras"
CLASSES_PATH = ROOT / "ia" / "modeles_v3" / "classes_v3.json"
THRESHOLD_PATH = ROOT / "ia" / "modeles_v3" / "seuil_v3.json"
TEST_DIR = ROOT / "dataset" / "processed" / "test"

IMAGE_SIZE = (224, 224)

# --------------------------------------------------
# 2. CHARGER LE MODELE ET LES CONFIGURATIONS
# --------------------------------------------------

print("Chargement du modele V3...")

with open(CLASSES_PATH, encoding="utf-8") as f:
    classes = json.load(f)

with open(THRESHOLD_PATH, encoding="utf-8") as f:
    config = json.load(f)

threshold = float(config["seuil"])

model = tf.keras.models.load_model(
    str(MODEL_PATH),
    compile=False
)

print("Modele charge avec succes !")
print("Classes :", classes)
print("Seuil :", threshold)

# --------------------------------------------------
# 3. PREPARER LES IMAGES ET LES PREDICTIONS
# --------------------------------------------------

y_true = []
y_pred = []
confidences = []

total = 0
manual_review = 0
automatic = 0
automatic_correct = 0

start = time.time()

for vraie_classe in classes:

    dossier = TEST_DIR / vraie_classe

    if not dossier.exists():
        print("Dossier manquant :", dossier)
        continue

    images = [
        p for p in dossier.iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    ]

    print(f"\nClasse {vraie_classe} : {len(images)} images")

    for image_path in images:

        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                img = img.resize(
                    IMAGE_SIZE,
                    Image.Resampling.BILINEAR
                )
                tableau = np.asarray(img, dtype=np.float32)

            entree = np.expand_dims(tableau, axis=0)

            probabilites = model.predict(
                entree,
                verbose=0
            )[0]

            index = int(np.argmax(probabilites))
            prediction = classes[index]
            confiance = float(probabilites[index])

            y_true.append(vraie_classe)
            y_pred.append(prediction)
            confidences.append(confiance)

            total += 1

            # Simuler la decision de l'API
            if prediction == "tapis_vide" or confiance < threshold:
                manual_review += 1
            else:
                automatic += 1

                if prediction == vraie_classe:
                    automatic_correct += 1

        except (UnidentifiedImageError, OSError) as e:
            print("Image ignoree :", image_path, e)

# --------------------------------------------------
# 4. CALCUL DES METRIQUES
# --------------------------------------------------

if total == 0:
    raise RuntimeError("Aucune image de test valide trouvee.")

accuracy = accuracy_score(y_true, y_pred)

elapsed = time.time() - start

print("\n" + "=" * 55)
print("              RESULTATS RECYMIND V3")
print("=" * 55)

print(f"\nNombre total d'images testees : {total}")
print(f"Accuracy globale : {accuracy * 100:.2f} %")

print("\n--- Classification Report ---")
print(
    classification_report(
        y_true,
        y_pred,
        labels=classes,
        target_names=classes,
        zero_division=0
    )
)

print("\n--- Matrice de confusion ---")
print("Ordre des classes :", classes)
print(confusion_matrix(y_true, y_pred, labels=classes))

# --------------------------------------------------
# 5. EVALUATION DU TRI AUTOMATIQUE
# --------------------------------------------------

print("\n--- Decision du systeme ---")

print(f"Tri automatique : {automatic}")
print(f"Controle manuel : {manual_review}")

print(
    f"Taux de controle manuel : "
    f"{manual_review / total * 100:.2f} %"
)

if automatic > 0:
    print(
        f"Accuracy des tris automatiques : "
        f"{automatic_correct / automatic * 100:.2f} %"
    )

print(f"\nTemps total : {elapsed:.2f} secondes")
print("=" * 55)
