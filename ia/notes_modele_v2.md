# Notes du modèle v2 (Personne 2) – à livrer à Personne 3

À compléter après l'exécution de `entrainement_v2_finetuning.ipynb`.

## Comparaison
| Modèle | Accuracy validation | Accuracy photos de l'équipe | Temps par image (ms) |
| --- | --- | --- | --- |
| MobileNetV3Small | à compléter | à compléter | à compléter |
| EfficientNetB0 | à compléter | à compléter | à compléter |

**Modèle retenu :** à compléter (choisi sur l'accuracy des photos de l'équipe).

## Informations pour `predict(image)` (Personne 3)
- Fichier : `modele_v2_<nom>.keras` + `classes_v2.json` (dossier Drive partagé `modeles/`).
- Taille d'entrée : 224 x 224, RGB, pixels entre 0 et 255 (pas de division par 255).
- Sortie : 7 probabilités (softmax), dans l'ordre de `classes_v2.json` (ordre alphabétique des dossiers).
- Confiance = la probabilité maximale ; classe = son indice dans `classes_v2.json`.
- Seuil de confiance du contrat : 0.40 (appliqué par le backend, pas par le modèle).
- Le modèle n'est PAS sur GitHub (trop lourd) : il est sur le Drive partagé.
