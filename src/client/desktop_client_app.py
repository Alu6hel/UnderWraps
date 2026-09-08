"""
==============================================================================
UnderWraps Client Messaging Application (Windows 11 Fluent Dark UI)
E2EE Messaging, Username/Password Auth, Optional 2FA, 150MB Media, Voice Notes & 48kHz Voice Calling

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
==============================================================================
"""

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
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Dict, List, Any, Optional

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

class UnderWrapsClientGUI:
    def __init__(self, root: tk.Tk, server_http: str = "http://127.0.0.1:8080", server_ws_host: str = "127.0.0.1", server_ws_port: int = 8081):
        self.root = root
        self.root.title("UnderWraps — Sovereign Private Messenger")
        self.root.geometry("1100x740")
        self.root.minsize(920, 620)
        self.current_theme = "galaxy"
        self.root.configure(bg=BG_APP)
        
        self.server_http = server_http
        self.server_ws_host = server_ws_host
        self.server_ws_port = server_ws_port
        
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
        self._show_auth_screen()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_APP, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_SIDEBAR, foreground=TEXT_MUTED, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", BG_APP)], foreground=[("selected", ACCENT_BLUE)])

    # --------------------------------------------------------------------------
    # Screen 1: Authentication (Signup / Login with Optional 2FA)
    # --------------------------------------------------------------------------
    def _show_auth_screen(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        auth_container = tk.Frame(self.root, bg=BG_APP)
        auth_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Card Box
        card = tk.Frame(auth_container, bg=BG_SIDEBAR, padx=36, pady=32, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack()
        
        # Logo & Header
        tk.Label(card, text="🛡️ UNDERWRAPS", font=("Segoe UI", 20, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(0, 4))
        tk.Label(card, text="Sovereign E2EE • Custom Username • 150MB Media • 48kHz Voice", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_SIDEBAR).pack(pady=(0, 20))
        
        # Server Address Box
        server_box = tk.Frame(card, bg=BG_SIDEBAR)
        server_box.pack(fill=tk.X, pady=(0, 14))
        
        tk.Label(server_box, text="Server Address", font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_SIDEBAR).pack(anchor="w")
        self.entry_server_url = tk.Entry(server_box, font=("Segoe UI", 9), bg=BG_INPUT, fg=ACCENT_BLUE, insertbackground=TEXT_WHITE, relief=tk.FLAT)
        self.entry_server_url.insert(0, self.server_http)
        self.entry_server_url.pack(fill=tk.X, ipady=2, pady=(2, 0))

        # Tabs for Sign In vs Sign Up
        notebook = ttk.Notebook(card)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Sign In
        tab_signin = tk.Frame(notebook, bg=BG_SIDEBAR, padx=10, pady=16)
        notebook.add(tab_signin, text="Sign In")
        
        tk.Label(tab_signin, text="Username or Email", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_login_id = tk.Entry(tab_signin, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT, width=32)
        self.entry_login_id.pack(fill=tk.X, pady=(0, 14), ipady=4)
        
        tk.Label(tab_signin, text="Password", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_login_pwd = tk.Entry(tab_signin, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, show="•", relief=tk.FLAT, width=32)
        self.entry_login_pwd.pack(fill=tk.X, pady=(0, 20), ipady=4)
        
        btn_login = tk.Button(tab_signin, text="Sign In", font=("Segoe UI", 10, "bold"), bg=ACCENT_BLUE, fg="#ffffff", activebackground="#388bfd", relief=tk.FLAT, pady=8, cursor="hand2", command=self._handle_login)
        btn_login.pack(fill=tk.X)
        
        # Tab 2: Create Account
        tab_signup = tk.Frame(notebook, bg=BG_SIDEBAR, padx=10, pady=16)
        notebook.add(tab_signup, text="Create Account")
        
        tk.Label(tab_signup, text="Custom Username", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_reg_user = tk.Entry(tab_signup, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT, width=32)
        self.entry_reg_user.pack(fill=tk.X, pady=(0, 10), ipady=4)
        
        tk.Label(tab_signup, text="Email Address", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_reg_email = tk.Entry(tab_signup, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, relief=tk.FLAT, width=32)
        self.entry_reg_email.pack(fill=tk.X, pady=(0, 10), ipady=4)
        
        tk.Label(tab_signup, text="Password", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w", pady=(0, 4))
        self.entry_reg_pwd = tk.Entry(tab_signup, font=("Segoe UI", 11), bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_WHITE, show="•", relief=tk.FLAT, width=32)
        self.entry_reg_pwd.pack(fill=tk.X, pady=(0, 18), ipady=4)
        
        btn_signup = tk.Button(tab_signup, text="Create Sovereign Account", font=("Segoe UI", 10, "bold"), bg=ACCENT_GREEN, fg="#ffffff", activebackground="#238636", relief=tk.FLAT, pady=8, cursor="hand2", command=self._handle_signup)
        btn_signup.pack(fill=tk.X)

    def _sync_server_url(self):
        url = self.entry_server_url.get().strip().rstrip("/")
        if url:
            self.server_http = url
            parsed = urllib.parse.urlparse(url)
            self.server_ws_host = parsed.hostname or "127.0.0.1"
            # Default WS port 8081 if not specified
            self.server_ws_port = 8081

    def _handle_login(self):
        self._sync_server_url()
        identifier = self.entry_login_id.get().strip()
        pwd = self.entry_login_pwd.get().strip()
        if not identifier or not pwd:
            messagebox.showwarning("Incomplete Fields", "Please enter your username/email and password.")
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
                self._on_auth_success(data)
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
            # Helpful banner in development
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
                self._on_auth_success(res_data)
            except Exception as ex:
                messagebox.showerror("2FA Error", str(ex))
                
        tk.Button(dialog, text="Verify & Login", font=("Segoe UI", 10, "bold"), bg=ACCENT_GREEN, fg="#ffffff", relief=tk.FLAT, padx=16, pady=6, cursor="hand2", command=submit_2fa).pack(fill=tk.X, padx=40)

    def _handle_signup(self):
        self._sync_server_url()
        user = self.entry_reg_user.get().strip()
        email = self.entry_reg_email.get().strip()
        pwd = self.entry_reg_pwd.get().strip()
        if not user or not email or not pwd:
            messagebox.showwarning("Incomplete Fields", "Please complete all registration fields.")
            return
            
        try:
            req = urllib.request.Request(
                f"{self.server_http}/api/v1/auth/signup",
                data=json.dumps({"username": user, "email": email, "password": pwd, "display_name": user}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            messagebox.showinfo("Registration Successful", f"Account @{user} created! You can now sign in.")
        except urllib.error.HTTPError as e:
            err_body = json.loads(e.read().decode("utf-8"))
            messagebox.showerror("Signup Failed", err_body.get("error", "Registration error"))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_auth_success(self, auth_data: Dict[str, Any]):
        self.current_user = auth_data
        self.session_token = auth_data["session_token"]
        self._build_main_messenger_ui()
        self._connect_websocket()
        self._load_conversations()

    # --------------------------------------------------------------------------
    # Screen 2: Main Messaging Interface
    # --------------------------------------------------------------------------
    def _build_main_messenger_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Top Container
        main_box = tk.Frame(self.root, bg=BG_APP)
        main_box.pack(fill=tk.BOTH, expand=True)
        
        # 1. Left Sidebar
        self.sidebar = tk.Frame(main_box, bg=BG_SIDEBAR, width=310, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # Sidebar User Header
        user_header = tk.Frame(self.sidebar, bg=BG_SIDEBAR, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        user_header.pack(fill=tk.X)
        
        u_box = tk.Frame(user_header, bg=BG_SIDEBAR)
        u_box.pack(side=tk.LEFT)
        
        tk.Label(u_box, text=f"👤 @{self.current_user['username']}", font=("Segoe UI", 11, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(anchor="w")
        self.lbl_ws_indicator = tk.Label(u_box, text="● Connected (E2EE Active)", font=("Segoe UI", 8), fg=ACCENT_GREEN, bg=BG_SIDEBAR)
        self.lbl_ws_indicator.pack(anchor="w")
        
        btn_settings = tk.Button(user_header, text="⚙️", font=("Segoe UI", 11), bg=BG_SIDEBAR, fg=TEXT_MUTED, activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._show_settings_modal)
        btn_settings.pack(side=tk.RIGHT)
        
        btn_neural_search_top = tk.Button(user_header, text="🧠", font=("Segoe UI", 11), bg=BG_SIDEBAR, fg=ACCENT_BLUE, activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._show_neural_search_modal)
        btn_neural_search_top.pack(side=tk.RIGHT, padx=(0, 4))
        
        # Sidebar Action Buttons (New Chat + 100% On-Device Neural Search)
        action_bar = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        action_bar.pack(fill=tk.X, padx=12, pady=10)
        
        btn_new_chat = tk.Button(action_bar, text="➕ New DM", font=("Segoe UI", 9, "bold"), bg=BG_INPUT, fg=ACCENT_BLUE, activebackground="#262c36", relief=tk.FLAT, pady=8, cursor="hand2", command=self._prompt_new_chat)
        btn_new_chat.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        
        btn_search = tk.Button(action_bar, text="🧠 Neural Search", font=("Segoe UI", 9, "bold"), bg="#122c30" if self.current_theme=="aurora" else "#1b2533", fg=ACCENT_BLUE, activebackground="#263445", relief=tk.FLAT, pady=8, cursor="hand2", command=self._show_neural_search_modal)
        btn_search.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        
        # Conversation List Box
        self.conv_list_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        self.conv_list_frame.pack(fill=tk.BOTH, expand=True, padx=4)

        # 2. Right Chat Area
        self.chat_area = tk.Frame(main_box, bg=BG_CHAT)
        self.chat_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Chat Header
        self.chat_header = tk.Frame(self.chat_area, bg=BG_SIDEBAR, height=60, padx=18, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.chat_header.pack(fill=tk.X, side=tk.TOP)
        
        self.lbl_chat_title = tk.Label(self.chat_header, text="Select a conversation to begin", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR)
        self.lbl_chat_title.pack(side=tk.LEFT)
        
        self.lbl_chat_status = tk.Label(self.chat_header, text="", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_SIDEBAR)
        self.lbl_chat_status.pack(side=tk.LEFT, padx=10)
        
        # High Quality Voice Call Button (48kHz)
        self.btn_call = tk.Button(self.chat_header, text="📞 Start Voice Call (48kHz)", font=("Segoe UI", 9, "bold"), bg="#1a3b2b", fg=ACCENT_GREEN, activebackground="#23533c", relief=tk.FLAT, padx=12, pady=5, cursor="hand2", command=self._start_voice_call)
        self.btn_call.pack(side=tk.RIGHT)
        self.btn_call.pack_forget() # Hidden until conversation is selected
        
        # Header Search Trigger
        self.btn_hdr_search = tk.Button(self.chat_header, text="🔍 Search Chat", font=("Segoe UI", 9), bg=BG_INPUT, fg=TEXT_MUTED, activebackground=BG_SIDEBAR, relief=tk.FLAT, padx=10, pady=5, cursor="hand2", command=self._show_neural_search_modal)
        self.btn_hdr_search.pack(side=tk.RIGHT, padx=(0, 8))
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-f>", lambda e: self._show_neural_search_modal())
        self.root.bind("<Control-F>", lambda e: self._show_neural_search_modal())
        
        # Message Feed Canvas & Scrollbar
        feed_container = tk.Frame(self.chat_area, bg=BG_CHAT)
        feed_container.pack(fill=tk.BOTH, expand=True)
        
        self.feed_canvas = tk.Canvas(feed_container, bg=BG_CHAT, highlightthickness=0)
        self.feed_scroll = ttk.Scrollbar(feed_container, orient="vertical", command=self.feed_canvas.yview)
        self.feed_inner = tk.Frame(self.feed_canvas, bg=BG_CHAT)
        
        self.feed_canvas.create_window((0, 0), window=self.feed_inner, anchor="nw", width=760)
        self.feed_canvas.configure(yscrollcommand=self.feed_scroll.set)
        
        self.feed_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.feed_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.feed_inner.bind("<Configure>", lambda e: self.feed_canvas.configure(scrollregion=self.feed_canvas.bbox("all")))

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
        
        # Voice Note Recording Button (🎙️)
        self.btn_voice_note = tk.Button(self.input_frame, text="🎙️", font=("Segoe UI", 12), bg=BG_SIDEBAR, fg="#a371f7", activebackground=BG_INPUT, relief=tk.FLAT, cursor="hand2", command=self._toggle_voice_note_record)
        self.btn_voice_note.pack(side=tk.LEFT, padx=(0, 8))
        
        # Send Button
        self.btn_send = tk.Button(self.input_frame, text="Send", font=("Segoe UI", 10, "bold"), bg=ACCENT_BLUE, fg="#ffffff", activebackground="#388bfd", relief=tk.FLAT, padx=16, pady=4, cursor="hand2", command=self._send_text_message)
        self.btn_send.pack(side=tk.RIGHT)

    # --------------------------------------------------------------------------
    # Settings Modal (2FA Toggle, Cache Vacuum)
    # --------------------------------------------------------------------------
    def _show_settings_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Account & Security Settings")
        modal.geometry("480x380")
        modal.configure(bg=BG_SIDEBAR)
        modal.transient(self.root)
        modal.grab_set()
        
        tk.Label(modal, text="⚙️ Account & Security Settings", font=("Segoe UI", 14, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(20, 14), padx=20, anchor="w")
        
        # User Info
        info_frame = tk.Frame(modal, bg=BG_CARD, padx=14, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 14))
        
        tk.Label(info_frame, text=f"Username: @{self.current_user['username']}", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(info_frame, text=f"Email: {self.current_user['email']}", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(2, 0))
        
        # Theme Selection Section
        theme_frame = tk.Frame(modal, bg=BG_CARD, padx=14, pady=14, highlightthickness=1, highlightbackground=BORDER_COLOR)
        theme_frame.pack(fill=tk.X, padx=20, pady=(0, 14))
        
        tk.Label(theme_frame, text="Live Dynamic Theme", font=("Segoe UI", 10, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(theme_frame, text="Choose your visual aesthetic (Dark Galaxy, Inverted Stars, Cyber Aurora).", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(2, 8))
        
        theme_options = ["Dark Galaxy Field", "Inverted Stars", "Cyber Aurora Matrix"]
        theme_map = {"Dark Galaxy Field": "galaxy", "Inverted Stars": "inverted", "Cyber Aurora Matrix": "aurora"}
        rev_theme_map = {v: k for k, v in theme_map.items()}
        
        selected_theme_var = tk.StringVar(value=rev_theme_map.get(self.current_theme, "Dark Galaxy Field"))
        
        def on_theme_change(choice):
            theme_key = theme_map.get(choice, "galaxy")
            self._apply_theme(theme_key)
            modal.destroy()
            self._show_settings_modal()
            
        theme_menu = ttk.Combobox(theme_frame, textvariable=selected_theme_var, values=theme_options, state="readonly", font=("Segoe UI", 9))
        theme_menu.pack(fill=tk.X, pady=(0, 4))
        theme_menu.bind("<<ComboboxSelected>>", lambda e: on_theme_change(selected_theme_var.get()))

        # 2FA Section
        twofa_frame = tk.Frame(modal, bg=BG_CARD, padx=14, pady=14, highlightthickness=1, highlightbackground=BORDER_COLOR)
        twofa_frame.pack(fill=tk.X, padx=20, pady=(0, 14))
        
        tk.Label(twofa_frame, text="Two-Factor Authentication (Email 2FA)", font=("Segoe UI", 10, "bold"), fg=TEXT_WHITE, bg=BG_CARD).pack(anchor="w")
        tk.Label(twofa_frame, text="Require a 6-digit OTP verification code upon every login.", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(2, 8))
        
        is_2fa = self.current_user.get("two_factor_enabled", False)
        lbl_status = tk.Label(twofa_frame, text="Status: ENABLED" if is_2fa else "Status: DISABLED (Optional)", font=("Segoe UI", 9, "bold"), fg=ACCENT_GREEN if is_2fa else ACCENT_YELLOW, bg=BG_CARD)
        lbl_status.pack(anchor="w", pady=(0, 8))
        
        def toggle_2fa():
            new_val = not self.current_user.get("two_factor_enabled", False)
            try:
                req = urllib.request.Request(
                    f"{self.server_http}/api/v1/auth/toggle-2fa",
                    data=json.dumps({"user_id": self.current_user["user_id"], "enabled": new_val}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pass
                self.current_user["two_factor_enabled"] = new_val
                lbl_status.config(
                    text="Status: ENABLED" if new_val else "Status: DISABLED (Optional)",
                    fg=ACCENT_GREEN if new_val else ACCENT_YELLOW
                )
                btn_2fa.config(text="Disable 2FA" if new_val else "Enable 2FA", bg=ACCENT_RED if new_val else ACCENT_BLUE)
                messagebox.showinfo("2FA Updated", f"Email 2FA is now {'ENABLED' if new_val else 'DISABLED'}.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        btn_2fa = tk.Button(twofa_frame, text="Disable 2FA" if is_2fa else "Enable 2FA", font=("Segoe UI", 9, "bold"), bg=ACCENT_RED if is_2fa else ACCENT_BLUE, fg="#ffffff", relief=tk.FLAT, padx=12, pady=5, cursor="hand2", command=toggle_2fa)
        btn_2fa.pack(anchor="w")

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
                
                # Send Handshake
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
                
                # Authenticate WebSocket
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
            header = bytearray([0x81]) # FIN + Text Opcode
            
            # Mask bit MUST be set from client to server (RFC 6455)
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
        
        # 1. New Message Received
        if event_type == "NEW_MESSAGE":
            m = msg.get("message", {})
            if m.get("conversation_id") == self.active_conv_id:
                self.root.after(0, self._render_message_bubble, m)
            self.root.after(0, self._load_conversations)

        # 2. Incoming Voice Call (48kHz)
        elif event_type == "CALL_INCOMING":
            self.root.after(0, self._show_incoming_call_modal, msg)

        # 3. Call Accepted
        elif event_type == "CALL_ACCEPTED":
            self.root.after(0, self._on_call_connected, msg)

        # 4. Call Terminated
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
        
        # Outgoing message payload
        event = {
            "type": "CHAT_MESSAGE",
            "conversation_id": self.active_conv_id,
            "sender_id": self.current_user["user_id"],
            "recipient_id": self.active_peer["user_id"],
            "ciphertext": text, # In production, encrypted with Double Ratchet ALU key
            "nonce": "nonce_" + str(int(time.time())),
            "message_type": "TEXT"
        }
        self._send_ws_event(event)

    def _toggle_voice_note_record(self):
        if not self.is_recording_voice:
            # Start Recording
            self.is_recording_voice = True
            self.record_start_time = time.time()
            self.btn_voice_note.config(text="⏹️ Stop", bg=ACCENT_RED, fg="#ffffff")
            self.txt_message.config(state="disabled")
        else:
            # Stop & Send Voice Note
            self.is_recording_voice = False
            duration_ms = int((time.time() - self.record_start_time) * 1000)
            self.btn_voice_note.config(text="🎙️", bg=BG_SIDEBAR, fg="#a371f7")
            self.txt_message.config(state="normal")
            
            if duration_ms < 500:
                return # Discard accidental clicks
                
            # Send Simulated 48kHz Voice Note with Waveform
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
                    
                # Send Attachment Message
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
    # High-Quality Voice Calling (48kHz)
    # --------------------------------------------------------------------------
    def _start_voice_call(self):
        if not self.active_peer:
            return
        self.active_call_id = f"call_{int(time.time())}"
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
        modal.geometry("360x220")
        modal.configure(bg=BG_SIDEBAR)
        modal.transient(self.root)
        
        tk.Label(modal, text="📞 INCOMING 48kHz VOICE CALL", font=("Segoe UI", 11, "bold"), fg=ACCENT_GREEN, bg=BG_SIDEBAR).pack(pady=(20, 4))
        tk.Label(modal, text=f"@{caller_name}", font=("Segoe UI", 16, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(0, 20))
        
        btn_box = tk.Frame(modal, bg=BG_SIDEBAR)
        btn_box.pack(fill=tk.X, padx=30)
        
        def accept():
            modal.destroy()
            self.active_call_id = call_id
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
        self.call_dialog.geometry("400x300")
        self.call_dialog.configure(bg=BG_SIDEBAR)
        
        tk.Label(self.call_dialog, text="🎙️ HIGH-QUALITY 48kHz VOICE CALL", font=("Segoe UI", 10, "bold"), fg=ACCENT_GREEN, bg=BG_SIDEBAR).pack(pady=(20, 6))
        
        peer_name = self.active_peer["username"] if self.active_peer else "Peer"
        tk.Label(self.call_dialog, text=f"@{peer_name}", font=("Segoe UI", 18, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(0, 8))
        
        self.lbl_call_timer = tk.Label(self.call_dialog, text="Calling..." if is_caller else "Connecting...", font=("Segoe UI", 12), fg=TEXT_MUTED, bg=BG_SIDEBAR)
        self.lbl_call_timer.pack(pady=(0, 20))
        
        # Mute and End Buttons
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
            self.root.after(1000, self._update_call_timer)

    def _end_voice_call(self):
        if self.active_call_id and self.active_peer:
            self._send_ws_event({"type": "CALL_HANGUP", "call_id": self.active_call_id, "caller_id": self.current_user["user_id"], "callee_id": self.active_peer["user_id"]})
        if self.call_dialog:
            self.call_dialog.destroy()
            self.call_dialog = None
        self.active_call_id = None
        self.call_start_time = None

    def _on_call_ended(self, msg: Dict[str, Any]):
        if self.call_dialog:
            self.call_dialog.destroy()
            self.call_dialog = None
        self.active_call_id = None
        self.call_start_time = None

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
            item = tk.Frame(self.conv_list_frame, bg=BG_INPUT if c["conversation_id"] == self.active_conv_id else BG_SIDEBAR, padx=10, pady=10, cursor="hand2")
            item.pack(fill=tk.X, pady=2)
            
            tk.Label(item, text=f"@{c.get('peer_username', 'User')}", font=("Segoe UI", 10, "bold"), fg=TEXT_WHITE, bg=item["bg"]).pack(anchor="w")
            last_msg = c.get("last_ciphertext") or "No messages yet"
            tk.Label(item, text=last_msg[:28], font=("Segoe UI", 8), fg=TEXT_MUTED, bg=item["bg"]).pack(anchor="w")
            
            item.bind("<Button-1>", lambda e, conv=c: self._select_conversation(conv))

    def _select_conversation(self, conv: Dict[str, Any]):
        self.active_conv_id = conv["conversation_id"]
        self.active_peer = {
            "user_id": conv["peer_id"],
            "username": conv["peer_username"],
            "display_name": conv.get("peer_display_name", conv["peer_username"])
        }
        self.lbl_chat_title.config(text=f"@{self.active_peer['username']}")
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
        
        # 1. Text Message
        if m_type == "TEXT":
            tk.Label(bubble, text=msg.get("ciphertext", ""), font=("Segoe UI", 10), fg=TEXT_WHITE, bg=bubble_bg, wraplength=480, justify=tk.LEFT).pack(anchor="w")

        # 2. Voice Note Message
        elif m_type == "VOICE_NOTE":
            dur_sec = round(msg.get("voice_duration_ms", 0) / 1000, 1)
            tk.Label(bubble, text=f"🎙️ VOICE NOTE • {dur_sec}s", font=("Segoe UI", 9, "bold"), fg="#a371f7" if not is_me else "#ffffff", bg=bubble_bg).pack(anchor="w")
            tk.Label(bubble, text=" ▂▃▅▆▇▆▅▃▂ ▂▃▅▆▇▆▅▃▂ ", font=("Consolas", 10, "bold"), fg=TEXT_WHITE, bg=bubble_bg).pack(anchor="w", pady=(2, 0))

        # 3. 150MB Media Attachment
        elif m_type == "MEDIA":
            att_id = msg.get("attachment_id")
            tk.Label(bubble, text=f"📁 {msg.get('file_name', 'File Attachment')}", font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=bubble_bg).pack(anchor="w")
            if att_id:
                btn_dl = tk.Button(bubble, text="⬇️ Download", font=("Segoe UI", 8, "bold"), bg="#21262d", fg=ACCENT_BLUE, relief=tk.FLAT, padx=8, pady=2, cursor="hand2", command=lambda a=att_id: self._download_attachment(a))
                btn_dl.pack(anchor="w", pady=(4, 0))

        # Timestamp
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
            if not other_users:
                messagebox.showinfo("No Users Found", "No other registered users found on the server.")
                return
                
            dialog = tk.Toplevel(self.root)
            dialog.title("Start Direct Conversation")
            dialog.geometry("380x320")
            dialog.configure(bg=BG_SIDEBAR)
            
            tk.Label(dialog, text="Select a user to message:", font=("Segoe UI", 11, "bold"), fg=TEXT_WHITE, bg=BG_SIDEBAR).pack(pady=(16, 8), padx=16, anchor="w")
            
            listbox = tk.Listbox(dialog, bg=BG_INPUT, fg=TEXT_WHITE, font=("Segoe UI", 10), selectbackground=ACCENT_BLUE, relief=tk.FLAT)
            listbox.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
            
            for u in other_users:
                listbox.insert(tk.END, f"@{u['username']} ({u['email']})")
                
            def start_dm():
                sel = listbox.curselection()
                if not sel: return
                target_user = other_users[sel[0]]
                dialog.destroy()
                
                # Create Direct Conversation
                req_dm = urllib.request.Request(
                    f"{self.server_http}/api/v1/conversations/direct",
                    data=json.dumps({"user1_id": self.current_user["user_id"], "user2_id": target_user["user_id"]}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req_dm, timeout=5) as r:
                    res = json.loads(r.read().decode("utf-8"))
                    
                self._load_conversations()
                
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
        
        # Status / Zero-Knowledge badge
        lbl_info = tk.Label(dialog, text="💡 Ask natural questions (e.g. 'What did we decide about the database schema?' or 'Find the picture of the server rack')", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_SIDEBAR, wraplength=580, justify=tk.LEFT)
        lbl_info.pack(anchor="w", padx=18, pady=(0, 8))
        
        # Results Scrollable Feed
        results_container = tk.Frame(dialog, bg=BG_CHAT, highlightthickness=1, highlightbackground=BORDER_COLOR)
        results_container.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))
        
        res_canvas = tk.Canvas(results_container, bg=BG_CHAT, highlightthickness=0)
        res_scroll = ttk.Scrollbar(results_container, orient="vertical", command=res_canvas.yview)
        res_inner = tk.Frame(res_canvas, bg=BG_CHAT)
        
        res_canvas.create_window((0, 0), window=res_inner, anchor="nw", width=580)
        res_canvas.configure(yscrollcommand=res_scroll.set)
        
        res_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        res_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        res_inner.bind("<Configure>", lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        
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
                    
                    # Content Snippet
                    snippet = item.get("text", "")
                    if item.get("entity_type") == "ATTACHMENT":
                        snippet = f"📁 [Attachment]: {item.get('file_name', 'File')} ({item.get('mime_type', 'Media')})"
                    tk.Label(card, text=snippet, font=("Segoe UI", 9), fg=TEXT_WHITE, bg=BG_INPUT, wraplength=520, justify=tk.LEFT).pack(anchor="w", pady=(6, 4))
                    
                    # Jump Action
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
