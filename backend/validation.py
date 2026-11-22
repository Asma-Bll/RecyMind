from datetime import datetime
from fastapi import HTTPException


def nettoyer_date(valeur, nom):
    """Vérifie qu'une date est au format ISO 8601. Renvoie la date nettoyée."""
    if valeur is None:
        return None
    valeur = valeur.replace(" ", "+")   # dans une URL, le "+" du fuseau devient un espace
    try:
        datetime.fromisoformat(valeur)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{nom} invalide : format ISO 8601 attendu")
    return valeur