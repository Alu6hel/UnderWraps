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

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.client.desktop_client_app import UnderWrapsClientGUI

def main():
    root = tk.Tk()
    app = UnderWrapsClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
