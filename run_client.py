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
    root = tk.Tk()
    app = UnderWrapsClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
