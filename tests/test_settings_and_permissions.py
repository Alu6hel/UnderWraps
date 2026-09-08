"""
==============================================================================
UnderWraps Settings & Permissions Automated Test Suite
Verifies Configuration Persistence, Permissions Schema & 2FA Toggles

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import json
import secrets
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.kybalion_adapter import KybalionDBAdapter

class TestSettingsAndPermissions(unittest.TestCase):
    def setUp(self):
        self.settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.json"))
        self.db = KybalionDBAdapter(data_dir="./underwraps_test_data")

    def test_settings_json_schema(self):
        """Validates settings.json structure and all configuration keys."""
        self.assertTrue(os.path.exists(self.settings_path))
        with open(self.settings_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            
        self.assertEqual(cfg["app_name"], "UnderWraps")
        self.assertIn("sound_reactive_themes", cfg)
        self.assertTrue(cfg["sound_reactive_themes"]["enabled"])
        self.assertEqual(cfg["sound_reactive_themes"]["sensitivity"], 1.0)
        
        self.assertIn("crypto_peer_halo", cfg)
        self.assertTrue(cfg["crypto_peer_halo"]["enabled"])
        
        self.assertIn("permissions", cfg)
        self.assertTrue(cfg["permissions"]["microphone_allowed"])
        self.assertTrue(cfg["permissions"]["notifications_allowed"])
        self.assertTrue(cfg["permissions"]["media_storage_allowed"])
        
        self.assertIn("media", cfg)
        self.assertEqual(cfg["media"]["max_file_size_mb"], 150)
        self.assertEqual(cfg["media"]["audio_sample_rate_hz"], 48000)

    def test_db_2fa_toggle_lifecycle(self):
        """Verifies database toggle and state persistence for optional Email 2FA."""
        rand = secrets.token_hex(4)
        user = self.db.register_user(f"settingstester_{rand}", f"settings_{rand}@test.org", "Pass1234!")
        user_id = user["user_id"]
        
        # Initial status is disabled
        self.assertFalse(bool(user.get("two_factor_enabled", 0)))
        
        # Toggle ON
        success_on = self.db.toggle_2fa(user_id, True)
        self.assertTrue(success_on)
        
        # Fetch directly from DB to assert persistence
        fetched = self.db.get_user_by_id(user_id)
        self.assertTrue(bool(fetched["two_factor_enabled"]))
        
        # Toggle OFF
        success_off = self.db.toggle_2fa(user_id, False)
        self.assertTrue(success_off)
        
        fetched_off = self.db.get_user_by_id(user_id)
        self.assertFalse(bool(fetched_off["two_factor_enabled"]))

if __name__ == "__main__":
    unittest.main()
