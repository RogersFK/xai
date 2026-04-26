from datetime import datetime
from pydantic import BaseModel


# ── LogFile ───────────────────────────────────────────────────────────────────

class LogFileOut(BaseModel):
    id:             int
    user_id:        int
    original_name:  str
    file_size:      int
    mime_type:      str
    log_source:     str
    log_format:     str
    uploaded_at:    datetime
    analysis_count: int = 0

    model_config = {"from_attributes": True}


# ── Analysis ──────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    log_file_id:      int
    user_prompt:      str = ""


class AnalysisOut(BaseModel):
    id:               int
    log_file_id:      int
    user_id:          int
    model_version_id: int | None
    user_prompt:      str
    summary:          str
    anomalies:        str       # JSON string
    patterns:         str       # JSON string
    severity:         str
    threat_score:     float
    ai_model:         str
    tokens_used:      int
    duration_sec:     float
    status:           str
    error_msg:        str
    created_at:       datetime

    model_config = {"from_attributes": True}