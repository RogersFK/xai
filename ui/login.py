
import tkinter as tk
import threading
from tkinter import messagebox
from colors import Palette
from components import Components
from helper import api
import requests

class LoginPage(tk.Frame):
    def __init__(self, parent, on_login=None,on_register=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._on_login = on_login
        self._on_register = on_register
        self._remember = tk.BooleanVar(value=False)
        self._status_var = tk.StringVar()
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        wrap = tk.Frame(self, bg=Palette.SURFACE)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        inner = tk.Frame(wrap, bg=Palette.SURFACE)
        inner.grid(row=0, column=0)

        # logo
        logo_box = tk.Frame(inner, bg=Palette.SURFACE_LOW, padx=20, pady=14)
        logo_box.pack(pady=(0, Palette.PAD_MD))
        tk.Label(logo_box, text="XAI",
                 font=Palette.font(Palette.HEADLINE_SM + 4, "bold"),
                 fg=Palette.PRIMARY, bg=Palette.SURFACE_LOW).pack()

        Components.label(
            inner, "XAI Forensics System",
            size=Palette.HEADLINE_SM + 2, weight="bold",
            color=Palette.ON_SURFACE, bg=Palette.SURFACE
        ).pack()

        Components.label(
            inner, "TERMINAL  AUTHENTICATION",
            size=Palette.LABEL_SM,
            color=Palette.ON_SURFACE_VAR, bg=Palette.SURFACE          # subtle subtitle
        ).pack(pady=(4, Palette.PAD_LG))

        # card
        card = tk.Frame(inner, bg=Palette.SURFACE_CONTAINER,
                        padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        card.pack(fill="x")

        # username
        Components.field_label(
            card, "Investigator Identity",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        self._username = Components.entry(
            card, placeholder="Badge ID or Username",
            icon="👤", bg=Palette.SURFACE_HIGHEST
        )
        self._username.pack(fill="x", ipady=4)                       

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # password header
        hdr = tk.Frame(card, bg=Palette.SURFACE_CONTAINER)
        hdr.pack(fill="x", pady=(0, Palette.PAD_SM))
        Components.field_label(
            hdr, "Access Protocol",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack(side="left")
        Components.ghost_button(
            hdr, "Reset Encryption?",
            command=self._reset_encryption,
            bg=Palette.SURFACE_CONTAINER
        ).pack(side="right")

        self._password = Components.entry(
            card, placeholder="password",
            show="*", icon="🔒", bg=Palette.SURFACE_HIGHEST
        )
        self._password.pack(fill="x", ipady=4)                       

        self._username.bind_entry("<Return>", lambda _: self._password._entry.focus())
        self._password.bind_entry("<Return>", lambda _: self._handle_login())

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        Components.toggle(
            card, self._remember,
            text="Remember node sessions",
            bg=Palette.SURFACE_CONTAINER
        ).pack(anchor="w")

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # status label (errors shown here, not messagebox)
        self._status_lbl = tk.Label(
            card, textvariable=self._status_var,
            fg=Palette.ERROR, bg=Palette.SURFACE_CONTAINER,
            font=Palette.font(Palette.LABEL_SM),
            wraplength=320, justify="center"
        )
        self._status_lbl.pack(fill="x")

        Components.spacer(card, Palette.PAD_SM, Palette.SURFACE_CONTAINER).pack()

        # CTA
        self._btn = Components.primary_button(
            card,
            text="Sign In",
            command=self._handle_login
        )
        self._btn.pack(fill="x", ipady=14)

        Components.spacer(card, Palette.PAD_LG, Palette.SURFACE_CONTAINER).pack()

        link = tk.Label(
            card,
            text="New operator? Request enrollment →",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.INFO,
            bg=Palette.SURFACE_CONTAINER,
            cursor="hand2"
        )
        link.pack(pady=(Palette.PAD_SM, 0))
        link.bind(
            "<Button-1>",
            lambda _: self._on_register()  if self._on_register else None
        )
        
        Components.spacer(card, Palette.PAD_LG, Palette.SURFACE_CONTAINER).pack()

        
        Components.label(
            card,
            "Authorized use only. All actions are logged and\n"
            "audited by the XAI Digital Forensics Authority.",
            size=Palette.LABEL_SM, color=Palette.WARNING,
            bg=Palette.SURFACE_CONTAINER, justify="center"
        ).pack()

        # status bar
        bar = tk.Frame(self, bg=Palette.SURFACE_LOWEST, pady=Palette.PAD_SM)
        bar.grid(row=1, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        Components.status_item(
            bar, "[*]", "Encrypted AES-256", bg=Palette.SURFACE_LOWEST
        ).grid(row=0, column=0, padx=Palette.PAD_LG)

        Components.status_item(
            bar, "[>]", "Node: ALPHA-01", bg=Palette.SURFACE_LOWEST
        ).grid(row=0, column=2, padx=Palette.PAD_LG)


    def _set_status(self, msg: str, color: str = None):
        self.after(0, lambda: (
            self._status_var.set(msg),
            self._status_lbl.config(fg=color or Palette.ERROR)
        ))

    def _set_busy(self, busy: bool):
        self.after(0, lambda: self._btn.config(
            state="disabled" if busy else "normal",
            text="Authenticating....." if busy else "Sign In"
        ))

    def _handle_login(self):
        u = self._username.get().strip()
        p = self._password.get()

        self._status_var.set("")                                       

        if not u:
            self._set_status("Enter your Badge ID or Username.")
            return
        if not p:
            self._set_status("Enter your Access Protocol.")
            return

        self._set_busy(True)
        threading.Thread(target=self._do_login, args=(u, p), daemon=True).start()

    def _do_login(self, u: str, p: str):
        try:
            response = api("post", "/auth/login", json={"username": u, "password": p})
            self.after(0, lambda: self._on_login(response))
        except requests.HTTPError as e:
            try:
                msg = e.response.json().get("detail", "Login failed.")
            except Exception:
                msg = f"Server error ({e.response.status_code})"
            self._set_status(msg)

        except requests.ConnectionError:
            self._set_status("Cannot reach server.")
        finally:
            self._set_busy(False)
    

    def _reset_encryption(self):
        ans = messagebox.askquestion(
            "Reset Encryption",
            "This will revoke your current session key.\nProceed?"
        )
        if ans == "yes":
            self._set_status("Session key revoked. Re-authenticate.", Palette.WARNING)