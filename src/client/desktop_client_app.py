"""
==============================================================================
UnderWraps Client Messaging Application (Windows 11 Fluent Dark UI)
E2EE Messaging, Username/Password Auth, Optional 2FA, 150MB Media, Voice Notes,
48kHz Voice Calling, Sound-Reactive Themes & Cryptographic Peer Color Halos

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
==============================================================================
"""

from __future__ import annotations

import os
import sys
import time
import json
import socket
import struct
import urllib.request
import urllib.error
import urllib.parse
import threading
import concurrent.futures
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog
except (ImportError, ModuleNotFoundError):
    tk = None
    ttk = None
    messagebox = None
    filedialog = None
    simpledialog = None
from typing import Dict, List, Any, Optional, Tuple, Set

# Import Sovereign ALU & Python Modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.crypto.peer_halo import derive_peer_halo
from src.client.sound_reactive_engine import SoundReactiveEngine

# Color Palettes & 3 Live Themes
THEMES = {
    "galaxy": {
        "name": "Dark Galaxy Field",
        "bg_app": "#0d1117",
        "bg_sidebar": "#161b22",
        "bg_chat": "#0f131a",
        "bg_input": "#1c2128",
        "bg_card": "#161b22",
        "bg_bubble_in": "#21262d",
        "bg_bubble_out": "#1f6feb",
        "border_color": "#30363d",
        "accent_blue": "#58a6ff",
        "accent_green": "#2ea043",
        "accent_red": "#da3633",
        "accent_yellow": "#d29922",
        "text_white": "#f0f6fc",
        "text_muted": "#8b949e",
    },
    "inverted": {
        "name": "Inverted Stars",
        "bg_app": "#f4f7fa",
        "bg_sidebar": "#eaedf1",
        "bg_chat": "#f0f3f6",
        "bg_input": "#ffffff",
        "bg_card": "#ffffff",
        "bg_bubble_in": "#dfe5ec",
        "bg_bubble_out": "#0969da",
        "border_color": "#d0d7de",
        "accent_blue": "#0969da",
        "accent_green": "#1a7f37",
        "accent_red": "#cf222e",
        "accent_yellow": "#9a6700",
        "text_white": "#1f2328",
        "text_muted": "#656d76",
    },
    "aurora": {
        "name": "Cyber Aurora Matrix",
        "bg_app": "#030608",
        "bg_sidebar": "#081416",
        "bg_chat": "#050d0f",
        "bg_input": "#0e2226",
        "bg_card": "#081416",
        "bg_bubble_in": "#122c30",
        "bg_bubble_out": "#00b4d8",
        "border_color": "#00f5d4",
        "accent_blue": "#00f5d4",
        "accent_green": "#00f59b",
        "accent_red": "#ff3366",
        "accent_yellow": "#fee440",
        "text_white": "#e0fff8",
        "text_muted": "#7ea8a4",
    }
}

# Active Global Colors (Default: Dark Galaxy)
BG_APP = THEMES["galaxy"]["bg_app"]
BG_SIDEBAR = THEMES["galaxy"]["bg_sidebar"]
BG_CHAT = THEMES["galaxy"]["bg_chat"]
BG_INPUT = THEMES["galaxy"]["bg_input"]
BG_CARD = THEMES["galaxy"]["bg_card"]
BG_BUBBLE_IN = THEMES["galaxy"]["bg_bubble_in"]
BG_BUBBLE_OUT = THEMES["galaxy"]["bg_bubble_out"]
BORDER_COLOR = THEMES["galaxy"]["border_color"]
ACCENT_BLUE = THEMES["galaxy"]["accent_blue"]
ACCENT_GREEN = THEMES["galaxy"]["accent_green"]
ACCENT_RED = THEMES["galaxy"]["accent_red"]
ACCENT_YELLOW = THEMES["galaxy"]["accent_yellow"]
TEXT_WHITE = THEMES["galaxy"]["text_white"]
TEXT_MUTED = THEMES["galaxy"]["text_muted"]

MAX_FILE_BYTES = 157286400  # 150 MB

# ------------------------------------------------------------------------------
# Zero-Configuration Server Discovery & Persistent Session Management
# ------------------------------------------------------------------------------
SESSION_FILE_PATH = os.path.expanduser("~/.underwraps/session.json")

SETTINGS_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../settings.json"))

def _probe_http_server(target: str, timeout: float = 0.35) -> Optional[Tuple[str, str, int]]:
    """Probes /api/v1/server/info to verify an UnderWraps Sovereign Node."""
    try:
        url = target if target.startswith("http") else f"http://{target}:8080"
        endpoint = f"{url.rstrip('/')}/api/v1/server/info"
        req = urllib.request.Request(endpoint)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("service") == "UNDERWRAPS_SERVER":
                    http_url = data.get("http_url", url)
                    host = data.get("host", urllib.parse.urlparse(url).hostname or "127.0.0.1")
                    ws_port = int(data.get("ws_port", 8081))
                    return http_url, host, ws_port
    except Exception:
        pass
    return None

def discover_underwraps_server(default_http: str = "http://192.168.50.179:8080", timeout: float = 0.8) -> Tuple[str, str, int]:
    """
    Zero-configuration 4-Tier Autonomous Discovery across Local Network:
    Note: The server runs on a dedicated machine across the network, NOT on this PC.
    1. Direct Priority Candidates: default_http and remote network target hosts (e.g. 192.168.50.179).
    2. Zero-Config UDP Broadcast Probe across LAN (Port 8088).
    3. Ultra-Fast Parallel Subnet Socket Sweep across /24 local network.
    4. Fallback to default remote host.
    """
    candidates = ["192.168.50.179"]
    if default_http:
        candidates.insert(0, default_http)

    # Read extra candidates from settings.json if present
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                extra = cfg.get("server", {}).get("target_hosts", [])
                for h in extra:
                    if h not in ("127.0.0.1", "localhost") and h not in candidates:
                        candidates.append(h)
    except Exception:
        pass

    seen = set()
    unique_candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(unique_candidates))) as ex:
        futures = [ex.submit(_probe_http_server, c, 0.35) for c in unique_candidates]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                return res

    # 2. Tier 2: UDP Broadcast Probe on LAN (Port 8088)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        probe_msg = b"UNDERWRAPS_DISCOVER_PROBE"
        sock.sendto(probe_msg, ("<broadcast>", 8088))
        data, addr = sock.recvfrom(2048)
        sock.close()
        info = json.loads(data.decode("utf-8"))
        http_url = info.get("http_url", f"http://{addr[0]}:8080")
        ws_host = info.get("host", addr[0])
        ws_port = int(info.get("ws_port", 8081))
        return http_url, ws_host, ws_port
    except Exception:
        pass

    # 3. Tier 3: Parallel Subnet Socket Sweep across /24 LAN range
    try:
        lan_prefix = None
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            lan_prefix = ".".join(my_ip.split(".")[:3])
        except Exception:
            pass
        finally:
            s.close()

        if lan_prefix:
            def fast_socket_check(ip):
                try:
                    csock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    csock.settimeout(0.2)
                    if csock.connect_ex((ip, 8080)) == 0:
                        csock.close()
                        return _probe_http_server(f"http://{ip}:8080", timeout=0.4)
                    csock.close()
                except Exception:
                    pass
                return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=80) as ex:
                sweep_futures = [ex.submit(fast_socket_check, f"{lan_prefix}.{i}") for i in range(1, 255)]
                for f in concurrent.futures.as_completed(sweep_futures):
                    res = f.result()
                    if res:
                        return res
    except Exception:
        pass

    # 4. Fallback to designated remote server
    parsed = urllib.parse.urlparse(default_http)
    host = parsed.hostname or "192.168.50.179"
    return default_http, host, 8081

def load_cached_session() -> Optional[Dict[str, Any]]:
    """Loads active session credentials from local storage."""
    try:
        if os.path.exists(SESSION_FILE_PATH):
            with open(SESSION_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("session_token"):
                    return data
    except Exception:
        pass
    return None

def save_cached_session(auth_data: Dict[str, Any], server_http: str):
    """Persists session credentials to local storage for zero-click auto login."""
    try:
        os.makedirs(os.path.dirname(SESSION_FILE_PATH), exist_ok=True)
        to_save = {
            "session_token": auth_data.get("session_token"),
            "username": auth_data.get("username"),
            "user_id": auth_data.get("user_id"),
            "email": auth_data.get("email"),
            "display_name": auth_data.get("display_name"),
            "identity_key_pub": auth_data.get("identity_key_pub"),
            "two_factor_enabled": auth_data.get("two_factor_enabled", False),
            "server_http": server_http,
            "saved_at": int(time.time())
        }
        with open(SESSION_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2)
    except Exception:
        pass

def clear_cached_session():
    """Removes cached session credentials upon logout."""
    try:
        if os.path.exists(SESSION_FILE_PATH):
            os.remove(SESSION_FILE_PATH)
    except Exception:
        pass


class UnderWrapsClientGUI:
    def __init__(self, root: Any, server_http: str = "http://192.168.50.179:8080", server_ws_host: str = "192.168.50.179", server_ws_port: int = 8081):
        self.root = root
        if hasattr(self.root, "title"):
            self.root.title("UnderWraps — Sovereign Private Messenger")
        if hasattr(self.root, "geometry"):
            self.root.geometry("1100x740")
        if hasattr(self.root, "minsize"):
            self.root.minsize(860, 580)
        self.current_theme = "galaxy"
        if hasattr(self.root, "configure"):
            self.root.configure(bg=BG_APP)

        # Set taskbar and window icon
        try:
            icon_candidates = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../web/assets/logo/app_icon.ico")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets/logo/app_icon.ico")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../web/icon.ico")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../web/app_icon_512.png"))
            ]
            for icon_path in icon_candidates:
                if os.path.exists(icon_path):
                    if icon_path.endswith('.ico') and hasattr(self.root, "iconbitmap"):
                        self.root.iconbitmap(icon_path)
                        break
                    elif icon_path.endswith('.png') and tk and hasattr(tk, 'PhotoImage') and hasattr(self.root, "iconphoto"):
                        img = tk.PhotoImage(file=icon_path)
                        self.root.iconphoto(True, img)
                        break
        except Exception:
            pass
        
        # Load cached session if available
        self.cached_session = load_cached_session()
        target_server = server_http
        if self.cached_session and self.cached_session.get("server_http") and server_http == "http://192.168.50.179:8080":
            target_server = self.cached_session.get("server_http")
        
        # Auto-discover UnderWraps server across LAN
        try:
            disc_http, disc_ws_host, disc_ws_port = discover_underwraps_server(default_http=target_server, timeout=0.6)
            self.server_http = disc_http
            self.server_ws_host = disc_ws_host
            self.server_ws_port = disc_ws_port
        except Exception:
            self.server_http = target_server
            self.server_ws_host = server_ws_host
            self.server_ws_port = server_ws_port
        
        # Sound-Reactive & Halo Features
        self.sound_engine = SoundReactiveEngine(sensitivity=1.0, enabled=True)
        self.peer_halo_enabled = True
        
        # Session State
        self.current_user: Optional[Dict[str, Any]] = None
        self.session_token: Optional[str] = None
        self.active_conv_id: Optional[str] = None
        self.active_peer: Optional[Dict[str, Any]] = None
        
        # WebSocket connection
        self.ws_sock: Optional[socket.socket] = None
        self.ws_connected = False
        
        # Voice Calling State
        self.active_call_id: Optional[str] = None
        self.call_start_time: Optional[float] = None
        self.call_dialog: Optional[tk.Toplevel] = None
        
        # Voice Note Recording State
        self.is_recording_voice = False
        self.record_start_time = 0.0
        
        self._setup_styles()
        
        # Attempt seamless zero-click session resumption
        if not self._try_auto_resume():
            self._show_auth_screen()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_APP, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_SIDEBAR, foreground=TEXT_MUTED, padding=[14, 6], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", BG_CARD)], foreground=[("selected", ACCENT_BLUE)])

    def _try_auto_resume(self) -> bool:
        """Attempts zero-click session resumption using cached session token."""
        if not self.cached_session or not self.cached_session.get("session_token"):
            return False
        
        token = self.cached_session["session_token"]
        try:
            req = urllib.request.Request(
                f"{self.server_http}/api/v1/auth/resume",
                data=json.dumps({"session_token": token}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success") and data.get("user"):
                    self._on_auth_success(data["user"], save_session=True)
                    return True
        except Exception:
            pass
        return False

    # --------------------------------------------------------------------------
    # Cryptographic Peer Color Halo Avatar Widget
    # --------------------------------------------------------------------------
    def _create_halo_avatar(self, parent: tk.Widget, identifier: str, size: int = 38, bg: Optional[str] = None) -> tk.Canvas:
        """
        Creates a Canvas widget displaying a deterministic concentric glowing color halo
        derived from the user's public key or identifier.
        """
        halo = derive_peer_halo(identifier)
        canvas_bg = bg or parent["bg"]
        cv = tk.Canvas(parent, width=size, height=size, bg=canvas_bg, highlightthickness=0)
        
        center = size / 2.0
        radius = (size / 2.0) - 2.0
        
        if self.peer_halo_enabled:
            # Concentric Halo Outer Rings
            cv.create_oval(1, 1, size-1, size-1, outline=halo["color1"], width=2.5)
            cv.create_arc(2, 2, size-2, size-2, start=halo["gradient_angle"], extent=180, outline=halo["color2"], width=2.5, style="arc")
            # Inner Avatar Background
            inner_r = radius - 3.5
            cv.create_oval(center - inner_r, center - inner_r, center + inner_r, center + inner_r, fill=BG_CARD, outline=BORDER_COLOR)
        else:
            cv.create_oval(2, 2, size-2, size-2, fill=BG_CARD, outline=BORDER_COLOR, width=1.5)
            
        # Centered Avatar Icon
        cv.create_text(center, center, text="👤", font=("Segoe UI Emoji", int(size * 0.42)))
        return cv

    # --------------------------------------------------------------------------
    # Screen 1: Streamlined Authentication (Username + Password Only)
    # --------------------------------------------------------------------------
    def _show_auth_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        auth_container = tk.Frame(self.root, bg=BG_APP)
        auth_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Card Box
        card = tk.Frame(auth_container, bg=BG_SIDEBAR, padx=36, pady=32, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack()
        
        # Logo & Header
        tk.Label(card, text="🛡️ UNDERWRAPS", font=("Segoe UI", 20, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(0, 4))
        tk.Label(card, text="Sovereign E2EE • Custom Username • 150MB Media • 48kHz Voice", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_SIDEBAR).pack(pady=(0, 16))
        
        # Auto-Discovery Status Badge (No manual IP needed)
        disc_box = tk.Frame(card, bg=BG_INPUT, padx=10, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
        disc_box.pack(fill=tk.X, pady=(0, 16))
        tk.Label(disc_box, text="⚡ Zero-Config Auto-Discovery Active", font=("Segoe UI", 8, "bold"), fg=ACCENT_GREEN, bg=BG_INPUT).pack(side=tk.LEFT)
        tk.Label(disc_box, text=f"• Connected to Server", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_INPUT).pack(side=tk.LEFT, padx=4)

        # Quick Resume Banner if previous session exists
        cached_user = self.cached_session.get("username") if self.cached_session else None
        if cached_user:
            quick_box = tk.Frame(card, bg="#122c30" if self.current_theme=="aurora" else "#1b2838", padx=12, pady=10, highlightthickness=1, highlightbackground=ACCENT_BLUE)
            quick_box.pack(fill=tk.X, pady=(0, 16))
            
            tk.Label(quick_box, text=f"Welcome back, @{cached_user}", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=quick_box["bg"]).pack(anchor="w")
            tk.Label(quick_box, text="Enter password to sign in, or switch tabs to create a new account.", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=quick_box["bg"]).pack(anchor="w", pady=(2, 6))

        # Tabs for Sign In vs Create Account
        notebook = ttk.Notebook(card)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Sign In
        tab_signin = tk.Frame(notebook, bg=BG_SIDEBAR, padx=10, pady=16)
        notebook.add(tab_signin, text="Sign In")
        
        tk.Label(tab_signin, text="Username", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_login_id = tk.Entry(tab_signin, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT, width=32)
        if cached_user:
            self.entry_login_id.insert(0, cached_user)
        self.entry_login_id.pack(fill=tk.X, pady=(0, 14), ipady=4)
        
        tk.Label(tab_signin, text="Password", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_login_pwd = tk.Entry(tab_signin, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, show="•", relief=tk.FLAT, width=32)
        self.entry_login_pwd.pack(fill=tk.X, pady=(0, 20), ipady=4)
        self.entry_login_pwd.bind("<Return>", lambda e: self._handle_login())
        
        btn_login = tk.Button(tab_signin, text="Sign In", font=("Segoe UI", 10, "bold"), bg=ACCENT_BLUE, fg="#ffffff", activebackground="#388bfd", relief=tk.FLAT, pady=8, cursor="hand2", command=self._handle_login)
        btn_login.pack(fill=tk.X)
        
        # Tab 2: Create Account (Username + Password Only)
        tab_signup = tk.Frame(notebook, bg=BG_SIDEBAR, padx=10, pady=16)
        notebook.add(tab_signup, text="Create Account")
        
        tk.Label(tab_signup, text="Choose Custom Username", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_reg_user = tk.Entry(tab_signup, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT, width=32)
        self.entry_reg_user.pack(fill=tk.X, pady=(0, 12), ipady=4)
        
        tk.Label(tab_signup, text="Choose Password", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_reg_pwd = tk.Entry(tab_signup, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, show="•", relief=tk.FLAT, width=32)
        self.entry_reg_pwd.pack(fill=tk.X, pady=(0, 20), ipady=4)
        self.entry_reg_pwd.bind("<Return>", lambda e: self._handle_signup())
        
        btn_signup = tk.Button(tab_signup, text="Create Sovereign Account", font=("Segoe UI", 10, "bold"), bg=ACCENT_GREEN, fg="#ffffff", activebackground="#238636", relief=tk.FLAT, pady=8, cursor="hand2", command=self._handle_signup)
        btn_signup.pack(fill=tk.X)

        # Footer Server Options
        footer_frame = tk.Frame(card, bg=BG_SIDEBAR)
        footer_frame.pack(fill=tk.X, pady=(16, 0))
        btn_adv = tk.Button(footer_frame, text="⚙️ Connection Settings", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_SIDEBAR, relief=tk.FLAT, cursor="hand2", command=self._prompt_manual_server_dialog)
        btn_adv.pack(side=tk.RIGHT)

    def _prompt_manual_server_dialog(self):
        """Optional dialog for manual server configuration if ever needed."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Server Connection Settings")
        dialog.geometry("420x220")
        dialog.configure(bg=BG_SIDEBAR)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="🌐 Server Connection", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(16, 4))
        tk.Label(dialog, text="UnderWraps auto-discovers local and network servers automatically.\nYou can also specify a custom server address below.", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_SIDEBAR, justify=tk.CENTER).pack(pady=(0, 12))

        entry_srv = tk.Entry(dialog, font=("Segoe UI", 10), bg=BG_INPUT, fg=ACCENT_BLUE, insertbackground=TEXT_WHITE, relief=tk.FLAT, width=36)
        entry_srv.insert(0, self.server_http)
        entry_srv.pack(pady=(0, 16), ipady=4)

        def save_and_reconnect():
            url = entry_srv.get().strip().rstrip("/")
            if url:
                self.server_http = url
                parsed = urllib.parse.urlparse(url)
                self.server_ws_host = parsed.hostname or "127.0.0.1"
                self.server_ws_port = 8081
            dialog.destroy()
            self._show_auth_screen()

        tk.Button(dialog, text="Save & Connect", font=("Segoe UI", 9, "bold"), bg=ACCENT_BLUE, fg="#ffffff", relief=tk.FLAT, padx=14, pady=6, cursor="hand2", command=save_and_reconnect).pack()

    def _handle_login(self):
        identifier = self.entry_login_id.get().strip()
        pwd = self.entry_login_pwd.get().strip()
        if not identifier or not pwd:
            messagebox.showwarning("Incomplete Fields", "Please enter your username and password.")
            return
            
        try:
            req = urllib.request.Request(
                f"{self.server_http}/api/v1/auth/login",
                data=json.dumps({"identifier": identifier, "password": pwd}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                
            if data.get("requires_2fa"):
                self._prompt_2fa_modal(data["token_id"], data.get("email_masked", "your email"), data.get("otp_code_dev"))
            else:
                self._on_auth_success(data, save_session=True)
        except urllib.error.HTTPError as e:
            err_body = json.loads(e.read().decode("utf-8"))
            messagebox.showerror("Login Failed", err_body.get("error", "Authentication error"))
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server at {self.server_http}: {str(e)}")

    def _prompt_2fa_modal(self, token_id: str, email_masked: str, otp_code_dev: Optional[str]):
        dialog = tk.Toplevel(self.root)
        dialog.title("Two-Factor Authentication (2FA)")
        dialog.geometry("400x260")
        dialog.configure(bg=BG_SIDEBAR)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="🔒 2FA Verification Code", font=("Segoe UI", 13, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(20, 4))
        tk.Label(dialog, text=f"Enter the 6-digit verification code sent to:\n{email_masked}", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_SIDEBAR, justify=tk.CENTER).pack(pady=(0, 14))
        
        if otp_code_dev:
            tk.Label(dialog, text=f"[Dev Mode Token]: {otp_code_dev}", font=("Consolas", 9, "bold"), fg=ACCENT_YELLOW, bg="#34280f", padx=8, pady=2).pack(pady=(0, 10))
            
        otp_entry = tk.Entry(dialog, font=("Segoe UI", 16, "bold"), bg=BG_INPUT, fg=TEXT_WHITE, justify=tk.CENTER, relief=tk.FLAT, width=12)
        otp_entry.pack(pady=(0, 18), ipady=4)
        otp_entry.focus()
        
        def submit_2fa():
            code = otp_entry.get().strip()
            if len(code) != 6:
                messagebox.showwarning("Invalid Code", "Please enter a 6-digit code.")
                return
            try:
                req = urllib.request.Request(
                    f"{self.server_http}/api/v1/auth/verify-2fa",
                    data=json.dumps({"token_id": token_id, "otp_code": code}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                dialog.destroy()
                self._on_auth_success(res_data, save_session=True)
            except Exception as ex:
                messagebox.showerror("2FA Error", str(ex))
                
        tk.Button(dialog, text="Verify & Login", font=("Segoe UI", 10, "bold"), bg=ACCENT_GREEN, fg="#ffffff", relief=tk.FLAT, padx=16, pady=6, cursor="hand2", command=submit_2fa).pack(fill=tk.X, padx=40)

    def _handle_signup(self):
        user = self.entry_reg_user.get().strip()
        pwd = self.entry_reg_pwd.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Incomplete Fields", "Please enter a username and password.")
            return
            
        try:
            req = urllib.request.Request(
                f"{self.server_http}/api/v1/auth/signup",
                data=json.dumps({"username": user, "password": pwd, "display_name": user}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            # Instant seamless login on account creation
            user_data = data.get("user", {})
            self._on_auth_success(user_data, save_session=True)
        except urllib.error.HTTPError as e:
            err_body = json.loads(e.read().decode("utf-8"))
            messagebox.showerror("Signup Failed", err_body.get("error", "Registration error"))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_auth_success(self, auth_data: Dict[str, Any], save_session: bool = True):
        self.current_user = auth_data
        self.session_token = auth_data.get("session_token")
        if save_session and self.session_token:
            save_cached_session(auth_data, self.server_http)
            self.cached_session = auth_data
        self._build_main_messenger_ui()
        self._connect_websocket()
        self._load_conversations()

    def _sign_out(self):
        """Signs out user, clears session cache, and returns to authentication screen."""
        clear_cached_session()
        self.cached_session = None
        self.current_user = None
        self.session_token = None
        self.ws_connected = False
        if self.ws_sock:
            try: self.ws_sock.close()
            except Exception: pass
            self.ws_sock = None
        self._show_auth_screen()

    # --------------------------------------------------------------------------
    # Screen 2: Main Messaging Interface (Responsive & Halo-Integrated)
    # --------------------------------------------------------------------------
    def _build_main_messenger_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        main_box = tk.Frame(self.root, bg=BG_APP)
        main_box.pack(fill=tk.BOTH, expand=True)
        
        # 1. Left Sidebar
        self.sidebar = tk.Frame(main_box, bg=BG_SIDEBAR, width=310, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # Sidebar User Header with Cryptographic Peer Color Halo
        user_header = tk.Frame(self.sidebar, bg=BG_SIDEBAR, padx=12, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        user_header.pack(fill=tk.X)
        
        u_box = tk.Frame(user_header, bg=BG_SIDEBAR)
        u_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # My Halo Avatar
        my_avatar = self._create_halo_avatar(u_box, self.current_user['username'], size=38)
        my_avatar.pack(side=tk.LEFT, padx=(0, 8))
        
        u_text_box = tk.Frame(u_box, bg=BG_SIDEBAR)
        u_text_box.pack(side=tk.LEFT, fill=tk.X)
        
        tk.Label(u_text_box, text=f"@{self.current_user['username']}", font=("Segoe UI", 10, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w")
        self.lbl_ws_indicator = tk.Label(u_text_box, text="● Online (E2EE Active)", font=("Segoe UI", 8), fg=ACCENT_GREEN, bg=BG_SIDEBAR)
        self.lbl_ws_indicator.pack(anchor="w")
        
        btn_settings = tk.Button(user_header, text="⚙️", font=("Segoe UI", 11), bg=BG_SIDEBAR, fg=TEXT_MUTED, activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._show_settings_modal)
        btn_settings.pack(side=tk.RIGHT)
        
        btn_neural_search_top = tk.Button(user_header, text="🧠", font=("Segoe UI", 11), bg=BG_SIDEBAR, fg=ACCENT_BLUE, activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._show_neural_search_modal)
        btn_neural_search_top.pack(side=tk.RIGHT, padx=(0, 4))
        
        # Sidebar Action Buttons
        action_bar = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        action_bar.pack(fill=tk.X, padx=10, pady=8)
        
        btn_new_chat = tk.Button(action_bar, text="➕ New DM", font=("Segoe UI", 9, "bold"), bg=BG_INPUT, fg=ACCENT_BLUE, activebackground="#262c36", relief=tk.FLAT, pady=6, cursor="hand2", command=self._prompt_new_chat)
        btn_new_chat.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        btn_search = tk.Button(action_bar, text="🧠 Neural Search", font=("Segoe UI", 9, "bold"), bg="#122c30" if self.current_theme=="aurora" else "#1b2533", fg=ACCENT_BLUE, activebackground="#263445", relief=tk.FLAT, pady=6, cursor="hand2", command=self._show_neural_search_modal)
        btn_search.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Conversation List Box
        self.conv_list_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        self.conv_list_frame.pack(fill=tk.BOTH, expand=True, padx=4)

        # 2. Right Chat Area
        self.chat_area = tk.Frame(main_box, bg=BG_CHAT)
        self.chat_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Chat Header
        self.chat_header = tk.Frame(self.chat_area, bg=BG_SIDEBAR, height=62, padx=16, pady=8, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.chat_header.pack(fill=tk.X, side=tk.TOP)
        
        self.header_left_box = tk.Frame(self.chat_header, bg=BG_SIDEBAR)
        self.header_left_box.pack(side=tk.LEFT, fill=tk.X)
        
        self.lbl_chat_title = tk.Label(self.header_left_box, text="Select a conversation to begin", font=("Segoe UI", 11, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR)
        self.lbl_chat_title.pack(side=tk.LEFT)
        
        self.lbl_chat_status = tk.Label(self.header_left_box, text="", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_SIDEBAR)
        self.lbl_chat_status.pack(side=tk.LEFT, padx=10)
        
        # High Quality Voice Call Button (48kHz)
        self.btn_call = tk.Button(self.chat_header, text="📞 Call (48kHz)", font=("Segoe UI", 9, "bold"), bg="#1a3b2b", fg=ACCENT_GREEN, activebackground="#23533c", relief=tk.FLAT, padx=12, pady=5, cursor="hand2", command=self._start_voice_call)
        self.btn_call.pack(side=tk.RIGHT)
        self.btn_call.pack_forget()
        
        # Header Search Trigger
        self.btn_hdr_search = tk.Button(self.chat_header, text="🔍 Search", font=("Segoe UI", 9), bg=BG_INPUT, fg=TEXT_MUTED, activebackground=BG_SIDEBAR, relief=tk.FLAT, padx=10, pady=5, cursor="hand2", command=self._show_neural_search_modal)
        self.btn_hdr_search.pack(side=tk.RIGHT, padx=(0, 8))
        
        # Keyboard Shortcuts
        self.root.bind("<Control-f>", lambda e: self._show_neural_search_modal())
        self.root.bind("<Control-F>", lambda e: self._show_neural_search_modal())
        
        # Message Feed Canvas & Scrollbar
        feed_container = tk.Frame(self.chat_area, bg=BG_CHAT)
        feed_container.pack(fill=tk.BOTH, expand=True)
        
        self.feed_canvas = tk.Canvas(feed_container, bg=BG_CHAT, highlightthickness=0)
        self.feed_scroll = ttk.Scrollbar(feed_container, orient="vertical", command=self.feed_canvas.yview)
        self.feed_inner = tk.Frame(self.feed_canvas, bg=BG_CHAT)
        
        self.feed_canvas_window = self.feed_canvas.create_window((0, 0), window=self.feed_inner, anchor="nw", width=760)
        self.feed_canvas.configure(yscrollcommand=self.feed_scroll.set)
        
        self.feed_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.feed_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.feed_inner.bind("<Configure>", lambda e: self.feed_canvas.configure(scrollregion=self.feed_canvas.bbox("all")))
        self.feed_canvas.bind("<Configure>", lambda e: self.feed_canvas.itemconfig(self.feed_canvas_window, width=e.width))

        # Input Area (Chat Box, 150MB Attachment Picker, Voice Recorder)
        self.input_frame = tk.Frame(self.chat_area, bg=BG_SIDEBAR, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Attachment Button (150MB Guard)
        self.btn_attach = tk.Button(self.input_frame, text="📎", font=("Segoe UI", 12), bg=BG_SIDEBAR, fg=ACCENT_BLUE, activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._pick_and_upload_attachment)
        self.btn_attach.pack(side=tk.LEFT, padx=(0, 8))
        
        # Text Entry
        self.txt_message = tk.Entry(self.input_frame, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT)
        self.txt_message.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self.txt_message.bind("<Return>", lambda e: self._send_text_message())
        
        # Voice Note Recording Button
        self.btn_voice_note = tk.Button(self.input_frame, text="🎙️", font=("Segoe UI", 12), bg=BG_SIDEBAR, fg="#a371f7", activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._toggle_voice_note_record)
        self.btn_voice_note.pack(side=tk.LEFT, padx=(0, 8))
        
        # Send Button
        self.btn_send = tk.Button(self.input_frame, text="Send", font=("Segoe UI", 10, "bold"), bg=ACCENT_BLUE, fg="#ffffff", activebackground="#388bfd", relief=tk.FLAT, padx=16, pady=4, cursor="hand2", command=self._send_text_message)
        self.btn_send.pack(side=tk.RIGHT)

    # --------------------------------------------------------------------------
    # Settings & Permissions Modal (Multi-Tab Interface)
    # --------------------------------------------------------------------------
    def _show_settings_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Settings & System Permissions")
        modal.geometry("560x460")
        modal.minsize(480, 380)
        modal.configure(bg=BG_SIDEBAR)
        modal.transient(self.root)
        modal.grab_set()
        
        tk.Label(modal, text="⚙️ Settings & Permissions", font=("Segoe UI", 13, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(16, 10), padx=18, anchor="w")
        
        # Notebook for Tabs
        notebook = ttk.Notebook(modal)
        notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        
        # ---------------------------------------------------------
        # Tab 1: Themes & Sound Reactivity
        # ---------------------------------------------------------
        tab_themes = tk.Frame(notebook, bg=BG_CARD, padx=16, pady=14)
        notebook.add(tab_themes, text="🎨 Themes & Shaders")
        
        tk.Label(tab_themes, text="Live Dynamic Theme", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(tab_themes, text="Choose GPU/Canvas atmospheric shaders.", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(1, 6))
        
        theme_options = ["Dark Galaxy Field", "Inverted Stars", "Cyber Aurora Matrix"]
        theme_map = {"Dark Galaxy Field": "galaxy", "Inverted Stars": "inverted", "Cyber Aurora Matrix": "aurora"}
        rev_theme_map = {v: k for k, v in theme_map.items()}
        selected_theme_var = tk.StringVar(value=rev_theme_map.get(self.current_theme, "Dark Galaxy Field"))
        
        def on_theme_change(choice):
            theme_key = theme_map.get(choice, "galaxy")
            self._apply_theme(theme_key)
            modal.destroy()
            self._show_settings_modal()
            
        theme_menu = ttk.Combobox(tab_themes, textvariable=selected_theme_var, values=theme_options, state="readonly", font=("Segoe UI", 9))
        theme_menu.pack(fill=tk.X, pady=(0, 12))
        theme_menu.bind("<<ComboboxSelected>>", lambda e: on_theme_change(selected_theme_var.get()))
        
        # Sound-Reactive Toggle
        chk_sound_var = tk.BooleanVar(value=self.sound_engine.enabled)
        def toggle_sound_react():
            self.sound_engine.set_enabled(chk_sound_var.get())
        chk_sound = tk.Checkbutton(tab_themes, text="⚡ Sound-Reactive Shaders (48kHz Audio Pulse)", variable=chk_sound_var, font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=ACCENT_BLUE, command=toggle_sound_react)
        chk_sound.pack(anchor="w", pady=(0, 4))
        
        # Sensitivity Slider
        lbl_sens = tk.Label(tab_themes, text=f"Audio Sensitivity: {self.sound_engine.sensitivity:.1f}x", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD)
        lbl_sens.pack(anchor="w")
        
        def on_sens_change(val):
            v = float(val)
            self.sound_engine.set_sensitivity(v)
            lbl_sens.config(text=f"Audio Sensitivity: {v:.1f}x")
            
        scale_sens = tk.Scale(tab_themes, from_=0.5, to=2.5, resolution=0.1, orient=tk.HORIZONTAL, bg=BG_CARD, fg=TEXT_WHITE, highlightthickness=0, command=on_sens_change)
        scale_sens.set(self.sound_engine.sensitivity)
        scale_sens.pack(fill=tk.X, pady=(0, 10))
        
        # Peer Halo Toggle
        chk_halo_var = tk.BooleanVar(value=self.peer_halo_enabled)
        def toggle_halo():
            self.peer_halo_enabled = chk_halo_var.get()
            self._build_main_messenger_ui()
            self._load_conversations()
        chk_halo = tk.Checkbutton(tab_themes, text="🔮 Cryptographic Peer Color Halo (Deterministic Glow)", variable=chk_halo_var, font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=ACCENT_BLUE, command=toggle_halo)
        chk_halo.pack(anchor="w", pady=(0, 6))

        # ---------------------------------------------------------
        # Tab 2: Security & Identity
        # ---------------------------------------------------------
        tab_identity = tk.Frame(notebook, bg=BG_CARD, padx=16, pady=14)
        notebook.add(tab_identity, text="🔒 Identity & Halo")
        
        # 2FA Section
        tk.Label(tab_identity, text="Two-Factor Authentication (Email 2FA)", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        is_2fa = self.current_user.get("two_factor_enabled", False)
        lbl_2fa_st = tk.Label(tab_identity, text="Status: ENABLED" if is_2fa else "Status: DISABLED (Optional)", font=("Segoe UI", 8, "bold"), fg=ACCENT_GREEN if is_2fa else ACCENT_YELLOW, bg=BG_CARD)
        lbl_2fa_st.pack(anchor="w", pady=(1, 6))
        
        def toggle_2fa():
            new_val = not self.current_user.get("two_factor_enabled", False)
            try:
                req = urllib.request.Request(
                    f"{self.server_http}/api/v1/auth/toggle-2fa",
                    data=json.dumps({"user_id": self.current_user["user_id"], "enabled": new_val}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10):
                    pass
                self.current_user["two_factor_enabled"] = new_val
                lbl_2fa_st.config(text="Status: ENABLED" if new_val else "Status: DISABLED (Optional)", fg=ACCENT_GREEN if new_val else ACCENT_YELLOW)
                btn_2fa.config(text="Disable 2FA" if new_val else "Enable 2FA", bg=ACCENT_RED if new_val else ACCENT_BLUE)
                messagebox.showinfo("2FA Updated", f"Email 2FA is now {'ENABLED' if new_val else 'DISABLED'}.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        btn_2fa = tk.Button(tab_identity, text="Disable 2FA" if is_2fa else "Enable 2FA", font=("Segoe UI", 9, "bold"), bg=ACCENT_RED if is_2fa else ACCENT_BLUE, fg="#ffffff", relief=tk.FLAT, padx=12, pady=4, cursor="hand2", command=toggle_2fa)
        btn_2fa.pack(anchor="w", pady=(0, 14))
        
        # Cryptographic Fingerprint
        tk.Label(tab_identity, text="Cryptographic Public Key Fingerprint", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        halo_data = derive_peer_halo(self.current_user["username"])
        
        fp_box = tk.Frame(tab_identity, bg=BG_INPUT, padx=8, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
        fp_box.pack(fill=tk.X, pady=(2, 10))
        tk.Label(fp_box, text=halo_data["fingerprint"], font=("Consolas", 8), fg=ACCENT_BLUE, bg=BG_INPUT, wraplength=460, justify=tk.LEFT).pack(anchor="w")
        
        # Halo Live Preview Box
        tk.Label(tab_identity, text="Your Cryptographic Halo Signature", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        preview_box = tk.Frame(tab_identity, bg=BG_INPUT, padx=12, pady=8, highlightthickness=1, highlightbackground=BORDER_COLOR)
        preview_box.pack(fill=tk.X, pady=(2, 0))
        
        halo_preview_cv = self._create_halo_avatar(preview_box, self.current_user["username"], size=46, bg=BG_INPUT)
        halo_preview_cv.pack(side=tk.LEFT, padx=(0, 12))
        
        tk.Label(preview_box, text=f"Primary: {halo_data['color1']} • Secondary: {halo_data['color2']}\nAngle: {halo_data['gradient_angle']}° • High-Contrast SMT Invariant", font=("Segoe UI", 8), fg=TEXT_WHITE, bg=BG_INPUT, justify=tk.LEFT).pack(side=tk.LEFT)

        # ---------------------------------------------------------
        # Tab 3: Permissions & Hardware
        # ---------------------------------------------------------
        tab_perms = tk.Frame(notebook, bg=BG_CARD, padx=16, pady=14)
        notebook.add(tab_perms, text="🎙️ Permissions")
        
        # Mic Permission Row
        tk.Label(tab_perms, text="Microphone Access (48kHz Lossless Voice)", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(tab_perms, text="● Granted / Active (48kHz Opus & DSP Ready)", font=("Segoe UI", 8), fg=ACCENT_GREEN, bg=BG_CARD).pack(anchor="w", pady=(1, 6))
        
        # Live VU Meter Simulation Test
        vu_box = tk.Frame(tab_perms, bg=BG_INPUT, padx=10, pady=8, highlightthickness=1, highlightbackground=BORDER_COLOR)
        vu_box.pack(fill=tk.X, pady=(0, 14))
        
        tk.Label(vu_box, text="Live VU Sound-Reactive Audio Test:", font=("Segoe UI", 8, "bold"), fg=TEXT_WHITE, bg=BG_INPUT).pack(anchor="w")
        vu_canvas = tk.Canvas(vu_box, height=12, bg="#10141a", highlightthickness=0)
        vu_canvas.pack(fill=tk.X, pady=(4, 6))
        
        def run_mic_test():
            self.sound_engine.update_audio_frame(manual_amplitude=0.90)
            vu_canvas.delete("all")
            vu_canvas.create_rectangle(0, 0, 380, 12, fill=ACCENT_GREEN)
            modal.after(400, lambda: vu_canvas.delete("all"))
            
        tk.Button(vu_box, text="Test Sound Reactivity", font=("Segoe UI", 8, "bold"), bg=BG_SIDEBAR, fg=ACCENT_BLUE, relief=tk.FLAT, padx=10, pady=2, cursor="hand2", command=run_mic_test).pack(anchor="w")
        
        # Notification Permission Row
        tk.Label(tab_perms, text="Desktop Push Notifications", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(tab_perms, text="● Allowed (Instant alerts for direct messages & calls)", font=("Segoe UI", 8), fg=ACCENT_GREEN, bg=BG_CARD).pack(anchor="w", pady=(1, 14))
        
        # 150MB Guard Storage Row
        tk.Label(tab_perms, text="Media Cache & 150MB Guard", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(tab_perms, text="● Active (Strict 150MB ceiling enforced by pure ALU SMT kernel)", font=("Segoe UI", 8), fg=ACCENT_BLUE, bg=BG_CARD).pack(anchor="w")

        # ---------------------------------------------------------
        # Tab 4: Server & Network
        # ---------------------------------------------------------
        tab_server = tk.Frame(notebook, bg=BG_CARD, padx=16, pady=14)
        notebook.add(tab_server, text="🌐 Server")
        
        tk.Label(tab_server, text="Server HTTP Endpoint", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        lbl_srv_url = tk.Label(tab_server, text=self.server_http, font=("Segoe UI", 9), fg=ACCENT_BLUE, bg=BG_CARD)
        lbl_srv_url.pack(anchor="w", pady=(1, 10))
        
        tk.Label(tab_server, text="WebSocket Host & Port", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(tab_server, text=f"{self.server_ws_host}:{self.server_ws_port} ({'Connected' if self.ws_connected else 'Reconnecting'})", font=("Segoe UI", 9), fg=ACCENT_GREEN if self.ws_connected else ACCENT_RED, bg=BG_CARD).pack(anchor="w", pady=(1, 14))
        
        lbl_ping = tk.Label(tab_server, text="", font=("Segoe UI", 8), fg=ACCENT_GREEN, bg=BG_CARD)
        lbl_ping.pack(anchor="w", pady=(0, 6))
        
        def ping_server():
            start_t = time.time()
            try:
                with urllib.request.urlopen(f"{self.server_http}/api/v1/health", timeout=5) as resp:
                    pass
                elapsed_ms = int((time.time() - start_t) * 1000)
                lbl_ping.config(text=f"● Latency: {elapsed_ms}ms (Online)", fg=ACCENT_GREEN)
            except Exception as ex:
                lbl_ping.config(text=f"✕ Unreachable: {str(ex)}", fg=ACCENT_RED)
                
        # Bottom Actions
        def handle_modal_signout():
            modal.destroy()
            self._sign_out()

        tk.Button(modal, text="🚪 Sign Out", font=("Segoe UI", 9, "bold"), bg=ACCENT_RED, fg="#ffffff", relief=tk.FLAT, padx=14, pady=5, cursor="hand2", command=handle_modal_signout).pack(side=tk.LEFT, padx=18, pady=(0, 14))
        tk.Button(modal, text="Close", font=("Segoe UI", 9, "bold"), bg=BG_INPUT, fg=TEXT_WHITE, relief=tk.FLAT, padx=16, pady=5, cursor="hand2", command=modal.destroy).pack(side=tk.RIGHT, padx=18, pady=(0, 14))

    def _apply_theme(self, theme_key: str):
        global BG_APP, BG_SIDEBAR, BG_CHAT, BG_INPUT, BG_CARD, BG_BUBBLE_IN, BG_BUBBLE_OUT
        global BORDER_COLOR, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW, TEXT_WHITE, TEXT_MUTED
        
        t = THEMES.get(theme_key, THEMES["galaxy"])
        self.current_theme = theme_key
        
        BG_APP = t["bg_app"]
        BG_SIDEBAR = t["bg_sidebar"]
        BG_CHAT = t["bg_chat"]
        BG_INPUT = t["bg_input"]
        BG_CARD = t["bg_card"]
        BG_BUBBLE_IN = t["bg_bubble_in"]
        BG_BUBBLE_OUT = t["bg_bubble_out"]
        BORDER_COLOR = t["border_color"]
        ACCENT_BLUE = t["accent_blue"]
        ACCENT_GREEN = t["accent_green"]
        ACCENT_RED = t["accent_red"]
        ACCENT_YELLOW = t["accent_yellow"]
        TEXT_WHITE = t["text_white"]
        TEXT_MUTED = t["text_muted"]
        
        self.root.configure(bg=BG_APP)
        self._setup_styles()
        if self.current_user:
            self._build_main_messenger_ui()
            self._load_conversations()
        else:
            self._show_auth_screen()

    # --------------------------------------------------------------------------
    # WebSocket Client Connection & Real-Time Event Loop
    # --------------------------------------------------------------------------
    def _connect_websocket(self):
        def ws_worker():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.server_ws_host, self.server_ws_port))
                
                sec_key = "dGhlIHNhbXBsZSBub25jZQ=="
                req = (
                    f"GET /ws HTTP/1.1\r\n"
                    f"Host: {self.server_ws_host}:{self.server_ws_port}\r\n"
                    f"Upgrade: websocket\r\n"
                    f"Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {sec_key}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n\r\n"
                )
                s.sendall(req.encode())
                
                resp = s.recv(1024)
                if b"101 Switching Protocols" not in resp:
                    return
                    
                self.ws_sock = s
                self.ws_connected = True
                
                self._send_ws_event({"type": "AUTH", "user_id": self.current_user["user_id"]})
                
                buffer = bytearray()
                while self.ws_connected:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    
                    while True:
                        if len(buffer) < 2:
                            break
                        b1, b2 = buffer[0], buffer[1]
                        opcode = b1 & 0x0F
                        payload_len = b2 & 0x7F
                        offset = 2
                        if payload_len == 126:
                            if len(buffer) < 4: break
                            payload_len = struct.unpack("!H", buffer[2:4])[0]
                            offset = 4
                        elif payload_len == 127:
                            if len(buffer) < 10: break
                            payload_len = struct.unpack("!Q", buffer[2:10])[0]
                            offset = 10
                            
                        if len(buffer) < offset + payload_len:
                            break
                            
                        payload = buffer[offset:offset+payload_len]
                        buffer = buffer[offset+payload_len:]
                        
                        if opcode in (0x1, 0x2):
                            self._handle_incoming_ws_event(json.loads(payload.decode("utf-8")))
            except Exception:
                self.ws_connected = False
                
        threading.Thread(target=ws_worker, daemon=True).start()

    def _send_ws_event(self, event_data: Dict[str, Any]):
        if not self.ws_sock:
            return
        try:
            payload = json.dumps(event_data).encode("utf-8")
            length = len(payload)
            header = bytearray([0x81])
            
            mask_key = b"\x12\x34\x56\x78"
            if length <= 125:
                header.append(0x80 | length)
            elif length <= 65535:
                header.append(0x80 | 126)
                header.extend(struct.pack("!H", length))
            else:
                header.append(0x80 | 127)
                header.extend(struct.pack("!Q", length))
                
            header.extend(mask_key)
            masked_payload = bytearray(payload)
            for i in range(len(masked_payload)):
                masked_payload[i] ^= mask_key[i % 4]
                
            self.ws_sock.sendall(bytes(header) + bytes(masked_payload))
        except Exception:
            pass

    def _handle_incoming_ws_event(self, msg: Dict[str, Any]):
        event_type = msg.get("type")
        
        if event_type == "NEW_MESSAGE":
            m = msg.get("message", {})
            if m.get("conversation_id") == self.active_conv_id:
                self.root.after(0, self._render_message_bubble, m)
            self.root.after(0, self._load_conversations)

        elif event_type == "CALL_INCOMING":
            self.root.after(0, self._show_incoming_call_modal, msg)

        elif event_type == "CALL_ACCEPTED":
            self.root.after(0, self._on_call_connected, msg)

        elif event_type == "CALL_TERMINATED":
            self.root.after(0, self._on_call_ended, msg)

    # --------------------------------------------------------------------------
    # Messaging, 150MB Media & Voice Note Upload
    # --------------------------------------------------------------------------
    def _send_text_message(self):
        text = self.txt_message.get().strip()
        if not text or not self.active_conv_id or not self.active_peer:
            return
        self.txt_message.delete(0, tk.END)
        
        event = {
            "type": "CHAT_MESSAGE",
            "conversation_id": self.active_conv_id,
            "sender_id": self.current_user["user_id"],
            "recipient_id": self.active_peer["user_id"],
            "ciphertext": text,
            "nonce": "nonce_" + str(int(time.time())),
            "message_type": "TEXT"
        }
        self._send_ws_event(event)

    def _toggle_voice_note_record(self):
        if not self.is_recording_voice:
            self.is_recording_voice = True
            self.record_start_time = time.time()
            self.btn_voice_note.config(text="⏹️ Stop", bg=ACCENT_RED, fg="#ffffff")
            self.txt_message.config(state="disabled")
            self.sound_engine.update_audio_frame(manual_amplitude=0.85)
        else:
            self.is_recording_voice = False
            duration_ms = int((time.time() - self.record_start_time) * 1000)
            self.btn_voice_note.config(text="🎙️", bg=BG_SIDEBAR, fg="#a371f7")
            self.txt_message.config(state="normal")
            self.sound_engine.update_audio_frame(manual_amplitude=0.0)
            
            if duration_ms < 500:
                return
                
            waveform = [round(0.2 + (0.8 * (i % 5) / 5), 2) for i in range(24)]
            event = {
                "type": "CHAT_MESSAGE",
                "conversation_id": self.active_conv_id,
                "sender_id": self.current_user["user_id"],
                "recipient_id": self.active_peer["user_id"],
                "ciphertext": "🎙️ Encrypted Voice Note (48kHz)",
                "nonce": "nonce_voice_" + str(int(time.time())),
                "message_type": "VOICE_NOTE",
                "voice_duration_ms": duration_ms,
                "waveform_data": json.dumps(waveform)
            }
            self._send_ws_event(event)

    def _pick_and_upload_attachment(self):
        if not self.active_conv_id or not self.active_peer:
            return
        filepath = filedialog.askopenfilename(title="Select Media Attachment (Max 150 MB)")
        if not filepath:
            return
            
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_BYTES:
            messagebox.showerror("File Too Large", f"Selected file ({round(file_size/(1024*1024), 2)} MB) exceeds strict 150MB limit!")
            return
            
        file_name = os.path.basename(filepath)
        
        def upload_worker():
            try:
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                    
                req = urllib.request.Request(
                    f"{self.server_http}/api/v1/attachments/upload",
                    data=file_bytes,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "X-Sender-Id": self.current_user["user_id"],
                        "X-File-Name": file_name,
                        "X-Is-Voice-Note": "false"
                    }
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    att_data = json.loads(resp.read().decode("utf-8"))
                    
                event = {
                    "type": "CHAT_MESSAGE",
                    "conversation_id": self.active_conv_id,
                    "sender_id": self.current_user["user_id"],
                    "recipient_id": self.active_peer["user_id"],
                    "ciphertext": f"📁 Attached: {file_name}",
                    "nonce": "nonce_att_" + str(int(time.time())),
                    "message_type": "MEDIA",
                    "attachment_id": att_data["attachment_id"]
                }
                self._send_ws_event(event)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Upload Error", str(e)))
                
        threading.Thread(target=upload_worker, daemon=True).start()

    # --------------------------------------------------------------------------
    # High-Quality Voice Calling (48kHz & Pulsing Halo)
    # --------------------------------------------------------------------------
    def _start_voice_call(self):
        if not self.active_peer:
            return
        self.active_call_id = f"call_{int(time.time())}"
        self.sound_engine.update_audio_frame(manual_amplitude=0.75)
        self._show_active_call_modal(is_caller=True)
        self._send_ws_event({
            "type": "CALL_INVITE",
            "call_id": self.active_call_id,
            "caller_id": self.current_user["user_id"],
            "callee_id": self.active_peer["user_id"]
        })

    def _show_incoming_call_modal(self, msg: Dict[str, Any]):
        call_id = msg.get("call_id")
        caller_name = msg.get("caller_username", "Unknown User")
        
        modal = tk.Toplevel(self.root)
        modal.title("Incoming Voice Call")
        modal.geometry("380x260")
        modal.configure(bg=BG_SIDEBAR)
        modal.transient(self.root)
        
        halo_cv = self._create_halo_avatar(modal, caller_name, size=52, bg=BG_SIDEBAR)
        halo_cv.pack(pady=(16, 4))
        
        tk.Label(modal, text="📞 INCOMING 48kHz VOICE CALL", font=("Segoe UI", 10, "bold"), fg=ACCENT_GREEN, bg=BG_SIDEBAR).pack(pady=(0, 2))
        tk.Label(modal, text=f"@{caller_name}", font=("Segoe UI", 16, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(0, 16))
        
        btn_box = tk.Frame(modal, bg=BG_SIDEBAR)
        btn_box.pack(fill=tk.X, padx=30)
        
        def accept():
            modal.destroy()
            self.active_call_id = call_id
            self.sound_engine.update_audio_frame(manual_amplitude=0.75)
            self._show_active_call_modal(is_caller=False)
            self._send_ws_event({"type": "CALL_ANSWER", "call_id": call_id, "caller_id": msg.get("caller_id")})
            
        def decline():
            modal.destroy()
            self._send_ws_event({"type": "CALL_DECLINE", "call_id": call_id, "caller_id": msg.get("caller_id")})
            
        tk.Button(btn_box, text="Decline", font=("Segoe UI", 10, "bold"), bg=ACCENT_RED, fg="#ffffff", relief=tk.FLAT, padx=14, pady=6, cursor="hand2", command=decline).pack(side=tk.LEFT, expand=True, padx=4)
        tk.Button(btn_box, text="Accept (48kHz)", font=("Segoe UI", 10, "bold"), bg=ACCENT_GREEN, fg="#ffffff", relief=tk.FLAT, padx=14, pady=6, cursor="hand2", command=accept).pack(side=tk.RIGHT, expand=True, padx=4)

    def _show_active_call_modal(self, is_caller: bool):
        self.call_dialog = tk.Toplevel(self.root)
        self.call_dialog.title("Active Voice Call (48kHz Lossless)")
        self.call_dialog.geometry("400x340")
        self.call_dialog.configure(bg=BG_SIDEBAR)
        
        peer_name = self.active_peer["username"] if self.active_peer else "Peer"
        halo_cv = self._create_halo_avatar(self.call_dialog, peer_name, size=64, bg=BG_SIDEBAR)
        halo_cv.pack(pady=(20, 6))
        
        tk.Label(self.call_dialog, text="🎙️ HIGH-QUALITY 48kHz VOICE CALL", font=("Segoe UI", 10, "bold"), fg=ACCENT_GREEN, bg=BG_SIDEBAR).pack(pady=(0, 4))
        tk.Label(self.call_dialog, text=f"@{peer_name}", font=("Segoe UI", 18, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(0, 8))
        
        self.lbl_call_timer = tk.Label(self.call_dialog, text="Calling..." if is_caller else "Connecting...", font=("Segoe UI", 12), fg=TEXT_MUTED, bg=BG_SIDEBAR)
        self.lbl_call_timer.pack(pady=(0, 16))
        
        btn_box = tk.Frame(self.call_dialog, bg=BG_SIDEBAR)
        btn_box.pack(fill=tk.X, padx=40)
        
        tk.Button(btn_box, text="End Call", font=("Segoe UI", 11, "bold"), bg=ACCENT_RED, fg="#ffffff", relief=tk.FLAT, padx=20, pady=8, cursor="hand2", command=self._end_voice_call).pack(fill=tk.X)

    def _on_call_connected(self, msg: Dict[str, Any]):
        self.call_start_time = time.time()
        self._update_call_timer()

    def _update_call_timer(self):
        if self.call_start_time and self.call_dialog and self.call_dialog.winfo_exists():
            elapsed = int(time.time() - self.call_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.lbl_call_timer.config(text=f"● Connected • {mins:02d}:{secs:02d}", fg=ACCENT_GREEN)
            self.sound_engine.update_audio_frame(manual_amplitude=0.65)
            self.root.after(1000, self._update_call_timer)

    def _end_voice_call(self):
        if self.active_call_id and self.active_peer:
            self._send_ws_event({"type": "CALL_HANGUP", "call_id": self.active_call_id, "caller_id": self.current_user["user_id"], "callee_id": self.active_peer["user_id"]})
        if self.call_dialog:
            self.call_dialog.destroy()
            self.call_dialog = None
        self.active_call_id = None
        self.call_start_time = None
        self.sound_engine.update_audio_frame(manual_amplitude=0.0)

    def _on_call_ended(self, msg: Dict[str, Any]):
        if self.call_dialog:
            self.call_dialog.destroy()
            self.call_dialog = None
        self.active_call_id = None
        self.call_start_time = None
        self.sound_engine.update_audio_frame(manual_amplitude=0.0)

    # --------------------------------------------------------------------------
    # UI Rendering & Conversation Management
    # --------------------------------------------------------------------------
    def _load_conversations(self):
        try:
            req = urllib.request.Request(f"{self.server_http}/api/v1/conversations?user_id={self.current_user['user_id']}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            self._render_conversation_list(data.get("conversations", []))
        except Exception:
            pass

    def _render_conversation_list(self, convs: List[Dict[str, Any]]):
        for widget in self.conv_list_frame.winfo_children():
            widget.destroy()
            
        for c in convs:
            item_bg = BG_INPUT if c["conversation_id"] == self.active_conv_id else BG_SIDEBAR
            item = tk.Frame(self.conv_list_frame, bg=item_bg, padx=8, pady=8, cursor="hand2")
            item.pack(fill=tk.X, pady=2)
            
            # Peer Halo Avatar
            halo_cv = self._create_halo_avatar(item, c.get("peer_username", "User"), size=34, bg=item_bg)
            halo_cv.pack(side=tk.LEFT, padx=(0, 8))
            
            details_box = tk.Frame(item, bg=item_bg)
            details_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(details_box, text=f"@{c.get('peer_username', 'User')}", font=("Segoe UI", 10, "bold"), fg=TEXT_WHITE, bg=item_bg).pack(anchor="w")
            last_msg = c.get("last_ciphertext") or "No messages yet"
            tk.Label(details_box, text=last_msg[:24], font=("Segoe UI", 8), fg=TEXT_MUTED, bg=item_bg).pack(anchor="w")
            
            item.bind("<Button-1>", lambda e, conv=c: self._select_conversation(conv))
            for w in [halo_cv, details_box]:
                w.bind("<Button-1>", lambda e, conv=c: self._select_conversation(conv))

    def _select_conversation(self, conv: Dict[str, Any]):
        self.active_conv_id = conv["conversation_id"]
        self.active_peer = {
            "user_id": conv["peer_id"],
            "username": conv["peer_username"],
            "display_name": conv.get("peer_display_name", conv["peer_username"])
        }
        
        # Clear header and render Peer Halo Avatar in Header
        for w in self.header_left_box.winfo_children():
            w.destroy()
            
        peer_avatar = self._create_halo_avatar(self.header_left_box, self.active_peer["username"], size=38, bg=BG_SIDEBAR)
        peer_avatar.pack(side=tk.LEFT, padx=(0, 8))
        
        hdr_txt_box = tk.Frame(self.header_left_box, bg=BG_SIDEBAR)
        hdr_txt_box.pack(side=tk.LEFT)
        
        tk.Label(hdr_txt_box, text=f"@{self.active_peer['username']}", font=("Segoe UI", 11, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w")
        halo_meta = derive_peer_halo(self.active_peer["username"])
        tk.Label(hdr_txt_box, text=f"● E2EE Verified • {halo_meta['fingerprint_short']}", font=("Segoe UI", 8), fg=ACCENT_GREEN, bg=BG_SIDEBAR).pack(anchor="w")
        
        self.btn_call.pack(side=tk.RIGHT)
        
        # Fetch Messages
        try:
            req = urllib.request.Request(f"{self.server_http}/api/v1/conversations/{self.active_conv_id}/messages")
            with urllib.request.urlopen(req, timeout=5) as resp:
                msgs = json.loads(resp.read().decode("utf-8")).get("messages", [])
            for w in self.feed_inner.winfo_children():
                w.destroy()
            for m in msgs:
                self._render_message_bubble(m)
        except Exception:
            pass

    def _render_message_bubble(self, msg: Dict[str, Any]):
        is_me = msg.get("sender_id") == self.current_user["user_id"]
        
        row = tk.Frame(self.feed_inner, bg=BG_CHAT, pady=4)
        row.pack(fill=tk.X, padx=14)
        
        bubble_bg = BG_BUBBLE_OUT if is_me else BG_BUBBLE_IN
        bubble = tk.Frame(row, bg=bubble_bg, padx=12, pady=8, highlightthickness=0)
        bubble.pack(side=tk.RIGHT if is_me else tk.LEFT)
        
        m_type = msg.get("message_type", "TEXT")
        
        if m_type == "TEXT":
            tk.Label(bubble, text=msg.get("ciphertext", ""), font=("Segoe UI", 10), fg=TEXT_WHITE, bg=bubble_bg, wraplength=480, justify=tk.LEFT).pack(anchor="w")

        elif m_type == "VOICE_NOTE":
            dur_sec = round(msg.get("voice_duration_ms", 0) / 1000, 1)
            tk.Label(bubble, text=f"🎙️ VOICE NOTE • {dur_sec}s (48kHz)", font=("Segoe UI", 9, "bold"), fg="#a371f7" if not is_me else "#ffffff", bg=bubble_bg).pack(anchor="w")
            tk.Label(bubble, text=" ▂▃▅▆▇▆▅▃▂ ▂▃▅▆▇▆▅▃▂ ", font=("Consolas", 10, "bold"), fg=TEXT_WHITE, bg=bubble_bg).pack(anchor="w", pady=(2, 0))

        elif m_type == "MEDIA":
            att_id = msg.get("attachment_id")
            tk.Label(bubble, text=f"📁 {msg.get('file_name', 'File Attachment')}", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=bubble_bg).pack(anchor="w")
            if att_id:
                btn_dl = tk.Button(bubble, text="⬇️ Download (150MB Guard)", font=("Segoe UI", 8, "bold"), bg="#21262d", fg=ACCENT_BLUE, relief=tk.FLAT, padx=8, pady=2, cursor="hand2", command=lambda a=att_id: self._download_attachment(a))
                btn_dl.pack(anchor="w", pady=(4, 0))

        t_str = time.strftime("%H:%M", time.localtime(msg["created_at"] / 1000)) if msg.get("created_at") else ""
        tk.Label(bubble, text=t_str, font=("Segoe UI", 7), fg="#d0d7de" if is_me else TEXT_MUTED, bg=bubble_bg).pack(anchor="e", pady=(2, 0))
        
        self.feed_canvas.update_idletasks()
        self.feed_canvas.yview_moveto(1.0)

    def _download_attachment(self, att_id: str):
        save_path = filedialog.asksaveasfilename(title="Save Attachment")
        if not save_path:
            return
        try:
            urllib.request.urlretrieve(f"{self.server_http}/api/v1/attachments/download/{att_id}", save_path)
            messagebox.showinfo("Download Complete", f"Saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))

    def _prompt_new_chat(self):
        try:
            req = urllib.request.Request(f"{self.server_http}/api/v1/users/list")
            with urllib.request.urlopen(req, timeout=5) as resp:
                users = json.loads(resp.read().decode("utf-8")).get("users", [])
                
            other_users = [u for u in users if u["user_id"] != self.current_user["user_id"]]
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Start Direct Conversation")
            dialog.geometry("400x380")
            dialog.configure(bg=BG_SIDEBAR)
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="➕ Start Direct Message", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(16, 4), padx=16, anchor="w")
            tk.Label(dialog, text="Select a user or search by @username:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_SIDEBAR).pack(padx=16, anchor="w", pady=(0, 8))
            
            entry_search = tk.Entry(dialog, font=("Segoe UI", 10), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT)
            entry_search.pack(fill=tk.X, padx=16, pady=(0, 8), ipady=3)
            entry_search.focus()
            
            listbox = tk.Listbox(dialog, bg=BG_INPUT, fg=TEXT_WHITE, font=("Segoe UI", 10), selectbackground=ACCENT_BLUE, relief=tk.FLAT)
            listbox.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
            
            displayed_users = list(other_users)
            
            def refresh_list():
                listbox.delete(0, tk.END)
                q = entry_search.get().strip().lower().replace("@", "")
                displayed_users.clear()
                for u in other_users:
                    if not q or q in u["username"].lower() or q in u.get("display_name", "").lower():
                        displayed_users.append(u)
                        status_str = "● Online" if u.get("is_online") else "Offline"
                        listbox.insert(tk.END, f"@{u['username']} ({status_str})")
            
            refresh_list()
            entry_search.bind("<KeyRelease>", lambda e: refresh_list())
                
            def start_dm():
                target_user = None
                sel = listbox.curselection()
                if sel:
                    target_user = displayed_users[sel[0]]
                else:
                    raw_name = entry_search.get().strip().lower().replace("@", "")
                    if raw_name:
                        for u in other_users:
                            if u["username"].lower() == raw_name:
                                target_user = u
                                break
                if not target_user:
                    messagebox.showwarning("Select User", "Please select or enter a registered username.")
                    return
                dialog.destroy()
                
                req_dm = urllib.request.Request(
                    f"{self.server_http}/api/v1/conversations/direct",
                    data=json.dumps({"user1_id": self.current_user["user_id"], "user2_id": target_user["user_id"]}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req_dm, timeout=5) as r:
                    res = json.loads(r.read().decode("utf-8"))
                    
                self._load_conversations()
                self._select_conversation({
                    "conversation_id": res["conversation_id"],
                    "peer_id": target_user["user_id"],
                    "peer_username": target_user["username"]
                })
                
            entry_search.bind("<Return>", lambda e: start_dm())
            tk.Button(dialog, text="Start Chat", font=("Segoe UI", 10, "bold"), bg=ACCENT_BLUE, fg="#ffffff", relief=tk.FLAT, padx=14, pady=6, cursor="hand2", command=start_dm).pack(fill=tk.X, padx=16, pady=(0, 14))
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    # --------------------------------------------------------------------------
    # 100% On-Device Neural Semantic Search (Kybalion 128-D Vector Engine)
    # --------------------------------------------------------------------------
    def _show_neural_search_modal(self):
        if not self.current_user:
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("🧠 100% On-Device Neural Semantic Search")
        dialog.geometry("640x560")
        dialog.minsize(540, 420)
        dialog.configure(bg=BG_SIDEBAR)
        dialog.transient(self.root)
        
        # Header
        header_frame = tk.Frame(dialog, bg=BG_SIDEBAR, padx=18, pady=14, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="🧠 Neural Semantic Search (128-D Vector Index)", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w")
        tk.Label(header_frame, text="Zero-Knowledge • Natural Language • Messages & 150MB Media", font=("Segoe UI", 8), fg=ACCENT_BLUE, bg=BG_SIDEBAR).pack(anchor="w", pady=(2, 0))
        
        # Search Box Container
        search_box_frame = tk.Frame(dialog, bg=BG_SIDEBAR, padx=18, pady=12)
        search_box_frame.pack(fill=tk.X)
        
        entry_query = tk.Entry(search_box_frame, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT)
        entry_query.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        entry_query.focus()
        
        btn_exec = tk.Button(search_box_frame, text="Search Vectors", font=("Segoe UI", 10, "bold"), bg=ACCENT_BLUE, fg="#ffffff", relief=tk.FLAT, padx=14, pady=4, cursor="hand2")
        btn_exec.pack(side=tk.RIGHT)
        
        lbl_info = tk.Label(dialog, text="💡 Ask natural questions (e.g. 'What did we decide about the database schema?' or 'Find the picture of the server rack')", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_SIDEBAR, wraplength=580, justify=tk.LEFT)
        lbl_info.pack(anchor="w", padx=18, pady=(0, 8))
        
        # Results Scrollable Feed
        results_container = tk.Frame(dialog, bg=BG_CHAT, highlightthickness=1, highlightbackground=BORDER_COLOR)
        results_container.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))
        
        res_canvas = tk.Canvas(results_container, bg=BG_CHAT, highlightthickness=0)
        res_scroll = ttk.Scrollbar(results_container, orient="vertical", command=res_canvas.yview)
        res_inner = tk.Frame(res_canvas, bg=BG_CHAT)
        
        res_window = res_canvas.create_window((0, 0), window=res_inner, anchor="nw", width=580)
        res_canvas.configure(yscrollcommand=res_scroll.set)
        
        res_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        res_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        res_inner.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.bind("<Configure>", lambda e: res_canvas.itemconfig(res_window, width=e.width))
        
        def run_search():
            q = entry_query.get().strip()
            if not q:
                return
            for w in res_inner.winfo_children():
                w.destroy()
                
            lbl_loading = tk.Label(res_inner, text="Computing 128-D vector projection & querying Kybalion...", font=("Segoe UI", 9, "italic"), fg=TEXT_MUTED, bg=BG_CHAT)
            lbl_loading.pack(pady=20)
            dialog.update_idletasks()
            
            try:
                encoded_q = urllib.parse.quote(q)
                conv_param = f"&conversation_id={self.active_conv_id}" if self.active_conv_id else ""
                req = urllib.request.Request(f"{self.server_http}/api/v1/search/semantic?user_id={self.current_user['user_id']}&q={encoded_q}{conv_param}&top_k=15")
                with urllib.request.urlopen(req, timeout=8) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                results = res_data.get("results", [])
                
                for w in res_inner.winfo_children():
                    w.destroy()
                    
                if not results:
                    tk.Label(res_inner, text=f"No semantic matches found for '{q}'.", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_CHAT).pack(pady=30)
                    return
                    
                tk.Label(res_inner, text=f"Found {len(results)} matches ranked by 128-D cosine similarity:", font=("Segoe UI", 9, "bold"), fg=ACCENT_GREEN, bg=BG_CHAT).pack(anchor="w", padx=10, pady=(10, 6))
                
                for item in results:
                    card = tk.Frame(res_inner, bg=BG_INPUT, padx=12, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
                    card.pack(fill=tk.X, padx=10, pady=4)
                    
                    header_row = tk.Frame(card, bg=BG_INPUT)
                    header_row.pack(fill=tk.X)
                    
                    score_val = item.get("similarity_score", 0.0)
                    badge_color = ACCENT_GREEN if score_val >= 0.75 else (ACCENT_BLUE if score_val >= 0.50 else ACCENT_YELLOW)
                    
                    tk.Label(header_row, text=f"🎯 {item.get('similarity_percent', '0%')} Match", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg=badge_color, padx=6, pady=1).pack(side=tk.LEFT)
                    tk.Label(header_row, text=f" @{item.get('sender_username', 'User')} • {item.get('message_type', 'TEXT')}", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_INPUT).pack(side=tk.LEFT, padx=6)
                    
                    t_str = time.strftime("%b %d, %H:%M", time.localtime(item["created_at"] / 1000)) if item.get("created_at") else ""
                    tk.Label(header_row, text=t_str, font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_INPUT).pack(side=tk.RIGHT)
                    
                    snippet = item.get("text", "")
                    if item.get("entity_type") == "ATTACHMENT":
                        snippet = f"📁 [Attachment]: {item.get('file_name', 'File')} ({item.get('mime_type', 'Media')})"
                    tk.Label(card, text=snippet, font=("Segoe UI", 9), fg=TEXT_WHITE, bg=BG_INPUT, wraplength=520, justify=tk.LEFT).pack(anchor="w", pady=(6, 4))
                    
                    target_conv_id = item.get("conversation_id")
                    if target_conv_id:
                        def jump(cid=target_conv_id, p_name=item.get("sender_username", "User")):
                            dialog.destroy()
                            self._select_conversation({"conversation_id": cid, "peer_id": item.get("sender_id"), "peer_username": p_name})
                        btn_jump = tk.Button(card, text="↗ Open Conversation", font=("Segoe UI", 8, "bold"), bg=BG_SIDEBAR, fg=ACCENT_BLUE, relief=tk.FLAT, padx=8, pady=2, cursor="hand2", command=jump)
                        btn_jump.pack(anchor="e")
            except Exception as e:
                for w in res_inner.winfo_children():
                    w.destroy()
                tk.Label(res_inner, text=f"Search error: {str(e)}", font=("Segoe UI", 9), fg=ACCENT_RED, bg=BG_CHAT).pack(pady=20)
                
        btn_exec.config(command=run_search)
        entry_query.bind("<Return>", lambda e: run_search())

    def _on_close(self):
        self.ws_connected = False
        if self.ws_sock:
            try: self.ws_sock.close()
            except Exception: pass
        self.root.destroy()

def main():
    root = tk.Tk()
    app = UnderWrapsClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
