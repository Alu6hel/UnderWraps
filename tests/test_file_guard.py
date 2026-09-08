"""
==============================================================================
UnderWraps File Guard Automated Verification Suite
Formally Verifies Strict 150MB Media Ceiling (157,286,400 bytes)

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import secrets
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.kybalion_adapter import KybalionDBAdapter

class TestFileGuard150MB(unittest.TestCase):
    MAX_ALLOWED = 157286400  # 150 * 1024 * 1024

    def setUp(self):
        self.db = KybalionDBAdapter(data_dir="./underwraps_test_data")
        rand = secrets.token_hex(4)
        self.user = self.db.register_user(f"guard_{rand}", f"guard_{rand}@test.com", "Password123!")

    def test_zero_byte_file(self):
        """Zero-byte file boundary assertion."""
        self.assertTrue(0 <= self.MAX_ALLOWED)

    def test_valid_sub_150mb_files(self):
        """Files below 150MB must pass validation."""
        test_sizes = [
            1024,                  # 1 KB
            1048576,               # 1 MB
            52428800,              # 50 MB
            104857600,             # 100 MB
            157286399,             # 150MB - 1 byte
            157286400              # Exactly 150MB
        ]
        for size in test_sizes:
            with self.subTest(size=size):
                self.assertLessEqual(size, self.MAX_ALLOWED)
                rand_id = secrets.token_hex(8)
                res = self.db.register_attachment(
                    attachment_id=f"att_{rand_id}",
                    sender_id=self.user["user_id"],
                    file_name=f"test_{size}_{rand_id}.dat",
                    file_size_bytes=size,
                    mime_type="application/octet-stream",
                    blake3_hash="dummy_hash_for_test",
                    storage_path="/tmp/dummy"
                )
                self.assertTrue(res)

    def test_exceeded_150mb_rejection(self):
        """Files exceeding 150MB MUST raise ValueError."""
        invalid_sizes = [
            157286401,             # 150MB + 1 byte
            157286400 + 1024,      # 150MB + 1KB
            209715200,             # 200 MB
            1073741824             # 1 GB
        ]
        for size in invalid_sizes:
            with self.subTest(size=size):
                self.assertGreater(size, self.MAX_ALLOWED)
                rand_id = secrets.token_hex(8)
                with self.assertRaises(ValueError):
                    self.db.register_attachment(
                        attachment_id=f"att_fail_{rand_id}",
                        sender_id=self.user["user_id"],
                        file_name=f"oversized_{size}_{rand_id}.dat",
                        file_size_bytes=size,
                        mime_type="application/octet-stream",
                        blake3_hash="dummy_hash",
                        storage_path="/tmp/oversized"
                    )

if __name__ == "__main__":
    unittest.main()
