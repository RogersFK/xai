# ui/profile.py
import tkinter as tk
from tkinter import messagebox
import threading
import requests
from colors import Palette
from components import GoldButton, PlaceholderEntry
from helper import api
from logger import get_logger

log = get_logger("PROFILE")


class ProfilePage(tk.Frame):

    def __init__(self, parent, user: dict = None,
                 on_profile_updated=None, **kw):
        super().__init__(parent, bg=Palette.SURFACE, **kw)
        self._user               = user or {}
        self._on_profile_updated = on_profile_updated
        self._build()

    # ── layout ────────────────────────────────────────────────────────

    def _build(self):
        # scrollable canvas
        canvas = tk.Canvas(self, bg=Palette.SURFACE,
                            highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical",
                           command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=Palette.SURFACE)
        win   = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(
                       scrollregion=canvas.bbox("all")))
        canvas.bind("<Enter>",
                    lambda e: canvas.bind_all(
                        "<MouseWheel>",
                        lambda ev: canvas.yview_scroll(
                            int(-1*(ev.delta/120)), "units")))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        self._populate(inner)

    def _populate(self, p):
        u  = self._user

        # ── page header ───────────────────────────────────────────────
        hdr = tk.Frame(p, bg=Palette.SURFACE)
        hdr.pack(fill="x", padx=Palette.PAD_XL,
                 pady=(Palette.PAD_LG, 0))
        tk.Label(hdr, text="My Profile",
                 font=Palette.bold(Palette.DISPLAY),
                 fg=Palette.ON_SURFACE,
                 bg=Palette.SURFACE).pack(anchor="w")
        tk.Label(hdr,
                 text="Manage your identity and access credentials.",
                 font=Palette.font(Palette.LABEL),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).pack(anchor="w", pady=(2, 0))

        tk.Frame(p, height=Palette.PAD_LG,
                 bg=Palette.SURFACE).pack()

        cols = tk.Frame(p, bg=Palette.SURFACE)
        cols.pack(fill="both", expand=True, padx=Palette.PAD_XL)
        cols.columnconfigure(0, weight=1, uniform="col")   
        cols.columnconfigure(1, weight=1, uniform="col")   
        cols.rowconfigure(0, weight=0)

        # LEFT — identity card + roles
        left = tk.Frame(cols, bg=Palette.SURFACE)
        left.grid(row=0, column=0, sticky="nsew",
                  padx=(0, Palette.PAD_MD))

        self._build_identity_card(left, u)
        tk.Frame(left, height=Palette.PAD_MD,
                 bg=Palette.SURFACE).pack()
        self._build_roles_card(left, u)

        # RIGHT — edit profile + change password
        right = tk.Frame(cols, bg=Palette.SURFACE)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_edit_card(right, u)
        tk.Frame(right, height=Palette.PAD_MD,
                 bg=Palette.SURFACE).pack()
        self._build_password_card(right)

        tk.Frame(p, height=Palette.PAD_XL,
                 bg=Palette.SURFACE).pack()

    # ── identity card ─────────────────────────────────────────────────

    def _build_identity_card(self, parent, u: dict):
        card = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
        card.pack(fill="x")

        # avatar row
        av_row = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                          padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        av_row.pack(fill="x")

        av = tk.Frame(av_row, bg=Palette.PRIMARY,
                      width=56, height=56)
        av.pack(side="left", padx=(0, Palette.PAD_MD))
        av.pack_propagate(False)
        initials = "".join(
            w[0].upper()
            for w in u.get("username", "?").split()[:2]
        ) or "?"
        tk.Label(av, text=initials,
                 font=Palette.bold(Palette.TITLE_LG),
                 fg=Palette.ON_PRIMARY,
                 bg=Palette.PRIMARY).place(relx=.5, rely=.5,
                                            anchor="center")

        info = tk.Frame(av_row, bg=Palette.SURFACE_CONTAINER)
        info.pack(side="left")

        self._name_lbl = tk.Label(
            info, text=u.get("username", ""),
            font=Palette.bold(Palette.HEADLINE_SM),
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_CONTAINER)
        self._name_lbl.pack(anchor="w")

        self._email_lbl = tk.Label(
            info, text=u.get("email", ""),
            font=Palette.font(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_CONTAINER)
        self._email_lbl.pack(anchor="w")

        tk.Label(info,
                 text=f"Joined {(u.get('created_at') or '')[:10]}",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w",
                                                     pady=(4, 0))

        tk.Frame(card, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_LG)

        # detail rows
        detail = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                          padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        detail.pack(fill="x")

        status_color = (Palette.SUCCESS if u.get("is_active")
                        else Palette.ERROR)
        status_text  = "Active" if u.get("is_active") else "Disabled"

        for label, value, color in [
            ("User ID",  str(u.get("id", "")),  Palette.ON_SURFACE),
            ("Status",   status_text,            status_color),
        ]:
            row = tk.Frame(detail, bg=Palette.SURFACE_CONTAINER)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER,
                     width=12, anchor="w").pack(side="left")
            tk.Label(row, text=value,
                     font=Palette.font(Palette.LABEL),
                     fg=color,
                     bg=Palette.SURFACE_CONTAINER).pack(side="left")

    # ── roles card ────────────────────────────────────────────────────

    def _build_roles_card(self, parent, u: dict):
        card = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
        card.pack(fill="x")

        hdr = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                       padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ROLES & PERMISSIONS",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(card, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_LG)

        roles = u.get("roles", [])
        if not roles:
            tk.Label(card, text="No roles assigned.",
                     font=Palette.font(Palette.LABEL),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER).pack(
                pady=Palette.PAD_LG, padx=Palette.PAD_LG,
                anchor="w")
        else:
            for role in roles:
                rframe = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                                   padx=Palette.PAD_LG,
                                   pady=Palette.PAD_SM)
                rframe.pack(fill="x")

                tk.Label(rframe, text=f"● {role.get('name','')}",
                         font=Palette.bold(Palette.LABEL),
                         fg=Palette.PRIMARY,
                         bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

                if role.get("description"):
                    tk.Label(rframe,
                             text=role["description"],
                             font=Palette.font(Palette.MICRO),
                             fg=Palette.ON_SURFACE_VAR,
                             bg=Palette.SURFACE_CONTAINER).pack(
                        anchor="w")

                perms = [p.get("code", "")
                         for p in role.get("permissions", [])]
                # replace the perms section inside _build_roles_card

                if perms:
                    pframe = tk.Frame(rframe, bg=Palette.SURFACE_CONTAINER)
                    pframe.pack(fill="x", pady=(4, 0))

                    # wrap chips across multiple lines using grid
                    col = 0
                    row = 0
                    max_cols = 2                        # chips per row before wrapping
                    for perm in perms:
                        chip = tk.Label(pframe, text=perm,
                                        font=Palette.bold(Palette.MICRO),
                                        fg=Palette.ON_SURFACE_VAR,
                                        bg=Palette.SURFACE_HIGH,
                                        padx=6, pady=2,
                                        wraplength=120)     # ← wrap long permission codes
                        chip.grid(row=row, column=col,
                                padx=(0, Palette.PAD_XS),
                                pady=(0, Palette.PAD_XS),
                                sticky="w")
                        col += 1
                        if col >= max_cols:
                            col = 0
                            row += 1

                tk.Frame(card, height=1,
                         bg=Palette.OUTLINE).pack(
                    fill="x", padx=Palette.PAD_LG)

        tk.Frame(card, height=Palette.PAD_SM,
                 bg=Palette.SURFACE_CONTAINER).pack()

    # ── edit profile card ─────────────────────────────────────────────

    def _build_edit_card(self, parent, u: dict):
        card = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
        card.pack(fill="x")

        hdr = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                       padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="EDIT PROFILE",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(card, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_LG)

        body = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                        padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        body.pack(fill="x")

        # username
        tk.Label(body, text="Username",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", pady=(0, 2))
        self._username_entry = PlaceholderEntry(
            body, placeholder=u.get("username", ""),
            icon="👤", bg=Palette.SURFACE_HIGHEST)
        self._username_entry.pack(fill="x", ipady=4)

        tk.Frame(body, height=Palette.PAD_SM,
                 bg=Palette.SURFACE_CONTAINER).pack()

        # email
        tk.Label(body, text="Email",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(
            anchor="w", pady=(0, 2))
        self._email_entry = PlaceholderEntry(
            body, placeholder=u.get("email", ""),
            icon="✉", bg=Palette.SURFACE_HIGHEST)
        self._email_entry.pack(fill="x", ipady=4)

        tk.Frame(body, height=Palette.PAD_MD,
                 bg=Palette.SURFACE_CONTAINER).pack()

        self._edit_status = tk.Label(
            body, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ERROR,
            bg=Palette.SURFACE_CONTAINER)
        self._edit_status.pack(anchor="w")

        GoldButton(body, text="Save Changes",
                   command=self._save_profile).pack(
            fill="x", ipady=8)

        tk.Frame(card, height=Palette.PAD_MD,
                 bg=Palette.SURFACE_CONTAINER).pack()

    # ── change password card ──────────────────────────────────────────

    def _build_password_card(self, parent):
        card = tk.Frame(parent, bg=Palette.SURFACE_CONTAINER)
        card.pack(fill="x")

        hdr = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                       padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        hdr.pack(fill="x")
        tk.Label(hdr, text="CHANGE PASSWORD",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_CONTAINER).pack(anchor="w")

        tk.Frame(card, height=1,
                 bg=Palette.OUTLINE).pack(fill="x",
                                           padx=Palette.PAD_LG)

        body = tk.Frame(card, bg=Palette.SURFACE_CONTAINER,
                        padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        body.pack(fill="x")

        for label, attr, placeholder in [
            ("Current Password", "_pw_current", "Enter current password"),
            ("New Password",     "_pw_new",     "Enter new password"),
            ("Confirm New",      "_pw_confirm", "Repeat new password"),
        ]:
            tk.Label(body, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=Palette.SURFACE_CONTAINER).pack(
                anchor="w", pady=(0, 2))
            entry = PlaceholderEntry(
                body, placeholder=placeholder,
                show="*", icon="🔒",
                bg=Palette.SURFACE_HIGHEST)
            entry.pack(fill="x", ipady=4)
            setattr(self, attr, entry)
            tk.Frame(body, height=Palette.PAD_SM,
                     bg=Palette.SURFACE_CONTAINER).pack()

        self._pw_status = tk.Label(
            body, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ERROR,
            bg=Palette.SURFACE_CONTAINER)
        self._pw_status.pack(anchor="w")

        GoldButton(body, text="Change Password",
                   command=self._change_password).pack(
            fill="x", ipady=8)

        tk.Frame(card, height=Palette.PAD_MD,
                 bg=Palette.SURFACE_CONTAINER).pack()

    # ── actions ───────────────────────────────────────────────────────

    def _save_profile(self):
        new_username = self._username_entry.get().strip()
        new_email    = self._email_entry.get().strip()

        if not new_username and not new_email:
            self._edit_status.config(
                text="Enter a new username or email.",
                fg=Palette.WARNING)
            return

        payload = {}
        if new_username:
            payload["username"] = new_username
        if new_email:
            payload["email"] = new_email

        self._edit_status.config(text="Saving…",
                                  fg=Palette.ON_SURFACE_VAR)

        def do():
            try:
                updated = api("patch", "/auth/me", json=payload)
                self.after(0, lambda: self._on_profile_saved(updated))
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail",
                                                   "Update failed.")
                except Exception:
                    msg = f"Server error ({exc.response.status_code})"
                self.after(0, lambda: self._edit_status.config(
                    text=msg, fg=Palette.ERROR))
            except requests.ConnectionError:
                self.after(0, lambda: self._edit_status.config(
                    text="Cannot reach server.", fg=Palette.ERROR))

        threading.Thread(target=do, daemon=True).start()

    def _on_profile_saved(self, updated: dict):
        self._user = updated
        self._name_lbl.config(text=updated.get("username", ""))
        self._email_lbl.config(text=updated.get("email", ""))
        self._edit_status.config(
            text="✓ Profile updated successfully.",
            fg=Palette.SUCCESS)
        log.info("Profile updated: %s", updated.get("username"))
        if self._on_profile_updated:
            self._on_profile_updated(updated)

    def _change_password(self):
        current = self._pw_current.get()
        new     = self._pw_new.get()
        confirm = self._pw_confirm.get()

        if not current:
            self._pw_status.config(
                text="Enter your current password.",
                fg=Palette.ERROR)
            return
        if not new or len(new) < 8:
            self._pw_status.config(
                text="Password must be at least 8 characters.",
                fg=Palette.ERROR)
            return
        if new != confirm:
            self._pw_status.config(
                text="Passwords do not match.",
                fg=Palette.ERROR)
            return

        self._pw_status.config(text="Changing…",
                                fg=Palette.ON_SURFACE_VAR)

        def do():
            try:
                api("post", "/auth/me/change-password",
                    json={"current_password": current,
                          "new_password":     new})
                self.after(0, self._on_pw_changed)
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Failed.")
                except Exception:
                    msg = f"Server error ({exc.response.status_code})"
                self.after(0, lambda: self._pw_status.config(
                    text=msg, fg=Palette.ERROR))
            except requests.ConnectionError:
                self.after(0, lambda: self._pw_status.config(
                    text="Cannot reach server.", fg=Palette.ERROR))

        threading.Thread(target=do, daemon=True).start()

    def _on_pw_changed(self):
        for attr in ("_pw_current", "_pw_new", "_pw_confirm"):
            getattr(self, attr)._show_placeholder()
        self._pw_status.config(
            text="✓ Password changed successfully.",
            fg=Palette.SUCCESS)
        log.info("Password changed for: %s",
                 self._user.get("username"))