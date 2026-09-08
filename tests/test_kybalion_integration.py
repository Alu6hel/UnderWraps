"""
==============================================================================
Kybalion Database Adapter Automated Integration Suite
Verifies Schemas, CRUD, Conversations, Voice Calls, and Hermetic Metrics

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import time
import secrets
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.kybalion_adapter import KybalionDBAdapter

class TestKybalionIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "./underwraps_test_data"
        self.db = KybalionDBAdapter(data_dir=self.test_dir)

    def test_user_lifecycle(self):
        rand = secrets.token_hex(4)
        username = f"testuser_{rand}"
        email = f"user_{rand}@kybalion.org"
        pwd = "TestPassword456!"
        
        # 1. Signup
        user = self.db.register_user(username, email, pwd, display_name="Test User")
        self.assertEqual(user["username"], username.lower())
        self.assertEqual(user["email"], email.lower())
        self.assertFalse(user["two_factor_enabled"])
        
        # 2. Login without 2FA
        auth = self.db.authenticate_user(username, pwd)
        self.assertFalse(auth["requires_2fa"])
        self.assertTrue(auth["session_token"].startswith("sess_"))
        
        # 3. Enable 2FA
        self.db.toggle_2fa(user["user_id"], True)
        
        # 4. Login with 2FA enabled -> requires OTP
        auth_2fa = self.db.authenticate_user(username, pwd)
        self.assertTrue(auth_2fa["requires_2fa"])
        self.assertTrue(auth_2fa["token_id"].startswith("2fa_"))
        
        # 5. Verify 2FA OTP
        verified = self.db.verify_2fa_otp(auth_2fa["token_id"], auth_2fa["otp_code_dev"])
        self.assertTrue(verified["two_factor_enabled"])
        self.assertEqual(verified["user_id"], user["user_id"])

    def test_conversation_and_messages(self):
        rand = secrets.token_hex(4)
        u1 = self.db.register_user(f"u1_{rand}", f"u1_{rand}@test.com", "Pass123!")
        u2 = self.db.register_user(f"u2_{rand}", f"u2_{rand}@test.com", "Pass123!")
        
        conv_id = self.db.create_direct_conversation(u1["user_id"], u2["user_id"])
        self.assertTrue(conv_id.startswith("conv_dm_"))
        
        m_id1 = f"msg_{secrets.token_hex(8)}"
        m_id2 = f"msg_{secrets.token_hex(8)}"
        
        # Save text message
        m1 = self.db.save_message(m_id1, conv_id, u1["user_id"], "Hello Bob", "nonce_1", message_type="TEXT")
        self.assertEqual(m1["message_sequence"], 1)
        
        # Save voice note
        m2 = self.db.save_message(m_id2, conv_id, u2["user_id"], "Voice Note Data", "nonce_2", message_type="VOICE_NOTE", voice_duration_ms=4200)
        self.assertEqual(m2["message_sequence"], 2)
        self.assertEqual(m2["voice_duration_ms"], 4200)
        
        # Fetch history
        msgs = self.db.get_messages(conv_id)
        self.assertEqual(len(msgs), 2)

    def test_voice_call_logging(self):
        rand = secrets.token_hex(4)
        u1 = self.db.register_user(f"caller_{rand}", f"caller_{rand}@test.com", "Pass123!")
        u2 = self.db.register_user(f"callee_{rand}", f"callee_{rand}@test.com", "Pass123!")
        
        call_id = f"call_test_{secrets.token_hex(6)}"
        started = int(time.time() * 1000)
        self.db.log_voice_call(call_id, u1["user_id"], u2["user_id"], "RINGING", started)
        
        answered = started + 2000
        ended = started + 62000
        self.db.log_voice_call(call_id, u1["user_id"], u2["user_id"], "ENDED", started, answered_at=answered, ended_at=ended, duration_seconds=60)
        
        telemetry = self.db.get_telemetry()
        self.assertGreaterEqual(telemetry["voice_call_count"], 1)

if __name__ == "__main__":
    unittest.main()
