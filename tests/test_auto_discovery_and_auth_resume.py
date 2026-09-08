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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.server.server_engine import UnderWrapsServer
from src.client.desktop_client_app import discover_underwraps_server, save_cached_session, load_cached_session, clear_cached_session, SESSION_FILE_PATH

class TestAutoDiscoveryAndAuthResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http_port = 8094
        cls.ws_port = 8095
        cls.discovery_port = 8096  # Isolated port for testing
        cls.test_dir = "./underwraps_autodisc_test_data"
        cls.server = UnderWrapsServer(
            host="127.0.0.1",
            http_port=cls.http_port,
            ws_port=cls.ws_port,
            discovery_port=cls.discovery_port,
            data_dir=cls.test_dir
        )
        cls.server.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        time.sleep(0.3)
        clear_cached_session()

    def test_01_server_info_and_udp_discovery(self):
        """Validates zero-config server info endpoint and UDP broadcast beacon response."""
        # 1. HTTP Server Info
        req = urllib.request.Request(f"http://127.0.0.1:{self.http_port}/api/v1/server/info")
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["service"], "UNDERWRAPS_SERVER")
            self.assertEqual(data["http_port"], self.http_port)
            self.assertEqual(data["ws_port"], self.ws_port)

        # 2. UDP Probe to Discovery Port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.sendto(b"UNDERWRAPS_DISCOVER_PROBE", ("127.0.0.1", self.discovery_port))
        resp_data, addr = sock.recvfrom(2048)
        sock.close()
        
        beacon = json.loads(resp_data.decode("utf-8"))
        self.assertEqual(beacon["service"], "UNDERWRAPS_SERVER")
        self.assertEqual(beacon["status"], "ONLINE")
        self.assertEqual(beacon["http_port"], self.http_port)
        self.assertEqual(beacon["ws_port"], self.ws_port)

    def test_02_username_and_password_only_registration(self):
        """Validates that a user can register with ONLY Username and Password (no email required)."""
        rand = secrets.token_hex(4)
        username = f"sovereign_user_{rand}"
        password = "MasterPassword999!"

        req = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": username, "password": password}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["success"])
            self.assertEqual(data["user"]["username"], username.lower())
            self.assertTrue("session_token" in data)
            self.assertTrue(data["session_token"].startswith("sess_"))
            self.assertIn("@sovereign.local", data["user"]["email"])

    def test_03_session_resume_valid_and_invalid(self):
        """Validates /api/v1/auth/resume endpoint for instant zero-click auto login."""
        rand = secrets.token_hex(4)
        username = f"resume_user_{rand}"
        password = "ResumePass123!"

        # 1. Signup and retrieve initial session token
        req_signup = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": username, "password": password}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_signup) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            token = data["session_token"]
            user_id = data["user"]["user_id"]

        # 2. Resume session with valid token
        req_resume = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/resume",
            data=json.dumps({"session_token": token}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_resume) as resp:
            self.assertEqual(resp.status, 200)
            res_data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res_data["success"])
            self.assertEqual(res_data["user"]["username"], username.lower())
            self.assertEqual(res_data["user"]["user_id"], user_id)

        # 3. Resume session with bogus / invalid token -> Expect 401
        req_bad = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/resume",
            data=json.dumps({"session_token": "sess_invalid_nonexistent_token"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_bad)
        self.assertEqual(ctx.exception.code, 401)

    def test_04_session_local_persistence_lifecycle(self):
        """Validates local session caching in ~/.underwraps/session.json."""
        clear_cached_session()
        self.assertIsNone(load_cached_session())

        sample_auth = {
            "session_token": "sess_test_123456789",
            "username": "tester",
            "user_id": "usr_test123",
            "email": "tester@sovereign.local",
            "display_name": "Tester",
            "identity_key_pub": "pk_test",
            "two_factor_enabled": False
        }
        server_url = f"http://127.0.0.1:{self.http_port}"

        # Save session
        save_cached_session(sample_auth, server_url)
        loaded = load_cached_session()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["username"], "tester")
        self.assertEqual(loaded["session_token"], "sess_test_123456789")
        self.assertEqual(loaded["server_http"], server_url)

        # Clear session
        clear_cached_session()
        self.assertIsNone(load_cached_session())

    def test_05_check_username_endpoint(self):
        """Validates /api/v1/auth/check-username availability check."""
        rand = secrets.token_hex(4)
        existing_user = f"check_me_{rand}"

        # Register user
        req_signup = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": existing_user, "password": "SamplePassword"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_signup):
            pass

        # Check existing user
        req_check1 = urllib.request.Request(f"http://127.0.0.1:{self.http_port}/api/v1/auth/check-username?username={existing_user}")
        with urllib.request.urlopen(req_check1) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["exists"])
            self.assertEqual(data["username"], existing_user.lower())

        # Check non-existent user
        req_check2 = urllib.request.Request(f"http://127.0.0.1:{self.http_port}/api/v1/auth/check-username?username=nonexistent_{rand}")
        with urllib.request.urlopen(req_check2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(data["exists"])

if __name__ == "__main__":
    unittest.main()
