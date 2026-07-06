import tkinter as tk
from tkinter import filedialog
import threading
import requests
import os
from colors import Palette
from components import GoldButton, SHAPBar, AnimatedProgressBar, ThreatRow
from helper import api, upload
from logger import get_logger

log = get_logger("ANALYSIS")


class LogSelectorPanel(tk.Frame):
    """
    Left panel — two tabs:
      [Uploaded Logs]  [Upload New]
    Calls on_select(log_id) when a log is ready to analyse.
    """

    def __init__(self, parent, on_select=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg        = bg
        self._on_select = on_select
        self._log_map   = {}        # display_name → log_id
        self._selected_id = None
        self._build()
        self._load_logs()

    def _build(self):
        # ── tab bar ──────────────────────────────────────────────────
        tab_bar = tk.Frame(self, bg=Palette.SURFACE_HIGH)
        tab_bar.pack(fill="x")

        self._tab_btns = {}
        for i, label in enumerate(["Uploaded Logs", "Upload New"]):
            btn = tk.Label(
                tab_bar, text=label,
                font=Palette.bold(Palette.MICRO),
                bg=Palette.SURFACE_HIGH,
                fg=Palette.ON_SURFACE_VAR,
                padx=Palette.PAD_MD,
                pady=Palette.PAD_SM,
                cursor="hand2"
            )
            btn.grid(row=0, column=i, sticky="nsew")
            tab_bar.columnconfigure(i, weight=1)
            btn.bind("<Button-1>", lambda e, l=label: self._switch(l))
            self._tab_btns[label] = btn

        # ── panels ───────────────────────────────────────────────────
        self._panels = {}

        # --- Uploaded Logs panel ---
        up = tk.Frame(self, bg=self._bg)
        self._panels["Uploaded Logs"] = up

        self._status_lbl = tk.Label(
            up, text="Loading…",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=self._bg
        )
        self._status_lbl.pack(anchor="w",
                               padx=Palette.PAD_MD,
                               pady=(Palette.PAD_SM, 0))

        # scrollable log list
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
        self._list_win = self._list_canvas.create_window(
            (0, 0), window=self._log_list, anchor="nw"
        )
        self._list_canvas.bind(
            "<Configure>",
            lambda e: self._list_canvas.itemconfig(
                self._list_win, width=e.width)
        )
        self._log_list.bind(
            "<Configure>",
            lambda e: self._list_canvas.configure(
                scrollregion=self._list_canvas.bbox("all"))
        )

        # --- Upload New panel ---
        un = tk.Frame(self, bg=self._bg)
        self._panels["Upload New"] = un
        self._build_upload_panel(un)

        # show first tab
        self._switch("Uploaded Logs")

    def _build_upload_panel(self, parent):
        tk.Frame(parent, height=Palette.PAD_MD,
                 bg=self._bg).pack()

        # drop zone placeholder (static border via highlightthickness)
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

        tk.Label(dz,
                 text=".json  .csv  .pcap  .log",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGH).pack(pady=(2, Palette.PAD_MD))

        # selected file label
        self._upload_lbl = tk.Label(
            parent, text="",
            font=Palette.bold(Palette.MICRO),
            fg=Palette.PRIMARY, bg=self._bg,
            wraplength=180
        )
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

        self._upload_status = tk.Label(
            parent, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR, bg=self._bg,
            wraplength=180
        )
        self._upload_status.pack(pady=(Palette.PAD_SM, 0),
                                   padx=Palette.PAD_MD, anchor="w")

        self._pending_file = None

    # ── tab switching ─────────────────────────────────────────────────

    def _switch(self, label: str):
        # hide all
        for p in self._panels.values():
            p.pack_forget()
        # reset tab colours
        for l, btn in self._tab_btns.items():
            active = l == label
            btn.config(
                bg=Palette.SURFACE_CONTAINER if active else Palette.SURFACE_HIGH,
                fg=Palette.PRIMARY if active else Palette.ON_SURFACE_VAR
            )
        # show selected
        self._panels[label].pack(fill="both", expand=True)

    # ── load uploaded logs ────────────────────────────────────────────

    def _load_logs(self):
        threading.Thread(target=self._fetch_logs, daemon=True).start()

    def _fetch_logs(self):
        try:
            logs = api("get", "/logs/")
            self.after(0, lambda: self._render_logs(logs))
        except Exception as exc:
            self.after(0, lambda: self._status_lbl.config(
                text=f"Failed to load: {exc}", fg=Palette.ERROR))

    def _render_logs(self, logs: list):
        for w in self._log_list.winfo_children():
            w.destroy()
        self._log_map.clear()

        if not logs:
            self._status_lbl.config(text="No logs uploaded yet.")
            tk.Label(self._log_list,
                     text="Upload a file using the\n'Upload New' tab.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg,
                     justify="center").pack(pady=Palette.PAD_LG)
            return

        self._status_lbl.config(
            text=f"{len(logs)} file(s) — click to select",
            fg=Palette.ON_SURFACE_VAR
        )

        for item in logs:
            log_id  = item["id"]
            fname   = item.get("original_name", item.get("filename", "unknown"))
            size    = self._fmt_size(item.get("file_size", 0))
            date    = (item.get("uploaded_at") or "")[:10]
            display = f"{fname}\n{size}  •  {date}"
            self._log_map[log_id] = fname

            row = tk.Frame(self._log_list, bg=self._bg,
                           cursor="hand2",
                           highlightbackground=Palette.OUTLINE,
                           highlightthickness=1)
            row.pack(fill="x", pady=2)

            dot = tk.Label(row, text="○",
                           font=Palette.bold(Palette.MICRO),
                           fg=Palette.OUTLINE_BRIGHT,
                           bg=self._bg)
            dot.pack(side="left", padx=(Palette.PAD_SM, 4))

            lbl = tk.Label(row, text=display,
                           font=Palette.font(Palette.MICRO),
                           fg=Palette.ON_SURFACE,
                           bg=self._bg,
                           anchor="w", justify="left")
            lbl.pack(side="left", fill="x", expand=True,
                     pady=Palette.PAD_SM)

            # bind click on all parts of the row
            for w in (row, dot, lbl):
                w.bind("<Button-1>",
                       lambda e, lid=log_id, r=row, d=dot:
                       self._select_row(lid, r, d))

    def _select_row(self, log_id: int, row: tk.Frame, dot: tk.Label):
        # reset all rows
        for child in self._log_list.winfo_children():
            child.config(bg=self._bg,
                          highlightbackground=Palette.OUTLINE)
            for w in child.winfo_children():
                w.config(bg=self._bg)
                if isinstance(w, tk.Label) and w.cget("text") in ("○", "●"):
                    w.config(text="○", fg=Palette.OUTLINE_BRIGHT)

        # highlight selected
        row.config(bg=Palette.SURFACE_HIGH,
                    highlightbackground=Palette.PRIMARY)
        for w in row.winfo_children():
            w.config(bg=Palette.SURFACE_HIGH)
        dot.config(text="●", fg=Palette.PRIMARY)

        self._selected_id = log_id
        log.debug("Selected log_id=%s", log_id)
        if self._on_select:
            self._on_select(log_id)

    # ── upload new ────────────────────────────────────────────────────

    def _browse(self):
        f = filedialog.askopenfilename(
            title="Select Forensic Evidence File",
            filetypes=[
                ("All Supported", "*.json *.csv *.pcap *.log"),
                ("JSON", "*.json"), ("CSV", "*.csv"),
                ("PCAP", "*.pcap"), ("LOG", "*.log"),
                ("All", "*.*"),
            ]
        )
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

    def _after_upload(self, log_id: int):
        self._upload_btn.config(state="disabled", text="Upload & Analyse")
        self._upload_status.config(
            text="✓ Uploaded — running analysis…", fg=Palette.SUCCESS)
        self._pending_file = None
        self._upload_lbl.config(text="")
        # reload logs list then trigger analysis
        self._load_logs()
        if self._on_select:
            self._on_select(log_id)

    def _upload_error(self, msg: str):
        self._upload_btn.config(state="normal", text="Upload & Analyse")
        self._upload_status.config(text=f"✗ {msg}", fg=Palette.ERROR)

    def refresh(self):
        self._load_logs()

    @staticmethod
    def _fmt_size(b: int) -> str:
        if not b:
            return "—"
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.0f} {u}"
            b /= 1024
        return f"{b:.1f} TB"


# ======================================================================
#  ANALYSIS PAGE  — keeps the original two-col + events structure
# ======================================================================
class AnalysisPage(tk.Frame):

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._prog_bar     = None
        self._pct_label    = None
        self._selected_id  = None
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=Palette.SURFACE, highlightthickness=0)
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
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1*(e.delta/120)), "units"))
        self._populate()

    def _populate(self):
        p = self._inner

        # ── header ───────────────────────────────────────────────────
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
                   style="outline").pack(
            side="left", padx=(0, Palette.PAD_SM), ipady=4, ipadx=8)

        self._run_btn = GoldButton(btn_row, text="Run Analysis",
                                    command=self._run_analysis)
        self._run_btn.pack(side="left", ipady=4, ipadx=8)

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # ── two-col layout ───────────────────────────────────────────
        cols = tk.Frame(p, bg=Palette.SURFACE)
        cols.pack(fill="x", padx=Palette.PAD_XL)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=2)

        # LEFT: log selector panel (replaces static DropZone)
        left = tk.Frame(cols, bg=Palette.SURFACE_CONTAINER)
        left.grid(row=0, column=0, sticky="nsew",
                   padx=(0, Palette.PAD_MD))

        LogSelectorPanel(
            left,
            on_select=self._on_log_selected,
            bg=Palette.SURFACE_CONTAINER
        ).pack(fill="both", expand=True)

        tk.Frame(left, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_MD)

        # scan status area (same as original)
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
            bg=Palette.SURFACE_CONTAINER,
            anchor="w"
        )
        self._scan_lbl.pack(anchor="w", pady=(Palette.PAD_SM, 0))

        # RIGHT: SHAP card (same as original)
        right = tk.Frame(cols, bg=Palette.SURFACE_CONTAINER)
        right.grid(row=0, column=1, sticky="nsew")

        shap_header = tk.Frame(right, bg=Palette.SURFACE_CONTAINER)
        shap_header.pack(fill="x", padx=Palette.PAD_LG,
                          pady=(Palette.PAD_LG, 4))
        tk.Label(shap_header, text="SHAP Global Explainer",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")

        tk.Label(right,
                 text="Impact of features on predictive outcome",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER,
                 anchor="w").pack(fill="x", padx=Palette.PAD_LG,
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

        # ── flagged events (same structure as original) ───────────────
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
        tk.Label(ev_hdr, text="SORT BY SCORE  ≡",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER,
                 cursor="hand2").pack(side="right")

        col_hdr = tk.Frame(events_card, bg=Palette.SURFACE_CONTAINER)
        col_hdr.pack(fill="x", padx=Palette.PAD_LG,
                      pady=(Palette.PAD_MD, Palette.PAD_SM))
        for txt, w in [("TIMESTAMP", 20), ("EVENT ID", 14),
                        ("THREAT SCORE", 16), ("STATUS", 12),
                        ("ACTIONS", 8)]:
            tk.Label(col_hdr, text=txt,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER,
                     width=w, anchor="w").pack(side="left")

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

    # ── callbacks ─────────────────────────────────────────────────────

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
        self._animate_progress(70, 100, on_done=lambda: (
            self._pct_label.config(text="100%"),
            self._scan_lbl.config(
                text=f"✓  Complete — threat score: "
                     f"{int(data.get('threat_score', 0) * 100)}%",
                fg=Palette.SUCCESS)
        ))
        self._run_btn.config(state="normal", text="Run Analysis")
        self._render_shap(data.get("shap", []))
        self._render_events(data.get("events", []))

    def _on_error(self, msg: str):
        self._prog_bar.set_value(0.0)
        self._pct_label.config(text="—")
        self._scan_lbl.config(text=f"✗  {msg}", fg=Palette.ERROR)
        self._run_btn.config(state="normal", text="Run Analysis")

    def _render_shap(self, shap_data: list):
        for w in self._shap_frame.winfo_children():
            w.destroy()
        if not shap_data:
            tk.Label(self._shap_frame, text="No SHAP data returned.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
            return
        for item in shap_data:
            SHAPBar(self._shap_frame,
                    label=item["feature"],
                    value=item["value"],
                    max_val=item["max_val"],
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
                pady=Palette.PAD_LG, anchor="w", padx=Palette.PAD_LG)
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

    def _animate_progress(self, current: int, target: int,
                           on_done=None):
        if current >= target:
            if on_done:
                on_done()
            return
        nxt = current + 1
        self._prog_bar.set_value(nxt / 100)
        self._pct_label.config(text=f"{nxt}%")
        self.after(30, lambda: self._animate_progress(nxt, target, on_done))