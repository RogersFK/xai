from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.analysis import Analysis
from app.models.threat_event import ThreatEvent
from app.models.model_version import ModelVersion
from app.schemas.dashboard import (
    DashboardOut, StatCardsOut, FeedEventOut,
    NodeIntelOut, ModelDistributionOut,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
bearer = HTTPBearer()


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    see_all = current_user.has_permission("analysis:view_all")

    analysis_q = db.query(Analysis).filter(Analysis.status == "completed")
    if not see_all:
        analysis_q = analysis_q.filter(Analysis.user_id == current_user.id)

    total_logs = analysis_q.count()

    threat_q = db.query(ThreatEvent).join(Analysis).filter(
        Analysis.status == "completed",
        ThreatEvent.severity.in_(["critical", "high"]),
    )
    if not see_all:
        threat_q = threat_q.filter(Analysis.user_id == current_user.id)

    suspicious_events = threat_q.count()
    normal_events     = max(total_logs - suspicious_events, 0)

    now       = datetime.utcnow()
    thirty    = now - timedelta(days=30)
    sixty     = now - timedelta(days=60)

    current_period_q = analysis_q.filter(Analysis.created_at >= thirty)
    previous_period_q = analysis_q.filter(
        Analysis.created_at >= sixty,
        Analysis.created_at <  thirty,
    )
    current_count  = current_period_q.count()
    previous_count = previous_period_q.count()

    if previous_count > 0:
        change_pct = ((current_count - previous_count) / previous_count) * 100
    else:
        change_pct = 0.0

    stat_cards = StatCardsOut(
        total_logs_analyzed   = total_logs,
        suspicious_events     = suspicious_events,
        normal_events         = normal_events,
        suspicious_change_pct = round(change_pct, 1),
    )
    
    feed_q = (
        db.query(ThreatEvent)
        .join(Analysis)
        .filter(Analysis.status == "completed")
    )

    if not see_all:
        feed_q = feed_q.filter(Analysis.user_id == current_user.id)

    feed_events      = feed_q.order_by(ThreatEvent.occurred_at.desc()).limit(20).all()
    total_feed_count = feed_q.count()

    live_feed = [
        FeedEventOut(
            id         = e.id,
            timestamp  = e.occurred_at or datetime.utcnow(),
            initials   = _initials(e.username),
            username   = e.username or "unknown",
            source_ip  = e.source_ip or "—",
            event_type = e.event_type,
            severity   = e.severity,
        )
        for e in feed_events
    ]

    active_model = (
        db.query(ModelVersion)
        .filter(ModelVersion.is_active == True)
        .first()
    )

    dist_rows = (
        db.query(
            ModelVersion.name,
            ModelVersion.version,
            func.count(Analysis.id).label("cnt"),
        )
        .join(Analysis, Analysis.model_version_id == ModelVersion.id)
        .filter(Analysis.status == "completed")
        .group_by(ModelVersion.id)
        .all()
    )

    total_analyses = sum(r.cnt for r in dist_rows) or 1
    distribution = [
        ModelDistributionOut(
            name       = f"{r.name} {r.version}",
            percentage = round((r.cnt / total_analyses) * 100, 1),
        )
        for r in dist_rows
    ]

    node_intel = NodeIntelOut(
        active_model_name    = active_model.name    if active_model else "No model deployed",
        active_model_version = active_model.version if active_model else "—",
        model_distribution   = distribution,
    )

    return DashboardOut(
        stat_cards       = stat_cards,
        live_feed        = live_feed,
        node_intel       = node_intel,
        total_feed_count = total_feed_count,
    )


def _initials(username: str) -> str:
    if not username:
        return "UK"
    parts = username.replace("_", " ").replace(".", " ").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return username[:2].upper()