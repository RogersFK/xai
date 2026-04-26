from sqlalchemy import (
    JSON, Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"
 
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = system
    action        = Column(String(128), nullable=False, index=True)
    resource_type = Column(String(64),  default="")
    resource_id   = Column(Integer,     nullable=True)
    payload       = Column(JSON,        nullable=True)
    ip_address    = Column(String(64),  default="")
    created_at    = Column(DateTime, default=datetime.utcnow, index=True)
 
    user = relationship("User", back_populates="audit_logs")