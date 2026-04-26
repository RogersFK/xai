# from colors import Palette
# import tkinter as tk
# from components import GoldButton



# class MetricCard(tk.Frame):
#     """
#     Left stat card: large integrity score + gold bar.
#     Right stat cluster: total artifacts / alerts / processing time.
#     """
#     def __init__(self, parent, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
#         super().__init__(parent, bg=bg, **kw)
#         self._bg = bg
#         self._build()

#     def _build(self):
#         outer = tk.Frame(self, bg=self._bg)
#         outer.pack(fill="x", padx=0, pady=0)
#         outer.columnconfigure(0, weight=1)
#         outer.columnconfigure(1, weight=2)

#         # ── left: integrity score ─────────────────────────────────────
#         left = tk.Frame(outer, bg=self._bg,
#                         padx=Palette.PAD_LG, pady=Palette.PAD_LG)
#         left.grid(row=0, column=0, sticky="nsew")

#         tk.Label(left, text="INTEGRITY SCORE",
#                  font=Palette.bold(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=self._bg).pack(anchor="w")

#         score_row = tk.Frame(left, bg=self._bg)
#         score_row.pack(anchor="w", pady=(Palette.PAD_SM, 0))

#         tk.Label(score_row, text="98.4",
#                  font=(Palette._FONT[0], 48, "bold"),
#                  fg=Palette.ON_SURFACE,
#                  bg=self._bg).pack(side="left")
#         tk.Label(score_row, text="%",
#                  font=Palette.bold(Palette.TITLE_LG),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=self._bg).pack(side="left", anchor="s", pady=(0,8))

#         # verified badge
#         tk.Label(score_row, text="✔",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.PRIMARY,
#                  bg=self._bg).pack(side="right", padx=Palette.PAD_LG)

#         # gold progress bar (static)
#         bar_track = tk.Frame(left, bg=Palette.SURFACE_HIGH, height=6)
#         bar_track.pack(fill="x", pady=(Palette.PAD_SM, 0))
#         bar_fill = tk.Frame(bar_track, bg=Palette.PRIMARY, height=6)
#         bar_fill.place(relx=0, rely=0, relwidth=0.984, relheight=1)

#         # divider
#         tk.Frame(outer, bg=Palette.OUTLINE,
#                  width=1).grid(row=0, column=0, sticky="nse", padx=(0,0))

#         # ── right: stats + info ───────────────────────────────────────
#         right = tk.Frame(outer, bg=self._bg)
#         right.grid(row=0, column=1, sticky="nsew")

#         stats_row = tk.Frame(right, bg=self._bg)
#         stats_row.pack(fill="x", padx=Palette.PAD_LG,
#                        pady=(Palette.PAD_LG, Palette.PAD_SM))

#         for label, val, color in [
#             ("TOTAL ARTIFACTS", "14,208", Palette.ON_SURFACE),
#             ("ALERTS LEVEL 5",  "12",     Palette.ERROR),
#             ("PROCESSING TIME", "1.4s",   Palette.ON_SURFACE),
#         ]:
#             blk = tk.Frame(stats_row, bg=self._bg)
#             blk.pack(side="left", padx=(0, Palette.PAD_XL))
#             tk.Label(blk, text=label,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=self._bg).pack(anchor="w")
#             tk.Label(blk, text=val,
#                      font=(Palette._FONT[0], 26, "bold"),
#                      fg=color, bg=self._bg).pack(anchor="w")

#         # info banner
#         info_banner = tk.Frame(right, bg=Palette.SURFACE_HIGH,
#                                padx=Palette.PAD_MD, pady=Palette.PAD_SM)
#         info_banner.pack(fill="x",
#                          padx=Palette.PAD_LG,
#                          pady=(0, Palette.PAD_LG))
#         tk.Label(info_banner, text="ℹ",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_HIGH).pack(side="left",
#                                                padx=(0, Palette.PAD_SM))
#         tk.Label(info_banner,
#                  text=("Report reflects automated analysis of kernel memory "
#                        "dumps and network packets from Node-12C."),
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_HIGH,
#                  wraplength=420, justify="left").pack(side="left")


# class BarChart(tk.Canvas):
#     """
#     Canvas bar chart — Threat Vector Distribution.
#     Animates bars on first draw.
#     """
#     CHART_H = 200
#     BAR_W   = 40
#     GAP     = 60

#     VECTORS = [
#         ("VEC_A", 0.82),
#         ("VEC_B", 0.55),
#         ("VEC_C", 0.38),
#         ("VEC_D", 0.67),
#         ("VEC_E", 0.21),
#     ]

#     def __init__(self, parent, bg=None, **kw):
#         bg = bg or Palette.SURFACE_CONTAINER
#         super().__init__(parent, bg=bg, highlightthickness=0,
#                          height=self.CHART_H + 40, **kw)
#         self._bg     = bg
#         self._anim   = 0.0
#         self._target = 1.0
#         self.bind("<Configure>", lambda e: self._redraw())
#         self.after(50, self._animate)

#     def _animate(self):
#         if self._anim < self._target:
#             self._anim = min(self._anim + 0.05, self._target)
#             self._redraw()
#             self.after(16, self._animate)
#         else:
#             self._redraw()

#     def _ease(self, t):
#         return t * t * (3 - 2*t)

#     def _redraw(self):
#         self.delete("all")
#         w = self.winfo_width()
#         h = self.winfo_height()
#         if w < 10: return

#         ch      = self.CHART_H
#         bw      = self.BAR_W
#         n       = len(self.VECTORS)
#         total_w = n * bw + (n-1) * self.GAP
#         x_off   = max(20, (w - total_w) // 2)
#         y_base  = ch + 10
#         prog    = self._ease(self._anim)

#         # horizontal grid lines
#         for i in range(1, 5):
#             y = y_base - int(ch * i / 4)
#             self.create_line(x_off - 10, y, x_off + total_w + 10, y,
#                              fill=Palette.OUTLINE, dash=(4, 4))
#             self.create_text(x_off - 14, y,
#                              text=f"{i*25}%",
#                              font=Palette.font(Palette.MICRO),
#                              fill=Palette.ON_SURFACE_VAR,
#                              anchor="e")

#         for i, (label, val) in enumerate(self.VECTORS):
#             x   = x_off + i * (bw + self.GAP)
#             bar_h = int(ch * val * prog)

#             # gradient bar
#             c0 = (0xf2, 0xca, 0x50)
#             c1 = (0xd4, 0xaf, 0x37)
#             for row in range(bar_h):
#                 t   = row / max(bar_h-1, 1)
#                 col = "#{:02x}{:02x}{:02x}".format(
#                     int(c0[0]+(c1[0]-c0[0])*(1-t)),
#                     int(c0[1]+(c1[1]-c0[1])*(1-t)),
#                     int(c0[2]+(c1[2]-c0[2])*(1-t)),
#                 )
#                 self.create_line(x, y_base-row, x+bw, y_base-row,
#                                  fill=col, width=1)

#             # value label on top
#             if bar_h > 0:
#                 self.create_text(x + bw//2, y_base - bar_h - 8,
#                                  text=f"{int(val*100)}%",
#                                  font=Palette.bold(Palette.MICRO),
#                                  fill=Palette.PRIMARY)

#             # x-axis label
#             self.create_text(x + bw//2, y_base + 16,
#                              text=label,
#                              font=Palette.font(Palette.MICRO),
#                              fill=Palette.ON_SURFACE_VAR)

#         # baseline
#         self.create_line(x_off - 10, y_base,
#                          x_off + total_w + 10, y_base,
#                          fill=Palette.OUTLINE_BRIGHT, width=1)


# class ArtifactRow(tk.Frame):
#     """Single row in the Critical Artifacts table."""
#     STATUS_COL = {
#         "CRITICAL": Palette.ERROR,
#         "WARNING":  Palette.WARNING,
#         "BENIGN":   Palette.ON_SURFACE_VAR,
#     }

#     def __init__(self, parent, timestamp, source, action, status, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
#         super().__init__(parent, bg=bg, **kw)
#         self._bg = bg
#         self._build(timestamp, source, action, status)

#     def _build(self, timestamp, source, action, status):
#         row = tk.Frame(self, bg=self._bg, pady=Palette.PAD_SM)
#         row.pack(fill="x", padx=Palette.PAD_LG)

#         color = self.STATUS_COL.get(status, Palette.ON_SURFACE_VAR)

#         for text, width, anchor, bold in [
#             (timestamp, 22, "w", False),
#             (source,    16, "w", True),
#             (action,    22, "w", False),
#         ]:
#             tk.Label(row, text=text,
#                      font=Palette.bold(Palette.BODY) if bold else Palette.font(Palette.BODY),
#                      fg=Palette.ON_SURFACE if bold else Palette.ON_SURFACE_VAR,
#                      bg=self._bg, width=width, anchor=anchor).pack(side="left")

#         tk.Label(row, text=status,
#                  font=Palette.bold(Palette.LABEL),
#                  fg=color, bg=self._bg,
#                  anchor="w", width=10).pack(side="left", padx=Palette.PAD_MD)

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(
#             fill="x", padx=Palette.PAD_LG)


# class MetadataPanel(tk.Frame):
#     """
#     Right sidebar: case metadata, investigator notes, crypto proof.
#     """
#     def __init__(self, parent, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
#         super().__init__(parent, bg=bg, **kw)
#         self._bg = bg
#         self._build()

#     def _build(self):
#         # metadata block
#         meta = tk.Frame(self, bg=self._bg,
#                         padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         meta.pack(fill="x")

#         hdr = tk.Frame(meta, bg=self._bg)
#         hdr.pack(fill="x", pady=(0, Palette.PAD_MD))
#         tk.Label(hdr, text="ℹ",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY, bg=self._bg).pack(side="left", padx=(0,6))
#         tk.Label(hdr, text="Metadata",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.ON_SURFACE, bg=self._bg).pack(side="left")

#         for field, value in [
#             ("CASE NUMBER",      "F-089-ALPHA-Z"),
#             ("HASH VERIFICATION","SHA256: 8e9c349e2e2e\n2e2e2f313131b8b8b8b8\nb8b8b8b8"),
#             ("CHAIN OF CUSTODY", "Verified by AI-Core 01"),
#         ]:
#             tk.Label(meta, text=field,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=self._bg, anchor="w").pack(fill="x",
#                                                    pady=(Palette.PAD_SM, 2))
#             tk.Label(meta, text=value,
#                      font=Palette.font(Palette.LABEL),
#                      fg=Palette.ON_SURFACE,
#                      bg=self._bg, anchor="w",
#                      justify="left").pack(fill="x")

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

#         # investigator notes
#         notes = tk.Frame(self, bg=self._bg,
#                          padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         notes.pack(fill="x")

#         tk.Label(notes, text="Investigator Notes",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.ON_SURFACE, bg=self._bg).pack(anchor="w",
#                                                           pady=(0, Palette.PAD_SM))

#         txt = tk.Text(notes, height=6,
#                       font=Palette.font(Palette.LABEL),
#                       fg=Palette.ON_SURFACE_VAR,
#                       bg=Palette.SURFACE_HIGH,
#                       insertbackground=Palette.PRIMARY,
#                       relief="flat", bd=0,
#                       padx=8, pady=8,
#                       wrap="word",
#                       highlightthickness=1,
#                       highlightbackground=Palette.OUTLINE,
#                       highlightcolor=Palette.PRIMARY)
#         txt.insert("1.0", "Enter findings or observations...")
#         txt.bind("<FocusIn>", lambda e: (
#             txt.delete("1.0","end") if txt.get("1.0","end-1c")=="Enter findings or observations..." else None,
#             txt.config(fg=Palette.ON_SURFACE)
#         ))
#         txt.pack(fill="x")

#         tk.Frame(notes, height=Palette.PAD_SM, bg=self._bg).pack()

#         append_btn = GoldButton(notes, text="APPEND TO LOG",
#                                 style="primary",
#                                 command=lambda: None)
#         append_btn.pack(fill="x", ipady=6)

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

#         # crypto proof
#         proof = tk.Frame(self, bg=self._bg,
#                          padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         proof.pack(fill="x")

#         proof_hdr = tk.Frame(proof, bg=self._bg)
#         proof_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
#         tk.Label(proof_hdr, text="✔",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.SUCCESS,
#                  bg=self._bg).pack(side="left", padx=(0,6))
#         tk.Label(proof_hdr, text="Cryptographic Proof",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.ON_SURFACE,
#                  bg=self._bg).pack(side="left")

#         tk.Label(proof,
#                  text=("This report is digitally signed and timestamped "
#                        "on the secure XAI ledger. Any modification will "
#                        "invalidate the forensic integrity."),
#                  font=Palette.font(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=self._bg,
#                  wraplength=160, justify="left").pack(anchor="w")


# # ======================================================================
# #  REPORTS PAGE
# # ======================================================================
# class ReportsPage(tk.Frame):
#     ARTIFACTS = [
#         ("2024-10-24  14:22:01", "SYS_DAEMON_12",  "Access Token Replay",  "CRITICAL"),
#         ("2024-10-24  14:21:44", "USRTMP_CACHE",   "Privilege Escalation", "WARNING"),
#         ("2024-10-24  14:19:12", "NET_FLOW_X",     "Beaconing Detected",   "CRITICAL"),
#     ]

#     def __init__(self, parent,user=None, on_profile_updated=None, **kw):
#         super().__init__(parent, bg=Palette.SURFACE, **kw)
#         self._build()

#     def _build(self):
#         # scrollable wrapper
#         canvas = tk.Canvas(self, bg=Palette.SURFACE, highlightthickness=0)
#         scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
#         canvas.configure(yscrollcommand=scroll.set)
#         scroll.pack(side="right", fill="y")
#         canvas.pack(side="left", fill="both", expand=True)

#         inner = tk.Frame(canvas, bg=Palette.SURFACE)
#         win   = canvas.create_window((0,0), window=inner, anchor="nw")

#         canvas.bind("<Configure>",
#                     lambda e: canvas.itemconfig(win, width=e.width))
#         inner.bind("<Configure>",
#                    lambda e: canvas.configure(
#                        scrollregion=canvas.bbox("all")))
#         canvas.bind_all("<MouseWheel>",
#                         lambda e: canvas.yview_scroll(
#                             int(-1*(e.delta/120)), "units"))

#         self._populate(inner)

#     def _populate(self, p):
#         # ── breadcrumb + title ───────────────────────────────────────
#         bc = tk.Frame(p, bg=Palette.SURFACE)
#         bc.pack(fill="x", padx=Palette.PAD_XL,
#                 pady=(Palette.PAD_LG, 0))
#         tk.Label(bc, text="Archives",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE, cursor="hand2").pack(side="left")
#         tk.Label(bc, text="  /  ",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.OUTLINE_BRIGHT,
#                  bg=Palette.SURFACE).pack(side="left")
#         tk.Label(bc, text="Current Report",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE).pack(side="left")

#         # title + export buttons
#         title_row = tk.Frame(p, bg=Palette.SURFACE)
#         title_row.pack(fill="x", padx=Palette.PAD_XL,
#                        pady=(Palette.PAD_SM, 0))

#         title_block = tk.Frame(title_row, bg=Palette.SURFACE)
#         title_block.pack(side="left", fill="x", expand=True)
#         tk.Label(title_block,
#                  text="Forensic Incident Report: #XAI-2024-089",
#                  font=Palette.bold(Palette.DISPLAY),
#                  fg=Palette.ON_SURFACE,
#                  bg=Palette.SURFACE,
#                  wraplength=580, justify="left").pack(anchor="w")
#         tk.Label(title_block,
#                  text="Generated on October 24, 2024  •  Security Clearance Level 3 Required",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE).pack(anchor="w", pady=(4, 0))

#         btn_row = tk.Frame(title_row, bg=Palette.SURFACE)
#         btn_row.pack(side="right", anchor="s", pady=Palette.PAD_SM)
#         for lbl, icon in [("PDF","📄"),("Word","📝"),("CSV","📊")]:
#             b = GoldButton(btn_row, text=lbl, icon=icon,
#                            style="outline")
#             b.pack(side="left", padx=(0, Palette.PAD_SM),
#                    ipady=4, ipadx=10)

#         tk.Frame(p, height=Palette.PAD_LG,
#                  bg=Palette.SURFACE).pack()

#         # ── metric strip ─────────────────────────────────────────────
#         metric = MetricCard(p, bg=Palette.SURFACE_CONTAINER)
#         metric.pack(fill="x", padx=Palette.PAD_XL)

#         # gold accent line below metric card
#         tk.Frame(p, height=3,
#                  bg=Palette.PRIMARY).pack(
#                      fill="x",
#                      padx=Palette.PAD_XL,
#                      pady=(0, Palette.PAD_LG))

#         # ── two-col: report body | right sidebar ─────────────────────
#         body_row = tk.Frame(p, bg=Palette.SURFACE)
#         body_row.pack(fill="x", padx=Palette.PAD_XL)
#         body_row.columnconfigure(0, weight=3)
#         body_row.columnconfigure(1, weight=1)

#         # ── left: report sections ────────────────────────────────────
#         left = tk.Frame(body_row, bg=Palette.SURFACE_CONTAINER)
#         left.grid(row=0, column=0, sticky="nsew",
#                   padx=(0, Palette.PAD_MD))

#         # I. Executive Summary
#         self._section(left, "I. EXECUTIVE SUMMARY",
#                       ("Analysis conducted on forensic node 01 reveals an "
#                        "unauthorized lateral movement attempt originating "
#                        "from internal IP 192.168.1.45. The \"Silent Authority\" "
#                        "detection algorithm identified anomalous credential "
#                        "harvesting signatures targeting the root directory. "
#                        "Initial penetration was achieved via a CVE-2024-21887 "
#                        "vulnerability on the perimeter gateway."))

#         # II. Threat Vector Distribution
#         sec2 = tk.Frame(left, bg=Palette.SURFACE_CONTAINER)
#         sec2.pack(fill="x", padx=Palette.PAD_LG,
#                   pady=(0, Palette.PAD_LG))
#         tk.Label(sec2, text="II. THREAT VECTOR DISTRIBUTION",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
#                                                     pady=(0, Palette.PAD_SM))
#         BarChart(sec2, bg=Palette.SURFACE_CONTAINER).pack(fill="x")

#         # III. Critical Artifacts
#         sec3 = tk.Frame(left, bg=Palette.SURFACE_CONTAINER)
#         sec3.pack(fill="x", padx=Palette.PAD_LG,
#                   pady=(0, Palette.PAD_LG))
#         tk.Label(sec3, text="III. CRITICAL ARTIFACTS",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_CONTAINER).pack(
#                      anchor="w", pady=(0, Palette.PAD_SM))

#         # table header
#         col_hdr = tk.Frame(sec3, bg=Palette.SURFACE_CONTAINER)
#         col_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
#         for txt, w in [("TIMESTAMP",22),("SOURCE",16),
#                        ("ACTION",22),("STATUS",10)]:
#             tk.Label(col_hdr, text=txt,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=Palette.SURFACE_CONTAINER,
#                      width=w, anchor="w").pack(side="left")

#         tk.Frame(sec3, height=1,
#                  bg=Palette.OUTLINE).pack(fill="x",
#                                           pady=(0, Palette.PAD_SM))

#         for ts, src, act, st in self.ARTIFACTS:
#             ArtifactRow(sec3, ts, src, act, st,
#                         bg=Palette.SURFACE_CONTAINER).pack(fill="x")

#         tk.Frame(left, height=Palette.PAD_LG,
#                  bg=Palette.SURFACE_CONTAINER).pack()

#         # ── right sidebar ─────────────────────────────────────────────
#         right_panel = MetadataPanel(body_row,
#                                     bg=Palette.SURFACE_CONTAINER)
#         right_panel.grid(row=0, column=1, sticky="nsew")

#         tk.Frame(p, height=Palette.PAD_XL,
#                  bg=Palette.SURFACE).pack()

#     def _section(self, parent, title, body):
#         frame = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
#         frame.pack(fill="x", padx=Palette.PAD_LG,
#                    pady=(Palette.PAD_LG, Palette.PAD_MD))
#         tk.Label(frame, text=title,
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
#                                                     pady=(0, Palette.PAD_SM))
#         tk.Label(frame, text=body,
#                  font=Palette.font(Palette.BODY),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER,
#                  wraplength=520, justify="left").pack(anchor="w")

from colors import Palette
import tkinter as tk
import threading
import requests
from tkinter import messagebox
from components import GoldButton
from helper import api
from logger import get_logger

log = get_logger("REPORTS")


# ── BarChart ──────────────────────────────────────────────────────────

class BarChart(tk.Canvas):
    CHART_H = 200
    BAR_W   = 40
    GAP     = 60

    def __init__(self, parent, vectors=None, bg=None, **kw):
        bg = bg or Palette.SURFACE_CONTAINER
        super().__init__(parent, bg=bg, highlightthickness=0,
                         height=self.CHART_H + 40, **kw)
        self._bg      = bg
        self._vectors = vectors or []
        self._anim    = 0.0
        self.bind("<Configure>", lambda e: self._redraw())
        self.after(50, self._animate)

    def set_vectors(self, vectors: list):
        self._vectors = vectors
        self._anim    = 0.0
        self.after(50, self._animate)

    def _animate(self):
        if self._anim < 1.0:
            self._anim = min(self._anim + 0.05, 1.0)
            self._redraw()
            self.after(16, self._animate)
        else:
            self._redraw()

    def _ease(self, t):
        return t * t * (3 - 2*t)

    def _redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or not self._vectors:
            return

        ch      = self.CHART_H
        bw      = self.BAR_W
        n       = len(self._vectors)
        total_w = n * bw + (n-1) * self.GAP
        x_off   = max(20, (w - total_w) // 2)
        y_base  = ch + 10
        prog    = self._ease(self._anim)

        # grid lines
        for i in range(1, 5):
            y = y_base - int(ch * i / 4)
            self.create_line(x_off-10, y, x_off+total_w+10, y,
                             fill=Palette.OUTLINE, dash=(4, 4))
            self.create_text(x_off-14, y,
                             text=f"{i*25}%",
                             font=Palette.font(Palette.MICRO),
                             fill=Palette.ON_SURFACE_VAR,
                             anchor="e")

        for i, vec in enumerate(self._vectors):
            label = vec.get("label", f"VEC_{i}")
            val   = float(vec.get("percentage", 0)) / 100
            x     = x_off + i * (bw + self.GAP)
            bar_h = int(ch * val * prog)

            c0, c1 = (0xf2, 0xca, 0x50), (0xd4, 0xaf, 0x37)
            for row in range(bar_h):
                t   = row / max(bar_h-1, 1)
                col = "#{:02x}{:02x}{:02x}".format(
                    int(c0[0]+(c1[0]-c0[0])*(1-t)),
                    int(c0[1]+(c1[1]-c0[1])*(1-t)),
                    int(c0[2]+(c1[2]-c0[2])*(1-t)),
                )
                self.create_line(x, y_base-row, x+bw, y_base-row,
                                 fill=col, width=1)

            if bar_h > 0:
                self.create_text(x+bw//2, y_base-bar_h-8,
                                 text=f"{int(val*100)}%",
                                 font=Palette.bold(Palette.MICRO),
                                 fill=Palette.PRIMARY)

            self.create_text(x+bw//2, y_base+16,
                             text=label,
                             font=Palette.font(Palette.MICRO),
                             fill=Palette.ON_SURFACE_VAR)

        self.create_line(x_off-10, y_base,
                         x_off+total_w+10, y_base,
                         fill=Palette.OUTLINE_BRIGHT, width=1)


# ── MetricCard ────────────────────────────────────────────────────────

class MetricCard(tk.Frame):
    def __init__(self, parent, data: dict = None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg   = bg
        self._data = data or {}
        self._build()

    def _build(self):
        d   = self._data
        bg  = self._bg

        outer = tk.Frame(self, bg=bg)
        outer.pack(fill="x")
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)

        # ── left: integrity score ─────────────────────────────────────
        left = tk.Frame(outer, bg=bg,
                        padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        left.grid(row=0, column=0, sticky="nsew")

        tk.Label(left, text="INTEGRITY SCORE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")

        score     = d.get("integrity_score", 0.0)
        score_str = f"{score:.1f}"

        score_row = tk.Frame(left, bg=bg)
        score_row.pack(anchor="w", pady=(Palette.PAD_SM, 0))
        tk.Label(score_row, text=score_str,
                 font=(Palette._FONT[0], 48, "bold"),
                 fg=Palette.ON_SURFACE, bg=bg).pack(side="left")
        tk.Label(score_row, text="%",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE_VAR, bg=bg).pack(
            side="left", anchor="s", pady=(0, 8))
        tk.Label(score_row, text="✔",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY, bg=bg).pack(
            side="right", padx=Palette.PAD_LG)

        bar_track = tk.Frame(left, bg=Palette.SURFACE_HIGH, height=6)
        bar_track.pack(fill="x", pady=(Palette.PAD_SM, 0))
        tk.Frame(bar_track, bg=Palette.PRIMARY, height=6).place(
            relx=0, rely=0,
            relwidth=min(score/100, 1.0),
            relheight=1)

        # ── right: stats ──────────────────────────────────────────────
        right = tk.Frame(outer, bg=bg)
        right.grid(row=0, column=1, sticky="nsew")

        stats_row = tk.Frame(right, bg=bg)
        stats_row.pack(fill="x", padx=Palette.PAD_LG,
                       pady=(Palette.PAD_LG, Palette.PAD_SM))

        total      = d.get("total_artifacts", 0)
        alerts     = d.get("alerts_critical", 0)
        proc_time  = d.get("processing_time", 0.0)

        for label, val, color in [
            ("TOTAL ARTIFACTS", f"{total:,}",    Palette.ON_SURFACE),
            ("ALERTS CRITICAL", str(alerts),      Palette.ERROR),
            ("PROCESSING TIME", f"{proc_time:.1f}s", Palette.ON_SURFACE),
        ]:
            blk = tk.Frame(stats_row, bg=bg)
            blk.pack(side="left", padx=(0, Palette.PAD_XL))
            tk.Label(blk, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")
            tk.Label(blk, text=val,
                     font=(Palette._FONT[0], 26, "bold"),
                     fg=color, bg=bg).pack(anchor="w")

        # info banner
        info = tk.Frame(right, bg=Palette.SURFACE_HIGH,
                        padx=Palette.PAD_MD, pady=Palette.PAD_SM)
        info.pack(fill="x", padx=Palette.PAD_LG,
                  pady=(0, Palette.PAD_LG))
        tk.Label(info, text="ℹ",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH).pack(side="left",
                                                padx=(0, Palette.PAD_SM))

        coc = d.get("chain_of_custody", "—")
        tk.Label(info, text=coc,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGH,
                 wraplength=380, justify="left").pack(side="left")


# ── ArtifactRow ───────────────────────────────────────────────────────

class ArtifactRow(tk.Frame):
    STATUS_COL = {
        "CRITICAL": Palette.ERROR,
        "WARNING":  Palette.WARNING,
        "BENIGN":   Palette.ON_SURFACE_VAR,
    }

    def __init__(self, parent, item: dict, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(item, bg)

    def _build(self, item: dict, bg: str):
        row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_LG)

        status    = (item.get("status") or "").upper()
        color     = self.STATUS_COL.get(status, Palette.ON_SURFACE_VAR)
        timestamp = item.get("timestamp", "—")
        source    = item.get("source", "—")
        action    = item.get("action", "—")

        for text, width, bold in [
            (timestamp, 22, False),
            (source,    16, True),
            (action,    22, False),
        ]:
            tk.Label(row, text=text,
                     font=Palette.bold(Palette.BODY) if bold
                          else Palette.font(Palette.BODY),
                     fg=Palette.ON_SURFACE if bold
                        else Palette.ON_SURFACE_VAR,
                     bg=bg, width=width, anchor="w").pack(side="left")

        tk.Label(row, text=status,
                 font=Palette.bold(Palette.LABEL),
                 fg=color, bg=bg,
                 anchor="w", width=10).pack(side="left",
                                             padx=Palette.PAD_MD)

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_LG)


# ── MetadataPanel ─────────────────────────────────────────────────────

class MetadataPanel(tk.Frame):
    def __init__(self, parent, report: dict = None,
                 on_save_notes=None, on_sign=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg           = bg
        self._report       = report or {}
        self._on_save_notes = on_save_notes
        self._on_sign       = on_sign
        self._build()

    def _build(self):
        r  = self._report
        bg = self._bg

        # metadata
        meta = tk.Frame(self, bg=bg,
                        padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        meta.pack(fill="x")

        hdr = tk.Frame(meta, bg=bg)
        hdr.pack(fill="x", pady=(0, Palette.PAD_MD))
        tk.Label(hdr, text="ℹ",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(side="left",
                                                  padx=(0, 6))
        tk.Label(hdr, text="Metadata",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.ON_SURFACE, bg=bg).pack(side="left")

        metric = r.get("metric_card", {})
        signed_at = r.get("signed_at")
        signed_str = str(signed_at)[:19] if signed_at else "Not signed"

        for field, value in [
            ("CASE NUMBER",       r.get("case_number", "—")),
            ("STATUS",            r.get("status", "—").upper()),
            ("CLEARANCE LEVEL",   f"Level {r.get('clearance_level', '—')}"),
            ("HASH SHA-256",      metric.get("hash_sha256", "—")),
            ("GENERATED",         str(r.get("generated_at", ""))[:10]),
            ("SIGNED AT",         signed_str),
        ]:
            tk.Label(meta, text=field,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg, anchor="w").pack(
                fill="x", pady=(Palette.PAD_SM, 2))
            color = (Palette.SUCCESS if value in ("SIGNED", "DRAFT")
                     else Palette.ON_SURFACE)
            tk.Label(meta, text=value,
                     font=Palette.font(Palette.LABEL),
                     fg=color, bg=bg,
                     anchor="w", justify="left",
                     wraplength=160).pack(fill="x")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # investigator notes
        notes = tk.Frame(self, bg=bg,
                         padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        notes.pack(fill="x")

        tk.Label(notes, text="Investigator Notes",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.ON_SURFACE, bg=bg).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        self._notes_txt = tk.Text(
            notes, height=6,
            font=Palette.font(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_HIGH,
            insertbackground=Palette.PRIMARY,
            relief="flat", bd=0,
            padx=8, pady=8, wrap="word",
            highlightthickness=1,
            highlightbackground=Palette.OUTLINE,
            highlightcolor=Palette.PRIMARY)

        placeholder = "Enter findings or observations..."
        self._notes_txt.insert("1.0", placeholder)
        self._notes_txt.bind("<FocusIn>", lambda e: (
            self._notes_txt.delete("1.0", "end")
            if self._notes_txt.get("1.0", "end-1c") == placeholder
            else None,
            self._notes_txt.config(fg=Palette.ON_SURFACE)
        ))
        self._notes_txt.pack(fill="x")

        tk.Frame(notes, height=Palette.PAD_SM, bg=bg).pack()

        self._notes_status = tk.Label(
            notes, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.SUCCESS, bg=bg)
        self._notes_status.pack(anchor="w")

        GoldButton(notes, text="APPEND TO LOG",
                   command=self._save_notes).pack(
            fill="x", ipady=6)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # sign button
        sign_frame = tk.Frame(self, bg=bg,
                              padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        sign_frame.pack(fill="x")

        signed = r.get("status", "") == "signed"
        if signed:
            tk.Label(sign_frame, text="✔  Report Signed",
                     font=Palette.bold(Palette.LABEL),
                     fg=Palette.SUCCESS, bg=bg).pack(anchor="w")
        else:
            GoldButton(sign_frame, text="Sign Report",
                       command=self._sign).pack(fill="x", ipady=6)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # crypto proof
        proof = tk.Frame(self, bg=bg,
                         padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        proof.pack(fill="x")

        proof_hdr = tk.Frame(proof, bg=bg)
        proof_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        tk.Label(proof_hdr, text="✔",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.SUCCESS, bg=bg).pack(side="left",
                                                  padx=(0, 6))
        tk.Label(proof_hdr, text="Cryptographic Proof",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE, bg=bg).pack(side="left")

        tk.Label(proof,
                 text=("This report is digitally signed and timestamped "
                       "on the secure XAI ledger. Any modification will "
                       "invalidate the forensic integrity."),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR, bg=bg,
                 wraplength=160, justify="left").pack(anchor="w")

    def _save_notes(self):
        text = self._notes_txt.get("1.0", "end-1c").strip()
        if not text or text == "Enter findings or observations...":
            return
        if self._on_save_notes:
            self._on_save_notes(text)
            self._notes_status.config(text="✓ Saved")
            self.after(2000, lambda: self._notes_status.config(text=""))

    def _sign(self):
        if self._on_sign:
            self._on_sign()


# ── Report List Panel (left sidebar) ─────────────────────────────────

class ReportListPanel(tk.Frame):
    def __init__(self, parent, on_select=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_LOW)
        super().__init__(parent, bg=bg, **kw)
        self._bg        = bg
        self._on_select = on_select
        self._sel_row   = None
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=self._bg,
                       padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="REPORTS",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg).pack(side="left")

        refresh = tk.Label(hdr, text="↻",
                           font=Palette.bold(Palette.LABEL),
                           fg=Palette.ON_SURFACE_VAR,
                           bg=self._bg, cursor="hand2")
        refresh.pack(side="right")
        refresh.bind("<Button-1>", lambda e: self._load())
        refresh.bind("<Enter>",
                     lambda e: refresh.config(fg=Palette.PRIMARY))
        refresh.bind("<Leave>",
                     lambda e: refresh.config(
                         fg=Palette.ON_SURFACE_VAR))

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        canvas = tk.Canvas(self, bg=self._bg, highlightthickness=0)
        sb     = tk.Scrollbar(self, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._list = tk.Frame(canvas, bg=self._bg)
        win = canvas.create_window((0, 0), window=self._list,
                                    anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        self._list.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))

        self._status = tk.Label(
            self._list, text="Loading…",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR, bg=self._bg)
        self._status.pack(pady=Palette.PAD_LG)

    def _load(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            data = api("get", "/reports/")
            self.after(0, lambda: self._render(data))
        except Exception as exc:
            self.after(0, lambda: self._status.config(
                text=f"Failed: {exc}", fg=Palette.ERROR))

    def _render(self, items: list):
        for w in self._list.winfo_children():
            w.destroy()

        if not items:
            tk.Label(self._list,
                     text="No reports yet.\nGenerate one from\nthe Analysis page.",
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg, justify="center").pack(
                pady=Palette.PAD_LG)
            return

        STATUS_COLOR = {"signed": Palette.SUCCESS,
                        "draft":  Palette.WARNING}

        for item in items:
            rid     = item["id"]
            title   = item.get("title", f"Report #{rid}")
            case    = item.get("case_number", "")
            status  = item.get("status", "draft").lower()
            date    = str(item.get("generated_at", ""))[:10]
            s_color = STATUS_COLOR.get(status, Palette.ON_SURFACE_VAR)

            row = tk.Frame(self._list, bg=self._bg,
                            cursor="hand2",
                            padx=Palette.PAD_MD, pady=Palette.PAD_SM)
            row.pack(fill="x")

            # status dot — pack right first
            tk.Label(row, text="●",
                     font=Palette.bold(Palette.MICRO),
                     fg=s_color, bg=self._bg).pack(side="right")

            # content
            tk.Label(row, text=title,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE,
                     bg=self._bg, anchor="w",
                     wraplength=160).pack(anchor="w")
            tk.Label(row,
                     text=f"{case}  •  {date}",
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg, anchor="w").pack(anchor="w")

            tk.Frame(self._list, height=1,
                     bg=Palette.OUTLINE).pack(fill="x")

            def _enter(e, r=row):
                r.config(bg=Palette.SURFACE_HIGH)
                for w in r.winfo_children():
                    w.config(bg=Palette.SURFACE_HIGH)

            def _leave(e, r=row, rid=rid):
                bg = (Palette.SURFACE_CONTAINER
                      if self._sel_row == rid
                      else self._bg)
                r.config(bg=bg)
                for w in r.winfo_children():
                    w.config(bg=bg)

            def _click(e, rid=rid, r=row):
                self._sel_row = rid
                if self._on_select:
                    self._on_select(rid)

            for w in [row] + list(row.winfo_children()):
                w.bind("<Enter>",    _enter)
                w.bind("<Leave>",    _leave)
                w.bind("<Button-1>", _click)

        # auto-select first
        if items and self._on_select:
            self._on_select(items[0]["id"])


# ── ReportsPage ───────────────────────────────────────────────────────

class ReportsPage(tk.Frame):

    def __init__(self, parent, user=None,
                 on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user       = user
        self._report     = None     # current full report dict
        self._report_id  = None
        self._bar_chart  = None
        self._build()

    # ── layout ────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=0)   # left list panel
        self.columnconfigure(1, weight=1)   # main content
        self.rowconfigure(0, weight=1)

        # left sidebar — report list
        ReportListPanel(
            self,
            on_select=self._on_report_selected,
            bg=Palette.SURFACE_LOW,
            width=200,
        ).grid(row=0, column=0, sticky="nsew")

        tk.Frame(self, bg=Palette.OUTLINE,
                 width=1).grid(row=0, column=0, sticky="nse")

        # main scrollable content
        scroll_host = tk.Frame(self, bg=Palette.SURFACE)
        scroll_host.grid(row=0, column=1, sticky="nsew")

        canvas = tk.Canvas(scroll_host, bg=Palette.SURFACE,
                            highlightthickness=0)
        scroll = tk.Scrollbar(scroll_host, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=Palette.SURFACE)
        win = canvas.create_window((0, 0), window=self._inner,
                                    anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
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

        self._show_empty()

    def _show_empty(self):
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(self._inner,
                 text="Select a report from the list.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).place(
            relx=0.5, rely=0.4, anchor="center")

    # ── report selection ──────────────────────────────────────────────

    def _on_report_selected(self, report_id: int):
        if self._report_id == report_id:
            return
        self._report_id = report_id
        self._show_loading()
        threading.Thread(
            target=self._fetch_report,
            args=(report_id,),
            daemon=True
        ).start()

    def _fetch_report(self, report_id: int):
        try:
            data = api("get", f"/reports/{report_id}")
            self.after(0, lambda: self._render_report(data))
        except requests.HTTPError as exc:
            msg = f"Server error ({exc.response.status_code})"
            self.after(0, lambda: self._show_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Cannot reach server."))
        except Exception as exc:
            self.after(0, lambda: self._show_error(str(exc)))

    def _show_loading(self):
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(self._inner, text="Loading report…",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(pady=Palette.PAD_XL)

    def _show_error(self, msg: str):
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(self._inner, text=f"⚠ {msg}",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ERROR,
                 bg=Palette.SURFACE).pack(pady=Palette.PAD_XL)

    # ── render full report ────────────────────────────────────────────

    def _render_report(self, data: dict):
        self._report = data
        for w in self._inner.winfo_children():
            w.destroy()
        p = self._inner

        # ── breadcrumb + title ────────────────────────────────────────
        bc = tk.Frame(p, bg=Palette.SURFACE)
        bc.pack(fill="x", padx=Palette.PAD_XL,
                pady=(Palette.PAD_LG, 0))
        tk.Label(bc, text="Archives",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE, cursor="hand2").pack(side="left")
        tk.Label(bc, text="  /  ",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.OUTLINE_BRIGHT,
                 bg=Palette.SURFACE).pack(side="left")
        tk.Label(bc, text=data.get("case_number", ""),
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE).pack(side="left")

        title_row = tk.Frame(p, bg=Palette.SURFACE)
        title_row.pack(fill="x", padx=Palette.PAD_XL,
                       pady=(Palette.PAD_SM, 0))

        title_block = tk.Frame(title_row, bg=Palette.SURFACE)
        title_block.pack(side="left", fill="x", expand=True)
        tk.Label(title_block,
                 text=data.get("title", "Forensic Report"),
                 font=Palette.bold(Palette.DISPLAY),
                 fg=Palette.ON_SURFACE, bg=Palette.SURFACE,
                 wraplength=560, justify="left").pack(anchor="w")

        gen_at  = str(data.get("generated_at", ""))[:10]
        level   = data.get("clearance_level", "—")
        tk.Label(title_block,
                 text=f"Generated {gen_at}  •  "
                      f"Security Clearance Level {level} Required",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w", pady=(4, 0))

        # export buttons
        btn_row = tk.Frame(title_row, bg=Palette.SURFACE)
        btn_row.pack(side="right", anchor="s", pady=Palette.PAD_SM)
        for lbl in ["PDF", "Word", "CSV"]:
            GoldButton(btn_row, text=lbl, style="outline").pack(
                side="left", padx=(0, Palette.PAD_SM),
                ipady=4, ipadx=10)

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # ── metric card ───────────────────────────────────────────────
        metric_data = data.get("metric_card", {})
        MetricCard(p, data=metric_data,
                   bg=Palette.SURFACE_CONTAINER).pack(
            fill="x", padx=Palette.PAD_XL)

        tk.Frame(p, height=3,
                 bg=Palette.PRIMARY).pack(
            fill="x", padx=Palette.PAD_XL,
            pady=(0, Palette.PAD_LG))

        # ── two-col: report body | metadata sidebar ───────────────────
        body_row = tk.Frame(p, bg=Palette.SURFACE)
        body_row.pack(fill="x", padx=Palette.PAD_XL)
        body_row.columnconfigure(0, weight=3)
        body_row.columnconfigure(1, weight=1)

        left = tk.Frame(body_row, bg=Palette.SURFACE_CONTAINER)
        left.grid(row=0, column=0, sticky="nsew",
                  padx=(0, Palette.PAD_MD))

        # I. Executive Summary
        self._section(left, "I. EXECUTIVE SUMMARY",
                      data.get("executive_summary", "—"))

        # II. Threat Vector Distribution
        sec2 = tk.Frame(left, bg=Palette.SURFACE_CONTAINER)
        sec2.pack(fill="x", padx=Palette.PAD_LG,
                  pady=(0, Palette.PAD_LG))
        tk.Label(sec2,
                 text="II. THREAT VECTOR DISTRIBUTION",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        vectors = data.get("threat_vectors", [])
        self._bar_chart = BarChart(sec2,
                                    vectors=vectors,
                                    bg=Palette.SURFACE_CONTAINER)
        self._bar_chart.pack(fill="x")

        # III. Critical Artifacts
        artifacts = data.get("critical_artifacts", [])
        sec3 = tk.Frame(left, bg=Palette.SURFACE_CONTAINER)
        sec3.pack(fill="x", padx=Palette.PAD_LG,
                  pady=(0, Palette.PAD_LG))
        tk.Label(sec3, text="III. CRITICAL ARTIFACTS",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        col_hdr = tk.Frame(sec3, bg=Palette.SURFACE_CONTAINER)
        col_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        for txt, w in [("TIMESTAMP", 22), ("SOURCE", 16),
                        ("ACTION", 22), ("STATUS", 10)]:
            tk.Label(col_hdr, text=txt,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER,
                     width=w, anchor="w").pack(side="left")

        tk.Frame(sec3, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           pady=(0, Palette.PAD_SM))

        if artifacts:
            for item in artifacts:
                ArtifactRow(sec3, item,
                            bg=Palette.SURFACE_CONTAINER).pack(fill="x")
        else:
            tk.Label(sec3, text="No critical artifacts recorded.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER).pack(
                anchor="w", pady=Palette.PAD_MD)

        tk.Frame(left, height=Palette.PAD_LG,
                 bg=Palette.SURFACE_CONTAINER).pack()

        # right metadata panel
        MetadataPanel(
            body_row,
            report=data,
            on_save_notes=self._save_notes,
            on_sign=self._sign_report,
            bg=Palette.SURFACE_CONTAINER,
        ).grid(row=0, column=1, sticky="nsew")

        tk.Frame(p, height=Palette.PAD_XL, bg=Palette.SURFACE).pack()

    def _section(self, parent, title, body):
        frame = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
        frame.pack(fill="x", padx=Palette.PAD_LG,
                   pady=(Palette.PAD_LG, Palette.PAD_MD))
        tk.Label(frame, text=title,
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", pady=(0, Palette.PAD_SM))
        tk.Label(frame, text=body,
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER,
                 wraplength=520, justify="left").pack(anchor="w")

    # ── actions ───────────────────────────────────────────────────────

    def _save_notes(self, text: str):
        if not self._report_id:
            return
        log.debug("Saving notes for report %s", self._report_id)

        def do():
            try:
                api("patch",
                    f"/reports/{self._report_id}/notes",
                    json={"notes": text})
                log.info("Notes saved for report %s", self._report_id)
            except Exception as exc:
                log.error("Failed to save notes: %s", exc)

        threading.Thread(target=do, daemon=True).start()

    def _sign_report(self):
        if not self._report_id:
            return
        confirmed = messagebox.askyesno(
            "Sign Report",
            f"Sign report #{self._report_id}?\n"
            "This action cannot be undone."
        )
        if not confirmed:
            return

        def do():
            try:
                data = api("patch",
                           f"/reports/{self._report_id}/sign")
                self.after(0, lambda: self._render_report(data))
                log.info("Report %s signed", self._report_id)
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Server error ({exc.response.status_code})"
                self.after(0, lambda: messagebox.showerror(
                    "Sign Failed", msg))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror(
                    "Sign Failed", str(exc)))

        threading.Thread(target=do, daemon=True).start()