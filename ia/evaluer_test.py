import time
from pathlib import Path

from predict import predict, FINALES
from evaluate import evaluer

TEST = Path("ia/donnees_test")
CLASSES = FINALES + ["tapis_vide"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

y_true, y_pred, temps = [], [], []

for classe in CLASSES:
    images = [p for p in (TEST / classe).iterdir() if p.suffix.lower() in EXTENSIONS]
    for p in images:
        debut = time.perf_counter()
        resultat = predict(p)
        temps.append(time.perf_counter() - debut)
        y_true.append(classe)
        y_pred.append(resultat["type"])
    print(f"{classe}: {len(images)} images")

print(f"\nTotal : {len(y_true)} images")
print(f"Temps moyen par image : {sum(temps) / len(temps) * 1000:.0f} ms\n")
evaluer(y_true, y_pred, CLASSES)