# ui/admin.py
import tkinter as tk
from tkinter import messagebox
import threading
import requests
from colors import Palette
from components import GoldButton
from helper import api
from logger import get_logger

log = get_logger("ADMIN")


class AdminPage(tk.Frame):

    def __init__(self, parent, user=None, on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._users      = []
        self._roles      = []
        self._sel_user   = None   # currently selected user dict
        self._sel_row    = None   # currently selected row Frame
        self._build()
        self._load()

    # ── layout ───────────────────────────────────────────────────────

    def _build(self):
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # page header
        hdr = tk.Frame(self, bg=Palette.SURFACE,
                       padx=Palette.PAD_XL, pady=Palette.PAD_LG)
        hdr.grid(row=0, column=0, sticky="ew")

        title = tk.Frame(hdr, bg=Palette.SURFACE)
        title.pack(side="left")
        tk.Label(title, text="User Management",
                 font=Palette.bold(Palette.DISPLAY),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(anchor="w")
        tk.Label(title,
                 text="Manage investigators, roles and permissions.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w")

        # refresh button
        GoldButton(hdr, text="Refresh",
                   command=self._load).pack(
            side="right", ipady=4, ipadx=12)

        # body — two columns: table left, detail right
        body = tk.Frame(self, bg=Palette.SURFACE)
        body.grid(row=1, column=0, sticky="nsew",
                  padx=Palette.PAD_XL, pady=(0, Palette.PAD_LG))
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        # LEFT — user table
        self._table_frame = tk.Frame(body, bg=Palette.SURFACE_CONTAINER)
        self._table_frame.grid(row=0, column=0, sticky="nsew",
                                padx=(0, Palette.PAD_MD))
        self._table_frame.rowconfigure(1, weight=1)
        self._table_frame.columnconfigure(0, weight=1)

        self._build_table_header()

        # scrollable rows
        canvas = tk.Canvas(self._table_frame, bg=Palette.SURFACE_CONTAINER,
                            highlightthickness=0)
        sb = tk.Scrollbar(self._table_frame, orient="vertical",
                           command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")
        canvas.grid(row=1, column=0, sticky="nsew")

        self._rows_frame = tk.Frame(canvas, bg=Palette.SURFACE_CONTAINER)
        win = canvas.create_window((0, 0), window=self._rows_frame,
                                    anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        self._rows_frame.bind("<Configure>",
                               lambda e: canvas.configure(
                                   scrollregion=canvas.bbox("all")))

        # status bar below table
        self._table_status = tk.Label(
            self._table_frame, text="Loading…",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER,
            anchor="w", padx=Palette.PAD_MD, pady=Palette.PAD_SM)
        self._table_status.grid(row=2, column=0, columnspan=2, sticky="ew")

        # RIGHT — detail panel
        self._detail = UserDetailPanel(
            body, bg=Palette.SURFACE_CONTAINER,
            on_action=self._on_action)
        self._detail.grid(row=0, column=1, sticky="nsew")

    def _build_table_header(self):
        hdr = tk.Frame(self._table_frame,
                       bg=Palette.SURFACE_LOW,
                       padx=Palette.PAD_MD, pady=Palette.PAD_SM)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")

        for txt, w in [("ID", 4), ("USERNAME", 18), ("EMAIL", 24),
                        ("STATUS", 10), ("CREATED", 14), ("ACTIONS", 16)]:
            tk.Label(hdr, text=txt,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_LOW,
                     width=w, anchor="w").pack(side="left")
            
    # ── data ──────────────────────────────────────────────────────────

    def _load(self):
        self._table_status.config(text="Loading…",
                                   fg=Palette.ON_SURFACE_VAR)
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            users = api("get", "/admin/users")
            roles = api("get", "/admin/roles")
            self.after(0, lambda: self._render(users, roles))
        except requests.HTTPError as exc:
            msg = f"Access denied ({exc.response.status_code})"
            self.after(0, lambda: self._table_status.config(
                text=msg, fg=Palette.ERROR))
        except requests.ConnectionError:
            self.after(0, lambda: self._table_status.config(
                text="Cannot reach server.", fg=Palette.ERROR))

    def _render(self, users: list, roles: list):
        self._users = users
        self._roles = roles

        for w in self._rows_frame.winfo_children():
            w.destroy()

        self._table_status.config(
            text=f"{len(users)} user(s) — click row to manage",
            fg=Palette.ON_SURFACE_VAR)

        for user in users:
            self._add_row(user)

    def _add_row(self, user: dict):
        is_active = user.get("is_active", True)
        bg        = Palette.SURFACE_CONTAINER

        row = tk.Frame(self._rows_frame, bg=bg,
                       padx=Palette.PAD_MD, pady=Palette.PAD_SM,
                       cursor="hand2")
        row.pack(fill="x")

        # ID
        tk.Label(row, text=str(user["id"]),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=4, anchor="w").pack(side="left")

        # username
        tk.Label(row, text=user.get("username", ""),
                 font=Palette.bold(Palette.LABEL),
                 fg=Palette.ON_SURFACE,
                 bg=bg, width=18, anchor="w").pack(side="left")

        # email
        tk.Label(row, text=user.get("email", ""),
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=24, anchor="w").pack(side="left")

        # status chip
        status_color = Palette.SUCCESS if is_active else Palette.ERROR
        status_text  = "ACTIVE" if is_active else "DISABLED"
        tk.Label(row, text=status_text,
                 font=Palette.bold(Palette.MICRO),
                 fg=status_color,
                 bg=bg, width=10, anchor="w").pack(side="left")

        # created
        created = (user.get("created_at") or "")[:10]
        tk.Label(row, text=created,
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg, width=14, anchor="w").pack(side="left")

        # inline action buttons
        actions = tk.Frame(row, bg=bg)
        actions.pack(side="left")

        # activate / deactivate toggle
        if is_active:
            tk.Label(actions, text="Disable",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ERROR,
                     bg=bg, cursor="hand2").pack(
                side="left", padx=(0, Palette.PAD_SM))
        else:
            tk.Label(actions, text="Enable",
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.SUCCESS,
                     bg=bg, cursor="hand2").pack(
                side="left", padx=(0, Palette.PAD_SM))

        # bind click on whole row → select user in detail panel
        for w in [row] + list(row.winfo_children()):
            w.bind("<Button-1>",
                   lambda e, u=user, r=row: self._select_user(u, r))
            w.bind("<Enter>",
                   lambda e, r=row: self._set_row_bg(
                       r, Palette.SURFACE_HIGH))
            w.bind("<Leave>",
                   lambda e, r=row: self._set_row_bg(
                       r, Palette.SURFACE_CONTAINER))

        # bind the action label separately
        for child in actions.winfo_children():
            child.bind("<Button-1>",
                       lambda e, u=user: self._toggle_active(u))

        # separator
        tk.Frame(self._rows_frame, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_MD)

    def _set_row_bg(self, row, color):
        row.config(bg=color)
        for w in row.winfo_children():
            try:
                w.config(bg=color)
            except Exception:
                pass

    def _select_user(self, user: dict, row: tk.Frame):
        # deselect previous
        if self._sel_row:
            self._set_row_bg(self._sel_row, Palette.SURFACE_CONTAINER)

        self._sel_user = user
        self._sel_row  = row
        self._set_row_bg(row, Palette.SURFACE_HIGH)
        self._detail.load(user, self._roles)        
        
        
    # ── actions ───────────────────────────────────────────────────────

    def _on_action(self, action: str, payload: dict):
        """Called by UserDetailPanel for any action."""
        dispatch = {
            "reset_password": self._reset_password,
            "assign_role":    self._assign_role,
            "remove_role":    self._remove_role,
        }
        fn = dispatch.get(action)
        if fn:
            fn(payload)

    def _toggle_active(self, user: dict):
        uid       = user["id"]
        is_active = user.get("is_active", True)
        action    = "deactivate" if is_active else "activate"

        confirmed = messagebox.askyesno(
            f"{'Disable' if is_active else 'Enable'} User",
            f"{'Disable' if is_active else 'Enable'} "
            f"{user['username']}?"
        )
        if not confirmed:
            return

        def do():
            try:
                api("patch",
                    f"/admin/users/{uid}/activate"
                    f"?is_active={'false' if is_active else 'true'}")
                self.after(0, self._load)
            except requests.HTTPError as exc:
                msg = (exc.response.json().get("detail", "Failed.")
                       if exc.response else "Failed.")
                self.after(0, lambda: messagebox.showerror("Error", msg))

        threading.Thread(target=do, daemon=True).start()

    def _reset_password(self, payload: dict):
        uid      = payload["user_id"]
        username = payload["username"]
        new_pw   = payload["password"]

        if not new_pw:
            messagebox.showwarning("Required", "Enter a new password.")
            return

        confirmed = messagebox.askyesno(
            "Reset Password",
            f"Reset password for {username}?"
        )
        if not confirmed:
            return

        def do():
            try:
                api("patch",
                    f"/admin/users/{uid}/reset-password",
                    json={"new_password": new_pw})
                self.after(0, lambda: messagebox.showinfo(
                    "Done", f"Password reset for {username}."))
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Error {exc.response.status_code}"
                self.after(0, lambda: messagebox.showerror("Error", msg))

        threading.Thread(target=do, daemon=True).start()

    def _assign_role(self, payload: dict):
        uid     = payload["user_id"]
        role_id = payload["role_id"]

        def do():
            try:
                api("post",
                    f"/admin/users/{uid}/roles/{role_id}")
                self.after(0, self._load)
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Error {exc.response.status_code}"
                self.after(0, lambda: messagebox.showerror("Error", msg))

        threading.Thread(target=do, daemon=True).start()

    def _remove_role(self, payload: dict):
        uid     = payload["user_id"]
        role_id = payload["role_id"]

        def do():
            try:
                api("delete",
                    f"/admin/users/{uid}/roles/{role_id}")
                self.after(0, self._load)
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Error {exc.response.status_code}"
                self.after(0, lambda: messagebox.showerror("Error", msg))

        threading.Thread(target=do, daemon=True).start()


# ── User Detail Panel ─────────────────────────────────────────────────

class UserDetailPanel(tk.Frame):
    """
    Right-side panel — shows full user detail and action controls
    when a row is clicked.
    """

    def __init__(self, parent, on_action=None, **kw):
        bg = kw.pop("bg", Palette.SURFACE_CONTAINER)
        super().__init__(parent, bg=bg, **kw)
        self._bg        = bg
        self._on_action = on_action
        self._user      = None
        self._roles     = []
        self._pw_var    = tk.StringVar()
        self._build_empty()

    def _build_empty(self):
        tk.Label(self, text="Select a user\nto manage.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=self._bg,
                 justify="center").place(relx=0.5, rely=0.5,
                                          anchor="center")

    def load(self, user: dict, roles: list):
        self._user  = user
        self._roles = roles
        for w in self.winfo_children():
            w.destroy()
        self._build_detail()

    def _build_detail(self):
        u  = self._user
        bg = self._bg

        # scroll wrapper
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb     = tk.Scrollbar(self, orient="vertical",
                               command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=bg)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))

        p = inner   # shorthand

        info = tk.Frame(p, bg=bg, padx=Palette.PAD_MD,
                        pady=Palette.PAD_MD)
        info.pack(fill="x")

        tk.Label(info, text="USER DETAIL",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(anchor="w")

        tk.Frame(info, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           pady=(Palette.PAD_SM, Palette.PAD_MD))

        for label, value in [
            ("ID",       str(u.get("id", ""))),
            ("Username", u.get("username", "")),
            ("Email",    u.get("email", "")),
            ("Status",   "Active" if u.get("is_active") else "Disabled"),
            ("Created",  (u.get("created_at") or "")[:10]),
        ]:
            row = tk.Frame(info, bg=bg)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg, width=10, anchor="w").pack(side="left")
            color = (Palette.SUCCESS if value == "Active"
                     else Palette.ERROR if value == "Disabled"
                     else Palette.ON_SURFACE)
            tk.Label(row, text=value,
                     font=Palette.font(Palette.LABEL),
                     fg=color, bg=bg,
                     anchor="w").pack(side="left")

        tk.Frame(p, height=1, bg=Palette.OUTLINE).pack(
            fill="x", padx=Palette.PAD_MD)

   
        roles_frame = tk.Frame(p, bg=bg,
                                padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        roles_frame.pack(fill="x")

        tk.Label(roles_frame, text="ROLES",
                font=Palette.bold(Palette.MICRO),
                fg=Palette.ON_SURFACE_VAR,
                bg=bg).pack(anchor="w", pady=(0, Palette.PAD_SM))

        user_roles    = u.get("roles", [])
        user_role_ids = {r["id"] for r in user_roles}

     
        if not user_roles:
            tk.Label(roles_frame,
                    text="No roles assigned.",
                    font=Palette.font(Palette.MICRO),
                    fg=Palette.ON_SURFACE_VAR,
                    bg=bg).pack(anchor="w")
        else:
            for role in user_roles:
                rid  = role["id"]
                name = role.get("name", "")

                rrow = tk.Frame(roles_frame, bg=Palette.SURFACE_HIGH,
                                padx=Palette.PAD_SM, pady=Palette.PAD_SM)
                rrow.pack(fill="x", pady=2)

                # ── 1. pack RIGHT items FIRST ─────────────────────────────
                def _remove(e, role_id=rid, uid=u["id"]):
                    if self._on_action:
                        self._on_action("remove_role",
                                        {"user_id": uid, "role_id": role_id})

                rm_lbl = tk.Label(rrow, text="✕ Remove",
                                font=Palette.bold(Palette.MICRO),
                                fg=Palette.ERROR,
                                bg=Palette.SURFACE_HIGH,
                                cursor="hand2")
                rm_lbl.pack(side="right", padx=(Palette.PAD_SM, 0))  # ← FIRST
                rm_lbl.bind("<Button-1>", _remove)
                rm_lbl.bind("<Enter>",
                            lambda e, l=rm_lbl: l.config(fg=Palette.WARNING))
                rm_lbl.bind("<Leave>",
                            lambda e, l=rm_lbl: l.config(fg=Palette.ERROR))

                # ── 2. then LEFT items ────────────────────────────────────
                tk.Label(rrow, text=f"● {name}",
                        font=Palette.bold(Palette.MICRO),
                        fg=Palette.PRIMARY,
                        bg=Palette.SURFACE_HIGH).pack(side="left")

                perms = [rp.get("code", "")
                        for rp in role.get("permissions", [])]
                if perms:
                    tk.Label(rrow,
                            text="  •  ".join(perms),
                            font=Palette.font(Palette.MICRO),
                            fg=Palette.ON_SURFACE_VAR,
                            bg=Palette.SURFACE_HIGH).pack(
                        side="left", padx=(Palette.PAD_SM, 0))
                # ── remove button — use default arg to capture rid ───────
                def _remove(e, role_id=rid, uid=u["id"]):
                    if self._on_action:
                        self._on_action("remove_role",
                                        {"user_id": uid,
                                        "role_id": role_id})

                rm_lbl = tk.Label(rrow, text="  ✕ Remove",
                                font=Palette.bold(Palette.MICRO),
                                fg=Palette.ERROR,
                                bg=Palette.SURFACE_HIGH,
                                cursor="hand2")
                rm_lbl.pack(side="right")
                rm_lbl.bind("<Button-1>", _remove)

                # hover on remove label only
                rm_lbl.bind("<Enter>",
                            lambda e, l=rm_lbl: l.config(fg=Palette.PRIMARY))
                rm_lbl.bind("<Leave>",
                            lambda e, l=rm_lbl: l.config(fg=Palette.ERROR))

        # ── assign role ───────────────────────────────────────────────
        assign_frame = tk.Frame(p, bg=bg,
                                 padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        assign_frame.pack(fill="x")

        tk.Label(assign_frame, text="ASSIGN ROLE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(anchor="w",
                              pady=(0, Palette.PAD_SM))

        # roles not yet assigned to this user
        from tkinter import ttk
        available = [r for r in self._roles
                     if r["id"] not in user_role_ids]

        if not available:
            tk.Label(assign_frame,
                     text="All roles already assigned.",
                     font=Palette.font(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg).pack(anchor="w")
        else:
            role_var = tk.StringVar()
            role_map = {r["name"]: r["id"] for r in available}

            cb = ttk.Combobox(assign_frame,
                               textvariable=role_var,
                               values=list(role_map.keys()),
                               state="readonly",
                               font=Palette.font(Palette.BODY_MD))
            cb.pack(fill="x", pady=(0, Palette.PAD_SM))
            cb.current(0)

            def _do_assign():
                name    = role_var.get()
                role_id = role_map.get(name)
                if role_id and self._on_action:
                    self._on_action("assign_role",
                                    {"user_id": u["id"],
                                     "role_id": role_id})

            GoldButton(assign_frame, text="Assign Role",
                       command=_do_assign).pack(
                fill="x", ipady=4)

        tk.Frame(p, height=1, bg=Palette.OUTLINE).pack(
            fill="x", padx=Palette.PAD_MD, pady=(Palette.PAD_SM, 0))

        # ── reset password ────────────────────────────────────────────
        pw_frame = tk.Frame(p, bg=bg,
                             padx=Palette.PAD_MD, pady=Palette.PAD_MD)
        pw_frame.pack(fill="x")

        tk.Label(pw_frame, text="RESET PASSWORD",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(anchor="w",
                              pady=(0, Palette.PAD_SM))

        from components import PlaceholderEntry
        pw_entry = PlaceholderEntry(
            pw_frame,
            placeholder="New password",
            show="*", icon="🔒",
            bg=Palette.SURFACE_HIGHEST
        )
        pw_entry.pack(fill="x", ipady=4,
                       pady=(0, Palette.PAD_SM))

        def _do_reset():
            if self._on_action:
                self._on_action("reset_password", {
                    "user_id":  u["id"],
                    "username": u["username"],
                    "password": pw_entry.get(),
                })

        GoldButton(pw_frame, text="Reset Password",
                   command=_do_reset).pack(fill="x", ipady=4)

        tk.Frame(p, height=Palette.PAD_LG, bg=bg).pack()    