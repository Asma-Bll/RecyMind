import json
import numpy as np
from PIL import Image
import keras

from predict import regrouper

model = keras.models.load_model("ia/modele/modele_v1.keras")
classes = json.load(open("ia/classes_v1.json"))

img = Image.open("backend/images/dechet_001.jpg").convert("RGB").resize((224, 224))
x = np.array(img, dtype="float32")[None, ...]   # pixels 0-255, SANS diviser par 255
probas = model.predict(x)[0]

print("Probabilités du modèle (10 classes) :")
for c, p in zip(classes, probas):
    print(f"  {c:12} {p:.3f}")
print("Après regroupement :", regrouper(probas, classes))