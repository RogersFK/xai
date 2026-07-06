# from colors import Palette
# import tkinter as tk
# import threading
# import requests
# from tkinter import messagebox
# from components import GoldButton
# from helper import api
# from logger import get_logger

# log = get_logger("REPORTS")

# class BarChart(tk.Canvas):
#     CHART_H = 200
#     BAR_W   = 40
#     GAP     = 60

#     def __init__(self, parent, vectors=None, bg=None, **kw):
#         bg = bg or Palette.SURFACE_CONTAINER
#         super().__init__(parent, bg=bg, highlightthickness=0,
#                          height=self.CHART_H + 40, **kw)
#         self._bg      = bg
#         self._vectors = vectors or []
#         self._anim    = 0.0
#         self.bind("<Configure>", lambda e: self._redraw())
#         self.after(50, self._animate)

#     def set_vectors(self, vectors: list):
#         self._vectors = vectors
#         self._anim    = 0.0
#         self.after(50, self._animate)

#     def _animate(self):
#         if self._anim < 1.0:
#             self._anim = min(self._anim + 0.05, 1.0)
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
#         if w < 10 or not self._vectors:
#             return

#         ch      = self.CHART_H
#         bw      = self.BAR_W
#         n       = len(self._vectors)
#         total_w = n * bw + (n-1) * self.GAP
#         x_off   = max(20, (w - total_w) // 2)
#         y_base  = ch + 10
#         prog    = self._ease(self._anim)

#         # grid lines
#         for i in range(1, 5):
#             y = y_base - int(ch * i / 4)
#             self.create_line(x_off-10, y, x_off+total_w+10, y,
#                              fill=Palette.OUTLINE, dash=(4, 4))
#             self.create_text(x_off-14, y,
#                              text=f"{i*25}%",
#                              font=Palette.font(Palette.MICRO),
#                              fill=Palette.ON_SURFACE_VAR,
#                              anchor="e")

#         for i, vec in enumerate(self._vectors):
#             label = vec.get("label", f"VEC_{i}")
#             val   = float(vec.get("percentage", 0)) / 100
#             x     = x_off + i * (bw + self.GAP)
#             bar_h = int(ch * val * prog)

#             c0, c1 = (0xf2, 0xca, 0x50), (0xd4, 0xaf, 0x37)
#             for row in range(bar_h):
#                 t   = row / max(bar_h-1, 1)
#                 col = "#{:02x}{:02x}{:02x}".format(
#                     int(c0[0]+(c1[0]-c0[0])*(1-t)),
#                     int(c0[1]+(c1[1]-c0[1])*(1-t)),
#                     int(c0[2]+(c1[2]-c0[2])*(1-t)),
#                 )
#                 self.create_line(x, y_base-row, x+bw, y_base-row,
#                                  fill=col, width=1)

#             if bar_h > 0:
#                 self.create_text(x+bw//2, y_base-bar_h-8,
#                                  text=f"{int(val*100)}%",
#                                  font=Palette.bold(Palette.MICRO),
#                                  fill=Palette.PRIMARY)

#             self.create_text(x+bw//2, y_base+16,
#                              text=label,
#                              font=Palette.font(Palette.MICRO),
#                              fill=Palette.ON_SURFACE_VAR)

#         self.create_line(x_off-10, y_base,
#                          x_off+total_w+10, y_base,
#                          fill=Palette.OUTLINE_BRIGHT, width=1)

# class MetricCard(tk.Frame):
#     def __init__(self, parent, data: dict = None, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
#         super().__init__(parent, bg=bg, **kw)
#         self._bg   = bg
#         self._data = data or {}
#         self._build()

#     def _build(self):
#         d   = self._data
#         bg  = self._bg

#         outer = tk.Frame(self, bg=bg)
#         outer.pack(fill="x")
#         outer.columnconfigure(0, weight=1)
#         outer.columnconfigure(1, weight=2)

#         left = tk.Frame(outer, bg=bg,
#                         padx=Palette.PAD_LG, pady=Palette.PAD_LG)
#         left.grid(row=0, column=0, sticky="nsew")

#         tk.Label(left, text="INTEGRITY SCORE",
#                  font=Palette.bold(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")

#         score     = d.get("integrity_score", 0.0)
#         score_str = f"{score:.1f}"

#         score_row = tk.Frame(left, bg=bg)
#         score_row.pack(anchor="w", pady=(Palette.PAD_SM, 0))
#         tk.Label(score_row, text=score_str,
#                  font=(Palette._FONT[0], 48, "bold"),
#                  fg=Palette.ON_SURFACE, bg=bg).pack(side="left")
#         tk.Label(score_row, text="%",
#                  font=Palette.bold(Palette.TITLE_LG),
#                  fg=Palette.ON_SURFACE_VAR, bg=bg).pack(
#             side="left", anchor="s", pady=(0, 8))
#         tk.Label(score_row, text="✔",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.PRIMARY, bg=bg).pack(
#             side="right", padx=Palette.PAD_LG)

#         bar_track = tk.Frame(left, bg=Palette.SURFACE_HIGH, height=6)
#         bar_track.pack(fill="x", pady=(Palette.PAD_SM, 0))
#         tk.Frame(bar_track, bg=Palette.PRIMARY, height=6).place(
#             relx=0, rely=0,
#             relwidth=min(score/100, 1.0),
#             relheight=1)

#         right = tk.Frame(outer, bg=bg)
#         right.grid(row=0, column=1, sticky="nsew")

#         stats_row = tk.Frame(right, bg=bg)
#         stats_row.pack(fill="x", padx=Palette.PAD_LG,
#                        pady=(Palette.PAD_LG, Palette.PAD_SM))

#         total      = d.get("total_artifacts", 0)
#         alerts     = d.get("alerts_critical", 0)
#         proc_time  = d.get("processing_time", 0.0)

#         for label, val, color in [
#             ("TOTAL ARTIFACTS", f"{total:,}",    Palette.ON_SURFACE),
#             ("ALERTS CRITICAL", str(alerts),      Palette.ERROR),
#             ("PROCESSING TIME", f"{proc_time:.1f}s", Palette.ON_SURFACE),
#         ]:
#             blk = tk.Frame(stats_row, bg=bg)
#             blk.pack(side="left", padx=(0, Palette.PAD_XL))
#             tk.Label(blk, text=label,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")
#             tk.Label(blk, text=val,
#                      font=(Palette._FONT[0], 26, "bold"),
#                      fg=color, bg=bg).pack(anchor="w")

#         info = tk.Frame(right, bg=Palette.SURFACE_HIGH,
#                         padx=Palette.PAD_MD, pady=Palette.PAD_SM)
#         info.pack(fill="x", padx=Palette.PAD_LG,
#                   pady=(0, Palette.PAD_LG))
#         tk.Label(info, text="ℹ",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_HIGH).pack(side="left",
#                                                 padx=(0, Palette.PAD_SM))

#         coc = d.get("chain_of_custody", "—")
#         tk.Label(info, text=coc,
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_HIGH,
#                  wraplength=380, justify="left").pack(side="left")

# class ArtifactRow(tk.Frame):
#     STATUS_COL = {
#         "CRITICAL": Palette.ERROR,
#         "WARNING":  Palette.WARNING,
#         "BENIGN":   Palette.ON_SURFACE_VAR,
#     }

#     def __init__(self, parent, item: dict, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
#         super().__init__(parent, bg=bg, **kw)
#         self._build(item, bg)

#     def _build(self, item: dict, bg: str):
#         row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
#         row.pack(fill="x", padx=Palette.PAD_LG)

#         status    = (item.get("status") or "").upper()
#         color     = self.STATUS_COL.get(status, Palette.ON_SURFACE_VAR)
#         timestamp = item.get("timestamp", "—")
#         source    = item.get("source", "—")
#         action    = item.get("action", "—")

#         for text, width, bold in [
#             (timestamp, 22, False),
#             (source,    16, True),
#             (action,    22, False),
#         ]:
#             tk.Label(row, text=text,
#                      font=Palette.bold(Palette.BODY) if bold
#                           else Palette.font(Palette.BODY),
#                      fg=Palette.ON_SURFACE if bold
#                         else Palette.ON_SURFACE_VAR,
#                      bg=bg, width=width, anchor="w").pack(side="left")

#         tk.Label(row, text=status,
#                  font=Palette.bold(Palette.LABEL),
#                  fg=color, bg=bg,
#                  anchor="w", width=10).pack(side="left",
#                                              padx=Palette.PAD_MD)

#         tk.Frame(self, height=1,
#                  bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_LG)

# class MetadataPanel(tk.Frame):
#     def __init__(self, parent, report: dict = None,
#                  on_save_notes=None, on_sign=None, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
#         super().__init__(parent, bg=bg, **kw)
#         self._bg           = bg
#         self._report       = report or {}
#         self._on_save_notes = on_save_notes
#         self._on_sign       = on_sign
#         self._build()

#     def _build(self):
#         r  = self._report
#         bg = self._bg

#         # metadata
#         meta = tk.Frame(self, bg=bg,
#                         padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         meta.pack(fill="x")

#         hdr = tk.Frame(meta, bg=bg)
#         hdr.pack(fill="x", pady=(0, Palette.PAD_MD))
#         tk.Label(hdr, text="ℹ",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY, bg=bg).pack(side="left",
#                                                   padx=(0, 6))
#         tk.Label(hdr, text="Metadata",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.ON_SURFACE, bg=bg).pack(side="left")

#         metric = r.get("metric_card", {})
#         signed_at = r.get("signed_at")
#         signed_str = str(signed_at)[:19] if signed_at else "Not signed"

#         for field, value in [
#             ("CASE NUMBER",       r.get("case_number", "—")),
#             ("STATUS",            r.get("status", "—").upper()),
#             ("CLEARANCE LEVEL",   f"Level {r.get('clearance_level', '—')}"),
#             ("HASH SHA-256",      metric.get("hash_sha256", "—")),
#             ("GENERATED",         str(r.get("generated_at", ""))[:10]),
#             ("SIGNED AT",         signed_str),
#         ]:
#             tk.Label(meta, text=field,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=bg, anchor="w").pack(
#                 fill="x", pady=(Palette.PAD_SM, 2))
#             color = (Palette.SUCCESS if value in ("SIGNED", "DRAFT")
#                      else Palette.ON_SURFACE)
#             tk.Label(meta, text=value,
#                      font=Palette.font(Palette.LABEL),
#                      fg=color, bg=bg,
#                      anchor="w", justify="left",
#                      wraplength=160).pack(fill="x")

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

#         # investigator notes
#         notes = tk.Frame(self, bg=bg,
#                          padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         notes.pack(fill="x")

#         tk.Label(notes, text="Investigator Notes",
#                  font=Palette.bold(Palette.TITLE_MD),
#                  fg=Palette.ON_SURFACE, bg=bg).pack(
#             anchor="w", pady=(0, Palette.PAD_SM))

#         self._notes_txt = tk.Text(
#             notes, height=6,
#             font=Palette.font(Palette.LABEL),
#             fg=Palette.ON_SURFACE_VAR,
#             bg=Palette.SURFACE_HIGH,
#             insertbackground=Palette.PRIMARY,
#             relief="flat", bd=0,
#             padx=8, pady=8, wrap="word",
#             highlightthickness=1,
#             highlightbackground=Palette.OUTLINE,
#             highlightcolor=Palette.PRIMARY)

#         placeholder = "Enter findings or observations..."
#         self._notes_txt.insert("1.0", placeholder)
#         self._notes_txt.bind("<FocusIn>", lambda e: (
#             self._notes_txt.delete("1.0", "end")
#             if self._notes_txt.get("1.0", "end-1c") == placeholder
#             else None,
#             self._notes_txt.config(fg=Palette.ON_SURFACE)
#         ))
#         self._notes_txt.pack(fill="x")

#         tk.Frame(notes, height=Palette.PAD_SM, bg=bg).pack()

#         self._notes_status = tk.Label(
#             notes, text="",
#             font=Palette.font(Palette.MICRO),
#             fg=Palette.SUCCESS, bg=bg)
#         self._notes_status.pack(anchor="w")

#         GoldButton(notes, text="APPEND TO LOG",
#                    command=self._save_notes).pack(
#             fill="x", ipady=6)

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

#         # sign button
#         sign_frame = tk.Frame(self, bg=bg,
#                               padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         sign_frame.pack(fill="x")

#         signed = r.get("status", "") == "signed"
#         if signed:
#             tk.Label(sign_frame, text="✔  Report Signed",
#                      font=Palette.bold(Palette.LABEL),
#                      fg=Palette.SUCCESS, bg=bg).pack(anchor="w")
#         else:
#             GoldButton(sign_frame, text="Sign Report",
#                        command=self._sign).pack(fill="x", ipady=6)

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

#         # crypto proof
#         proof = tk.Frame(self, bg=bg,
#                          padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         proof.pack(fill="x")

#         proof_hdr = tk.Frame(proof, bg=bg)
#         proof_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
#         tk.Label(proof_hdr, text="✔",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.SUCCESS, bg=bg).pack(side="left",
#                                                   padx=(0, 6))
#         tk.Label(proof_hdr, text="Cryptographic Proof",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.ON_SURFACE, bg=bg).pack(side="left")

#         tk.Label(proof,
#                  text=("This report is digitally signed and timestamped "
#                        "on the secure XAI ledger. Any modification will "
#                        "invalidate the forensic integrity."),
#                  font=Palette.font(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR, bg=bg,
#                  wraplength=160, justify="left").pack(anchor="w")

#     def _save_notes(self):
#         text = self._notes_txt.get("1.0", "end-1c").strip()
#         if not text or text == "Enter findings or observations...":
#             return
#         if self._on_save_notes:
#             self._on_save_notes(text)
#             self._notes_status.config(text="✓ Saved")
#             self.after(2000, lambda: self._notes_status.config(text=""))

#     def _sign(self):
#         if self._on_sign:
#             self._on_sign()

# class ReportListPanel(tk.Frame):
#     def __init__(self, parent, on_select=None, **kw):
#         bg = kw.pop("bg", Palette.SURFACE_LOW)
#         super().__init__(parent, bg=bg, **kw)
#         self._bg        = bg
#         self._on_select = on_select
#         self._sel_row   = None
#         self._build()
#         self._load()

#     def _build(self):
#         hdr = tk.Frame(self, bg=self._bg,
#                        padx=Palette.PAD_MD, pady=Palette.PAD_MD)
#         hdr.pack(fill="x")
#         tk.Label(hdr, text="REPORTS",
#                  font=Palette.bold(Palette.MICRO),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=self._bg).pack(side="left")

#         refresh = tk.Label(hdr, text="↻",
#                            font=Palette.bold(Palette.LABEL),
#                            fg=Palette.ON_SURFACE_VAR,
#                            bg=self._bg, cursor="hand2")
#         refresh.pack(side="right")
#         refresh.bind("<Button-1>", lambda e: self._load())
#         refresh.bind("<Enter>",
#                      lambda e: refresh.config(fg=Palette.PRIMARY))
#         refresh.bind("<Leave>",
#                      lambda e: refresh.config(
#                          fg=Palette.ON_SURFACE_VAR))

#         tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

#         canvas = tk.Canvas(self, bg=self._bg, highlightthickness=0)
#         sb     = tk.Scrollbar(self, orient="vertical",
#                                command=canvas.yview)
#         canvas.configure(yscrollcommand=sb.set)
#         sb.pack(side="right", fill="y")
#         canvas.pack(side="left", fill="both", expand=True)

#         self._list = tk.Frame(canvas, bg=self._bg)
#         win = canvas.create_window((0, 0), window=self._list,
#                                     anchor="nw")
#         canvas.bind("<Configure>",
#                     lambda e: canvas.itemconfig(win, width=e.width))
#         self._list.bind("<Configure>",
#                         lambda e: canvas.configure(
#                             scrollregion=canvas.bbox("all")))

#         self._status = tk.Label(
#             self._list, text="Loading…",
#             font=Palette.font(Palette.MICRO),
#             fg=Palette.ON_SURFACE_VAR, bg=self._bg)
#         self._status.pack(pady=Palette.PAD_LG)

#     def _load(self):
#         threading.Thread(target=self._fetch, daemon=True).start()

#     def _fetch(self):
#         try:
#             data = api("get", "/reports/")
#             self.after(0, lambda: self._render(data))
#         except Exception as exc:
#             self.after(0, lambda: self._status.config(
#                 text=f"Failed: {exc}", fg=Palette.ERROR))

#     def _render(self, items: list):
#         for w in self._list.winfo_children():
#             w.destroy()

#         if not items:
#             tk.Label(self._list,
#                      text="No reports yet.\nGenerate one from\nthe Analysis page.",
#                      font=Palette.font(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=self._bg, justify="center").pack(
#                 pady=Palette.PAD_LG)
#             return

#         STATUS_COLOR = {"signed": Palette.SUCCESS,
#                         "draft":  Palette.WARNING}

#         for item in items:
#             rid     = item["id"]
#             title   = item.get("title", f"Report #{rid}")
#             case    = item.get("case_number", "")
#             status  = item.get("status", "draft").lower()
#             date    = str(item.get("generated_at", ""))[:10]
#             s_color = STATUS_COLOR.get(status, Palette.ON_SURFACE_VAR)

#             row = tk.Frame(self._list, bg=self._bg,
#                             cursor="hand2",
#                             padx=Palette.PAD_MD, pady=Palette.PAD_SM)
#             row.pack(fill="x")

#             # status dot — pack right first
#             tk.Label(row, text="●",
#                      font=Palette.bold(Palette.MICRO),
#                      fg=s_color, bg=self._bg).pack(side="right")

#             # content
#             tk.Label(row, text=title,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE,
#                      bg=self._bg, anchor="w",
#                      wraplength=160).pack(anchor="w")
#             tk.Label(row,
#                      text=f"{case}  •  {date}",
#                      font=Palette.font(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=self._bg, anchor="w").pack(anchor="w")

#             tk.Frame(self._list, height=1,
#                      bg=Palette.OUTLINE).pack(fill="x")

#             def _enter(e, r=row):
#                 r.config(bg=Palette.SURFACE_HIGH)
#                 for w in r.winfo_children():
#                     w.config(bg=Palette.SURFACE_HIGH)

#             def _leave(e, r=row, rid=rid):
#                 bg = (Palette.SURFACE_CONTAINER
#                       if self._sel_row == rid
#                       else self._bg)
#                 r.config(bg=bg)
#                 for w in r.winfo_children():
#                     w.config(bg=bg)

#             def _click(e, rid=rid, r=row):
#                 self._sel_row = rid
#                 if self._on_select:
#                     self._on_select(rid)

#             for w in [row] + list(row.winfo_children()):
#                 w.bind("<Enter>",    _enter)
#                 w.bind("<Leave>",    _leave)
#                 w.bind("<Button-1>", _click)

#         # auto-select first
#         if items and self._on_select:
#             self._on_select(items[0]["id"])

# class ReportsPage(tk.Frame):

#     def __init__(self, parent, user=None,
#                  on_profile_updated=None, **kw):
#         super().__init__(parent, bg=Palette.SURFACE, **kw)
#         self._user       = user
#         self._report     = None     # current full report dict
#         self._report_id  = None
#         self._bar_chart  = None
#         self._build()
        

#     # add this method to ReportsPage:
#     def _download_pdf(self, encrypted: bool = False):
#         if not self._report_id:
#             return
#         import threading
#         threading.Thread(
#             target=self._do_download, args=(encrypted,), daemon=True
#         ).start()
        
        
#     def _show_key_dialog(self, hex_key: str, title: str, subtitle: str):
#         """Custom key dialog with one-click copy button."""
#         dialog = tk.Toplevel(self)
#         dialog.title(title)
#         dialog.configure(bg=Palette.SURFACE)
#         dialog.resizable(False, False)
#         dialog.grab_set()

#         # centre
#         dialog.geometry("520x340")
#         dialog.update_idletasks()
#         x = self.winfo_rootx() + (self.winfo_width()  - 520) // 2
#         y = self.winfo_rooty() + (self.winfo_height() - 340) // 2
#         dialog.geometry(f"+{x}+{y}")

#         hdr = tk.Frame(dialog, bg=Palette.PRIMARY,
#                     padx=Palette.PAD_LG, pady=Palette.PAD_MD)
#         hdr.pack(fill="x")

#         tk.Label(
#             hdr, text="🔐  " + title,
#             font=Palette.bold(Palette.TITLE_MD),
#             fg=Palette.ON_PRIMARY, bg=Palette.PRIMARY,
#         ).pack(anchor="w")

#         tk.Label(
#             hdr, text=subtitle,
#             font=Palette.font(Palette.MICRO),
#             fg=Palette.ON_PRIMARY, bg=Palette.PRIMARY,
#         ).pack(anchor="w", pady=(2, 0))

#         warn = tk.Frame(dialog, bg=Palette.WARNING,
#                         padx=Palette.PAD_MD, pady=Palette.PAD_SM)
#         warn.pack(fill="x")
#         tk.Label(
#             warn,
#             text="⚠  This key will NOT be shown again. Save it immediately.",
#             font=Palette.bold(Palette.MICRO),
#             fg=Palette.SURFACE, bg=Palette.WARNING,
#         ).pack(anchor="w")

#         key_frame = tk.Frame(dialog, bg=Palette.SURFACE,
#                             padx=Palette.PAD_LG, pady=Palette.PAD_MD)
#         key_frame.pack(fill="x")

#         tk.Label(
#             key_frame, text="DECRYPTION KEY",
#             font=Palette.bold(Palette.MICRO),
#             fg=Palette.ON_SURFACE_VAR, bg=Palette.SURFACE,
#         ).pack(anchor="w", pady=(0, Palette.PAD_SM))

#         # key text box — selectable, read-only
#         key_box = tk.Text(
#             key_frame,
#             height=2,
#             font=("Courier New", 10, "bold"),
#             fg=Palette.PRIMARY,
#             bg=Palette.SURFACE_CONTAINER,
#             relief="flat",
#             bd=0,
#             padx=10,
#             pady=8,
#             wrap="word",
#             highlightthickness=1,
#             highlightbackground=Palette.OUTLINE,
#             highlightcolor=Palette.PRIMARY,
#         )
#         key_box.insert("1.0", hex_key)
#         key_box.config(state="disabled")   # read-only but selectable
#         key_box.pack(fill="x")

#         # ── copy button + status ──────────────────────────────────
#         copy_row = tk.Frame(dialog, bg=Palette.SURFACE,
#                             padx=Palette.PAD_LG, pady=Palette.PAD_SM)
#         copy_row.pack(fill="x")

#         copy_status = tk.Label(
#             copy_row, text="",
#             font=Palette.bold(Palette.MICRO),
#             fg=Palette.SUCCESS, bg=Palette.SURFACE,
#         )
#         copy_status.pack(side="right")

#         def _copy():
#             dialog.clipboard_clear()
#             dialog.clipboard_append(hex_key)
#             dialog.update()
#             copy_btn.config(text="✔  Copied!", bg=Palette.SUCCESS)
#             copy_status.config(text="Key copied to clipboard")
#             dialog.after(2500, lambda: (
#                 copy_btn.config(text="⎘  Copy Key", bg=Palette.PRIMARY),
#                 copy_status.config(text=""),
#             ))

#         copy_btn = tk.Button(
#             copy_row,
#             text="⎘  Copy Key",
#             font=Palette.bold(Palette.LABEL_SM),
#             fg=Palette.ON_SURFACE,        # dark text #0f172a
#             bg=Palette.SURFACE_HIGHEST,
#             activebackground=Palette.PRIMARY_DIM,
#             activeforeground=Palette.PRIMARY,
#             relief="flat",
#             cursor="hand2",
#             padx=16,
#             pady=6,
#             command=_copy,
#         )
#         copy_btn.pack(side="left")

#         tk.Frame(dialog, bg=Palette.OUTLINE, height=1).pack(fill="x")

#         btn_row = tk.Frame(dialog, bg=Palette.SURFACE,
#                         padx=Palette.PAD_LG, pady=Palette.PAD_MD)
#         btn_row.pack(fill="x")

#         tk.Label(
#             btn_row,
#             text="Store this key in a password manager or secure vault.",
#             font=Palette.font(Palette.MICRO),
#             fg=Palette.ON_SURFACE_VAR, bg=Palette.SURFACE,
#         ).pack(side="left")

#         tk.Button(
#             btn_row,
#             text="Close",
#             font=Palette.font(Palette.LABEL_SM),
#             fg=Palette.ON_SURFACE,
#             bg=Palette.SURFACE_HIGH,
#             activebackground=Palette.SURFACE_HIGHEST,
#             relief="flat",
#             cursor="hand2",
#             padx=12,
#             pady=4,
#             command=dialog.destroy,
#         ).pack(side="right")  
        
          

#     def _do_download(self, encrypted: bool):
#         import requests as req
#         from tkinter import filedialog
#         try:
#             from helper import BASE_URL, session
#             url  = f"{BASE_URL}/reports/{self._report_id}/download"
#             params = {"encrypt": str(encrypted).lower()}
#             resp = session.get(url, params=params, timeout=(10, 60))
#             resp.raise_for_status()

#             ext  = ".xpdf" if encrypted else ".pdf"
#             path = filedialog.asksaveasfilename(
#                 defaultextension=ext,
#                 filetypes=[("PDF file", f"*{ext}")],
#                 initialfile=f"report_{self._report_id}{ext}",
#             )
#             if not path:
#                 return

#             with open(path, "wb") as f:
#                 f.write(resp.content)

#             # if encrypted, show the key — investigator MUST save it
#             if encrypted:
#                 key = resp.headers.get("X-Decrypt-Key", "")
#                 self.after(0, lambda k=key: self._show_key_dialog(
#                     k,
#                     title="PDF Decryption Key",
#                     subtitle="AES-256-GCM encrypted report download",
#                 ))
#             # if encrypted:
#             #     key = resp.headers.get("X-Decrypt-Key", "")
#             #     self.after(0, lambda: messagebox.showinfo(
#             #         "Decryption Key — SAVE THIS",
#             #         f"Your report is encrypted with AES-256-GCM.\n\n"
#             #         f"DECRYPTION KEY:\n{key}\n\n"
#             #         f"Store this key securely. Without it the report\n"
#             #         f"cannot be decrypted. It will NOT be shown again."
#             #     ))
#             else:
#                 self.after(0, lambda: messagebox.showinfo(
#                     "Downloaded", f"Report saved to:\n{path}"))

#         except Exception as exc:
#             msg = str(exc)
#             self.after(0, lambda: messagebox.showerror("Download Failed", msg))     


#     def _build(self):
#         self.columnconfigure(0, weight=0)   # left list panel
#         self.columnconfigure(1, weight=1)   # main content
#         self.rowconfigure(0, weight=1)

#         # left sidebar — report list
#         ReportListPanel(
#             self,
#             on_select=self._on_report_selected,
#             bg=Palette.SURFACE_LOW,
#             width=200,
#         ).grid(row=0, column=0, sticky="nsew")

#         tk.Frame(self, bg=Palette.OUTLINE,
#                  width=1).grid(row=0, column=0, sticky="nse")

#         # main scrollable content
#         scroll_host = tk.Frame(self, bg=Palette.SURFACE)
#         scroll_host.grid(row=0, column=1, sticky="nsew")

#         canvas = tk.Canvas(scroll_host, bg=Palette.SURFACE,
#                             highlightthickness=0)
#         scroll = tk.Scrollbar(scroll_host, orient="vertical",
#                                command=canvas.yview)
#         canvas.configure(yscrollcommand=scroll.set)
#         scroll.pack(side="right", fill="y")
#         canvas.pack(side="left", fill="both", expand=True)

#         self._inner = tk.Frame(canvas, bg=Palette.SURFACE)
#         win = canvas.create_window((0, 0), window=self._inner,
#                                     anchor="nw")
#         canvas.bind("<Configure>",
#                     lambda e: canvas.itemconfig(win, width=e.width))
#         self._inner.bind("<Configure>",
#                          lambda e: canvas.configure(
#                              scrollregion=canvas.bbox("all")))
#         canvas.bind("<Enter>",
#                     lambda e: canvas.bind_all(
#                         "<MouseWheel>",
#                         lambda ev: canvas.yview_scroll(
#                             int(-1*(ev.delta/120)), "units")))
#         canvas.bind("<Leave>",
#                     lambda e: canvas.unbind_all("<MouseWheel>"))

#         self._show_empty()

#     def _show_empty(self):
#         for w in self._inner.winfo_children():
#             w.destroy()
#         tk.Label(self._inner,
#                  text="Select a report from the list.",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE).place(
#             relx=0.5, rely=0.4, anchor="center")


#     def _on_report_selected(self, report_id: int):
#         if self._report_id == report_id:
#             return
#         self._report_id = report_id
#         self._show_loading()
#         threading.Thread(
#             target=self._fetch_report,
#             args=(report_id,),
#             daemon=True
#         ).start()

#     def _fetch_report(self, report_id: int):
#         try:
#             data = api("get", f"/reports/{report_id}")
#             self.after(0, lambda: self._render_report(data))
#         except requests.HTTPError as exc:
#             msg = f"Server error ({exc.response.status_code})"
#             self.after(0, lambda: self._show_error(msg))
#         except requests.ConnectionError:
#             self.after(0, lambda: self._show_error("Cannot reach server."))
#         except Exception as exc:
#             self.after(0, lambda: self._show_error(str(exc)))

#     def _show_loading(self):
#         for w in self._inner.winfo_children():
#             w.destroy()
#         tk.Label(self._inner, text="Loading report…",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE).pack(pady=Palette.PAD_XL)

#     def _show_error(self, msg: str):
#         for w in self._inner.winfo_children():
#             w.destroy()
#         tk.Label(self._inner, text=f"⚠ {msg}",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ERROR,
#                  bg=Palette.SURFACE).pack(pady=Palette.PAD_XL)


#     def _render_report(self, data: dict):
#         self._report = data
#         for w in self._inner.winfo_children():
#             w.destroy()
#         p = self._inner

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
#         tk.Label(bc, text=data.get("case_number", ""),
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE).pack(side="left")

#         title_row = tk.Frame(p, bg=Palette.SURFACE)
#         title_row.pack(fill="x", padx=Palette.PAD_XL,
#                        pady=(Palette.PAD_SM, 0))

#         title_block = tk.Frame(title_row, bg=Palette.SURFACE)
#         title_block.pack(side="left", fill="x", expand=True)
#         tk.Label(title_block,
#                  text=data.get("title", "Forensic Report"),
#                  font=Palette.bold(Palette.DISPLAY),
#                  fg=Palette.ON_SURFACE, bg=Palette.SURFACE,
#                  wraplength=560, justify="left").pack(anchor="w")

#         gen_at  = str(data.get("generated_at", ""))[:10]
#         level   = data.get("clearance_level", "—")
#         tk.Label(title_block,
#                  text=f"Generated {gen_at}  •  "
#                       f"Security Clearance Level {level} Required",
#                  font=Palette.font(Palette.LABEL),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE).pack(anchor="w", pady=(4, 0))

#         # export buttons
#         btn_row = tk.Frame(title_row, bg=Palette.SURFACE)
#         btn_row.pack(side="right", anchor="s", pady=Palette.PAD_SM)
#         # for lbl in ["PDF"]:
#         #     GoldButton(btn_row, text=lbl, style="outline", ).pack(
#         #         side="left", padx=(0, Palette.PAD_SM),
#         #         ipady=4, ipadx=10)
        
#         # for lbl, encrypted in [("PDF", False), ("PDF (Encrypted)", True)]:
#         for lbl, encrypted in [ ("PDF (Encrypted)", True)]:
#             GoldButton(
#                 btn_row, text=lbl, style="outline",
#                 command=lambda e=encrypted: self._download_pdf(e)
#             ).pack(side="left", padx=(0, Palette.PAD_SM), ipady=4, ipadx=10)

#         tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

#         metric_data = data.get("metric_card", {})
#         MetricCard(p, data=metric_data,
#                    bg=Palette.SURFACE_CONTAINER).pack(
#             fill="x", padx=Palette.PAD_XL)

#         tk.Frame(p, height=3,
#                  bg=Palette.PRIMARY).pack(
#             fill="x", padx=Palette.PAD_XL,
#             pady=(0, Palette.PAD_LG))

#         body_row = tk.Frame(p, bg=Palette.SURFACE)
#         body_row.pack(fill="x", padx=Palette.PAD_XL)
#         body_row.columnconfigure(0, weight=3)
#         body_row.columnconfigure(1, weight=1)

#         left = tk.Frame(body_row, bg=Palette.SURFACE_CONTAINER)
#         left.grid(row=0, column=0, sticky="nsew",
#                   padx=(0, Palette.PAD_MD))

#         self._section(left, "I. EXECUTIVE SUMMARY",
#                       data.get("executive_summary", "—"))

#         # II. Threat Vector Distribution
#         sec2 = tk.Frame(left, bg=Palette.SURFACE_CONTAINER)
#         sec2.pack(fill="x", padx=Palette.PAD_LG,
#                   pady=(0, Palette.PAD_LG))
#         tk.Label(sec2,
#                  text="II. THREAT VECTOR DISTRIBUTION",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_CONTAINER).pack(
#             anchor="w", pady=(0, Palette.PAD_SM))

#         vectors = data.get("threat_vectors", [])
#         self._bar_chart = BarChart(sec2,
#                                     vectors=vectors,
#                                     bg=Palette.SURFACE_CONTAINER)
#         self._bar_chart.pack(fill="x")

#         artifacts = data.get("critical_artifacts", [])
#         sec3 = tk.Frame(left, bg=Palette.SURFACE_CONTAINER)
#         sec3.pack(fill="x", padx=Palette.PAD_LG,
#                   pady=(0, Palette.PAD_LG))
#         tk.Label(sec3, text="III. CRITICAL ARTIFACTS",
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_CONTAINER).pack(
#             anchor="w", pady=(0, Palette.PAD_SM))

#         col_hdr = tk.Frame(sec3, bg=Palette.SURFACE_CONTAINER)
#         col_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
#         for txt, w in [("TIMESTAMP", 22), ("SOURCE", 16),
#                         ("ACTION", 22), ("STATUS", 10)]:
#             tk.Label(col_hdr, text=txt,
#                      font=Palette.bold(Palette.MICRO),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=Palette.SURFACE_CONTAINER,
#                      width=w, anchor="w").pack(side="left")

#         tk.Frame(sec3, height=1,
#                  bg=Palette.OUTLINE).pack(fill="x",
#                                            pady=(0, Palette.PAD_SM))

#         if artifacts:
#             for item in artifacts:
#                 ArtifactRow(sec3, item,
#                             bg=Palette.SURFACE_CONTAINER).pack(fill="x")
#         else:
#             tk.Label(sec3, text="No critical artifacts recorded.",
#                      font=Palette.font(Palette.LABEL),
#                      fg=Palette.ON_SURFACE_VAR,
#                      bg=Palette.SURFACE_CONTAINER).pack(
#                 anchor="w", pady=Palette.PAD_MD)

#         tk.Frame(left, height=Palette.PAD_LG,
#                  bg=Palette.SURFACE_CONTAINER).pack()

#         MetadataPanel(
#             body_row,
#             report=data,
#             on_save_notes=self._save_notes,
#             on_sign=self._sign_report,
#             bg=Palette.SURFACE_CONTAINER,
#         ).grid(row=0, column=1, sticky="nsew")

#         tk.Frame(p, height=Palette.PAD_XL, bg=Palette.SURFACE).pack()

#     def _section(self, parent, title, body):
#         frame = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
#         frame.pack(fill="x", padx=Palette.PAD_LG,
#                    pady=(Palette.PAD_LG, Palette.PAD_MD))
#         tk.Label(frame, text=title,
#                  font=Palette.bold(Palette.LABEL),
#                  fg=Palette.PRIMARY,
#                  bg=Palette.SURFACE_CONTAINER).pack(
#             anchor="w", pady=(0, Palette.PAD_SM))
#         tk.Label(frame, text=body,
#                  font=Palette.font(Palette.BODY),
#                  fg=Palette.ON_SURFACE_VAR,
#                  bg=Palette.SURFACE_CONTAINER,
#                  wraplength=520, justify="left").pack(anchor="w")


#     def _save_notes(self, text: str):
#         if not self._report_id:
#             return
#         log.debug("Saving notes for report %s", self._report_id)

#         def do():
#             try:
#                 api("patch",
#                     f"/reports/{self._report_id}/notes",
#                     json={"notes": text})
#                 log.info("Notes saved for report %s", self._report_id)
#             except Exception as exc:
#                 log.error("Failed to save notes: %s", exc)

#         threading.Thread(target=do, daemon=True).start()

#     def _sign_report(self):
#         if not self._report_id:
#             return
#         confirmed = messagebox.askyesno(
#             "Sign Report",
#             f"Sign report #{self._report_id}?\n"
#             "This action cannot be undone."
#         )
#         if not confirmed:
#             return

#         def do():
#             try:
#                 data = api("patch",
#                            f"/reports/{self._report_id}/sign")
#                 self.after(0, lambda: self._render_report(data))
#                 log.info("Report %s signed", self._report_id)
#             except requests.HTTPError as exc:
#                 try:
#                     msg = exc.response.json().get("detail", "Failed.")
#                 except Exception:
#                     msg = f"Server error ({exc.response.status_code})"
#                 self.after(0, lambda: messagebox.showerror(
#                     "Sign Failed", msg))
#             except Exception as exc:
#                 self.after(0, lambda: messagebox.showerror(
#                     "Sign Failed", str(exc)))

#         threading.Thread(target=do, daemon=True).start()

from colors import Palette
import tkinter as tk
import threading
import requests
from tkinter import messagebox
from components import GoldButton
from helper import api
from logger import get_logger

log = get_logger("REPORTS")


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

    def set_vectors(self, vectors):
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
        return t * t * (3 - 2 * t)

    def _redraw(self):
        self.delete("all")
        w = self.winfo_width()
        if w < 10 or not self._vectors:
            return
        ch      = self.CHART_H
        bw      = self.BAR_W
        n       = len(self._vectors)
        total_w = n * bw + (n - 1) * self.GAP
        x_off   = max(20, (w - total_w) // 2)
        y_base  = ch + 10
        prog    = self._ease(self._anim)

        for i in range(1, 5):
            y = y_base - int(ch * i / 4)
            self.create_line(x_off - 10, y, x_off + total_w + 10, y,
                             fill=Palette.OUTLINE, dash=(4, 4))
            self.create_text(x_off - 14, y, text=f"{i * 25}%",
                             font=Palette.font(Palette.MICRO),
                             fill=Palette.ON_SURFACE_VAR, anchor="e")

        for i, vec in enumerate(self._vectors):
            label = vec.get("label", f"VEC_{i}")
            val   = float(vec.get("percentage", 0)) / 100
            x     = x_off + i * (bw + self.GAP)
            bar_h = int(ch * val * prog)
            c0, c1 = (0xf2, 0xca, 0x50), (0xd4, 0xaf, 0x37)
            for row in range(bar_h):
                t   = row / max(bar_h - 1, 1)
                col = "#{:02x}{:02x}{:02x}".format(
                    int(c0[0] + (c1[0] - c0[0]) * (1 - t)),
                    int(c0[1] + (c1[1] - c0[1]) * (1 - t)),
                    int(c0[2] + (c1[2] - c0[2]) * (1 - t)),
                )
                self.create_line(x, y_base - row, x + bw, y_base - row,
                                 fill=col, width=1)
            if bar_h > 0:
                self.create_text(x + bw // 2, y_base - bar_h - 8,
                                 text=f"{int(val * 100)}%",
                                 font=Palette.bold(Palette.MICRO),
                                 fill=Palette.PRIMARY)
            self.create_text(x + bw // 2, y_base + 16, text=label,
                             font=Palette.font(Palette.MICRO),
                             fill=Palette.ON_SURFACE_VAR)
        self.create_line(x_off - 10, y_base, x_off + total_w + 10, y_base,
                         fill=Palette.OUTLINE_BRIGHT, width=1)


class MetricCard(tk.Frame):
    def __init__(self, parent, data=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg   = bg
        self._data = data or {}
        self._build()

    def _build(self):
        d  = self._data
        bg = self._bg

        outer = tk.Frame(self, bg=bg)
        outer.pack(fill="x")
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)

        left = tk.Frame(outer, bg=bg, padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        left.grid(row=0, column=0, sticky="nsew")

        tk.Label(left, text="INTEGRITY SCORE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")

        score     = d.get("integrity_score", 0.0)
        score_row = tk.Frame(left, bg=bg)
        score_row.pack(anchor="w", pady=(Palette.PAD_SM, 0))
        tk.Label(score_row, text=f"{score:.1f}",
                 font=(Palette._FONT[0], 48, "bold"),
                 fg=Palette.ON_SURFACE, bg=bg).pack(side="left")
        tk.Label(score_row, text="%",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE_VAR, bg=bg).pack(
            side="left", anchor="s", pady=(0, 8))
        tk.Label(score_row, text="✔",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY, bg=bg).pack(side="right",
                                                  padx=Palette.PAD_LG)

        bar_track = tk.Frame(left, bg=Palette.SURFACE_HIGH, height=6)
        bar_track.pack(fill="x", pady=(Palette.PAD_SM, 0))
        tk.Frame(bar_track, bg=Palette.PRIMARY, height=6).place(
            relx=0, rely=0, relwidth=min(score / 100, 1.0), relheight=1)

        right = tk.Frame(outer, bg=bg)
        right.grid(row=0, column=1, sticky="nsew")

        stats_row = tk.Frame(right, bg=bg)
        stats_row.pack(fill="x", padx=Palette.PAD_LG,
                       pady=(Palette.PAD_LG, Palette.PAD_SM))

        for label, val, color in [
            ("TOTAL ARTIFACTS",  f"{d.get('total_artifacts', 0):,}", Palette.ON_SURFACE),
            ("ALERTS CRITICAL",  str(d.get("alerts_critical", 0)),   Palette.ERROR),
            ("PROCESSING TIME",  f"{d.get('processing_time', 0):.1f}s", Palette.ON_SURFACE),
        ]:
            blk = tk.Frame(stats_row, bg=bg)
            blk.pack(side="left", padx=(0, Palette.PAD_XL))
            tk.Label(blk, text=label, font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")
            tk.Label(blk, text=val,
                     font=(Palette._FONT[0], 26, "bold"),
                     fg=color, bg=bg).pack(anchor="w")

        info = tk.Frame(right, bg=Palette.SURFACE_HIGH,
                        padx=Palette.PAD_MD, pady=Palette.PAD_SM)
        info.pack(fill="x", padx=Palette.PAD_LG, pady=(0, Palette.PAD_LG))
        tk.Label(info, text="ℹ", font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY, bg=Palette.SURFACE_HIGH).pack(
            side="left", padx=(0, Palette.PAD_SM))
        tk.Label(info, text=d.get("chain_of_custody", "—"),
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR, bg=Palette.SURFACE_HIGH,
                 wraplength=380, justify="left").pack(side="left")


class ArtifactRow(tk.Frame):
    STATUS_COL = {
        "CRITICAL": Palette.ERROR,
        "HIGH":     Palette.ERROR,
        "MEDIUM":   Palette.WARNING,
        "LOW":      Palette.SUCCESS,
        "NORMAL":   Palette.SUCCESS,
        "BENIGN":   Palette.ON_SURFACE_VAR,
    }

    def __init__(self, parent, item, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(item, bg)

    def _build(self, item, bg):
        row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_LG)

        status = (item.get("status") or "").upper()
        color  = self.STATUS_COL.get(status, Palette.ON_SURFACE_VAR)

        for text, width, bold in [
            (item.get("timestamp", "—"), 22, False),
            (item.get("source",    "—"), 16, True),
            (item.get("action",    "—"), 22, False),
        ]:
            tk.Label(row, text=text,
                     font=Palette.bold(Palette.BODY) if bold
                          else Palette.font(Palette.BODY),
                     fg=Palette.ON_SURFACE if bold else Palette.ON_SURFACE_VAR,
                     bg=bg, width=width, anchor="w").pack(side="left")

        tk.Label(row, text=status, font=Palette.bold(Palette.LABEL),
                 fg=color, bg=bg, anchor="w", width=10).pack(
            side="left", padx=Palette.PAD_MD)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(
            fill="x", padx=Palette.PAD_LG)


class EventDetailRow(tk.Frame):
    """Renders one event with verdict, SHAP features and counterfactuals."""

    STATUS_COL = {
        "CRITICAL": Palette.ERROR,
        "HIGH":     Palette.ERROR,
        "MEDIUM":   Palette.WARNING,
        "LOW":      Palette.SUCCESS,
        "NORMAL":   Palette.SUCCESS,
        "BENIGN":   Palette.SUCCESS,
    }
    URGENCY_COL = {
        "IMMEDIATE": Palette.ERROR,
        "24 HOURS":  Palette.WARNING,
        "LONG TERM": Palette.SUCCESS,
        "INFO":      Palette.INFO,
    }

    def __init__(self, parent, idx, item, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg      = bg
        self._item    = item
        self._idx     = idx
        self._expanded = False
        self._body     = None
        self._build()

    def _build(self):
        item   = self._item
        bg     = self._bg
        status = (item.get("status") or "UNKNOWN").upper()
        color  = self.STATUS_COL.get(status, Palette.ON_SURFACE_VAR)
        action = item.get("action", "—")

        # ── header row (always visible, clickable) ────────────────
        hdr = tk.Frame(self, bg=Palette.SURFACE_HIGH,
                       padx=Palette.PAD_MD, pady=Palette.PAD_SM,
                       cursor="hand2")
        hdr.pack(fill="x")

        # event number
        tk.Label(hdr, text=f"{self._idx:02d}",
                 font=Palette.bold(Palette.LABEL_SM),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH,
                 width=3).pack(side="left")

        # status badge
        badge = tk.Frame(hdr, bg=color, padx=6, pady=1)
        badge.pack(side="left", padx=(0, Palette.PAD_SM))
        tk.Label(badge, text=status,
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.SURFACE, bg=color).pack()

        # action / attack type
        tk.Label(hdr, text=action,
                 font=Palette.bold(Palette.LABEL_SM),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_HIGH,
                 anchor="w").pack(side="left", fill="x", expand=True)

        # timestamp
        tk.Label(hdr,
                 text=item.get("timestamp", "—"),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGH).pack(side="right",
                                               padx=(0, Palette.PAD_SM))

        # toggle arrow
        self._arrow = tk.Label(hdr, text="▶",
                               font=Palette.bold(Palette.MICRO),
                               fg=Palette.PRIMARY,
                               bg=Palette.SURFACE_HIGH,
                               cursor="hand2")
        self._arrow.pack(side="right")

        for w in [hdr] + list(hdr.winfo_children()):
            w.bind("<Button-1>", lambda e: self._toggle())

        self._body = tk.Frame(self, bg=bg)

        # source info
        src_row = tk.Frame(self._body, bg=bg,
                           padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        src_row.pack(fill="x")
        for label, val in [
            ("Source",    item.get("source", "—")),
            ("Timestamp", item.get("timestamp", "—")),
        ]:
            r = tk.Frame(src_row, bg=bg)
            r.pack(fill="x", pady=1)
            tk.Label(r, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg, width=10, anchor="w").pack(side="left")
            tk.Label(r, text=val,
                     font=Palette.font(Palette.LABEL_SM),
                     fg=Palette.ON_SURFACE,
                     bg=bg).pack(side="left")

        # verdict
        verdict = item.get("verdict", "")
        if verdict:
            v_frame = tk.Frame(self._body, bg=Palette.SURFACE_CONTAINER,
                               padx=Palette.PAD_LG, pady=Palette.PAD_SM)
            v_frame.pack(fill="x", padx=Palette.PAD_LG,
                         pady=(0, Palette.PAD_SM))
            tk.Label(v_frame, text="VERDICT",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.PRIMARY,
                     bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
            tk.Label(v_frame, text=verdict,
                     font=Palette.font(Palette.LABEL_SM),
                     fg=Palette.ON_SURFACE,
                     bg=Palette.SURFACE_CONTAINER,
                     wraplength=550, justify="left").pack(anchor="w")

        # SHAP features
        features = item.get("top_features", [])
        if features:
            f_frame = tk.Frame(self._body, bg=bg,
                               padx=Palette.PAD_LG, pady=Palette.PAD_SM)
            f_frame.pack(fill="x")
            tk.Label(f_frame, text="FEATURE CONTRIBUTIONS",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg).pack(anchor="w",
                                 pady=(0, Palette.PAD_SM))

            max_shap = max(abs(f.get("shap_value", 0))
                           for f in features) or 1.0

            for feat in features[:4]:
                direction = feat.get("direction", "up")
                shap_val  = float(feat.get("shap_value", 0))
                arr_color = Palette.ERROR if direction == "up" \
                            else Palette.SUCCESS
                arrow     = "▲" if direction == "up" else "▼"

                frow = tk.Frame(f_frame, bg=Palette.SURFACE_CONTAINER,
                                padx=Palette.PAD_MD, pady=Palette.PAD_SM)
                frow.pack(fill="x", pady=2)

                top = tk.Frame(frow, bg=Palette.SURFACE_CONTAINER)
                top.pack(fill="x")
                tk.Label(top, text=arrow,
                         font=Palette.bold(Palette.MICRO),
                         fg=arr_color,
                         bg=Palette.SURFACE_CONTAINER).pack(
                    side="left", padx=(0, Palette.PAD_XS))
                tk.Label(top, text=feat.get("feature", ""),
                         font=Palette.bold(Palette.LABEL_SM),
                         fg=Palette.ON_SURFACE,
                         bg=Palette.SURFACE_CONTAINER).pack(side="left")
                tk.Label(top, text=f"SHAP: {shap_val:+.3f}",
                         font=Palette.bold(Palette.MICRO),
                         fg=arr_color,
                         bg=Palette.SURFACE_CONTAINER).pack(side="right")

                # mini bar
                track = tk.Frame(frow, bg=Palette.SURFACE_HIGH, height=3)
                track.pack(fill="x", pady=(2, 0))
                tk.Frame(track, bg=arr_color, height=3).place(
                    relx=0, rely=0,
                    relwidth=min(abs(shap_val) / max_shap, 1.0),
                    relheight=1)

                if feat.get("reason"):
                    tk.Label(frow, text=feat["reason"],
                             font=Palette.font(Palette.MICRO),
                             fg=Palette.ON_SURFACE_VAR,
                             bg=Palette.SURFACE_CONTAINER,
                             wraplength=540, justify="left",
                             anchor="w").pack(
                        fill="x", pady=(Palette.PAD_XS, 0))

        # counterfactuals
        cfs = item.get("counter_factuals", [])
        if cfs:
            cf_frame = tk.Frame(self._body, bg=bg,
                                padx=Palette.PAD_LG,
                                pady=Palette.PAD_SM)
            cf_frame.pack(fill="x")
            tk.Label(cf_frame, text="COUNTERFACTUAL ANALYSIS",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg).pack(anchor="w",
                                 pady=(0, Palette.PAD_SM))

            for cf in cfs:
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
                tk.Label(cfrow, text=f"→ {outcome}",
                         font=Palette.bold(Palette.MICRO),
                         fg=out_col,
                         bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
                tk.Label(cfrow, text=change,
                         font=Palette.font(Palette.MICRO),
                         fg=Palette.ON_SURFACE_VAR,
                         bg=Palette.SURFACE_CONTAINER,
                         wraplength=540, justify="left").pack(
                    anchor="w", pady=(2, 0))

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x")

    def _toggle(self):
        self._expanded = not self._expanded
        self._arrow.config(text="▼" if self._expanded else "▶")
        if self._expanded:
            self._body.pack(fill="x")
        else:
            self._body.pack_forget()


class RecommendationPanel(tk.Frame):
    """Shows per-family recommendations matching the PDF section VI."""

    _RECS = {
        "DoS": [
            ("IMMEDIATE",  "Block source IP at firewall level immediately."),
            ("IMMEDIATE",  "Enable SYN cookies on the affected host."),
            ("24 HOURS",   "Implement rate limiting on affected ports and services."),
            ("24 HOURS",   "Contact upstream ISP to apply null-routing on attacking IP."),
            ("LONG TERM",  "Deploy a DDoS mitigation service or scrubbing center."),
            ("LONG TERM",  "Harden network architecture with redundant failover paths."),
        ],
        "Probe": [
            ("IMMEDIATE",  "Identify and close all unused open ports on scanned hosts."),
            ("IMMEDIATE",  "Add the scanning IP to the firewall block list."),
            ("24 HOURS",   "Enable port scan detection on IDS/IPS and tune thresholds."),
            ("24 HOURS",   "Audit firewall rules — remove overly permissive allow rules."),
            ("LONG TERM",  "Schedule regular vulnerability scans across all services."),
            ("LONG TERM",  "Segment the network to limit lateral visibility."),
        ],
        "R2L": [
            ("IMMEDIATE",  "Lock or reset credentials for all targeted accounts."),
            ("IMMEDIATE",  "Terminate all active sessions for affected user accounts."),
            ("IMMEDIATE",  "Block the source IP at the perimeter firewall."),
            ("24 HOURS",   "Enforce multi-factor authentication on all remote access."),
            ("24 HOURS",   "Audit SSH authorized_keys and remove unrecognized keys."),
            ("LONG TERM",  "Implement account lockout after 5 failed authentication attempts."),
            ("LONG TERM",  "Deploy SIEM rule to alert on repeated failed logins."),
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

    _URGENCY_COL = {
        "IMMEDIATE": Palette.ERROR,
        "24 HOURS":  Palette.WARNING,
        "LONG TERM": Palette.SUCCESS,
    }

    _URGENCY_BG = {
        "IMMEDIATE": Palette.SURFACE,
        "24 HOURS":  Palette.SURFACE,
        "LONG TERM": Palette.SURFACE,
    }

    def __init__(self, parent, artifacts=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg        = bg
        self._artifacts = artifacts or []
        self._build()

    def _detect_families(self):
        families = set()
        for a in self._artifacts:
            action = a.get("action", "")
            status = (a.get("status") or "").upper()
            if any(k in action for k in ("DoS", "Flood")):
                families.add("DoS")
            if any(k in action for k in ("Probe", "Scan")):
                families.add("Probe")
            if any(k in action for k in ("R2L", "Brute", "Exfil",
                                          "Login", "FTP")):
                families.add("R2L")
            if any(k in action for k in ("U2R", "Priv", "Shell",
                                          "Rootkit", "Backdoor",
                                          "SUID", "Cron", "Reverse")):
                families.add("U2R")
        return families or set(self._RECS.keys())

    def _build(self):
        bg       = self._bg
        families = self._detect_families()

        tk.Label(self, text="VI. RECOMMENDATIONS",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(
            anchor="w",
            padx=Palette.PAD_LG,
            pady=(Palette.PAD_LG, Palette.PAD_SM))

        for family in ["DoS", "Probe", "R2L", "U2R"]:
            if family not in families:
                continue

            # family header
            fhdr = tk.Frame(self, bg=Palette.SURFACE_HIGH,
                            padx=Palette.PAD_MD, pady=Palette.PAD_SM)
            fhdr.pack(fill="x", padx=Palette.PAD_LG,
                      pady=(Palette.PAD_SM, 0))
            tk.Label(fhdr,
                     text=f"Recommendations for {family} Attacks",
                     font=Palette.bold(Palette.LABEL_SM),
                     fg=Palette.ON_SURFACE,
                     bg=Palette.SURFACE_HIGH).pack(anchor="w")

            for urgency, text in self._RECS[family]:
                color = self._URGENCY_COL.get(urgency, Palette.ON_SURFACE_VAR)

                wrapper = tk.Frame(self, bg=color)
                wrapper.pack(fill="x",
                             padx=Palette.PAD_LG,
                             pady=1)

                row = tk.Frame(wrapper,
                               bg=Palette.SURFACE_CONTAINER,
                               padx=Palette.PAD_MD,
                               pady=Palette.PAD_SM)
                row.pack(fill="x", padx=(3, 0))

                badge = tk.Frame(row, bg=color, padx=6, pady=1)
                badge.pack(side="left", padx=(0, Palette.PAD_SM))
                tk.Label(badge, text=urgency,
                         font=Palette.bold(Palette.MICRO),
                         fg=Palette.SURFACE, bg=color).pack()

                tk.Label(row, text=text,
                         font=Palette.font(Palette.LABEL_SM),
                         fg=Palette.ON_SURFACE,
                         bg=Palette.SURFACE_CONTAINER,
                         wraplength=500,
                         justify="left",
                         anchor="w").pack(side="left",
                                          fill="x", expand=True)

        tk.Frame(self, height=Palette.PAD_LG, bg=bg).pack()


class MetadataPanel(tk.Frame):
    def __init__(self, parent, report=None,
                 on_save_notes=None, on_sign=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg            = bg
        self._report        = report or {}
        self._on_save_notes = on_save_notes
        self._on_sign       = on_sign
        self._build()

    def _build(self):
        r  = self._report
        bg = self._bg

        meta = tk.Frame(self, bg=bg, padx=Palette.PAD_MD,
                        pady=Palette.PAD_MD)
        meta.pack(fill="x")

        hdr = tk.Frame(meta, bg=bg)
        hdr.pack(fill="x", pady=(0, Palette.PAD_MD))
        tk.Label(hdr, text="ℹ", font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(side="left", padx=(0, 6))
        tk.Label(hdr, text="Metadata",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.ON_SURFACE, bg=bg).pack(side="left")

        metric    = r.get("metric_card", {})
        signed_at = r.get("signed_at")
        signed_str = str(signed_at)[:19] if signed_at else "Not signed"

        for field, value in [
            ("CASE NUMBER",     r.get("case_number", "—")),
            ("STATUS",          r.get("status", "—").upper()),
            ("CLEARANCE LEVEL", f"Level {r.get('clearance_level', '—')}"),
            ("HASH SHA-256",    metric.get("hash_sha256", "—")),
            ("GENERATED",       str(r.get("generated_at", ""))[:10]),
            ("SIGNED AT",       signed_str),
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
                     fg=color, bg=bg, anchor="w",
                     justify="left", wraplength=160).pack(fill="x")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

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

        self._notes_status = tk.Label(notes, text="",
                                       font=Palette.font(Palette.MICRO),
                                       fg=Palette.SUCCESS, bg=bg)
        self._notes_status.pack(anchor="w")

        GoldButton(notes, text="APPEND TO LOG",
                   command=self._save_notes).pack(fill="x", ipady=6)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        sign_frame = tk.Frame(self, bg=bg,
                              padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        sign_frame.pack(fill="x")

        if r.get("status", "") == "signed":
            tk.Label(sign_frame, text="✔  Report Signed",
                     font=Palette.bold(Palette.LABEL),
                     fg=Palette.SUCCESS, bg=bg).pack(anchor="w")
        else:
            GoldButton(sign_frame, text="Sign Report",
                       command=self._sign).pack(fill="x", ipady=6)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        proof = tk.Frame(self, bg=bg,
                         padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        proof.pack(fill="x")
        proof_hdr = tk.Frame(proof, bg=bg)
        proof_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        tk.Label(proof_hdr, text="✔",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.SUCCESS, bg=bg).pack(side="left", padx=(0, 6))
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
                     lambda e: refresh.config(fg=Palette.ON_SURFACE_VAR))

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        canvas = tk.Canvas(self, bg=self._bg, highlightthickness=0)
        sb     = tk.Scrollbar(self, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._list = tk.Frame(canvas, bg=self._bg)
        win = canvas.create_window((0, 0), window=self._list, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        self._list.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))

        self._status = tk.Label(self._list, text="Loading…",
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

    def _render(self, items):
        for w in self._list.winfo_children():
            w.destroy()

        if not items:
            tk.Label(self._list,
                     text="No reports yet.\nGenerate one from\nthe Analysis page.",
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg, justify="center").pack(pady=Palette.PAD_LG)
            return

        STATUS_COLOR = {"signed": Palette.SUCCESS, "draft": Palette.WARNING}

        for item in items:
            rid    = item["id"]
            title  = item.get("title", f"Report #{rid}")
            case   = item.get("case_number", "")
            status = item.get("status", "draft").lower()
            date   = str(item.get("generated_at", ""))[:10]
            s_col  = STATUS_COLOR.get(status, Palette.ON_SURFACE_VAR)

            row = tk.Frame(self._list, bg=self._bg, cursor="hand2",
                           padx=Palette.PAD_MD, pady=Palette.PAD_SM)
            row.pack(fill="x")

            tk.Label(row, text="●", font=Palette.bold(Palette.MICRO),
                     fg=s_col, bg=self._bg).pack(side="right")
            tk.Label(row, text=title,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE, bg=self._bg,
                     anchor="w", wraplength=160).pack(anchor="w")
            tk.Label(row, text=f"{case}  •  {date}",
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
                      if self._sel_row == rid else self._bg)
                r.config(bg=bg)
                for w in r.winfo_children():
                    w.config(bg=bg)

            def _click(e, rid=rid):
                self._sel_row = rid
                if self._on_select:
                    self._on_select(rid)

            for w in [row] + list(row.winfo_children()):
                w.bind("<Enter>",    _enter)
                w.bind("<Leave>",    _leave)
                w.bind("<Button-1>", _click)

        if items and self._on_select:
            self._on_select(items[0]["id"])


class ReportsPage(tk.Frame):

    def __init__(self, parent, user=None, on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user      = user
        self._report    = None
        self._report_id = None
        self._bar_chart = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        ReportListPanel(
            self,
            on_select=self._on_report_selected,
            bg=Palette.SURFACE_LOW,
            width=200,
        ).grid(row=0, column=0, sticky="nsew")

        tk.Frame(self, bg=Palette.OUTLINE,
                 width=1).grid(row=0, column=0, sticky="nse")

        scroll_host = tk.Frame(self, bg=Palette.SURFACE)
        scroll_host.grid(row=0, column=1, sticky="nsew")

        self._canvas = tk.Canvas(scroll_host, bg=Palette.SURFACE,
                                  highlightthickness=0)
        scroll = tk.Scrollbar(scroll_host, orient="vertical",
                               command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=Palette.SURFACE)
        win = self._canvas.create_window((0, 0), window=self._inner,
                                          anchor="nw")
        self._canvas.bind("<Configure>",
                           lambda e: self._canvas.itemconfig(
                               win, width=e.width))
        self._inner.bind("<Configure>",
                          lambda e: self._canvas.configure(
                              scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Enter>",
                           lambda e: self._canvas.bind_all(
                               "<MouseWheel>",
                               lambda ev: self._canvas.yview_scroll(
                                   int(-1 * (ev.delta / 120)), "units")))
        self._canvas.bind("<Leave>",
                           lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._show_empty()

    def _show_empty(self):
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(self._inner, text="Select a report from the list.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).place(relx=0.5, rely=0.4, anchor="center")

    def _show_loading(self):
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(self._inner, text="Loading report…",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(pady=Palette.PAD_XL)

    def _show_error(self, msg):
        for w in self._inner.winfo_children():
            w.destroy()
        tk.Label(self._inner, text=f"⚠ {msg}",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ERROR,
                 bg=Palette.SURFACE).pack(pady=Palette.PAD_XL)

    def _on_report_selected(self, report_id):
        if self._report_id == report_id:
            return
        self._report_id = report_id
        self._show_loading()
        threading.Thread(target=self._fetch_report,
                         args=(report_id,), daemon=True).start()

    def _fetch_report(self, report_id):
        try:
            data = api("get", f"/reports/{report_id}")
            self.after(0, lambda: self._render_report(data))
        except requests.HTTPError as exc:
            msg = f"Server error ({exc.response.status_code})"
            self.after(0, lambda: self._show_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Cannot reach server."))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: self._show_error(msg))

    def _render_report(self, data):
        self._report = data
        for w in self._inner.winfo_children():
            w.destroy()
        p = self._inner

        # breadcrumb
        bc = tk.Frame(p, bg=Palette.SURFACE)
        bc.pack(fill="x", padx=Palette.PAD_XL, pady=(Palette.PAD_LG, 0))
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

        # title row
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
        tk.Label(title_block,
                 text=(f"Generated {str(data.get('generated_at', ''))[:10]}"
                       f"  •  Security Clearance Level "
                       f"{data.get('clearance_level', '—')} Required"),
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w", pady=(4, 0))

        # download button
        btn_row = tk.Frame(title_row, bg=Palette.SURFACE)
        btn_row.pack(side="right", anchor="s", pady=Palette.PAD_SM)
        GoldButton(btn_row, text="PDF (Encrypted)", style="outline",
                   command=lambda: self._download_pdf(True)).pack(
            side="left", padx=(0, Palette.PAD_SM), ipady=4, ipadx=10)

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        # metric card
        MetricCard(p, data=data.get("metric_card", {}),
                   bg=Palette.SURFACE_CONTAINER).pack(
            fill="x", padx=Palette.PAD_XL)

        tk.Frame(p, height=3, bg=Palette.PRIMARY).pack(
            fill="x", padx=Palette.PAD_XL, pady=(0, Palette.PAD_LG))

        # two-column body
        body_row = tk.Frame(p, bg=Palette.SURFACE)
        body_row.pack(fill="x", padx=Palette.PAD_XL)
        body_row.columnconfigure(0, weight=3)
        body_row.columnconfigure(1, weight=1)

        left = tk.Frame(body_row, bg=Palette.SURFACE_CONTAINER)
        left.grid(row=0, column=0, sticky="nsew",
                  padx=(0, Palette.PAD_MD))
        artifacts = data.get("critical_artifacts", [])

        main = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        main.pack(fill="x", padx=Palette.PAD_XL)

        self._section(main, "I. EXECUTIVE SUMMARY",
                      data.get("executive_summary", "—"))

        self._render_status(main, artifacts)

        self._render_vectors(main, data.get("threat_vectors", []))

        self._render_artifacts_overview(main, artifacts)

        self._render_event_details(main, artifacts)

        RecommendationPanel(main, artifacts=artifacts,
                            bg=Palette.SURFACE_CONTAINER).pack(fill="x")

        tk.Frame(main, height=Palette.PAD_LG,
                 bg=Palette.SURFACE_CONTAINER).pack()

        MetadataPanel(
            p,
            report=data,
            on_save_notes=self._save_notes,
            on_sign=self._sign_report,
            bg=Palette.SURFACE_CONTAINER,
        ).pack(fill="x", padx=Palette.PAD_XL,
               pady=(Palette.PAD_MD, 0))

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

    def _render_status(self, parent, artifacts):
        """II. Overall log file status in percentages."""
        bg = Palette.SURFACE_CONTAINER

        sec = tk.Frame(parent, bg=bg)
        sec.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(0, Palette.PAD_LG))

        tk.Label(sec, text="II. OVERALL LOG FILE STATUS",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        total   = len(artifacts)
        normal  = sum(1 for a in artifacts
                      if (a.get("status") or "").upper()
                      in ("LOW", "NORMAL", "BENIGN"))
        threats = total - normal
        n_pct   = (normal  / total * 100) if total else 0
        t_pct   = (threats / total * 100) if total else 0

        stats_row = tk.Frame(sec, bg=bg)
        stats_row.pack(fill="x")

        for label, count, pct, color in [
            ("TOTAL EVENTS",         total,   100.0,  Palette.ON_SURFACE),
            ("THREAT EVENTS",        threats, t_pct,  Palette.ERROR),
            ("NORMAL / BENIGN",      normal,  n_pct,  Palette.SUCCESS),
        ]:
            blk = tk.Frame(stats_row, bg=Palette.SURFACE_HIGH,
                           padx=Palette.PAD_MD, pady=Palette.PAD_MD)
            blk.pack(side="left", fill="x", expand=True,
                     padx=(0, Palette.PAD_SM))

            tk.Label(blk, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_HIGH).pack(anchor="w")
            tk.Label(blk, text=str(count),
                     font=(Palette._FONT[0], 28, "bold"),
                     fg=color,
                     bg=Palette.SURFACE_HIGH).pack(anchor="w")
            tk.Label(blk, text=f"{pct:.1f}%",
                     font=Palette.bold(Palette.LABEL_SM),
                     fg=color,
                     bg=Palette.SURFACE_HIGH).pack(anchor="w")

            # progress bar
            track = tk.Frame(blk, bg=Palette.SURFACE_HIGHEST, height=4)
            track.pack(fill="x", pady=(Palette.PAD_SM, 0))
            tk.Frame(track, bg=color, height=4).place(
                relx=0, rely=0,
                relwidth=min(pct / 100, 1.0),
                relheight=1)

    def _render_vectors(self, parent, vectors):
        """III. Threat vector distribution."""
        bg  = Palette.SURFACE_CONTAINER
        sec = tk.Frame(parent, bg=bg)
        sec.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(0, Palette.PAD_LG))

        tk.Label(sec, text="III. THREAT VECTOR DISTRIBUTION",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        self._bar_chart = BarChart(sec, vectors=vectors, bg=bg)
        self._bar_chart.pack(fill="x")

    def _render_artifacts_overview(self, parent, artifacts):
        """IV. Critical artifacts overview table."""
        bg  = Palette.SURFACE_CONTAINER
        sec = tk.Frame(parent, bg=bg)
        sec.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(0, Palette.PAD_LG))

        tk.Label(sec, text="IV. CRITICAL ARTIFACTS OVERVIEW",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        col_hdr = tk.Frame(sec, bg=bg)
        col_hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        for txt, w in [("TIMESTAMP", 22), ("SOURCE", 16),
                        ("ACTION",    22), ("STATUS", 10)]:
            tk.Label(col_hdr, text=txt,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg, width=w, anchor="w").pack(side="left")

        tk.Frame(sec, height=1, bg=Palette.OUTLINE).pack(
            fill="x", pady=(0, Palette.PAD_SM))

        if artifacts:
            for item in artifacts:
                ArtifactRow(sec, item, bg=bg).pack(fill="x")
        else:
            tk.Label(sec, text="No critical artifacts recorded.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR, bg=bg).pack(
                anchor="w", pady=Palette.PAD_MD)

    def _render_event_details(self, parent, artifacts):
        """V. Detailed event analysis — all events, collapsible rows."""
        bg  = Palette.SURFACE_CONTAINER
        sec = tk.Frame(parent, bg=bg)
        sec.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(0, Palette.PAD_LG))

        tk.Label(sec, text="V. DETAILED EVENT ANALYSIS",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=bg).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        tk.Label(sec,
                 text="Click any event row to expand verdict, "
                      "SHAP features and counterfactuals.",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR, bg=bg).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        if artifacts:
            for idx, item in enumerate(artifacts, start=1):
                EventDetailRow(sec, idx, item, bg=bg).pack(
                    fill="x", pady=1)
        else:
            tk.Label(sec, text="No events to display.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR, bg=bg).pack(
                anchor="w", pady=Palette.PAD_MD)

    def _download_pdf(self, encrypted=False):
        if not self._report_id:
            return
        threading.Thread(target=self._do_download,
                         args=(encrypted,), daemon=True).start()

    def _do_download(self, encrypted):
        from tkinter import filedialog
        try:
            from helper import BASE_URL, session
            resp = session.get(
                f"{BASE_URL}/reports/{self._report_id}/download",
                params={"encrypt": str(encrypted).lower()},
                timeout=(10, 60),
            )
            resp.raise_for_status()

            ext  = ".xpdf" if encrypted else ".pdf"
            path = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=[("Report file", f"*{ext}")],
                initialfile=f"report_{self._report_id}{ext}",
            )
            if not path:
                return

            with open(path, "wb") as f:
                f.write(resp.content)

            if encrypted:
                key = resp.headers.get("X-Decrypt-Key", "")
                self.after(0, lambda k=key: self._show_key_dialog(
                    k,
                    title="PDF Decryption Key",
                    subtitle="AES-256-GCM encrypted report download",
                ))
            else:
                self.after(0, lambda: messagebox.showinfo(
                    "Downloaded", f"Saved to:\n{path}"))

        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: messagebox.showerror("Download Failed", msg))

    def _show_key_dialog(self, hex_key, title, subtitle):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.configure(bg=Palette.SURFACE)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.geometry("520x340")
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()  - 520) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 340) // 2
        dialog.geometry(f"+{x}+{y}")

        hdr = tk.Frame(dialog, bg=Palette.PRIMARY,
                       padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"🔐  {title}",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.ON_PRIMARY, bg=Palette.PRIMARY).pack(anchor="w")
        tk.Label(hdr, text=subtitle,
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_PRIMARY, bg=Palette.PRIMARY).pack(
            anchor="w", pady=(2, 0))

        warn = tk.Frame(dialog, bg=Palette.WARNING,
                        padx=Palette.PAD_MD, pady=Palette.PAD_SM)
        warn.pack(fill="x")
        tk.Label(warn,
                 text="⚠  This key will NOT be shown again. Save it immediately.",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.SURFACE, bg=Palette.WARNING).pack(anchor="w")

        key_frame = tk.Frame(dialog, bg=Palette.SURFACE,
                             padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        key_frame.pack(fill="x")
        tk.Label(key_frame, text="DECRYPTION KEY",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w",
                                           pady=(0, Palette.PAD_SM))

        key_box = tk.Text(key_frame, height=2,
                          font=("Courier New", 10, "bold"),
                          fg=Palette.ON_SURFACE,
                          bg=Palette.SURFACE_HIGHEST,
                          relief="flat", bd=0,
                          padx=10, pady=8, wrap="word",
                          highlightthickness=1,
                          highlightbackground=Palette.OUTLINE,
                          highlightcolor=Palette.PRIMARY)
        key_box.insert("1.0", hex_key)
        key_box.config(state="disabled")
        key_box.pack(fill="x")

        copy_row = tk.Frame(dialog, bg=Palette.SURFACE,
                            padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        copy_row.pack(fill="x")

        copy_status = tk.Label(copy_row, text="",
                                font=Palette.bold(Palette.MICRO),
                                fg=Palette.SUCCESS, bg=Palette.SURFACE)
        copy_status.pack(side="right")

        def _copy():
            dialog.clipboard_clear()
            dialog.clipboard_append(hex_key)
            dialog.update()
            copy_btn.config(text="✔  Copied!", bg=Palette.SUCCESS)
            copy_status.config(text="Key copied to clipboard")
            dialog.after(2500, lambda: (
                copy_btn.config(text="⎘  Copy Key",
                                bg=Palette.SURFACE_HIGHEST),
                copy_status.config(text=""),
            ))

        copy_btn = tk.Button(copy_row, text="⎘  Copy Key",
                              font=Palette.bold(Palette.LABEL_SM),
                              fg=Palette.ON_SURFACE,
                              bg=Palette.SURFACE_HIGHEST,
                              activebackground=Palette.PRIMARY_DIM,
                              activeforeground=Palette.ON_PRIMARY,
                              relief="flat", cursor="hand2",
                              padx=16, pady=6, command=_copy)
        copy_btn.pack(side="left")

        tk.Frame(dialog, bg=Palette.OUTLINE, height=1).pack(fill="x")
        btn_row = tk.Frame(dialog, bg=Palette.SURFACE,
                           padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        btn_row.pack(fill="x")
        tk.Label(btn_row,
                 text="Store this key in a password manager or secure vault.",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(side="left")
        tk.Button(btn_row, text="Close",
                  font=Palette.font(Palette.LABEL_SM),
                  fg=Palette.ON_SURFACE, bg=Palette.SURFACE_HIGH,
                  activebackground=Palette.SURFACE_HIGHEST,
                  relief="flat", cursor="hand2",
                  padx=12, pady=4,
                  command=dialog.destroy).pack(side="right")

    def _save_notes(self, text):
        if not self._report_id:
            return

        def do():
            try:
                api("patch", f"/reports/{self._report_id}/notes",
                    json={"notes": text})
                log.info("Notes saved for report %s", self._report_id)
            except Exception as exc:
                log.error("Failed to save notes: %s", exc)

        threading.Thread(target=do, daemon=True).start()

    def _sign_report(self):
        if not self._report_id:
            return
        if not messagebox.askyesno(
            "Sign Report",
            f"Sign report #{self._report_id}?\nThis action cannot be undone."
        ):
            return

        def do():
            try:
                data = api("patch", f"/reports/{self._report_id}/sign")
                self.after(0, lambda: self._render_report(data))
                log.info("Report %s signed", self._report_id)
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Server error ({exc.response.status_code})"
                self.after(0, lambda: messagebox.showerror("Sign Failed", msg))
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: messagebox.showerror("Sign Failed", msg))

        threading.Thread(target=do, daemon=True).start()