
import tkinter as tk
from colors import Palette


class TopBar(tk.Frame):
    def __init__(self, parent,
                 title: str = "XAI Network Logs Analysis System",
                 role: str = "L3 Authority",
                 agent: dict = None,
                 search_placeholder: str = "Search evidence...",
                 on_search=None,
                 **kw):
        topbar_h = getattr(Palette, "TOPBAR_H", 52)
        bg       = getattr(Palette, "SURFACE_LOW", "#181818")

        super().__init__(parent, bg=bg, height=topbar_h, **kw)
        self.pack_propagate(False)

        self._build(title, agent, role, search_placeholder)

    def _build(self, title, agent, role, search_placeholder):
        bg       = getattr(Palette, "SURFACE_LOW",    "#181818")
        primary  = getattr(Palette, "PRIMARY",        "#f2ca50")
        surf_hi  = getattr(Palette, "SURFACE_HIGHEST","#303030")
        surf_hgh = getattr(Palette, "SURFACE_HIGH",   "#252525")
        on_surf  = getattr(Palette, "ON_SURFACE",     "#e4e4e4")
        on_var   = getattr(Palette, "ON_SURFACE_VAR", "#888888")
        outline  = getattr(Palette, "OUTLINE",        "#2e2e2e")
        pad_lg   = getattr(Palette, "PAD_LG",         18)
        pad_md   = getattr(Palette, "PAD_MD",         12)

        ff       = getattr(Palette, "_FONT", ["Helvetica Neue"])[0]
        title_md = getattr(Palette, "TITLE_MD", 13)
        label_s  = getattr(Palette, "LABEL",    10)
        micro    = getattr(Palette, "MICRO",     9)
        body     = getattr(Palette, "BODY",      12)

        tk.Label(self, text=title,
                 font=(ff, title_md, "bold"),
                 fg=primary, bg=bg).pack(side="left", padx=pad_lg)

        right = tk.Frame(self, bg=bg)
        right.pack(side="right", padx=pad_lg)

    
        
        av = tk.Frame(right, bg=surf_hi,
                  width=30, height=30, cursor="hand2")
        av.pack(side="right", padx=(6, 0))
        av.pack_propagate(False)
        initials = "".join(
            w[0].upper()
            for w in agent['username'].split()[:2]
        ) or "??"
        av_lbl = tk.Label(av, text=initials,
                        font=(ff, micro, "bold"),
                        fg=primary, bg=surf_hi,
                        cursor="hand2")
        av_lbl.place(relx=.5, rely=.5, anchor="center")

        self._agent = agent

        for w in (av, av_lbl):
            w.bind("<Button-1>", lambda e: self._open_profile())

        # hover effect
        av.bind("<Enter>",
                lambda e: av.config(bg=Palette.OUTLINE_BRIGHT))
        av.bind("<Leave>",
                lambda e: av.config(bg=surf_hi))

        # name + role
        info = tk.Frame(right, bg=bg)
        info.pack(side="right", padx=(0, 6))
        tk.Label(info, text=agent['username'],
                 font=(ff, label_s, "bold"),
                 fg=on_surf, bg=bg).pack(anchor="e")
        tk.Label(info, text=role,
                 font=(ff, micro, "normal"),
                 fg=on_var, bg=bg).pack(anchor="e")

        # bell
        tk.Label(right, text="🔔",
                 font=(ff, title_md, "normal"),
                 fg=on_var, bg=bg,
                 cursor="hand2").pack(side="right", padx=(0, 14))

        sf = tk.Frame(self, bg=surf_hgh,
                      highlightbackground=outline,
                      highlightthickness=1)
        sf.pack(side="left", padx=pad_md)

        tk.Label(sf, text="⌕",
                 font=(ff, body, "normal"),
                 fg=on_var, bg=surf_hgh).pack(side="left", padx=(8, 4))

        e = tk.Entry(sf,
                     font=(ff, body, "normal"),
                     fg=on_var,
                     bg=surf_hgh,
                     insertbackground=primary,
                     relief="flat", bd=0, width=26)
        e.insert(0, search_placeholder)
        e.pack(side="left", pady=6, padx=(0, 8))

        def _fi(ev):
            if e.get() == search_placeholder:
                e.delete(0, "end")
                e.config(fg=on_surf)
        def _fo(ev):
            if not e.get():
                e.insert(0, search_placeholder)
                e.config(fg=on_var)

        e.bind("<FocusIn>",  _fi)
        e.bind("<FocusOut>", _fo)

        # bottom divider line
        tk.Frame(self, height=1, bg=outline).place(
            relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        
        
    def _open_profile(self):
        from profile import ProfilePanel
        ProfilePanel(
            self.winfo_toplevel(),
            user=self._agent,
            on_profile_updated=self._on_profile_updated
        )

    def _on_profile_updated(self, updated: dict):
        """Refresh the initials and username label after profile edit."""
        self._agent = updated
        # rebuild topbar is simplest — app handles this
        if hasattr(self, "_on_user_updated") and self._on_user_updated:
            self._on_user_updated(updated)    