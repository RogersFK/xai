# import uuid
# import numpy as np
# from datetime import datetime
# from .loader import get_artifacts
# from .log_parser import parse_log_file, events_to_matrix


# _SEVERITY_MAP = {
#     "DoS":    ("HIGH",     0.74),
#     "Probe":  ("MEDIUM",   0.55),
#     "R2L":    ("HIGH",     0.68),
#     "U2R":    ("CRITICAL", 0.91),
#     "Normal": ("LOW",      0.10),
# }

# _HINT_TO_ATTACK_TYPE = {
#     # DoS
#     "dos_flood":             "DoS — Flood Attack",
#     # Probe
#     "port_scan":             "Probe — Port Scan",
#     # R2L
#     "ssh_brute_force":       "R2L — SSH Brute Force",
#     "ftp_brute_force":       "R2L — FTP Brute Force",
#     "data_exfiltration":     "R2L — Data Exfiltration",
#     "ssh_login":             "R2L — Suspicious Remote Login",
#     # U2R
#     "privilege_escalation":  "U2R — Privilege Escalation",
#     "backdoor_creation":     "U2R — Backdoor Creation",
#     "rootkit_installation":  "U2R — Rootkit Installation",
#     "suid_manipulation":     "U2R — SUID Bit Manipulation",
#     "persistence_crontab":   "U2R — Cron Persistence",
#     "reverse_shell":         "U2R — Reverse Shell",
#     "web_shell":             "U2R — Web Shell Execution",
#     # fallback
#     "unknown":               "Unknown — Suspicious Activity",
# }

# _HINT_FAMILY_OVERRIDE = {
#     "ssh_brute_force":      "R2L",
#     "ftp_brute_force":      "R2L",
#     "data_exfiltration":    "R2L",
#     # "ssh_login":            "R2L",
#     "privilege_escalation": "U2R",
#     "backdoor_creation":    "U2R",
#     "rootkit_installation": "U2R",
#     "suid_manipulation":    "U2R",
#     "persistence_crontab":  "U2R",
#     "reverse_shell":        "U2R",
#     "web_shell":            "U2R",
#     "dos_flood":            "DoS",
#     "port_scan":            "Probe",
# }

# _CONFIDENCE_THRESHOLD = 0.55

# _DIRECTION_HINTS = {
#     "num_failed_logins":          "Multiple failed authentication attempts detected",
#     "serror_rate":                "High SYN error rate — possible port scan or flood",
#     "rerror_rate":                "Elevated REJ error rate — connections being refused",
#     "root_shell":                 "Root shell spawned — privilege escalation indicator",
#     "su_attempted":               "su/sudo invocation detected outside normal pattern",
#     "src_bytes":                  "Unusually large outbound data volume",
#     "dst_bytes":                  "Unusually large inbound data volume",
#     "count":                      "High connection count to same host",
#     "num_compromised":            "Compromised condition flags raised",
#     "hot":                        "Hot indicators present in session",
#     "logged_in":                  "Session authenticated successfully",
#     "same_srv_rate":              "Traffic concentrated on single service",
#     "diff_srv_rate":              "Traffic spread across multiple services — scanning",
#     "dst_host_serror_rate":       "Destination host showing high SYN error rate",
#     "srv_serror_rate":            "Service-level SYN error rate elevated",
#     "dst_host_rerror_rate":       "Destination host showing high REJ error rate",
#     "num_shells":                 "Shell process spawned — possible command execution",
#     "num_root":                   "Root-level operations detected",
#     "num_access_files":           "Sensitive file access detected",
#     "num_file_creations":         "Unusual file creation activity",
#     "wrong_fragment":             "Malformed packet fragments — possible evasion",
#     "urgent":                     "Urgent flag set — possible DoS signal",
#     "srv_count":                  "High service connection count",
#     "dst_host_count":             "High destination host connection count",
#     "dst_host_srv_count":         "High destination host service count",
#     "dst_host_diff_srv_rate":     "Destination accessing multiple services — lateral movement",
#     "dst_host_same_src_port_rate":"Consistent source port usage — automated tool indicator",
#     "srv_diff_host_rate":         "Service accessed from multiple hosts",
# }

# _VERDICT_TEMPLATES = {
#     "dos_flood": (
#         "Classified as DoS — Flood Attack. High volume of connection attempts "
#         "from {source_ip} caused connection table exhaustion and SYN flooding. "
#         "This pattern matches automated denial-of-service tooling."
#     ),
#     "port_scan": (
#         "Classified as Probe — Port Scan. Source {source_ip} probed multiple "
#         "ports in rapid succession. This reconnaissance activity is consistent "
#         "with automated scanning tools such as nmap or masscan."
#     ),
#     "ssh_brute_force": (
#         "Classified as R2L — SSH Brute Force. Source {source_ip} attempted "
#         "authentication {count} times against multiple usernames. "
#         "This pattern is consistent with automated credential stuffing attacks."
#     ),
#     "ftp_brute_force": (
#         "Classified as R2L — FTP Brute Force. Source {source_ip} made repeated "
#         "failed FTP login attempts against multiple accounts. "
#         "Possible credential dictionary attack in progress."
#     ),
#     "data_exfiltration": (
#         "Classified as R2L — Data Exfiltration. User {username} transferred "
#         "large volumes of data to external host via curl/wget after gaining "
#         "access. Sensitive files may have been compromised."
#     ),
#     "ssh_login": (
#         "Classified as R2L — Suspicious Remote Login. User {username} logged in "
#         "from {source_ip} following prior failed attempts. "
#         "Possible successful brute force or stolen credential use."
#     ),
#     "privilege_escalation": (
#         "Classified as U2R — Privilege Escalation. User {username} invoked sudo "
#         "to gain root access and accessed sensitive system files including "
#         "/etc/shadow. Strong indicator of unauthorized privilege abuse."
#     ),
#     "backdoor_creation": (
#         "Classified as U2R — Backdoor Creation. User {username} created a new "
#         "system account with full sudo privileges and no password requirement. "
#         "Persistent unauthorized access has been established."
#     ),
#     "rootkit_installation": (
#         "Classified as U2R — Rootkit Installation. User {username} installed a "
#         "shared library override and ran ldconfig to activate it. "
#         "System binaries may be compromised."
#     ),
#     "suid_manipulation": (
#         "Classified as U2R — SUID Manipulation. User {username} set the SUID bit "
#         "on a binary allowing privilege escalation without sudo. "
#         "This is a classic local privilege escalation technique."
#     ),
#     "persistence_crontab": (
#         "Classified as U2R — Cron Persistence. User {username} added a cron job "
#         "that periodically downloads and executes a remote payload. "
#         "Command-and-control beacon has been established."
#     ),
#     "reverse_shell": (
#         "Classified as U2R — Reverse Shell. A process on this host established "
#         "an outbound connection to {source_ip} and attached a shell to it. "
#         "The attacker has interactive remote code execution."
#     ),
#     "web_shell": (
#         "Classified as U2R — Web Shell. A PHP/script file was uploaded and "
#         "executed via the web server, spawning system commands as www-data. "
#         "The web application has been fully compromised."
#     ),
# }


# def _resolve_family(hint: str, pred_family: str,
#                     probs: np.ndarray,
#                     class_names: list,
#                     prior_fails: int = 0) -> tuple[str, float]:

#     top_prob = float(np.max(probs))

#     # ssh_login — only R2L if it followed many failed attempts
#     if hint == "ssh_login":
#         if prior_fails >= 5:
#             r2l_prob = float(probs[class_names.index("R2L")])
#             return "R2L", max(r2l_prob + 0.20, 0.55)
#         else:
#             # clean login — trust the model
#             return pred_family, top_prob

#     # model confident — trust it
#     if top_prob >= _CONFIDENCE_THRESHOLD:
#         if hint == "ssh_brute_force" and pred_family == "DoS":
#             r2l_prob = float(probs[class_names.index("R2L")])
#             if r2l_prob > 0.02:
#                 return "R2L", max(r2l_prob + 0.30, 0.60)
#         if hint == "port_scan" and pred_family == "DoS":
#             probe_prob = float(probs[class_names.index("Probe")])
#             if probe_prob > 0.05:
#                 return "Probe", max(probe_prob + 0.20, 0.55)
#         return pred_family, top_prob

#     # model uncertain — use hint override
#     override = _HINT_FAMILY_OVERRIDE.get(hint)
#     if override:
#         override_idx  = class_names.index(override)
#         override_prob = float(probs[override_idx])
#         boosted       = max(override_prob + 0.30, 0.55)
#         return override, min(boosted, 0.95)

#     return pred_family, top_prob



# def _shap_features(shap_vec, feature_cols, raw_values, top_k=4):
#     pairs = sorted(zip(feature_cols, shap_vec, raw_values),
#                    key=lambda x: abs(x[1]), reverse=True)
#     result = []
#     for name, sv, orig in pairs[:top_k]:
#         result.append({
#             "feature":    name,
#             "shap_value": round(float(sv), 4),
#             "direction":  "up" if sv > 0 else "down",
#             "reason":     _DIRECTION_HINTS.get(
#                 name,
#                 f"{name}={orig} contributed {'+' if sv > 0 else ''}{sv:.3f}"
#             ),
#         })
#     return result


# def _counterfactuals(family: str, hint: str, shap_feats: list) -> list:
#     cf = []
#     top_feat = shap_feats[0]["feature"] if shap_feats else "count"

#     _CF_MAP = {
#         "DoS": [
#             {"change": f"If {top_feat} dropped to baseline, threat score would fall to LOW",
#              "outcome": "Low"},
#             {"change": "If source IP was rate-limited at the perimeter, attack would be mitigated",
#              "outcome": "Low"},
#         ],
#         "Probe": [
#             {"change": f"If connection count was under 5, score would fall to LOW",
#              "outcome": "Low"},
#             {"change": "If ports scanned were limited to known services, score would be MEDIUM",
#              "outcome": "Medium"},
#         ],
#         "R2L": [
#             {"change": f"If {top_feat} was within normal range, classification would shift to MEDIUM",
#              "outcome": "Medium"},
#             {"change": "If MFA was enforced, brute force would not result in access",
#              "outcome": "Low"},
#         ],
#         "U2R": [
#             {"change": "If sudo access was restricted to specific commands, escalation would fail",
#              "outcome": "Low"},
#             {"change": "If file integrity monitoring was active, rootkit installation would be detected",
#              "outcome": "Medium"},
#         ],
#         "Normal": [
#             {"change": "No significant threat factors — activity appears benign",
#              "outcome": "Benign"},
#         ],
#     }
#     return _CF_MAP.get(family, [
#         {"change": "Insufficient data to generate counterfactuals", "outcome": "Unknown"}
#     ])



# def _empty_result(filename: str) -> dict:
#     return {
#         "threat_score": 0.0,
#         "severity":     "low",
#         "summary":      f"No parseable log events found in {filename}.",
#         "shap":         [],
#         "events":       [],
#         "tokens_used":  0,
#         "duration_sec": 0.0,
#     }



# def analyze_log(raw_text: str, filename: str) -> dict:
#     art          = get_artifacts()
#     rf           = art["rf"]
#     scaler       = art["scaler"]
#     feature_cols = art["feature_cols"]
#     class_names  = art["class_names"]
#     explainer    = art["explainer"]
#     encoders     = art.get("encoders", {})

#     # 1. parse raw log
#     events = parse_log_file(raw_text)
#     if not events:
#         return _empty_result(filename)

#     # 2. feature matrix
#     X        = events_to_matrix(events, feature_cols, encoders)
#     X_scaled = scaler.transform(X)

#     # 3. model predictions
#     probs_all = rf.predict_proba(X_scaled)
#     pred_idxs = np.argmax(probs_all, axis=1)

#     # 4. resolve family with hint override
#     families    = []
#     confidences = []
#     for i, (ev, pred_idx) in enumerate(zip(events, pred_idxs)):
#         hint      = ev["meta"].get("event_hint", "")
#         pred_fam  = class_names[pred_idx]
#         prior_fails = int(ev["features"].get("num_failed_logins", 0))
#         fam, conf   = _resolve_family(hint, pred_fam, probs_all[i],
#                                     class_names, prior_fails)
#         # fam, conf = _resolve_family(hint, pred_fam, probs_all[i], class_names)
#         families.append(fam)
#         confidences.append(conf)

#         # debug
#         print(f"[DEBUG] Event {i}: hint={hint} → predicted={pred_fam} "
#               f"→ resolved={fam} ({conf:.2f}) "
#               f"probs={dict(zip(class_names, [f'{p:.2f}' for p in probs_all[i]]))}")

#     # 5. SHAP values
#     shap_vals = explainer.shap_values(X_scaled)
#     shap_arr  = np.array(shap_vals)  # (n_classes, n_events, n_features)

#     # 6. global SHAP summary
#     global_shap = np.mean(np.abs(shap_arr), axis=(0, 1))
#     top_global  = sorted(zip(feature_cols, global_shap),
#                          key=lambda x: x[1], reverse=True)[:5]
#     max_gs      = top_global[0][1] if top_global else 1.0
#     shap_summary = [
#         {
#             "feature": f,
#             "value":   round(float(v), 4),
#             "max_val": round(float(max_gs), 4),
#         }
#         for f, v in top_global
#     ]

#     # 7. overall threat score
#     attack_classes = [i for i, c in enumerate(class_names) if c != "Normal"]
#     threat_score   = float(np.max(probs_all[:, attack_classes]))
#     severity = (
#         "critical" if threat_score >= 0.80 else
#         "high"     if threat_score >= 0.60 else
#         "medium"   if threat_score >= 0.40 else
#         "low"
#     )

#     # 8. build output events
#     out_events = []
#     now        = datetime.utcnow()

#     for i, (ev, family) in enumerate(zip(events, families)):
#         meta       = ev["meta"]
#         raw_vals   = X[i]
#         conf       = confidences[i]
#         pred_idx   = class_names.index(family)
#         hint       = meta.get("event_hint", "unknown")

#         # SHAP vector for predicted class
#         if shap_arr.ndim == 3 and shap_arr.shape[0] == len(class_names):
#             sv_vec = shap_arr[pred_idx, i, :]
#         else:
#             sv_vec = shap_arr[i, :, pred_idx]

#         status, _  = _SEVERITY_MAP.get(family, ("MEDIUM", 0.5))
#         shap_feats = _shap_features(sv_vec, feature_cols, raw_vals)
#         cfs        = _counterfactuals(family, hint, shap_feats)
#         source_ip  = meta.get("source_ip") or "unknown"
#         username   = meta.get("username")  or "unknown"

#         # human readable attack type
#         attack_type = _HINT_TO_ATTACK_TYPE.get(hint, f"{family} — {hint.replace('_', ' ').title()}")

#         # verdict from template
#         template = _VERDICT_TEMPLATES.get(hint, "")
#         if template:
#             verdict = template.format(
#                 source_ip = source_ip,
#                 username  = username,
#                 count     = int(ev["features"].get("count", 1)),
#             )
#         else:
#             verdict = (
#                 f"Classified as {attack_type} (confidence {conf:.0%}). "
#                 f"Top signal: {shap_feats[0]['feature']} — "
#                 f"{shap_feats[0]['reason']}."
#                 if shap_feats
#                 else f"Classified as {attack_type} with confidence {conf:.0%}."
#             )

#         top_feat = shap_feats[0] if shap_feats else {}
#         neg_feat = next(
#             (f["feature"] for f in shap_feats if f["direction"] == "down"),
#             "logged_in"
#         )

#         out_events.append({
#             "event_id":   f"EVT-{str(uuid.uuid4())[:6].upper()}",
#             "timestamp":  now.strftime("%Y-%m-%d %H:%M:%S"),
#             "type":       attack_type,        # detailed e.g. "R2L — SSH Brute Force"
#             "family":     family,             # model family e.g. "R2L"
#             "score":      round(conf, 3),
#             "status":     status,
#             "source_ip":  source_ip,
#             "dest_ip":    "internal",
#             "username":   username,
#             "process":    hint,
#             "port":       meta.get("port", 0),
#             "protocol":   ev["features"].get("protocol_type", "tcp").upper(),
#             "bytes_sent": int(ev["features"].get("src_bytes", 0)),

#             "explanation": {
#                 "verdict":          verdict,
#                 "top_features":     shap_feats,
#                 "counter_factuals": cfs,
#                 "raw_evidence": {
#                     "source_ip":  source_ip,
#                     "dest_ip":    "internal",
#                     "username":   username,
#                     "process":    hint,
#                     "bytes_sent": int(ev["features"].get("src_bytes", 0)),
#                     "port":       meta.get("port", 0),
#                     "protocol":   ev["features"].get("protocol_type", "tcp"),
#                 },
#             },

#             "lime": shap_feats[0]["reason"] if shap_feats else "",
#             "pos":  top_feat.get("feature", ""),
#             "neg":  neg_feat,
#         })

#     # 9. summary
#     attack_types = [e["type"] for e in out_events if e["family"] != "Normal"]
#     unique_types = sorted(set(attack_types))
#     summary = (
#         f"Detected {len(attack_types)} threat event(s) in {filename}: "
#         + ", ".join(unique_types)
#         + f". Overall threat score: {threat_score:.2f}."
#         if attack_types
#         else f"No significant threats detected in {filename}."
#     )

#     return {
#         "threat_score": round(threat_score, 3),
#         "severity":     severity,
#         "summary":      summary,
#         "shap":         shap_summary,
#         "events":       out_events,
#         "tokens_used":  0,
#         "duration_sec": 0.0,
#     }


import uuid
import numpy as np
from datetime import datetime
from .loader import get_artifacts
from .log_parser import parse_log_file, events_to_matrix


# ── severity map by family ─────────────────────────────────────────────────────
_SEVERITY_MAP = {
    "DoS":    ("HIGH",     0.74),
    "Probe":  ("MEDIUM",   0.55),
    "R2L":    ("HIGH",     0.68),
    "U2R":    ("CRITICAL", 0.91),
    "Normal": ("LOW",      0.10),
}

# ── attack type labels ─────────────────────────────────────────────────────────
_HINT_TO_ATTACK_TYPE = {
    # DoS
    "dos_flood":            "DoS — Flood Attack",
    # Probe
    "port_scan":            "Probe — Port Scan",
    # R2L
    "ssh_brute_force":      "R2L — SSH Brute Force",
    "ftp_brute_force":      "R2L — FTP Brute Force",
    "data_exfiltration":    "R2L — Data Exfiltration",
    "ssh_login":            "Normal — Authenticated Session",
    # U2R
    "privilege_escalation": "U2R — Privilege Escalation",
    "backdoor_creation":    "U2R — Backdoor Creation",
    "rootkit_installation": "U2R — Rootkit Installation",
    "suid_manipulation":    "U2R — SUID Bit Manipulation",
    "persistence_crontab":  "U2R — Cron Persistence",
    "reverse_shell":        "U2R — Reverse Shell",
    "web_shell":            "U2R — Web Shell Execution",
    # Normal
    "unknown":              "Normal — Routine Activity",
}

# used when ssh_login resolves to R2L (followed brute force)
_R2L_LOGIN_LABEL = "R2L — Suspicious Remote Login"

# ── hint → family override ─────────────────────────────────────────────────────
_HINT_FAMILY_OVERRIDE = {
    "ssh_brute_force":      "R2L",
    "ftp_brute_force":      "R2L",
    "data_exfiltration":    "R2L",
    # ssh_login intentionally excluded — handled in _resolve_family
    "privilege_escalation": "U2R",
    "backdoor_creation":    "U2R",
    "rootkit_installation": "U2R",
    "suid_manipulation":    "U2R",
    "persistence_crontab":  "U2R",
    "reverse_shell":        "U2R",
    "web_shell":            "U2R",
    "dos_flood":            "DoS",
    "port_scan":            "Probe",
}

# ── confidence threshold ───────────────────────────────────────────────────────
_CONFIDENCE_THRESHOLD = 0.55

# ── human readable SHAP reasons ───────────────────────────────────────────────
_DIRECTION_HINTS = {
    "num_failed_logins":           "Multiple failed authentication attempts detected",
    "serror_rate":                 "High SYN error rate — possible port scan or flood",
    "srv_serror_rate":             "Service-level SYN error rate elevated",
    "rerror_rate":                 "Elevated REJ error rate — connections being refused",
    "srv_rerror_rate":             "Service-level REJ error rate elevated",
    "root_shell":                  "Root shell spawned — privilege escalation indicator",
    "su_attempted":                "su/sudo invocation detected outside normal pattern",
    "src_bytes":                   "Unusually large outbound data volume",
    "dst_bytes":                   "Unusually large inbound data volume",
    "count":                       "High connection count to same host",
    "srv_count":                   "High service connection count",
    "num_compromised":             "Compromised condition flags raised",
    "hot":                         "Hot indicators present in session",
    "logged_in":                   "Session authenticated successfully",
    "same_srv_rate":               "Traffic concentrated on single service",
    "diff_srv_rate":               "Traffic spread across multiple services — scanning",
    "srv_diff_host_rate":          "Service accessed from multiple hosts",
    "dst_host_count":              "High destination host connection count",
    "dst_host_srv_count":          "Number of distinct services accessed on destination host",
    "dst_host_serror_rate":        "Destination host showing high SYN error rate",
    "dst_host_srv_serror_rate":    "Destination service showing high SYN error rate",
    "dst_host_rerror_rate":        "Destination host showing high REJ error rate",
    "dst_host_srv_rerror_rate":    "Destination service showing high REJ error rate",
    "dst_host_same_srv_rate":      "All connections to same service — expected for dedicated accounts",
    "dst_host_diff_srv_rate":      "Destination accessing multiple services — lateral movement",
    "dst_host_same_src_port_rate": "Single consistent source port — typical of scripted connections",
    "dst_host_srv_diff_host_rate": "Service accessed from varied hosts — possible scanning",
    "num_shells":                  "Shell process spawned — possible command execution",
    "num_root":                    "Root-level operations detected",
    "num_access_files":            "Sensitive file access detected",
    "num_file_creations":          "Unusual file creation activity",
    "num_outbound_cmds":           "Outbound commands detected in session",
    "wrong_fragment":              "Malformed packet fragments — possible evasion",
    "urgent":                      "Urgent flag set — possible DoS signal",
    "land":                        "Source and destination IP/port match — rare anomaly",
    "service":                     "SSH service connection — standard remote access protocol",
    "protocol_type":               "Network protocol used for this connection",
    "flag":                        "TCP connection flag indicating connection state",
    "duration":                    "Connection duration — longer sessions may indicate data transfer",
    "is_host_login":               "Host login detected",
    "is_guest_login":              "Guest or anonymous login detected",
}

# ── verdict templates ──────────────────────────────────────────────────────────
_VERDICT_TEMPLATES = {
    "dos_flood": (
        "Classified as DoS — Flood Attack. High volume of connection attempts "
        "from {source_ip} caused connection table exhaustion and SYN flooding. "
        "This pattern matches automated denial-of-service tooling."
    ),
    "port_scan": (
        "Classified as Probe — Port Scan. Source {source_ip} probed multiple "
        "ports in rapid succession. This reconnaissance activity is consistent "
        "with automated scanning tools such as nmap or masscan."
    ),
    "ssh_brute_force": (
        "Classified as R2L — SSH Brute Force. Source {source_ip} attempted "
        "authentication {count} times against multiple usernames. "
        "This pattern is consistent with automated credential stuffing attacks."
    ),
    "ftp_brute_force": (
        "Classified as R2L — FTP Brute Force. Source {source_ip} made repeated "
        "failed FTP login attempts against multiple accounts. "
        "Possible credential dictionary attack in progress."
    ),
    "data_exfiltration": (
        "Classified as R2L — Data Exfiltration. User {username} transferred "
        "large volumes of data to an external host via curl/wget after gaining "
        "access. Sensitive files may have been compromised."
    ),
    "privilege_escalation": (
        "Classified as U2R — Privilege Escalation. User {username} invoked sudo "
        "to gain root access and accessed sensitive system files including "
        "/etc/shadow. Strong indicator of unauthorized privilege abuse."
    ),
    "backdoor_creation": (
        "Classified as U2R — Backdoor Creation. User {username} created a new "
        "system account with full sudo privileges and no password requirement. "
        "Persistent unauthorized access has been established."
    ),
    "rootkit_installation": (
        "Classified as U2R — Rootkit Installation. User {username} installed a "
        "shared library override and ran ldconfig to activate it. "
        "System binaries may be compromised."
    ),
    "suid_manipulation": (
        "Classified as U2R — SUID Manipulation. User {username} set the SUID bit "
        "on a binary allowing privilege escalation without sudo. "
        "This is a classic local privilege escalation technique."
    ),
    "persistence_crontab": (
        "Classified as U2R — Cron Persistence. User {username} added a cron job "
        "that periodically downloads and executes a remote payload. "
        "Command-and-control beacon has been established."
    ),
    "reverse_shell": (
        "Classified as U2R — Reverse Shell. A process on this host established "
        "an outbound connection to {source_ip} and attached a shell to it. "
        "The attacker has interactive remote code execution."
    ),
    "web_shell": (
        "Classified as U2R — Web Shell. A PHP/script file was uploaded and "
        "executed via the web server, spawning system commands as www-data. "
        "The web application has been fully compromised."
    ),
}

# ssh_login verdicts — family-dependent
_SSH_LOGIN_VERDICT_NORMAL = (
    "Normal authenticated session. User {username} logged in from {source_ip} "
    "using valid credentials with no prior failed attempts. "
    "Activity appears benign and consistent with routine access."
)
_SSH_LOGIN_VERDICT_R2L = (
    "Classified as R2L — Suspicious Remote Login. User {username} logged in "
    "from {source_ip} following prior failed authentication attempts. "
    "Possible successful brute force or stolen credential use."
)


# ── resolution logic ───────────────────────────────────────────────────────────

def _resolve_family(hint: str, pred_family: str,
                    probs: np.ndarray,
                    class_names: list,
                    prior_fails: int = 0) -> tuple[str, float]:
    """
    Returns (family, confidence).
    Trusts the model when confident.
    Falls back to hint-based override when model is uncertain.
    ssh_login is handled specially — only R2L when prior fails >= 5.
    """
    top_prob = float(np.max(probs))

    # ── ssh_login: only R2L if preceded by brute force ────────────
    if hint == "ssh_login":
        if prior_fails >= 5:
            r2l_prob = float(probs[class_names.index("R2L")])
            return "R2L", max(r2l_prob + 0.20, 0.55)
        # clean login — trust the model, default Normal if uncertain
        if top_prob < _CONFIDENCE_THRESHOLD:
            return "Normal", max(
                float(probs[class_names.index("Normal")]), 0.46
            )
        return pred_family, top_prob

    # ── model confident — trust it with corrections ───────────────
    if top_prob >= _CONFIDENCE_THRESHOLD:
        # fix DoS/R2L confusion for brute force
        if hint == "ssh_brute_force" and pred_family == "DoS":
            r2l_prob = float(probs[class_names.index("R2L")])
            if r2l_prob > 0.02:
                return "R2L", max(r2l_prob + 0.30, 0.60)
        # fix DoS/Probe confusion for port scan
        if hint == "port_scan" and pred_family == "DoS":
            probe_prob = float(probs[class_names.index("Probe")])
            if probe_prob > 0.05:
                return "Probe", max(probe_prob + 0.20, 0.55)
        return pred_family, top_prob

    # ── model uncertain — use hint override ───────────────────────
    override = _HINT_FAMILY_OVERRIDE.get(hint)
    if override:
        override_idx  = class_names.index(override)
        override_prob = float(probs[override_idx])
        boosted       = max(override_prob + 0.30, 0.55)
        return override, min(boosted, 0.95)

    return pred_family, top_prob


# ── SHAP helpers ───────────────────────────────────────────────────────────────

def _shap_features(shap_vec, feature_cols, raw_values, top_k=4):
    pairs = sorted(zip(feature_cols, shap_vec, raw_values),
                   key=lambda x: abs(x[1]), reverse=True)
    result = []
    for name, sv, orig in pairs[:top_k]:
        hint   = _DIRECTION_HINTS.get(name)
        reason = hint if hint else (
            f"{name} contributed {'+' if sv > 0 else ''}{sv:.3f}"
        )
        result.append({
            "feature":    name,
            "shap_value": round(float(sv), 4),
            "direction":  "up" if sv > 0 else "down",
            "reason":     reason,
        })
    return result


def _counterfactuals(family: str, hint: str, shap_feats: list) -> list:
    top_feat = shap_feats[0]["feature"] if shap_feats else "count"

    _CF_MAP = {
        "DoS": [
            {
                "change":  f"If {top_feat} dropped to baseline, "
                           "threat score would fall to LOW",
                "outcome": "Low",
            },
            {
                "change":  "If source IP was rate-limited at the perimeter, "
                           "attack would be mitigated",
                "outcome": "Low",
            },
        ],
        "Probe": [
            {
                "change":  "If connection count was under 5, "
                           "score would fall to LOW",
                "outcome": "Low",
            },
            {
                "change":  "If ports scanned were limited to known services, "
                           "score would be MEDIUM",
                "outcome": "Medium",
            },
        ],
        "R2L": [
            {
                "change":  f"If {top_feat} was within normal range, "
                           "classification would shift to MEDIUM",
                "outcome": "Medium",
            },
            {
                "change":  "If MFA was enforced, brute force would not "
                           "result in access",
                "outcome": "Low",
            },
        ],
        "U2R": [
            {
                "change":  "If sudo access was restricted to specific commands, "
                           "escalation would fail",
                "outcome": "Low",
            },
            {
                "change":  "If file integrity monitoring was active, "
                           "rootkit installation would be detected",
                "outcome": "Medium",
            },
        ],
        "Normal": [
            {
                "change":  "No significant threat factors — "
                           "activity appears benign",
                "outcome": "Benign",
            },
        ],
    }
    return _CF_MAP.get(family, [
        {
            "change":  "Insufficient data to generate counterfactuals",
            "outcome": "Unknown",
        }
    ])


# ── empty result ───────────────────────────────────────────────────────────────

def _empty_result(filename: str) -> dict:
    return {
        "threat_score": 0.0,
        "severity":     "low",
        "summary":      f"No parseable log events found in {filename}.",
        "shap":         [],
        "events":       [],
        "tokens_used":  0,
        "duration_sec": 0.0,
    }


# ── main entry point ───────────────────────────────────────────────────────────

def analyze_log(raw_text: str, filename: str) -> dict:
    art          = get_artifacts()
    rf           = art["rf"]
    scaler       = art["scaler"]
    feature_cols = art["feature_cols"]
    class_names  = art["class_names"]
    explainer    = art["explainer"]
    encoders     = art.get("encoders", {})

    # 1. parse raw log
    events = parse_log_file(raw_text)
    if not events:
        return _empty_result(filename)

    # 2. feature matrix
    X        = events_to_matrix(events, feature_cols, encoders)
    X_scaled = scaler.transform(X)

    # 3. model predictions
    probs_all = rf.predict_proba(X_scaled)
    pred_idxs = np.argmax(probs_all, axis=1)

    # 4. resolve family with hint override
    families    = []
    confidences = []
    for i, (ev, pred_idx) in enumerate(zip(events, pred_idxs)):
        hint        = ev["meta"].get("event_hint", "")
        pred_fam    = class_names[pred_idx]
        prior_fails = int(ev["features"].get("num_failed_logins", 0))
        fam, conf   = _resolve_family(
            hint, pred_fam, probs_all[i], class_names, prior_fails
        )
        families.append(fam)
        confidences.append(conf)

        print(
            f"[DEBUG] Event {i}: hint={hint} → predicted={pred_fam} "
            f"→ resolved={fam} ({conf:.2f}) "
            f"probs={dict(zip(class_names, [f'{p:.2f}' for p in probs_all[i]]))}"
        )

    # 5. SHAP values
    shap_vals = explainer.shap_values(X_scaled)
    shap_arr  = np.array(shap_vals)  # (n_classes, n_events, n_features)

    # 6. global SHAP summary
    global_shap = np.mean(np.abs(shap_arr), axis=(0, 1))
    top_global  = sorted(zip(feature_cols, global_shap),
                         key=lambda x: x[1], reverse=True)[:5]
    max_gs      = top_global[0][1] if top_global else 1.0
    shap_summary = [
        {
            "feature": f,
            "value":   round(float(v), 4),
            "max_val": round(float(max_gs), 4),
        }
        for f, v in top_global
    ]

    # 7. overall threat score
    attack_classes = [i for i, c in enumerate(class_names) if c != "Normal"]
    threat_score   = float(np.max(probs_all[:, attack_classes]))
    severity = (
        "critical" if threat_score >= 0.80 else
        "high"     if threat_score >= 0.60 else
        "medium"   if threat_score >= 0.40 else
        "low"
    )

    # 8. build output events
    out_events = []
    now        = datetime.utcnow()

    for i, (ev, family) in enumerate(zip(events, families)):
        meta        = ev["meta"]
        raw_vals    = X[i]
        conf        = confidences[i]
        pred_idx    = class_names.index(family)
        hint        = meta.get("event_hint", "unknown")
        source_ip   = meta.get("source_ip") or "unknown"
        username    = meta.get("username")  or "unknown"

        # SHAP vector for resolved class
        if shap_arr.ndim == 3 and shap_arr.shape[0] == len(class_names):
            sv_vec = shap_arr[pred_idx, i, :]
        else:
            sv_vec = shap_arr[i, :, pred_idx]

        status, _  = _SEVERITY_MAP.get(family, ("MEDIUM", 0.5))
        shap_feats = _shap_features(sv_vec, feature_cols, raw_vals)
        cfs        = _counterfactuals(family, hint, shap_feats)

        # ── attack type label (family-aware for ssh_login) ────────
        if hint == "ssh_login":
            attack_type = (
                _R2L_LOGIN_LABEL
                if family == "R2L"
                else "Normal — Authenticated Session"
            )
        else:
            attack_type = _HINT_TO_ATTACK_TYPE.get(
                hint,
                f"{family} — {hint.replace('_', ' ').title()}"
            )

        # ── verdict (family-aware for ssh_login) ──────────────────
        if hint == "ssh_login":
            template = (
                _SSH_LOGIN_VERDICT_R2L
                if family == "R2L"
                else _SSH_LOGIN_VERDICT_NORMAL
            )
            verdict = template.format(
                source_ip=source_ip,
                username=username,
            )
        elif hint in _VERDICT_TEMPLATES:
            verdict = _VERDICT_TEMPLATES[hint].format(
                source_ip=source_ip,
                username=username,
                count=int(ev["features"].get("count", 1)),
            )
        else:
            verdict = (
                f"Classified as {attack_type} (confidence {conf:.0%}). "
                f"Top signal: {shap_feats[0]['feature']} — "
                f"{shap_feats[0]['reason']}."
                if shap_feats
                else f"Classified as {attack_type} with confidence {conf:.0%}."
            )

        top_feat = shap_feats[0] if shap_feats else {}
        neg_feat = next(
            (f["feature"] for f in shap_feats if f["direction"] == "down"),
            "logged_in",
        )

        out_events.append({
            "event_id":   f"EVT-{str(uuid.uuid4())[:6].upper()}",
            "timestamp":  now.strftime("%Y-%m-%d %H:%M:%S"),
            "type":       attack_type,
            "family":     family,
            "score":      round(conf, 3),
            "status":     status,
            "source_ip":  source_ip,
            "dest_ip":    "internal",
            "username":   username,
            "process":    hint,
            "port":       meta.get("port", 0),
            "protocol":   ev["features"].get("protocol_type", "tcp").upper(),
            "bytes_sent": int(ev["features"].get("src_bytes", 0)),

            "explanation": {
                "verdict":          verdict,
                "top_features":     shap_feats,
                "counter_factuals": cfs,
                "raw_evidence": {
                    "source_ip":  source_ip,
                    "dest_ip":    "internal",
                    "username":   username,
                    "process":    hint,
                    "bytes_sent": int(ev["features"].get("src_bytes", 0)),
                    "port":       meta.get("port", 0),
                    "protocol":   ev["features"].get("protocol_type", "tcp"),
                },
            },

            "lime": shap_feats[0]["reason"] if shap_feats else "",
            "pos":  top_feat.get("feature", ""),
            "neg":  neg_feat,
        })

    # 9. summary
    attack_events = [e for e in out_events if e["family"] != "Normal"]
    normal_events = [e for e in out_events if e["family"] == "Normal"]
    unique_types  = sorted(set(e["type"] for e in attack_events))

    summary = (
        f"Detected {len(attack_events)} threat event(s) and "
        f"{len(normal_events)} normal event(s) in {filename}: "
        + ", ".join(unique_types)
        + f". Overall threat score: {threat_score:.2f}."
        if attack_events
        else f"No significant threats detected in {filename}. "
             f"{len(normal_events)} normal event(s) identified."
    )

    return {
        "threat_score": round(threat_score, 3),
        "severity":     severity,
        "summary":      summary,
        "shap":         shap_summary,
        "events":       out_events,
        "tokens_used":  0,
        "duration_sec": 0.0,
    }