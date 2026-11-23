
import time
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt

from predict_v3 import predict_v3, CLASSES

DOSSIER = Path(__file__).resolve().parent
DOSSIER_TEST = DOSSIER / "donnees_test"

y_true = []
y_pred = []
temps = []

extensions = {".jpg", ".jpeg", ".png"}

for classe in CLASSES:
    dossier_classe = DOSSIER_TEST / classe

    images = [
        p for p in dossier_classe.iterdir()
        if p.suffix.lower() in extensions
    ]

    print(f"\nEvaluation de {classe} : {len(images)} images")

    for image_path in images:
        debut = time.perf_counter()

        resultat = predict_v3(image_path)

        fin = time.perf_counter()

        y_true.append(classe)
        y_pred.append(resultat["type"])
        temps.append((fin - debut) * 1000)

print("\n===== RESULTATS V3 =====")

print("\nRapport de classification :")
print(classification_report(
    y_true,
    y_pred,
    labels=CLASSES,
    zero_division=0
))

print("Temps moyen par image :", round(np.mean(temps), 2), "ms")

matrice = confusion_matrix(
    y_true,
    y_pred,
    labels=CLASSES
)

affichage = ConfusionMatrixDisplay(
    confusion_matrix=matrice,
    display_labels=CLASSES
)

affichage.plot(xticks_rotation=45)
plt.title("Matrice de confusion - V3")
plt.tight_layout()
plt.show()
