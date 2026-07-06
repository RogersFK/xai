

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import requests
from colors import Palette
from components import GoldButton
from helper import api, upload
from logger import get_logger

log = get_logger("UPLOAD")


class DashedBorderCanvas(tk.Canvas):
    def __init__(self, parent, bg=None, **kw):
        bg = bg or Palette.SURFACE_CONTAINER
        super().__init__(parent, bg=bg, highlightthickness=0, **kw)
        self._offset   = 0
        self._hovering = False
        self._win_id   = None
        self.bind("<Configure>", self._on_resize)
        self._animate()

    def _on_resize(self, event):
        if self._win_id is not None:
            self.itemconfigure(self._win_id,
                               width=event.width,
                               height=event.height)
        self._draw()

    def set_inner(self, widget):
        self._win_id = self.create_window(
            0, 0, anchor="nw", window=widget,
            width=self.winfo_width() or 400,
            height=self.winfo_height() or 300,
        )
        self._draw()

    def _animate(self):
        self._offset = (self._offset + 1) % 16
        self._draw()
        self.after(60, self._animate)

    def _draw(self):
        self.delete("border")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10:
            return
        r   = 14
        col = Palette.PRIMARY if self._hovering else Palette.OUTLINE_BRIGHT
        dash, gap = 8, 6
        off = self._offset

        def draw_seg(x0, y0, x1, y1, horizontal):
            length = abs(x1-x0) if horizontal else abs(y1-y0)
            pos = (-off) % (dash + gap)
            while pos < length:
                end = min(pos+dash, length)
                if horizontal:
                    self.create_line(x0+pos, y0, x0+end, y0,
                                     fill=col, width=2, tags="border")
                else:
                    self.create_line(x0, y0+pos, x0, y0+end,
                                     fill=col, width=2, tags="border")
                pos += dash + gap

        draw_seg(r, 1, w-r, 1, True)
        draw_seg(r, h-1, w-r, h-1, True)
        draw_seg(1, r, 1, h-r, False)
        draw_seg(w-1, r, w-1, h-r, False)
        for xi, yi, a0 in [(0,0,90),(w-2*r,0,0),(0,h-2*r,180),(w-2*r,h-2*r,270)]:
            self.create_arc(xi+1, yi+1, xi+2*r-1, yi+2*r-1,
                            start=a0, extent=90,
                            outline=col, style="arc",
                            width=2, tags="border")
        self.tag_raise("border")

    def set_hover(self, state: bool):
        self._hovering = state
        self._draw()


class DropZoneUpload(tk.Frame):
    ACCEPTED_EXT = [".log"]

    def __init__(self, parent, on_file_selected=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg               = bg
        self._on_file_selected = on_file_selected
        self._selected_files   = []
        self._index_btn        = None
        self._offset           = 0
        self._hovering         = False
        self._build()
        self._animate()

    def _build(self):
        self._border_canvas = tk.Canvas(self, bg=self._bg,
                                         highlightthickness=0, bd=0)
        self._border_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._border_canvas.bind("<Configure>",
                                  lambda e: self._draw_border())

        inner = tk.Frame(self, bg=self._bg)
        inner.place(x=12, y=12, relwidth=1.0, relheight=1.0,
                    width=-24, height=-24)
        inner.columnconfigure(0, weight=1)

        icon_frame = tk.Frame(inner, bg=Palette.SURFACE_HIGH,
                              width=64, height=64)
        icon_frame.pack(pady=(Palette.PAD_XL, Palette.PAD_MD))
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text="⬆",
                 font=Palette.bold(28),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH).place(relx=.5, rely=.5,
                                                anchor="center")

        tk.Label(inner, text="Drag and drop forensic assets",
                 font=Palette.bold(Palette.TITLE_LG + 2),
                 fg=Palette.ON_SURFACE, bg=self._bg).pack()

        tk.Label(inner,
                 text=("Securely transfer system logs, network captures,\n"
                       "or neural data snapshots for forensic processing."),
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE_VAR, bg=self._bg,
                 justify="center").pack(
            pady=(Palette.PAD_SM, Palette.PAD_LG))

        self._file_label = tk.Label(inner, text="",
                                    font=Palette.bold(Palette.LABEL),
                                    fg=Palette.PRIMARY, bg=self._bg)
        self._file_label.pack()

        btn_row = tk.Frame(inner, bg=self._bg)
        btn_row.pack(pady=(Palette.PAD_SM, Palette.PAD_LG))

        GoldButton(
            btn_row, 
            text="Browse Files",
            command=self._browse).pack(
            side="left", 
            ipady=8, 
            ipadx=20,
            padx=(0, Palette.PAD_MD)
        )

        self._index_btn = GoldButton(btn_row, text="Upload file",
                                     command=self._start_indexing)
        self._index_btn.pack(side="left", ipady=8, ipadx=20)
        self._index_btn.config(state="disabled")

        chips = tk.Frame(inner, bg=self._bg)
        chips.pack(pady=(0, Palette.PAD_XL))
        for ext in [".LOG"]:
            tk.Label(chips, text=ext,
                     font=Palette.bold(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_HIGH,
                     padx=10, pady=4).pack(
                side="left", padx=Palette.PAD_SM)

        for widget in (self._border_canvas, inner):
            widget.bind("<Enter>", lambda e: self._set_hover(True))
            widget.bind("<Leave>", lambda e: self._set_hover(False))

    def _draw_border(self):
        c = self._border_canvas
        c.delete("border")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10 or h < 10:
            return
        r, dash, gap = 14, 8, 6
        col = Palette.PRIMARY if self._hovering else Palette.OUTLINE_BRIGHT
        off = self._offset

        def seg(x0, y0, x1, y1, horiz):
            length = abs(x1-x0) if horiz else abs(y1-y0)
            pos = (-off) % (dash+gap)
            while pos < length:
                end = min(pos+dash, length)
                if horiz:
                    c.create_line(x0+pos, y0, x0+end, y0,
                                  fill=col, width=2, tags="border")
                else:
                    c.create_line(x0, y0+pos, x0, y0+end,
                                  fill=col, width=2, tags="border")
                pos += dash + gap

        seg(r, 2, w-r, 2, True)
        seg(r, h-2, w-r, h-2, True)
        seg(2, r, 2, h-r, False)
        seg(w-2, r, w-2, h-r, False)
        for xi, yi, a0 in [(0,0,90),(w-2*r,0,0),(0,h-2*r,180),(w-2*r,h-2*r,270)]:
            c.create_arc(xi+2, yi+2, xi+2*r-2, yi+2*r-2,
                         start=a0, extent=90,
                         outline=col, style="arc",
                         width=2, tags="border")

    def _animate(self):
        self._offset = (self._offset + 1) % 16
        self._draw_border()
        self.after(60, self._animate)

    def _set_hover(self, state: bool):
        self._hovering = state
        self._draw_border()

    def _browse(self):
        files = filedialog.askopenfilenames(
            title="Select Forensic Evidence Files",
            filetypes=[
                ("All Supported", "*.json *.csv *.pcap *.log"),
                ("JSON", "*.json"), ("CSV", "*.csv"),
                ("PCAP", "*.pcap"), ("LOG", "*.log"),
                ("All", "*.*"),
            ]
        )
        if files:
            self._selected_files = list(files)
            names = [os.path.basename(f) for f in files]
            display = ", ".join(names[:2])
            if len(names) > 2:
                display += f" +{len(names)-2} more"
            self._file_label.config(text=f"Selected: {display}")
            self._index_btn.config(state="normal")
            if self._on_file_selected:
                self._on_file_selected(self._selected_files)

    def _start_indexing(self):
        if not self._selected_files:
            return
        self._index_btn.config(state="disabled", text="Uploading…")
        self._file_label.config(text="")
        threading.Thread(
            target=self._do_upload,
            args=(list(self._selected_files),),
            daemon=True
        ).start()

    def _do_upload(self, files: list):
        succeeded = []
        failed    = []
        for filepath in files:
            try:
                result = upload("/logs/upload", filepath)
                succeeded.append(result.get("original_name",
                                            os.path.basename(filepath)))
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Upload failed.")
                except Exception:
                    msg = f"Server error ({exc.response.status_code})"
                failed.append((os.path.basename(filepath), msg))
            except requests.ConnectionError:
                failed.append((os.path.basename(filepath),
                               "Cannot reach server."))
            except Exception as exc:
                failed.append((os.path.basename(filepath), str(exc)))
        self.after(0, lambda: self._on_upload_done(succeeded, failed))

    def _on_upload_done(self, succeeded: list, failed: list):
        self._selected_files = []
        self._index_btn.config(state="disabled", text="Upload file")
        if succeeded and not failed:
            self._file_label.config(
                text=f"✓ {len(succeeded)} file(s) uploaded successfully.",
                fg=Palette.SUCCESS)
        elif failed and not succeeded:
            self._file_label.config(
                text=f"✗ Failed: {', '.join(f for f, _ in failed)}",
                fg=Palette.ERROR)
        else:
            self._file_label.config(
                text=f"✓ {len(succeeded)} uploaded   ✗ {len(failed)} failed",
                fg=Palette.WARNING)
        if succeeded and hasattr(self, "_recent"):
            self._recent.refresh()



class IngestionItem(tk.Frame):
    STATUS_MAP = {
        "PROCESSING": (Palette.WARNING, "●"),
        "COMPLETE":   (Palette.SUCCESS, "●"),
        "FAILED":     (Palette.ERROR,   "●"),
        "PENDING":    (Palette.INFO,    "●"),
    }
    ICON_MAP = {
        ".pcap": "☰",
        ".csv":  "☰",
        ".log":  "☐",
        ".json": "{ }",
    }

    def __init__(self, parent, item: dict, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(item, bg)

    def _build(self, item: dict, bg: str):
        filename       = item.get("original_name", "unknown")
        size           = self._fmt_size(item.get("file_size", 0))
        date           = self._fmt_date(item.get("uploaded_at", ""))
        status         = (item.get("status") or "COMPLETE").upper()
        log_source     = item.get("log_source", "")
        log_format     = item.get("log_format", "")
        analysis_count = item.get("analysis_count", 0)

        row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_MD)

        # file type icon
        ext      = os.path.splitext(filename)[1].lower()
        icon_char = self.ICON_MAP.get(ext, "☐")
        icon_bg   = Palette.ERROR if status == "FAILED" else Palette.SURFACE_HIGH

        ic = tk.Frame(row, bg=icon_bg, width=36, height=36)
        ic.pack(side="left", padx=(0, Palette.PAD_SM))
        ic.pack_propagate(False)
        tk.Label(ic, text=icon_char,
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR if status != "FAILED"
                    else Palette.ERROR,
                 bg=icon_bg).place(relx=.5, rely=.5, anchor="center")

        col, dot = self.STATUS_MAP.get(status,
                                       (Palette.ON_SURFACE_VAR, "●"))
        chip = tk.Frame(row, bg=bg)
        chip.pack(side="right", anchor="center")
        tk.Label(chip, text=dot,
                 font=Palette.bold(Palette.MICRO),
                 fg=col, bg=bg).pack(side="left", padx=(0, 3))
        tk.Label(chip, text=status,
                 font=Palette.bold(Palette.MICRO),
                 fg=col, bg=bg).pack(side="left")

        # analysis count badge
        if analysis_count > 0:
            tk.Label(row,
                     text=f"◈ {analysis_count}",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.PRIMARY,
                     bg=bg).pack(side="right",
                                  padx=(0, Palette.PAD_SM))

        info = tk.Frame(row, bg=bg)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=filename,
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=bg, anchor="w").pack(fill="x")

        meta_parts = [size, date]
        if log_source:
            meta_parts.append(log_source)
        if log_format:
            meta_parts.append(log_format.upper())

        tk.Label(info,
                 text="  •  ".join(meta_parts),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, anchor="w").pack(fill="x")

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_MD)

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        if not size_bytes:
            return "—"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def _fmt_date(iso: str) -> str:
        if not iso:
            return "—"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y")
        except Exception:
            return str(iso)[:10]



class RecentIngestion(tk.Frame):

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg   = bg
        self._list = None
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=Palette.PAD_MD,
                 pady=(Palette.PAD_LG, 0))

        title_block = tk.Frame(hdr, bg=self._bg)
        title_block.pack(side="left")
        tk.Label(title_block, text="Recent Ingestions",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack(anchor="w")
        self._subtitle = tk.Label(
            title_block, text="Loading…",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=self._bg)
        self._subtitle.pack(anchor="w")

        # VIEW HISTORY + REFRESH on the right
        right_hdr = tk.Frame(hdr, bg=self._bg)
        right_hdr.pack(side="right", anchor="n")

        refresh_lbl = tk.Label(
            right_hdr, text="↻",
            font=Palette.bold(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=self._bg, cursor="hand2")
        refresh_lbl.pack(side="right", padx=(Palette.PAD_SM, 0))
        refresh_lbl.bind("<Button-1>", lambda e: self._load())
        refresh_lbl.bind("<Enter>",
                         lambda e: refresh_lbl.config(fg=Palette.PRIMARY))
        refresh_lbl.bind("<Leave>",
                         lambda e: refresh_lbl.config(
                             fg=Palette.ON_SURFACE_VAR))

        lbl = tk.Label(right_hdr, text="VIEW\nHISTORY",
                       font=Palette.bold(Palette.MICRO),
                       fg=Palette.PRIMARY,
                       bg=self._bg, cursor="hand2",
                       justify="right")
        lbl.pack(side="right")
        lbl.bind("<Enter>",
                 lambda e: lbl.config(fg=Palette.PRIMARY_DIM))
        lbl.bind("<Leave>",
                 lambda e: lbl.config(fg=Palette.PRIMARY))

        tk.Frame(self, height=Palette.PAD_MD, bg=self._bg).pack()

        self._list = tk.Frame(self, bg=self._bg)
        self._list.pack(fill="both", expand=True)

        tk.Frame(self, height=Palette.PAD_MD, bg=self._bg).pack()

    def _load(self):
        self._set_subtitle("Loading…")
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            data = api("get", "/logs/")
            self.after(0, lambda: self._render(data))
        except requests.HTTPError as exc:
            msg = f"Server error ({exc.response.status_code})"
            self.after(0, lambda: self._on_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._on_error("Cannot reach server."))
        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))

    def _render(self, items: list):
        for w in self._list.winfo_children():
            w.destroy()

        if not items:
            self._set_subtitle("No ingestions yet.")
            tk.Label(self._list,
                     text="No files uploaded yet.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg).pack(pady=Palette.PAD_LG)
            return

        # summary line with total size
        total_size = sum(i.get("file_size", 0) for i in items)
        total_analyses = sum(i.get("analysis_count", 0) for i in items)
        self._set_subtitle(
            f"{len(items)} file(s)  •  "
            f"{self._fmt_size(total_size)}  •  "
            f"{total_analyses} analyse(s)"
        )

        for item in items:
            IngestionItem(self._list, item,
                          bg=self._bg).pack(fill="x")

    def _on_error(self, msg: str):
        for w in self._list.winfo_children():
            w.destroy()
        self._set_subtitle("Failed to load.")
        tk.Label(self._list,
                 text=f"⚠ {msg}",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ERROR,
                 bg=self._bg).pack(pady=Palette.PAD_LG)

    def _set_subtitle(self, text: str):
        self._subtitle.config(text=text)

    def refresh(self):
        self._load()

    @staticmethod
    def _fmt_size(b: int) -> str:
        if not b:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} PB"



class FeatureCard(tk.Frame):
    def __init__(self, parent, tag, title, body, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(tag, title, body, bg)

    def _build(self, tag, title, body, bg):
        tk.Frame(self, bg=Palette.PRIMARY,
                 width=3).pack(side="left", fill="y")
        content = tk.Frame(self, bg=bg,
                           padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        content.pack(side="left", fill="both", expand=True)
        tk.Label(content, text=tag.upper(),
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR, bg=bg).pack(anchor="w")
        tk.Label(content, text=title,
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE, bg=bg).pack(
            anchor="w", pady=(Palette.PAD_SM, 0))
        tk.Label(content, text=body,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR, bg=bg,
                 wraplength=220, justify="left").pack(
            anchor="w", pady=(Palette.PAD_SM, 0))



class StatusBar(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=Palette.SURFACE_LOWEST,
                         height=32, **kw)
        self.pack_propagate(False)
        self._build()

    def _build(self):
        left = tk.Frame(self, bg=Palette.SURFACE_LOWEST)
        left.pack(side="left", padx=Palette.PAD_LG)
        for icon, text, color in [
            ("🔒", "E2EE TUNNEL ACTIVE",  Palette.SUCCESS),
            ("☰",  "84% VAULT CAPACITY",  Palette.ON_SURFACE_VAR),
        ]:
            chip = tk.Frame(left, bg=Palette.SURFACE_LOWEST)
            chip.pack(side="left", padx=(0, Palette.PAD_LG))
            tk.Label(chip, text=icon,
                     font=Palette.font(Palette.MICRO),
                     fg=color,
                     bg=Palette.SURFACE_LOWEST).pack(
                side="left", padx=(0, 4))
            tk.Label(chip, text=text,
                     font=Palette.bold(Palette.MICRO),
                     fg=color,
                     bg=Palette.SURFACE_LOWEST).pack(side="left")
        tk.Label(self,
                 text="SOVEREIGN FORENSICS PROTOCOL V4.2.1-GOLD",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOWEST).pack(
            side="right", padx=Palette.PAD_LG)



class UploadLogsPage(tk.Frame):
    def __init__(self, parent, user=None,
                 on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user = user
        self._build()

    def _build(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        body = tk.Frame(self, bg=Palette.SURFACE)
        body.grid(row=0, column=0, sticky="nsew")
        StatusBar(self).grid(row=1, column=0, sticky="ew")
        self._populate(body)

    def _populate(self, p):
        hdr = tk.Frame(p, bg=Palette.SURFACE)
        hdr.pack(fill="x", padx=Palette.PAD_XL,
                 pady=(Palette.PAD_LG, 0))
        tk.Label(hdr, text="Network Log Ingestion",
                 font=(Palette._FONT[0], Palette.DISPLAY, "bold"),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(anchor="w")
        tk.Label(hdr,
                 text="Upload and index new forensic log files for neural analysis.",
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w", pady=(4, 0))

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        cols = tk.Frame(p, bg=Palette.SURFACE)
        cols.pack(fill="both", expand=True, padx=Palette.PAD_XL)
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=2)
        cols.rowconfigure(0, weight=1)
        cols.rowconfigure(1, weight=0)

        left = tk.Frame(cols, bg=Palette.SURFACE)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew",
                  padx=(0, Palette.PAD_MD))
        left.rowconfigure(0, weight=1)
        left.rowconfigure(1, weight=0)
        left.columnconfigure(0, weight=1)
        left.columnconfigure(1, weight=1)

        self._dz = DropZoneUpload(
            left, bg=Palette.SURFACE_CONTAINER,
            on_file_selected=self._on_files)
        self._dz.grid(row=0, column=0, columnspan=2,
                      sticky="nsew", pady=(0, Palette.PAD_MD))

        FeatureCard(left,
                    tag="Vault Integrity",
                    title="SHA-256 Verified",
                    body=("Every bit of uploaded data is hashed "
                          "and anchored to the forensic chain of custody."),
                    bg=Palette.SURFACE_CONTAINER).grid(
            row=1, column=0, columnspan=2, sticky="nsew",
            padx=(0, Palette.PAD_SM))

        # FeatureCard(left,
        #             tag="Processing Power",
        #             title="Neural Indexing",
        #             body=("Automated classification of suspicious patterns "
        #                   "using sovereign AI protocols."),
        #             bg=Palette.SURFACE_CONTAINER).grid(
        #     row=1, column=1, sticky="nsew")

        self._recent = RecentIngestion(cols, bg=Palette.SURFACE_CONTAINER)
        self._recent.grid(row=0, column=1, sticky="nsew")
        self._dz._recent = self._recent

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

    def _on_files(self, files):
        log.debug("Selected %d file(s):", len(files))
        for f in files:
            log.debug("  %s", f)