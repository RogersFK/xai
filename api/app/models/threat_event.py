from sqlalchemy import (
    JSON, Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db.base import Base

class ThreatEvent(Base):
    """
    Individual suspicious event extracted from an Analysis.
    Each event corresponds to one row in the Live Forensic Feed.
 
    event_type examples: 'Elevated Privileges', 'SSH Brute Force',
                         'File Decryption', 'Database Dump',
                         'Lateral Movement', 'C2 Beaconing'
    severity   : 'critical' | 'high' | 'medium' | 'low'
    status     : 'open' | 'investigating' | 'resolved' | 'false_positive'
    """
    __tablename__ = "threat_events"
 
    id          = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
 
    event_type  = Column(String(128), nullable=False)
    source_ip   = Column(String(64),  default="")
    dest_ip     = Column(String(64),  default="")
    username    = Column(String(128), default="")
    action      = Column(String(256), default="")
    severity    = Column(String(16),  default="medium")
    status      = Column(String(32),  default="open")
 
    # Full raw log entry that triggered this event (for forensic drill-down)
    raw_entry   = Column(JSON, nullable=True)
 
    occurred_at = Column(DateTime, nullable=True)   # timestamp from the log itself
 
    analysis     = relationship("Analysis",    back_populates="threat_events")
    explanations = relationship("Explanation", back_populates="threat_event",
                                cascade="all, delete-orphan")
    alerts       = relationship("Alert",       back_populates="threat_event")