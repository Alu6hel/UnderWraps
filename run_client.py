"""
==============================================================================
UnderWraps Sovereign Client Messenger Launcher
Runs the Windows 11 Fluent Dark Private Messaging Client.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import tkinter as tk

# Handle PyInstaller onefile runtime path vs development path
if getattr(sys, "frozen", False):
    basedir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    basedir = os.path.abspath(os.path.dirname(__file__))

if basedir not in sys.path:
    sys.path.insert(0, basedir)

from src.client.desktop_client_app import UnderWrapsClientGUI

def main():
    import argparse
    import urllib.parse
    parser = argparse.ArgumentParser(description="UnderWraps Sovereign Client")
    parser.add_argument("--server", type=str, default="http://192.168.50.179:8080", help="Remote Server HTTP address (e.g. http://192.168.50.179:8080)")
    args, _ = parser.parse_known_args()

    root = tk.Tk()
    server_target = args.server or "http://192.168.50.179:8080"
    import re
    server_raw = server_target.strip()
    m = re.search(r'https?://[^\s\)\]>"\']+', server_raw)
    if m:
        server_raw = m.group(0)
    elif not server_raw.startswith(("http://", "https://")):
        server_raw = "http://" + server_raw
    parsed = urllib.parse.urlparse(server_raw)
    host = parsed.hostname or "192.168.50.179"
    port = parsed.port or 8080
    ws_port = 8081
    app = UnderWrapsClientGUI(root, server_http=f"http://{host}:{port}", server_ws_host=host, server_ws_port=ws_port)
    root.mainloop()

if __name__ == "__main__":
    main()
