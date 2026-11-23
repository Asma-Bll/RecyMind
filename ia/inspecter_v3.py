
import json
from pathlib import Path
import tensorflow as tf

DOSSIER = Path(__file__).resolve().parent

model_path = DOSSIER / "modele" / "modele_v3.keras"
classes_path = DOSSIER / "modele" / "classes_v3.json"

model = tf.keras.models.load_model(
    model_path,
    compile=False
)

with open(classes_path, encoding="utf-8") as f:
    classes = json.load(f)

print("INPUT :", model.input_shape)
print("OUTPUT :", model.output_shape)
print("CLASSES :", classes)

print("\nCOUCHES DE PREPROCESSING :")

for layer in model.layers:
    if any(word in layer.name.lower()
           for word in ["rescaling", "normalization", "mobilenet", "efficientnet"]):
        print(layer.name, layer.__class__.__name__)

print("\nNOMBRE DE COUCHES :", len(model.layers))

print("\nDETAILS DU MODELE MOBILE NET :")

for layer in model.layers:
    if isinstance(layer, tf.keras.Model):
        for sublayer in layer.layers:
            if "rescaling" in sublayer.name.lower():
                print(
                    "Couche :", sublayer.name,
                    "| Type :", sublayer.__class__.__name__,
                    "| Config :", sublayer.get_config()
                )

