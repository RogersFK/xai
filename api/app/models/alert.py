from sqlalchemy import (
    JSON, Column, Integer, String, DateTime, ForeignKey, Float, Text
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Alert(Base):
    """
    Actionable security alert derived from an Analysis or ThreatEvent.
 
    level   : 'critical' | 'high' | 'medium' | 'low'  (maps to StatCard badge)
    status  : 'open' | 'acknowledged' | 'resolved' | 'suppressed'
    """
    __tablename__ = "alerts"
 
    id              = Column(Integer, primary_key=True, index=True)
    analysis_id     = Column(Integer, ForeignKey("analyses.id"),      nullable=False)
    threat_event_id = Column(Integer, ForeignKey("threat_events.id"), nullable=True)
    assigned_to_id  = Column(Integer, ForeignKey("users.id"),         nullable=True)
 
    level           = Column(String(16), nullable=False, default="medium")
    title           = Column(String(256), nullable=False)
    description     = Column(Text, default="")
    status          = Column(String(32), default="open")
 
    triggered_at    = Column(DateTime, default=datetime.utcnow)
    resolved_at     = Column(DateTime, nullable=True)
 
    analysis     = relationship("Analysis",    back_populates="alerts")
    threat_event = relationship("ThreatEvent", back_populates="alerts")
    assigned_to  = relationship("User",        back_populates="alerts",
                                foreign_keys=[assigned_to_id])
    