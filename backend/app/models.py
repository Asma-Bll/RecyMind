
import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Double,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nom = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    mot_de_passe_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default="operator")
    date_creation = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    corrections = relationship("Correction", back_populates="utilisateur")


class Tri(Base):
    __tablename__ = "tris"
    __table_args__ = (
        CheckConstraint(
            "type IN ('plastique', 'papier_carton', 'verre', "
            "'metal', 'textile', 'autre')",
            name="ck_tris_type",
        ),
        CheckConstraint(
            "confiance >= 0 AND confiance <= 1",
            name="ck_tris_confiance",
        ),
        CheckConstraint(
            "(statut = 'controle_manuel' AND bac IS NULL) OR "
            "(statut = 'trie' AND bac IS NOT NULL)",
            name="ck_tris_bac_statut",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    image_url = Column(Text, nullable=False)
    type = Column(String(30), nullable=False)
    confiance = Column(Double, nullable=False)
    bac = Column(String(20), nullable=True)
    statut = Column(String(30), nullable=False)

    correction = relationship(
        "Correction",
        back_populates="tri",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Correction(Base):
    __tablename__ = "corrections"
    __table_args__ = (
        UniqueConstraint("tri_id", name="uq_corrections_tri_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tri_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tris.id", ondelete="CASCADE"),
        nullable=False,
    )
    utilisateur_id = Column(
        UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )
    type_corrige = Column(String(30), nullable=False)
    date_correction = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    tri = relationship("Tri", back_populates="correction")
    utilisateur = relationship("Utilisateur", back_populates="corrections")
