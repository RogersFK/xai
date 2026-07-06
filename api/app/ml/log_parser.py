# import re
# import numpy as np
# from collections import defaultdict

# _FEATURE_DEFAULTS = {
#     "duration": 0, "protocol_type": "tcp", "service": "other", "flag": "SF",
#     "src_bytes": 0, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
#     "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0,
#     "root_shell": 0, "su_attempted": 0, "num_root": 0, "num_file_creations": 0,
#     "num_shells": 0, "num_access_files": 0, "num_outbound_cmds": 0,
#     "is_host_login": 0, "is_guest_login": 0, "count": 1, "srv_count": 1,
#     "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 0.0,
#     "srv_rerror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0,
#     "srv_diff_host_rate": 0.0, "dst_host_count": 1, "dst_host_srv_count": 1,
#     "dst_host_same_srv_rate": 1.0, "dst_host_diff_srv_rate": 0.0,
#     "dst_host_same_src_port_rate": 0.0, "dst_host_srv_diff_host_rate": 0.0,
#     "dst_host_serror_rate": 0.0, "dst_host_srv_serror_rate": 0.0,
#     "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0,
# }

# _PATTERNS = {
#     "ssh_fail":   re.compile(r"Failed (password|publickey) for (?:invalid user )?(\S+) from ([\d.]+) port (\d+)", re.I),
#     "ssh_accept": re.compile(r"Accepted (password|publickey) for (\S+) from ([\d.]+)", re.I),
#     "sudo":       re.compile(r"sudo.*USER=(\S+).*COMMAND=(.*)", re.I),
#     "su_attempt": re.compile(r"\bsu\b.*to (\S+)", re.I),
#     "repeated":   re.compile(r"message repeated (\d+) times", re.I),
#     "syslog_ip":  re.compile(r"from ([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})"),
#     "port":       re.compile(r"port (\d+)"),
#     "bytes":      re.compile(r"(\d+)\s*bytes"),
#     "shadow":     re.compile(r"/etc/shadow|/etc/passwd|/etc/sudoers", re.I),
#     "shell_cmd":  re.compile(r"COMMAND=.*(bash|sh|zsh|ksh|csh)\b", re.I),
#     "curl_wget":  re.compile(r"COMMAND=.*(curl|wget|nc|netcat)\b", re.I),
#     "useradd":    re.compile(r"COMMAND=.*(useradd|usermod|adduser)\b", re.I),
#     "tar_zip":    re.compile(r"COMMAND=.*(tar|zip|gzip|7z)\b", re.I),
# }


# def parse_log_file(raw_text: str) -> list[dict]:
#     lines = raw_text.splitlines()

#     # ── pass 1: count per-IP activity ────────────────────────────
#     ip_fail_counts   = defaultdict(int)
#     ip_lines         = defaultdict(list)
#     ip_sudo_counts   = defaultdict(int)
#     ip_users         = defaultdict(set)

#     for line in lines:
#         # handle "message repeated N times" — expand the count
#         rep = _PATTERNS["repeated"].search(line)
#         repeat_factor = int(rep.group(1)) if rep else 1

#         m = _PATTERNS["syslog_ip"].search(line)
#         ip = m.group(1) if m else "local"

#         ip_lines[ip].append(line)

#         if _PATTERNS["ssh_fail"].search(line):
#             ip_fail_counts[ip] += repeat_factor

#         if _PATTERNS["sudo"].search(line):
#             ip_sudo_counts[ip] += 1

#         mf = _PATTERNS["ssh_fail"].search(line)
#         if mf:
#             ip_users[ip].add(mf.group(2))

#     # ── pass 2: build one event per significant IP/action ────────
#     events       = []
#     processed    = set()

#     for line in lines:
#         feat = dict(_FEATURE_DEFAULTS)
#         meta = {"raw_line": line, "source_ip": None,
#                 "username": None, "event_hint": None}

#         # ── SSH brute force ───────────────────────────────────────
#         m = _PATTERNS["ssh_fail"].search(line)
#         if m:
#             _, username, src_ip, port = m.groups()
#             key = ("fail", src_ip)
#             if key in processed:
#                 continue
#             processed.add(key)

#             rep   = _PATTERNS["repeated"].search(line)
#             extra = int(rep.group(1)) if rep else 0
#             fail_count = ip_fail_counts[src_ip] + extra
#             unique_users = len(ip_users[src_ip])

#             # strong R2L / brute-force signal
#             serror   = min(fail_count / (fail_count + 1), 0.99)
#             rerror   = min(fail_count / 100, 0.99)
#             rej_flag = "REJ" if fail_count > 10 else "S0"

#             feat.update({
#                 "protocol_type":           "tcp",
#                 "service":                 "ssh",
#                 "flag":                    rej_flag,
#                 "num_failed_logins":       min(fail_count, 5),
#                 "logged_in":               0,
#                 "count":                   min(fail_count, 511),
#                 "srv_count":               min(fail_count, 511),
#                 "serror_rate":             serror,
#                 "srv_serror_rate":         serror,
#                 "rerror_rate":             rerror,
#                 "srv_rerror_rate":         rerror,
#                 "diff_srv_rate":           min(unique_users / 10, 1.0),
#                 "dst_host_count":          min(fail_count, 255),
#                 "dst_host_srv_count":      min(fail_count, 255),
#                 "dst_host_serror_rate":    serror,
#                 "dst_host_srv_serror_rate":serror,
#                 "dst_host_rerror_rate":    rerror,
#                 "same_srv_rate":           max(1.0 - serror, 0.01),
#                 "hot":                     min(fail_count // 10, 30),
#             })
#             meta.update({
#                 "source_ip":  src_ip,
#                 "username":   username,
#                 "port":       int(port),
#                 "event_hint": "ssh_brute_force",
#             })
#             events.append({"features": feat, "meta": meta})
#             continue

#         # ── successful SSH login ──────────────────────────────────
#         m = _PATTERNS["ssh_accept"].search(line)
#         if m:
#             _, username, src_ip = m.groups()
#             key = ("accept", src_ip, username)
#             if key in processed:
#                 continue
#             processed.add(key)

#             prior_fails = ip_fail_counts.get(src_ip, 0)
#             feat.update({
#                 "protocol_type":   "tcp",
#                 "service":         "ssh",
#                 "flag":            "SF",
#                 "logged_in":       1,
#                 "num_failed_logins": min(prior_fails, 5),
#                 "is_guest_login":  1 if username in ("guest", "anonymous") else 0,
#                 "count":           max(prior_fails, 1),
#                 "srv_count":       max(prior_fails, 1),
#                 "hot":             2 if prior_fails > 0 else 0,
#             })
#             meta.update({
#                 "source_ip":  src_ip,
#                 "username":   username,
#                 "event_hint": "ssh_login",
#             })
#             events.append({"features": feat, "meta": meta})
#             continue

#         # ── sudo / privilege escalation ───────────────────────────
#         m = _PATTERNS["sudo"].search(line)
#         if m:
#             target_user, command = m.groups()
#             key = ("sudo", command.strip()[:60])
#             if key in processed:
#                 continue
#             processed.add(key)

#             is_shadow   = bool(_PATTERNS["shadow"].search(line))
#             is_shell    = bool(_PATTERNS["shell_cmd"].search(line))
#             is_exfil    = bool(_PATTERNS["curl_wget"].search(line))
#             is_useradd  = bool(_PATTERNS["useradd"].search(line))
#             is_archive  = bool(_PATTERNS["tar_zip"].search(line))

#             src_ip_m = _PATTERNS["syslog_ip"].search(line)
#             src_ip   = src_ip_m.group(1) if src_ip_m else "local"

#             bytes_m  = _PATTERNS["bytes"].search(line)
#             bsent    = int(bytes_m.group(1)) if bytes_m else 0

#             feat.update({
#                 "protocol_type":    "tcp",
#                 "service":          "shell" if is_shell else "ssh",
#                 "flag":             "SF",
#                 "logged_in":        1,
#                 "su_attempted":     1,
#                 "root_shell":       1 if target_user == "root" or is_shell else 0,
#                 "num_shells":       1 if is_shell else 0,
#                 "num_root":         1 if target_user == "root" else 0,
#                 "num_access_files": 1 if is_shadow else 0,
#                 "num_compromised":  3 if is_shadow else (2 if is_shell else 1),
#                 "num_file_creations": 1 if is_archive else 0,
#                 "hot":              min(
#                     4 * int(is_shadow) + 3 * int(is_shell) +
#                     3 * int(is_exfil)  + 2 * int(is_useradd) +
#                     2 * int(is_archive), 30
#                 ),
#                 "src_bytes":        bsent,
#                 "count":            ip_sudo_counts.get(src_ip, 1),
#                 "srv_count":        ip_sudo_counts.get(src_ip, 1),
#                 "diff_srv_rate":    0.5 if is_exfil else 0.1,
#                 "dst_host_diff_srv_rate": 0.5 if is_exfil else 0.0,
#             })
#             meta.update({
#                 "source_ip":  src_ip,
#                 "username":   target_user,
#                 "event_hint": (
#                     "data_exfiltration"  if is_exfil  else
#                     "backdoor_creation"  if is_useradd else
#                     "privilege_escalation"
#                 ),
#                 "command": command.strip(),
#             })
#             events.append({"features": feat, "meta": meta})

#     return events


# def events_to_matrix(events: list[dict], feature_cols: list[str],
#                      encoders: dict) -> np.ndarray:

#     _PROTOCOL_MAP = {"tcp": 2, "udp": 1, "icmp": 0}
#     _SERVICE_MAP  = {
#         "ssh": 58, "ftp": 20, "http": 27, "smtp": 54, "shell": 50,
#         "telnet": 61, "domain_u": 16, "other": 39, "private": 44,
#     }
#     _FLAG_MAP = {
#         "SF": 9, "S0": 5, "REJ": 4, "RSTO": 6, "SH": 8,
#         "RSTR": 7, "S1": 2, "S2": 3, "S3": 1, "OTH": 0,
#     }
#     _FALLBACK = {
#         "protocol_type": _PROTOCOL_MAP,
#         "service":       _SERVICE_MAP,
#         "flag":          _FLAG_MAP,
#     }

#     rows = []
#     for ev in events:
#         feat = ev["features"]
#         row  = []
#         for col in feature_cols:
#             val = feat.get(col, 0)

#             if col in encoders:
#                 le  = encoders[col]
#                 val = str(val)
#                 val = le.transform([val])[0] if val in le.classes_ else -1
#             elif col in _FALLBACK:
#                 val = _FALLBACK[col].get(str(val), -1)
#             else:
#                 try:
#                     val = float(val)
#                 except (ValueError, TypeError):
#                     val = 0.0

#             row.append(float(val))
#         rows.append(row)

#     return np.array(rows, dtype=np.float32)



import re
import numpy as np
from collections import defaultdict

_FEATURE_DEFAULTS = {
    "duration": 0, "protocol_type": "tcp", "service": "other", "flag": "SF",
    "src_bytes": 0, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
    "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0,
    "root_shell": 0, "su_attempted": 0, "num_root": 0, "num_file_creations": 0,
    "num_shells": 0, "num_access_files": 0, "num_outbound_cmds": 0,
    "is_host_login": 0, "is_guest_login": 0, "count": 1, "srv_count": 1,
    "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 0.0,
    "srv_rerror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0,
    "srv_diff_host_rate": 0.0, "dst_host_count": 1, "dst_host_srv_count": 1,
    "dst_host_same_srv_rate": 1.0, "dst_host_diff_srv_rate": 0.0,
    "dst_host_same_src_port_rate": 0.0, "dst_host_srv_diff_host_rate": 0.0,
    "dst_host_serror_rate": 0.0, "dst_host_srv_serror_rate": 0.0,
    "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0,
}

_P = {
    # auth
    "ssh_fail":    re.compile(
        r"Failed (password|publickey) for (?:invalid user )?(\S+) from ([\d.]+) port (\d+)", re.I),
    "ssh_accept":  re.compile(
        r"Accepted (password|publickey) for (\S+) from ([\d.]+)", re.I),
    "repeated":    re.compile(r"message repeated (\d+) times", re.I),
    "ftp_fail":    re.compile(r"FAIL LOGIN.*Client.*?([\d.]+).*user.*?(\S+)", re.I),

    # privilege escalation / sudo
    "sudo":        re.compile(r"sudo.*?USER=(\S+).*?COMMAND=(.*)", re.I),
    "su_attempt":  re.compile(r"\bsu\b.*to (\S+)", re.I),

    # sensitive file access
    "shadow":      re.compile(r"/etc/shadow|/etc/passwd|/etc/sudoers|\.ssh|\.pem|\.key|\.env", re.I),
    "shell_cmd":   re.compile(r"COMMAND=.*?(/bin/bash|/bin/sh|/bin/zsh|/bin/ksh|/bin/csh)\b", re.I),
    "reverse_shell": re.compile(r"socket.*connect|dup2.*fileno|subprocess.*shell|nc\s+-e|/bin/sh.*-i", re.I),
    "exfil_cmd":   re.compile(r"COMMAND=.*(curl|wget|nc\b|netcat)\s.*http", re.I),
    "useradd_cmd": re.compile(r"COMMAND=.*(useradd|usermod|adduser)\b", re.I),
    "archive_cmd": re.compile(r"COMMAND=.*(tar|zip|gzip|7z)\b", re.I),
    "chmod_suid":  re.compile(r"COMMAND=.*chmod\s.*[+]s|COMMAND=.*chmod\s+4[0-9]{3}", re.I),
    "crontab_cmd": re.compile(r"COMMAND=.*(crontab|/var/spool/cron)", re.I),
    "find_suid":   re.compile(r"COMMAND=.*find.*-perm.*-[0-9]*4000", re.I),
    "ldconfig":    re.compile(r"COMMAND=.*(ldconfig|/lib/.*\.so)", re.I),

    # DoS signals
    "syn_flood":   re.compile(r"SYN flood|possible SYN flooding", re.I),
    "conntrack":   re.compile(r"nf_conntrack.*table full|dropping packet", re.I),
    "udp_flood":   re.compile(r"UDP flood", re.I),

    # probe / port scan
    "port_scan":   re.compile(r"port scan|portsweep|nmap|satan|mscan", re.I),

    # web shell
    "web_shell":   re.compile(r"POST.*\.(php|asp|aspx|jsp|cgi).*200", re.I),

    # generic
    "syslog_ip":   re.compile(r"from ([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})"),
    "any_ip":      re.compile(r"([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})"),
    "port":        re.compile(r"port (\d+)"),
    "bytes":       re.compile(r"(\d+)\s*bytes"),
}



def _scan_lines(lines: list[str]) -> tuple[dict, dict, dict, dict, dict, set]:
    ip_fail_counts  = defaultdict(int)
    ip_sudo_counts  = defaultdict(int)
    ip_users        = defaultdict(set)
    ip_ports        = defaultdict(set)
    ip_lines        = defaultdict(list)
    dos_ips         = set()

    for line in lines:
        # expand "repeated N times"
        rep = _P["repeated"].search(line)
        repeat = int(rep.group(1)) if rep else 1

        # DoS signals
        if _P["syn_flood"].search(line) or _P["conntrack"].search(line) or _P["udp_flood"].search(line):
            m = _P["any_ip"].search(line)
            if m:
                dos_ips.add(m.group(1))

        # SSH failures
        m = _P["ssh_fail"].search(line)
        if m:
            _, username, src_ip, port = m.groups()
            ip_fail_counts[src_ip] += repeat
            ip_users[src_ip].add(username)
            ip_ports[src_ip].add(port)

        # FTP failures
        m = _P["ftp_fail"].search(line)
        if m:
            src_ip, username = m.group(1), m.group(2)
            ip_fail_counts[src_ip] += repeat
            ip_users[src_ip].add(username)

        # Sudo
        m = _P["sudo"].search(line)
        if m:
            src_m = _P["syslog_ip"].search(line)
            ip    = src_m.group(1) if src_m else "local"
            ip_sudo_counts[ip] += 1

        ip_m = _P["any_ip"].search(line)
        if ip_m:
            ip_lines[ip_m.group(1)].append(line)

    return ip_fail_counts, ip_sudo_counts, ip_users, ip_ports, ip_lines, dos_ips



def _make_dos_event(src_ip: str, fail_count: int) -> dict:
    feat = dict(_FEATURE_DEFAULTS)
    # DoS profile: high count, high serror, REJ flag, UDP/ICMP mix
    serror = min(fail_count / (fail_count + 1), 0.99)
    feat.update({
        "protocol_type":            "tcp",
        "service":                  "http",
        "flag":                     "S0",
        "count":                    min(fail_count, 511),
        "srv_count":                min(fail_count, 511),
        "serror_rate":              serror,
        "srv_serror_rate":          serror,
        "rerror_rate":              0.0,
        "same_srv_rate":            0.99,
        "diff_srv_rate":            0.01,
        "dst_host_count":           min(fail_count, 255),
        "dst_host_srv_count":       min(fail_count, 255),
        "dst_host_serror_rate":     serror,
        "dst_host_srv_serror_rate": serror,
        "dst_host_rerror_rate":     0.0,
        "num_failed_logins":        0,
        "logged_in":                0,
        "hot":                      0,
        "wrong_fragment":           min(fail_count // 100, 3),
        "urgent":                   1 if fail_count > 200 else 0,
    })
    return {
        "features": feat,
        "meta": {
            "source_ip":  src_ip,
            "username":   "unknown",
            "event_hint": "dos_flood",
            "port":       80,
        }
    }


def _make_probe_event(src_ip: str, ports: set, fail_count: int) -> dict:
    feat = dict(_FEATURE_DEFAULTS)
    n_ports      = len(ports)
    rerror       = min(n_ports / 30, 0.99)
    diff_srv     = min(n_ports / 20, 0.99)
    serror       = min(fail_count / (fail_count + n_ports + 1), 0.5)

    feat.update({
        "protocol_type":                "tcp",
        "service":                      "private",
        "flag":                         "REJ",
        "count":                        min(n_ports * 3, 511),
        "srv_count":                    min(n_ports, 511),
        "serror_rate":                  serror,
        "srv_serror_rate":              serror,
        "rerror_rate":                  rerror,
        "srv_rerror_rate":              rerror,
        "same_srv_rate":                max(1.0 - diff_srv, 0.01),
        "diff_srv_rate":                diff_srv,
        "srv_diff_host_rate":           min(n_ports / 25, 0.99),
        "dst_host_count":               min(n_ports * 5, 255),
        "dst_host_srv_count":           min(n_ports, 255),
        "dst_host_same_srv_rate":       max(1.0 - diff_srv, 0.01),
        "dst_host_diff_srv_rate":       diff_srv,
        "dst_host_serror_rate":         serror,
        "dst_host_srv_serror_rate":     serror,
        "dst_host_rerror_rate":         rerror,
        "dst_host_srv_rerror_rate":     rerror,
        "dst_host_same_src_port_rate":  0.01,
        "num_failed_logins":            min(fail_count, 5),
        "logged_in":                    0,
        "hot":                          0,
    })
    return {
        "features": feat,
        "meta": {
            "source_ip":  src_ip,
            "username":   "unknown",
            "event_hint": "port_scan",
            "port":       0,
        }
    }


def _make_brute_force_event(src_ip: str, fail_count: int,
                             unique_users: int, port: int) -> dict:
    feat     = dict(_FEATURE_DEFAULTS)
    serror   = min(fail_count / (fail_count + 1), 0.99)
    rerror   = min(fail_count / 100, 0.99)
    rej_flag = "REJ" if fail_count > 10 else "S0"

    feat.update({
        "protocol_type":            "tcp",
        "service":                  "ssh",
        "flag":                     rej_flag,
        "num_failed_logins":        min(fail_count, 5),
        "logged_in":                0,
        "count":                    min(fail_count, 511),
        "srv_count":                min(fail_count, 511),
        "serror_rate":              serror,
        "srv_serror_rate":          serror,
        "rerror_rate":              rerror,
        "srv_rerror_rate":          rerror,
        "diff_srv_rate":            min(unique_users / 10, 0.99),
        "same_srv_rate":            max(1.0 - serror, 0.01),
        "dst_host_count":           min(fail_count, 255),
        "dst_host_srv_count":       min(fail_count, 255),
        "dst_host_serror_rate":     serror,
        "dst_host_srv_serror_rate": serror,
        "dst_host_rerror_rate":     rerror,
        "dst_host_same_src_port_rate": 0.01,
        "hot":                      min(fail_count // 10, 30),
    })
    return {
        "features": feat,
        "meta": {
            "source_ip":  src_ip,
            "username":   "unknown",
            "event_hint": "ssh_brute_force",
            "port":       port,
        }
    }


def _make_sudo_event(src_ip: str, target_user: str,
                     command: str, sudo_count: int,
                     bytes_sent: int) -> dict:
    feat = dict(_FEATURE_DEFAULTS)

    is_shadow      = bool(_P["shadow"].search(command))
    is_shell       = bool(_P["shell_cmd"].search(command))
    is_rev_shell   = bool(_P["reverse_shell"].search(command))
    is_exfil       = bool(_P["exfil_cmd"].search(command))
    is_useradd     = bool(_P["useradd_cmd"].search(command))
    is_archive     = bool(_P["archive_cmd"].search(command))
    is_chmod_suid  = bool(_P["chmod_suid"].search(command))
    is_crontab     = bool(_P["crontab_cmd"].search(command))
    is_find_suid   = bool(_P["find_suid"].search(command))
    is_ldconfig    = bool(_P["ldconfig"].search(command))

    hot = (
        4 * int(is_shadow)     +
        3 * int(is_shell)      +
        4 * int(is_rev_shell)  +
        3 * int(is_exfil)      +
        3 * int(is_useradd)    +
        2 * int(is_archive)    +
        3 * int(is_chmod_suid) +
        2 * int(is_crontab)    +
        2 * int(is_find_suid)  +
        2 * int(is_ldconfig)
    )

    feat.update({
        "protocol_type":     "tcp",
        "service":           "shell" if (is_shell or is_rev_shell) else "ssh",
        "flag":              "SF",
        "logged_in":         1,
        "su_attempted":      1,
        "root_shell":        1 if (target_user == "root" or is_shell or is_rev_shell) else 0,
        "num_shells":        1 if (is_shell or is_rev_shell) else 0,
        "num_root":          1 if target_user == "root" else 0,
        "num_access_files":  1 if is_shadow else 0,
        "num_compromised":   min(
            int(is_shadow) * 3 + int(is_shell) * 2 +
            int(is_rev_shell) * 4 + int(is_exfil) * 2 +
            int(is_useradd) * 3 + int(is_chmod_suid) * 3, 10
        ),
        "num_file_creations": 1 if (is_archive or is_useradd) else 0,
        "hot":               min(hot, 30),
        "src_bytes":         bytes_sent,
        "count":             max(sudo_count, 1),
        "srv_count":         max(sudo_count, 1),
        "diff_srv_rate":     0.5 if (is_exfil or is_rev_shell) else 0.1,
        "dst_host_diff_srv_rate": 0.5 if (is_exfil or is_rev_shell) else 0.0,
        "dst_host_srv_diff_host_rate": 0.3 if is_rev_shell else 0.0,
    })

    hint = (
        "reverse_shell"        if is_rev_shell   else
        "data_exfiltration"    if is_exfil        else
        "backdoor_creation"    if is_useradd       else
        "rootkit_installation" if is_ldconfig      else
        "suid_manipulation"    if is_chmod_suid    else
        "persistence_crontab"  if is_crontab       else
        "privilege_escalation"
    )

    return {
        "features": feat,
        "meta": {
            "source_ip":  src_ip,
            "username":   target_user,
            "event_hint": hint,
            "command":    command.strip(),
            "port":       22,
        }
    }


def _make_login_event(src_ip: str, username: str,
                       prior_fails: int) -> dict:
    feat = dict(_FEATURE_DEFAULTS)
    feat.update({
        "protocol_type":     "tcp",
        "service":           "ssh",
        "flag":              "SF",
        "logged_in":         1,
        "num_failed_logins": min(prior_fails, 5),
        "is_guest_login":    1 if username in ("guest", "anonymous") else 0,
        "count":             max(prior_fails, 1),
        "srv_count":         max(prior_fails, 1),
        "hot":               2 if prior_fails > 0 else 0,
        "serror_rate":       min(prior_fails / 100, 0.5),
        "rerror_rate":       min(prior_fails / 200, 0.3),
        "dst_host_count":    max(prior_fails, 1),
        "dst_host_srv_count":max(prior_fails, 1),
    })
    return {
        "features": feat,
        "meta": {
            "source_ip":  src_ip,
            "username":   username,
            "event_hint": "ssh_login",
            "port":       22,
        }
    }



def parse_log_file(raw_text: str) -> list[dict]:
    lines = [l for l in raw_text.splitlines()
             if l.strip() and not l.strip().startswith("#")]

    (ip_fail_counts, ip_sudo_counts,
     ip_users, ip_ports,
     ip_lines, dos_ips) = _scan_lines(lines)

    events      = []
    processed   = set()

    for ip in dos_ips:
        key = ("dos", ip)
        if key in processed:
            continue
        processed.add(key)
        fail_count = ip_fail_counts.get(ip, 100)
        events.append(_make_dos_event(ip, max(fail_count, 100)))

    for ip, ports in ip_ports.items():
        if len(ports) >= 8 and ip not in dos_ips:
            key = ("probe", ip)
            if key in processed:
                continue
            processed.add(key)
            events.append(_make_probe_event(
                ip, ports, ip_fail_counts.get(ip, len(ports))
            ))

    for line in lines:
        m = _P["ssh_fail"].search(line)
        if not m:
            m2 = _P["ftp_fail"].search(line)
            if not m2:
                continue
            src_ip   = m2.group(1)
            username = m2.group(2)
            port_val = 21
        else:
            _, username, src_ip, port_str = m.groups()
            port_val = int(port_str)

        # skip if already handled as probe or DoS
        if ("probe", src_ip) in processed or ("dos", src_ip) in processed:
            continue

        key = ("fail", src_ip)
        if key in processed:
            continue
        processed.add(key)

        rep         = _P["repeated"].search(line)
        extra       = int(rep.group(1)) if rep else 0
        fail_count  = ip_fail_counts.get(src_ip, 0) + extra
        unique_users = len(ip_users.get(src_ip, {username}))

        if fail_count >= 3:
            events.append(_make_brute_force_event(
                src_ip, fail_count, unique_users, port_val
            ))

    for line in lines:
        m = _P["ssh_accept"].search(line)
        if not m:
            continue
        _, username, src_ip = m.groups()
        key = ("accept", src_ip, username)
        if key in processed:
            continue
        processed.add(key)
        prior_fails = ip_fail_counts.get(src_ip, 0)
        events.append(_make_login_event(src_ip, username, prior_fails))

    for line in lines:
        m = _P["sudo"].search(line)
        if not m:
            # web shell POST
            if _P["web_shell"].search(line):
                ip_m = _P["any_ip"].search(line)
                src_ip = ip_m.group(1) if ip_m else "unknown"
                key = ("webshell", src_ip)
                if key not in processed:
                    processed.add(key)
                    feat = dict(_FEATURE_DEFAULTS)
                    feat.update({
                        "protocol_type": "tcp", "service": "http",
                        "flag": "SF", "logged_in": 1,
                        "hot": 8, "num_compromised": 4,
                        "num_shells": 1, "root_shell": 1,
                        "count": 10, "srv_count": 10,
                    })
                    events.append({
                        "features": feat,
                        "meta": {
                            "source_ip":  src_ip,
                            "username":   "www-data",
                            "event_hint": "web_shell",
                            "port":       80,
                        }
                    })
            continue

        target_user, command = m.groups()
        key = ("sudo", command.strip()[:80])
        if key in processed:
            continue
        processed.add(key)

        src_m      = _P["syslog_ip"].search(line)
        src_ip     = src_m.group(1) if src_m else "local"
        bytes_m    = _P["bytes"].search(line)
        bytes_sent = int(bytes_m.group(1)) if bytes_m else 0
        sudo_count = ip_sudo_counts.get(src_ip, 1)

        events.append(_make_sudo_event(
            src_ip, target_user, command, sudo_count, bytes_sent
        ))

    return events



def events_to_matrix(events: list[dict], feature_cols: list[str],
                     encoders: dict) -> np.ndarray:

    _PROTOCOL_MAP = {"tcp": 2, "udp": 1, "icmp": 0}
    _SERVICE_MAP  = {
        "ssh": 58, "ftp": 20, "http": 27, "smtp": 54, "shell": 50,
        "telnet": 61, "domain_u": 16, "other": 39, "private": 44,
        "ftp_data": 19, "eco_i": 14, "ecr_i": 15,
    }
    _FLAG_MAP = {
        "SF": 9, "S0": 5, "REJ": 4, "RSTO": 6, "SH": 8,
        "RSTR": 7, "S1": 2, "S2": 3, "S3": 1, "OTH": 0,
    }
    _FALLBACK = {
        "protocol_type": _PROTOCOL_MAP,
        "service":       _SERVICE_MAP,
        "flag":          _FLAG_MAP,
    }

    rows = []
    for ev in events:
        feat = ev["features"]
        row  = []
        for col in feature_cols:
            val = feat.get(col, 0)
            if col in encoders:
                le  = encoders[col]
                val = str(val)
                val = le.transform([val])[0] if val in le.classes_ else -1
            elif col in _FALLBACK:
                val = _FALLBACK[col].get(str(val), -1)
            else:
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = 0.0
            row.append(float(val))
        rows.append(row)

    return np.array(rows, dtype=np.float32)