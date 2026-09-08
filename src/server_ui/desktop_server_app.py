"""
==============================================================================
UnderWraps Server Desktop Application (Windows 11 Fluent Dark UI)
Visual Server Management Node, Live Telemetry, KQL Studio & 150MB Media Vault

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
==============================================================================
"""

import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Ensure path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.server.server_engine import UnderWrapsServer

# Color Palette (Windows 11 Fluent Dark)
BG_MAIN = "#0d1117"
BG_CARD = "#161b22"
BG_CARD_HOVER = "#21262d"
BORDER_COLOR = "#30363d"
ACCENT_BLUE = "#58a6ff"
ACCENT_GREEN = "#2ea043"
ACCENT_RED = "#da3633"
ACCENT_YELLOW = "#d29922"
TEXT_PRIMARY = "#f0f6fc"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED = "#6e7681"

class UnderWrapsServerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("UnderWraps Server Node — Sovereign Core")
        self.root.geometry("1020x720")
        self.root.minsize(880, 600)
        self.root.configure(bg=BG_MAIN)
        
        # Initialize Core Engine
        self.data_dir = os.path.abspath("./underwraps_data")
        self.server = UnderWrapsServer(host="0.0.0.0", http_port=8080, ws_port=8081, data_dir=self.data_dir)
        self.server.log_callbacks.append(self._on_server_log)
        
        self._setup_styles()
        self._build_ui()
        
        # Start Server automatically
        self._start_server()
        
        # Telemetry Polling Loop
        self._poll_telemetry()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_SECONDARY, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", BG_MAIN)], foreground=[("selected", ACCENT_BLUE)])
        
        style.configure("Treeview", background=BG_CARD, foreground=TEXT_PRIMARY, fieldbackground=BG_CARD, bordercolor=BORDER_COLOR, rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#21262d", foreground=TEXT_PRIMARY, font=("Segoe UI", 9, "bold"), bordercolor=BORDER_COLOR)
        style.map("Treeview", background=[("selected", "#388bfd")], foreground=[("selected", "#ffffff")])

    def _build_ui(self):
        # 1. Header Toolbar
        header_frame = tk.Frame(self.root, bg=BG_CARD, height=68, padx=20, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        # Logo & Title
        title_box = tk.Frame(header_frame, bg=BG_CARD)
        title_box.pack(side=tk.LEFT, fill=tk.Y)
        
        title_lbl = tk.Label(title_box, text="🛡️ UNDERWRAPS SERVER NODE", font=("Segoe UI", 14, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD)
        title_lbl.pack(anchor="w")
        
        sub_lbl = tk.Label(title_box, text="Pure ALU SMT Verified • Kybalion DB • 150MB Guard • 48kHz Voice", font=("Segoe UI", 8), fg=TEXT_SECONDARY, bg=BG_CARD)
        sub_lbl.pack(anchor="w")
        
        # Right Controls
        controls_box = tk.Frame(header_frame, bg=BG_CARD)
        controls_box.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_pill = tk.Label(controls_box, text="● STARTING", font=("Segoe UI", 9, "bold"), fg=ACCENT_YELLOW, bg="#34280f", padx=12, pady=4)
        self.status_pill.pack(side=tk.LEFT, padx=12)
        
        self.btn_toggle = tk.Button(controls_box, text="STOP SERVER", font=("Segoe UI", 9, "bold"), bg=ACCENT_RED, fg="#ffffff", activebackground="#b62324", relief=tk.FLAT, padx=14, pady=6, cursor="hand2", command=self._toggle_server)
        self.btn_toggle.pack(side=tk.LEFT)

        # 2. Main Tabbed Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)
        
        self.tab_dashboard = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_users = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_media = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_kql = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_config = tk.Frame(self.notebook, bg=BG_MAIN)
        
        self.notebook.add(self.tab_dashboard, text="📊 Dashboard & Telemetry")
        self.notebook.add(self.tab_users, text="👥 User & 2FA Accounts")
        self.notebook.add(self.tab_media, text="📦 150MB Media Vault")
        self.notebook.add(self.tab_kql, text="⚡ Kybalion KQL Studio")
        self.notebook.add(self.tab_config, text="⚙️ Configuration")
        
        self._build_dashboard_tab()
        self._build_users_tab()
        self._build_media_tab()
        self._build_kql_tab()
        self._build_config_tab()

    # --------------------------------------------------------------------------
    # Tab 1: Dashboard
    # --------------------------------------------------------------------------
    def _build_dashboard_tab(self):
        # KPI Row
        kpi_row = tk.Frame(self.tab_dashboard, bg=BG_MAIN)
        kpi_row.pack(fill=tk.X, pady=(0, 14))
        
        self.card_ws = self._create_kpi_card(kpi_row, "Active WS Clients", "0", ACCENT_BLUE)
        self.card_calls = self._create_kpi_card(kpi_row, "Active Voice Calls", "0", ACCENT_GREEN)
        self.card_msgs = self._create_kpi_card(kpi_row, "Messages Routed", "0", ACCENT_YELLOW)
        self.card_qps = self._create_kpi_card(kpi_row, "Throughput QPS", "0.0", "#a371f7")
        self.card_storage = self._create_kpi_card(kpi_row, "Storage Used", "0.0 MB", "#f0883e")
        
        # Split Bottom: Left Storage & Hermetic Stats / Right Live Event Log
        split_frame = tk.Frame(self.tab_dashboard, bg=BG_MAIN)
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel (Kybalion Engine Overview)
        left_panel = tk.Frame(split_frame, bg=BG_CARD, width=320, padx=16, pady=16, highlightthickness=1, highlightbackground=BORDER_COLOR)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        tk.Label(left_panel, text="KYBALION SMT ENGINE STATE", font=("Segoe UI", 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(0, 10))
        
        self.lbl_hermetic_epoch = tk.Label(left_panel, text="• Mentalism Epoch: 1", font=("Segoe UI", 9), fg=TEXT_SECONDARY, bg=BG_CARD)
        self.lbl_hermetic_epoch.pack(anchor="w", pady=2)
        
        self.lbl_vibration = tk.Label(left_panel, text="• Vibration Frequency: 1000.0 Hz", font=("Segoe UI", 9), fg=TEXT_SECONDARY, bg=BG_CARD)
        self.lbl_vibration.pack(anchor="w", pady=2)
        
        self.lbl_db_reads = tk.Label(left_panel, text="• SMT Read Ops: 0", font=("Segoe UI", 9), fg=TEXT_SECONDARY, bg=BG_CARD)
        self.lbl_db_reads.pack(anchor="w", pady=2)
        
        self.lbl_db_writes = tk.Label(left_panel, text="• SMT Write Ops: 0", font=("Segoe UI", 9), fg=TEXT_SECONDARY, bg=BG_CARD)
        self.lbl_db_writes.pack(anchor="w", pady=2)
        
        self.lbl_max_media = tk.Label(left_panel, text="• Max Single Media Limit: 150.0 MB", font=("Segoe UI", 9, "bold"), fg=ACCENT_GREEN, bg=BG_CARD)
        self.lbl_max_media.pack(anchor="w", pady=8)
        
        tk.Button(left_panel, text="Vacuum & Compact DB", font=("Segoe UI", 8, "bold"), bg="#21262d", fg=TEXT_PRIMARY, relief=tk.FLAT, padx=10, pady=6, cursor="hand2", command=self._vacuum_db).pack(fill=tk.X, pady=(12, 0))
        
        # Right Panel (Live Console Log)
        right_panel = tk.Frame(split_frame, bg=BG_CARD, padx=14, pady=14, highlightthickness=1, highlightbackground=BORDER_COLOR)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_panel, text="REAL-TIME SERVER EVENT LOG", font=("Segoe UI", 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(0, 6))
        
        self.log_text = scrolledtext.ScrolledText(right_panel, bg="#0b0e14", fg="#7ee787", font=("Consolas", 9), insertbackground="#ffffff", relief=tk.FLAT, highlightthickness=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _create_kpi_card(self, parent, title: str, value: str, color: str) -> tk.Label:
        card = tk.Frame(parent, bg=BG_CARD, padx=14, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        
        tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"), fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")
        val_lbl = tk.Label(card, text=value, font=("Segoe UI", 16, "bold"), fg=color, bg=BG_CARD)
        val_lbl.pack(anchor="w", pady=(2, 0))
        return val_lbl

    # --------------------------------------------------------------------------
    # Tab 2: Users & 2FA
    # --------------------------------------------------------------------------
    def _build_users_tab(self):
        toolbar = tk.Frame(self.tab_users, bg=BG_MAIN)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(toolbar, text="🔄 Refresh Users", font=("Segoe UI", 9, "bold"), bg="#21262d", fg=TEXT_PRIMARY, relief=tk.FLAT, padx=12, pady=6, cursor="hand2", command=self._refresh_users_table).pack(side=tk.LEFT)
        
        # Table
        cols = ("user_id", "username", "email", "2fa_status", "status", "last_seen")
        self.users_tree = ttk.Treeview(self.tab_users, columns=cols, show="headings")
        self.users_tree.heading("user_id", text="User ID")
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("email", text="Email")
        self.users_tree.heading("2fa_status", text="2FA Active")
        self.users_tree.heading("status", text="Account Status")
        self.users_tree.heading("last_seen", text="Last Seen")
        
        self.users_tree.column("user_id", width=160)
        self.users_tree.column("username", width=140)
        self.users_tree.column("email", width=220)
        self.users_tree.column("2fa_status", width=100)
        self.users_tree.column("status", width=100)
        self.users_tree.column("last_seen", width=160)
        
        self.users_tree.pack(fill=tk.BOTH, expand=True)

    # --------------------------------------------------------------------------
    # Tab 3: Media Vault
    # --------------------------------------------------------------------------
    def _build_media_tab(self):
        toolbar = tk.Frame(self.tab_media, bg=BG_MAIN)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(toolbar, text="🔄 Refresh Media", font=("Segoe UI", 9, "bold"), bg="#21262d", fg=TEXT_PRIMARY, relief=tk.FLAT, padx=12, pady=6, cursor="hand2", command=self._refresh_media_table).pack(side=tk.LEFT)
        
        cols = ("attachment_id", "file_name", "size_mb", "type", "blake3_hash", "created_at")
        self.media_tree = ttk.Treeview(self.tab_media, columns=cols, show="headings")
        self.media_tree.heading("attachment_id", text="Attachment ID")
        self.media_tree.heading("file_name", text="File Name")
        self.media_tree.heading("size_mb", text="Size (MB)")
        self.media_tree.heading("type", text="Category")
        self.media_tree.heading("blake3_hash", text="BLAKE3 / SHA-256")
        self.media_tree.heading("created_at", text="Stored Timestamp")
        
        self.media_tree.column("attachment_id", width=160)
        self.media_tree.column("file_name", width=200)
        self.media_tree.column("size_mb", width=90)
        self.media_tree.column("type", width=110)
        self.media_tree.column("blake3_hash", width=220)
        self.media_tree.column("created_at", width=140)
        
        self.media_tree.pack(fill=tk.BOTH, expand=True)

    # --------------------------------------------------------------------------
    # Tab 4: KQL Query Studio
    # --------------------------------------------------------------------------
    def _build_kql_tab(self):
        input_frame = tk.Frame(self.tab_kql, bg=BG_CARD, padx=12, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(input_frame, text="EXECUTE KQL / SQL QUERY", font=("Segoe UI", 9, "bold"), fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")
        
        self.txt_kql = tk.Entry(input_frame, font=("Consolas", 11), bg="#0b0e14", fg="#58a6ff", insertbackground="#ffffff", relief=tk.FLAT)
        self.txt_kql.insert(0, "SELECT * FROM users LIMIT 10")
        self.txt_kql.pack(fill=tk.X, pady=(6, 8))
        
        tk.Button(input_frame, text="⚡ Run KQL Query", font=("Segoe UI", 9, "bold"), bg=ACCENT_BLUE, fg="#ffffff", relief=tk.FLAT, padx=14, pady=6, cursor="hand2", command=self._run_kql_query).pack(side=tk.RIGHT)
        
        self.kql_results = scrolledtext.ScrolledText(self.tab_kql, bg=BG_CARD, fg=TEXT_PRIMARY, font=("Consolas", 9), relief=tk.FLAT, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.kql_results.pack(fill=tk.BOTH, expand=True)

    # --------------------------------------------------------------------------
    # Tab 5: Configuration
    # --------------------------------------------------------------------------
    def _build_config_tab(self):
        box = tk.Frame(self.tab_config, bg=BG_CARD, padx=20, pady=20, highlightthickness=1, highlightbackground=BORDER_COLOR)
        box.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(box, text="UNDERWRAPS SERVER CONFIGURATION", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(0, 14))
        
        self._add_config_row(box, "HTTP API Port:", "8080 (REST, Auth, Media Stream)")
        self._add_config_row(box, "WebSocket Port:", "8081 (Real-Time Duplex & Voice Signaling)")
        self._add_config_row(box, "Strict File Limit:", "150.0 MB (157,286,400 Bytes - Formally Verified)")
        self._add_config_row(box, "Audio DSP Sample Rate:", "48,000 Hz (Broadcast Lossless)")
        self._add_config_row(box, "Kybalion Data Dir:", self.data_dir)
        self._add_config_row(box, "Encryption at Rest:", "AES-256-GCM SMT Verified (Active)")

    def _add_config_row(self, parent, label: str, val: str):
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill=tk.X, pady=6)
        tk.Label(row, text=label, font=("Segoe UI", 9, "bold"), fg=TEXT_SECONDARY, bg=BG_CARD, width=22, anchor="w").pack(side=tk.LEFT)
        tk.Label(row, text=val, font=("Segoe UI", 9), fg=TEXT_PRIMARY, bg=BG_CARD).pack(side=tk.LEFT)

    # --------------------------------------------------------------------------
    # Actions & Handlers
    # --------------------------------------------------------------------------
    def _start_server(self):
        try:
            self.server.start()
            self.status_pill.config(text="● ONLINE :8080/:8081", fg=ACCENT_GREEN, bg="#0d2e16")
            self.btn_toggle.config(text="STOP SERVER", bg=ACCENT_RED)
        except Exception as e:
            messagebox.showerror("Server Error", str(e))

    def _stop_server(self):
        self.server.stop()
        self.status_pill.config(text="● STOPPED", fg=ACCENT_RED, bg="#3b1219")
        self.btn_toggle.config(text="START SERVER", bg=ACCENT_GREEN)

    def _toggle_server(self):
        if self.server.is_running:
            self._stop_server()
        else:
            self._start_server()

    def _on_server_log(self, text: str, level: str):
        self.root.after(0, self._append_log, text, level)

    def _append_log(self, text: str, level: str):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _poll_telemetry(self):
        if self.server.is_running:
            try:
                t = self.server.get_telemetry()
                self.card_ws.config(text=str(t["active_ws_connections"]))
                self.card_calls.config(text=str(t["active_voice_calls"]))
                self.card_msgs.config(text=str(t["total_messages_routed"]))
                self.card_qps.config(text=str(t["qps"]))
                self.card_storage.config(text=f"{t['storage']['total_mb']} MB")
                
                db_t = t["db_telemetry"]
                self.lbl_hermetic_epoch.config(text=f"• Mentalism Epoch: {db_t['hermetic_indices']['mentalism_epoch']}")
                self.lbl_vibration.config(text=f"• Vibration Frequency: {db_t['hermetic_indices']['vibration_frequency_hz']} Hz")
                self.lbl_db_reads.config(text=f"• SMT Read Ops: {db_t['total_reads']}")
                self.lbl_db_writes.config(text=f"• SMT Write Ops: {db_t['total_writes']}")
            except Exception:
                pass
                
        self.root.after(1000, self._poll_telemetry)

    def _refresh_users_table(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = self.server.db.list_all_users()
        for u in users:
            two_fa = "YES (Enabled)" if u.get("two_factor_enabled") else "NO (Disabled)"
            last_seen = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(u["last_seen_at"] / 1000)) if u.get("last_seen_at") else "Never"
            self.users_tree.insert("", tk.END, values=(u["user_id"], u["username"], u["email"], two_fa, u["status"], last_seen))

    def _refresh_media_table(self):
        for item in self.media_tree.get_children():
            self.media_tree.delete(item)
        with self.server.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attachments ORDER BY created_at DESC LIMIT 50")
            for row in cursor.fetchall():
                size_mb = round(row["file_size_bytes"] / (1024 * 1024), 2)
                cat = "🎙️ Voice Note" if row["is_voice_note"] else "📁 Media"
                t_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row["created_at"] / 1000))
                self.media_tree.insert("", tk.END, values=(row["attachment_id"], row["file_name"], size_mb, cat, row["blake3_hash"][:16] + "...", t_str))

    def _run_kql_query(self):
        query = self.txt_kql.get().strip()
        if not query:
            return
        try:
            with self.server.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                if query.upper().startswith("SELECT"):
                    rows = [dict(r) for r in cursor.fetchall()]
                    self.kql_results.delete("1.0", tk.END)
                    self.kql_results.insert(tk.END, json.dumps(rows, indent=2))
                else:
                    conn.commit()
                    self.kql_results.delete("1.0", tk.END)
                    self.kql_results.insert(tk.END, f"Query executed successfully. Rows affected: {cursor.rowcount}")
        except Exception as e:
            self.kql_results.delete("1.0", tk.END)
            self.kql_results.insert(tk.END, f"KQL Error: {str(e)}")

    def _vacuum_db(self):
        self.server.db.vacuum()
        messagebox.showinfo("Kybalion DB", "Database successfully vacuumed and compacted.")

    def _on_close(self):
        self._stop_server()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = UnderWrapsServerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
