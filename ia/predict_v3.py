
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image


# 1. Chemin du dossier IA
DOSSIER = Path(__file__).resolve().parent

# 2. Chargement des classes
with open(DOSSIER / "modele" / "classes_v3.json", encoding="utf-8") as f:
    CLASSES = json.load(f)

# 3. Chargement du modèle une seule fois
MODELE = tf.keras.models.load_model(
    DOSSIER / "modele" / "modele_v3.keras",
    compile=False
)


def predict_v3(image_path):
    """
    Prédit la catégorie d'une image avec le modèle V3.
    """

    # Préparer l'image
    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))

    # Convertir en tableau NumPy
    x = np.array(image, dtype=np.float32)

    # Ajouter la dimension batch
    x = np.expand_dims(x, axis=0)

    # Prédiction
    probabilites = MODELE.predict(x, verbose=0)[0]

    # Trouver la classe ayant la probabilité maximale
    index = int(np.argmax(probabilites))

    classe = CLASSES[index]
    confiance = float(probabilites[index])

    return {
        "type": classe,
        "confiance": round(confiance, 4)
    }
if __name__ == "__main__":
    image_test = DOSSIER / "donnees_test" / "tapis_vide" / "tapis_vide_000000.jpg"

    resultat = predict_v3(image_test)
    print(resultat)