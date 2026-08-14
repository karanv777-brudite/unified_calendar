from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
import enum

class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class EventInvite(Base):
    __tablename__ = "event_invites"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    event_id = Column(String, nullable=False, index=True)  # Unified event ID or original ID
    invited_email = Column(String, nullable=False, index=True)  # Guest's email address
    status = Column(String, default=InviteStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)