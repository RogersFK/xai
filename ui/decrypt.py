import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from colors import Palette
from components import Components
import fitz  # pymupdf
from PIL import Image, ImageTk



class DecryptPage(tk.Frame):
    """
    Allows an investigator to decrypt an encrypted .xpdf report
    by providing the AES-256-GCM hex key issued at download time.
    """

    def __init__(self, parent, user=None, on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user               = user
        self._on_profile_updated = on_profile_updated
        self._file_path          = None          # selected .xpdf path
        self._status_var         = tk.StringVar()
        self._build()


    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # centre card
        card_wrap = tk.Frame(self, bg=Palette.SURFACE)
        card_wrap.grid(row=0, column=0)

        # ── header ────────────────────────────────────────────────
        hdr = tk.Frame(card_wrap, bg=Palette.SURFACE)
        hdr.pack(fill="x", pady=(0, Palette.PAD_LG))

        tk.Label(
            hdr, text="🔓",
            font=Palette.font(48),
            bg=Palette.SURFACE,
            fg=Palette.PRIMARY,
        ).pack()

        tk.Label(
            hdr,
            text="Decrypt Forensic Report",
            font=Palette.font(Palette.HEADLINE_SM + 2, "bold"),
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE,
        ).pack()

        tk.Label(
            hdr,
            text="Provide an encrypted .xpdf file and the AES-256-GCM key\n"
                 "issued when the report was downloaded.",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE,
            justify="center",
        ).pack(pady=(4, 0))

        # ── card ──────────────────────────────────────────────────
        card = tk.Frame(
            card_wrap,
            bg=Palette.SURFACE_CONTAINER,
            padx=Palette.PAD_LG,
            pady=Palette.PAD_LG,
        )
        card.pack(fill="x", ipadx=Palette.PAD_LG)

        # step 1 — file picker
        Components.field_label(
            card, "Step 1 — Select encrypted report (.xpdf)",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER,
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        file_row = tk.Frame(card, bg=Palette.SURFACE_CONTAINER)
        file_row.pack(fill="x")
        file_row.columnconfigure(0, weight=1)

        self._file_label = tk.Label(
            file_row,
            text="No file selected",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_HIGHEST,
            anchor="w",
            padx=10,
            pady=8,
        )
        self._file_label.grid(row=0, column=0, sticky="ew")

        tk.Button(
            file_row,
            text="Browse…",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_HIGH,
            activebackground=Palette.PRIMARY,
            activeforeground=Palette.SURFACE,
            relief="flat",
            cursor="hand2",
            padx=12,
            command=self._pick_file,
        ).grid(row=0, column=1, padx=(Palette.PAD_SM, 0))

        Components.spacer(card, Palette.PAD_LG,
                          Palette.SURFACE_CONTAINER).pack()

        # step 2 — key input
        Components.field_label(
            card, "Step 2 — Paste your decryption key",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER,
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        self._key_entry = tk.Text(
            card,
            height=3,
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_HIGHEST,
            insertbackground=Palette.PRIMARY,
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            wrap="word",
            highlightthickness=1,
            highlightbackground=Palette.OUTLINE,
            highlightcolor=Palette.PRIMARY,
        )
        self._key_entry.pack(fill="x", ipady=4)

        tk.Label(
            card,
            text="The key is a 64-character hex string issued at download time.",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER,
        ).pack(anchor="w", pady=(4, 0))

        Components.spacer(card, Palette.PAD_LG,
                          Palette.SURFACE_CONTAINER).pack()

        # step 3 — output location
        Components.field_label(
            card, "Step 3 — Choose where to save the decrypted PDF",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER,
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        out_row = tk.Frame(card, bg=Palette.SURFACE_CONTAINER)
        out_row.pack(fill="x")
        out_row.columnconfigure(0, weight=1)

        self._out_label = tk.Label(
            out_row,
            text="No output location selected",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_HIGHEST,
            anchor="w",
            padx=10,
            pady=8,
        )
        self._out_label.grid(row=0, column=0, sticky="ew")

        tk.Button(
            out_row,
            text="Browse…",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_HIGH,
            activebackground=Palette.PRIMARY,
            activeforeground=Palette.SURFACE,
            relief="flat",
            cursor="hand2",
            padx=12,
            command=self._pick_output,
        ).grid(row=0, column=1, padx=(Palette.PAD_SM, 0))

        Components.spacer(card, Palette.PAD_LG,
                          Palette.SURFACE_CONTAINER).pack()

        # status label
        self._status_lbl = tk.Label(
            card,
            textvariable=self._status_var,
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ERROR,
            bg=Palette.SURFACE_CONTAINER,
            wraplength=420,
            justify="center",
        )
        self._status_lbl.pack(fill="x", pady=(0, Palette.PAD_SM))

        # decrypt button
        self._btn = Components.primary_button(
            card,
            text="Decrypt Report",
            command=self._handle_decrypt,
        )
        self._btn.pack(fill="x", ipady=14)

        Components.spacer(card, Palette.PAD_LG,
                          Palette.SURFACE_CONTAINER).pack()

        # info footer
        info = tk.Frame(
            card,
            bg=Palette.SURFACE_HIGH,
            padx=Palette.PAD_MD,
            pady=Palette.PAD_SM,
        )
        info.pack(fill="x")

        tk.Label(
            info,
            text="ℹ",
            font=Palette.bold(Palette.LABEL),
            fg=Palette.PRIMARY,
            bg=Palette.SURFACE_HIGH,
        ).pack(side="left", padx=(0, Palette.PAD_SM))

        tk.Label(
            info,
            text="Decryption happens locally. Your key is never sent to the server.\n"
                 "AES-256-GCM ensures any tampering with the file will cause decryption to fail.",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_HIGH,
            wraplength=380,
            justify="left",
        ).pack(side="left")


    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Select encrypted report",
            filetypes=[("Encrypted report", "*.xpdf"),
                       ("All files", "*.*")],
        )
        if path:
            self._file_path = path
            self._file_label.config(
                text=Path(path).name,
                fg=Palette.ON_SURFACE,
            )
            # auto-suggest output path
            suggested = path.replace(".xpdf", "_decrypted.pdf")
            self._out_path = suggested
            self._out_label.config(
                text=Path(suggested).name,
                fg=Palette.ON_SURFACE,
            )

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Save decrypted PDF",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")],
            initialfile="report_decrypted.pdf",
        )
        if path:
            self._out_path = path
            self._out_label.config(
                text=Path(path).name,
                fg=Palette.ON_SURFACE,
            )


    def _set_status(self, msg: str, color: str = None):
        self.after(0, lambda: (
            self._status_var.set(msg),
            self._status_lbl.config(fg=color or Palette.ERROR),
        ))

    def _set_busy(self, busy: bool):
        self.after(0, lambda: self._btn.config(
            state="disabled" if busy else "normal",
            text="Decrypting…" if busy else "Decrypt Report",
        ))

    def _handle_decrypt(self):
        # validate inputs
        if not self._file_path:
            self._set_status("Please select an encrypted .xpdf file.")
            return

        hex_key = self._key_entry.get("1.0", "end-1c").strip()
        if not hex_key:
            self._set_status("Please paste your decryption key.")
            return

        if len(hex_key) != 64:
            self._set_status(
                f"Key must be 64 hex characters. "
                f"You entered {len(hex_key)} characters."
            )
            return

        try:
            bytes.fromhex(hex_key)
        except ValueError:
            self._set_status("Key contains invalid characters. "
                             "It must be a hex string (0–9, a–f).")
            return

        out_path = getattr(self, "_out_path", None)
        if not out_path:
            self._set_status("Please choose an output location.")
            return

        self._status_var.set("")
        self._set_busy(True)
        threading.Thread(
            target=self._do_decrypt,
            args=(self._file_path, hex_key, out_path),
            daemon=True,
        ).start()

    def _do_decrypt(self, file_path: str, hex_key: str, out_path: str):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            with open(file_path, "rb") as f:
                payload = f.read()

            if len(payload) < 13:
                raise ValueError("File is too small to be a valid encrypted report.")

            key    = bytes.fromhex(hex_key)
            nonce  = payload[:12]
            ct     = payload[12:]
            aesgcm = AESGCM(key)

            try:
                pdf_bytes = aesgcm.decrypt(nonce, ct, None)
            except Exception:
                raise ValueError(
                    "Decryption failed. The key is incorrect or "
                    "the file has been tampered with."
                )

            # verify it looks like a PDF
            if not pdf_bytes.startswith(b"%PDF"):
                raise ValueError(
                    "Decrypted content does not appear to be a valid PDF. "
                    "Please check your key."
                )

            with open(out_path, "wb") as f:
                f.write(pdf_bytes)

            self._set_busy(False)
            self._set_status(
                f"✔ Report decrypted successfully.", Palette.SUCCESS
            )
            # self.after(0, lambda: messagebox.showinfo(
            #     "Decryption Successful",
            #     f"Report saved to:\n{out_path}\n\n"
            #     f"You can now open it with any PDF viewer.",
            # ))
            self.after(0, lambda p=out_path: PDFViewerWindow(self, p))

        except ValueError as exc:
            self._set_busy(False)
            self._set_status(str(exc))

        except OSError as exc:
            self._set_busy(False)
            self._set_status(f"File error: {exc}")

        except Exception as exc:
            self._set_busy(False)
            self._set_status(f"Unexpected error: {exc}")
            
            
            
class PDFViewerWindow(tk.Toplevel):
    """
    Opens a standalone window that renders a decrypted PDF page by page.
    """
    def __init__(self, parent, pdf_path: str):
        super().__init__(parent)
        self.title(f"Decrypted Report — {Path(pdf_path).name}")
        self.configure(bg=Palette.SURFACE)
        self.minsize(700, 600)
        self.state("zoomed")

        self._pdf_path  = pdf_path
        self._doc       = fitz.open(pdf_path)
        self._page_idx  = 0
        self._zoom      = 1.5       # render scale
        self._photos    = []        # keep references alive
        self._build()
        self._render_page()

    def _build(self):
        bar = tk.Frame(self, bg=Palette.SURFACE_LOW,
                       padx=Palette.PAD_MD, pady=Palette.PAD_SM)
        bar.pack(fill="x", side="top")

        tk.Button(
            bar, text="◀  Prev",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_HIGH,
            relief="flat", cursor="hand2", padx=10,
            command=self._prev_page,
        ).pack(side="left")

        tk.Button(
            bar, text="Next  ▶",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_HIGH,
            relief="flat", cursor="hand2", padx=10,
            command=self._next_page,
        ).pack(side="left", padx=(Palette.PAD_SM, 0))

        self._page_lbl = tk.Label(
            bar,
            text=f"Page 1 of {len(self._doc)}",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_LOW,
        )
        self._page_lbl.pack(side="left", padx=Palette.PAD_LG)

        # zoom controls
        for label, delta in [("  −  ", -0.25), ("  +  ", 0.25)]:
            tk.Button(
                bar, text=label,
                font=Palette.font(Palette.LABEL_SM),
                fg=Palette.ON_SURFACE, bg=Palette.SURFACE_HIGH,
                relief="flat", cursor="hand2",
                command=lambda d=delta: self._change_zoom(d),
            ).pack(side="left", padx=(Palette.PAD_SM, 0))

        self._zoom_lbl = tk.Label(
            bar,
            text=f"{int(self._zoom * 100)}%",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_LOW,
            width=5,
        )
        self._zoom_lbl.pack(side="left", padx=(Palette.PAD_SM, 0))

        tk.Button(
            bar, text="✕  Close",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ERROR, bg=Palette.SURFACE_HIGH,
            relief="flat", cursor="hand2", padx=10,
            command=self.destroy,
        ).pack(side="right")

        tk.Frame(self, bg=Palette.OUTLINE, height=1).pack(fill="x")

        # ── scrollable canvas ─────────────────────────────────────
        host = tk.Frame(self, bg=Palette.SURFACE)
        host.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(
            host, bg=Palette.SURFACE,
            highlightthickness=0,
        )
        v_scroll = tk.Scrollbar(host, orient="vertical",
                                command=self._canvas.yview)
        h_scroll = tk.Scrollbar(host, orient="horizontal",
                                command=self._canvas.xview)

        self._canvas.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
        )

        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right",  fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # mouse wheel scroll
        self._canvas.bind("<Enter>", lambda e: self._canvas.bind_all(
            "<MouseWheel>",
            lambda ev: self._canvas.yview_scroll(
                int(-1 * (ev.delta / 120)), "units"
            )
        ))
        self._canvas.bind("<Leave>",
                          lambda e: self._canvas.unbind_all("<MouseWheel>"))

        # keyboard navigation
        self.bind("<Right>", lambda e: self._next_page())
        self.bind("<Left>",  lambda e: self._prev_page())
        self.bind("<plus>",  lambda e: self._change_zoom(0.25))
        self.bind("<minus>", lambda e: self._change_zoom(-0.25))

    def _render_page(self):
        self._canvas.delete("all")
        self._photos.clear()

        page = self._doc[self._page_idx]
        mat  = fitz.Matrix(self._zoom, self._zoom)
        pix  = page.get_pixmap(matrix=mat, alpha=False)

        img   = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        photo = ImageTk.PhotoImage(img)
        self._photos.append(photo)   # prevent GC

        # centre the page on the canvas
        self._canvas.config(scrollregion=(0, 0, pix.width, pix.height))
        self._canvas.create_image(
            pix.width // 2, 0,
            anchor="n", image=photo,
        )

        self._page_lbl.config(
            text=f"Page {self._page_idx + 1} of {len(self._doc)}"
        )

    def _prev_page(self):
        if self._page_idx > 0:
            self._page_idx -= 1
            self._render_page()
            self._canvas.yview_moveto(0)

    def _next_page(self):
        if self._page_idx < len(self._doc) - 1:
            self._page_idx += 1
            self._render_page()
            self._canvas.yview_moveto(0)

    def _change_zoom(self, delta: float):
        self._zoom = max(0.5, min(self._zoom + delta, 3.0))
        self._zoom_lbl.config(text=f"{int(self._zoom * 100)}%")
        self._render_page()            