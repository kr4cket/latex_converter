import enum
from datetime import datetime
from app.infra.database.models.base import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum, Index


class StatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Conversions(Base):
    __tablename__ = 'conversions'

    id           = Column(Integer, primary_key=True, index=True)
    file_id      = Column(String, unique=True, index=True)
    file_name    = Column(String, index=True)
    status       = Column(Enum(StatusEnum), default=StatusEnum.pending)
    created_at   = Column(DateTime, default=datetime.utcnow)
    started_at   = Column(DateTime, nullable=True)
    ended_at     = Column(DateTime, nullable=True)
    download_url = Column(String, nullable=True)
    error        = Column(String, nullable=True)
