
import threading
import tkinter as tk
import platform
from tkinter import ttk, messagebox

from colors import Palette
from login import LoginPage
from sidebar import SideNav
from toolbar import TopBar
from dashboard import DashboardPage
from analysis import AnalysisPage
from report import ReportsPage
from settings import SettingsPage
from register import RegisterPage
from security import clear_tokens, load_tokens, save_tokens
from helper import BASE_URL, api, clear_token, register_expiry_callback, set_token, session
from admin import AdminPage
from my_profile import ProfilePage
from decrypt import DecryptPage
from upload_logs import UploadLogsPage
from logger import get_logger
import requests


log = get_logger("APP")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._shell    = None
        self._nav      = None
        self._host     = None
        self._user = None

        self.access_token  = None   
        self.refresh_token = None   
        register_expiry_callback(self._on_session_expired)
        self._configure_window()
        self._apply_theme()

        tokens = load_tokens()      
        if tokens:                  
            self._try_auto_login(tokens)  
        else:                       
            self._show_login()  

    def _configure_window(self):
        self.title("XAI Forensics System")
        self.minsize(
            getattr(Palette, "WIN_MIN_W", 1024),
            getattr(Palette, "WIN_MIN_H", 680),
        )
        self.resizable(True, True)

        os_name = platform.system()
        if os_name == "Windows":
            self.state("zoomed")
        elif os_name == "Darwin":
            self.after(50, lambda: self.state("zoomed"))
        else:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                self.after(50, lambda: self.state("zoomed"))

        try:
            self.iconbitmap("xai.ico")
        except Exception:
            pass

    def _apply_theme(self):
        self.configure(bg=Palette.SURFACE)
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        try:
            style.configure(".",
                            background=Palette.SURFACE,
                            foreground=Palette.ON_SURFACE,
                            font=Palette.font())
        except Exception:
            pass

    def _clear_window(self):
        for w in self.winfo_children():
            w.destroy()
        self._shell = None
        self._nav   = None
        self._host  = None

    def _show_login(self):
        self._clear_window()
        self.title("XAI Forensics System — Terminal Authentication")
        LoginPage(
            self, 
            on_login=self._on_login,
            on_register=self._show_register
        ).pack(fill="both", expand=True)
        
    def _show_register(self):
        self._clear_window()
        self.title("XAI Forensics System — Operator Enrollment")
        RegisterPage(
            self,
            on_register=self._show_login,   
            on_back=self._show_login        
        ).pack(fill="both", expand=True)    

    def _on_login(self, response: dict):
        self._user         = response["user"]
        self.access_token  = response["access_token"]
        self.refresh_token = response["refresh_token"]
        save_tokens(self.access_token, self.refresh_token)
        set_token(self.access_token)
        self._clear_window()
        self._build_shell()

    def _on_session_expired(self):
        self.after(0, self._handle_expiry)

    def _handle_expiry(self):
        from tkinter import messagebox
        
        choice = messagebox.askquestion(
            "Session Expired",
            "Your session has expired.\n\n"
            "Would you like to stay signed in?\n\n"
            "• Yes — refresh your session\n"
            "• No  — return to login",
            icon="warning"
        )

        if choice == "yes":
            self._try_silent_refresh()
        else:
            self._force_logout()

    def _try_silent_refresh(self):
        def attempt():
            try:
                tokens = load_tokens()
                if not tokens or not tokens.get("refresh"):
                    self.after(0, self._force_logout)
                    return

                resp = requests.post(
                    f"{BASE_URL}/auth/refresh",
                    headers={
                        "Content-Type":  "application/json",
                        "Authorization": f"Bearer {tokens['refresh']}",  # ← same fix
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data       = resp.json()
                new_access = data["access_token"]
                save_tokens(new_access, tokens["refresh"])
                set_token(new_access)

                user          = api("get", "/auth/me")
                self._user    = user
                self.access_token = new_access

                self.after(0, lambda: messagebox.showinfo(
                    "Session Restored",
                    "Your session has been refreshed. You can continue."
                ))

            except Exception:
                self.after(0, lambda: (
                    messagebox.showwarning(
                        "Session Expired",
                        "Your refresh token has also expired.\n"
                        "Please sign in again."
                    ),
                    self._force_logout()
                ))

        threading.Thread(target=attempt, daemon=True).start()

    def _force_logout(self):
        """Clean logout — clears everything and shows login."""
        clear_tokens()
        clear_token()
        self._user         = None
        self.access_token  = None
        self.refresh_token = None
        self._show_login()
    
    def _build_shell(self, refresh: bool = False):
        if refresh:
            self._clear_window()

        self._shell = tk.Frame(self, bg=Palette.SURFACE)
        self._shell.pack(fill="both", expand=True)

        # check if user is admin before building nav
        is_admin = self._user_is_admin()

        self._nav = SideNav(
            self._shell,
            active="Dashboard",
            on_navigate=self._navigate,
            is_admin=is_admin,             # ← pass to nav
        )
        self._nav.pack(side="left", fill="y")

        right = tk.Frame(self._shell, bg=Palette.SURFACE)
        right.pack(side="left", fill="both", expand=True)

        self._build_topbar(right)

        self._host = tk.Frame(right, bg=Palette.SURFACE)
        self._host.pack(side="top", fill="both", expand=True)

        self._load_page("Dashboard")
        
    def _user_is_admin(self) -> bool:
        """Check if logged-in user has admin:users permission."""
        if not self._user:
            return False
        roles = self._user.get("roles", [])
        for role in roles:
            for perm in role.get("permissions", []):
                if perm.get("code") == "admin:users":
                    return True
        return False 
    
    def _build_topbar(self, parent: tk.Frame):
        roles = self._user.get("roles", []) if self._user else []
        role_label = "  •  ".join(r["name"] for r in roles) if roles else "No Role"

        try:
            bar = TopBar(
                parent,
                title="XAI Network Logs Analysis System",
                agent=self._user,
                role=role_label,              
                search_placeholder="Search case ID or evidence...",
            )
            bar._on_user_updated = self._on_profile_updated
        except Exception as exc:
            log.error("TopBar failed: %s", exc)
            bar = tk.Frame(parent, bg=Palette.SURFACE_LOW,
                        height=Palette.TOPBAR_H)

        bar.pack(side="top", fill="x")
        
    def _on_profile_updated(self, updated: dict):
        self._user = updated
        self.title(f"XAI Forensics System — {updated.get('username')}")
        log.info("Profile updated: %s", updated.get("username"))

    
        if self._shell:
            for widget in self._shell.winfo_children():
                if widget != self._nav:         
                    for child in widget.winfo_children():
                        if isinstance(child, TopBar):
                            child.destroy()
                            self._build_topbar(widget)
                            break
                    break    

    def _navigate(self, label: str):
        log.info("Navigate → %s", label)
        if self._host is None:
            print(f"[WARN] _navigate('{label}') called before shell ready.")
            return

        if label == "Logout":
            self._logout()
            return

        self._nav.set_active(label)
        self._load_page(label)

    def _load_page(self, label: str):
        if self._host is None:
            return
        for w in self._host.winfo_children():
            w.destroy()

        PAGE_MAP = {
            "Dashboard":   DashboardPage,
            "Analysis":    AnalysisPage,
            "Reports":     ReportsPage,
            "Settings":    SettingsPage,
            "Upload Logs": UploadLogsPage,
            "Admin":       AdminPage,         
            "Profile":     ProfilePage, 
            "Decrypt":     DecryptPage,
        }

        if label in PAGE_MAP:
            try:
                PAGE_MAP[label](self._host,user=self._user,
                            on_profile_updated=self._on_profile_updated).pack(fill="both", expand=True)
            except Exception as exc:
                log.error("Failed to load page '%s': %s", label, exc)
                self._show_placeholder(f"{label} (load error)")
        else:
            self._show_placeholder(label)

    def _show_placeholder(self, label: str):
        ph = tk.Frame(self._host, bg=Palette.SURFACE)
        ff = getattr(Palette, "_FONT", ["Helvetica Neue"])[0]
        tk.Label(ph, text=label,
                 font=(ff, 32, "bold"),
                 fg=Palette.SURFACE_HIGH,
                 bg=Palette.SURFACE).place(relx=0.5, rely=0.44,
                                           anchor="center")
        tk.Label(ph, text="Page coming soon",
                 font=(ff, 12, "normal"),
                 fg=Palette.ON_SURFACE_VAR,
                 bg=Palette.SURFACE).place(relx=0.5, rely=0.54,
                                           anchor="center")
        ph.pack(fill="both", expand=True)

    def _logout(self):
        confirmed = messagebox.askyesno(
            "Logout",
            "End investigation session and return to login?"
        )
        if confirmed:
            self._force_logout()

    def _try_auto_login(self, tokens: dict):
        def attempt():
            try:
                set_token(tokens["access"])
                user = api("get", "/auth/me")   

                self.access_token  = session.headers.get(
                    "Authorization", "").replace("Bearer ", "")
                self.refresh_token = tokens["refresh"]
                self._user         = user
                self.after(0, lambda: self._build_shell(refresh=True))

            except requests.HTTPError:
                self.after(0, self._show_login)

            except requests.ConnectionError:
                self.after(0, self._show_login)

        threading.Thread(target=attempt, daemon=True).start()
        
        
if __name__ == "__main__":
    app = App()
    app.mainloop()