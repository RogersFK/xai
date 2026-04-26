from colors import Palette
import tkinter as tk
import datetime
import random
from components import GoldButton


class StatCard(tk.Frame):
    def __init__(self, parent, icon="▣", badge="", badge_color=None,
                 value="0", label="", icon_color=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(icon, badge, badge_color, value, label, icon_color, bg)

    def _build(self, icon, badge, badge_color, value, label, icon_color, bg):
        top = tk.Frame(self, bg=bg)
        top.pack(fill="x", padx=Palette.PAD_LG, pady=(Palette.PAD_LG, 0))

        # icon circle
        ic = tk.Frame(top, bg=Palette.SURFACE_HIGH, width=40, height=40)
        ic.pack(side="left")
        ic.pack_propagate(False)
        tk.Label(ic, text=icon,
                 font=Palette.bold(16),
                 fg=icon_color or Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH).place(relx=.5, rely=.5,
                                                anchor="center")

        # badge chip
        if badge:
            chip = tk.Frame(top, bg=Palette.SURFACE_HIGH)
            chip.pack(side="right", anchor="n")
            chip_bg = badge_color or Palette.SURFACE_HIGHEST
            tk.Label(chip, text=badge,
                     font=Palette.bold(Palette.MICRO),
                     fg=chip_bg,
                     bg=bg).pack()

        # big value
        tk.Label(self, text=value,
                 font=(Palette._FONT[0], 32, "bold"),
                 fg=Palette.ON_SURFACE if badge_color != Palette.ERROR
                    else Palette.ERROR,
                 bg=bg).pack(anchor="w",
                             padx=Palette.PAD_LG,
                             pady=(Palette.PAD_SM, 0))

        # label
        tk.Label(self, text=label.upper(),
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(anchor="w", padx=Palette.PAD_LG,
                             pady=(0, Palette.PAD_LG))

class UserAvatar(tk.Canvas):
    def __init__(self, parent, initials="??", bg_color=None, **kw):
        size = kw.pop("size", 28)
        super().__init__(parent, width=size, height=size,
                         highlightthickness=0, bd=0, **kw)
        try:
            self.config(bg=parent.cget("bg"))
        except Exception:
            self.config(bg=Palette.SURFACE_CONTAINER)
        self._size     = size
        self._initials = initials
        self._color    = bg_color or Palette.SURFACE_HIGHEST
        self.bind("<Configure>", self._draw)
        self.after(10, self._draw)

    def _draw(self, _=None):
        self.delete("all")
        s = self._size
        self.create_oval(0, 0, s, s, fill=self._color, outline="")
        self.create_text(s//2, s//2, text=self._initials,
                         font=Palette.bold(Palette.MICRO),
                         fill=Palette.ON_SURFACE_VAR)

class LiveFeedRow(tk.Frame):
    """Single row in the Live Forensic Feed."""
    AVATAR_COLORS = {
        "jd": "#2a3a2a",
        "sa": "#2a2a3a",
        "bt": "#3a2a2a",
        "uk": "#3a3020",
    }
    EVENT_COLORS = {
        "Elevated Privileges": Palette.ERROR,
        "SSH Brute Force":     Palette.ERROR,
        "File Decryption":     Palette.WARNING,
        "Database Dump":       Palette.WARNING,
    }

    def __init__(self, parent, timestamp, initials, username,
                 ip, event_type, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(timestamp, initials, username, ip, event_type, bg)

    def _build(self, timestamp, initials, username, ip, event_type, bg):
        row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_LG)

        # timestamp (monospace feel with fixed width)
        tk.Label(row, text=timestamp,
                 font=(Palette._FONT[0], Palette.LABEL, "normal"),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=18, anchor="w",
                 justify="left").pack(side="left")

        # avatar + username
        user_frame = tk.Frame(row, bg=bg)
        user_frame.pack(side="left", padx=(0, Palette.PAD_MD))

        av_color = self.AVATAR_COLORS.get(initials.lower(),
                                          Palette.SURFACE_HIGHEST)
        UserAvatar(user_frame, initials=initials.upper(),
                   bg_color=av_color, size=26).pack(side="left",
                                                    padx=(0, Palette.PAD_SM))
        tk.Label(user_frame, text=username,
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=bg).pack(side="left")

        # ip
        tk.Label(row, text=ip,
                 font=(Palette._FONT[0], Palette.LABEL, "normal"),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=16, anchor="w").pack(side="left",
                                                   padx=(0, Palette.PAD_MD))

        # event type
        ev_color = self.EVENT_COLORS.get(event_type, Palette.ON_SURFACE)
        tk.Label(row, text=event_type,
                 font=Palette.font(Palette.BODY),
                 fg=ev_color,
                 bg=bg, anchor="w").pack(side="left")

        # divider
        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(
            fill="x", padx=Palette.PAD_LG)

class ModelDistBar(tk.Frame):
    """Single model distribution row with thin bar."""
    def __init__(self, parent, label, pct, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)

        row = tk.Frame(self, bg=bg)
        row.pack(fill="x")
        tk.Label(row, text=label,
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(side="left")
        tk.Label(row, text=f"{pct}%",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=bg).pack(side="right")

        track = tk.Frame(self, bg=Palette.SURFACE_HIGH, height=4)
        track.pack(fill="x", pady=(3, Palette.PAD_SM))
        fill_f = tk.Frame(track, bg=Palette.PRIMARY, height=4)
        fill_f.place(relx=0, rely=0, relwidth=pct/100, relheight=1)

class SecurityCoreCanvas(tk.Canvas):
    """Animated circuit board / security core visual."""
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_HIGH)
        super().__init__(parent, bg=bg, height=120,
                         highlightthickness=0, **kw)
        self._bg    = bg
        self._tick  = 0
        self._nodes = [(random.randint(20, 240), random.randint(10, 100))
                       for _ in range(18)]
        self._edges = []
        for i in range(len(self._nodes)):
            for j in range(i+1, len(self._nodes)):
                nx,ny = self._nodes[i]; mx,my = self._nodes[j]
                if abs(nx-mx)+abs(ny-my) < 80:
                    self._edges.append((i,j))
        self.bind("<Configure>", self._rescale)
        self._animate()

    def _rescale(self, e=None):
        w = self.winfo_width()
        if w < 10: return
        scale = w / 260
        self._scaled = [(int(x*scale), y) for x,y in self._nodes]

    def _animate(self):
        self._tick += 1
        self._draw()
        self.after(80, self._animate)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return

        nodes = getattr(self, "_scaled", self._nodes)

        # edges
        for i,j in self._edges:
            x0,y0 = nodes[i]; x1,y1 = nodes[j]
            alpha = 0.3 + 0.2*abs(((self._tick + i*7)%20)/20 - 0.5)
            gray  = int(40 + alpha*60)
            col   = "#{:02x}{:02x}{:02x}".format(gray, gray, int(gray*0.8))
            self.create_line(x0,y0,x1,y1,fill=col,width=1)

        # nodes
        for idx,(x,y) in enumerate(nodes):
            pulse = (self._tick + idx*3) % 30
            size  = 3 if pulse > 20 else 4
            gold  = idx % 5 == 0
            col   = Palette.PRIMARY if gold else "#4a4030"
            self.create_oval(x-size,y-size,x+size,y+size,
                             fill=col,outline="")

        # label
        self.create_rectangle(0, h-28, w, h,
                              fill=self._bg, outline="")
        self.create_text(Palette.PAD_SM, h-20,
                         text="SECURITY CORE",
                         font=Palette.bold(Palette.MICRO),
                         fill=Palette.PRIMARY, anchor="w")
        self.create_text(Palette.PAD_SM, h-8,
                         text="Encrypted Layer 7 Monitoring",
                         font=Palette.font(Palette.MICRO),
                         fill=Palette.ON_SURFACE_VAR, anchor="w")

class NodeIntelPanel(tk.Frame):
    """Right sidebar: node status, model distribution, security core, export."""
    MODEL_DATA = [
        ("Pattern Matching",   42),
        ("Anomaly Detection",  31),
        ("Signature Recognition", 27),
    ]

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_LOW)
        super().__init__(parent, bg=bg, width=Palette.RIGHT_PANEL_W, **kw)
        self.pack_propagate(False)
        self._bg = bg
        self._build()

    def _build(self):
        # header
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=Palette.PAD_MD, pady=(Palette.PAD_LG, 0))
        tk.Label(hdr, text="⬡",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=self._bg).pack(side="left", padx=(0,6))
        tk.Label(hdr, text="NODE INTELLIGENCE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack(side="left")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(
            fill="x", pady=(Palette.PAD_SM, 0))

        # ── primary node status ───────────────────────────────────────
        ns = tk.Frame(self, bg=Palette.SURFACE_CONTAINER,
                      padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        ns.pack(fill="x", padx=Palette.PAD_MD, pady=Palette.PAD_MD)

        tk.Label(ns, text="PRIMARY NODE STATUS",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
                                                    pady=(0, Palette.PAD_SM))

        stat_row = tk.Frame(ns, bg=Palette.SURFACE_CONTAINER)
        stat_row.pack(fill="x")
        tk.Label(stat_row, text="Active Nodes",
                 font=Palette.font(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")
        tk.Label(stat_row, text="12 / 12",
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_CONTAINER).pack(side="right")

        # full bar
        bar_track = tk.Frame(ns, bg=Palette.SURFACE_HIGH, height=6)
        bar_track.pack(fill="x", pady=(Palette.PAD_SM, 0))
        tk.Frame(bar_track, bg=Palette.PRIMARY,
                 height=6).place(relx=0, rely=0,
                                 relwidth=1.0, relheight=1)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # ── model distribution ────────────────────────────────────────
        md = tk.Frame(self, bg=self._bg,
                      padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        md.pack(fill="x")
        tk.Label(md, text="MODEL DISTRIBUTION",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg).pack(anchor="w", pady=(0, Palette.PAD_MD))
        for label, pct in self.MODEL_DATA:
            ModelDistBar(md, label, pct, bg=self._bg).pack(fill="x")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # ── security core visual ──────────────────────────────────────
        sc_wrap = tk.Frame(self, bg=Palette.SURFACE_HIGH)
        sc_wrap.pack(fill="x", padx=Palette.PAD_MD,
                     pady=Palette.PAD_MD)
        SecurityCoreCanvas(sc_wrap, bg=Palette.SURFACE_HIGH).pack(
            fill="x", expand=True)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # ── export button ─────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=self._bg,
                             padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        btn_frame.pack(fill="x")
        GoldButton(btn_frame, text="Export System Log",
                   icon="↓", style="outline").pack(
                       fill="x", ipady=6)

class LiveFeed(tk.Frame):
    FEED_DATA = [
        ("2023-10-24\n13:58:42", "JD", "j.doe_admin",  "192.168.1.104", "Elevated Privileges"),
        ("2023-10-24\n13:57:15", "SA", "s.agent_04",   "10.0.4.52",     "File Decryption"),
        ("2023-10-24\n13:55:01", "BT", "backup_task",  "172.16.0.44",   "Database Dump"),
        ("2023-10-24\n13:54:22", "UK", "unknown_user", "212.44.15.2",   "SSH Brute Force"),
    ]

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(Palette.PAD_MD, Palette.PAD_SM))
        for col, w in [("TIMESTAMP",18),("USER IDENTITY",20),
                       ("IP ADDRESS",16),("EVENT TYPE",16)]:
            tk.Label(hdr, text=col,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg, width=w, anchor="w").pack(side="left")

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(
            fill="x", padx=Palette.PAD_LG)

        # rows
        for ts, ini, usr, ip, ev in self.FEED_DATA:
            LiveFeedRow(self, ts, ini, usr, ip, ev,
                        bg=self._bg).pack(fill="x")

        # footer
        tk.Label(self,
                 text="Showing 1-4 of 1,284,902 results",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg).pack(anchor="w",
                                   padx=Palette.PAD_LG,
                                   pady=Palette.PAD_MD)

class DashboardPage(tk.Frame):
    def __init__(self, parent,user=None, on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._clock_label = None
        self._build()
        self._tick_clock()


    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=1)

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
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")

        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")))

        # ── mousewheel fix ────────────────────────────────────────────
        def _on_wheel(e):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self._populate_main(inner)             

        NodeIntelPanel(self, bg=Palette.SURFACE_LOW).grid(
            row=0, column=1, sticky="nsew")

    def _populate_main(self, p):
        # page header
        hdr = tk.Frame(p, bg=Palette.SURFACE)
        hdr.pack(fill="x", padx=Palette.PAD_XL,
                 pady=(Palette.PAD_LG, 0))

        tk.Label(hdr, text="Operational Overview",
                 font=(Palette._FONT[0], Palette.DISPLAY, "bold"),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(anchor="w")

        sub_row = tk.Frame(hdr, bg=Palette.SURFACE)
        sub_row.pack(fill="x", pady=(4, 0))
        tk.Label(sub_row, text="System state as of ",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(side="left")
        self._clock_label = tk.Label(sub_row, text="",
                                     font=Palette.bold(Palette.LABEL),
                                     fg=Palette.ON_SURFACE_VAR,
                                     bg=Palette.SURFACE)
        self._clock_label.pack(side="left")

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        cards_row = tk.Frame(p, bg=Palette.SURFACE)
        cards_row.pack(fill="x", padx=Palette.PAD_XL)
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)
        cards_row.columnconfigure(2, weight=1)

        StatCard(cards_row,
                 icon="▣", badge="+12% VS PREV",
                 badge_color=Palette.SUCCESS,
                 value="1,284,902",
                 label="Total Logs Analyzed",
                 icon_color=Palette.PRIMARY,
                 bg=Palette.SURFACE_CONTAINER
                 ).grid(row=0, column=0, sticky="nsew",
                        padx=(0, Palette.PAD_SM))

        StatCard(cards_row,
                 icon="⚠", badge="CRITICAL",
                 badge_color=Palette.ERROR,
                 value="42",
                 label="Suspicious Events",
                 icon_color=Palette.ERROR,
                 bg=Palette.SURFACE_CONTAINER
                 ).grid(row=0, column=1, sticky="nsew",
                        padx=(0, Palette.PAD_SM))

        StatCard(cards_row,
                 icon="✔", badge="STABLE",
                 badge_color=Palette.SUCCESS,
                 value="1.2M",
                 label="Normal Events",
                 icon_color=Palette.SUCCESS,
                 bg=Palette.SURFACE_CONTAINER
                 ).grid(row=0, column=2, sticky="nsew")

        tk.Frame(p, height=Palette.PAD_LG, bg=Palette.SURFACE).pack()

        feed_card = tk.Frame(p, bg=Palette.SURFACE_CONTAINER)
        feed_card.pack(fill="x", padx=Palette.PAD_XL)

        feed_hdr = tk.Frame(feed_card, bg=Palette.SURFACE_CONTAINER)
        feed_hdr.pack(fill="x", padx=Palette.PAD_LG,
                      pady=(Palette.PAD_LG, 0))

        dot_frame = tk.Frame(feed_hdr, bg=Palette.SURFACE_CONTAINER)
        dot_frame.pack(side="left")
        self._dot = tk.Label(dot_frame, text="●",
                             font=Palette.bold(Palette.MICRO),
                             fg=Palette.SUCCESS,
                             bg=Palette.SURFACE_CONTAINER)
        self._dot.pack(side="left", padx=(0, 6))
        tk.Label(feed_hdr, text="Live Forensic Feed",
                 font=(Palette._FONT[0], Palette.TITLE_LG, "bold"),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE_CONTAINER).pack(side="left")

        LiveFeed(feed_card, bg=Palette.SURFACE_CONTAINER).pack(fill="x")

        tk.Frame(p, height=Palette.PAD_XL, bg=Palette.SURFACE).pack()

        self._blink_dot()

    def _tick_clock(self):
        if self._clock_label and self._clock_label.winfo_exists():
            now = datetime.datetime.utcnow()
            self._clock_label.config(
                text=now.strftime("%d %b %Y  %H:%M:%S UTC"))
            self.after(1000, self._tick_clock)

    def _blink_dot(self):
        if hasattr(self, "_dot") and self._dot.winfo_exists():
            cur = self._dot.cget("fg")
            nxt = Palette.SUCCESS if cur == Palette.SURFACE_CONTAINER \
                  else Palette.SURFACE_CONTAINER
            self._dot.config(fg=nxt)
            self.after(800, self._blink_dot)

