import tkinter as tk
from tkinter import ttk, filedialog
import threading
from tkinter import messagebox
import requests
import os
import json
from colors import Palette
from components import GoldButton, SHAPBar, AnimatedProgressBar
from helper import api, upload
from logger import get_logger

log = get_logger("ANALYSIS")

class ScanHistoryPanel(tk.Toplevel):
    def __init__(self, parent, on_load=None):
        super().__init__(parent)
        self._on_load = on_load
        self.title("Scan History")
        self.configure(bg=Palette.SURFACE)
        self.geometry("700x500")
        self.resizable(True, True)
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=Palette.SURFACE,
                       padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Scan History",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(side="left")
        tk.Label(hdr, text="Click any scan to reload its full results.",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(side="left",
                                          padx=(Palette.PAD_MD, 0))

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        col_hdr = tk.Frame(self, bg=Palette.SURFACE_LOW,
                           padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        col_hdr.pack(fill="x")
        for txt, w in [("FILE", 22), ("DATE", 14),
                        ("SEVERITY", 12), ("THREAT", 10), ("STATUS", 10)]:
            tk.Label(col_hdr, text=txt,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_LOW,
                     width=w, anchor="w").pack(side="left")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        canvas = tk.Canvas(self, bg=Palette.SURFACE,
                            highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical",
                           command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._list = tk.Frame(canvas, bg=Palette.SURFACE)
        win = canvas.create_window((0, 0), window=self._list,
                                    anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        self._list.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))

        self._status = tk.Label(self._list, text="Loading…",
                                font=Palette.font(Palette.LABEL),
                                fg=Palette.ON_SURFACE_VAR,
                                bg=Palette.SURFACE)
        self._status.pack(pady=Palette.PAD_LG)

    def _load(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            data = api("get", "/analysis/history")
            self.after(0, lambda: self._render(data))
        except Exception as exc:
            self.after(0, lambda: self._status.config(
                text=f"Failed: {exc}", fg=Palette.ERROR))

    def _render(self, items: list):
        for w in self._list.winfo_children():
            w.destroy()

        if not items:
            tk.Label(self._list,
                     text="No scans yet. Run an analysis first.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE).pack(pady=Palette.PAD_LG)
            return

        SEV_COLOR = {"critical": Palette.ERROR,
                     "high":     Palette.ERROR,
                     "medium":   Palette.WARNING,
                     "low":      Palette.SUCCESS,
                     "info":     Palette.INFO}

        for item in items:
            aid      = item["id"]
            filename = item.get("filename", "unknown")
            date     = str(item.get("created_at", ""))[:10]
            severity = item.get("severity", "info").lower()
            score    = int(float(item.get("threat_score", 0)) * 100)
            status   = item.get("status", "").upper()
            sev_col  = SEV_COLOR.get(severity, Palette.ON_SURFACE_VAR)

            row = tk.Frame(self._list, bg=Palette.SURFACE,
                            cursor="hand2",
                            padx=Palette.PAD_LG, pady=Palette.PAD_SM)
            row.pack(fill="x")

            tk.Label(row, text=filename,
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE,
                     bg=Palette.SURFACE,
                     width=22, anchor="w").pack(side="left")
            tk.Label(row, text=date,
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE,
                     width=14, anchor="w").pack(side="left")
            tk.Label(row, text=severity.upper(),
                     font=Palette.bold(Palette.MICRO),
                     fg=sev_col,
                     bg=Palette.SURFACE,
                     width=12, anchor="w").pack(side="left")
            tk.Label(row, text=f"{score}%",
                     font=Palette.bold(Palette.MICRO),
                     fg=sev_col,
                     bg=Palette.SURFACE,
                     width=10, anchor="w").pack(side="left")
            tk.Label(row, text=status,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.SUCCESS if status == "COMPLETED"
                        else Palette.ERROR,
                     bg=Palette.SURFACE,
                     width=10, anchor="w").pack(side="left")

            tk.Frame(self._list, height=1,
                     bg=Palette.OUTLINE).pack(fill="x",
                                               padx=Palette.PAD_LG)

            def _enter(e, r=row):
                r.config(bg=Palette.SURFACE_LOW)
                for w in r.winfo_children():
                    w.config(bg=Palette.SURFACE_LOW)

            def _leave(e, r=row):
                r.config(bg=Palette.SURFACE)
                for w in r.winfo_children():
                    w.config(bg=Palette.SURFACE)

            def _click(e, a=aid):
                self._load_result(a)

            for w in [row] + list(row.winfo_children()):
                w.bind("<Enter>",    _enter)
                w.bind("<Leave>",    _leave)
                w.bind("<Button-1>", _click)

    def _load_result(self, analysis_id: int):
        def fetch():
            try:
                data = api("get", f"/analysis/{analysis_id}")
                self.after(0, lambda: (
                    self._on_load(data) if self._on_load else None,
                    self.destroy()
                ))
            except Exception as exc:
                log.error("Failed to load analysis %s: %s",
                           analysis_id, exc)
        threading.Thread(target=fetch, daemon=True).start()


class EventDetailPanel(tk.Toplevel):
    
    _RECOMMENDATIONS = {
        "DoS": [
            ("IMMEDIATE",  "Block source IP at firewall level immediately.",                          Palette.ERROR),
            ("IMMEDIATE",  "Enable SYN cookies on the affected host to mitigate flood attacks.",      Palette.ERROR),
            ("24 HOURS",   "Implement rate limiting on affected ports and services.",                  Palette.WARNING),
            ("24 HOURS",   "Contact upstream ISP to apply null-routing on the attacking IP range.",    Palette.WARNING),
            ("LONG TERM",  "Deploy a DDoS mitigation service or scrubbing center.",                    Palette.SUCCESS),
            ("LONG TERM",  "Review and harden network architecture with redundant failover paths.",    Palette.SUCCESS),
        ],
        "Probe": [
            ("IMMEDIATE",  "Identify and close all unused open ports on the scanned host.",            Palette.ERROR),
            ("IMMEDIATE",  "Add the scanning IP to the firewall block list.",                          Palette.ERROR),
            ("24 HOURS",   "Enable port scan detection on IDS/IPS and tune alert thresholds.",        Palette.WARNING),
            ("24 HOURS",   "Audit firewall rules — remove any overly permissive allow rules.",         Palette.WARNING),
            ("LONG TERM",  "Schedule regular network vulnerability scans to find exposed services.",   Palette.SUCCESS),
            ("LONG TERM",  "Segment the network to limit lateral visibility between zones.",           Palette.SUCCESS),
        ],
        "R2L": [
            ("IMMEDIATE",  "Lock or reset credentials for all accounts targeted in this event.",       Palette.ERROR),
            ("IMMEDIATE",  "Terminate all active sessions for the affected user accounts.",            Palette.ERROR),
            ("IMMEDIATE",  "Block the source IP at the perimeter firewall.",                           Palette.ERROR),
            ("24 HOURS",   "Enforce multi-factor authentication on all remote access services.",       Palette.WARNING),
            ("24 HOURS",   "Audit SSH authorized_keys and remove any unrecognized public keys.",       Palette.WARNING),
            ("LONG TERM",  "Implement account lockout policy after 5 failed authentication attempts.", Palette.SUCCESS),
            ("LONG TERM",  "Deploy a SIEM rule to alert on repeated failed logins across accounts.",   Palette.SUCCESS),
        ],
        "U2R": [
            ("IMMEDIATE",  "Isolate the affected host from the network immediately.",                  Palette.ERROR),
            ("IMMEDIATE",  "Revoke all sudo and elevated privileges for the involved user.",           Palette.ERROR),
            ("IMMEDIATE",  "Check /etc/passwd and /etc/sudoers for unauthorized new entries.",         Palette.ERROR),
            ("IMMEDIATE",  "Forensic image the disk before any remediation to preserve evidence.",     Palette.ERROR),
            ("24 HOURS",   "Audit all cron jobs, startup scripts, and systemd services for backdoors.",Palette.WARNING),
            ("24 HOURS",   "Review all recently created or modified files on the compromised host.",   Palette.WARNING),
            ("LONG TERM",  "Apply principle of least privilege — remove unnecessary sudo access.",     Palette.SUCCESS),
            ("LONG TERM",  "Deploy file integrity monitoring (FIM) on critical system files.",         Palette.SUCCESS),
        ],
        "Normal": [
            ("INFO",       "No threat detected. Continue routine monitoring.",                         Palette.SUCCESS),
            ("INFO",       "Verify this event matches expected behaviour for this host and user.",      Palette.SUCCESS),
        ],
    }

    _RECOMMENDATIONS_DEFAULT = [
        ("IMMEDIATE",  "Investigate the event manually — unknown attack pattern detected.",            Palette.ERROR),
        ("24 HOURS",   "Cross-reference with threat intelligence feeds for this source IP.",           Palette.WARNING),
        ("LONG TERM",  "Update detection signatures to cover this pattern.",                           Palette.SUCCESS),
    ]
 
    SEV_COLOR = {
        "CRITICAL": Palette.ERROR,
        "HIGH":     Palette.ERROR,
        "MEDIUM":   Palette.WARNING,
        "LOW":      Palette.SUCCESS,
        "BENIGN":   Palette.SUCCESS,
    }

    def __init__(self, parent, event: dict):
        super().__init__(parent)
        self._event = event
        fname = event.get("event_id", "Event")
        self.title(f"Event Detail — {fname}")
        self.configure(bg=Palette.SURFACE)
        self.geometry("680x620")
        self.resizable(True, True)
        self.transient(parent)
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=Palette.SURFACE,
                            highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical",
                           command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=Palette.SURFACE)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all(
                        "<MouseWheel>",
                        lambda ev: canvas.yview_scroll(
                            int(-1*(ev.delta/120)), "units")))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        self._populate(inner)

    def _populate(self, p):
        e    = self._event
        expl = e.get("explanation", {})
        bg   = Palette.SURFACE

        status    = e.get("status", "UNKNOWN").upper()
        sev_color = self.SEV_COLOR.get(status, Palette.ON_SURFACE_VAR)
        score     = int(float(e.get("score", 0)) * 100)

        hdr = tk.Frame(p, bg=Palette.SURFACE_LOW,
                       padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"● {status}",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=sev_color,
                 bg=Palette.SURFACE_LOW).pack(side="left")
        tk.Label(hdr, text=f"{score}%",
                 font=Palette.bold(Palette.HEADLINE_SM),
                 fg=sev_color,
                 bg=Palette.SURFACE_LOW).pack(side="right")

        meta = tk.Frame(p, bg=bg,
                        padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        meta.pack(fill="x")
        for label, value in [
            ("Event ID",  e.get("event_id", "—")),
            ("Timestamp", e.get("timestamp", "—")),
        ]:
            row = tk.Frame(meta, bg=bg)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=value,
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE,
                     bg=bg).pack(side="left")

        tk.Frame(p, height=1, bg=Palette.OUTLINE).pack(fill="x")

        verdict = expl.get("verdict", e.get("lime", ""))
        if verdict:
            self._section(p, "VERDICT")
            vbox = tk.Frame(p, bg=Palette.SURFACE_CONTAINER,
                            padx=Palette.PAD_LG, pady=Palette.PAD_MD)
            vbox.pack(fill="x", padx=Palette.PAD_LG,
                      pady=(0, Palette.PAD_MD))
            tk.Label(vbox, text=verdict,
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE,
                     bg=Palette.SURFACE_CONTAINER,
                     wraplength=580, justify="left").pack(anchor="w")

        top_features = expl.get("top_features", [])
        if top_features:
            self._section(p, "FEATURE CONTRIBUTIONS  (SHAP + LIME)")
            feat_frame = tk.Frame(p, bg=bg,
                                   padx=Palette.PAD_LG,
                                   pady=Palette.PAD_SM)
            feat_frame.pack(fill="x")

            max_val = max(abs(f.get("shap_value", 0))
                         for f in top_features) or 1.0

            for feat in top_features:
                direction = feat.get("direction", "up")
                shap_val  = float(feat.get("shap_value", 0))
                reason    = feat.get("reason", "")
                fname     = feat.get("feature", "")

                frow = tk.Frame(feat_frame,
                                bg=Palette.SURFACE_CONTAINER,
                                padx=Palette.PAD_MD,
                                pady=Palette.PAD_SM)
                frow.pack(fill="x", pady=2)

                # direction arrow + feature name
                arrow     = "▲" if direction == "up" else "▼"
                arr_color = Palette.ERROR if direction == "up" \
                            else Palette.SUCCESS
                top_row   = tk.Frame(frow, bg=Palette.SURFACE_CONTAINER)
                top_row.pack(fill="x")
                tk.Label(top_row, text=arrow,
                         font=Palette.bold(Palette.MICRO),
                         fg=arr_color,
                         bg=Palette.SURFACE_CONTAINER).pack(
                    side="left", padx=(0, Palette.PAD_XS))
                tk.Label(top_row, text=fname,
                         font=Palette.bold(Palette.LABEL),
                         fg=Palette.ON_SURFACE,
                         bg=Palette.SURFACE_CONTAINER).pack(side="left")
                tk.Label(top_row,
                         text=f"SHAP: {shap_val:+.3f}",
                         font=Palette.bold(Palette.MICRO),
                         fg=arr_color,
                         bg=Palette.SURFACE_CONTAINER).pack(side="right")

                # mini bar
                bar_track = tk.Frame(frow, bg=Palette.SURFACE_HIGH,
                                     height=3)
                bar_track.pack(fill="x", pady=(2, 0))
                bar_color = Palette.ERROR if direction == "up" \
                            else Palette.SUCCESS
                tk.Frame(bar_track, bg=bar_color, height=3).place(
                    relx=0, rely=0,
                    relwidth=min(abs(shap_val)/max_val, 1.0),
                    relheight=1)

                # reason text
                if reason:
                    tk.Label(frow, text=reason,
                             font=Palette.font(Palette.MICRO),
                             fg=Palette.ON_SURFACE_VAR,
                             bg=Palette.SURFACE_CONTAINER,
                             wraplength=560, justify="left",
                             anchor="w").pack(fill="x",
                                              pady=(Palette.PAD_XS, 0))

        cf_list = expl.get("counter_factuals", [])
        if cf_list:
            self._section(p, "COUNTERFACTUAL ANALYSIS")
            cf_frame = tk.Frame(p, bg=bg,
                                 padx=Palette.PAD_LG,
                                 pady=Palette.PAD_SM)
            cf_frame.pack(fill="x")
            for cf in cf_list:
                outcome = cf.get("outcome", "")
                change  = cf.get("change", "")
                out_col = (Palette.SUCCESS
                           if outcome.lower() in ("benign", "low")
                           else Palette.WARNING
                           if outcome.lower() == "medium"
                           else Palette.ON_SURFACE)

                cfrow = tk.Frame(cf_frame,
                                  bg=Palette.SURFACE_CONTAINER,
                                  padx=Palette.PAD_MD,
                                  pady=Palette.PAD_SM)
                cfrow.pack(fill="x", pady=2)

                # outcome badge
                tk.Label(cfrow, text=f"→ {outcome}",
                         font=Palette.bold(Palette.MICRO),
                         fg=out_col,
                         bg=Palette.SURFACE_CONTAINER).pack(
                    anchor="w")
                tk.Label(cfrow, text=change,
                         font=Palette.font(Palette.MICRO),
                         fg=Palette.ON_SURFACE_VAR,
                         bg=Palette.SURFACE_CONTAINER,
                         wraplength=560, justify="left").pack(
                    anchor="w", pady=(2, 0))

        raw = expl.get("raw_evidence", {})
        if raw:
            self._section(p, "RAW EVIDENCE")
            ev_frame = tk.Frame(p, bg=Palette.SURFACE_CONTAINER,
                                 padx=Palette.PAD_LG,
                                 pady=Palette.PAD_MD)
            ev_frame.pack(fill="x", padx=Palette.PAD_LG,
                           pady=(0, Palette.PAD_MD))

            fields = [
                ("Source IP",  raw.get("source_ip", "—")),
                ("Dest IP",    raw.get("dest_ip",   "—")),
                ("Username",   raw.get("username",  "—")),
                ("Process",    raw.get("process",   "—")),
                ("Protocol",   raw.get("protocol",  "—")),
                ("Port",       str(raw.get("port",  "—"))),
                ("Bytes Sent", self._fmt_bytes(raw.get("bytes_sent", 0))),
            ]
            for label, value in fields:
                row = tk.Frame(ev_frame, bg=Palette.SURFACE_CONTAINER)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=label,
                         font=Palette.bold(Palette.MICRO),
                         fg=Palette.ON_SURFACE_VAR,
                         bg=Palette.SURFACE_CONTAINER,
                         width=14, anchor="w").pack(side="left")
                tk.Label(row, text=value,
                         font=Palette.font(Palette.LABEL),
                         fg=Palette.PRIMARY
                         if "IP" in label else Palette.ON_SURFACE,
                         bg=Palette.SURFACE_CONTAINER).pack(side="left")
                
                
        self._build_recommendations(p)
        
        tk.Frame(p, height=Palette.PAD_XL, bg=bg).pack()

    def _section(self, parent, title: str):
        f = tk.Frame(parent, bg=Palette.SURFACE_LOW,
                     padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        f.pack(fill="x", pady=(Palette.PAD_MD, 0))
        tk.Label(f, text=title,
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW).pack(anchor="w")
        
    def _build_recommendations(self, parent):
        e  = self._event
        event_type = e.get("type", e.get("event_type", "")).strip()

        _FAMILY_MAP = {
            "SSH Brute Force":      "R2L",
            "Lateral Movement":     "R2L",
            "Data Exfiltration":    "R2L",
            "Elevated Privileges":  "U2R",
            "Privilege Escalation": "U2R",
            "C2 Beaconing":         "R2L",
            "DoS":                  "DoS",
            "Probe":                "Probe",
            "R2L":                  "R2L",
            "U2R":                  "U2R",
            "Normal":               "Normal",
        }

        family = _FAMILY_MAP.get(event_type, event_type)
        recs   = self._RECOMMENDATIONS.get(family, self._RECOMMENDATIONS_DEFAULT)

        self._section(parent, "RECOMMENDED ACTIONS")

        container = tk.Frame(parent, bg=Palette.SURFACE,
                            padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        container.pack(fill="x", pady=(0, Palette.PAD_MD))

        # urgency config: (badge_bg, badge_fg, row_bg, row_border)
        _URGENCY_STYLE = {
            "IMMEDIATE": (Palette.ERROR,   Palette.SURFACE, Palette.SURFACE,    Palette.ERROR),
            "24 HOURS":  (Palette.WARNING, Palette.SURFACE, Palette.SURFACE,    Palette.WARNING),
            "LONG TERM": (Palette.SUCCESS, Palette.SURFACE, Palette.SURFACE,    Palette.SUCCESS),
            "INFO":      (Palette.INFO,    Palette.SURFACE, Palette.SURFACE_LOW, Palette.INFO),
        }

        for i, (urgency, text, color) in enumerate(recs, start=1):
            badge_bg, badge_fg, row_bg, border_color = _URGENCY_STYLE.get(
                urgency,
                (Palette.ON_SURFACE_VAR, Palette.SURFACE,
                Palette.SURFACE_LOW, Palette.OUTLINE)
            )

            # outer wrapper for left border effect
            wrapper = tk.Frame(container, bg=border_color)
            wrapper.pack(fill="x", pady=2)

            row = tk.Frame(
                wrapper,
                bg=Palette.SURFACE_CONTAINER,
                padx=Palette.PAD_MD,
                pady=Palette.PAD_SM,
            )
            row.pack(fill="x", padx=(3, 0))  # 3px left border visible

            # step number
            tk.Label(
                row,
                text=f"{i:02d}",
                font=Palette.bold(Palette.LABEL_SM),
                fg=border_color,
                bg=Palette.SURFACE_CONTAINER,
                width=3,
                anchor="w",
            ).pack(side="left")

            # urgency badge
            badge = tk.Frame(row, bg=badge_bg, padx=8, pady=2)
            badge.pack(side="left", padx=(0, Palette.PAD_MD))
            tk.Label(
                badge,
                text=urgency,
                font=Palette.bold(Palette.MICRO),
                fg=badge_fg,
                bg=badge_bg,
            ).pack()

            # recommendation text
            tk.Label(
                row,
                text=text,
                font=Palette.font(Palette.LABEL_SM),
                fg=Palette.ON_SURFACE,
                bg=Palette.SURFACE_CONTAINER,
                wraplength=500,
                justify="left",
                anchor="w",
            ).pack(side="left", fill="x", expand=True)     
        
    # def _build_recommendations(self, parent):
    #     e  = self._event
    #     event_type  = e.get("type", e.get("event_type", "")).strip()

    #     # map event_type to family
    #     _FAMILY_MAP = {
    #         "SSH Brute Force":       "R2L",
    #         "Lateral Movement":      "R2L",
    #         "Data Exfiltration":     "R2L",
    #         "Elevated Privileges":   "U2R",
    #         "Privilege Escalation":  "U2R",
    #         "C2 Beaconing":          "R2L",
    #         "DoS":                   "DoS",
    #         "Probe":                 "Probe",
    #         "R2L":                   "R2L",
    #         "U2R":                   "U2R",
    #         "Normal":                "Normal",
    #     }

    #     family = _FAMILY_MAP.get(event_type, event_type)
    #     recs   = self._RECOMMENDATIONS.get(family, self._RECOMMENDATIONS_DEFAULT)

    #     self._section(parent, "RECOMMENDED ACTIONS")

    #     container = tk.Frame(parent, bg=Palette.SURFACE,
    #                         padx=Palette.PAD_LG, pady=Palette.PAD_SM)
    #     container.pack(fill="x", pady=(0, Palette.PAD_MD))

    #     _URGENCY_BG = {
    #         "IMMEDIATE": "#2a1515",
    #         "24 HOURS":  "#2a2010",
    #         "LONG TERM": "#152015",
    #         "INFO":      "#151a2a",
    #     }

    #     for i, (urgency, text, color) in enumerate(recs, start=1):
    #         row = tk.Frame(
    #             container,
    #             bg=_URGENCY_BG.get(urgency, Palette.SURFACE_CONTAINER),
    #             padx=Palette.PAD_MD,
    #             pady=Palette.PAD_SM,
    #         )
    #         row.pack(fill="x", pady=2)

    #         # step number
    #         tk.Label(
    #             row,
    #             text=f"{i:02d}",
    #             font=Palette.bold(Palette.MICRO),
    #             fg=color,
    #             bg=_URGENCY_BG.get(urgency, Palette.SURFACE_CONTAINER),
    #             width=3,
    #             anchor="w",
    #         ).pack(side="left")

    #         # urgency badge
    #         badge_frame = tk.Frame(
    #             row,
    #             bg=color,
    #             padx=6,
    #             pady=1,
    #         )
    #         badge_frame.pack(side="left", padx=(0, Palette.PAD_SM))
    #         tk.Label(
    #             badge_frame,
    #             text=urgency,
    #             font=Palette.bold(Palette.MICRO),
    #             fg=Palette.SURFACE,
    #             bg=color,
    #         ).pack()

    #         # recommendation text
    #         tk.Label(
    #             row,
    #             text=text,
    #             font=Palette.font(Palette.LABEL_SM),
    #             fg=Palette.ON_SURFACE,
    #             bg=_URGENCY_BG.get(urgency, Palette.SURFACE_CONTAINER),
    #             wraplength=520,
    #             justify="left",
    #             anchor="w",
    #         ).pack(side="left", fill="x", expand=True)    

    @staticmethod
    def _fmt_bytes(b: int) -> str:
        if not b:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"



class EventRow(tk.Frame):
    """
    Compact event row with inline LIME summary.
    Click 'Detail' to open full EventDetailPanel.
    """
    SEV_COLOR = {
        "CRITICAL": Palette.ERROR,
        "HIGH":     Palette.ERROR,
        "MEDIUM":   Palette.WARNING,
        "LOW":      Palette.SUCCESS,
        "BENIGN":   Palette.SUCCESS,
    }

    def __init__(self, parent, event: dict, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._event = event
        self._bg    = bg
        self._build()

    def _build(self):
        e         = self._event
        bg        = self._bg
        status    = e.get("status", "UNKNOWN").upper()
        sev_color = self.SEV_COLOR.get(status, Palette.ON_SURFACE_VAR)
        score     = int(float(e.get("score", 0)) * 100)
        lime      = e.get("lime", "")

        # ── main row ──────────────────────────────────────────────────
        row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_LG)

        # DETAIL button — pack right first
        detail_btn = tk.Label(row, text="Detail →",
                              font=Palette.bold(Palette.MICRO),
                              fg=Palette.PRIMARY,
                              bg=bg, cursor="hand2")
        detail_btn.pack(side="right")
        detail_btn.bind("<Button-1>",
                        lambda e: EventDetailPanel(
                            self.winfo_toplevel(), self._event))
        detail_btn.bind("<Enter>",
                        lambda e: detail_btn.config(
                            fg=Palette.PRIMARY_DIM))
        detail_btn.bind("<Leave>",
                        lambda e: detail_btn.config(fg=Palette.PRIMARY))

        # status chip — pack right second
        chip = tk.Frame(row, bg=bg)
        chip.pack(side="right", padx=(0, Palette.PAD_MD))
        tk.Label(chip, text="●",
                 font=Palette.bold(Palette.MICRO),
                 fg=sev_color, bg=bg).pack(side="left", padx=(0, 3))
        tk.Label(chip, text=f"{status}  {score}%",
                 font=Palette.bold(Palette.MICRO),
                 fg=sev_color, bg=bg).pack(side="left")

        # timestamp
        tk.Label(row, text=e.get("timestamp", "—"),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=20, anchor="w").pack(side="left")

        # event id
        tk.Label(row, text=e.get("event_id", "—"),
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=bg, width=14, anchor="w").pack(side="left")

        # ── LIME summary line ─────────────────────────────────────────
        if lime:
            lime_row = tk.Frame(self, bg=Palette.SURFACE_HIGH,
                                padx=Palette.PAD_LG, pady=4)
            lime_row.pack(fill="x")
            tk.Label(lime_row, text="◈",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.PRIMARY,
                     bg=Palette.SURFACE_HIGH).pack(side="left",
                                                    padx=(0, Palette.PAD_XS))
            tk.Label(lime_row, text=lime,
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_HIGH,
                     wraplength=700, justify="left",
                     anchor="w").pack(side="left", fill="x", expand=True)

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_LG)


class LogSelectorPanel(tk.Frame):
    def __init__(self, parent, on_select=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg        = bg
        self._on_select = on_select
        self._log_map   = {}
        self._build()
        self._load_logs()

    def _build(self):
        tab_bar = tk.Frame(self, bg=Palette.SURFACE_HIGH)
        tab_bar.pack(fill="x")
        self._tab_btns = {}
        for i, label in enumerate(["Uploaded Logs", "Upload New"]):
            btn = tk.Label(tab_bar, text=label,
                           font=Palette.bold(Palette.MICRO),
                           bg=Palette.SURFACE_HIGH,
                           fg=Palette.ON_SURFACE_VAR,
                           padx=Palette.PAD_MD,
                           pady=Palette.PAD_SM,
                           cursor="hand2")
            btn.grid(row=0, column=i, sticky="nsew")
            tab_bar.columnconfigure(i, weight=1)
            btn.bind("<Button-1>", lambda e, l=label: self._switch(l))
            self._tab_btns[label] = btn

        self._panels = {}

        up = tk.Frame(self, bg=self._bg)
        self._panels["Uploaded Logs"] = up

        self._status_lbl = tk.Label(up, text="Loading…",
                                    font=Palette.font(Palette.MICRO),
                                    fg=Palette.ON_SURFACE_VAR,
                                    bg=self._bg)
        self._status_lbl.pack(anchor="w",
                               padx=Palette.PAD_MD,
                               pady=(Palette.PAD_SM, 0))

        list_frame = tk.Frame(up, bg=self._bg)
        list_frame.pack(fill="both", expand=True,
                         padx=Palette.PAD_MD, pady=Palette.PAD_SM)

        self._list_canvas = tk.Canvas(list_frame, bg=self._bg,
                                       highlightthickness=0)
        sb = tk.Scrollbar(list_frame, orient="vertical",
                           command=self._list_canvas.yview)
        self._list_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._list_canvas.pack(side="left", fill="both", expand=True)

        self._log_list = tk.Frame(self._list_canvas, bg=self._bg)
        win = self._list_canvas.create_window(
            (0, 0), window=self._log_list, anchor="nw")
        self._list_canvas.bind("<Configure>",
            lambda e: self._list_canvas.itemconfig(win, width=e.width))
        self._log_list.bind("<Configure>",
            lambda e: self._list_canvas.configure(
                scrollregion=self._list_canvas.bbox("all")))

        un = tk.Frame(self, bg=self._bg)
        self._panels["Upload New"] = un
        self._build_upload_panel(un)

        self._switch("Uploaded Logs")

    def _build_upload_panel(self, parent):
        tk.Frame(parent, height=Palette.PAD_MD, bg=self._bg).pack()

        dz = tk.Frame(parent, bg=Palette.SURFACE_HIGH,
                       highlightbackground=Palette.OUTLINE_BRIGHT,
                       highlightthickness=1)
        dz.pack(fill="x", padx=Palette.PAD_MD)
        tk.Label(dz, text="⬆",
                 font=Palette.bold(22),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH).pack(pady=(Palette.PAD_MD, 0))
        tk.Label(dz, text="Drop file here or browse",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_HIGH).pack()
        tk.Label(dz, text=".json  .csv  .pcap  .log",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGH).pack(pady=(2, Palette.PAD_MD))

        self._upload_lbl = tk.Label(parent, text="",
                                    font=Palette.bold(Palette.MICRO),
                                    fg=Palette.PRIMARY,
                                    bg=self._bg, wraplength=180)
        self._upload_lbl.pack(pady=(Palette.PAD_SM, 0))
        tk.Frame(parent, height=Palette.PAD_SM, bg=self._bg).pack()

        GoldButton(parent, text="Browse Files",
                   command=self._browse).pack(
            fill="x", padx=Palette.PAD_MD, ipady=6)
        tk.Frame(parent, height=Palette.PAD_SM, bg=self._bg).pack()

        self._upload_btn = GoldButton(parent, text="Upload & Analyse",
                                       command=self._upload_and_analyse)
        self._upload_btn.pack(fill="x", padx=Palette.PAD_MD, ipady=6)
        self._upload_btn.config(state="disabled")

        self._upload_status = tk.Label(parent, text="",
                                        font=Palette.font(Palette.MICRO),
                                        fg=Palette.ON_SURFACE_VAR,
                                        bg=self._bg, wraplength=180)
        self._upload_status.pack(pady=(Palette.PAD_SM, 0),
                                   padx=Palette.PAD_MD, anchor="w")
        self._pending_file = None

    def _switch(self, label):
        for p in self._panels.values():
            p.pack_forget()
        for l, btn in self._tab_btns.items():
            active = l == label
            btn.config(
                bg=Palette.SURFACE_CONTAINER if active
                   else Palette.SURFACE_HIGH,
                fg=Palette.PRIMARY if active
                   else Palette.ON_SURFACE_VAR)
        self._panels[label].pack(fill="both", expand=True)

    def _load_logs(self):
        threading.Thread(target=self._fetch_logs, daemon=True).start()

    def _fetch_logs(self):
        try:
            logs = api("get", "/logs/")
            self.after(0, lambda: self._render_logs(logs))
        except Exception as exc:
            self.after(0, lambda: self._status_lbl.config(
                text=f"Failed: {exc}", fg=Palette.ERROR))

    def _render_logs(self, logs: list):
        for w in self._log_list.winfo_children():
            w.destroy()
        self._log_map.clear()

        if not logs:
            self._status_lbl.config(text="No logs uploaded yet.")
            tk.Label(self._log_list,
                     text="Upload a file using\nthe 'Upload New' tab.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg, justify="center").pack(
                pady=Palette.PAD_LG)
            return

        self._status_lbl.config(
            text=f"{len(logs)} file(s) — click to select",
            fg=Palette.ON_SURFACE_VAR)

        for item in logs:
            log_id = item["id"]
            fname  = item.get("original_name",
                               item.get("filename", "unknown"))
            size   = self._fmt_size(item.get("file_size", 0))
            date   = str(item.get("uploaded_at", ""))[:10]
            count  = item.get("analysis_count", 0)
            self._log_map[log_id] = fname

            row = tk.Frame(self._log_list, bg=self._bg,
                            cursor="hand2",
                            highlightbackground=Palette.OUTLINE,
                            highlightthickness=1)
            row.pack(fill="x", pady=2)

            dot = tk.Label(row, text="○",
                           font=Palette.bold(Palette.MICRO),
                           fg=Palette.OUTLINE_BRIGHT, bg=self._bg)
            dot.pack(side="left", padx=(Palette.PAD_SM, 4))

            # analysis count badge
            if count > 0:
                tk.Label(row, text=f"◈{count}",
                         font=Palette.bold(Palette.MICRO),
                         fg=Palette.PRIMARY,
                         bg=self._bg).pack(side="right",
                                            padx=(0, Palette.PAD_SM))

            lbl = tk.Label(row,
                           text=f"{fname}\n{size}  •  {date}",
                           font=Palette.font(Palette.MICRO),
                           fg=Palette.ON_SURFACE,
                           bg=self._bg, anchor="w", justify="left")
            lbl.pack(side="left", fill="x", expand=True,
                     pady=Palette.PAD_SM)

            for w in (row, dot, lbl):
                w.bind("<Button-1>",
                       lambda e, lid=log_id, r=row, d=dot:
                       self._select_row(lid, r, d))

    def _select_row(self, log_id, row, dot):
        for child in self._log_list.winfo_children():
            child.config(bg=self._bg,
                          highlightbackground=Palette.OUTLINE)
            for w in child.winfo_children():
                try:
                    w.config(bg=self._bg)
                    if isinstance(w, tk.Label) and \
                            w.cget("text") in ("○", "●"):
                        w.config(text="○", fg=Palette.OUTLINE_BRIGHT)
                except Exception:
                    pass
        row.config(bg=Palette.SURFACE_HIGH,
                    highlightbackground=Palette.PRIMARY)
        for w in row.winfo_children():
            try:
                w.config(bg=Palette.SURFACE_HIGH)
            except Exception:
                pass
        dot.config(text="●", fg=Palette.PRIMARY)
        if self._on_select:
            self._on_select(log_id)

    def _browse(self):
        f = filedialog.askopenfilename(
            title="Select Forensic Evidence File",
            filetypes=[("All Supported", "*.json *.csv *.pcap *.log"),
                       ("All", "*.*")])
        if f:
            self._pending_file = f
            self._upload_lbl.config(text=os.path.basename(f))
            self._upload_btn.config(state="normal")

    def _upload_and_analyse(self):
        if not self._pending_file:
            return
        self._upload_btn.config(state="disabled", text="Uploading…")
        self._upload_status.config(text="", fg=Palette.ON_SURFACE_VAR)
        threading.Thread(target=self._do_upload, daemon=True).start()

    def _do_upload(self):
        try:
            result = upload("/logs/upload", self._pending_file)
            log_id = result["id"]
            self.after(0, lambda: self._after_upload(log_id))
        except requests.HTTPError as exc:
            try:
                msg = exc.response.json().get("detail", "Upload failed.")
            except Exception:
                msg = f"Server error ({exc.response.status_code})"
            self.after(0, lambda: self._upload_error(msg))
        except Exception as exc:
            self.after(0, lambda: self._upload_error(str(exc)))

    def _after_upload(self, log_id):
        self._upload_btn.config(state="disabled",
                                 text="Upload & Analyse")
        self._upload_status.config(
            text="✓ Uploaded — running analysis…",
            fg=Palette.SUCCESS)
        self._pending_file = None
        self._upload_lbl.config(text="")
        self._load_logs()
        if self._on_select:
            self._on_select(log_id)

    def _upload_error(self, msg):
        self._upload_btn.config(state="normal",
                                 text="Upload & Analyse")
        self._upload_status.config(text=f"✗ {msg}", fg=Palette.ERROR)

    def refresh(self):
        self._load_logs()

    @staticmethod
    def _fmt_size(b):
        if not b:
            return "—"
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.0f} {u}"
            b /= 1024
        return f"{b:.1f} TB"


class AnalysisPage(tk.Frame):

    def __init__(self, parent, user=None,
                 on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user        = user
        self._prog_bar    = None
        self._pct_label   = None
        self._selected_id = None
        self._history_win = None
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=Palette.SURFACE,
                            highlightthickness=0)
        scroll = tk.Scrollbar(self, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=Palette.SURFACE)
        win_id = canvas.create_window((0, 0), window=self._inner,
                                       anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(
                             scrollregion=canvas.bbox("all")))
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all(
                        "<MouseWheel>",
                        lambda ev: canvas.yview_scroll(
                            int(-1*(ev.delta/120)), "units")))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))
        self._populate()

    def _populate(self):
        p = self._inner

        hdr = tk.Frame(p, bg=Palette.SURFACE)
        hdr.pack(fill="x", padx=Palette.PAD_XL,
                 pady=(Palette.PAD_LG, 0))

        title_block = tk.Frame(hdr, bg=Palette.SURFACE)
        title_block.pack(side="left")
        tk.Label(title_block, text="Log Analysis",
                 font=Palette.bold(Palette.DISPLAY),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(anchor="w")
        tk.Label(title_block,
                 text="Neural Inspection & Explainable AI Module",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w", pady=(2, 0))

        btn_row = tk.Frame(hdr, bg=Palette.SURFACE)
        btn_row.pack(side="right", pady=8)

        GoldButton(btn_row, text="Scan History",
                   command=self._open_history).pack(
            side="left", padx=(0, Palette.PAD_SM), ipady=4, ipadx=8)

        self._run_btn = GoldButton(btn_row, text="Run Analysis",
                                    command=self._run_analysis)
        self._run_btn.pack(side="left", ipady=4, ipadx=8)
        
        
        self._gen_btn = GoldButton(btn_row, text="Generate Report",
                                    command=self._generate_report)
        self._gen_btn.pack(side="left", ipady=4, ipadx=8)
        self._gen_btn.config(state="disabled")   # enabled after analysis completes

        self._last_analysis_id = None

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        cols = tk.Frame(p, bg=Palette.SURFACE)
        cols.pack(fill="x", padx=Palette.PAD_XL)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=2)

        left = tk.Frame(cols, bg=Palette.SURFACE_CONTAINER)
        left.grid(row=0, column=0, sticky="nsew",
                   padx=(0, Palette.PAD_MD))

        LogSelectorPanel(left,
                          on_select=self._on_log_selected,
                          bg=Palette.SURFACE_CONTAINER
                          ).pack(fill="both", expand=True)

        tk.Frame(left, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_MD)

        scan_area = tk.Frame(left, bg=Palette.SURFACE_CONTAINER,
                              padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        scan_area.pack(fill="x")

        scan_hdr = tk.Frame(scan_area, bg=Palette.SURFACE_CONTAINER)
        scan_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        tk.Label(scan_hdr, text="NEURAL SCAN STATUS",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")
        self._pct_label = tk.Label(
            scan_hdr, text="—",
            font=Palette.bold(Palette.MICRO),
            fg=Palette.PRIMARY,
            bg=Palette.SURFACE_CONTAINER)
        self._pct_label.pack(side="right")

        self._prog_bar = AnimatedProgressBar(
            scan_area, value=0.0, bg=Palette.SURFACE_CONTAINER)
        self._prog_bar.pack(fill="x")

        self._scan_lbl = tk.Label(
            scan_area,
            text="Select a log file and press Run Analysis.",
            font=Palette.font(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER, anchor="w")
        self._scan_lbl.pack(anchor="w", pady=(Palette.PAD_SM, 0))

        # RIGHT — summary + SHAP
        right = tk.Frame(cols, bg=Palette.SURFACE_CONTAINER)
        right.grid(row=0, column=1, sticky="nsew")

        # summary section
        sum_hdr = tk.Frame(right, bg=Palette.SURFACE_CONTAINER)
        sum_hdr.pack(fill="x", padx=Palette.PAD_LG,
                      pady=(Palette.PAD_LG, 4))
        tk.Label(sum_hdr, text="AI Executive Summary",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")

        self._summary_frame = tk.Frame(right,
                                        bg=Palette.SURFACE_CONTAINER)
        self._summary_frame.pack(fill="x", padx=Palette.PAD_LG,
                                  pady=(0, Palette.PAD_MD))
        tk.Label(self._summary_frame,
                 text="Run analysis to see AI summary.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(right, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_LG)

        shap_hdr = tk.Frame(right, bg=Palette.SURFACE_CONTAINER)
        shap_hdr.pack(fill="x", padx=Palette.PAD_LG,
                       pady=(Palette.PAD_MD, 4))
        tk.Label(shap_hdr, text="SHAP Global Explainer",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")

        tk.Label(right,
                 text="Impact of features on predictive outcome",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER, anchor="w").pack(
            fill="x", padx=Palette.PAD_LG,
            pady=(0, Palette.PAD_MD))

        self._shap_frame = tk.Frame(right, bg=Palette.SURFACE_CONTAINER)
        self._shap_frame.pack(fill="x", padx=Palette.PAD_LG)
        tk.Label(self._shap_frame,
                 text="Run analysis to see SHAP feature weights.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(right, height=Palette.PAD_MD,
                 bg=Palette.SURFACE_CONTAINER).pack()

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        events_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        events_card.pack(fill="x", padx=Palette.PAD_XL)

        ev_hdr = tk.Frame(events_card, bg=Palette.SURFACE_CONTAINER)
        ev_hdr.pack(fill="x", padx=Palette.PAD_LG,
                     pady=(Palette.PAD_LG, 0))
        tk.Label(ev_hdr, text="Flagged Suspicious Events",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")

        self._result_meta = tk.Label(
            ev_hdr, text="",
            font=Palette.bold(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER)
        self._result_meta.pack(side="right")

        # column headers
        col_hdr = tk.Frame(events_card, bg=Palette.SURFACE_CONTAINER)
        col_hdr.pack(fill="x", padx=Palette.PAD_LG,
                      pady=(Palette.PAD_MD, Palette.PAD_SM))
        for txt, w in [("TIMESTAMP", 20), ("EVENT ID", 14),
                        ("STATUS", 16), ("LIME SUMMARY", 0)]:
            tk.Label(col_hdr, text=txt,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER,
                     width=w if w else None,
                     anchor="w").pack(side="left")

        tk.Frame(events_card, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_LG)

        self._events_frame = tk.Frame(events_card,
                                       bg=Palette.SURFACE_CONTAINER)
        self._events_frame.pack(fill="x")
        tk.Label(self._events_frame,
                 text="No analysis run yet.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(
            pady=Palette.PAD_LG, anchor="w", padx=Palette.PAD_LG)

        tk.Frame(p, height=Palette.PAD_XL, bg=Palette.SURFACE).pack()


    def _open_history(self):
        if self._history_win and self._history_win.winfo_exists():
            self._history_win.lift()
            return
        self._history_win = ScanHistoryPanel(
            self, on_load=self._load_historical_result)

    def _load_historical_result(self, data: dict):
        self._prog_bar.set_value(1.0)
        self._pct_label.config(text="100%")
        date  = str(data.get("created_at", ""))[:10]
        score = int(float(data.get("threat_score", 0)) * 100)
        sev   = data.get("severity", "").upper()
        self._scan_lbl.config(
            text=f"✓  Historical — {date} — {sev}  {score}%",
            fg=Palette.INFO)
        self._result_meta.config(
            text=f"Analysis #{data.get('id')}  •  "
                 f"{data.get('filename', '')}  •  {date}")
        self._render_summary(data.get("summary", ""),
                             data.get("severity", ""))
        self._render_shap(data.get("shap", []))
        self._render_events(data.get("events", []))

    def _on_log_selected(self, log_id: int):
        self._selected_id = log_id
        self._scan_lbl.config(
            text=f"Log #{log_id} selected — press Run Analysis.",
            fg=Palette.ON_SURFACE_VAR)

    def _run_analysis(self):
        if not self._selected_id:
            self._scan_lbl.config(
                text="Select a log file first.", fg=Palette.WARNING)
            return
        self._run_btn.config(state="disabled", text="Running…")
        self._prog_bar.set_value(0.0)
        self._pct_label.config(text="0%")
        self._scan_lbl.config(
            text="⚡  Neural scan initialising…",
            fg=Palette.ON_SURFACE_VAR)
        self._animate_progress(0, 70)
        threading.Thread(target=self._do_analysis,
                          args=(self._selected_id,),
                          daemon=True).start()

    def _do_analysis(self, log_id: int):
        try:
            result = api("post", f"/analysis/run?log_id={log_id}", timeout=(10, 300))
            self.after(0, lambda: self._on_result(result))
        except requests.HTTPError as exc:
            try:
                msg = exc.response.json().get("detail", "Analysis failed.")
                print(exc.response)
            except Exception:
                msg = f"Server error ({exc.response.status_code}) {exc.response.m}"
            self.after(0, lambda m=msg: self._on_error(m))
        except requests.ConnectionError:
            self.after(0, lambda: self._on_error("Cannot reach server."))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self._on_error(m))


    def _generate_report(self):
        if not self._last_analysis_id:
            return

        self._gen_btn.config(state="disabled", text="Generating…")

        def do():
            try:
                api("post",
                    f"/reports/generate/{self._last_analysis_id}")
                self.after(0, self._on_report_generated)
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Server error ({exc.response.status_code})"
                self.after(0, lambda: (
                    self._gen_btn.config(state="normal",
                                        text="Generate Report"),
                    messagebox.showerror("Report Failed", msg)
                ))
            except Exception as exc:
                self.after(0, lambda: (
                    self._gen_btn.config(state="normal",
                                        text="Generate Report"),
                    messagebox.showerror("Report Failed", str(exc))
                ))

        threading.Thread(target=do, daemon=True).start()

    def _on_report_generated(self):
        self._gen_btn.config(state="normal", text="✓ Report Generated")
        self.after(3000, lambda: self._gen_btn.config(
            text="Generate Report"))
        messagebox.showinfo(
            "Report Generated",
            "Report created successfully.\n"
            "View it in the Reports page."
        )

    def _on_result(self, data: dict):
        score = int(float(data.get("threat_score", 0)) * 100)
        sev   = data.get("severity", "").upper()
        date  = str(data.get("created_at", ""))[:10]

        SEV_COLOR = {"CRITICAL": Palette.ERROR, "HIGH": Palette.ERROR,
                    "MEDIUM": Palette.WARNING, "LOW": Palette.SUCCESS}
        done_color = SEV_COLOR.get(sev, Palette.SUCCESS)

        self._animate_progress(70, 100, on_done=lambda: (
            self._pct_label.config(text="100%"),
            self._scan_lbl.config(
                text=f"✓  Complete — {sev}  {score}%",
                fg=done_color)
        ))
        self._run_btn.config(state="normal", text="Run Analysis")
        self._result_meta.config(
            text=f"Analysis #{data.get('id')}  •  "
                f"{data.get('filename', '')}  •  {date}")

        self._last_analysis_id = data.get("id")
        self._gen_btn.config(state="normal", text="Generate Report")

        self._render_summary(data.get("summary", ""),
                            data.get("severity", ""))
        self._render_shap(data.get("shap", []))
        self._render_events(data.get("events", []))

    def _on_error(self, msg: str):
        self._prog_bar.set_value(0.0)
        self._pct_label.config(text="—")
        self._scan_lbl.config(text=f"✗  {msg}", fg=Palette.ERROR)
        self._run_btn.config(state="normal", text="Run Analysis")


    def _render_summary(self, summary: str, severity: str):
        for w in self._summary_frame.winfo_children():
            w.destroy()

        if not summary:
            tk.Label(self._summary_frame,
                     text="No summary returned.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
            return

        SEV_COLOR = {"critical": Palette.ERROR,
                     "high": Palette.ERROR,
                     "medium": Palette.WARNING,
                     "low": Palette.SUCCESS,
                     "info": Palette.INFO}
        sev_col = SEV_COLOR.get(severity.lower(),
                                 Palette.ON_SURFACE_VAR)

        if severity:
            tk.Label(self._summary_frame,
                     text=f"● {severity.upper()}",
                     font=Palette.bold(Palette.MICRO),
                     fg=sev_col,
                     bg=Palette.SURFACE_CONTAINER).pack(
                anchor="w", pady=(0, Palette.PAD_XS))

        tk.Label(self._summary_frame,
                 text=summary,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER,
                 wraplength=380, justify="left").pack(anchor="w")

    def _render_shap(self, shap_data: list):
        for w in self._shap_frame.winfo_children():
            w.destroy()
        if not shap_data:
            tk.Label(self._shap_frame,
                     text="No SHAP data returned.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
            return
        for item in shap_data:
            SHAPBar(self._shap_frame,
                    label=item.get("feature", ""),
                    value=float(item.get("value", 0)),
                    max_val=float(item.get("max_val", 0.5)),
                    bg=Palette.SURFACE_CONTAINER).pack(fill="x")

    def _render_events(self, events: list):
        for w in self._events_frame.winfo_children():
            w.destroy()

        if not events:
            tk.Label(self._events_frame,
                     text="No suspicious events detected.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.SUCCESS,
                     bg=Palette.SURFACE_CONTAINER).pack(
                pady=Palette.PAD_LG, anchor="w",
                padx=Palette.PAD_LG)
            return

        for event in events:
            EventRow(self._events_frame,
                     event=event,
                     bg=Palette.SURFACE_CONTAINER).pack(fill="x")


    def _animate_progress(self, current: int, target: int,
                           on_done=None):
        if current >= target:
            if on_done:
                on_done()
            return
        nxt = current + 1
        self._prog_bar.set_value(nxt / 100)
        self._pct_label.config(text=f"{nxt}%")
        self.after(30, lambda: self._animate_progress(
            nxt, target, on_done))