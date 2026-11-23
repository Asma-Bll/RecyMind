import asyncio
import random
import sys
import uuid
from datetime import datetime
from pathlib import Path

import stockage
from routes.ws import diffuser

# Pour pouvoir importer ia/predict.py depuis le backend
RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "ia"))

IMAGES = Path(__file__).resolve().parent / "images"
SEUIL = 0.40
BACS = {"plastique": "bac_1", "papier_carton": "bac_2", "verre": "bac_3",
        "metal": "bac_4", "textile": "bac_5", "autre": "bac_6"}

_etat = "arretee"
_tache = None


def etat():
    return {"etat": _etat}


def decider(resultat):
    """Règle du contrat : confiance < 0.40 -> contrôle manuel (bac = null)."""
    if resultat["confiance"] < SEUIL:
        return None, "controle_manuel"
    return BACS[resultat["type"]], "trie"


async def _boucle(cadence):
    global _etat
    attente = 60 / cadence
    try:
        from predict import predict   # charge TensorFlow au premier lancement
        while True:
            images = list(IMAGES.glob("*.jpg"))
            if not images:
                print("SIMULATION : aucune image dans backend/images, arrêt.")
                break
            image = random.choice(images)
            resultat = await asyncio.to_thread(predict, image)

            # Tapis vide : aucune action, aucun enregistrement
            if resultat["type"] != "tapis_vide":
                bac, statut = decider(resultat)
                tri = {
                    "id": str(uuid.uuid4()),
                    "date": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "image_url": f"/images/{image.name}",
                    "type": resultat["type"],
                    "confiance": resultat["confiance"],
                    "bac": bac,
                    "statut": statut,
                    "correction": None,
                }
                # À l'intégration : remplacer cette ligne par l'enregistrement en base
                stockage.ajouter_tri(tri)
                await diffuser({"event": "nouveau_tri", "data": tri})

            await asyncio.sleep(attente)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        # Mode dégradé : en cas d'erreur, la simulation s'arrête proprement
        print("SIMULATION : erreur, arrêt.", repr(e))
    finally:
        if _tache is asyncio.current_task():
            _etat = "arretee"


def demarrer(cadence):
    global _etat, _tache
    if _etat == "en_cours":                  # pas de deuxième simulation
        return {"etat": "en_cours", "message": "Simulation déjà en cours."}
    _etat = "en_cours"
    _tache = asyncio.create_task(_boucle(cadence))
    return {"etat": "en_cours", "message": "Simulation démarrée."}


def arreter():
    global _etat
    if _tache is not None and not _tache.done():
        _tache.cancel()
    _etat = "arretee"
    return {"etat": "arretee", "message": "Simulation arrêtée."}