
import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional
import requests

API = "http://127.0.0.1:8000"

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#0d0d14"
PANEL    = "#13131e"
CARD     = "#1a1a28"
BORDER   = "#252538"
ACCENT   = "#00d4aa"       # teal-green
ACCENT2  = "#00a87f"
WARN     = "#f0a500"
ERROR    = "#e05c5c"
SUCCESS  = "#00d4aa"
TEXT     = "#dce3f0"
MUTED    = "#5a607a"
SUBTLE   = "#2a2a40"

SEVERITY_COLOR = {"info": "#4a9eff", "warning": WARN, "critical": ERROR, "unknown": MUTED}

# ── Fonts (pure Tk — no external downloads needed) ───────────────────────────
F_TITLE  = ("Georgia",    22, "bold")
F_HEAD   = ("Georgia",    14, "bold")
F_LABEL  = ("Courier",    9)
F_BODY   = ("Courier",    10)
F_BTN    = ("Helvetica",  10, "bold")
F_SMALL  = ("Helvetica",  8)
F_MONO   = ("Courier",    9)


# ══════════════════════════════════════════════════════════════════════════════
# Reusable widget helpers
# ══════════════════════════════════════════════════════════════════════════════

def _entry(parent, show=None, width=30):
    e = tk.Entry(
        parent, bg=CARD, fg=TEXT, insertbackground=ACCENT,
        relief="flat", font=F_BODY, width=width,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT, show=show or "",
    )
    return e


def _btn(parent, text, cmd, color=ACCENT, fg="black", width=None):
    kw = dict(width=width) if width else {}
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=color, fg=fg, activebackground=ACCENT2,
        activeforeground="black", relief="flat",
        font=F_BTN, cursor="hand2", padx=12, pady=6, **kw,
    )
    b.bind("<Enter>", lambda e: b.config(bg=ACCENT2))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def _lbl(parent, text, fg=TEXT, font=F_BODY, bg=None, **kw):
    return tk.Label(parent, text=text, fg=fg, font=font,
                    bg=bg or parent["bg"], **kw)


def _sep(parent):
    return tk.Frame(parent, height=1, bg=BORDER)


def _card(parent, **kw):
    return tk.Frame(parent, bg=CARD, highlightthickness=1,
                    highlightbackground=BORDER, **kw)


def _scrolled_text(parent, height=12):
    frame = tk.Frame(parent, bg=CARD)
    sb = tk.Scrollbar(frame)
    sb.pack(side="right", fill="y")
    t = tk.Text(
        frame, bg=CARD, fg=TEXT, font=F_MONO,
        relief="flat", wrap="word", height=height,
        yscrollcommand=sb.set, state="disabled",
        selectbackground=SUBTLE, padx=8, pady=6,
    )
    t.pack(side="left", fill="both", expand=True)
    sb.config(command=t.yview)
    return frame, t


def _set_text(widget, content):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", content)
    widget.config(state="disabled")


# ══════════════════════════════════════════════════════════════════════════════
# API helpers  (all run on background threads)
# ══════════════════════════════════════════════════════════════════════════════

def api(method, path, **kw):
    """Thin wrapper; raises requests.RequestException on network errors."""
    url = f"{API}{path}"
    r = getattr(requests, method)(url, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


# ══════════════════════════════════════════════════════════════════════════════
# Base screen
# ══════════════════════════════════════════════════════════════════════════════

class Screen(tk.Frame):
    """Every screen inherits this. `app` is the root App instance."""
    def __init__(self, app: "App"):
        super().__init__(app, bg=BG)
        self.app = app

    def destroy_and(self, next_screen_fn):
        self.destroy()
        next_screen_fn()


# ══════════════════════════════════════════════════════════════════════════════
# Login Screen
# ══════════════════════════════════════════════════════════════════════════════

class LoginScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self._build()
        self.pack(expand=True, fill="both")

    def _build(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        _lbl(wrap, "◈  LogAnalyzer", fg=ACCENT, font=("Georgia", 28, "bold"), bg=BG).pack(pady=(0, 4))
        _lbl(wrap, "AI-powered log intelligence platform", fg=MUTED, font=F_SMALL, bg=BG).pack(pady=(0, 30))

        box = _card(wrap)
        box.pack(ipadx=30, ipady=24)

        _lbl(box, "SIGN IN", fg=ACCENT, font=("Courier", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 2))
        _sep(box).pack(fill="x", padx=20, pady=(0, 18))

        for label, attr, show in [("USERNAME", "e_user", None), ("PASSWORD", "e_pass", "•")]:
            _lbl(box, label, fg=MUTED, font=("Courier", 8), bg=CARD).pack(anchor="w", padx=20)
            e = _entry(box, show=show)
            e.pack(padx=20, pady=(2, 12), fill="x", ipady=5)
            setattr(self, attr, e)

        self.e_pass.bind("<Return>", lambda _: self._login())

        self.status = _lbl(box, "", fg=ERROR, font=F_SMALL, bg=CARD, wraplength=280)
        self.status.pack(padx=20)

        self.btn = _btn(box, "Sign In →", self._login)
        self.btn.pack(fill="x", padx=20, pady=(10, 8), ipady=2)

        _sep(box).pack(fill="x", padx=20, pady=(4, 12))
        link = _lbl(box, "New here? Create an account", fg=ACCENT, font=("Courier", 9, "underline"), bg=CARD, cursor="hand2")
        link.pack(pady=(0, 20))
        link.bind("<Button-1>", lambda _: self.app.show_register())

    def _login(self):
        u, p = self.e_user.get().strip(), self.e_pass.get()
        if not u or not p:
            self.status.config(text="Please fill both fields.")
            return
        self.btn.config(state="disabled", text="Signing in…")
        self.status.config(text="")
        threading.Thread(target=self._do, args=(u, p), daemon=True).start()

    def _do(self, u, p):
        try:
            user = api("post", "/auth/login", json={"username": u, "password": p})
            self.after(0, lambda: self.app.show_dashboard(user['user']))
        except requests.HTTPError as e:
            try:
                msg = e.response.json().get("detail", "Login failed.")
            except Exception:
                msg = f"Server error ({e.response.status_code})"
            self.after(0, lambda: self.status.config(text=msg))
        except requests.ConnectionError:
            self.after(0, lambda: self.status.config(text="Cannot reach server."))
        finally:
            self.after(0, lambda: self.btn.config(state="normal", text="Sign In →"))


# ══════════════════════════════════════════════════════════════════════════════
# Register Screen
# ══════════════════════════════════════════════════════════════════════════════

class RegisterScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self._build()
        self.pack(expand=True, fill="both")

    def _build(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        _lbl(wrap, "◈  LogAnalyzer", fg=ACCENT, font=("Georgia", 28, "bold"), bg=BG).pack(pady=(0, 4))
        _lbl(wrap, "Create your account", fg=MUTED, font=F_SMALL, bg=BG).pack(pady=(0, 30))

        box = _card(wrap)
        box.pack(ipadx=30, ipady=24)

        _lbl(box, "REGISTER", fg=ACCENT, font=("Courier", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 2))
        _sep(box).pack(fill="x", padx=20, pady=(0, 18))

        fields = [("USERNAME", "e_user", None), ("EMAIL", "e_email", None),
                  ("PASSWORD", "e_pass", "•"), ("CONFIRM PASSWORD", "e_conf", "•")]
        for label, attr, show in fields:
            _lbl(box, label, fg=MUTED, font=("Courier", 8), bg=CARD).pack(anchor="w", padx=20)
            e = _entry(box, show=show)
            e.pack(padx=20, pady=(2, 10), fill="x", ipady=5)
            setattr(self, attr, e)

        self.status = _lbl(box, "", fg=ERROR, font=F_SMALL, bg=CARD, wraplength=280)
        self.status.pack(padx=20)

        self.btn = _btn(box, "Create Account", self._submit, color="#1a6e58")
        self.btn.pack(fill="x", padx=20, pady=(10, 8), ipady=2)

        _sep(box).pack(fill="x", padx=20, pady=(4, 12))
        link = _lbl(box, "Already have an account? Sign in", fg=ACCENT, font=("Courier", 9, "underline"), bg=CARD, cursor="hand2")
        link.pack(pady=(0, 20))
        link.bind("<Button-1>", lambda _: self.app.show_login())

    def _submit(self):
        u  = self.e_user.get().strip()
        em = self.e_email.get().strip()
        p  = self.e_pass.get()
        c  = self.e_conf.get()
        if not all([u, em, p, c]):
            self.status.config(text="Please fill all fields.")
            return
        if p != c:
            self.status.config(text="Passwords do not match.")
            return
        self.btn.config(state="disabled", text="Creating…")
        threading.Thread(target=self._do, args=(u, em, p), daemon=True).start()

    def _do(self, u, em, p):
        try:
            api("post", "/auth/register", json={"username": u, "email": em, "password": p})
            self.after(0, lambda: [
                self.status.config(text="Account created! Redirecting…", fg=SUCCESS),
                self.after(1200, self.app.show_login),
            ])
        except requests.HTTPError as e:
            try:
                msg = e.response.json().get("detail", "Registration failed.")
            except Exception:
                msg = f"Server error ({e.response.status_code})"
            self.after(0, lambda: self.status.config(text=msg, fg=ERROR))
        except requests.ConnectionError:
            self.after(0, lambda: self.status.config(text="Cannot reach server.", fg=ERROR))
        finally:
            self.after(0, lambda: self.btn.config(state="normal", text="Create Account"))


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard Screen
# ══════════════════════════════════════════════════════════════════════════════

class DashboardScreen(Screen):
    def __init__(self, app, user: dict):
        super().__init__(app)
        self.user = user
        self._files: list[dict] = []
        self._build()
        self.pack(expand=True, fill="both")
        self._load_files()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Top bar
        bar = tk.Frame(self, bg=PANEL, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        _lbl(bar, "◈  LogAnalyzer", fg=ACCENT, font=("Georgia", 14, "bold"), bg=PANEL).pack(side="left", padx=20)
        _lbl(bar, f"  {self.user['username']}", fg=MUTED, font=F_SMALL, bg=PANEL).pack(side="left")
        _btn(bar, "Logout", self.app.show_login, color=SUBTLE, fg=MUTED).pack(side="right", padx=16, pady=10)
        _btn(bar, "+ Upload Log", self._open_upload, color=ACCENT, fg="black").pack(side="right", padx=4, pady=10)

        # Body split
        body = tk.Frame(self, bg=BG)
        body.pack(expand=True, fill="both", padx=20, pady=16)

        # Left: file list
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        _lbl(left, "LOG FILES", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 8))

        self.file_frame = tk.Frame(left, bg=BG)
        self.file_frame.pack(fill="both", expand=True)

        self.empty_lbl = _lbl(self.file_frame, "No log files yet.\nClick '+ Upload Log' to get started.",
                               fg=MUTED, font=F_BODY, bg=BG, justify="center")

        # Right: stats sidebar
        right = tk.Frame(body, bg=BG, width=200)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        _lbl(right, "ACCOUNT", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 8))
        info = _card(right)
        info.pack(fill="x")

        for label, val in [
            ("User ID",  str(self.user["id"])),
            ("Username", self.user["username"]),
            ("Email",    self.user["email"]),
            ("Member",   self.user["created_at"][:10]),
        ]:
            row = tk.Frame(info, bg=CARD)
            row.pack(anchor="w", padx=12, pady=3)
            _lbl(row, f"{label}: ", fg=MUTED, font=("Courier", 8), bg=CARD).pack(side="left")
            _lbl(row, val, fg=TEXT, font=("Courier", 8, "bold"), bg=CARD).pack(side="left")

        _lbl(right, "", bg=BG).pack(pady=8)
        _lbl(right, "STATS", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 8))
        self.stats_card = _card(right)
        self.stats_card.pack(fill="x")
        self.stat_files = self._stat_row(self.stats_card, "Files uploaded", "—")
        self.stat_analyses = self._stat_row(self.stats_card, "Analyses run", "—")

    def _stat_row(self, parent, label, value):
        row = tk.Frame(parent, bg=CARD)
        row.pack(anchor="w", padx=12, pady=4)
        _lbl(row, f"{label}: ", fg=MUTED, font=("Courier", 8), bg=CARD).pack(side="left")
        v = _lbl(row, value, fg=ACCENT, font=("Courier", 9, "bold"), bg=CARD)
        v.pack(side="left")
        return v

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_files(self):
        threading.Thread(target=self._fetch_files, daemon=True).start()

    def _fetch_files(self):
        try:
            files = api("get", f"/logs/?user_id={self.user['id']}")
            self.after(0, lambda: self._render_files(files))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _render_files(self, files: list):
        self._files = files
        for w in self.file_frame.winfo_children():
            w.destroy()

        total_analyses = sum(f.get("analysis_count", 0) for f in files)
        self.stat_files.config(text=str(len(files)))
        self.stat_analyses.config(text=str(total_analyses))

        if not files:
            self.empty_lbl = _lbl(self.file_frame,
                                   "No log files yet.\nClick '+ Upload Log' to get started.",
                                   fg=MUTED, font=F_BODY, bg=BG, justify="center")
            self.empty_lbl.pack(expand=True, pady=60)
            return

        # Scrollable list
        canvas = tk.Canvas(self.file_frame, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self.file_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for f in files:
            self._file_card(inner, f).pack(fill="x", pady=4)

    def _file_card(self, parent, f: dict):
        card = _card(parent)
        card.pack_configure(fill="x")

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=14, pady=(12, 4))

        _lbl(top, f["original_name"], fg=TEXT, font=("Courier", 10, "bold"), bg=CARD).pack(side="left")
        size_kb = f["file_size"] // 1024
        _lbl(top, f"{size_kb} KB", fg=MUTED, font=F_SMALL, bg=CARD).pack(side="right")

        bot = tk.Frame(card, bg=CARD)
        bot.pack(fill="x", padx=14, pady=(0, 10))

        uploaded = f["uploaded_at"][:16].replace("T", " ")
        _lbl(bot, f"Uploaded {uploaded}", fg=MUTED, font=F_SMALL, bg=CARD).pack(side="left")

        ac = f.get("analysis_count", 0)
        _lbl(bot, f"{ac} analysis{'es' if ac != 1 else ''}", fg=ACCENT if ac else MUTED,
             font=F_SMALL, bg=CARD).pack(side="left", padx=12)

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(0, 12))

        _btn(btn_row, "Analyse", lambda fid=f["id"]: self.app.show_analysis(self.user, fid),
             color=ACCENT, fg="black").pack(side="left", padx=(0, 6))
        _btn(btn_row, "Delete", lambda fid=f["id"]: self._delete_file(fid),
             color="#3a1a1a", fg=ERROR).pack(side="left")

        return card

    def _delete_file(self, file_id: int):
        if not messagebox.askyesno("Delete", "Delete this log file and all its analyses?"):
            return
        threading.Thread(target=self._do_delete, args=(file_id,), daemon=True).start()

    def _do_delete(self, file_id: int):
        try:
            requests.delete(f"{API}/logs/{file_id}?user_id={self.user['id']}", timeout=10)
            self.after(0, self._load_files)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    # ── Upload dialog ─────────────────────────────────────────────────────────
    def _open_upload(self):
        path = filedialog.askopenfilename(
            title="Select a log file",
            filetypes=[("Log files", "*.log *.txt *.csv *.json *.gz"), ("All files", "*.*")],
        )
        if not path:
            return
        self.app.show_upload(self.user, path, on_done=self._load_files)


# ══════════════════════════════════════════════════════════════════════════════
# Upload Screen  (progress + confirmation)
# ══════════════════════════════════════════════════════════════════════════════

class UploadScreen(Screen):
    def __init__(self, app, user: dict, file_path: str, on_done):
        super().__init__(app)
        self.user = user
        self.file_path = file_path
        self.on_done = on_done
        self._build()
        self.pack(expand=True, fill="both")
        self.after(300, self._upload)

    def _build(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        _lbl(wrap, "Uploading File", fg=TEXT, font=F_HEAD, bg=BG).pack(pady=(0, 10))
        fname = os.path.basename(self.file_path)
        _lbl(wrap, fname, fg=MUTED, font=F_SMALL, bg=BG).pack(pady=(0, 20))

        self.pb = ttk.Progressbar(wrap, mode="indeterminate", length=320)
        self.pb.pack(pady=(0, 16))
        self.pb.start(12)

        self.status = _lbl(wrap, "Uploading…", fg=ACCENT, font=F_BODY, bg=BG)
        self.status.pack()

    def _upload(self):
        threading.Thread(target=self._do_upload, daemon=True).start()

    def _do_upload(self):
        try:
            with open(self.file_path, "rb") as fh:
                fname = os.path.basename(self.file_path)
                r = requests.post(
                    f"{API}/logs/upload?user_id={self.user['id']}",
                    files={"file": (fname, fh)},
                    timeout=60,
                )
                r.raise_for_status()
            self.after(0, self._done_ok)
        except requests.HTTPError as e:
            msg = e.response.json().get("detail", "Upload failed.")
            self.after(0, lambda: self._done_err(msg))
        except Exception as e:
            self.after(0, lambda: self._done_err(str(e)))

    def _done_ok(self):
        self.pb.stop()
        self.status.config(text="✓  Upload successful!", fg=SUCCESS)
        self.after(900, lambda: [self.on_done(), self.app.show_dashboard(self.user)])

    def _done_err(self, msg):
        self.pb.stop()
        self.status.config(text=f"Error: {msg}", fg=ERROR)
        self.after(2000, lambda: self.app.show_dashboard(self.user))


# ══════════════════════════════════════════════════════════════════════════════
# Analysis Screen  — list analyses for a file, trigger new one
# ══════════════════════════════════════════════════════════════════════════════

class AnalysisScreen(Screen):
    def __init__(self, app, user: dict, file_id: int):
        super().__init__(app)
        self.user = user
        self.file_id = file_id
        self._build()
        self.pack(expand=True, fill="both")
        self._load()

    def _build(self):
        # Top bar
        bar = tk.Frame(self, bg=PANEL, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        _btn(bar, "← Back", lambda: self.app.show_dashboard(self.user),
             color=SUBTLE, fg=MUTED).pack(side="left", padx=16, pady=10)
        _lbl(bar, "Log Analyses", fg=TEXT, font=F_HEAD, bg=PANEL).pack(side="left", padx=8)

        # Prompt row
        prompt_row = tk.Frame(self, bg=BG)
        prompt_row.pack(fill="x", padx=20, pady=14)

        _lbl(prompt_row, "Custom instruction (optional):", fg=MUTED, font=F_SMALL, bg=BG).pack(side="left", padx=(0, 8))
        self.prompt_entry = _entry(prompt_row, width=50)
        self.prompt_entry.pack(side="left", ipady=4, padx=(0, 10))
        self.run_btn = _btn(prompt_row, "▶ Run Analysis", self._run_analysis)
        self.run_btn.pack(side="left")
        self.run_status = _lbl(prompt_row, "", fg=MUTED, font=F_SMALL, bg=BG)
        self.run_status.pack(side="left", padx=12)

        _sep(self).pack(fill="x", padx=20)

        # Analysis list
        _lbl(self, "PREVIOUS ANALYSES", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", padx=20, pady=(12, 6))
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _load(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rows = api("get", f"/analyses/file/{self.file_id}?user_id={self.user['id']}")
            self.after(0, lambda: self._render(rows))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _render(self, rows: list):
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not rows:
            _lbl(self.list_frame, "No analyses yet — run one above!", fg=MUTED, font=F_BODY, bg=BG).pack(pady=40)
            return

        canvas = tk.Canvas(self.list_frame, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self.list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for row in rows:
            self._analysis_row(inner, row).pack(fill="x", pady=4)

    def _analysis_row(self, parent, a: dict):
        sev = a.get("severity", "unknown")
        sev_color = SEVERITY_COLOR.get(sev, MUTED)
        card = _card(parent)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=14, pady=(10, 4))

        # Severity badge
        badge = tk.Label(top, text=f" {sev.upper()} ", bg=sev_color,
                         fg="black", font=("Courier", 8, "bold"), padx=4)
        badge.pack(side="left", padx=(0, 10))

        ts = a.get("created_at", "")[:16].replace("T", " ")
        _lbl(top, ts, fg=MUTED, font=F_SMALL, bg=CARD).pack(side="left")

        status = a.get("status", "")
        st_color = SUCCESS if status == "done" else (ERROR if status == "error" else WARN)
        _lbl(top, status.upper(), fg=st_color, font=("Courier", 8, "bold"), bg=CARD).pack(side="right")

        summary = a.get("summary", "")[:120] + ("…" if len(a.get("summary", "")) > 120 else "")
        _lbl(card, summary, fg=TEXT, font=("Courier", 9), bg=CARD, wraplength=600, justify="left").pack(
            anchor="w", padx=14, pady=(0, 6))

        meta = tk.Frame(card, bg=CARD)
        meta.pack(fill="x", padx=14, pady=(0, 10))

        model = a.get("ai_model", "")
        tokens = a.get("tokens_used", 0)
        dur = a.get("duration_sec", 0)
        anomaly_count = len(json.loads(a.get("anomalies", "[]")))
        pattern_count = len(json.loads(a.get("patterns", "[]")))

        for txt in [f"model: {model}", f"{tokens} tokens", f"{dur}s",
                    f"{anomaly_count} anomalies", f"{pattern_count} patterns"]:
            _lbl(meta, txt, fg=MUTED, font=("Courier", 8), bg=CARD).pack(side="left", padx=(0, 14))

        _btn(meta, "View Detail →", lambda aid=a["id"]: self.app.show_detail(self.user, aid),
             color=SUBTLE, fg=ACCENT).pack(side="right")

        return card

    def _run_analysis(self):
        prompt = self.prompt_entry.get().strip()
        self.run_btn.config(state="disabled", text="Running…")
        self.run_status.config(text="Sending to AI…", fg=WARN)
        threading.Thread(target=self._do_run, args=(prompt,), daemon=True).start()

    def _do_run(self, prompt: str):
        try:
            api("post", f"/analyses/run?user_id={self.user['id']}",
                json={"log_file_id": self.file_id, "user_prompt": prompt})
            self.after(0, lambda: [
                self.run_status.config(text="✓ Analysis complete!", fg=SUCCESS),
                self._load(),
            ])
        except requests.HTTPError as e:
            msg = e.response.json().get("detail", "Analysis failed.")
            self.after(0, lambda: self.run_status.config(text=f"Error: {msg}", fg=ERROR))
        except Exception as e:
            self.after(0, lambda: self.run_status.config(text=str(e), fg=ERROR))
        finally:
            self.after(0, lambda: self.run_btn.config(state="normal", text="▶ Run Analysis"))


# ══════════════════════════════════════════════════════════════════════════════
# Detail Screen  — full analysis result
# ══════════════════════════════════════════════════════════════════════════════

class DetailScreen(Screen):
    def __init__(self, app, user: dict, analysis_id: int):
        super().__init__(app)
        self.user = user
        self.analysis_id = analysis_id
        self._build()
        self.pack(expand=True, fill="both")
        self._load()

    def _build(self):
        bar = tk.Frame(self, bg=PANEL, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        _btn(bar, "← Back", lambda: self.app.history_back(),
             color=SUBTLE, fg=MUTED).pack(side="left", padx=16, pady=10)
        _lbl(bar, "Analysis Detail", fg=TEXT, font=F_HEAD, bg=PANEL).pack(side="left", padx=8)

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=20, pady=16)
        _lbl(self.body, "Loading…", fg=MUTED, font=F_BODY, bg=BG).pack(pady=60)

    def _load(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            data = api("get", f"/analyses/{self.analysis_id}?user_id={self.user['id']}")
            self.after(0, lambda: self._render(data))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _render(self, a: dict):
        for w in self.body.winfo_children():
            w.destroy()

        sev = a.get("severity", "unknown")
        sev_color = SEVERITY_COLOR.get(sev, MUTED)

        # Header row
        hdr = tk.Frame(self.body, bg=BG)
        hdr.pack(fill="x", pady=(0, 12))
        badge = tk.Label(hdr, text=f"  {sev.upper()}  ", bg=sev_color,
                         fg="black", font=("Courier", 11, "bold"), padx=6, pady=4)
        badge.pack(side="left")
        ts = a.get("created_at", "")[:16].replace("T", " ")
        _lbl(hdr, f"  Analysed on {ts}", fg=MUTED, font=F_SMALL, bg=BG).pack(side="left")
        _lbl(hdr, f"{a.get('tokens_used', 0)} tokens  •  {a.get('duration_sec', 0)}s  •  {a.get('ai_model', '')}",
             fg=MUTED, font=F_SMALL, bg=BG).pack(side="right")

        # Summary
        _lbl(self.body, "SUMMARY", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 4))
        sumbox = _card(self.body)
        sumbox.pack(fill="x", pady=(0, 14))
        _lbl(sumbox, a.get("summary", "No summary."), fg=TEXT, font=("Courier", 10),
             bg=CARD, wraplength=860, justify="left").pack(padx=16, pady=12, anchor="w")

        # Custom prompt (if any)
        if a.get("user_prompt"):
            _lbl(self.body, "CUSTOM INSTRUCTION", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 4))
            pbox = _card(self.body)
            pbox.pack(fill="x", pady=(0, 14))
            _lbl(pbox, a["user_prompt"], fg=WARN, font=("Courier", 9, "italic"),
                 bg=CARD, wraplength=860, justify="left").pack(padx=16, pady=8, anchor="w")

        # Two-column: anomalies | patterns
        cols = tk.Frame(self.body, bg=BG)
        cols.pack(fill="both", expand=True)

        # Anomalies
        left = tk.Frame(cols, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        _lbl(left, "ANOMALIES", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 6))

        anomalies = json.loads(a.get("anomalies", "[]"))
        if anomalies:
            for item in anomalies:
                c = _card(left)
                c.pack(fill="x", pady=3)
                asc = SEVERITY_COLOR.get(item.get("severity", "info"), MUTED)
                tk.Label(c, text=f" {item.get('severity','').upper()} ",
                         bg=asc, fg="black", font=("Courier", 7, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
                _lbl(c, item.get("line", ""), fg=WARN, font=("Courier", 8),
                     bg=CARD, wraplength=380, justify="left").pack(anchor="w", padx=10, pady=(0, 4))
                _lbl(c, item.get("description", ""), fg=TEXT, font=("Courier", 8),
                     bg=CARD, wraplength=380, justify="left").pack(anchor="w", padx=10, pady=(0, 8))
        else:
            _lbl(left, "No anomalies detected.", fg=MUTED, font=F_BODY, bg=BG).pack(pady=20)

        # Patterns
        right = tk.Frame(cols, bg=BG)
        right.pack(side="right", fill="both", expand=True)
        _lbl(right, "PATTERNS", fg=MUTED, font=("Courier", 8, "bold"), bg=BG).pack(anchor="w", pady=(0, 6))

        patterns = json.loads(a.get("patterns", "[]"))
        if patterns:
            for item in patterns:
                c = _card(right)
                c.pack(fill="x", pady=3)
                top = tk.Frame(c, bg=CARD)
                top.pack(fill="x", padx=10, pady=(8, 4))
                _lbl(top, item.get("pattern", ""), fg=ACCENT, font=("Courier", 9, "bold"), bg=CARD).pack(side="left")
                _lbl(top, f"×{item.get('occurrences', '')}", fg=MUTED, font=F_SMALL, bg=CARD).pack(side="right")
                _lbl(c, item.get("meaning", ""), fg=TEXT, font=("Courier", 8),
                     bg=CARD, wraplength=380, justify="left").pack(anchor="w", padx=10, pady=(0, 8))
        else:
            _lbl(right, "No patterns detected.", fg=MUTED, font=F_BODY, bg=BG).pack(pady=20)


# ══════════════════════════════════════════════════════════════════════════════
# Root App  — screen router
# ══════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LogAnalyzer")
        self.configure(bg=BG)
        self.geometry("960x640")
        self.minsize(760, 520)

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 960) // 2
        y = (self.winfo_screenheight() - 640) // 2
        self.geometry(f"960x640+{x}+{y}")

        # ttk style for progressbar
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TProgressbar", troughcolor=CARD, background=ACCENT, thickness=6)

        self._current: Optional[Screen] = None
        self._user: Optional[dict] = None
        self._prev_file_id: Optional[int] = None   # for back navigation from detail

        self.show_login()

    def _clear(self):
        if self._current:
            self._current.destroy()
            self._current = None

    def show_login(self):
        self._clear()
        self.geometry("480x580")
        self._current = LoginScreen(self)

    def show_register(self):
        self._clear()
        self.geometry("480x640")
        self._current = RegisterScreen(self)

    def show_dashboard(self, user: dict):
        self._clear()
        self._user = user
        self.geometry("960x640")
        self._current = DashboardScreen(self, user)

    def show_upload(self, user: dict, path: str, on_done):
        self._clear()
        self.geometry("480x260")
        self._current = UploadScreen(self, user, path, on_done)

    def show_analysis(self, user: dict, file_id: int):
        self._clear()
        self._prev_file_id = file_id
        self.geometry("960x680")
        self._current = AnalysisScreen(self, user, file_id)

    def show_detail(self, user: dict, analysis_id: int):
        self._clear()
        self.geometry("1040x700")
        self._current = DetailScreen(self, user, analysis_id)

    def history_back(self):
        """Go back from detail → analysis list."""
        if self._prev_file_id and self._user:
            self.show_analysis(self._user, self._prev_file_id)
        elif self._user:
            self.show_dashboard(self._user)
        else:
            self.show_login()


if __name__ == "__main__":
    App().mainloop()