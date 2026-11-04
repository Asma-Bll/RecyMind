import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Uuid

from database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # operator, admin ou simulateur
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
