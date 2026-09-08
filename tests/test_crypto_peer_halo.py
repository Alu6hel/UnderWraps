"""
==============================================================================
UnderWraps Cryptographic Peer Color Halo Automated Test Suite
Verifies SMT Invariants, Determinism & Uniqueness of Public Key Derived Halos

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.crypto.peer_halo import derive_peer_halo, hsl_to_hex

class TestCryptoPeerHalo(unittest.TestCase):
    def test_determinism_invariant(self):
        """Identical public key / username must ALWAYS yield identical halo outputs."""
        halo1 = derive_peer_halo("sovereign_peer_alpha")
        halo2 = derive_peer_halo("sovereign_peer_alpha")
        
        self.assertEqual(halo1["hue_primary"], halo2["hue_primary"])
        self.assertEqual(halo1["hue_secondary"], halo2["hue_secondary"])
        self.assertEqual(halo1["color1"], halo2["color1"])
        self.assertEqual(halo1["color2"], halo2["color2"])
        self.assertEqual(halo1["css_linear_gradient"], halo2["css_linear_gradient"])
        self.assertEqual(halo1["fingerprint"], halo2["fingerprint"])

    def test_uniqueness_across_distinct_peers(self):
        """Distinct peer keys must produce distinct color signatures."""
        halo_a = derive_peer_halo("alice_ed25519_pubkey_01")
        halo_b = derive_peer_halo("bob_ed25519_pubkey_02")
        halo_c = derive_peer_halo("charlie_ed25519_pubkey_03")
        
        self.assertNotEqual(halo_a["fingerprint"], halo_b["fingerprint"])
        self.assertNotEqual(halo_b["fingerprint"], halo_c["fingerprint"])
        self.assertNotEqual(halo_a["color1"], halo_b["color1"])

    def test_smt_bounds_and_contrast_invariants(self):
        """Validates all mathematical ranges defined in ALU formal specifications."""
        test_identifiers = [
            "master_architect_alu",
            "peer_vault_9921",
            "sovereign_node_kybalion",
            "ed25519_pk_74893721980312",
            "test_user_x"
        ]
        
        for ident in test_identifiers:
            halo = derive_peer_halo(ident)
            
            # 1. Hues in [0, 359]
            self.assertGreaterEqual(halo["hue_primary"], 0)
            self.assertLess(halo["hue_primary"], 360)
            self.assertGreaterEqual(halo["hue_secondary"], 0)
            self.assertLess(halo["hue_secondary"], 360)
            
            # 2. Saturation clamp [70%, 100%]
            self.assertGreaterEqual(halo["saturation"], 70)
            self.assertLessEqual(halo["saturation"], 100)
            
            # 3. Lightness clamp [45%, 65%] (ensures high contrast on both dark & light themes)
            self.assertGreaterEqual(halo["lightness"], 45)
            self.assertLessEqual(halo["lightness"], 65)
            
            # 4. Angle in [0, 359]
            self.assertGreaterEqual(halo["gradient_angle"], 0)
            self.assertLess(halo["gradient_angle"], 360)
            
            # 5. Glow radius in [8px, 16px]
            self.assertGreaterEqual(halo["glow_radius_px"], 8)
            self.assertLessEqual(halo["glow_radius_px"], 16)
            
            # 6. Valid Hex Strings
            self.assertTrue(halo["color1"].startswith("#"))
            self.assertEqual(len(halo["color1"]), 7)
            self.assertTrue(halo["color2"].startswith("#"))
            self.assertEqual(len(halo["color2"]), 7)

    def test_hsl_to_hex_converter(self):
        """Verifies color conversion accuracy."""
        # Pure Red: H=0, S=100, L=50 -> #ff0000
        self.assertEqual(hsl_to_hex(0, 100, 50), "#ff0000")
        # Pure Green: H=120, S=100, L=50 -> #00ff00
        self.assertEqual(hsl_to_hex(120, 100, 50), "#00ff00")
        # Pure Blue: H=240, S=100, L=50 -> #0000ff
        self.assertEqual(hsl_to_hex(240, 100, 50), "#0000ff")

if __name__ == "__main__":
    unittest.main()
