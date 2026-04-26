from datetime import datetime
from pydantic import BaseModel


class ArtifactOut(BaseModel):
    timestamp: str
    source:    str
    action:    str
    status:    str


class ThreatVectorOut(BaseModel):
    label:      str
    percentage: float


class MetricCardOut(BaseModel):
    integrity_score:  float
    total_artifacts:  int
    alerts_critical:  int
    processing_time:  float
    case_number:      str
    hash_sha256:      str
    chain_of_custody: str


class ReportDetailOut(BaseModel):
    id:               int
    title:            str
    case_number:      str
    status:           str
    clearance_level:  int
    generated_at:     datetime
    signed_at:        datetime | None

    # sections
    executive_summary:    str
    metric_card:          MetricCardOut
    threat_vectors:       list[ThreatVectorOut]
    critical_artifacts:   list[ArtifactOut]

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id:              int
    title:           str
    case_number:     str
    status:          str
    clearance_level: int
    generated_at:    datetime

    model_config = {"from_attributes": True}


class AppendNotesRequest(BaseModel):
    notes: str