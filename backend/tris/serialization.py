"""Transforme un Tri en dictionnaire conforme au contrat (section 5). A reutiliser dans GET /tris et GET /tris/{id}."""
from datetime import timezone


def iso(d):
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.isoformat()


def tri_to_dict(tri) -> dict:
    c = tri.correction
    return {
        "id": str(tri.id),
        "date": iso(tri.date),
        "image_url": tri.image_url,
        "type": tri.type,
        "confiance": tri.confiance,
        "bac": tri.bac,
        "statut": tri.statut,
        "correction": None if c is None else {
            "type_corrige": c.type_corrige,
            "date_correction": iso(c.date_correction),
        },
    }
