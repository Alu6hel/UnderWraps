"""
==============================================================================
UnderWraps Sovereign Server Launcher
Runs either the Windows 11 Fluent Dark GUI Dashboard or Headless Daemon.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import argparse
import tkinter as tk

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.server_ui.desktop_server_app import UnderWrapsServerGUI
from src.server.server_engine import UnderWrapsServer

def main():
    parser = argparse.ArgumentParser(description="UnderWraps Sovereign Server Node")
    parser.add_argument("--daemon", action="store_true", help="Run as a headless background server daemon (No GUI)")
    parser.add_argument("--http-port", type=int, default=8080, help="HTTP API Port (default: 8080)")
    parser.add_argument("--ws-port", type=int, default=8081, help="WebSocket Port (default: 8081)")
    parser.add_argument("--data-dir", type=str, default="./underwraps_data", help="Kybalion DB data path")
    args = parser.parse_args()

    if args.daemon:
        print("\n" + "="*78)
        print(" 🛡️  UNDERWRAPS HEADLESS SERVER DAEMON")
        print(f" HTTP Port: {args.http_port} | WS Port: {args.ws_port} | 150MB Guard: ACTIVE")
        print("="*78 + "\n")
        server = UnderWrapsServer(host="0.0.0.0", http_port=args.http_port, ws_port=args.ws_port, data_dir=args.data_dir)
        server.start()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
    else:
        root = tk.Tk()
        app = UnderWrapsServerGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()
