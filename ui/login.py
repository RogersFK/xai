from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
import threading
from tkinter import messagebox
from colors import Palette
from components import Components
from helper import api
import requests

class LoginPage(tk.Frame):
    def __init__(self, parent, on_login=None, on_register=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._on_login = on_login
        self._on_register = on_register
        self._remember = tk.BooleanVar(value=False)
        self._status_var = tk.StringVar()
        self._build()

    def _resize_bg(self, event=None):
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 2 or h < 2:
            return
        img = self._bg_pil.resize((w, h), Image.LANCZOS)
        self._bg_photo = ImageTk.PhotoImage(img)
        self._canvas.delete("bg")
        self._canvas.create_image(0, 0, anchor="nw", image=self._bg_photo, tags="bg")
        self._canvas.tag_lower("bg")  # keep image behind everything

    def _on_canvas_resize(self, event):
        self._resize_bg()
        self._canvas.coords(self._card_window, event.width // 2, event.height // 2)

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        bg_path = Path(__file__).parent / "assets" / "picha.jpg"
        self._bg_pil = Image.open(bg_path)
        self._bg_photo = None

        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._canvas.bind("<Configure>", self._resize_bg)

        # place the login card on top of the canvas using canvas.create_window
        inner = tk.Frame(self._canvas, bg=Palette.SURFACE_CONTAINER,
                        padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        self._card_window = self._canvas.create_window(
            0, 0, anchor="center", window=inner
        )
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        logo_box = tk.Frame(inner, bg=Palette.SURFACE_LOW, padx=20, pady=14)
        logo_box.pack(pady=(0, Palette.PAD_MD))
        # tk.Label(
        #     logo_box, text="XAI",
        #     font=Palette.font(Palette.HEADLINE_SM + 4, "bold"),
        #     fg=Palette.PRIMARY, bg=Palette.SURFACE_LOW
        # ).pack()

        Components.label(
            inner, "XAI NETWORK LOGS SYSTEM",
            size=Palette.HEADLINE_SM + 2, weight="bold",
            color=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack()

      
        
        logo_path = Path(__file__).parent / "assets" / "head.jpg"
        logo_pil = Image.open(logo_path).convert("RGBA")

        screen_w = self.winfo_screenwidth()
        size = int(screen_w * 0.08)  
        size = max(60, min(size, 120)) 

        logo_pil = logo_pil.resize((size, size), Image.LANCZOS)

        mask = Image.new("L", (size, size), 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)

        circular = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        circular.paste(logo_pil, mask=mask)

        self._logo_photo = ImageTk.PhotoImage(circular)
        tk.Label(inner, image=self._logo_photo, bg=Palette.SURFACE_CONTAINER, bd=0).pack(pady=(4, Palette.PAD_LG))
        
        
        card = tk.Frame(
            inner,
            bg=Palette.SURFACE_CONTAINER,
            padx=25,
            pady=25
        )

        card.pack()

        Components.field_label(
            card,
            "Enter Username",
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_CONTAINER
        ).pack(fill="x", pady=(0, 6))

        self._username = Components.entry(
            card,
            placeholder="Username",
            icon="👤",
            bg=Palette.SURFACE_HIGHEST
        )

        self._username.pack(fill="x", ipady=4)

        Components.spacer(
            card,
            Palette.PAD_MD,
            Palette.SURFACE_CONTAINER
        ).pack()


        hdr = tk.Frame(card, bg=Palette.SURFACE_CONTAINER)
        hdr.pack(fill="x", pady=(0, 6))

        Components.field_label(
            hdr,
            "Enter password",
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_CONTAINER
        ).pack(side="left")

        Components.ghost_button(
            hdr,
            "",
            command=self._reset_encryption,  # Fixed: was 'self', now correct
            bg=Palette.SURFACE_CONTAINER
        ).pack(side="right")

        # Password Entry

        self._password = Components.entry(
            card,
            placeholder="Password",
            show="*",
            icon="🔒",
            bg=Palette.SURFACE_HIGHEST
        )

        self._password.pack(fill="x", ipady=4)

        self._username.bind_entry(
            "<Return>",
            lambda _: self._password._entry.focus()
        )

        self._password.bind_entry(
            "<Return>",
            lambda _: self._handle_login()
        )

        Components.spacer(
            card,
            Palette.PAD_MD,
            Palette.SURFACE_CONTAINER
        ).pack()

        # Remember Toggle

        Components.toggle(
            card,
            self._remember,
            text="Remember node sessions",
            bg=Palette.SURFACE_CONTAINER
        ).pack(anchor="w")

        Components.spacer(
            card,
            Palette.PAD_MD,
            Palette.SURFACE_CONTAINER
        ).pack()

        # Status Label

        self._status_lbl = tk.Label(
            card,
            textvariable=self._status_var,
            fg=Palette.ERROR,
            bg=Palette.SURFACE_CONTAINER,
            font=Palette.font(Palette.LABEL_SM),
            wraplength=320,
            justify="center"
        )

        self._status_lbl.pack(fill="x")

        Components.spacer(
            card,
            Palette.PAD_SM,
            Palette.SURFACE_CONTAINER
        ).pack()

        # Login Button

        self._btn = Components.primary_button(
            card,
            text="Sign In",
            command=self._handle_login
        )

        self._btn.pack(fill="x", ipady=14)

        Components.spacer(
            card,
            Palette.PAD_LG,
            Palette.SURFACE_CONTAINER
        ).pack()

        # Register Link

        link = tk.Label(
            card,
            text="New operator? Request enrollment →",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.INFO,
            bg=Palette.SURFACE_CONTAINER,
            cursor="hand2"
        )

        link.pack()

        link.bind(
            "<Button-1>",
            lambda _: self._on_register()
            if self._on_register else None
        )

        Components.spacer(
            card,
            Palette.PAD_LG,
            Palette.SURFACE_CONTAINER
        ).pack()

        Components.label(
            card,
            "Authorized use only. All actions are logged and\n"
            "audited by the XAI Network Authority.",
            size=Palette.LABEL_SM,
            color=Palette.WARNING,
            bg=Palette.SURFACE_CONTAINER,
            justify="center"
        ).pack()
        

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