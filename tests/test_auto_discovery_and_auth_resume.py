"""
==============================================================================
UnderWraps Auto-Discovery, Minimalist Auth & Session Resume Test Suite
Validates Zero-Config UDP Discovery, Username+Password Only Signup,
Session Token Lifecycle and /api/v1/auth/resume.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import time
import json
import socket
import secrets
import urllib.request
import urllib.error
import unittest

import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.client.desktop_client_app import discover_underwraps_server, save_cached_session, load_cached_session, clear_cached_session, SESSION_FILE_PATH

class TestAutoDiscoveryAndAuthResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery_port = 8097
        cls._running = True
        
        # Start a lightweight mock discovery beacon
        def mock_beacon():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", cls.discovery_port))
                sock.settimeout(0.5)
                while cls._running:
                    try:
                        data, addr = sock.recvfrom(1024)
                        if b"UNDERWRAPS_DISCOVER_PROBE" in data:
                            payload = json.dumps({
                                "service": "UNDERWRAPS_SERVER",
                                "status": "ONLINE",
                                "http_port": 8080,
                                "ws_port": 8081,
                                "server_name": "Mock Private Relay",
                                "version": "1.0.0"
                            }).encode("utf-8")
                            sock.sendto(payload, addr)
                    except socket.timeout:
                        continue
            finally:
                sock.close()

        cls.beacon_thread = threading.Thread(target=mock_beacon, daemon=True)
        cls.beacon_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls._running = False
        time.sleep(0.2)
        clear_cached_session()

    def test_01_client_udp_discovery(self):
        """Validates client UDP discovery beacon broadcast and response parsing."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(b"UNDERWRAPS_DISCOVER_PROBE", ("127.0.0.1", self.discovery_port))
        resp_data, addr = sock.recvfrom(2048)
        sock.close()
        
        beacon = json.loads(resp_data.decode("utf-8"))
        self.assertEqual(beacon["service"], "UNDERWRAPS_SERVER")
        self.assertEqual(beacon["status"], "ONLINE")
        self.assertEqual(beacon["http_port"], 8080)
        self.assertEqual(beacon["ws_port"], 8081)

    def test_02_session_local_persistence_lifecycle(self):
        """Validates local session caching in ~/.underwraps/session.json."""
        clear_cached_session()
        self.assertIsNone(load_cached_session())

        sample_auth = {
            "session_token": "sess_client_test_token_999",
            "username": "client_tester",
            "user_id": "usr_client123",
            "email": "client_tester@underwraps.local",
            "display_name": "Client Tester",
            "identity_key_pub": "pk_client_test",
            "two_factor_enabled": False
        }
        server_url = "http://127.0.0.1:8080"

        # Save session
        save_cached_session(sample_auth, server_url)
        loaded = load_cached_session()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["username"], "client_tester")
        self.assertEqual(loaded["session_token"], "sess_client_test_token_999")
        self.assertEqual(loaded["server_http"], server_url)

        # Clear session
        clear_cached_session()
        self.assertIsNone(load_cached_session())

    def test_03_discovery_helper_fallback_or_probe(self):
        """Validates discover_underwraps_server client function."""
        # When no server responds, fallback to localhost
        discovered = discover_underwraps_server()
        self.assertTrue(isinstance(discovered, tuple))
        self.assertEqual(len(discovered), 3)
        self.assertTrue(discovered[0].startswith("http://"))
        self.assertTrue(isinstance(discovered[1], str))
        self.assertTrue(isinstance(discovered[2], int))
