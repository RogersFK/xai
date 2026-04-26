from datetime import datetime
from pydantic import BaseModel


class SHAPFeature(BaseModel):
    feature: str
    value:   float
    max_val: float


class EventOut(BaseModel):
    timestamp: str
    event_id:  str
    score:     float
    status:    str
    lime:      str | None = None
    pos:       str | None = None
    neg:       str | None = None


class AnalysisRunOut(BaseModel):
    id:           int
    filename:     str
    threat_score: float
    severity:     str
    status:       str
    summary:      str
    created_at:   datetime
    shap:         list[SHAPFeature]
    events:       list[EventOut]

    model_config = {"from_attributes": True}


class AnalysisHistoryItem(BaseModel):
    id:           int
    filename:     str
    threat_score: float
    severity:     str
    status:       str
    created_at:   datetime

    model_config = {"from_attributes": True}