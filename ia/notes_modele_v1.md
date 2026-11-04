# Notes du modèle v1 (Personne 2)

À compléter après l'exécution du notebook `entrainement_v1.ipynb`.

| Élément | Valeur |
| --- | --- |
| Accuracy de validation (dataset seul) | à compléter |
| Nombre de classes du dataset | à compléter |
| Classes, dans l'ordre | à compléter (copier `class_names`) |
| Taille d'entrée | 224 x 224, pixels entre 0 et 255 |
| Modèle | MobileNetV3Small, base gelée, 8 époques, Adam 1e-3 |
| Fichiers | `modele_v1.keras` et `classes_v1.json` (sur Drive, pas sur GitHub) |

L'accuracy est mesurée sur le dataset seul : c'est un point de départ, pas un résultat final.
Les 7 classes du contrat (`plastique, papier_carton, verre, metal, textile, autre, tapis_vide`) seront utilisées après le regroupement fait par Personne 1.
