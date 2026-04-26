
from datetime import datetime
from sqlalchemy import JSON, Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Analysis(Base):
    """
    One AI analysis run against a LogFile.
 
    severity    : 'critical' | 'high' | 'medium' | 'low' | 'none'
    status      : 'pending' | 'running' | 'completed' | 'failed'
    threat_score: 0.0–1.0 float returned by the model
    shap_data   : global SHAP summary {feature: mean_abs_shap, ...}
    events      : raw structured events extracted from the log (list of dicts)
    """
    __tablename__ = "analyses"
 
    id               = Column(Integer, primary_key=True, index=True)
    log_file_id      = Column(Integer, ForeignKey("log_files.id"),      nullable=False)
    user_id          = Column(Integer, ForeignKey("users.id"),          nullable=False)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=True)
 
    # Input
    user_prompt  = Column(Text,    default="")
 
    # AI output
    summary      = Column(Text,    default="")
    anomalies    = Column(Text,    default="[]")    # JSON list of anomaly descriptions
    patterns     = Column(Text,    default="[]")    # JSON list of detected patterns
    severity     = Column(String(16), default="unknown")
    threat_score = Column(Float,   nullable=False, default=0.0)
    ai_model     = Column(String(64), default="")
 
    # Explainability (global, per-analysis)
    shap_data    = Column(JSON, nullable=True)      # {feature_name: mean_abs_shap_value}
 
    # Raw structured events extracted from the log
    events       = Column(JSON, nullable=True)      # list[dict]
 
    # Execution metadata
    tokens_used  = Column(Integer, default=0)
    duration_sec = Column(Float,   default=0.0)
    status       = Column(String(16), default="pending")
    error_msg    = Column(Text,    default="")
    raw_response = Column(Text,    default="")
 
    created_at   = Column(DateTime, default=datetime.utcnow)
 
    # relationships
    log_file      = relationship("LogFile",      back_populates="analyses")
    user          = relationship("User",         back_populates="analyses")
    model_version = relationship("ModelVersion", back_populates="analyses")
    threat_events = relationship("ThreatEvent",  back_populates="analysis",
                                 cascade="all, delete-orphan")
    explanations  = relationship("Explanation",  back_populates="analysis",
                                 cascade="all, delete-orphan")
    reports       = relationship("Report",       back_populates="analysis")
    alerts        = relationship("Alert",        back_populates="analysis",
                                 cascade="all, delete-orphan")
 

