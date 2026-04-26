from colors import Palette
import tkinter as tk

class SideNav(tk.Frame):
    # ITEMS  = [("Dashboard","▣"),("Upload Logs","↑"),
    #            ("Analysis","◈"),("Reports","☰"),("Settings","⚙")]
    # BOTTOM = [("Profile","👤"),("Support","?"),("Logout","↩")] 
    
    ITEMS  = [("Dashboard","▣"),("Upload Logs","↑"),
               ("Analysis","◈"),("Reports","☰"),]
    BOTTOM = [("Profile","👤"),("Logout","↩")] 

    def __init__(self, parent, active="Dashboard", on_navigate=None, is_admin=False, **kw):
        super().__init__(parent, bg=Palette.SURFACE_LOW,
                         width=Palette.NAV_W, **kw)
        self.pack_propagate(False)
        self._active      = active
        # self._on_navigate = on_navigate
        # self._build()
        self._is_admin   = is_admin
        self._on_navigate = on_navigate
        self._build()


    
    def _build(self):
        # brand
        brand = tk.Frame(self, bg=Palette.SURFACE_LOW, height=80)
        brand.pack(fill="x")
        brand.pack_propagate(False)

        card = tk.Frame(brand, bg=Palette.SURFACE_CONTAINER,
                        padx=12, pady=10)
        card.pack(fill="x", padx=12, pady=12)

        badge = tk.Frame(card, bg=Palette.PRIMARY, width=28, height=28)
        badge.pack(side="left", padx=(0,10))
        badge.pack_propagate(False)
        tk.Label(badge, text="⬡", font=Palette.bold(12),
                fg=Palette.ON_PRIMARY,
                bg=Palette.PRIMARY).place(relx=.5, rely=.5, anchor="center")

        inf = tk.Frame(card, bg=Palette.SURFACE_CONTAINER)
        inf.pack(side="left")
        tk.Label(inf, text="Forensic Node",
                font=Palette.bold(Palette.LABEL),
                fg=Palette.ON_SURFACE,
                bg=Palette.SURFACE_CONTAINER).pack(anchor="w")
        tk.Label(inf, text="Terminal 01",
                font=Palette.font(Palette.MICRO),
                fg=Palette.ON_SURFACE_VAR,
                bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        # nav items — add Admin only for admins
        items = list(self.ITEMS)
        if self._is_admin:
            items.append(("Admin", "◎"))

        nav_wrap = tk.Frame(self, bg=Palette.SURFACE_LOW)
        nav_wrap.pack(fill="x", padx=8, pady=(4, 0))
        for label, icon in items:
            self._item(nav_wrap, label, icon)

        # bottom
        bot = tk.Frame(self, bg=Palette.SURFACE_LOW)
        bot.pack(side="bottom", fill="x", padx=8, pady=12)
        tk.Frame(bot, height=1, bg=Palette.OUTLINE).pack(fill="x", pady=(0, 8))
        for label, icon in self.BOTTOM:
            self._item(bot, label, icon)

    def _item(self, parent, label, icon):
        active = label == self._active
        bg = Palette.SURFACE_HIGH if active else Palette.SURFACE_LOW
        fg = Palette.PRIMARY if active else Palette.ON_SURFACE_VAR

        row = tk.Frame(parent, bg=bg, cursor="hand2", height=36)
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

        for w in [row] + list(row.winfo_children()):
            w.bind("<Button-1>", lambda e, l=label: self._click(l))
        if not active:
            for w in [row] + list(row.winfo_children()):
                w.bind("<Enter>", lambda e, r=row: r.config(bg=Palette.SURFACE_HIGH))
                w.bind("<Leave>", lambda e, r=row: r.config(bg=Palette.SURFACE_LOW))

    def _click(self, label):
        if self._on_navigate:
            self._on_navigate(label)

    def set_active(self, label):
        self._active = label
        for w in self.winfo_children():
            w.destroy()
        self._build()

