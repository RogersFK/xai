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


class ProfilePanel(tk.Toplevel):
    """
    Floating profile panel — opens when avatar is clicked.
    Sections: user info, edit profile, change password.
    """

    def __init__(self, parent, user: dict, on_profile_updated=None):
        super().__init__(parent)
        self._user               = user
        self._on_profile_updated = on_profile_updated

        self.title("My Profile")
        self.configure(bg=Palette.SURFACE)
        self.resizable(False, False)
        self.geometry("420x600")

        # center over parent
        self.transient(parent)
        self.grab_set()

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
                        lambda e: canvas.yview_scroll(
                            int(-1*(e.delta/120)), "units")))
        canvas.bind("<Leave>",
                    lambda e: canvas.unbind_all("<MouseWheel>"))

        self._populate(inner)

    def _populate(self, p):
        u  = self._user
        bg = Palette.SURFACE

        # ── avatar + name header ──────────────────────────────────────
        hdr = tk.Frame(p, bg=Palette.SURFACE_LOW,
                       padx=Palette.PAD_LG, pady=Palette.PAD_LG)
        hdr.pack(fill="x")

        av = tk.Frame(hdr, bg=Palette.SURFACE_HIGHEST,
                      width=52, height=52)
        av.pack(side="left", padx=(0, Palette.PAD_MD))
        av.pack_propagate(False)
        initials = "".join(w[0].upper()
                           for w in u.get("username", "?").split()[:2])
        tk.Label(av, text=initials,
                 font=Palette.bold(Palette.TITLE_MD),
                 fg=Palette.PRIMARY,
                 bg=Palette.SURFACE_HIGHEST).place(
            relx=.5, rely=.5, anchor="center")

        info = tk.Frame(hdr, bg=Palette.SURFACE_LOW)
        info.pack(side="left")

        self._name_lbl = tk.Label(
            info, text=u.get("username", ""),
            font=Palette.bold(Palette.TITLE_LG),
            fg=Palette.ON_SURFACE,
            bg=Palette.SURFACE_LOW)
        self._name_lbl.pack(anchor="w")

        self._email_lbl = tk.Label(
            info, text=u.get("email", ""),
            font=Palette.font(Palette.LABEL),
            fg=Palette.ON_SURFACE_VAR,
            bg=Palette.SURFACE_LOW)
        self._email_lbl.pack(anchor="w")

        # roles
        roles = u.get("roles", [])
        if roles:
            role_names = "  •  ".join(r.get("name", "") for r in roles)
            tk.Label(info, text=role_names,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.PRIMARY,
                     bg=Palette.SURFACE_LOW).pack(anchor="w",
                                                   pady=(4, 0))

        # joined date
        created = (u.get("created_at") or "")[:10]
        tk.Label(hdr, text=f"Joined {created}",
                 font=Palette.font(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW).pack(
            side="right", anchor="ne")

        tk.Frame(p, height=1, bg=Palette.OUTLINE).pack(fill="x")

        # ── edit profile ──────────────────────────────────────────────
        self._section(p, "EDIT PROFILE")

        edit = tk.Frame(p, bg=bg,
                        padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        edit.pack(fill="x")

        tk.Label(edit, text="Username",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(anchor="w", pady=(0, 2))

        self._username_entry = PlaceholderEntry(
            edit, placeholder=u.get("username", ""),
            icon="👤", bg=Palette.SURFACE_HIGHEST)
        self._username_entry.pack(fill="x", ipady=4)

        tk.Frame(edit, height=Palette.PAD_SM,
                 bg=bg).pack()

        tk.Label(edit, text="Email",
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=bg).pack(anchor="w", pady=(0, 2))

        self._email_entry = PlaceholderEntry(
            edit, placeholder=u.get("email", ""),
            icon="✉", bg=Palette.SURFACE_HIGHEST)
        self._email_entry.pack(fill="x", ipady=4)

        tk.Frame(edit, height=Palette.PAD_MD, bg=bg).pack()

        # status label
        self._edit_status = tk.Label(
            edit, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ERROR, bg=bg)
        self._edit_status.pack(anchor="w")

        GoldButton(edit, text="Save Changes",
                   command=self._save_profile).pack(
            fill="x", ipady=6)

        tk.Frame(p, height=1, bg=Palette.OUTLINE).pack(
            fill="x", pady=(Palette.PAD_MD, 0))

        # ── change password ───────────────────────────────────────────
        self._section(p, "CHANGE PASSWORD")

        pw = tk.Frame(p, bg=bg,
                      padx=Palette.PAD_LG, pady=Palette.PAD_MD)
        pw.pack(fill="x")

        for label, attr, placeholder in [
            ("Current Password", "_pw_current", "Enter current password"),
            ("New Password",     "_pw_new",     "Enter new password"),
            ("Confirm New",      "_pw_confirm", "Repeat new password"),
        ]:
            tk.Label(pw, text=label,
                     font=Palette.bold(Palette.MICRO),
                     fg=Palette.ON_SURFACE_VAR,
                     bg=bg).pack(anchor="w", pady=(0, 2))

            entry = PlaceholderEntry(
                pw, placeholder=placeholder,
                show="*", icon="🔒",
                bg=Palette.SURFACE_HIGHEST)
            entry.pack(fill="x", ipady=4)
            setattr(self, attr, entry)

            tk.Frame(pw, height=Palette.PAD_SM, bg=bg).pack()

        # strength bar
        from components import _StrengthBar  # reuse from register
        self._strength = _StrengthBar(pw, bg=bg)
        self._strength.pack(fill="x")
        self._pw_new._entry.bind(
            "<KeyRelease>",
            lambda e: self._strength.update(
                self._pw_new._entry.get()),
            add="+"
        )

        tk.Frame(pw, height=Palette.PAD_SM, bg=bg).pack()

        self._pw_status = tk.Label(
            pw, text="",
            font=Palette.font(Palette.MICRO),
            fg=Palette.ERROR, bg=bg)
        self._pw_status.pack(anchor="w")

        GoldButton(pw, text="Change Password",
                   command=self._change_password).pack(
            fill="x", ipady=6)

        tk.Frame(p, height=Palette.PAD_XL, bg=bg).pack()

    def _section(self, parent, title: str):
        f = tk.Frame(parent, bg=Palette.SURFACE_LOW,
                     padx=Palette.PAD_LG, pady=Palette.PAD_SM)
        f.pack(fill="x")
        tk.Label(f, text=title,
                 font=Palette.bold(Palette.MICRO),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE_LOW).pack(anchor="w")

    # ── save profile ──────────────────────────────────────────────────

    def _save_profile(self):
        new_username = self._username_entry.get().strip()
        new_email    = self._email_entry.get().strip()

        if not new_username and not new_email:
            self._edit_status.config(
                text="Enter a new username or email.",
                fg=Palette.WARNING)
            return

        self._edit_status.config(text="Saving…",
                                  fg=Palette.ON_SURFACE_VAR)

        payload = {}
        if new_username:
            payload["username"] = new_username
        if new_email:
            payload["email"] = new_email

        def do():
            try:
                updated = api("patch", "/auth/me", json=payload)
                self.after(0, lambda: self._on_profile_saved(updated))
            except requests.HTTPError as exc:
                try:
                    msg = exc.response.json().get("detail", "Update failed.")
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

    # ── change password ───────────────────────────────────────────────

    def _change_password(self):
        current = self._pw_current.get()
        new     = self._pw_new.get()
        confirm = self._pw_confirm.get()

        if not current:
            self._pw_status.config(
                text="Enter your current password.",
                fg=Palette.ERROR)
            return
        if not new:
            self._pw_status.config(
                text="Enter a new password.",
                fg=Palette.ERROR)
            return
        if len(new) < 8:
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
        # clear all password fields
        for attr in ("_pw_current", "_pw_new", "_pw_confirm"):
            entry = getattr(self, attr)
            entry._show_placeholder()
        self._strength.update("")
        self._pw_status.config(
            text="✓ Password changed successfully.",
            fg=Palette.SUCCESS)
        log.info("Password changed for: %s",
                 self._user.get("username"))