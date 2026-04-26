"""
Test seeder — populates all tables with realistic-looking fake data.
Remove this file and its call in create_app() before going to production.
"""
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role, Permission, UserRole, RolePermission
from app.models.log_file import LogFile
from app.models.analysis import Analysis
from app.models.threat_event import ThreatEvent
from app.models.explanation import Explanation
from app.models.model_version import ModelVersion
from app.models.report import Report
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.core.security import hash_password


# ── helpers ───────────────────────────────────────────────────────────────────

def _already_seeded(db: Session) -> bool:
    """Skip entirely if test data already exists."""
    return db.query(ModelVersion).filter(
        ModelVersion.name == "XAI-Test-Model"
    ).first() is not None


def _random_ip():
    return f"{random.randint(10,220)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def _random_dt(days_back=30):
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


# ── main entry ────────────────────────────────────────────────────────────────

def run_test_seed(db: Session) -> None:
    if _already_seeded(db):
        return

    print("[TEST SEED] Seeding test data...")

    model_versions = _seed_model_versions(db)
    users          = _seed_users(db)
    log_files      = _seed_log_files(db, users)
    analyses       = _seed_analyses(db, users, log_files, model_versions)
    threat_events  = _seed_threat_events(db, analyses)
    _seed_explanations(db, analyses, threat_events)
    _seed_reports(db, analyses, users)
    _seed_alerts(db, analyses, threat_events, users)
    _seed_audit_logs(db, users)

    print("[TEST SEED] Done.")


# ── model versions ────────────────────────────────────────────────────────────

def _seed_model_versions(db: Session) -> list:
    versions = [
        ModelVersion(
            name            = "XAI-Test-Model",
            version         = "1.0.0",
            model_type      = "random_forest",
            file_path       = "/models/xai_rf_1.0.0.pkl",
            hyperparameters = {"n_estimators": 200, "max_depth": 10},
            feature_names   = ["failed_logins", "bytes_sent", "port_scan_count",
                               "privilege_escalation", "outbound_connections"],
            accuracy        = 0.97,
            precision_score = 0.95,
            recall          = 0.93,
            f1_score        = 0.94,
            auc_roc         = 0.98,
            is_active       = True,
            trained_at      = datetime.utcnow() - timedelta(days=60),
            deployed_at     = datetime.utcnow() - timedelta(days=30),
        ),
        ModelVersion(
            name            = "XAI-Test-Model",
            version         = "0.9.0",
            model_type      = "xgboost",
            file_path       = "/models/xai_xgb_0.9.0.pkl",
            hyperparameters = {"n_estimators": 150, "learning_rate": 0.1},
            feature_names   = ["failed_logins", "bytes_sent", "port_scan_count"],
            accuracy        = 0.94,
            precision_score = 0.91,
            recall          = 0.89,
            f1_score        = 0.90,
            auc_roc         = 0.95,
            is_active       = False,
            trained_at      = datetime.utcnow() - timedelta(days=120),
            deployed_at     = datetime.utcnow() - timedelta(days=90),
        ),
    ]
    db.add_all(versions)
    db.commit()
    for v in versions:
        db.refresh(v)
    return versions


# ── users ─────────────────────────────────────────────────────────────────────

def _seed_users(db: Session) -> list:
    # fetch roles created by the main seeder
    analyst_role = db.query(Role).filter(Role.name == "analyst").first()
    viewer_role  = db.query(Role).filter(Role.name == "viewer").first()

    test_users = [
        {"username": "j.doe_admin",   "email": "jdoe@xai.local",    "role": analyst_role},
        {"username": "s.agent_04",    "email": "sagent@xai.local",   "role": analyst_role},
        {"username": "backup_task",   "email": "backup@xai.local",   "role": viewer_role},
        {"username": "unknown_user",  "email": "unknown@xai.local",  "role": viewer_role},
        {"username": "m.chen_sec",    "email": "mchen@xai.local",    "role": analyst_role},
    ]

    created = []
    for u in test_users:
        exists = db.query(User).filter(User.username == u["username"]).first()
        if exists:
            created.append(exists)
            continue

        user = User(
            username  = u["username"],
            email     = u["email"],
            hashed_pw = hash_password("Test@1234"),
            is_active = True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        if u["role"]:
            db.add(UserRole(user_id=user.id, role_id=u["role"].id))
            db.commit()

        created.append(user)

    return created


# ── log files ─────────────────────────────────────────────────────────────────

def _seed_log_files(db: Session, users: list) -> list:
    sources = [
        ("auth.log",           "linux_auth",    "syslog",       "text/plain"),
        ("windows_event.evtx", "windows_event", "evtx",         "application/octet-stream"),
        ("firewall.log",       "firewall",      "csv",          "text/csv"),
        ("network_capture.pcap","pcap",         "pcap",         "application/octet-stream"),
        ("apache_access.log",  "web_server",    "combined_log", "text/plain"),
        ("syslog.log",         "linux_syslog",  "syslog",       "text/plain"),
    ]

    created = []
    for i, (name, source, fmt, mime) in enumerate(sources):
        lf = LogFile(
            user_id       = users[i % len(users)].id,
            original_name = name,
            stored_path   = f"/uploads/test/{name}",
            file_size     = random.randint(50_000, 5_000_000),
            mime_type     = mime,
            log_source    = source,
            log_format    = fmt,
            uploaded_at   = _random_dt(days_back=30),
        )
        db.add(lf)
        db.commit()
        db.refresh(lf)
        created.append(lf)

    return created


# ── analyses ──────────────────────────────────────────────────────────────────

def _seed_analyses(db: Session, users, log_files, model_versions) -> list:
    severities   = ["critical", "high", "medium", "low", "none"]
    active_model = model_versions[0]
    old_model    = model_versions[1]

    summaries = [
        "Unauthorized lateral movement detected from internal subnet. Credential harvesting signatures identified.",
        "Brute force attack on SSH service. 847 failed attempts from external IP within 10 minutes.",
        "Anomalous outbound data transfer detected. Possible exfiltration via port 443.",
        "Privilege escalation attempt on root directory. CVE-2024-21887 exploit signature matched.",
        "Beaconing activity detected with 60-second intervals. Possible C2 communication.",
        "Normal log activity. No suspicious events detected during this period.",
    ]

    created = []
    for i, lf in enumerate(log_files):
        severity = severities[i % len(severities)]
        score    = round(random.uniform(0.6, 0.99), 2) if severity in ("critical","high") \
                   else round(random.uniform(0.1, 0.59), 2)

        analysis = Analysis(
            log_file_id      = lf.id,
            user_id          = lf.user_id,
            model_version_id = active_model.id if i % 3 != 0 else old_model.id,
            user_prompt      = "Analyse this log file for malware and suspicious activity.",
            summary          = summaries[i % len(summaries)],
            anomalies        = '["Failed login spike", "Unusual outbound traffic", "Root access attempt"]',
            patterns         = '["Brute force pattern", "Lateral movement", "Data staging"]',
            severity         = severity,
            threat_score     = score,
            ai_model         = "claude-sonnet-4-6",
            tokens_used      = random.randint(800, 4000),
            duration_sec     = round(random.uniform(0.8, 4.5), 2),
            status           = "completed",
            shap_data        = {
                "failed_logins":          round(random.uniform(0.1, 0.5), 3),
                "bytes_sent":             round(random.uniform(0.05, 0.3), 3),
                "port_scan_count":        round(random.uniform(0.05, 0.25), 3),
                "privilege_escalation":   round(random.uniform(0.1, 0.4), 3),
                "outbound_connections":   round(random.uniform(0.02, 0.2), 3),
            },
            events           = [
                {"line": 142, "raw": "Failed password for root from 212.44.15.2 port 22 ssh2"},
                {"line": 891, "raw": "Accepted publickey for admin from 192.168.1.104"},
            ],
            created_at       = lf.uploaded_at + timedelta(minutes=random.randint(1, 10)),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        created.append(analysis)

    return created


# ── threat events ─────────────────────────────────────────────────────────────

def _seed_threat_events(db: Session, analyses: list) -> list:
    event_types = [
        ("Elevated Privileges",  "critical"),
        ("SSH Brute Force",      "critical"),
        ("File Decryption",      "high"),
        ("Database Dump",        "high"),
        ("Lateral Movement",     "high"),
        ("C2 Beaconing",         "critical"),
        ("Port Scan",            "medium"),
        ("Data Exfiltration",    "critical"),
    ]

    usernames = ["j.doe_admin", "s.agent_04", "backup_task", "unknown_user", "m.chen_sec"]

    created = []
    for analysis in analyses:
        if analysis.severity == "none":
            continue

        # 2–5 events per analysis
        count = random.randint(2, 5)
        for _ in range(count):
            ev_type, ev_severity = random.choice(event_types)
            te = ThreatEvent(
                analysis_id = analysis.id,
                event_type  = ev_type,
                source_ip   = _random_ip(),
                dest_ip     = _random_ip(),
                username    = random.choice(usernames),
                action      = f"{ev_type} detected on host",
                severity    = ev_severity,
                status      = random.choice(["open", "investigating", "resolved"]),
                raw_entry   = {
                    "line":      random.randint(1, 5000),
                    "raw":       f"[ALERT] {ev_type} from {_random_ip()}",
                    "process":   random.choice(["sshd", "sudo", "cron", "nginx"]),
                    "pid":       random.randint(1000, 9999),
                },
                occurred_at = analysis.created_at + timedelta(
                    seconds=random.randint(10, 3600)
                ),
            )
            db.add(te)
            db.commit()
            db.refresh(te)
            created.append(te)

    return created


# ── explanations ──────────────────────────────────────────────────────────────

def _seed_explanations(db: Session, analyses: list, threat_events: list) -> None:
    narratives = [
        "This event was classified as malicious primarily because of 47 failed SSH attempts "
        "from 212.44.15.2 within 2 minutes, which is 8.3 standard deviations above baseline.",

        "Privilege escalation was flagged due to unusual sudo invocation outside business hours "
        "combined with access to /etc/shadow. The combination of these features drives 73% of the score.",

        "Outbound transfer volume of 2.3GB to an unknown external IP at 03:14 UTC triggered this alert. "
        "Historical baseline for this host is under 50MB per hour.",

        "The process spawned an unexpected child shell (bash) from nginx worker, "
        "a strong indicator of web shell exploitation.",
    ]

    for analysis in analyses:
        if analysis.severity == "none":
            continue

        related_events = [te for te in threat_events if te.analysis_id == analysis.id]

        exp = Explanation(
            analysis_id     = analysis.id,
            threat_event_id = related_events[0].id if related_events else None,
            feature_name    = "failed_logins",
            shap_value      = round(random.uniform(0.2, 0.6), 3),
            base_value      = 0.12,
            top_features    = [
                {"name": "failed_logins",        "shap": round(random.uniform(0.2, 0.5), 3), "direction": "up"},
                {"name": "bytes_sent",           "shap": round(random.uniform(0.1, 0.3), 3), "direction": "up"},
                {"name": "privilege_escalation", "shap": round(random.uniform(0.1, 0.4), 3), "direction": "up"},
                {"name": "outbound_connections", "shap": round(random.uniform(0.05, 0.2), 3),"direction": "up"},
                {"name": "normal_login_hours",   "shap": round(random.uniform(0.01, 0.1), 3),"direction": "down"},
            ],
            counter_factuals = [
                {"change": "Reduce failed_logins to below 5", "outcome": "Score drops to 0.18 (benign)"},
                {"change": "Remove outbound transfer",        "outcome": "Score drops to 0.31 (low risk)"},
            ],
            narrative       = random.choice(narratives),
            created_at      = analysis.created_at + timedelta(seconds=5),
        )
        db.add(exp)

    db.commit()


# ── reports ───────────────────────────────────────────────────────────────────

def _seed_reports(db: Session, analyses: list, users: list) -> None:
    admin = db.query(User).filter(User.username == "admin").first()
    creator_id = admin.id if admin else users[0].id

    statuses = ["draft", "signed", "archived"]

    for i, analysis in enumerate(analyses):
        if analysis.severity in ("none", "low"):
            continue

        report = Report(
            analysis_id      = analysis.id,
            created_by       = creator_id,
            title            = f"Forensic Incident Report: #XAI-2024-{str(i+1).zfill(3)}",
            case_number      = f"F-{str(i+1).zfill(3)}-ALPHA-{chr(65+i)}",
            status           = statuses[i % len(statuses)],
            hash_sha256      = f"8e9c349e{i:04x}2e2e2f31313{i}b8b8b8b8b8b8b8b8",
            chain_of_custody = "Verified by AI-Core 01 → Reviewed by j.doe_admin",
            clearance_level  = random.randint(2, 5),
            generated_at     = analysis.created_at + timedelta(minutes=5),
            signed_at        = analysis.created_at + timedelta(hours=1)
                               if i % 2 == 0 else None,
        )
        db.add(report)

    db.commit()


# ── alerts ────────────────────────────────────────────────────────────────────

def _seed_alerts(db: Session, analyses: list, threat_events: list, users: list) -> None:
    levels      = ["critical", "high", "medium"]
    statuses    = ["open", "acknowledged", "resolved"]
    analyst     = next((u for u in users if "doe" in u.username), users[0])

    for te in threat_events:
        if te.severity not in ("critical", "high"):
            continue

        alert = Alert(
            analysis_id     = te.analysis_id,
            threat_event_id = te.id,
            assigned_to_id  = analyst.id,
            level           = te.severity,
            title           = f"{te.event_type} detected — immediate review required",
            description     = (
                f"Threat event '{te.event_type}' was detected from {te.source_ip}. "
                f"User involved: {te.username}. Severity: {te.severity.upper()}."
            ),
            status          = random.choice(statuses),
            triggered_at    = te.occurred_at,
            resolved_at     = te.occurred_at + timedelta(hours=random.randint(1, 48))
                              if random.random() > 0.5 else None,
        )
        db.add(alert)

    db.commit()


# ── audit logs ────────────────────────────────────────────────────────────────

def _seed_audit_logs(db: Session, users: list) -> None:
    actions = [
        ("upload_log",      "LogFile"),
        ("run_analysis",    "Analysis"),
        ("export_report",   "Report"),
        ("login",           "User"),
        ("assign_role",     "User"),
        ("view_dashboard",  "Dashboard"),
    ]

    for user in users:
        for _ in range(random.randint(3, 8)):
            action, resource = random.choice(actions)
            db.add(AuditLog(
                user_id       = user.id,
                action        = action,
                resource_type = resource,
                resource_id   = random.randint(1, 20),
                payload       = {"note": f"test action by {user.username}"},
                ip_address    = _random_ip(),
                created_at    = _random_dt(days_back=30),
            ))

    db.commit()