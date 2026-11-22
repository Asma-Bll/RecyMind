import json
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image

DOSSIER = Path(__file__).resolve().parent

CLASSES = ["plastique", "papier_carton", "verre", "metal",
           "textile", "autre", "tapis_vide"]

# Regroupement des 10 classes du modèle vers nos 6 classes de déchets
REGROUPEMENT = {
    "plastic": "plastique",
    "paper": "papier_carton", "cardboard": "papier_carton",
    "glass": "verre",
    "metal": "metal",
    "clothes": "textile",
    "shoes": "autre", "biological": "autre", "battery": "autre", "trash": "autre",
}
FINALES = ["plastique", "papier_carton", "verre", "metal", "textile", "autre"]

_model = None
_classes = None


def _charger():
    """Charge le modèle une seule fois (au premier appel)."""
    global _model, _classes
    if _model is None:
        import keras
        _model = keras.models.load_model(DOSSIER / "modele" / "modele_v1.keras")
        with open(DOSSIER / "classes_v1.json") as f:
            _classes = json.load(f)
    return _model, _classes


def regrouper(probas, classes_modele):
    """Additionne les probabilités des classes qui vont ensemble.
    Renvoie la meilleure de nos classes, avec la somme comme confiance."""
    somme = {c: 0.0 for c in FINALES}
    for classe, p in zip(classes_modele, probas):
        somme[REGROUPEMENT[classe]] += float(p)
    meilleure = max(somme, key=somme.get)
    return {"type": meilleure, "confiance": round(somme[meilleure], 2)}


def predict(image_path):
    """Vrai modèle (v1). Renvoie {"type": ..., "confiance": ...}.
    Limite : ce modèle n'a pas de classe tapis_vide (prévue en v2)."""
    model, classes = _charger()
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    x = np.array(img, dtype="float32")[None, ...]   # pixels 0-255, SANS diviser par 255
    probas = model(x, training=False).numpy()[0]
    return regrouper(probas, classes)


def predict_faux(image_path):
    """Faux modèle au hasard, pour tester sans TensorFlow."""
    return {
        "type": random.choice(CLASSES),
        "confiance": round(random.uniform(0.2, 0.99), 2),
    }


if __name__ == "__main__":
    image = DOSSIER.parent / "backend" / "images" / "dechet_001.jpg"

    t = time.perf_counter()
    _charger()
    print(f"Chargement du modèle : {time.perf_counter() - t:.2f} s")

    t = time.perf_counter()
    print(predict(image))
    print(f"1re prédiction : {(time.perf_counter() - t) * 1000:.0f} ms")

    N = 20
    t = time.perf_counter()
    for _ in range(N):
        predict(image)
    print(f"Moyenne sur {N} prédictions : {(time.perf_counter() - t) / N * 1000:.0f} ms")