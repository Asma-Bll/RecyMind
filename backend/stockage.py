from datetime import datetime, timedelta

# Stockage provisoire : liste en mémoire (se vide à chaque redémarrage).
# Sera remplacé par PostgreSQL à l'intégration.
_TRIS = []


def _parse(s):
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.astimezone()
    return d


def ajouter_tri(tri):
    _TRIS.append(tri)
    return tri


def obtenir_tri(tri_id):
    for t in _TRIS:
        if t["id"] == tri_id:
            return t
    return None


def _filtrer(date_debut=None, date_fin=None, type=None, statut=None):
    debut = _parse(date_debut) if date_debut else None
    fin = _parse(date_fin) if date_fin else None
    if date_fin and len(date_fin) == 10:      # "2026-10-31" -> jusqu'à la fin du jour
        fin = fin + timedelta(days=1)
    resultats = []
    for t in _TRIS:
        d = _parse(t["date"])
        if debut and d < debut:
            continue
        if fin and d > fin:
            continue
        if type and t["type"] != type:
            continue
        if statut and t["statut"] != statut:
            continue
        resultats.append(t)
    resultats.sort(key=lambda t: _parse(t["date"]), reverse=True)  # plus récent d'abord
    return resultats


def lister_tris(date_debut=None, date_fin=None, type=None, statut=None, page=1, limit=20):
    tous = _filtrer(date_debut, date_fin, type, statut)
    debut = (page - 1) * limit
    return tous[debut:debut + limit], len(tous)


def stats(date_debut=None, date_fin=None):
    tris = _filtrer(date_debut, date_fin)
    total = len(tris)
    par_type = {c: 0 for c in ["plastique", "papier_carton", "verre", "metal", "textile", "autre"]}
    for t in tris:
        par_type[t["type"]] += 1
    controle = [t for t in tris if t["statut"] == "controle_manuel"]
    a_traiter = [t for t in controle if t["correction"] is None]

    # Débit : tris des 5 dernières minutes / 5 (indépendant de la période filtrée)
    limite = datetime.now().astimezone() - timedelta(minutes=5)
    recents = [t for t in _TRIS if _parse(t["date"]) >= limite]

    periode = None
    if date_debut or date_fin:
        periode = {"date_debut": date_debut, "date_fin": date_fin}
    return {
        "periode": periode,
        "total_tris": total,
        "par_type": par_type,
        "nombre_controle_manuel": len(controle),
        "nombre_a_traiter": len(a_traiter),
        "taux_incertitude": round(len(controle) / total, 2) if total else 0,
        "debit_objets_minute": round(len(recents) / 5, 1),
    }


if __name__ == "__main__":
    # Petit test rapide
    maintenant = datetime.now().astimezone().isoformat(timespec="seconds")
    for i, (typ, conf) in enumerate([("plastique", 0.9), ("metal", 0.3), ("verre", 0.7)]):
        ajouter_tri({
            "id": str(i), "date": maintenant, "image_url": "/images/dechet_001.jpg",
            "type": typ, "confiance": conf,
            "bac": None if conf < 0.4 else "bac_x",
            "statut": "controle_manuel" if conf < 0.4 else "trie",
            "correction": None,
        })
    print(stats())
    print(lister_tris(type="metal"))