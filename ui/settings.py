from colors import Palette
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import platform
from components import ToggleSwitch, GoldButton




class StyledEntry(tk.Frame):
    """Single-line dark input field matching the design."""
    def __init__(self, parent, value="", placeholder="",
                 show="", width=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_HIGH)
        super().__init__(parent, bg=bg,
                         highlightbackground=Palette.OUTLINE,
                         highlightcolor=Palette.PRIMARY,
                         highlightthickness=1, bd=0)
        self._var = tk.StringVar(value=value)
        kw2 = {}
        if width:
            kw2["width"] = width
        self._entry = tk.Entry(
            self, textvariable=self._var,
            font=Palette.font(Palette.BODY),
            fg=Palette.ON_SURFACE,
            bg=bg, bd=0, relief="flat",
            insertbackground=Palette.PRIMARY,
            selectbackground=Palette.PRIMARY_DIM,
            selectforeground=Palette.ON_PRIMARY,
            show=show, **kw2
        )
        self._entry.pack(fill="x", padx=10, pady=8)
        self._entry.bind("<FocusIn>",
                         lambda e: self.config(
                             highlightbackground=Palette.PRIMARY))
        self._entry.bind("<FocusOut>",
                         lambda e: self.config(
                             highlightbackground=Palette.OUTLINE))

    def get(self): return self._var.get()
    def set(self, v): self._var.set(v)


class StyledDropdown(tk.Frame):
    """Gold-accent dropdown (OptionMenu)."""
    def __init__(self, parent, options, default=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_HIGH)
        super().__init__(parent, bg=bg,
                         highlightbackground=Palette.OUTLINE_BRIGHT,
                         highlightthickness=1)
        self._var = tk.StringVar(value=default or options[0])
        style = ttk.Style()
        style.configure("Gold.TMenubutton",
                         background=Palette.SURFACE_HIGH,
                         foreground=Palette.ON_SURFACE,
                         relief="flat",
                         font=Palette.font(Palette.BODY))
        menu = tk.OptionMenu(self, self._var, *options)
        menu.config(bg=Palette.SURFACE_HIGH,
                    fg=Palette.ON_SURFACE,
                    activebackground=Palette.SURFACE_HIGHEST,
                    activeforeground=Palette.PRIMARY,
                    highlightthickness=0,
                    relief="flat",
                    font=Palette.font(Palette.BODY),
                    indicatoron=True,
                    bd=0)
        menu["menu"].config(bg=Palette.SURFACE_HIGH,
                            fg=Palette.ON_SURFACE,
                            activebackground=Palette.PRIMARY_DIM,
                            activeforeground=Palette.ON_PRIMARY,
                            font=Palette.font(Palette.BODY),
                            relief="flat", bd=0)
        menu.pack(fill="x", padx=4, pady=4)

    def get(self): return self._var.get()


class SectionHeader(tk.Frame):
    """Gold shield icon + section title."""
    def __init__(self, parent, icon="⬡", title="Section",
                 icon_bg=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        icon_bg = icon_bg or "#2a2000"

        ic = tk.Frame(self, bg=icon_bg, width=36, height=36)
        ic.pack(side="left", padx=(0, Palette.PAD_SM))
        ic.pack_propagate(False)
        tk.Label(ic, text=icon,
                 font=Palette.bold(14),
                 fg=Palette.PRIMARY,
                 bg=icon_bg).place(relx=.5, rely=.5, anchor="center")

        tk.Label(self, text=title,
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=bg).pack(side="left")


class FieldLabel(tk.Label):
    """Small-caps field label."""
    def __init__(self, parent, text, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, text=text.upper(),
                         font=Palette.bold(Palette.MICRO),
                         fg=Palette.ON_SURFACE_VAR,
                         bg=bg, anchor="w", **kw)


class UserProfileCard(tk.Frame):
    """Left card — avatar, update photo, name/badge/clearance."""
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=self._bg,
                       padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        pad.pack(fill="both", expand=True)

        # section header
        SectionHeader(pad, icon="👤", title="User Profile",
                      bg=self._bg, icon_bg="#252010").pack(
                          anchor="w", pady=(0, Palette.PAD_LG))

        # avatar circle
        av_frame = tk.Frame(pad, bg=self._bg)
        av_frame.pack(anchor="center")

        av = tk.Canvas(av_frame, width=80, height=80,
                       bg=self._bg, highlightthickness=2,
                       highlightbackground=Palette.PRIMARY)
        av.pack()
        av.create_oval(0, 0, 80, 80,
                       fill=Palette.SURFACE_HIGHEST, outline="")
        av.create_text(40, 40, text="ET",
                       font=Palette.bold(22),
                       fill=Palette.PRIMARY)

        tk.Label(av_frame, text="UPDATE PHOTO",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.PRIMARY,
                 bg=self._bg, cursor="hand2").pack(
                     pady=(Palette.PAD_SM, Palette.PAD_LG))

        # full name
        FieldLabel(pad, "Full Name", bg=self._bg).pack(
            fill="x", pady=(0, Palette.PAD_XS))
        self._name = StyledEntry(pad, value="Elias Thorne",
                                 bg=Palette.SURFACE_HIGH)
        self._name.pack(fill="x", pady=(0, Palette.PAD_MD))

        # badge + clearance row
        row = tk.Frame(pad, bg=self._bg)
        row.pack(fill="x")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        left = tk.Frame(row, bg=self._bg)
        left.grid(row=0, column=0, sticky="ew",
                  padx=(0, Palette.PAD_SM))
        FieldLabel(left, "Badge ID", bg=self._bg).pack(
            fill="x", pady=(0, Palette.PAD_XS))
        self._badge = StyledEntry(left, value="SF-9921-X",
                                  bg=Palette.SURFACE_HIGH)
        self._badge.pack(fill="x")

        right = tk.Frame(row, bg=self._bg)
        right.grid(row=0, column=1, sticky="ew")
        FieldLabel(right, "Clearance", bg=self._bg).pack(
            fill="x", pady=(0, Palette.PAD_XS))

        # clearance badge + dot
        cl_row = tk.Frame(right, bg=Palette.SURFACE_HIGH,
                          highlightbackground=Palette.OUTLINE,
                          highlightthickness=1)
        cl_row.pack(fill="x")
        tk.Label(cl_row, text="Lvl 4",
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_HIGH).pack(
                     side="left", padx=10, pady=8)
        tk.Label(cl_row, text="●",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.SUCCESS,
                 bg=Palette.SURFACE_HIGH).pack(side="right", padx=8)

        tk.Frame(pad, height=Palette.PAD_LG,
                 bg=self._bg).pack()


class SecurityProtocolCard(tk.Frame):
    """Right card — MFA toggle, API key, session timeout, regen."""
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._mfa = tk.BooleanVar(value=True)
        self._api_visible = False
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=self._bg,
                       padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        pad.pack(fill="both", expand=True)

        SectionHeader(pad, icon="🛡", title="Security Protocol",
                      bg=self._bg, icon_bg="#1a2010").pack(
                          anchor="w", pady=(0, Palette.PAD_LG))

        # MFA toggle row
        mfa_row = tk.Frame(pad, bg=self._bg)
        mfa_row.pack(fill="x", pady=(0, Palette.PAD_LG))

        mfa_text = tk.Frame(mfa_row, bg=self._bg)
        mfa_text.pack(side="left", fill="x", expand=True)
        tk.Label(mfa_text, text="Multi-Factor Authentication",
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack(anchor="w")
        tk.Label(mfa_text,
                 text="Require biometric confirmation for vault access.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg).pack(anchor="w")

        ToggleSwitch(mfa_row, self._mfa, bg=self._bg).pack(
            side="right", anchor="center")

        # two-col: API key | session timeout
        cols = tk.Frame(pad, bg=self._bg)
        cols.pack(fill="x", pady=(0, Palette.PAD_LG))
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=2)

        # API key
        api_col = tk.Frame(cols, bg=self._bg)
        api_col.grid(row=0, column=0, sticky="ew",
                     padx=(0, Palette.PAD_MD))

        api_hdr = tk.Frame(api_col, bg=self._bg)
        api_hdr.pack(fill="x", pady=(0, Palette.PAD_XS))
        FieldLabel(api_hdr, "API Governance Key",
                   bg=self._bg).pack(side="left")

        show_btn = tk.Label(api_hdr, text="👁  SHOW",
                            font=Palette.bold(Palette.MICRO),
                            fg=Palette.PRIMARY,
                            bg=self._bg, cursor="hand2")
        show_btn.pack(side="right")

        self._api_entry = StyledEntry(
            api_col, value="●"*22,
            show="", bg=Palette.SURFACE_HIGH)
        self._api_entry.pack(fill="x")
        # make it look masked by setting fg to dots
        self._api_entry._entry.config(fg=Palette.ON_SURFACE_VAR)

        # copy button next to entry
        copy_btn = tk.Frame(api_col, bg=self._bg)
        copy_btn.pack(anchor="e", pady=(Palette.PAD_XS, 0))
        copy_lbl = tk.Label(copy_btn, text="⧉",
                            font=Palette.bold(Palette.TITLE_MD),
                            fg=Palette.ON_SURFACE_VAR,
                            bg=Palette.SURFACE_HIGH,
                            cursor="hand2", padx=6, pady=4)
        copy_lbl.pack()
        copy_lbl.bind("<Button-1>", lambda e: self._copy_key())

        show_btn.bind("<Button-1>", lambda e: self._toggle_key(show_btn))

        # session timeout
        sess_col = tk.Frame(cols, bg=self._bg)
        sess_col.grid(row=0, column=1, sticky="ew")
        FieldLabel(sess_col, "Session Timeout",
                   bg=self._bg).pack(fill="x",
                                      pady=(0, Palette.PAD_XS))
        StyledDropdown(sess_col,
                       ["15 Minutes", "30 Minutes",
                        "1 Hour", "4 Hours", "Never"],
                       default="30 Minutes",
                       bg=Palette.SURFACE_HIGH).pack(fill="x")

        # regen button
        GoldButton(pad, text="REGENERATE CREDENTIALS",
                   style="outline",
                   command=self._regen).pack(fill="x", ipady=6)

    def _toggle_key(self, btn):
        self._api_visible = not self._api_visible
        if self._api_visible:
            self._api_entry._entry.config(
                fg=Palette.ON_SURFACE)
            self._api_entry.set("sk-xai-9f3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c")
            btn.config(text="👁  HIDE")
        else:
            self._api_entry._entry.config(
                fg=Palette.ON_SURFACE_VAR)
            self._api_entry.set("●"*22)
            btn.config(text="👁  SHOW")

    def _copy_key(self):
        self.clipboard_clear()
        self.clipboard_append("sk-xai-9f3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c")
        messagebox.showinfo("Copied", "API key copied to clipboard.")

    def _regen(self):
        messagebox.askquestion(
            "Regenerate Credentials",
            "This will invalidate your current API key.\nProceed?"
        )


class GoldSlider(tk.Canvas):
    """Custom gold slider — draggable thumb on a track."""
    HEIGHT = 8

    def __init__(self, parent, from_=0, to=100, value=82,
                 on_change=None, bg=None, **kw):
        bg = bg or Palette.SURFACE_CONTAINER
        super().__init__(parent, height=28,
                         bg=bg, highlightthickness=0, **kw)
        self._from   = from_
        self._to     = to
        self._val    = value
        self._on_change = on_change
        self._dragging  = False
        self.bind("<Configure>",      self._draw)
        self.bind("<Button-1>",       self._on_click)
        self.bind("<B1-Motion>",      self._on_drag)
        self.bind("<ButtonRelease-1>",lambda e: setattr(self, "_dragging", False))

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        pad = 10
        ty  = h // 2
        tw  = w - 2*pad
        pct = (self._val - self._from) / max(self._to - self._from, 1)
        fx  = pad + int(pct * tw)

        # track background
        self.create_rectangle(pad, ty-self.HEIGHT//2,
                              w-pad, ty+self.HEIGHT//2,
                              fill=Palette.SURFACE_HIGHEST, outline="")

        # filled portion — gradient
        c0, c1 = (0xf2,0xca,0x50), (0xd4,0xaf,0x37)
        for i in range(pad, fx):
            t   = (i-pad)/max(tw, 1)
            col = "#{:02x}{:02x}{:02x}".format(
                int(c0[0]+(c1[0]-c0[0])*t),
                int(c0[1]+(c1[1]-c0[1])*t),
                int(c0[2]+(c1[2]-c0[2])*t))
            self.create_line(i, ty-self.HEIGHT//2,
                             i, ty+self.HEIGHT//2, fill=col, width=1)

        # thumb
        r = 9
        self.create_oval(fx-r, ty-r, fx+r, ty+r,
                         fill=Palette.PRIMARY, outline=Palette.PRIMARY_DIM,
                         width=2)
        self.create_oval(fx-4, ty-4, fx+4, ty+4,
                         fill=Palette.ON_PRIMARY, outline="")

    def _on_click(self, e):
        self._dragging = True
        self._update_from_x(e.x)

    def _on_drag(self, e):
        if self._dragging:
            self._update_from_x(e.x)

    def _update_from_x(self, x):
        w   = self.winfo_width()
        pad = 10
        pct = max(0., min(1., (x-pad)/(w-2*pad)))
        self._val = self._from + pct*(self._to-self._from)
        self._draw()
        if self._on_change:
            self._on_change(int(self._val))

    def get(self): return int(self._val)


class NeuralEngineCard(tk.Frame):
    """Detection sensitivity slider + log retention dropdown."""
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._sens_val = tk.IntVar(value=82)
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=self._bg,
                       padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        pad.pack(fill="both", expand=True)

        SectionHeader(pad, icon="⬡", title="Neural Engine Configuration",
                      bg=self._bg, icon_bg="#201a00").pack(
                          anchor="w", pady=(0, Palette.PAD_LG))

        # two-col
        cols = tk.Frame(pad, bg=self._bg)
        cols.pack(fill="x")
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=2)

        # left: sensitivity
        left = tk.Frame(cols, bg=self._bg)
        left.grid(row=0, column=0, sticky="nsew",
                  padx=(0, Palette.PAD_LG))

        # header row with live value
        sens_hdr = tk.Frame(left, bg=self._bg)
        sens_hdr.pack(fill="x", pady=(0, Palette.PAD_XS))
        tk.Label(sens_hdr, text="Detection Sensitivity",
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack(side="left")

        self._sens_label = tk.Label(sens_hdr, text="82% (High)",
                                    font=Palette.bold(Palette.LABEL),
                                    fg=Palette.PRIMARY,
                                    bg=self._bg)
        self._sens_label.pack(side="right")

        # slider
        self._slider = GoldSlider(left, from_=0, to=100, value=82,
                                  on_change=self._on_slider,
                                  bg=self._bg)
        self._slider.pack(fill="x", pady=(Palette.PAD_SM, Palette.PAD_MD))

        tk.Label(left,
                 text=("Adjusting the sensitivity threshold impacts the neural "
                       "engine's anomaly detection rate and false-positive filtering."),
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg, wraplength=300, justify="left").pack(anchor="w")

        # right: log retention
        right = tk.Frame(cols, bg=self._bg)
        right.grid(row=0, column=1, sticky="nsew")

        FieldLabel(right, "Log Retention Period",
                   bg=self._bg).pack(fill="x",
                                      pady=(0, Palette.PAD_XS))
        StyledDropdown(right,
                       ["30 Days", "90 Days", "6 Months",
                        "1 Year (Archival)", "Indefinite"],
                       default="1 Year (Archival)",
                       bg=Palette.SURFACE_HIGH).pack(fill="x")

        tk.Label(right,
                 text=("Note: Extending retention beyond 1 year\n"
                       "increases vault storage overhead."),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.WARNING,
                 bg=self._bg,
                 justify="left").pack(anchor="w",
                                      pady=(Palette.PAD_MD, 0))

    def _on_slider(self, val):
        if val >= 80:
            label = f"{val}% (High)"
        elif val >= 50:
            label = f"{val}% (Medium)"
        else:
            label = f"{val}% (Low)"
        self._sens_label.config(text=label)


class AlertToggleRow(tk.Frame):
    """Single alerting toggle: icon + title + desc + switch."""
    def __init__(self, parent, title, description,
                 default=True, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._var = tk.BooleanVar(value=default)
        self._build(title, description, bg)

    def _build(self, title, description, bg):
        # toggle
        ToggleSwitch(self, self._var, bg=bg).pack(
            side="left", padx=(0, Palette.PAD_MD))

        # text
        txt = tk.Frame(self, bg=bg)
        txt.pack(side="left", fill="x", expand=True)
        tk.Label(txt, text=title,
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=bg).pack(anchor="w")
        tk.Label(txt, text=description,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, wraplength=200,
                 justify="left").pack(anchor="w")

    def get(self): return self._var.get()


class AlertingCard(tk.Frame):
    """Full-width alerting & reports card — 3 toggle columns."""
    ALERTS = [
        ("High-Threat Alerts",
         "Instant SMS and email for Priority 1 breaches.", True),
        ("System Health Monitor",
         "Status updates on neural engine latency and server uptime.", True),
        ("Daily Briefing Reports",
         "Automated PDF summaries of all investigative activity.", False),
    ]

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=self._bg,
                       padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        pad.pack(fill="both", expand=True)

        SectionHeader(pad, icon="🔔", title="Alerting & Reports",
                      bg=self._bg, icon_bg="#201500").pack(
                          anchor="w", pady=(0, Palette.PAD_LG))

        grid = tk.Frame(pad, bg=self._bg)
        grid.pack(fill="x")

        for i, (title, desc, default) in enumerate(self.ALERTS):
            grid.columnconfigure(i, weight=1)
            AlertToggleRow(grid, title, desc, default=default,
                           bg=self._bg).grid(
                               row=0, column=i, sticky="nsew",
                               padx=(0 if i == 0 else Palette.PAD_MD, 0))


class CommitBar(tk.Frame):
    """Bottom commit bar — note + large gold CTA."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=Palette.SURFACE_LOW,
                         height=72, **kw)
        self.pack_propagate(False)
        self._build()

    def _build(self):
        inner = tk.Frame(self, bg=Palette.SURFACE_LOW)
        inner.place(relx=.5, rely=.5, anchor="center",
                    relwidth=.96)

        tk.Label(inner,
                 text=("Settings modifications are logged to the Sovereign Forensic "
                       "Audit Trail and associated with Investigator Badge SF-9921-X."),
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW,
                 wraplength=480, justify="center").pack(side="left",
                                                        fill="x",
                                                        expand=True)

        GoldButton(inner, text="COMMIT CONFIGURATIONS  →",
                   style="primary",
                   command=self._commit).pack(side="right",
                                              ipady=10, ipadx=20)

    def _commit(self):
        messagebox.showinfo("Committed",
                            "Configuration changes saved and logged to Audit Trail.")



class SideNav(tk.Frame):
    ITEMS  = [("Dashboard","▣"),("Evidence Vault","☐"),
               ("Upload Logs","↑"),("Settings","⚙"),("Audit Trail","≡")]
    BOTTOM = [("Logout","↩")]

    def __init__(self, parent, active="Settings", on_navigate=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE_LOW,
                         width=Palette.NAV_W, **kw)
        self.pack_propagate(False)
        self._active=active; self._on_navigate=on_navigate
        self._build()

    def _build(self):
        # brand
        brand = tk.Frame(self, bg=Palette.SURFACE_LOW,
                         padx=Palette.PAD_MD, pady=Palette.PAD_LG)
        brand.pack(fill="x")
        tk.Label(brand, text="SOVEREIGN SHIELD",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_LOW).pack(anchor="w")
        tk.Label(brand,
                 text="FORENSIC AUTHORITY  •  LEVEL 4 ACCESS",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW).pack(anchor="w")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x",
                                                           pady=(0, Palette.PAD_SM))

        wrap = tk.Frame(self, bg=Palette.SURFACE_LOW)
        wrap.pack(fill="x", padx=8)
        for label, icon in self.ITEMS:
            self._item(wrap, label, icon)

        bot = tk.Frame(self, bg=Palette.SURFACE_LOW)
        bot.pack(side="bottom", fill="x", padx=8, pady=12)
        tk.Frame(bot, height=1, bg=Palette.OUTLINE).pack(fill="x",
                                                           pady=(0,8))

        # CTA
        cta = tk.Frame(self, bg=Palette.SURFACE_LOW, padx=8)
        cta.pack(side="bottom", fill="x", pady=(0, Palette.PAD_SM))
        GoldButton(cta, text="+ New Investigation",
                   style="primary").pack(fill="x", ipady=8)

        for label, icon in self.BOTTOM:
            self._item(bot, label, icon)

    def _item(self, parent, label, icon):
        active = label == self._active
        bg = Palette.SURFACE_HIGH if active else Palette.SURFACE_LOW
        fg = Palette.PRIMARY if active else Palette.ON_SURFACE_VAR
        row = tk.Frame(parent, bg=bg, cursor="hand2", height=38)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        if active:
            tk.Frame(row, bg=Palette.PRIMARY, width=3).pack(side="left", fill="y")
        tk.Label(row, text=icon, font=Palette.font(Palette.LABEL),
                 fg=fg, bg=bg, width=3).pack(
                     side="left", padx=(8 if not active else 5, 4))
        tk.Label(row, text=label,
                 font=Palette.bold(Palette.LABEL) if active else Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE if active else fg,
                 bg=bg).pack(side="left")
        for w in [row]+list(row.winfo_children()):
            w.bind("<Button-1>", lambda e, l=label: self._click(l))
        if not active:
            for w in [row]+list(row.winfo_children()):
                w.bind("<Enter>", lambda e, r=row: r.config(bg=Palette.SURFACE_HIGH))
                w.bind("<Leave>", lambda e, r=row: r.config(bg=Palette.SURFACE_LOW))

    def _click(self, label):
        if self._on_navigate: self._on_navigate(label)

    def set_active(self, label):
        self._active = label
        for w in self.winfo_children(): w.destroy()
        self._build()


# ======================================================================
#  TOP BAR
# ======================================================================
class TopBar(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=Palette.SURFACE_LOW,
                         height=Palette.TOPBAR_H, **kw)
        self.pack_propagate(False)
        self._build()

    def _build(self):
        tk.Label(self, text="SOVEREIGN FORENSIC",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_LOW).pack(side="left",
                                              padx=Palette.PAD_LG)
        tk.Label(self, text="System Configuration",
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW).pack(side="left",
                                              padx=(Palette.PAD_SM, 0))

        right = tk.Frame(self, bg=Palette.SURFACE_LOW)
        right.pack(side="right", padx=Palette.PAD_LG)

        # agent info
        info = tk.Frame(right, bg=Palette.SURFACE_LOW)
        info.pack(side="right", padx=(Palette.PAD_SM, 0))
        tk.Label(info, text="Investigator Thorne",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_LOW).pack(anchor="e")
        tk.Label(info, text="LVL 4 ADMIN",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW).pack(anchor="e")

        av = tk.Canvas(right, width=32, height=32,
                       bg=Palette.SURFACE_LOW, highlightthickness=0)
        av.pack(side="right", padx=(Palette.PAD_MD, 0))
        av.bind("<Configure>", lambda e: (
            av.delete("all"),
            av.create_oval(0,0,32,32,fill=Palette.SURFACE_HIGHEST,
                           outline=Palette.PRIMARY, width=1),
            av.create_text(16,16,text="IT",font=Palette.bold(Palette.MICRO),
                           fill=Palette.PRIMARY)
        ))

        tk.Label(right, text="?",
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW, cursor="hand2").pack(
                     side="right", padx=(0, Palette.PAD_SM))
        tk.Label(right, text="🔔",
                 font=Palette.font(Palette.TITLE_MD),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW, cursor="hand2").pack(
                     side="right", padx=(0, Palette.PAD_SM))

        tk.Frame(self, height=1, bg=Palette.OUTLINE).place(
            relx=0, rely=1.0, relwidth=1.0, anchor="sw")


# ======================================================================
#  SETTINGS PAGE
# ======================================================================
class SettingsPage(tk.Frame):
    def __init__(self, parent,user=None, on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._build()

    def _build(self):
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        # scrollable body
        scroll_host = tk.Frame(self, bg=Palette.SURFACE)
        scroll_host.grid(row=0, column=0, sticky="nsew")

        canvas = tk.Canvas(scroll_host, bg=Palette.SURFACE,
                           highlightthickness=0)
        scroll = tk.Scrollbar(scroll_host, orient="vertical",
                              command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=Palette.SURFACE)
        win   = canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1*(e.delta/120)), "units"))

        self._populate(inner)

        # commit bar
        CommitBar(self).grid(row=1, column=0, sticky="ew")

    def _populate(self, p):
        hdr = tk.Frame(p, bg=Palette.SURFACE)
        hdr.pack(fill="x", padx=Palette.PAD_XL,
                 pady=(Palette.PAD_LG, 0))

        title_block = tk.Frame(hdr, bg=Palette.SURFACE)
        title_block.pack(side="left")
        tk.Label(title_block, text="System Configuration",
                 font=(Palette._FONT[0], Palette.DISPLAY, "bold"),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(anchor="w")
        tk.Label(title_block,
                 text="Manage your investigative environment and security protocols.",
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w", pady=(4,0))

        # Discard + Save
        btn_row = tk.Frame(hdr, bg=Palette.SURFACE)
        btn_row.pack(side="right", anchor="center")
        GoldButton(btn_row, text="Discard",
                   style="outline").pack(side="left", ipady=6,
                                         ipadx=14,
                                         padx=(0, Palette.PAD_SM))
        GoldButton(btn_row, text="Save Changes",
                   style="primary",
                   command=self._save).pack(side="left", ipady=6,
                                             ipadx=14)

        tk.Frame(p, height=Palette.PAD_LG,
                 bg=Palette.SURFACE).pack()

        # ── row 1: user profile | security protocol ───────────────────
        row1 = tk.Frame(p, bg=Palette.SURFACE)
        row1.pack(fill="x", padx=Palette.PAD_XL)
        row1.columnconfigure(0, weight=1)
        row1.columnconfigure(1, weight=2)

        UserProfileCard(row1, bg=Palette.SURFACE_CONTAINER).grid(
            row=0, column=0, sticky="nsew",
            padx=(0, Palette.PAD_MD))

        SecurityProtocolCard(row1, bg=Palette.SURFACE_CONTAINER).grid(
            row=0, column=1, sticky="nsew")

        tk.Frame(p, height=Palette.PAD_MD,
                 bg=Palette.SURFACE).pack()

        # ── row 2: neural engine ──────────────────────────────────────
        NeuralEngineCard(p, bg=Palette.SURFACE_CONTAINER).pack(
            fill="x", padx=Palette.PAD_XL)

        tk.Frame(p, height=Palette.PAD_MD,
                 bg=Palette.SURFACE).pack()

        # ── row 3: alerting ───────────────────────────────────────────
        AlertingCard(p, bg=Palette.SURFACE_CONTAINER).pack(
            fill="x", padx=Palette.PAD_XL)

        tk.Frame(p, height=Palette.PAD_XL,
                 bg=Palette.SURFACE).pack()

    def _save(self):
        messagebox.showinfo("Saved", "Settings saved successfully.")


