import hashlib
import os
import json
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import HTTPException

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from app.models.report import Report
from app.models.analysis import Analysis
from app.models.threat_event import ThreatEvent
from app.models.log_file import LogFile
from app.models.alert import Alert



def _hash_report(report: Report) -> str:
    content = json.dumps({
        "id":                report.id,
        "title":             report.title,
        "executive_summary": report.executive_summary,
        "case_number":       report.case_number,
        "threat_vectors":    report.threat_vectors,
        "critical_artifacts":report.critical_artifacts,
        "created_by":        report.created_by,
        "generated_at":      str(report.generated_at),
    }, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def _build_metric_card(report: Report, analysis: Analysis,
                        threat_events: list, db: Session) -> dict:
    critical_alerts = db.query(Alert).filter(
        Alert.analysis_id == report.analysis_id,
        Alert.level       == "critical",
    ).count()

    mc = report.metric_card or {}
    return {
        "integrity_score":  round((1 - (analysis.threat_score or 0)) * 100, 1)
                            if analysis else 0.0,
        "total_artifacts":  len(threat_events),
        "alerts_critical":  critical_alerts,
        "processing_time":  analysis.duration_sec if analysis else 0.0,
        "case_number":      report.case_number,
        "hash_sha256":      mc.get("hash_sha256", report.hash_sha256 or "—"),
        "chain_of_custody": report.chain_of_custody or "—",
        "signed_by":        mc.get("signed_by", "—"),
    }


def _build_vectors(analysis: Analysis) -> list:
    shap_raw = (analysis.shap_data or {}) if analysis else {}
    total    = sum(shap_raw.values()) or 1
    vectors  = [
        {
            "label":      feat.replace("_", " ").title(),
            "percentage": round((val / total) * 100, 1),
        }
        for feat, val in sorted(
            shap_raw.items(), key=lambda x: x[1], reverse=True
        )
    ][:5]
    for i, v in enumerate(vectors):
        v["label"] = f"VEC_{chr(65 + i)}"
    return vectors



def _build_artifacts(threat_events: list, db: Session = None) -> list:
    from app.models.explanation import Explanation
    result = []
    for te in threat_events:
        raw = te.raw_entry or {}
        exp = None
        if db:
            exp = db.query(Explanation).filter(
                Explanation.threat_event_id == te.id
            ).first()

        result.append({
            "timestamp":       te.occurred_at.strftime("%Y-%m-%d %H:%M:%S")
                               if te.occurred_at else "—",
            "source":          te.username or te.source_ip or "UNKNOWN",
            "action":          te.event_type,
            "status":          te.severity.upper(),
            # detail fields for PDF
            "verdict":         exp.narrative        if exp else raw.get("lime", ""),
            "top_features":    exp.top_features     if exp else raw.get("explanation", {}).get("top_features", []),
            "counter_factuals":exp.counter_factuals if exp else raw.get("explanation", {}).get("counter_factuals", []),
        })
    return result


# def _build_artifacts(threat_events: list) -> list:
#     return [
#         {
#             "timestamp": te.occurred_at.strftime("%Y-%m-%d %H:%M:%S")
#                          if te.occurred_at else "—",
#             "source":    te.username or te.source_ip or "UNKNOWN",
#             "action":    te.event_type,
#             "status":    te.severity.upper(),
#         }
#         for te in threat_events
#     ]



def generate_report(db: Session, analysis_id: int, user_id: int) -> Report:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(404, "Analysis not found")

    existing = db.query(Report).filter(
        Report.analysis_id == analysis_id
    ).first()
    if existing:
        return existing

    lf = db.query(LogFile).filter(
        LogFile.id == analysis.log_file_id
    ).first()
    filename = lf.original_name if lf else "unknown"

    report_count = db.query(Report).count() + 1
    case_number  = (
        f"F-{str(report_count).zfill(3)}-ALPHA-"
        f"{chr(64 + (report_count % 26) + 1)}"
    )

    threat_events = (
        db.query(ThreatEvent)
        .filter(ThreatEvent.analysis_id == analysis_id)
        .order_by(ThreatEvent.occurred_at.desc())
        .all()
    )

    vectors   = _build_vectors(analysis)
    # artifacts = _build_artifacts(threat_events)
    artifacts = _build_artifacts(threat_events, db=db)
    critical_alerts = db.query(Alert).filter(
        Alert.analysis_id == analysis_id,
        Alert.level       == "critical",
    ).count()

    metric_card = {
        "integrity_score":  round((1 - (analysis.threat_score or 0)) * 100, 1),
        "total_artifacts":  len(threat_events),
        "alerts_critical":  critical_alerts,
        "processing_time":  analysis.duration_sec or 0.0,
        "case_number":      case_number,
        "hash_sha256":      "—",
        "chain_of_custody": f"Generated from analysis #{analysis_id} | File: {filename}",
        "signed_by":        "—",
    }

    report = Report(
        analysis_id       = analysis_id,
        created_by        = user_id,
        title             = (
            f"Forensic Report #XAI-{datetime.utcnow().year}-"
            f"{str(report_count).zfill(3)}"
        ),
        case_number       = case_number,
        status            = "draft",
        hash_sha256       = "—",
        chain_of_custody  = (
            f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}] "
            f"Report generated from analysis #{analysis_id} | File: {filename}"
        ),
        clearance_level   = 3,
        generated_at      = datetime.utcnow(),
        executive_summary = analysis.summary or "",
        threat_vectors    = vectors,
        critical_artifacts= artifacts,
        metric_card       = metric_card,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report_detail(db: Session, report_id: int) -> dict:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")

    analysis = db.query(Analysis).filter(
        Analysis.id == report.analysis_id
    ).first()

    threat_events = (
        db.query(ThreatEvent)
        .filter(ThreatEvent.analysis_id == report.analysis_id)
        .order_by(ThreatEvent.occurred_at.desc())
        .all()
    ) if analysis else []

    metric_card = _build_metric_card(report, analysis, threat_events, db)

    return {
        "id":                report.id,
        "title":             report.title,
        "case_number":       report.case_number,
        "status":            report.status,
        "clearance_level":   report.clearance_level,
        "generated_at":      report.generated_at,
        "signed_at":         report.signed_at,
        "executive_summary": report.executive_summary
                             or (analysis.summary if analysis else ""),
        "metric_card":       metric_card,
        "threat_vectors":    report.threat_vectors or _build_vectors(analysis),
        "critical_artifacts":report.critical_artifacts
                             or _build_artifacts(threat_events),
        "chain_of_custody":  report.chain_of_custody or "—",
    }


def list_reports(db: Session, user_id: int, see_all: bool) -> list:
    q = db.query(Report)
    if not see_all:
        q = q.filter(Report.created_by == user_id)
    return q.order_by(Report.generated_at.desc()).all()


def append_notes(db: Session, report_id: int,
                 notes: str, user_id: int) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if report.created_by != user_id:
        raise HTTPException(403, "Access denied")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    existing  = report.chain_of_custody or ""
    report.chain_of_custody = (
        f"{existing}\n[{timestamp}] NOTE: {notes}"
    ).strip()

    # sync into metric_card so frontend displays updated CoC
    mc = report.metric_card or {}
    mc["chain_of_custody"] = report.chain_of_custody
    report.metric_card = mc

    db.commit()
    db.refresh(report)
    return report


def sign_report(db: Session, report_id: int, signed_by: str) -> dict:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if report.status == "signed":
        raise HTTPException(400, "Report is already signed")

    content_hash = _hash_report(report)
    now          = datetime.utcnow()
    now_str      = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    report.status     = "signed"
    report.signed_at  = now
    report.hash_sha256 = content_hash
    report.chain_of_custody = (
        f"{report.chain_of_custody or ''}\n"
        f"[{now_str}] SIGNED by {signed_by} | "
        f"SHA-256: {content_hash[:16]}…"
    ).strip()

    mc = report.metric_card or {}
    mc["hash_sha256"]      = content_hash
    mc["signed_by"]        = signed_by
    mc["signed_at"]        = now.isoformat()
    mc["chain_of_custody"] = report.chain_of_custody
    report.metric_card     = mc

    db.commit()
    db.refresh(report)
    return {"hash": content_hash}


def generate_pdf_bytes(report: Report) -> bytes:
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm
    )

    title_style = ParagraphStyle("title",
        fontSize=18, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f766e"), spaceAfter=6)
    heading_style = ParagraphStyle("heading",
        fontSize=10, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f766e"),
        spaceAfter=6, spaceBefore=14)
    subheading_style = ParagraphStyle("subheading",
        fontSize=9, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4, spaceBefore=8)
    body_style = ParagraphStyle("body",
        fontSize=9, fontName="Helvetica",
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6, leading=14)
    meta_style = ParagraphStyle("meta",
        fontSize=7, fontName="Helvetica",
        textColor=colors.HexColor("#475569"), spaceAfter=3)
    small_style = ParagraphStyle("small",
        fontSize=8, fontName="Helvetica",
        textColor=colors.HexColor("#475569"),
        spaceAfter=4, leading=12)

    # color constants
    COL_TEAL    = colors.HexColor("#0f766e")
    COL_DARK    = colors.HexColor("#0f172a")
    COL_MUTED   = colors.HexColor("#475569")
    COL_ERROR   = colors.HexColor("#dc2626")
    COL_WARNING = colors.HexColor("#d97706")
    COL_SUCCESS = colors.HexColor("#15803d")
    COL_INFO    = colors.HexColor("#0284c7")
    COL_SURFACE = colors.HexColor("#dff4f2")
    COL_HIGH    = colors.HexColor("#cfeceb")
    COL_WHITE   = colors.white

    mc         = report.metric_card or {}
    artifacts  = report.critical_artifacts or []
    vectors    = report.threat_vectors    or []
    story      = []

    # ── header ────────────────────────────────────────────────
    story.append(Paragraph("XAI FORENSICS SYSTEM", meta_style))
    story.append(Paragraph("CLASSIFIED FORENSIC REPORT", title_style))
    story.append(Paragraph(report.title or "Forensic Report", title_style))
    story.append(Spacer(1, 0.4*cm))

    # ── metadata table ────────────────────────────────────────
    meta_data = [
        ["Case Number",     report.case_number or "—"],
        ["Status",          (report.status or "draft").upper()],
        ["Clearance Level", f"Level {report.clearance_level or '—'}"],
        ["Generated",       str(report.generated_at or "")[:19]],
        ["Signed At",       str(report.signed_at or "Not signed")[:19]],
        ["SHA-256",         (mc.get("hash_sha256") or "Not signed")[:48]],
        ["Signed By",       mc.get("signed_by") or "—"],
        ["Integrity Score", f"{mc.get('integrity_score', 0):.1f}%"],
        ["Total Artifacts", str(mc.get("total_artifacts", 0))],
        ["Critical Alerts", str(mc.get("alerts_critical", 0))],
    ]
    meta_table = Table(meta_data, colWidths=[4*cm, 13*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (0, -1), COL_HIGH),
        ("BACKGROUND",     (1, 0), (1, -1), COL_WHITE),
        ("TEXTCOLOR",      (0, 0), (0, -1), COL_TEAL),
        ("TEXTCOLOR",      (1, 0), (1, -1), COL_DARK),
        ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [COL_HIGH, COL_SURFACE]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
        ("PADDING",        (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    # ── I. executive summary ──────────────────────────────────
    story.append(Paragraph("I. EXECUTIVE SUMMARY", heading_style))
    story.append(Paragraph(report.executive_summary or "—", body_style))

    # ── II. overall log file status ───────────────────────────
    story.append(Paragraph("II. OVERALL LOG FILE STATUS", heading_style))

    total_events  = len(artifacts)
    normal_events = sum(
        1 for a in artifacts
        if (a.get("status") or "").upper() in ("LOW", "NORMAL", "BENIGN")
    )
    threat_events = total_events - normal_events
    normal_pct    = (normal_events / total_events * 100) if total_events else 0
    threat_pct    = (threat_events / total_events * 100) if total_events else 0

    status_data = [
        ["Metric",                    "Count", "Percentage"],
        ["Total Events Detected",     str(total_events),  "100%"],
        ["Threat Events",             str(threat_events), f"{threat_pct:.1f}%"],
        ["Normal / Benign Events",    str(normal_events), f"{normal_pct:.1f}%"],
    ]
    status_table = Table(status_data, colWidths=[9*cm, 3*cm, 5*cm])
    status_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  COL_TEAL),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  COL_WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COL_WHITE, COL_SURFACE]),
        ("TEXTCOLOR",   (0, 1), (-1, -1), COL_DARK),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
        ("PADDING",     (0, 0), (-1, -1), 6),
        # highlight threat row red
        ("TEXTCOLOR",   (0, 2), (-1, 2),  COL_ERROR),
        ("FONTNAME",    (0, 2), (-1, 2),  "Helvetica-Bold"),
        # highlight normal row green
        ("TEXTCOLOR",   (0, 3), (-1, 3),  COL_SUCCESS),
        ("FONTNAME",    (0, 3), (-1, 3),  "Helvetica-Bold"),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.3*cm))

    # ── III. threat vector distribution ──────────────────────
    story.append(Paragraph("III. THREAT VECTOR DISTRIBUTION", heading_style))
    if vectors:
        vec_data = [["Threat Vector", "Percentage"]] + [
            [v.get("label", "—"), f"{v.get('percentage', 0):.1f}%"]
            for v in vectors
        ]
        vec_table = Table(vec_data, colWidths=[11*cm, 6*cm])
        vec_table.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  COL_TEAL),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  COL_WHITE),
            ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COL_WHITE, COL_SURFACE]),
            ("TEXTCOLOR",      (0, 1), (-1, -1), COL_DARK),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
            ("PADDING",        (0, 0), (-1, -1), 6),
        ]))
        story.append(vec_table)
    else:
        story.append(Paragraph("No threat vectors recorded.", body_style))

    # ── IV. critical artifacts overview ───────────────────────
    story.append(Paragraph("IV. CRITICAL ARTIFACTS OVERVIEW", heading_style))
    if artifacts:
        art_data = [["Timestamp", "Source", "Action", "Status"]] + [
            [a.get("timestamp", "—"), a.get("source", "—"),
             a.get("action",    "—"), a.get("status", "—")]
            for a in artifacts
        ]
        art_table = Table(art_data, colWidths=[4*cm, 4*cm, 7*cm, 2*cm])

        art_styles = [
            ("BACKGROUND",  (0, 0), (-1, 0),  COL_TEAL),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  COL_WHITE),
            ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 7),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
            ("PADDING",     (0, 0), (-1, -1), 5),
        ]
        for row_i, a in enumerate(artifacts, start=1):
            status = (a.get("status") or "").upper()
            bg     = (colors.HexColor("#fef2f2") if status in ("CRITICAL", "HIGH")
                      else colors.HexColor("#fffbeb") if status == "MEDIUM"
                      else colors.HexColor("#f0fdf4") if status in ("LOW", "NORMAL", "BENIGN")
                      else COL_WHITE)
            art_styles.append(("BACKGROUND", (0, row_i), (-1, row_i), bg))
            txt_col = (COL_ERROR   if status in ("CRITICAL", "HIGH")
                       else COL_WARNING if status == "MEDIUM"
                       else COL_SUCCESS if status in ("LOW", "NORMAL", "BENIGN")
                       else COL_DARK)
            art_styles.append(("TEXTCOLOR", (3, row_i), (3, row_i), txt_col))

        art_table.setStyle(TableStyle(art_styles))
        story.append(art_table)
    else:
        story.append(Paragraph("No critical artifacts recorded.", body_style))

    # ── V. event details (all events including normal) ────────
    story.append(Paragraph("V. DETAILED EVENT ANALYSIS", heading_style))

    # pull full events from raw_response stored in analysis if available
    # artifacts already contains per-event data — we use it enriched
    _STATUS_LABEL = {
        "CRITICAL": ("CRITICAL", COL_ERROR),
        "HIGH":     ("HIGH",     COL_ERROR),
        "MEDIUM":   ("MEDIUM",   COL_WARNING),
        "LOW":      ("LOW",      COL_SUCCESS),
        "NORMAL":   ("NORMAL",   COL_SUCCESS),
        "BENIGN":   ("BENIGN",   COL_SUCCESS),
    }

    if artifacts:
        for idx, a in enumerate(artifacts, start=1):
            status     = (a.get("status") or "UNKNOWN").upper()
            lbl, scol  = _STATUS_LABEL.get(status, (status, COL_MUTED))
            action     = a.get("action", "—")
            source     = a.get("source", "—")
            timestamp  = a.get("timestamp", "—")
            verdict    = a.get("verdict", "")
            features   = a.get("top_features", [])
            cfs        = a.get("counter_factuals", [])

            # event header row
            ev_hdr_data = [[
                f"Event {idx:02d}",
                f"{lbl}",
                action,
                timestamp,
            ]]
            ev_hdr = Table(ev_hdr_data, colWidths=[2*cm, 3*cm, 8*cm, 4*cm])
            ev_hdr.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0), COL_HIGH),
                ("TEXTCOLOR",   (0, 0), (0,  0), COL_TEAL),
                ("FONTNAME",    (0, 0), (0,  0), "Helvetica-Bold"),
                ("TEXTCOLOR",   (1, 0), (1,  0), scol),
                ("FONTNAME",    (1, 0), (1,  0), "Helvetica-Bold"),
                ("TEXTCOLOR",   (2, 0), (-1, 0), COL_DARK),
                ("FONTSIZE",    (0, 0), (-1, -1), 8),
                ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
                ("PADDING",     (0, 0), (-1, -1), 5),
            ]))
            story.append(ev_hdr)

            # source info
            src_data = [
                ["Source", source, "Action", action],
            ]
            src_table = Table(src_data, colWidths=[2*cm, 6*cm, 2*cm, 7*cm])
            src_table.setStyle(TableStyle([
                ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE",  (0, 0), (-1, -1), 7),
                ("TEXTCOLOR", (0, 0), (-1, -1), COL_MUTED),
                ("BACKGROUND",(0, 0), (-1, -1), COL_WHITE),
                ("GRID",      (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
                ("PADDING",   (0, 0), (-1, -1), 4),
            ]))
            story.append(src_table)

            # verdict
            if verdict:
                story.append(Paragraph(
                    f"<b>Verdict:</b> {verdict}", small_style))

            # SHAP features
            if features:
                story.append(Paragraph("<b>Feature Contributions:</b>", small_style))
                feat_rows = [["Feature", "SHAP", "Direction", "Reason"]]
                for f in features[:4]:
                    feat_rows.append([
                        f.get("feature", "—"),
                        f"{f.get('shap_value', 0):+.3f}",
                        "▲ UP" if f.get("direction") == "up" else "▼ DOWN",
                        f.get("reason", "—")[:60],
                    ])
                feat_table = Table(feat_rows,
                                   colWidths=[3.5*cm, 1.5*cm, 2*cm, 10*cm])
                feat_styles = [
                    ("BACKGROUND",  (0, 0), (-1, 0), COL_TEAL),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), COL_WHITE),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0, 0), (-1, -1), 7),
                    ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
                    ("PADDING",     (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COL_WHITE, COL_SURFACE]),
                    ("TEXTCOLOR",   (0, 1), (-1, -1), COL_DARK),
                ]
                # color direction column
                for r, f in enumerate(features[:4], start=1):
                    col = COL_ERROR if f.get("direction") == "up" else COL_SUCCESS
                    feat_styles.append(("TEXTCOLOR", (2, r), (2, r), col))
                feat_table.setStyle(TableStyle(feat_styles))
                story.append(feat_table)

            # counterfactuals
            if cfs:
                story.append(Paragraph("<b>Counterfactual Analysis:</b>", small_style))
                cf_rows = [["Outcome", "Scenario"]]
                for cf in cfs:
                    cf_rows.append([
                        cf.get("outcome", "—"),
                        cf.get("change", "—")[:80],
                    ])
                cf_table = Table(cf_rows, colWidths=[3*cm, 14*cm])
                cf_table.setStyle(TableStyle([
                    ("BACKGROUND",  (0, 0), (-1, 0), COL_TEAL),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), COL_WHITE),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0, 0), (-1, -1), 7),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COL_WHITE, COL_SURFACE]),
                    ("TEXTCOLOR",   (0, 1), (-1, -1), COL_DARK),
                    ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
                    ("PADDING",     (0, 0), (-1, -1), 4),
                ]))
                story.append(cf_table)

            story.append(Spacer(1, 0.3*cm))
    else:
        story.append(Paragraph("No events to display.", body_style))

    # ── VI. recommendations ───────────────────────────────────
    story.append(Paragraph("VI. RECOMMENDATIONS", heading_style))

    _RECS = {
        "DoS": [
            ("IMMEDIATE",  "Block source IP at firewall level immediately."),
            ("IMMEDIATE",  "Enable SYN cookies on the affected host."),
            ("24 HOURS",   "Implement rate limiting on affected ports and services."),
            ("24 HOURS",   "Contact upstream ISP to apply null-routing on attacking IP range."),
            ("LONG TERM",  "Deploy a DDoS mitigation service or scrubbing center."),
            ("LONG TERM",  "Review and harden network architecture with redundant failover."),
        ],
        "Probe": [
            ("IMMEDIATE",  "Identify and close all unused open ports on scanned hosts."),
            ("IMMEDIATE",  "Add the scanning IP to the firewall block list."),
            ("24 HOURS",   "Enable port scan detection on IDS/IPS and tune thresholds."),
            ("24 HOURS",   "Audit firewall rules — remove overly permissive allow rules."),
            ("LONG TERM",  "Schedule regular vulnerability scans to find exposed services."),
            ("LONG TERM",  "Segment the network to limit lateral visibility between zones."),
        ],
        "R2L": [
            ("IMMEDIATE",  "Lock or reset credentials for all targeted accounts."),
            ("IMMEDIATE",  "Terminate all active sessions for affected user accounts."),
            ("IMMEDIATE",  "Block the source IP at the perimeter firewall."),
            ("24 HOURS",   "Enforce multi-factor authentication on all remote access."),
            ("24 HOURS",   "Audit SSH authorized_keys and remove unrecognized public keys."),
            ("LONG TERM",  "Implement account lockout after 5 failed authentication attempts."),
            ("LONG TERM",  "Deploy SIEM rule to alert on repeated failed logins across accounts."),
        ],
        "U2R": [
            ("IMMEDIATE",  "Isolate the affected host from the network immediately."),
            ("IMMEDIATE",  "Revoke all sudo and elevated privileges for the involved user."),
            ("IMMEDIATE",  "Check /etc/passwd and /etc/sudoers for unauthorized entries."),
            ("IMMEDIATE",  "Forensic image the disk before any remediation."),
            ("24 HOURS",   "Audit all cron jobs, startup scripts, and systemd services."),
            ("24 HOURS",   "Review all recently created or modified files on the host."),
            ("LONG TERM",  "Apply principle of least privilege — remove unnecessary sudo."),
            ("LONG TERM",  "Deploy file integrity monitoring (FIM) on critical system files."),
        ],
    }

    _URGENCY_COLOR = {
        "IMMEDIATE": COL_ERROR,
        "24 HOURS":  COL_WARNING,
        "LONG TERM": COL_SUCCESS,
    }

    # collect families present in this report
    families_present = set()
    for a in artifacts:
        status = (a.get("status") or "").upper()
        action = a.get("action", "")
        if "DoS"    in action or "Flood" in action: families_present.add("DoS")
        if "Probe"  in action or "Scan"  in action: families_present.add("Probe")
        if "R2L"    in action or "Brute" in action or "Exfil" in action:
            families_present.add("R2L")
        if "U2R"    in action or "Priv"  in action or "Shell" in action or "Rootkit" in action or "Backdoor" in action: families_present.add("U2R")

    # fallback — include all if we can't determine
    if not families_present:
        families_present = set(_RECS.keys())

    for family in ["DoS", "Probe", "R2L", "U2R"]:
        if family not in families_present:
            continue

        story.append(Paragraph(
            f"Recommendations for {family} Attacks:", subheading_style))

        rec_data = [["Priority", "Action"]]
        for urgency, text in _RECS[family]:
            rec_data.append([urgency, text])

        rec_table = Table(rec_data, colWidths=[3*cm, 14*cm])
        rec_styles = [
            ("BACKGROUND",  (0, 0), (-1, 0), COL_TEAL),
            ("TEXTCOLOR",   (0, 0), (-1, 0), COL_WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COL_WHITE, COL_SURFACE]),
            ("TEXTCOLOR",   (0, 1), (-1, -1), COL_DARK),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#b6d7d5")),
            ("PADDING",     (0, 0), (-1, -1), 5),
        ]
        for r, (urgency, _) in enumerate(_RECS[family], start=1):
            col = _URGENCY_COLOR.get(urgency, COL_MUTED)
            rec_styles.append(("TEXTCOLOR",  (0, r), (0, r), col))
            rec_styles.append(("FONTNAME",   (0, r), (0, r), "Helvetica-Bold"))

        rec_table.setStyle(TableStyle(rec_styles))
        story.append(rec_table)
        story.append(Spacer(1, 0.2*cm))

    # ── VII. chain of custody ─────────────────────────────────
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("VII. CHAIN OF CUSTODY", heading_style))
    coc_text = report.chain_of_custody or "No custody record."
    for line in coc_text.split("\n"):
        story.append(Paragraph(line or " ", body_style))

    # ── footer ────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "AUTHORIZED USE ONLY — All actions are logged and audited "
        "by the XAI Digital Forensics Authority.",
        meta_style))

    doc.build(story)
    return buffer.getvalue()


# def generate_pdf_bytes(report: Report) -> bytes:
#     buffer = BytesIO()
#     doc    = SimpleDocTemplate(
#         buffer, pagesize=A4,
#         rightMargin=2*cm, leftMargin=2*cm,
#         topMargin=2*cm,   bottomMargin=2*cm
#     )

#     title_style = ParagraphStyle("title",
#         fontSize=18, fontName="Helvetica-Bold",
#         textColor=colors.HexColor("#D4AF37"), spaceAfter=6)
#     heading_style = ParagraphStyle("heading",
#         fontSize=10, fontName="Helvetica-Bold",
#         textColor=colors.HexColor("#D4AF37"),
#         spaceAfter=6, spaceBefore=14)
#     body_style = ParagraphStyle("body",
#         fontSize=9,  fontName="Helvetica",
#         textColor=colors.HexColor("#222222"),
#         spaceAfter=6, leading=14)
#     meta_style = ParagraphStyle("meta",
#         fontSize=7,  fontName="Helvetica",
#         textColor=colors.HexColor("#666666"), spaceAfter=3)

#     mc      = report.metric_card or {}
#     story   = []

#     story.append(Paragraph("XAI FORENSICS SYSTEM", meta_style))
#     story.append(Paragraph("CLASSIFIED FORENSIC REPORT", title_style))
#     story.append(Paragraph(report.title or "Forensic Report", title_style))
#     story.append(Spacer(1, 0.4*cm))

#     meta_data = [
#         ["Case Number",     report.case_number or "—"],
#         ["Status",          (report.status or "draft").upper()],
#         ["Clearance Level", f"Level {report.clearance_level or '—'}"],
#         ["Generated",       str(report.generated_at or "")[:19]],
#         ["Signed At",       str(report.signed_at or "Not signed")[:19]],
#         ["SHA-256",         (mc.get("hash_sha256") or "Not signed")[:48] + "…"
#                             if len(mc.get("hash_sha256") or "") > 48
#                             else mc.get("hash_sha256") or "Not signed"],
#         ["Signed By",       mc.get("signed_by") or "—"],
#         ["Integrity Score", f"{mc.get('integrity_score', 0):.1f}%"],
#         ["Total Artifacts", str(mc.get("total_artifacts", 0))],
#         ["Critical Alerts", str(mc.get("alerts_critical", 0))],
#     ]
#     meta_table = Table(meta_data, colWidths=[4*cm, 13*cm])
#     meta_table.setStyle(TableStyle([
#         ("BACKGROUND",     (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
#         ("BACKGROUND",     (1, 0), (1, -1), colors.white),
#         ("TEXTCOLOR",      (0, 0), (0, -1), colors.HexColor("#333333")),
#         ("TEXTCOLOR",      (1, 0), (1, -1), colors.HexColor("#111111")),
#         ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
#         ("FONTSIZE",       (0, 0), (-1, -1), 8),
#         ("ROWBACKGROUNDS", (0, 0), (-1, -1),
#          [colors.HexColor("#F9F9F9"), colors.white]),
#         ("GRID",           (0, 0), (-1, -1), 0.5,
#          colors.HexColor("#CCCCCC")),
#         ("PADDING",        (0, 0), (-1, -1), 6),
#     ]))
#     story.append(meta_table)
#     story.append(Spacer(1, 0.5*cm))

#     story.append(Paragraph("I. EXECUTIVE SUMMARY", heading_style))
#     story.append(Paragraph(report.executive_summary or "—", body_style))

#     story.append(Paragraph("II. THREAT VECTOR DISTRIBUTION", heading_style))
#     vectors = report.threat_vectors or []
#     if vectors:
#         vec_data = [["Threat Vector", "Percentage"]] + [
#             [v.get("label", "—"), f"{v.get('percentage', 0):.1f}%"]
#             for v in vectors
#         ]
#         vec_table = Table(vec_data, colWidths=[11*cm, 6*cm])
#         vec_table.setStyle(TableStyle([
#             ("BACKGROUND",     (0, 0), (-1, 0),
#              colors.HexColor("#D4AF37")),
#             ("TEXTCOLOR",      (0, 0), (-1, 0), colors.black),
#             ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
#             ("FONTSIZE",       (0, 0), (-1, -1), 8),
#             ("ROWBACKGROUNDS", (0, 1), (-1, -1),
#              [colors.HexColor("#F9F9F9"), colors.white]),
#             ("TEXTCOLOR",      (0, 1), (-1, -1),
#              colors.HexColor("#222222")),
#             ("GRID",           (0, 0), (-1, -1), 0.5,
#              colors.HexColor("#CCCCCC")),
#             ("PADDING",        (0, 0), (-1, -1), 6),
#         ]))
#         story.append(vec_table)
#     else:
#         story.append(Paragraph("No threat vectors recorded.", body_style))

#     story.append(Paragraph("III. CRITICAL ARTIFACTS", heading_style))
#     artifacts = report.critical_artifacts or []
#     if artifacts:
#         art_data = [["Timestamp", "Source", "Action", "Status"]] + [
#             [a.get("timestamp", "—"), a.get("source", "—"),
#              a.get("action",    "—"), a.get("status", "—")]
#             for a in artifacts
#         ]
#         art_table = Table(art_data, colWidths=[4*cm, 4*cm, 7*cm, 2*cm])
#         art_table.setStyle(TableStyle([
#             ("BACKGROUND",     (0, 0), (-1, 0),
#              colors.HexColor("#D4AF37")),
#             ("TEXTCOLOR",      (0, 0), (-1, 0), colors.black),
#             ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
#             ("FONTSIZE",       (0, 0), (-1, -1), 7),
#             ("ROWBACKGROUNDS", (0, 1), (-1, -1),
#              [colors.HexColor("#F9F9F9"), colors.white]),
#             ("TEXTCOLOR",      (0, 1), (-1, -1),
#              colors.HexColor("#222222")),
#             ("GRID",           (0, 0), (-1, -1), 0.5,
#              colors.HexColor("#CCCCCC")),
#             ("PADDING",        (0, 0), (-1, -1), 5),
#         ]))
#         story.append(art_table)
#     else:
#         story.append(Paragraph("No critical artifacts recorded.", body_style))

#     story.append(Spacer(1, 0.4*cm))
#     story.append(Paragraph("IV. CHAIN OF CUSTODY", heading_style))
#     coc_text = (report.chain_of_custody or "No custody record.")
#     for line in coc_text.split("\n"):
#         story.append(Paragraph(line or " ", body_style))

#     story.append(Spacer(1, 1*cm))
#     story.append(Paragraph(
#         "AUTHORIZED USE ONLY — All actions are logged and audited "
#         "by the XAI Digital Forensics Authority.",
#         meta_style))

#     doc.build(story)
#     return buffer.getvalue()



def encrypt_pdf(pdf_bytes: bytes) -> tuple[bytes, str]:
    """
    Encrypt PDF with AES-256-GCM.
    Returns (payload, hex_key).
    payload = 12-byte nonce + ciphertext + 16-byte GCM tag.
    hex_key must be saved by the investigator — it is never stored server-side.
    """
    key      = AESGCM.generate_key(bit_length=256)
    nonce    = os.urandom(12)
    aesgcm   = AESGCM(key)
    ct       = aesgcm.encrypt(nonce, pdf_bytes, None)
    payload  = nonce + ct
    return payload, key.hex()


def decrypt_pdf(payload: bytes, hex_key: str) -> bytes:
    """Decrypt a payload produced by encrypt_pdf."""
    key    = bytes.fromhex(hex_key)
    nonce  = payload[:12]
    ct     = payload[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)