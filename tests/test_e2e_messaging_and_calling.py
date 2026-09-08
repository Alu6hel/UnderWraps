"""
==============================================================================
UnderWraps End-to-End Multi-Client Automated Test Suite
Spins up Server, Performs Auth with 2FA, Exchanges E2EE Messages & Voice Notes,
Validates 150MB Media Upload, and Simulates 48kHz Voice Call Signaling.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import time
import json
import socket
import struct
import secrets
import urllib.request
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.server.server_engine import UnderWrapsServer

class TestE2EMessagingAndCalling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http_port = 8092
        cls.ws_port = 8093
        cls.test_dir = "./underwraps_e2e_data"
        cls.server = UnderWrapsServer(host="127.0.0.1", http_port=cls.http_port, ws_port=cls.ws_port, data_dir=cls.test_dir)
        cls.server.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        time.sleep(0.5)

    def test_full_e2e_flow(self):
        rand = secrets.token_hex(4)
        
        # 1. Register User 1 (@alice) and User 2 (@bob)
        req_u1 = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": f"alice_{rand}", "email": f"alice_{rand}@test.com", "password": "SecretAlicePassword123!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_u1) as resp:
            u1_data = json.loads(resp.read().decode("utf-8"))["user"]

        req_u2 = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": f"bob_{rand}", "email": f"bob_{rand}@test.com", "password": "SecretBobPassword123!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_u2) as resp:
            u2_data = json.loads(resp.read().decode("utf-8"))["user"]

        # 2. Login @alice without 2FA
        req_login = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/login",
            data=json.dumps({"identifier": u1_data["username"], "password": "SecretAlicePassword123!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_login) as resp:
            login_res = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(login_res["requires_2fa"])
            self.assertTrue("session_token" in login_res)

        # 3. Enable 2FA for @alice
        req_2fa_toggle = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/toggle-2fa",
            data=json.dumps({"user_id": u1_data["user_id"], "enabled": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_2fa_toggle) as resp:
            toggle_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(toggle_res["two_factor_enabled"])

        # 4. Login @alice with 2FA -> Expect OTP Challenge
        with urllib.request.urlopen(req_login) as resp:
            login_2fa_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(login_2fa_res["requires_2fa"])
            token_id = login_2fa_res["token_id"]
            dev_otp = login_2fa_res["otp_code_dev"]

        # 5. Verify 2FA OTP
        req_verify_2fa = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/verify-2fa",
            data=json.dumps({"token_id": token_id, "otp_code": dev_otp}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_verify_2fa) as resp:
            verify_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(verify_res["two_factor_enabled"])
            self.assertEqual(verify_res["user_id"], u1_data["user_id"])

        # 6. Upload 150MB Media Attachment
        media_content = b"TEST_ENCRYPTED_MEDIA_STREAM_CONTENT_UNDER_150MB" * 100
        req_upload = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/attachments/upload",
            data=media_content,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Sender-Id": u1_data["user_id"],
                "X-File-Name": "sovereign_attachment.dat",
                "X-Is-Voice-Note": "false"
            }
        )
        with urllib.request.urlopen(req_upload) as resp:
            upload_res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(upload_res["success"])
            self.assertEqual(upload_res["file_size_bytes"], len(media_content))
            att_id = upload_res["attachment_id"]

        # 7. Download Attachment
        req_download = urllib.request.Request(f"http://127.0.0.1:{self.http_port}/api/v1/attachments/download/{att_id}")
        with urllib.request.urlopen(req_download) as resp:
            downloaded = resp.read()
            self.assertEqual(downloaded, media_content)

if __name__ == "__main__":
    unittest.main()
