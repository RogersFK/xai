from colors import Palette
import tkinter as tk

class GoldButton(tk.Canvas):
    BTN_H = 20

    def __init__(self, parent, text="", command=None, style="primary", icon="", **kw):
        super().__init__(
            parent,
            height=self.BTN_H,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            **kw
        )

        self._text    = text
        self._icon    = icon
        self._command = command
        self._style   = style
        self._hovered = False
        self._pressed = False
        self._disabled = False          # ← new

        self.bind("<Configure>",       self._redraw)
        self.bind("<Enter>",           lambda e: self._set(hover=True))
        self.bind("<Leave>",           lambda e: self._set(hover=False))
        self.bind("<Button-1>",        lambda e: self._set(pressed=True))
        self.bind("<ButtonRelease-1>", self._on_release)

    def config(self, state=None, text=None, **kw):
        """Mimics tk widget .config() so _set_busy() works unchanged."""
        if state is not None:
            self._disabled = (state == "disabled")
            self.configure(cursor="arrow" if self._disabled else "hand2")
        if text is not None:
            self._text = text
        if kw:
            super().configure(**kw)     # pass anything else to Canvas
        self._redraw()

    configure = config                  

    def _set(self, hover=None, pressed=None):
        if self._disabled:             
            return
        if hover   is not None: self._hovered = hover
        if pressed is not None: self._pressed = pressed
        self._redraw()

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1,
            x2,   y1, x2,   y1+r,
            x2,   y2-r, x2, y2,
            x2-r, y2, x1+r, y2,
            x1,   y2, x1,   y2-r,
            x1,   y1+r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        r = min(Palette.RADIUS, h // 2)

        # disabled washes out the gradient
        if self._disabled:
            c0, c1 = (100, 90, 50), (90, 80, 45)
        elif self._pressed:
            c0, c1 = (200, 160, 40), (176, 144, 32)
        elif self._hovered:
            c0, c1 = (255, 216, 96), (224, 188, 64)
        else:
            c0, c1 = (242, 202, 80), (212, 175, 55)

        for i in range(w):
            t = i / max(w - 1, 1)
            col = "#{:02x}{:02x}{:02x}".format(
                int(c0[0] + (c1[0] - c0[0]) * t),
                int(c0[1] + (c1[1] - c0[1]) * t),
                int(c0[2] + (c1[2] - c0[2]) * t),
            )
            self.create_line(i, 0, i, h, fill=col)

        self._rounded_rect(1, 1, w-1, h-1, r,
                           outline=Palette.OUTLINE_VAR, width=1, fill="")

        text_color = Palette.ON_SURFACE_VAR if self._disabled else Palette.ON_PRIMARY
        self.create_text(
            w // 2, h // 2,
            text=f"{self._text}   →",
            font=Palette.font(Palette.TITLE_MD, "bold"),
            fill=text_color
        )

    def _on_release(self, event=None):
        if self._disabled:
            return
        self._pressed = False
        self._redraw()
        if self._command:
            self._command()



class _ToggleSwitch(tk.Frame):
    TW, TH, KD = 44, 24, 18

    def __init__(self, parent, variable: tk.BooleanVar,
                 text: str = "", bg: str = None):
        bg = bg or Palette.SURFACE_CONTAINER
        super().__init__(parent, bg=bg)
        self._var = variable

        cv = tk.Canvas(self, width=self.TW, height=self.TH,
                       bg=bg, highlightthickness=0, cursor="hand2")
        cv.pack(side="left", padx=(0, 8))
        cv.bind("<Button-1>", lambda e: variable.set(not variable.get()))
        self._cv = cv

        tk.Label(self, text=text,
                 font=Palette.font(Palette.BODY_MD),
                 fg=Palette.ON_SURFACE, bg=bg).pack(side="left")

        self._draw()
        variable.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        c  = self._cv
        on = self._var.get()
        c.delete("all")
        w, h, r = self.TW, self.TH, self.TH // 2
        trk = Palette.PRIMARY_DIM if on else Palette.SURFACE_HIGHEST
        c.create_oval(0, 0, h, h, fill=trk, outline="")
        c.create_oval(w-h, 0, w, h, fill=trk, outline="")
        c.create_rectangle(r, 0, w-r, h, fill=trk, outline="")
        pad  = (h - self.KD) // 2
        x    = w - self.KD - pad if on else pad
        kfil = Palette.ON_PRIMARY if on else Palette.ON_SURFACE_VAR
        c.create_oval(x, pad, x+self.KD, pad+self.KD,
                      fill=kfil, outline="")


class PlaceholderEntry(tk.Frame):
    def __init__(self, parent, placeholder: str = "", show: str = "",
                 icon: str = "o", bg: str = None, **kw):
        bg = bg or Palette.SURFACE_HIGHEST
        super().__init__(parent, bg=bg,
                         highlightbackground=Palette.OUTLINE_BRIGHT,   # was SURFACE_HIGHEST — invisible
                         highlightcolor=Palette.PRIMARY,
                         highlightthickness=1, bd=0)

        self._show        = show
        self._placeholder = placeholder
        self._is_empty    = True
        self._eye_open    = False

        self._icon_lbl = tk.Label(self, text=icon,
                                  font=Palette.font(Palette.BODY_MD),
                                  fg=Palette.ON_SURFACE_VAR, bg=bg)   # was OUTLINE — invisible
        self._icon_lbl.pack(side="left", padx=(10, 0))

        self._entry = tk.Entry(
            self,
            font=Palette.font(Palette.BODY_MD),
            fg=Palette.ON_SURFACE_VAR,                                 # was OUTLINE — invisible
            bg=bg, bd=0,
            insertbackground=Palette.PRIMARY,
            selectbackground=Palette.PRIMARY_DIM,
            selectforeground=Palette.ON_PRIMARY,
            relief="flat",
            show=""
        )
        self._entry.pack(side="left", fill="both", expand=True,
                         padx=8, pady=10)                              # pady gives the entry height

        self._eye_btn = None
        if show:
            self._eye_btn = tk.Label(
                self, text="👁",
                font=Palette.font(Palette.BODY_MD),
                fg=Palette.ON_SURFACE_VAR, bg=bg, cursor="hand2"
            )
            self._eye_btn.pack(side="right", padx=(0, 10))
            self._eye_btn.bind("<Button-1>", self._toggle_reveal)

        self._show_placeholder()
        self._entry.bind("<FocusIn>",  self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<FocusIn>",
                         lambda e: self.config(
                             highlightbackground=Palette.PRIMARY), add="+")
        self._entry.bind("<FocusOut>",
                         lambda e: self.config(
                             highlightbackground=Palette.OUTLINE_BRIGHT), add="+")  # restore visible border

    # --- internal helpers unchanged except color fix ---
    def _show_placeholder(self):
        self._entry.config(show="")
        self._entry.delete(0, "end")
        self._entry.insert(0, self._placeholder)
        self._entry.config(fg=Palette.ON_SURFACE_VAR)                 # was OUTLINE — invisible
        self._is_empty = True

    def _on_focus_in(self, _=None):
        if self._is_empty:
            self._entry.delete(0, "end")
            self._entry.config(
                fg=Palette.ON_SURFACE,
                show="" if (self._eye_open or not self._show) else self._show
            )
            self._is_empty = False

    def _on_focus_out(self, _=None):
        if not self._entry.get():
            self._show_placeholder()

    def _toggle_reveal(self, _=None):
        self._eye_open = not self._eye_open
        if not self._is_empty:
            self._entry.config(show="" if self._eye_open else self._show)
        if self._eye_btn:
            self._eye_btn.config(
                fg=Palette.PRIMARY if self._eye_open else Palette.ON_SURFACE_VAR
            )

    def get(self) -> str:
        return "" if self._is_empty else self._entry.get()

    def bind_entry(self, sequence, func, add=""):
        """Expose inner entry binding (e.g. <Return>) to callers."""
        self._entry.bind(sequence, func, add=add)   


class ToggleSwitch(tk.Canvas):
    TW, TH, KD = 44, 24, 18

    def __init__(self, parent, variable: tk.BooleanVar,
                 on_change=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, width=self.TW, height=self.TH,
                         bg=bg, highlightthickness=0,
                         cursor="hand2", **kw)
        self._var = variable
        self._on_change = on_change
        self._draw()
        variable.trace_add("write", lambda *_: self._draw())
        self.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        self._var.set(not self._var.get())
        if self._on_change:
            self._on_change(self._var.get())

    def _draw(self):
        self.delete("all")
        on = self._var.get()
        w, h = self.TW, self.TH
        r    = h // 2
        trk  = Palette.PRIMARY_DIM if on else Palette.SURFACE_HIGHEST
        self.create_oval(0, 0, h, h, fill=trk, outline="")
        self.create_oval(w-h, 0, w, h, fill=trk, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=trk, outline="")
        pad  = (h - self.KD) // 2
        x    = w - self.KD - pad if on else pad
        kfil = Palette.ON_PRIMARY if on else Palette.ON_SURFACE_VAR
        self.create_oval(x, pad, x+self.KD, pad+self.KD,
                         fill=kfil, outline="")


class Components:
    
    @staticmethod
    def label(parent, text: str, size: int = None, weight: str = "normal",
              color: str = None, bg: str = None, **kw) -> tk.Label:
        return tk.Label(
            parent, text=text,
            font=Palette.font(size or Palette.BODY_MD, weight),
            fg=color or Palette.ON_SURFACE,
            bg=bg or Palette.SURFACE_CONTAINER,
            **kw
        )

    @staticmethod
    def field_label(parent, text: str, bg: str = None, fg: str = None) -> tk.Label:
        return tk.Label(
            parent, text=text.upper(),
            font=Palette.font(Palette.LABEL_SM, "bold"),
            fg= fg or Palette.OUTLINE,
            bg=bg or Palette.SURFACE_CONTAINER,
            anchor="w"
        )

    @staticmethod
    def entry(parent, placeholder: str = "", show: str = "",
              icon: str = "o", bg: str = None) -> PlaceholderEntry:
        return PlaceholderEntry(
            parent, placeholder=placeholder,
            show=show, icon=icon,
            bg=bg or Palette.SURFACE_HIGHEST
        )

    @staticmethod
    def primary_button(parent, text: str, command=None) -> GoldButton:
        return GoldButton(parent, text=text, command=command)

    @staticmethod
    def ghost_button(parent, text: str, command=None,
                     color: str = None, bg: str = None) -> tk.Label:
        color = color or Palette.PRIMARY
        bg    = bg    or Palette.SURFACE_CONTAINER
        lbl   = tk.Label(parent, text=text,
                         font=Palette.font(Palette.LABEL_SM),
                         fg=color, bg=bg, cursor="hand2")
        if command:
            lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.config(fg=Palette.ON_SURFACE))
        lbl.bind("<Leave>", lambda e: lbl.config(fg=color))
        return lbl

    @staticmethod
    def toggle(parent, variable: tk.BooleanVar,
               text: str, bg: str = None) -> _ToggleSwitch:
        return _ToggleSwitch(parent, variable=variable,
                             text=text, bg=bg or Palette.SURFACE_CONTAINER)

    @staticmethod
    def spacer(parent, h: int = 8, bg: str = None) -> tk.Frame:
        return tk.Frame(parent, height=h,
                        bg=bg or Palette.SURFACE_CONTAINER)

    @staticmethod
    def status_item(parent, icon: str, text: str,
                    bg: str = None) -> tk.Frame:
        bg  = bg or Palette.SURFACE_LOWEST
        frm = tk.Frame(parent, bg=bg)
        tk.Label(frm, text=icon,
                 font=Palette.font(Palette.LABEL_SM),
                 fg=Palette.OUTLINE, bg=bg).pack(side="left", padx=(0, 4))
        tk.Label(frm, text=text.upper(),
                 font=Palette.font(Palette.LABEL_SM),
                 fg=Palette.OUTLINE, bg=bg).pack(side="left")
        return frm

        
class SHAPBar(tk.Frame):
    """
    Single SHAP feature bar row.
    label: str, value: float (-1 to 1), max_val: float
    """
    BAR_H = 22

    def __init__(self, parent, label: str, value: float,
                 max_val: float = 0.5, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)

        sign    = "+" if value >= 0 else ""
        val_str = f"{sign}{value:.3f}"
        color   = Palette.PRIMARY if value >= 0 else Palette.SURFACE_HIGHEST

        # label row
        hdr = tk.Frame(self, bg=bg)
        hdr.pack(fill="x")
        tk.Label(hdr, text=label,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(side="left")
        tk.Label(hdr, text=val_str,
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY if value >= 0 else Palette.ON_SURFACE_VAR,
                 bg=bg).pack(side="right")

        # bar track
        track = tk.Frame(self, bg=Palette.SURFACE_HIGH,
                         height=self.BAR_H)
        track.pack(fill="x", pady=(4, 0))
        track.pack_propagate(False)

        fill_pct = min(abs(value) / max(max_val, 0.001), 1.0)

        bar = tk.Frame(track, bg=color, height=self.BAR_H)
        bar.place(x=0, y=0, relwidth=fill_pct, height=self.BAR_H)

        tk.Frame(self, height=Palette.PAD_SM, bg=bg).pack()


class AnimatedProgressBar(tk.Canvas):
    """Animated gold progress bar with shimmer."""
    HEIGHT = 10

    def __init__(self, parent, value: float = 0.74,
                 bg: str = None, **kw):
        bg = bg or Palette.SURFACE_CONTAINER
        super().__init__(parent, height=self.HEIGHT,
                         bg=bg, highlightthickness=0, bd=0, **kw)
        self._value   = value
        self._shimmer = 0.0
        self._running = True
        self.bind("<Configure>", self._redraw)
        self._animate()

    def _animate(self):
        if not self._running:
            return
        self._shimmer = (self._shimmer + 0.03) % 1.0
        self._redraw()
        self.after(40, self._animate)

    def _redraw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2:
            return
        r   = h // 2
        bw  = int(w * self._value)

        # track
        self.create_rectangle(0, 0, w, h,
                              fill=Palette.SURFACE_HIGH, outline="")

        if bw > 0:
            # gradient fill
            c0 = (0xf2, 0xca, 0x50)
            c1 = (0xd4, 0xaf, 0x37)
            for i in range(bw):
                t   = i / max(bw-1, 1)
                col = "#{:02x}{:02x}{:02x}".format(
                    int(c0[0]+(c1[0]-c0[0])*t),
                    int(c0[1]+(c1[1]-c0[1])*t),
                    int(c0[2]+(c1[2]-c0[2])*t),
                )
                self.create_line(i, 0, i, h, fill=col, width=1)

            # shimmer overlay
            sx = int((self._shimmer * (w + 60)) - 30)
            self.create_rectangle(sx, 0, sx+30, h,
                                  fill="#ffffff", stipple="gray25",
                                  outline="")

        # rounded end cap
        if bw >= r:
            self.create_oval(bw-r, 0, bw+r, h,
                             fill=Palette.PRIMARY_DIM, outline="")

    def stop(self):
        self._running = False

    def set_value(self, v: float):
        self._value = max(0.0, min(1.0, v))


class ThreatRow(tk.Frame):
    """
    Single row in the flagged events table.
    Expandable to show LIME explanation panel.
    """
    STATUS_COLORS = {
        "CRITICAL": ("#e05252", "#ffffff"),
        "REVIEW":   ("#4a4030", Palette.WARNING),
        "BENIGN":   ("#2a2a2a", Palette.ON_SURFACE_VAR),
    }

    def __init__(self, parent, timestamp: str, event_id: str,
                 score: int, status: str,
                 lime_text: str = None,
                 lime_pos: str = None,
                 lime_neg: str = None,
                 **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg       = bg
        self._expanded = False
        self._lime     = lime_text
        self._lime_pos = lime_pos
        self._lime_neg = lime_neg

        self._detail = None
        self._build(timestamp, event_id, score, status)

    def _build(self, timestamp, event_id, score, status):
        row = tk.Frame(self, bg=self._bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_LG)

        # timestamp
        tk.Label(row, text=timestamp,
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg, width=20,
                 anchor="w").pack(side="left")

        # event id
        tk.Label(row, text=event_id,
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg, width=14,
                 anchor="w").pack(side="left", padx=Palette.PAD_MD)

        # threat score bar + number
        score_frame = tk.Frame(row, bg=self._bg)
        score_frame.pack(side="left", padx=Palette.PAD_MD)
        bar_color = (Palette.ERROR   if score >= 80 else
                     Palette.WARNING if score >= 40 else
                     Palette.BENIGN)
        bar_w = max(4, int(80 * score / 100))
        tk.Frame(score_frame, bg=bar_color,
                 width=bar_w, height=4).pack(pady=(10, 0))
        tk.Label(score_frame, text=f"{score}%",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack()

        # status badge
        sbg, sfg = self.STATUS_COLORS.get(status,
                                           (Palette.SURFACE_HIGH,
                                            Palette.ON_SURFACE_VAR))
        tk.Label(row, text=status,
                 font=Palette.bold(Palette.MICRO),
                 fg=sfg, bg=sbg,
                 padx=8, pady=3).pack(side="left",
                                      padx=Palette.PAD_LG)

        # expand chevron
        if self._lime:
            self._chev = tk.Label(row, text="⌄",
                                  font=Palette.font(Palette.TITLE_LG),
                                  fg=Palette.ON_SURFACE_VAR,
                                  bg=self._bg, cursor="hand2")
            self._chev.pack(side="right", padx=Palette.PAD_MD)
            self._chev.bind("<Button-1>", self._toggle)
            row.bind("<Button-1>", self._toggle)

        # separator
        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                          padx=Palette.PAD_LG)

    def _toggle(self, _=None):
        if self._expanded:
            if self._detail:
                self._detail.destroy()
                self._detail = None
            self._chev.config(text="⌄")
            self._expanded = False
        else:
            self._build_lime()
            self._chev.config(text="⌃")
            self._expanded = True

    def _build_lime(self):
        self._detail = tk.Frame(self, bg=Palette.SURFACE_HIGH)
        self._detail.pack(fill="x", padx=Palette.PAD_LG,
                          pady=(0, Palette.PAD_SM))

        top = tk.Frame(self._detail, bg=Palette.SURFACE_HIGH)
        top.pack(fill="x", padx=Palette.PAD_MD, pady=(Palette.PAD_SM, 4))

        tk.Label(top, text="⚡  LIME LOCAL EXPLANATION",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH).pack(side="left")

        tk.Label(self._detail, text=self._lime,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGH,
                 wraplength=500, justify="left",
                 anchor="w").pack(fill="x",
                                  padx=Palette.PAD_MD,
                                  pady=(0, Palette.PAD_SM))

        bottom = tk.Frame(self._detail, bg=Palette.SURFACE_HIGH)
        bottom.pack(fill="x", padx=Palette.PAD_MD,
                    pady=(0, Palette.PAD_MD))

        pos_f = tk.Frame(bottom, bg=Palette.SURFACE_HIGHEST)
        pos_f.pack(side="left", fill="x", expand=True,
                   padx=(0, Palette.PAD_SM))
        tk.Label(pos_f, text="TOP POSITIVE (SUSPICIOUS)",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGHEST).pack(anchor="w",
                                                  padx=8, pady=(6,2))
        tk.Label(pos_f, text=self._lime_pos or "",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGHEST).pack(anchor="w",
                                                  padx=8, pady=(0,6))

        neg_f = tk.Frame(bottom, bg=Palette.SURFACE_HIGHEST)
        neg_f.pack(side="left", fill="x", expand=True)
        tk.Label(neg_f, text="TOP NEGATIVE (NORMAL)",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGHEST).pack(anchor="w",
                                                  padx=8, pady=(6,2))
        tk.Label(neg_f, text=self._lime_neg or "",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.SUCCESS,
                 bg=Palette.SURFACE_HIGHEST).pack(anchor="w",
                                                  padx=8, pady=(0,6))


class DropZone(tk.Frame):
    """Drag-and-drop evidence zone."""
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._build()

    def _build(self):
        tk.Label(self,
                 text="⬆",
                 font=Palette.font(32),
                 fg=Palette.SURFACE_HIGH,
                 bg=self._bg).pack(pady=(Palette.PAD_LG, 4))

        tk.Label(self, text="Drop Evidence Logs",
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack()

        tk.Label(self,
                 text="Supports .JSON, .CSV, and RAW Binary dumps",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg,
                 justify="center").pack(pady=(4, Palette.PAD_MD))

        btn_frame = tk.Frame(self, bg=Palette.SURFACE_HIGH,
                             padx=12, pady=6)
        btn_frame.pack()
        tk.Label(btn_frame, text="MAX FILE SIZE 2GB",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_HIGH).pack()

        tk.Frame(self, height=Palette.PAD_LG,
                 bg=self._bg).pack()


