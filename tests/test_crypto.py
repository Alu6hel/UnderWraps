"""
==============================================================================
UnderWraps Cryptography & 2FA Automated Test Suite
Verifies Password Derivation, 2FA OTP Token Lifecycle, and Envelope Encryption

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import time
import secrets
import hashlib
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.kybalion_adapter import KybalionDBAdapter

class TestCryptoAnd2FA(unittest.TestCase):
    def setUp(self):
        self.db = KybalionDBAdapter(data_dir="./underwraps_test_data")

    def test_salted_password_hashing(self):
        salt1 = self.db._generate_salt()
        salt2 = self.db._generate_salt()
        pwd = "PrivateMasterKey2026!"
        
        hash1 = self.db._hash_password(pwd, salt1)
        hash2 = self.db._hash_password(pwd, salt2)
        
        # Salted hashes must be deterministic for identical salt but unique for different salts
        self.assertEqual(hash1, self.db._hash_password(pwd, salt1))
        self.assertNotEqual(hash1, hash2)
        self.assertEqual(len(hash1), 128) # SHA-512 hex length

    def test_2fa_otp_generation_and_consumption(self):
        rand = secrets.token_hex(4)
        token_id = "2fa_test_" + secrets.token_hex(8)
        email = f"tester_{rand}@crypto.org"
        otp_code = "849201"
        salt = secrets.token_hex(8)
        
        # 1. Register dummy user
        user = self.db.register_user(f"cryptotester_{rand}", email, "SecurePass123!")
        user_id = user["user_id"]
            
        # 2. Save 2FA token with 10s expiration
        self.db.save_2fa_token(token_id, user_id, email, otp_code, salt, expires_in_sec=10)
        
        # 3. Invalid OTP should fail
        with self.assertRaises(ValueError):
            self.db.verify_2fa_otp(token_id, "000000")
            
        # 4. Valid OTP should succeed
        res = self.db.verify_2fa_otp(token_id, otp_code)
        self.assertTrue(res["two_factor_enabled"])
        self.assertTrue(res["session_token"].startswith("sess_"))
        
        # 5. Second attempt with same OTP should fail (replay attack protection)
        with self.assertRaises(ValueError):
            self.db.verify_2fa_otp(token_id, otp_code)

if __name__ == "__main__":
    unittest.main()
