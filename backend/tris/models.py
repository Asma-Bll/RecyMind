"""MODELE PROVISOIRE de la table tris (contrat v1.2, section 9.2).

Cette table appartient a Personne 1. Si elle existe deja dans le depot,
SUPPRIMEZ ce fichier et corrigez seulement l'import `from tris.models import Tri`
(dans corrections/models.py, routes/corrections.py et tests/test_correction.py).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Uuid

from database import Base


class Tri(Base):
    __tablename__ = "tris"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    image_url = Column(String, nullable=False)
    type = Column(String, nullable=False)        # prediction initiale de l'IA
    confiance = Column(Float, nullable=False)
    bac = Column(String, nullable=True)          # null si controle manuel
    statut = Column(String, nullable=False)      # trie ou controle_manuel
