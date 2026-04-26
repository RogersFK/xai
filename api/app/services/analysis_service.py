import json
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.threat_event import ThreatEvent
from app.models.explanation import Explanation
from app.models.log_file import LogFile
from app.models.model_version import ModelVersion

_SUMMARIES = [
    "Unauthorized lateral movement detected from internal subnet 192.168.1.x. "
    "Credential harvesting signatures identified targeting the root directory. "
    "Initial penetration achieved via CVE-2024-21887 on the perimeter gateway.",

    "SSH brute force attack detected. 847 failed authentication attempts from "
    "external IP 212.44.15.2 within a 10-minute window. Possible credential "
    "stuffing using leaked database.",

    "Anomalous outbound data transfer of 2.3GB to unknown external endpoint. "
    "Transfer occurred at 03:14 UTC outside business hours. Possible exfiltration "
    "via encrypted tunnel on port 443.",

    "Privilege escalation attempt detected. Process spawned unexpected child shell "
    "from nginx worker — strong indicator of web shell exploitation.",

    "C2 beaconing activity detected with consistent 60-second intervals to "
    "185.220.101.x. Pattern matches known Cobalt Strike malleable profile.",
]

_EVENT_POOL = [
    {
        "type":     "SSH Brute Force",
        "status":   "CRITICAL",
        "score":    0.91,
        "process":  "sshd",
        "port":     22,
        "protocol": "SSH",
        "features": [
            {"feature": "failed_logins",      "shap_value": 0.43, "direction": "up",
             "reason": "847 failed attempts in 10 minutes — 8.3 std deviations above baseline"},
            {"feature": "login_hour_anomaly", "shap_value": 0.18, "direction": "up",
             "reason": "Activity at 03:14 UTC — outside normal working hours for this account"},
            {"feature": "bytes_sent",         "shap_value": 0.08, "direction": "up",
             "reason": "Repeated small packets consistent with credential stuffing pattern"},
            {"feature": "normal_login_hours", "shap_value": 0.04, "direction": "down",
             "reason": "No scheduled job registered for this time window"},
        ],
        "counter_factuals": [
            {"change": "If failed_logins dropped below 5, threat score would fall to 0.12 (BENIGN)", "outcome": "Benign"},
            {"change": "If activity occurred between 08:00–18:00 UTC, threat score would fall to 0.44 (MEDIUM)", "outcome": "Medium"},
        ],
        "verdict_template": (
            "This event was classified as CRITICAL because {username} generated "
            "{count} failed SSH authentication attempts from {source_ip} within "
            "10 minutes — 8.3 standard deviations above the established baseline. "
            "The combination of volume, external origin, and off-hours timing "
            "strongly indicates an automated credential stuffing attack."
        ),
    },
    {
        "type":     "Elevated Privileges",
        "status":   "CRITICAL",
        "score":    0.88,
        "process":  "sudo",
        "port":     0,
        "protocol": "LOCAL",
        "features": [
            {"feature": "privilege_escalation", "shap_value": 0.38, "direction": "up",
             "reason": "sudo invocation accessing /etc/shadow outside business hours"},
            {"feature": "login_hour_anomaly",   "shap_value": 0.21, "direction": "up",
             "reason": "Escalation at 03:58 UTC — 5.2 std deviations outside normal pattern"},
            {"feature": "process_spawn_depth",  "shap_value": 0.14, "direction": "up",
             "reason": "Spawned child shell from web worker — anomalous process tree"},
            {"feature": "normal_login_hours",   "shap_value": 0.03, "direction": "down",
             "reason": "No maintenance window scheduled for this host"},
        ],
        "counter_factuals": [
            {"change": "If escalation occurred during business hours, threat score would fall to 0.41 (MEDIUM)", "outcome": "Medium"},
            {"change": "If /etc/shadow was not accessed, threat score would fall to 0.29 (LOW)", "outcome": "Low"},
        ],
        "verdict_template": (
            "This event was classified as CRITICAL because {username} performed "
            "a privilege escalation via sudo at {timestamp}, accessing sensitive "
            "system files including /etc/shadow. The process tree shows an "
            "unexpected child shell spawned from a web server worker process, "
            "which is a strong indicator of web shell exploitation."
        ),
    },
    {
        "type":     "Data Exfiltration",
        "status":   "HIGH",
        "score":    0.74,
        "process":  "svchost.exe",
        "port":     443,
        "protocol": "HTTPS",
        "features": [
            {"feature": "outbound_connections", "shap_value": 0.31, "direction": "up",
             "reason": "2.3GB transferred to 185.220.101.47 — host baseline is under 50MB/hour"},
            {"feature": "login_hour_anomaly",   "shap_value": 0.18, "direction": "up",
             "reason": "Transfer at 06:38 UTC — 4.1 std deviations outside normal hours"},
            {"feature": "bytes_sent",           "shap_value": 0.12, "direction": "up",
             "reason": "Single session byte count exceeds this host monthly average"},
            {"feature": "normal_login_hours",   "shap_value": 0.04, "direction": "down",
             "reason": "No scheduled backup or sync task registered for this window"},
        ],
        "counter_factuals": [
            {"change": "If outbound volume dropped below 200MB, threat score would fall to 0.28 (LOW)", "outcome": "Low"},
            {"change": "If destination IP was in the allowed list, threat score would fall to 0.33 (LOW)", "outcome": "Low"},
        ],
        "verdict_template": (
            "This event was classified as HIGH because {username} transferred "
            "2.3GB of data to external IP {dest_ip} via port 443 at {timestamp}. "
            "This volume is 46x above the established hourly baseline for this host. "
            "The destination IP is not in the approved allowlist and has no "
            "associated business justification."
        ),
    },
    {
        "type":     "C2 Beaconing",
        "status":   "CRITICAL",
        "score":    0.95,
        "process":  "rundll32.exe",
        "port":     443,
        "protocol": "HTTPS",
        "features": [
            {"feature": "dns_query_rate",       "shap_value": 0.44, "direction": "up",
             "reason": "60-second interval beaconing to 185.220.101.x — matches Cobalt Strike profile"},
            {"feature": "outbound_connections", "shap_value": 0.26, "direction": "up",
             "reason": "Consistent jitter pattern (±2s) consistent with automated C2 heartbeat"},
            {"feature": "process_spawn_depth",  "shap_value": 0.15, "direction": "up",
             "reason": "rundll32.exe spawned from Word macro — high-risk process chain"},
            {"feature": "normal_login_hours",   "shap_value": 0.02, "direction": "down",
             "reason": "Beaconing continued through business hours reducing anomaly score slightly"},
        ],
        "counter_factuals": [
            {"change": "If beacon interval exceeded 120s with >10s jitter, threat score would fall to 0.51 (MEDIUM)", "outcome": "Medium"},
            {"change": "If destination IP was categorised as CDN, threat score would fall to 0.44 (MEDIUM)", "outcome": "Medium"},
        ],
        "verdict_template": (
            "This event was classified as CRITICAL because the process {process} "
            "on host {source_ip} exhibited consistent 60-second interval beaconing "
            "to {dest_ip} — a pattern matching known Cobalt Strike malleable C2 "
            "profiles. The process was spawned from a Word macro execution chain, "
            "indicating a phishing-based initial compromise."
        ),
    },
    {
        "type":     "Lateral Movement",
        "status":   "HIGH",
        "score":    0.68,
        "process":  "wmiexec.py",
        "port":     445,
        "protocol": "SMB",
        "features": [
            {"feature": "failed_logins",        "shap_value": 0.28, "direction": "up",
             "reason": "Authentication attempts across 14 internal hosts within 3 minutes"},
            {"feature": "port_scan_count",      "shap_value": 0.22, "direction": "up",
             "reason": "SMB port 445 probed across entire /24 subnet"},
            {"feature": "outbound_connections", "shap_value": 0.11, "direction": "up",
             "reason": "WMI remote execution commands observed on 3 successful connections"},
            {"feature": "normal_login_hours",   "shap_value": 0.05, "direction": "down",
             "reason": "Some target hosts had active admin sessions reducing suspicion slightly"},
        ],
        "counter_factuals": [
            {"change": "If connections were limited to 2 hosts, threat score would fall to 0.31 (LOW)", "outcome": "Low"},
            {"change": "If SMB traffic was within normal admin patterns, threat score would fall to 0.38 (MEDIUM)", "outcome": "Medium"},
        ],
        "verdict_template": (
            "This event was classified as HIGH because {username} attempted "
            "authentication across 14 internal hosts within 3 minutes using WMI "
            "remote execution from {source_ip}. This pattern is consistent with "
            "automated lateral movement tools. Three hosts accepted the connection "
            "indicating successful spread."
        ),
    },
]

_USERNAMES  = ["j.doe_admin", "s.agent_04", "backup_task", "unknown_user", "m.chen_sec"]
_DEST_IPS   = ["185.220.101.47", "212.44.15.2", "91.108.4.1", "45.33.32.156"]


def _random_ip():
    return f"{random.randint(10,220)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def _fake_ai_response(filename: str) -> dict:
    threat_score = round(random.uniform(0.3, 0.97), 3)
    severity = (
        "critical" if threat_score >= 0.80 else
        "high"     if threat_score >= 0.60 else
        "medium"   if threat_score >= 0.40 else
        "low"
    )

    # global SHAP — summary across entire log file
    all_features = [
        "failed_logins", "bytes_sent", "port_scan_count",
        "privilege_escalation", "outbound_connections",
        "login_hour_anomaly", "process_spawn_depth", "dns_query_rate",
    ]
    feature_pool = random.sample(all_features, 5)
    remaining    = threat_score
    shap_values  = []
    for feat in feature_pool:
        val = round(random.uniform(0.02, remaining * 0.55), 3)
        remaining = max(remaining - val, 0.01)
        shap_values.append({"feature": feat, "value": val})
    shap_values.sort(key=lambda x: x["value"], reverse=True)
    max_val = shap_values[0]["value"] if shap_values else 0.5
    for s in shap_values:
        s["max_val"] = max_val

    # events — pick from pool based on severity
    count       = random.randint(2, 5) if severity in ("critical", "high") else random.randint(0, 2)
    event_pool  = random.sample(_EVENT_POOL, min(count, len(_EVENT_POOL)))
    base_time   = datetime.utcnow() - timedelta(hours=random.randint(1, 8))
    events      = []

    for i, template in enumerate(event_pool):
        source_ip = _random_ip()
        dest_ip   = random.choice(_DEST_IPS)
        username  = random.choice(_USERNAMES)
        ev_time   = base_time + timedelta(minutes=i * random.randint(5, 20))
        bytes_sent = random.randint(50_000_000, 3_000_000_000)

        verdict = template["verdict_template"].format(
            username  = username,
            source_ip = source_ip,
            dest_ip   = dest_ip,
            timestamp = ev_time.strftime("%Y-%m-%d %H:%M:%S"),
            process   = template["process"],
            count     = random.randint(200, 900),
        )

        events.append({
            "event_id":    f"EVT-{str(uuid.uuid4())[:6].upper()}",
            "timestamp":   ev_time.strftime("%Y-%m-%d %H:%M:%S"),
            "type":        template["type"],
            "score":       template["score"],
            "status":      template["status"],
            "source_ip":   source_ip,
            "dest_ip":     dest_ip,
            "username":    username,
            "process":     template["process"],
            "port":        template["port"],
            "protocol":    template["protocol"],
            "bytes_sent":  bytes_sent,

            # explainability
            "explanation": {
                "verdict":          verdict,
                "top_features":     template["features"],
                "counter_factuals": template["counter_factuals"],
                "raw_evidence": {
                    "source_ip":  source_ip,
                    "dest_ip":    dest_ip,
                    "username":   username,
                    "process":    template["process"],
                    "bytes_sent": bytes_sent,
                    "port":       template["port"],
                    "protocol":   template["protocol"],
                },
            },

            # kept for frontend backward compat
            "lime": template["features"][0]["reason"],
            "pos":  template["features"][0]["feature"],
            "neg":  next(
                (f["feature"] for f in template["features"] if f["direction"] == "down"),
                "normal_login_hours"
            ),
        })

    return {
        "threat_score": threat_score,
        "severity":     severity,
        "summary":      random.choice(_SUMMARIES),
        "shap":         shap_values,
        "events":       events,
        "tokens_used":  random.randint(800, 3500),
        "duration_sec": round(random.uniform(0.8, 4.2), 2),
    }


def run_analysis(db: Session, log_file_id: int, user_id: int) -> Analysis:
    from fastapi import HTTPException

    lf = db.query(LogFile).filter(LogFile.id == log_file_id).first()
    if not lf:
        raise HTTPException(404, "Log file not found")

    active_model = db.query(ModelVersion).filter(
        ModelVersion.is_active == True
    ).first()

    ai_result = _fake_ai_response(lf.original_name)

    analysis = Analysis(
        log_file_id      = log_file_id,
        user_id          = user_id,
        model_version_id = active_model.id if active_model else None,
        user_prompt      = "",
        summary          = ai_result["summary"],
        anomalies        = json.dumps([e["type"] for e in ai_result["events"]]),
        patterns         = json.dumps(["Brute force", "Lateral movement", "Exfiltration"]),
        severity         = ai_result["severity"],
        threat_score     = ai_result["threat_score"],
        ai_model         = "fake-model-v0",
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
        db.flush()  # get te.id before creating explanation

        exp_data = ev["explanation"]
        explanation = Explanation(
            analysis_id      = analysis.id,
            threat_event_id  = te.id,
            feature_name     = exp_data["top_features"][0]["feature"],
            shap_value       = exp_data["top_features"][0]["shap_value"],
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

    # pull events from ThreatEvent table with their explanations
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