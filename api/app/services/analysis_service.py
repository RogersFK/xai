import json
from pathlib import Path
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.threat_event import ThreatEvent
from app.models.explanation import Explanation
from app.models.log_file import LogFile
from app.models.model_version import ModelVersion
from app.ml.predictor import analyze_log


def run_analysis(db: Session, log_file_id: int, user_id: int) -> Analysis:
    from fastapi import HTTPException

    lf = db.query(LogFile).filter(LogFile.id == log_file_id).first()
    if not lf:
        raise HTTPException(404, "Log file not found")

    active_model = db.query(ModelVersion).filter(
        ModelVersion.is_active == True
    ).first()
    
    
    
    try:
        BASE_DIR  = Path(__file__).parent.parent.parent  
        file_path = BASE_DIR / lf.stored_path 
        print(f"file path: {file_path}")
        with open(file_path, "r", errors="ignore") as fh:
            raw_text = fh.read()
    except (OSError, TypeError) as e:
        raise HTTPException(500, f"Could not read log file: {e}")

    ai_result = analyze_log(raw_text, lf.original_name)

    analysis = Analysis(
        log_file_id      = log_file_id,
        user_id          = user_id,
        model_version_id = active_model.id if active_model else None,
        user_prompt      = "",
        summary          = ai_result["summary"],
        anomalies        = json.dumps([e["type"] for e in ai_result["events"]]),
        patterns         = json.dumps(list({e["type"] for e in ai_result["events"] if e["type"] != "Normal"})),
        severity         = ai_result["severity"],
        threat_score     = ai_result["threat_score"],
        ai_model         = "random-forest-nslkdd-v1",
        tokens_used      = ai_result["tokens_used"],
        duration_sec     = ai_result["duration_sec"],
        status           = "completed",
        shap_data        = {s["feature"]: s["value"] for s in ai_result["shap"]},
        events           = ai_result["events"],
        raw_response     = json.dumps(ai_result),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # persist each threat event + its explanation
    for ev in ai_result["events"]:
        te = ThreatEvent(
            analysis_id = analysis.id,
            event_type  = ev["type"],
            source_ip   = ev["source_ip"],
            dest_ip     = ev["dest_ip"],
            username    = ev["username"],
            action      = ev["type"],
            severity    = ev["status"].lower(),
            status      = "open",
            raw_entry   = ev,
            occurred_at = datetime.strptime(ev["timestamp"], "%Y-%m-%d %H:%M:%S"),
        )
        db.add(te)
        db.flush()

        exp_data = ev["explanation"]
        explanation = Explanation(
            analysis_id      = analysis.id,
            threat_event_id  = te.id,
            feature_name     = exp_data["top_features"][0]["feature"] if exp_data["top_features"] else "unknown",
            shap_value       = exp_data["top_features"][0]["shap_value"] if exp_data["top_features"] else 0.0,
            base_value       = 0.12,
            top_features     = exp_data["top_features"],
            counter_factuals = exp_data["counter_factuals"],
            narrative        = exp_data["verdict"],
        )
        db.add(explanation)

    db.commit()
    return analysis


def get_analysis(db: Session, analysis_id: int) -> Analysis:
    from fastapi import HTTPException
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not a:
        raise HTTPException(404, "Analysis not found")
    return a


def list_analyses(db: Session, user_id: int, see_all: bool) -> list[Analysis]:
    q = db.query(Analysis)
    if not see_all:
        q = q.filter(Analysis.user_id == user_id)
    return q.order_by(Analysis.created_at.desc()).all()


def format_analysis_out(analysis: Analysis, db: Session) -> dict:
    lf = db.query(LogFile).filter(LogFile.id == analysis.log_file_id).first()
    filename = lf.original_name if lf else "unknown"

    shap_raw = analysis.shap_data or {}
    max_val  = max(shap_raw.values(), default=0.5)
    shap     = [
        {"feature": k, "value": v, "max_val": max_val}
        for k, v in sorted(shap_raw.items(), key=lambda x: x[1], reverse=True)
    ]

    threat_events = (
        db.query(ThreatEvent)
        .filter(ThreatEvent.analysis_id == analysis.id)
        .order_by(ThreatEvent.occurred_at)
        .all()
    )

    events = []
    for te in threat_events:
        exp = db.query(Explanation).filter(
            Explanation.threat_event_id == te.id
        ).first()

        explanation = None
        if exp:
            explanation = {
                "verdict":          exp.narrative,
                "top_features":     exp.top_features     or [],
                "counter_factuals": exp.counter_factuals or [],
                "raw_evidence":     te.raw_entry.get("explanation", {}).get("raw_evidence", {}),
            }

        raw = te.raw_entry or {}
        events.append({
            "timestamp":   te.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if te.occurred_at else "—",
            "event_id":    raw.get("event_id", f"EVT-{te.id}"),
            "score":       raw.get("score", 0),
            "status":      te.severity.upper(),
            "type":        te.event_type,
            "source_ip":   te.source_ip,
            "dest_ip":     te.dest_ip,
            "username":    te.username,
            "process":     raw.get("process", "unknown"),
            "port":        raw.get("port", 0),
            "protocol":    raw.get("protocol", "unknown"),
            "bytes_sent":  raw.get("bytes_sent", 0),
            "lime":        raw.get("lime"),
            "pos":         raw.get("pos"),
            "neg":         raw.get("neg"),
            "explanation": explanation,
        })

    return {
        "id":           analysis.id,
        "filename":     filename,
        "threat_score": analysis.threat_score,
        "severity":     analysis.severity,
        "status":       analysis.status,
        "summary":      analysis.summary,
        "created_at":   analysis.created_at,
        "shap":         shap,
        "events":       events,
    }