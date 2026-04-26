from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class ModelVersion(Base):
    """
    Versioned ML model record.  Tracks every trained model so results
    remain reproducible and auditable.
 
    model_type examples: 'random_forest', 'xgboost', 'isolation_forest',
                         'lstm', 'transformer'
    """
    __tablename__ = "model_versions"
 
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(128), nullable=False)
    version         = Column(String(32),  nullable=False)       # "1.3.0"
    model_type      = Column(String(64),  nullable=False)
    file_path       = Column(String,      nullable=False)       # saved model artifact
 
    # Training configuration
    hyperparameters = Column(JSON, nullable=True)               # {"n_estimators": 200, ...}
    feature_names   = Column(JSON, nullable=True)               # ordered list used at train time
 
    # Performance metrics (filled after evaluation)
    accuracy        = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall          = Column(Float, nullable=True)
    f1_score        = Column(Float, nullable=True)
    auc_roc         = Column(Float, nullable=True)
 
    is_active       = Column(Boolean, default=False)            # only one active at a time
    trained_at      = Column(DateTime, nullable=True)
    deployed_at     = Column(DateTime, nullable=True)
 
    analyses = relationship("Analysis", back_populates="model_version")