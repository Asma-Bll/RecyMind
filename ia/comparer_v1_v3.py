
import json
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report

DOSSIER = Path(__file__).resolve().parent
DOSSIER_MODELES = DOSSIER / "modele"
DOSSIER_TEST = DOSSIER / "donnees_test"

# Les six catégories communes
CLASSES_FINALES = [
    "autre",
    "metal",
    "papier_carton",
    "plastique",
    "textile",
    "verre"
]

# Correspondance des classes originales de V1
REGROUPEMENT = {
    "plastic": "plastique",
    "paper": "papier_carton",
    "cardboard": "papier_carton",
    "glass": "verre",
    "metal": "metal",
    "clothes": "textile",
    "shoes": "autre",
    "biological": "autre",
    "battery": "autre",
    "trash": "autre"
}

# Charger les modèles
model_v1 = tf.keras.models.load_model(
    DOSSIER_MODELES / "modele_v1.keras",
    compile=False
)

model_v3 = tf.keras.models.load_model(
    DOSSIER_MODELES / "modele_v3.keras",
    compile=False
)

# Charger les classes
with open(DOSSIER / "classes_v1.json", encoding="utf-8") as f:
    classes_v1 = json.load(f)

with open(DOSSIER_MODELES / "classes_v3.json", encoding="utf-8") as f:
    classes_v3 = json.load(f)


def preparer_image(path):
    image = Image.open(path).convert("RGB")
    image = image.resize((224, 224))
    x = np.array(image, dtype=np.float32)
    return np.expand_dims(x, axis=0)


def predire_v1(x):
    probas = model_v1(x, training=False).numpy()[0]

    sommes = {c: 0.0 for c in CLASSES_FINALES}

    for classe, proba in zip(classes_v1, probas):
        sommes[REGROUPEMENT[classe]] += float(proba)

    return max(sommes, key=sommes.get)


def predire_v3(x):
    probas = model_v3(x, training=False).numpy()[0]

    # V3 possède une sortie tapis_vide.
    # Pour cette comparaison, on compare seulement les 6 classes communes.
    sommes = {
        c: float(probas[classes_v3.index(c)])
        for c in CLASSES_FINALES
    }

    return max(sommes, key=sommes.get)


y_true = []
predictions_v1 = []
predictions_v3 = []

for classe in CLASSES_FINALES:
    dossier = DOSSIER_TEST / classe

    images = [
        p for p in dossier.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]

    print(f"{classe}: {len(images)} images")

    for path in images:
        x = preparer_image(path)

        predictions_v1.append(predire_v1(x))
        predictions_v3.append(predire_v3(x))
        y_true.append(classe)


print("\n===== COMPARAISON SUR LES 6 CLASSES =====")

print("\nV1")
print("Accuracy :", round(accuracy_score(y_true, predictions_v1), 4))
print(classification_report(
    y_true, predictions_v1,
    labels=CLASSES_FINALES,
    zero_division=0
))

print("\nV3")
print("Accuracy :", round(accuracy_score(y_true, predictions_v3), 4))
print(classification_report(
    y_true, predictions_v3,
    labels=CLASSES_FINALES,
    zero_division=0
))

