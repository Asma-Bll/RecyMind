# Notes du modèle v1

À compléter après l'exécution du notebook `entrainement_v1.ipynb`.

|| Élément | Valeur |
| --- | --- |
| Accuracy de validation (dataset seul) | 0.9058 (90.58 %) |
| Nombre de classes du dataset | 10 |
| Classes, dans l'ordre | battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoes, trash |
| Taille d'entrée | 224 x 224, pixels entre 0 et 255 |
| Modèle | MobileNetV3Small, base gelée, 8 époques, Adam 1e-3 |
| Fichiers | `modele_v1.keras` et `classes_v1.json` (sur Drive, pas sur GitHub) |