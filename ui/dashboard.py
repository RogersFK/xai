from colors import Palette
import tkinter as tk
import datetime
import threading
import requests
from components import GoldButton
from helper import api
from logger import get_logger
import random

log = get_logger("DASHBOARD")

class SecurityCoreCanvas(tk.Canvas):
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
                nx, ny = self._nodes[i]
                mx, my = self._nodes[j]
                if abs(nx-mx) + abs(ny-my) < 80:
                    self._edges.append((i, j))
        self.bind("<Configure>", self._rescale)
        self._animate()

    def _rescale(self, e=None):
        w = self.winfo_width()
        if w < 10:
            return
        scale = w / 260
        self._scaled = [(int(x*scale), y) for x, y in self._nodes]

    def _animate(self):
        self._tick += 1
        self._draw()
        self.after(80, self._animate)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10:
            return

        nodes = getattr(self, "_scaled", self._nodes)

        for i, j in self._edges:
            x0, y0 = nodes[i]
            x1, y1 = nodes[j]
            alpha = 0.3 + 0.2 * abs(((self._tick + i*7) % 20) / 20 - 0.5)
            gray  = int(40 + alpha * 60)
            col   = "#{:02x}{:02x}{:02x}".format(
                gray, gray, int(gray * 0.8))
            self.create_line(x0, y0, x1, y1, fill=col, width=1)

        for idx, (x, y) in enumerate(nodes):
            pulse = (self._tick + idx*3) % 30
            size  = 3 if pulse > 20 else 4
            col   = Palette.PRIMARY if idx % 5 == 0 else "#4a4030"
            self.create_oval(x-size, y-size, x+size, y+size,
                             fill=col, outline="")

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


class StatCard(tk.Frame):
    def __init__(self, parent, icon="▣", badge="", badge_color=None,
                 value="0", label="", icon_color=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(icon, badge, badge_color, value, label, icon_color, bg)

    def _build(self, icon, badge, badge_color, value, label, icon_color, bg):
        top = tk.Frame(self, bg=bg)
        top.pack(fill="x", padx=Palette.PAD_LG, pady=(Palette.PAD_LG, 0))

        ic = tk.Frame(top, bg=Palette.SURFACE_HIGH, width=40, height=40)
        ic.pack(side="left")
        ic.pack_propagate(False)
        tk.Label(ic, text=icon,
                 font=Palette.bold(16),
                 fg=icon_color or Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGH).place(relx=.5, rely=.5,
                                                anchor="center")
        if badge:
            tk.Label(top, text=badge,
                     font=Palette.bold(Palette.MICRO),
                     fg=badge_color or Palette.ON_SURFACE_VAR,
                     bg=bg).pack(side="right", anchor="n")

        tk.Label(self, text=value,
                 font=(Palette._FONT[0], 32, "bold"),
                 fg=Palette.ERROR if badge_color == Palette.ERROR
                    else Palette.ON_SURFACE,
                 bg=bg).pack(anchor="w",
                             padx=Palette.PAD_LG,
                             pady=(Palette.PAD_SM, 0))
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
    SEVERITY_COLORS = {
        "critical": Palette.ERROR,
        "high":     Palette.ERROR,
        "medium":   Palette.WARNING,
        "low":      Palette.SUCCESS,
        "info":     Palette.INFO,
    }
    AVATAR_PALETTE = [
        "#2a3a2a", "#2a2a3a", "#3a2a2a",
        "#3a3020", "#203a3a", "#3a2030",
    ]

    def __init__(self, parent, timestamp, initials, username,
                 source_ip, event_type, severity, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._build(timestamp, initials, username,
                    source_ip, event_type, severity, bg)

    def _build(self, timestamp, initials, username,
               source_ip, event_type, severity, bg):
        row = tk.Frame(self, bg=bg, pady=Palette.PAD_SM)
        row.pack(fill="x", padx=Palette.PAD_LG)

        # timestamp
        ts = timestamp[:19].replace("T", "\n") if "T" in timestamp \
             else str(timestamp)[:19]
        tk.Label(row, text=ts,
                 font=(Palette._FONT[0], Palette.LABEL, "normal"),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=18, anchor="w",
                 justify="left").pack(side="left")

        # avatar + username
        user_frame = tk.Frame(row, bg=bg)
        user_frame.pack(side="left", padx=(0, Palette.PAD_MD))

        av_color = self.AVATAR_PALETTE[
            hash(initials) % len(self.AVATAR_PALETTE)]
        UserAvatar(user_frame, initials=initials.upper(),
                   bg_color=av_color, size=26).pack(
            side="left", padx=(0, Palette.PAD_SM))
        tk.Label(user_frame, text=username,
                 font=Palette.bold(Palette.BODY),
                 fg=Palette.ON_SURFACE,
                 bg=bg).pack(side="left")

        # source ip
        tk.Label(row, text=source_ip,
                 font=(Palette._FONT[0], Palette.LABEL, "normal"),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=16, anchor="w").pack(
            side="left", padx=(0, Palette.PAD_MD))

        # event type
        ev_color = self.SEVERITY_COLORS.get(
            severity.lower(), Palette.ON_SURFACE)
        tk.Label(row, text=event_type,
                 font=Palette.font(Palette.BODY),
                 fg=ev_color, bg=bg,
                 anchor="w").pack(side="left")

        # severity chip on right
        sev_color = self.SEVERITY_COLORS.get(
            severity.lower(), Palette.ON_SURFACE_VAR)
        tk.Label(row, text=severity.upper(),
                 font=Palette.bold(Palette.MICRO),
                 fg=sev_color, bg=bg).pack(side="right")

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_LG)



class LiveFeed(tk.Frame):
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg           = bg
        self._total_count  = 0
        self._rows_frame   = None
        self._footer_lbl   = None
        self._build()

    def _build(self):
        # column headers
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(Palette.PAD_MD, Palette.PAD_SM))
        for col, w in [("TIMESTAMP", 18), ("USER IDENTITY", 20),
                       ("IP ADDRESS", 16), ("EVENT TYPE", 16),
                       ("SEVERITY", 10)]:
            tk.Label(hdr, text=col,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg, width=w, anchor="w").pack(side="left")

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x", padx=Palette.PAD_LG)

        # rows container
        self._rows_frame = tk.Frame(self, bg=self._bg)
        self._rows_frame.pack(fill="x")

        # loading placeholder
        self._loading = tk.Label(
            self._rows_frame,
            text="Loading feed…",
            font=Palette.font(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=self._bg)
        self._loading.pack(pady=Palette.PAD_LG)

        # footer
        self._footer_lbl = tk.Label(
            self,
            text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=self._bg)
        self._footer_lbl.pack(anchor="w",
                               padx=Palette.PAD_LG,
                               pady=Palette.PAD_MD)

    def render(self, events: list, total: int):
        """Called from DashboardPage after API load."""
        for w in self._rows_frame.winfo_children():
            w.destroy()

        if not events:
            tk.Label(self._rows_frame,
                     text="No events recorded yet.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg).pack(pady=Palette.PAD_LG)
        else:
            for e in events:
                ts  = str(e.get("timestamp", ""))
                LiveFeedRow(
                    self._rows_frame,
                    timestamp  = ts,
                    initials   = e.get("initials",   "??"),
                    username   = e.get("username",   "unknown"),
                    source_ip  = e.get("source_ip",  "—"),
                    event_type = e.get("event_type", "—"),
                    severity   = e.get("severity",   "info"),
                    bg=self._bg,
                ).pack(fill="x")

        shown = len(events)
        self._footer_lbl.config(
            text=f"Showing 1–{shown} of {total:,} events")

    def set_error(self, msg: str):
        for w in self._rows_frame.winfo_children():
            w.destroy()
        tk.Label(self._rows_frame,
                 text=f"⚠ {msg}",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ERROR,
                 bg=self._bg).pack(pady=Palette.PAD_LG)



class ModelDistBar(tk.Frame):
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
        tk.Frame(track, bg=Palette.PRIMARY,
                 height=4).place(relx=0, rely=0,
                                 relwidth=max(pct, 0)/100,
                                 relheight=1)



class NodeIntelPanel(tk.Frame):
    def __init__(self, parent, **kw):
        bg = kw.pop("bg", Palette.SURFACE_LOW)
        super().__init__(parent, bg=bg,
                         width=Palette.RIGHT_PANEL_W, **kw)
        self.pack_propagate(False)
        self._bg       = bg
        self._dist_frame = None
        self._model_lbl  = None
        self._ver_lbl    = None
        self._build()

    def _build(self):
        # header
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=Palette.PAD_MD,
                 pady=(Palette.PAD_LG, 0))
        tk.Label(hdr, text="⬡",
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.PRIMARY, bg=self._bg).pack(
            side="left", padx=(0, 6))
        tk.Label(hdr, text="NODE INTELLIGENCE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE,
                 bg=self._bg).pack(side="left")

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(
            fill="x", pady=(Palette.PAD_SM, 0))

        # active model status
        ns = tk.Frame(self, bg=Palette.SURFACE_CONTAINER,
                      padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        ns.pack(fill="x", padx=Palette.PAD_MD, pady=Palette.PAD_MD)

        tk.Label(ns, text="ACTIVE MODEL",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", pady=(0, Palette.PAD_SM))

        self._model_lbl = tk.Label(
            ns, text="Loading…",
            font=Palette.bold(Palette.LABEL),
            fg=Palette.PRIMARY,
            bg=Palette.SURFACE_CONTAINER)
        self._model_lbl.pack(anchor="w")

        self._ver_lbl = tk.Label(
            ns, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER)
        self._ver_lbl.pack(anchor="w")

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x")

        # model distribution
        md = tk.Frame(self, bg=self._bg,
                      padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        md.pack(fill="x")
        tk.Label(md, text="MODEL DISTRIBUTION",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg).pack(anchor="w",
                                    pady=(0, Palette.PAD_MD))

        self._dist_frame = tk.Frame(md, bg=self._bg)
        self._dist_frame.pack(fill="x")

        tk.Label(self._dist_frame,
                 text="Loading…",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg).pack(anchor="w")

        tk.Frame(self, height=1,
                 bg=Palette.OUTLINE).pack(fill="x")
        
        
        sc_wrap = tk.Frame(self, bg=Palette.SURFACE_HIGH)
        sc_wrap.pack(fill="x", padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        SecurityCoreCanvas(sc_wrap, bg=Palette.SURFACE_HIGH).pack(
            fill="x", expand=True)

        tk.Frame(self, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # btn_frame = tk.Frame(self, bg=self._bg,
        #                      padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        # btn_frame.pack(fill="x")
        # GoldButton(btn_frame, text="Export System Log",
        #            icon="↓", style="outline").pack(
        #     fill="x", ipady=6)

    def render(self, node_intel: dict):
        """Called after API load to populate model info."""
        self._model_lbl.config(
            text=node_intel.get("active_model_name", "—"))
        self._ver_lbl.config(
            text=f"v{node_intel.get('active_model_version', '—')}")

        for w in self._dist_frame.winfo_children():
            w.destroy()

        dist = node_intel.get("model_distribution", [])
        if not dist:
            tk.Label(self._dist_frame,
                     text="No model data available.",
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=self._bg).pack(anchor="w")
        else:
            for item in dist:
                ModelDistBar(
                    self._dist_frame,
                    label=item.get("name", ""),
                    pct=item.get("percentage", 0),
                    bg=self._bg,
                ).pack(fill="x")

    def set_error(self, msg: str):
        self._model_lbl.config(text=f"⚠ {msg}", fg=Palette.ERROR)
        for w in self._dist_frame.winfo_children():
            w.destroy()



class DashboardPage(tk.Frame):
    def __init__(self, parent, user=None,
                 on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user        = user
        self._clock_label = None
        self._stat_cards  = []       # list of (frame, value_label)
        self._live_feed   = None
        self._node_panel  = None
        self._build()
        self._tick_clock()
        self._load()                 # fetch from backend on mount


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

        def _on_wheel(e):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        self._populate_main(inner)

        self._node_panel = NodeIntelPanel(self, bg=Palette.SURFACE_LOW)
        self._node_panel.grid(row=0, column=1, sticky="nsew")

    def _populate_main(self, p):
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
        self._clock_label = tk.Label(
            sub_row, text="",
            font=Palette.bold(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE)
        self._clock_label.pack(side="left")

        # refresh button
        GoldButton(hdr, text="Refresh",
                   command=self._load).pack(
            side="right", ipady=4, ipadx=12)

        tk.Frame(p, height=Palette.PAD_LG,
                 bg=Palette.SURFACE).pack()

        cards_row = tk.Frame(p, bg=Palette.SURFACE)
        cards_row.pack(fill="x", padx=Palette.PAD_XL)
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)
        cards_row.columnconfigure(2, weight=1)

        # store refs so we can update values after API call
        self._card_total = self._make_stat_card(
            cards_row,
            icon="▣", badge="", badge_color=Palette.SUCCESS,
            value="…", label="Total Logs Analyzed",
            icon_color=Palette.PRIMARY,
            col=0)

        self._card_suspicious = self._make_stat_card(
            cards_row,
            icon="⚠", badge="", badge_color=Palette.ERROR,
            value="…", label="Suspicious Events",
            icon_color=Palette.ERROR,
            col=1)

        self._card_normal = self._make_stat_card(
            cards_row,
            icon="✔", badge="STABLE", badge_color=Palette.SUCCESS,
            value="…", label="Normal Events",
            icon_color=Palette.SUCCESS,
            col=2)

        tk.Frame(p, height=Palette.PAD_LG,
                 bg=Palette.SURFACE).pack()

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

        self._live_feed = LiveFeed(feed_card,
                                    bg=Palette.SURFACE_CONTAINER)
        self._live_feed.pack(fill="x")

        tk.Frame(p, height=Palette.PAD_XL,
                 bg=Palette.SURFACE).pack()

        self._blink_dot()

    def _make_stat_card(self, parent, icon, badge, badge_color,
                        value, label, icon_color, col) -> tk.Label:
        """Creates a StatCard and returns its value label for later updates."""
        frame = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0 if col == 2 else Palette.PAD_SM, 0)
                   if col > 0 else (0, Palette.PAD_SM))

        top = tk.Frame(frame, bg=Palette.SURFACE_CONTAINER)
        top.pack(fill="x", padx=Palette.PAD_LG,
                 pady=(Palette.PAD_LG, 0))

        ic = tk.Frame(top, bg=Palette.SURFACE_HIGH, width=40, height=40)
        ic.pack(side="left")
        ic.pack_propagate(False)
        tk.Label(ic, text=icon, font=Palette.bold(16),
                 fg=icon_color,
                 bg=Palette.SURFACE_HIGH).place(relx=.5, rely=.5,
                                                anchor="center")

        badge_lbl = tk.Label(top, text=badge,
                              font=Palette.bold(Palette.MICRO),
                              fg=badge_color,
                              bg=Palette.SURFACE_CONTAINER)
        badge_lbl.pack(side="right", anchor="n")

        val_lbl = tk.Label(frame, text=value,
                           font=(Palette._FONT[0], 32, "bold"),
                           fg=Palette.ERROR if badge_color == Palette.ERROR
                              else Palette.ON_SURFACE,
                           bg=Palette.SURFACE_CONTAINER)
        val_lbl.pack(anchor="w", padx=Palette.PAD_LG,
                     pady=(Palette.PAD_SM, 0))

        tk.Label(frame, text=label.upper(),
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", padx=Palette.PAD_LG,
            pady=(0, Palette.PAD_LG))

        # store badge label ref for updating later
        val_lbl._badge_lbl = badge_lbl
        return val_lbl


    def _load(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            data = api("get", "/dashboard")
            self.after(0, lambda: self._render(data))
        except requests.HTTPError as exc:
            msg = f"Server error ({exc.response.status_code})"
            self.after(0, lambda: self._on_error(msg))
        except requests.ConnectionError:
            self.after(0, lambda: self._on_error("Cannot reach server."))
        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))

    def _render(self, data: dict):
        stats     = data.get("stat_cards",  {})
        feed      = data.get("live_feed",   [])
        intel     = data.get("node_intel",  {})
        total     = data.get("total_feed_count", 0)

        change = stats.get("suspicious_change_pct", 0)
        change_str = (f"+{change:.1f}%" if change >= 0
                      else f"{change:.1f}%")
        change_color = Palette.SUCCESS if change >= 0 else Palette.ERROR

        self._card_total.config(
            text=f"{stats.get('total_logs_analyzed', 0):,}")
        self._card_total._badge_lbl.config(
            text=f"{change_str} VS PREV",
            fg=change_color)

        self._card_suspicious.config(
            text=str(stats.get("suspicious_events", 0)))
        self._card_suspicious._badge_lbl.config(
            text="CRITICAL" if stats.get("suspicious_events", 0) > 0
                 else "CLEAR",
            fg=Palette.ERROR if stats.get("suspicious_events", 0) > 0
               else Palette.SUCCESS)

        self._card_normal.config(
            text=f"{stats.get('normal_events', 0):,}")

        self._live_feed.render(feed, total)

        self._node_panel.render(intel)

        log.debug("Dashboard loaded — %d feed events, %d total",
                  len(feed), total)

    def _on_error(self, msg: str):
        log.error("Dashboard load failed: %s", msg)
        self._card_total.config(text="—")
        self._card_suspicious.config(text="—")
        self._card_normal.config(text="—")
        self._live_feed.set_error(msg)
        self._node_panel.set_error(msg)


    def _tick_clock(self):
        if self._clock_label and self._clock_label.winfo_exists():
            now = datetime.datetime.utcnow()
            self._clock_label.config(
                text=now.strftime("%d %b %Y  %H:%M:%S UTC"))
            self.after(1000, self._tick_clock)

    def _blink_dot(self):
        if hasattr(self, "_dot") and self._dot.winfo_exists():
            cur = self._dot.cget("fg")
            nxt = (Palette.SUCCESS
                   if cur == Palette.SURFACE_CONTAINER
                   else Palette.SURFACE_CONTAINER)
            self._dot.config(fg=nxt)
            self.after(800, self._blink_dot)