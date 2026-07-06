from pathlib import Path
import tkinter as tk
import threading
import requests
from tkinter import messagebox
from PIL import Image, ImageTk
from colors import Palette
from components import Components
from helper import api


class RegisterPage(tk.Frame):
    def __init__(self, parent, on_register=None, on_back=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._on_register = on_register  
        self._on_back     = on_back       
        self._status_var  = tk.StringVar()
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

        # logo
        logo_box = tk.Frame(inner, bg=Palette.SURFACE_LOW, padx=20, pady=14)
        logo_box.pack(pady=(0, Palette.PAD_MD))
        # tk.Label(logo_box, text="XAI",
        #          font=Palette.font(Palette.HEADLINE_SM + 4, "bold"),
        #          fg=Palette.PRIMARY, bg=Palette.SURFACE_LOW).pack()

        Components.label(
            inner, "XAI NETWORK LOGS SYSTEM",
            size=Palette.HEADLINE_SM + 2, weight="bold",
            color=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack()

        # Components.label(
        #     inner, "OPERATOR  ENROLLMENT",
        #     size=Palette.LABEL_SM,
        #     color=Palette.ON_SURFACE_VAR, bg=Palette.SURFACE
        # ).pack(pady=(4, Palette.PAD_LG))
        
        
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
        
        

        # card
        card = tk.Frame(inner, bg=Palette.SURFACE_CONTAINER,
                        padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        card.pack(fill="x")

        # username
        Components.field_label(
            card, "Enter username",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        self._username = Components.entry(
            card, placeholder="Choose a username",
            icon="👤", bg=Palette.SURFACE_HIGHEST
        )
        self._username.pack(fill="x", ipady=4)

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # email
        Components.field_label(
            card, "Enter email",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        self._email = Components.entry(
            card, placeholder="operator@domain.gov",
            icon="✉", bg=Palette.SURFACE_HIGHEST
        )
        self._email.pack(fill="x", ipady=4)

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # password
        Components.field_label(
            card, "Enter password",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        self._password = Components.entry(
            card, placeholder="Create password",
            show="*", icon="🔒", bg=Palette.SURFACE_HIGHEST
        )
        self._password.pack(fill="x", ipady=4)

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # confirm password
        Components.field_label(
            card, "Confirm password",
            fg=Palette.ON_SURFACE, bg=Palette.SURFACE_CONTAINER
        ).pack(fill="x", pady=(0, Palette.PAD_SM))

        self._confirm = Components.entry(
            card, placeholder="Repeat password",
            show="*", icon="🔒", bg=Palette.SURFACE_HIGHEST
        )
        self._confirm.pack(fill="x", ipady=4)

        self._username.bind_entry("<Return>", lambda _: self._email._entry.focus())
        self._email.bind_entry("<Return>",    lambda _: self._password._entry.focus())
        self._password.bind_entry("<Return>", lambda _: self._confirm._entry.focus())
        self._confirm.bind_entry("<Return>",  lambda _: self._handle_register())

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # strength bar
        self._strength_bar = _StrengthBar(card, bg=Palette.SURFACE_CONTAINER)
        self._strength_bar.pack(fill="x")
        self._password._entry.bind(
            "<KeyRelease>",
            lambda _: self._strength_bar.update(self._password._entry.get()),
            add="+"
        )

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        # status label
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
            text="Sign Up",
            command=self._handle_register
        )
        self._btn.pack(fill="x", ipady=14)

        Components.spacer(card, Palette.PAD_MD, Palette.SURFACE_CONTAINER).pack()

        back = tk.Label(
            card,
            text="Already enrolled? Return to authentication →",
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.INFO,
            bg=Palette.SURFACE_CONTAINER,
            cursor="hand2"
        )
        back.pack()
        back.bind("<Button-1>", lambda _: self._on_back() if self._on_back else None)

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
            bar, "[+]", "Enrollment Portal", bg=Palette.SURFACE_LOWEST
        ).grid(row=0, column=2, padx=Palette.PAD_LG)


    def _set_status(self, msg: str, color: str = None):
        self.after(0, lambda: (
            self._status_var.set(msg),
            self._status_lbl.config(fg=color or Palette.ERROR)
        ))

    def _set_busy(self, busy: bool):
        self.after(0, lambda: self._btn.config(
            state="disabled" if busy else "normal",
            text="Registering…" if busy else "Sign Up"
        ))


    def _validate(self, u, e, p, c) -> str | None:
        if not u:
            return "Username is required."
        if len(u) < 3:
            return "Username must be at least 3 characters."
        if not e or "@" not in e or "." not in e.split("@")[-1]:
            return "Enter a valid email address."
        if not p:
            return "Password is required."
        if len(p) < 8:
            return "Password must be at least 8 characters."
        if p != c:
            return "Passwords do not match."
        return None


    def _handle_register(self):
        u = self._username.get().strip()
        e = self._email.get().strip()
        p = self._password.get()
        c = self._confirm.get()

        self._status_var.set("")

        err = self._validate(u, e, p, c)
        if err:
            self._set_status(err)
            return

        self._set_busy(True)
        threading.Thread(
            target=self._do_register, args=(u, e, p), daemon=True
        ).start()

    def _do_register(self, u: str, e: str, p: str):
        try:
            api("post", "/auth/register",
                json={"username": u, "email": e, "password": p})

            self.after(0, self._on_success)

        except requests.HTTPError as exc:
            try:
                msg = exc.response.json().get("detail", "Registration failed.")
            except Exception:
                msg = f"Server error ({exc.response.status_code})"
            self._set_status(msg)

        except requests.ConnectionError:
            self._set_status("Cannot reach server. Is the backend running?")

        except requests.Timeout:
            self._set_status("Request timed out. Try again.")

        except Exception as exc:
            self._set_status(f"Unexpected error: {exc}")

        finally:
            self._set_busy(False)

    def _on_success(self):
        messagebox.showinfo(
            "Enrollment Complete",
            "Operator account created.\nReturn to authentication to sign in."
        )
        if self._on_register:
            self._on_register()         



class _StrengthBar(tk.Frame):
    _LEVELS = [
        (0,  "Too short",  Palette_ref := None),   
        (25, "Weak",       None),
        (50, "Fair",       None),
        (75, "Strong",     None),
        (100,"Very strong",None),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=kw.get("bg", Palette.SURFACE_CONTAINER))
        self._bg = kw.get("bg", Palette.SURFACE_CONTAINER)

        row = tk.Frame(self, bg=self._bg)
        row.pack(fill="x")

        self._bar = tk.Frame(row, height=3, bg=Palette.SURFACE_HIGH)
        self._bar.pack(fill="x", side="left", expand=True)

        self._lbl = tk.Label(
            row, text="", width=10,
            font=Palette.font(Palette.LABEL_SM),
            fg=Palette.ON_SURFACE_VAR, bg=self._bg,
            anchor="e"
        )
        self._lbl.pack(side="right")

        self._fill = tk.Frame(self._bar, height=3, bg=Palette.SURFACE_HIGH)
        self._fill.place(x=0, y=0, relheight=1, relwidth=0)

    def update(self, password: str):
        score, label, color = self._score(password)
        self._fill.place(relwidth=score / 100)
        self._fill.config(bg=color)
        self._lbl.config(text=label, fg=color)

    @staticmethod
    def _score(pw: str):
        if len(pw) < 6:
            return 0,  "Too short", Palette.ERROR
        score = 0
        if len(pw) >= 8:  score += 25
        if len(pw) >= 12: score += 15
        if any(c.isupper() for c in pw): score += 20
        if any(c.isdigit() for c in pw): score += 20
        if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pw): score += 20
        score = min(score, 100)

        if score < 25:  return score, "Weak",        Palette.ERROR
        if score < 50:  return score, "Fair",         Palette.WARNING
        if score < 75:  return score, "Strong",       Palette.SUCCESS
        return              score, "Very strong",  Palette.SUCCESS