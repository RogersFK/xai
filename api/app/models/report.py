from sqlalchemy import (
    JSON, Column, Integer, String, DateTime, ForeignKey, Float, Text
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Report(Base):
    """
    Forensic Incident Report generated from an Analysis.
    Mirrors what the ReportsPage UI displays.
 
    status          : 'draft' | 'signed' | 'archived'
    hash_sha256     : SHA-256 of the report PDF/content for integrity.
    chain_of_custody: Free-text or structured JSON audit trail.
    clearance_level : 1–5 (maps to the 'Security Clearance Level N' badge).
    """
    __tablename__ = "reports"
 
    id                = Column(Integer, primary_key=True, index=True)
    analysis_id       = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    created_by        = Column(Integer, ForeignKey("users.id"),    nullable=False)
 
    title             = Column(String(256), nullable=False)
    case_number       = Column(String(64),  unique=True, nullable=False)  # "F-089-ALPHA-Z"
    status            = Column(String(16),  default="draft")
    hash_sha256       = Column(String(64),  default="")
    chain_of_custody  = Column(Text,        default="")
    clearance_level   = Column(Integer,     default=3)
 
    generated_at      = Column(DateTime, default=datetime.utcnow)
    signed_at         = Column(DateTime, nullable=True)
 
    analysis = relationship("Analysis", back_populates="reports")
    creator  = relationship("User",     foreign_keys=[created_by])