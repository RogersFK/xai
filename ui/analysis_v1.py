# import tkinter as tk
# from tkinter import ttk
# import platform
# import threading
# import time
# import math
# from colors import Palette
# from components import GoldButton, DropZone, SHAPBar, AnimatedProgressBar, ThreatRow

# class AnalysisPage(tk.Frame):
#     """
#     Evidence Analysis page.
#     Assembles TopBar (excluded here, handled by App), and the body.
#     """

#     SHAP_DATA = [
#         ("Source Entropy Variance",  0.428, 0.5),
#         ("Packet Header Anomaly",    0.312, 0.5),
#         ("Payload Signature Match", -0.115, 0.5),
#         ("Temporal Drift",           0.098, 0.5),
#     ]

#     THREAT_DATA = [
#         {
#             "timestamp": "2023-11-04 14:22:01",
#             "event_id":  "EFX-0012-92",
#             "score":     92,
#             "status":    "CRITICAL",
#             "lime": (
#                 "Individual observation analysis: The high threat score is "
#                 "primarily driven by an unusual payload-to-latency ratio "
#                 "which deviates 4.2σ from the baseline investigator profile."
#             ),
#             "pos": "Port 443 Tunneling [0.82]",
#             "neg": "Known IP Range [-0.15]",
#         },
#         {
#             "timestamp": "2023-11-04 14:21:44",
#             "event_id":  "EFX-0012-88",
#             "score":     45,
#             "status":    "REVIEW",
#             "lime":      None,
#         },
#         {
#             "timestamp": "2023-11-04 14:20:12",
#             "event_id":  "EFX-0012-74",
#             "score":     12,
#             "status":    "BENIGN",
#             "lime":      None,
#         },
#     ]

#     def __init__(self, parent, **kw):
#         super().__init__(parent, bg=Palette.SURFACE, **kw)
#         self._prog_bar = None
#         self._build()

#     def _build(self):
#         # scrollable canvas wrapper
#         canvas = tk.Canvas(self, bg=Palette.SURFACE,
#                            highlightthickness=0)
#         scroll = tk.Scrollbar(self, orient="vertical",
#                               command=canvas.yview)
#         canvas.configure(yscrollcommand=scroll.set)

#         scroll.pack(side="right", fill="y")
#         canvas.pack(side="left", fill="both", expand=True)

#         self._inner = tk.Frame(canvas, bg=Palette.SURFACE)
#         win_id = canvas.create_window((0, 0), window=self._inner,
#                                       anchor="nw")

#         def _on_resize(e):
#             canvas.itemconfig(win_id, width=e.width)
#         canvas.bind("<Configure>", _on_resize)

#         self._inner.bind("<Configure>",
#                          lambda e: canvas.configure(
#                              scrollregion=canvas.bbox("all")))

#         # mousewheel
#         def _wheel(e):
#             canvas.yview_scroll(int(-1*(e.delta/120)), "units")
#         canvas.bind_all("<MouseWheel>", _wheel)

#         self._populate()

#     def _populate(self):
#         p = self._inner

#         # ── page header ──────────────────────────────────────────────
#         hdr = tk.Frame(p, bg=Palette.SURFACE)
#         hdr.pack(fill="x", padx=Palette.PAD_XL, pady=(Palette.PAD_LG, 0))

#         title_block = tk.Frame(hdr, bg=Palette.SURFACE)
#         title_block.pack(side="left")
#         tk.Label(title_block, text="Evidence Analysis",
#                  font=Palette.bold(Palette.DISPLAY),
#                  fg=Palette.ON_SURFACE,
#                  bg=Palette.SURFACE).pack(anchor="w")
#         tk.Label(title_block,
#                  text="Neural Inspection & Explainable AI Module",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE).pack(anchor="w", pady=(2, 0))

#         btn_row = tk.Frame(hdr, bg=Palette.SURFACE)
#         btn_row.pack(side="right", pady=8)

#         history_btn = GoldButton(btn_row, text="Scan History",
#                                  style="outline")
#         history_btn.pack(side="left", padx=(0, Palette.PAD_SM),
#                          ipady=4, ipadx=8)

#         run_btn = GoldButton(btn_row, text="Run Analysis",
#                              style="primary",
#                              command=self._run_analysis)
#         run_btn.pack(side="left", ipady=4, ipadx=8)

#         tk.Frame(p, height=Palette.PAD_LG,
#                  bg=Palette.SURFACE).pack()

#         # ── top two-col layout ───────────────────────────────────────
#         cols = tk.Frame(p, bg=Palette.SURFACE)
#         cols.pack(fill="x", padx=Palette.PAD_XL)
#         cols.columnconfigure(0, weight=1)
#         cols.columnconfigure(1, weight=2)

#         # left card: drop zone + scan status
#         left = tk.Frame(cols, bg=Palette.SURFACE_CONTAINER)
#         left.grid(row=0, column=0, sticky="nsew",
#                   padx=(0, Palette.PAD_MD))

#         DropZone(left, bg=Palette.SURFACE_CONTAINER).pack(fill="x")

#         tk.Frame(left, height=1,
#                  bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_MD)

#         scan_area = tk.Frame(left, bg=Palette.SURFACE_CONTAINER,
#                              padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         scan_area.pack(fill="x")

#         scan_hdr = tk.Frame(scan_area, bg=Palette.SURFACE_CONTAINER)
#         scan_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
#         tk.Label(scan_hdr, text="NEURAL SCAN STATUS",
#                  font=Palette.bold(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER).pack(side="left")
#         self._pct_label = tk.Label(scan_hdr, text="74%",
#                                    font=Palette.bold(Palette.MICRO),
#                                    fg=Palette.PRIMARY,
#                                    bg=Palette.SURFACE_CONTAINER)
#         self._pct_label.pack(side="right")

#         self._prog_bar = AnimatedProgressBar(scan_area, value=0.74,
#                                              bg=Palette.SURFACE_CONTAINER)
#         self._prog_bar.pack(fill="x")

#         tk.Label(scan_area,
#                  text="⚡  Deciphering encrypted packets...",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER,
#                  anchor="w").pack(anchor="w", pady=(Palette.PAD_SM, 0))

#         # right card: SHAP explainer
#         right = tk.Frame(cols, bg=Palette.SURFACE_CONTAINER)
#         right.grid(row=0, column=1, sticky="nsew")

#         shap_header = tk.Frame(right, bg=Palette.SURFACE_CONTAINER)
#         shap_header.pack(fill="x",
#                          padx=Palette.PAD_LG, pady=(Palette.PAD_LG, 4))
#         tk.Label(shap_header, text="SHAP Global Explainer",
#                  font=Palette.bold(Palette.TITLE_LG),
#                  fg=Palette.ON_SURFACE,
#                  bg=Palette.SURFACE_CONTAINER).pack(side="left")
#         tk.Label(shap_header, text="ⓘ",
#                  font=Palette.font(Palette.TITLE_LG),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER,
#                  cursor="hand2").pack(side="right")

#         tk.Label(right,
#                  text="Impact of features on predictive outcome",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER,
#                  anchor="w").pack(fill="x",
#                                   padx=Palette.PAD_LG,
#                                   pady=(0, Palette.PAD_MD))

#         for label, val, mx in self.SHAP_DATA:
#             SHAPBar(right, label=label, value=val, max_val=mx,
#                     bg=Palette.SURFACE_CONTAINER).pack(
#                 fill="x", padx=Palette.PAD_LG)

#         tk.Frame(right, height=Palette.PAD_MD,
#                  bg=Palette.SURFACE_CONTAINER).pack()

#         # ── flagged events ───────────────────────────────────────────
#         tk.Frame(p, height=Palette.PAD_LG,
#                  bg=Palette.SURFACE).pack()

#         events_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
#         events_card.pack(fill="x", padx=Palette.PAD_XL)

#         ev_hdr = tk.Frame(events_card, bg=Palette.SURFACE_CONTAINER)
#         ev_hdr.pack(fill="x",
#                     padx=Palette.PAD_LG, pady=(Palette.PAD_LG, 0))
#         tk.Label(ev_hdr, text="Flagged Suspicious Events",
#                  font=Palette.bold(Palette.TITLE_LG),
#                  fg=Palette.ON_SURFACE,
#                  bg=Palette.SURFACE_CONTAINER).pack(side="left")
#         tk.Label(ev_hdr, text="SORT BY SCORE  ≡",
#                  font=Palette.bold(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER,
#                  cursor="hand2").pack(side="right")

#         # column headers
#         col_hdr = tk.Frame(events_card,
#                            bg=Palette.SURFACE_CONTAINER)
#         col_hdr.pack(fill="x",
#                      padx=Palette.PAD_LG,
#                      pady=(Palette.PAD_MD, Palette.PAD_SM))
#         for txt, w in [("TIMESTAMP", 20), ("EVENT ID", 14),
#                        ("THREAT SCORE", 16), ("STATUS", 12),
#                        ("ACTIONS", 8)]:
#             tk.Label(col_hdr, text=txt,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=Palette.SURFACE_CONTAINER,
#                      width=w, anchor="w").pack(side="left")

#         tk.Frame(events_card, height=1,
#                  bg=Palette.OUTLINE).pack(fill="x",
#                                           padx=Palette.PAD_LG)

#         for d in self.THREAT_DATA:
#             ThreatRow(
#                 events_card,
#                 timestamp=d["timestamp"],
#                 event_id=d["event_id"],
#                 score=d["score"],
#                 status=d["status"],
#                 lime_text=d.get("lime"),
#                 lime_pos=d.get("pos"),
#                 lime_neg=d.get("neg"),
#                 bg=Palette.SURFACE_CONTAINER,
#             ).pack(fill="x")

#         tk.Frame(p, height=Palette.PAD_XL,
#                  bg=Palette.SURFACE).pack()

#     def _run_analysis(self):
#         """Simulate a new scan progress animation."""
#         if self._prog_bar:
#             self._prog_bar.set_value(0.0)
#             self._pct_label.config(text="0%")
#             self._animate_progress(0)

#     def _animate_progress(self, step):
#         val = min(step / 100, 1.0)
#         if self._prog_bar:
#             self._prog_bar.set_value(val)
#             self._pct_label.config(text=f"{step}%")
#         if step < 100:
#             self.after(40, self._animate_progress, step + 1)


import tkinter as tk
from tkinter import ttk
import threading
import requests
from colors import Palette
from components import GoldButton, SHAPBar, AnimatedProgressBar, ThreatRow
from helper import api
from logger import get_logger

log = get_logger("ANALYSIS")


class AnalysisPage(tk.Frame):

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._prog_bar    = None
        self._pct_label   = None
        self._selected_id = None        # currently selected log_id
        self._log_map     = {}          # {display_name: log_id}
        self._shap_frame  = None        # redrawn after analysis
        self._events_frame = None       # redrawn after analysis
        self._build()
        self._load_logs()               # populate dropdown on open

    # ── layout ───────────────────────────────────────────────────────

    def _build(self):
        canvas = tk.Canvas(self, bg=Palette.SURFACE, highlightthickness=0)
        scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=Palette.SURFACE)
        win_id = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        self._inner.bind("<Configure>",
                         lambda e: canvas.configure(
                             scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1*(e.delta/120)), "units"))

        self._populate()

    def _populate(self):
        p = self._inner

        # ── page header ──────────────────────────────────────────────
        hdr = tk.Frame(p, bg=Palette.SURFACE)
        hdr.pack(fill="x", padx=Palette.PAD_XL, pady=(Palette.PAD_LG, 0))

        title_block = tk.Frame(hdr, bg=Palette.SURFACE)
        title_block.pack(side="left")
        tk.Label(title_block, text="Evidence Analysis",
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

        self._run_btn = GoldButton(btn_row, text="Run Analysis",
                                   command=self._run_analysis)
        self._run_btn.pack(side="left", ipady=4, ipadx=8)

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # ── log selector card ────────────────────────────────────────
        sel_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        sel_card.pack(fill="x", padx=Palette.PAD_XL)

        sel_inner = tk.Frame(sel_card, bg=Palette.SURFACE_CONTAINER,
                             padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        sel_inner.pack(fill="x")
        sel_inner.columnconfigure(1, weight=1)

        tk.Label(sel_inner, text="SELECT LOG FILE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).grid(row=0, column=0,
                                                     sticky="w",
                                                     padx=(0, Palette.PAD_MD))

        self._log_var = tk.StringVar(value="Loading logs…")
        self._dropdown = ttk.Combobox(
            sel_inner,
            textvariable=self._log_var,
            state="readonly",
            font=Palette.font(Palette.BODY_MD),
        )
        self._dropdown.grid(row=0, column=1, sticky="ew")
        self._dropdown.bind("<<ComboboxSelected>>", self._on_log_selected)

        # status label under selector
        self._sel_status = tk.Label(
            sel_card, text="",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER
        )
        self._sel_status.pack(anchor="w", padx=Palette.PAD_LG,
                               pady=(0, Palette.PAD_SM))

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # ── scan status card ─────────────────────────────────────────
        scan_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        scan_card.pack(fill="x", padx=Palette.PAD_XL)

        scan_inner = tk.Frame(scan_card, bg=Palette.SURFACE_CONTAINER,
                              padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        scan_inner.pack(fill="x")

        scan_hdr = tk.Frame(scan_inner, bg=Palette.SURFACE_CONTAINER)
        scan_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        tk.Label(scan_hdr, text="NEURAL SCAN STATUS",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")
        self._pct_label = tk.Label(scan_hdr, text="—",
                                   font=Palette.bold(Palette.MICRO),
                                   fg=Palette.PRIMARY,
                                   bg=Palette.SURFACE_CONTAINER)
        self._pct_label.pack(side="right")

        self._prog_bar = AnimatedProgressBar(scan_inner, value=0.0,
                                             bg=Palette.SURFACE_CONTAINER)
        self._prog_bar.pack(fill="x")

        self._scan_status_lbl = tk.Label(
            scan_inner,
            text="Select a log file and press Run Analysis.",
            font=Palette.font(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER,
            anchor="w"
        )
        self._scan_status_lbl.pack(anchor="w", pady=(Palette.PAD_SM, 0))

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # ── SHAP card (empty until results arrive) ───────────────────
        self._shap_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        self._shap_card.pack(fill="x", padx=Palette.PAD_XL)
        self._shap_frame = tk.Frame(self._shap_card,
                                    bg=Palette.SURFACE_CONTAINER)
        self._shap_frame.pack(fill="x", padx=Palette.PAD_LG,
                               pady=Palette.PAD_LG)
        tk.Label(self._shap_frame,
                 text="SHAP results will appear here after analysis.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # ── events card (empty until results arrive) ─────────────────
        self._events_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        self._events_card.pack(fill="x", padx=Palette.PAD_XL)
        self._events_frame = tk.Frame(self._events_card,
                                      bg=Palette.SURFACE_CONTAINER)
        self._events_frame.pack(fill="x", padx=Palette.PAD_LG,
                                 pady=Palette.PAD_LG)
        tk.Label(self._events_frame,
                 text="Flagged events will appear here after analysis.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(p, height=Palette.PAD_XL, bg=Palette.SURFACE).pack()

    # ── load logs into dropdown ───────────────────────────────────────

    def _load_logs(self):
        threading.Thread(target=self._fetch_logs, daemon=True).start()

    def _fetch_logs(self):
        try:
            logs = api("get", "/logs/")
            self.after(0, lambda: self._populate_dropdown(logs))
        except requests.HTTPError as exc:
            self.after(0, lambda: self._set_sel_status(
                f"Failed to load logs ({exc.response.status_code})",
                Palette.ERROR))
        except requests.ConnectionError:
            self.after(0, lambda: self._set_sel_status(
                "Cannot reach server.", Palette.ERROR))

    def _populate_dropdown(self, logs: list):
        if not logs:
            self._log_var.set("No logs uploaded yet")
            self._set_sel_status(
                "Upload a log file first via Evidence Ingestion.",
                Palette.ON_SURFACE_VAR)
            return

        self._log_map = {
            f"{l.get('original_name', l.get('filename', 'unknown'))}  "
            f"({self._fmt_size(l.get('file_size', 0))}  •  "
            f"{l.get('uploaded_at', '')[:10]})": l["id"]
            for l in logs
        }
        names = list(self._log_map.keys())
        self._dropdown["values"] = names
        self._log_var.set(names[0])
        self._selected_id = self._log_map[names[0]]
        self._set_sel_status(
            f"{len(logs)} log file(s) available.", Palette.ON_SURFACE_VAR)

    def _on_log_selected(self, _=None):
        name = self._log_var.get()
        self._selected_id = self._log_map.get(name)
        log.debug("Selected log_id=%s", self._selected_id)

    # ── run analysis ─────────────────────────────────────────────────

    def _run_analysis(self):
        if not self._selected_id:
            self._set_scan_status("Select a log file first.", Palette.WARNING)
            return

        self._run_btn.config(state="disabled", text="Running…")
        self._prog_bar.set_value(0.0)
        self._pct_label.config(text="0%")
        self._set_scan_status("⚡  Neural scan initialising…",
                               Palette.ON_SURFACE_VAR)
        self._animate_progress(0, target=70)   # fake progress to 70% while waiting

        threading.Thread(
            target=self._do_analysis,
            args=(self._selected_id,),
            daemon=True
        ).start()

    def _do_analysis(self, log_id: int):
        try:
            result = api("post", f"/analysis/run?log_id={log_id}")
            self.after(0, lambda: self._on_result(result))
        except requests.HTTPError as exc:
            try:
                msg = exc.response.json().get("detail", "Analysis failed.")
            except Exception:
                msg = f"Server error ({exc.response.status_code})"
            self.after(0, lambda: self._on_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._on_error("Cannot reach server."))
        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))

    def _on_result(self, data: dict):
        # finish progress bar
        self._animate_progress(70, target=100, on_done=lambda: (
            self._pct_label.config(text="100%"),
            self._set_scan_status(
                f"✓  Analysis complete — threat score: "
                f"{int(data.get('threat_score', 0) * 100)}%",
                Palette.SUCCESS
            )
        ))
        self._run_btn.config(state="normal", text="Run Analysis")
        self._render_shap(data.get("shap", []))
        self._render_events(data.get("events", []))

    def _on_error(self, msg: str):
        self._prog_bar.set_value(0.0)
        self._pct_label.config(text="—")
        self._set_scan_status(f"✗  {msg}", Palette.ERROR)
        self._run_btn.config(state="normal", text="Run Analysis")

    # ── render results ────────────────────────────────────────────────

    def _render_shap(self, shap_data: list):
        for w in self._shap_frame.winfo_children():
            w.destroy()

        tk.Label(self._shap_frame, text="SHAP Global Explainer",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
                                                     pady=(0, Palette.PAD_SM))
        tk.Label(self._shap_frame,
                 text="Impact of features on predictive outcome",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
                                                     pady=(0, Palette.PAD_MD))
        for item in shap_data:
            SHAPBar(self._shap_frame,
                    label=item["feature"],
                    value=item["value"],
                    max_val=item["max_val"],
                    bg=Palette.SURFACE_CONTAINER).pack(fill="x")

    def _render_events(self, events: list):
        for w in self._events_frame.winfo_children():
            w.destroy()

        tk.Label(self._events_frame,
                 text="Flagged Suspicious Events",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
                                                     pady=(0, Palette.PAD_MD))

        if not events:
            tk.Label(self._events_frame,
                     text="No suspicious events detected.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.SUCCESS,
                     bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
            return

        for d in events:
            ThreatRow(
                self._events_frame,
                timestamp=d.get("timestamp", "—"),
                event_id=d.get("event_id", "—"),
                score=d.get("score", 0),
                status=d.get("status", "UNKNOWN"),
                lime_text=d.get("lime"),
                lime_pos=d.get("pos"),
                lime_neg=d.get("neg"),
                bg=Palette.SURFACE_CONTAINER,
            ).pack(fill="x")

    # ── helpers ───────────────────────────────────────────────────────

    def _animate_progress(self, current: int, target: int,
                           on_done=None, step: int = 0):
        if current >= target:
            if on_done:
                on_done()
            return
        nxt = current + 1
        val = nxt / 100
        self._prog_bar.set_value(val)
        self._pct_label.config(text=f"{nxt}%")
        self.after(30, lambda: self._animate_progress(
            nxt, target, on_done, step + 1))

    def _set_scan_status(self, msg: str, color: str = None):
        self._scan_status_lbl.config(
            text=msg, fg=color or Palette.ON_SURFACE_VAR)

    def _set_sel_status(self, msg: str, color: str = None):
        self._sel_status.config(
            text=msg, fg=color or Palette.ON_SURFACE_VAR)

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        if not size_bytes:
            return "—"
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.0f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"