from datetime import datetime
from pydantic import BaseModel


class StatCardsOut(BaseModel):
    total_logs_analyzed: int
    suspicious_events: int
    normal_events: int
    suspicious_change_pct: float   # e.g. +12.0 means +12% vs previous period


class FeedEventOut(BaseModel):
    id: int
    timestamp: datetime
    initials: str                  # derived from username e.g. "JD"
    username: str
    source_ip: str
    event_type: str
    severity: str

    model_config = {"from_attributes": True}


class ModelDistributionOut(BaseModel):
    name: str
    percentage: float


class NodeIntelOut(BaseModel):
    active_model_name: str
    active_model_version: str
    model_distribution: list[ModelDistributionOut]


class DashboardOut(BaseModel):
    stat_cards: StatCardsOut
    live_feed: list[FeedEventOut]
    node_intel: NodeIntelOut
    total_feed_count: int