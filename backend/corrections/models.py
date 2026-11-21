import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import backref, relationship

from auth.models import Utilisateur  # noqa: F401
from database import Base
from tris.models import Tri


class Correction(Base):
    """Une seule correction par tri : tri_id est unique (relation un-a-un, contrat section 9.3)."""
    __tablename__ = "corrections"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tri_id = Column(Uuid(as_uuid=True), ForeignKey("tris.id"), unique=True, nullable=False)
    type_corrige = Column(String, nullable=False)
    date_correction = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    utilisateur_id = Column(Uuid(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False)

    tri = relationship(Tri, backref=backref("correction", uselist=False))
