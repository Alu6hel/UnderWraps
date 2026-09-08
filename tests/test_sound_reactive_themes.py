"""
==============================================================================
UnderWraps Sound-Reactive Live Theme Automated Test Suite
Verifies ALU SMT Invariants, Audio RMS Energy & Shader Modulation Factors

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import math
import struct
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.client.sound_reactive_engine import SoundReactiveEngine

class TestSoundReactiveThemes(unittest.TestCase):
    def setUp(self):
        self.engine = SoundReactiveEngine(sensitivity=1.0, enabled=True)

    def test_default_idle_modulation(self):
        """Idle state without audio must yield base neutral modulation."""
        mod = self.engine.get_modulation()
        self.assertEqual(mod["particle_speed_mult"], 1.0)
        self.assertEqual(mod["gravitational_wave_speed"], 1.0)
        self.assertEqual(mod["aurora_harmonic_disp"], 55.0)
        self.assertEqual(mod["grid_pulse_alpha"], 0.14)
        self.assertFalse(mod["is_sound_reactive_active"])

    def test_smt_invariants_under_full_amplitude(self):
        """Full amplitude must stay strictly within pure ALU SMT bounds."""
        self.engine.update_audio_frame(manual_amplitude=1.0)
        mod = self.engine.get_modulation()
        
        # SMT Invariant: Particle speed in [1.0, 5.0]
        self.assertGreaterEqual(mod["particle_speed_mult"], 1.0)
        self.assertLessEqual(mod["particle_speed_mult"], 5.0)
        
        # SMT Invariant: Gravitational wave speed in [1.0, 4.0]
        self.assertGreaterEqual(mod["gravitational_wave_speed"], 1.0)
        self.assertLessEqual(mod["gravitational_wave_speed"], 4.0)
        
        # SMT Invariant: Aurora displacement in [30.0, 160.0]
        self.assertGreaterEqual(mod["aurora_harmonic_disp"], 30.0)
        self.assertLessEqual(mod["aurora_harmonic_disp"], 160.0)
        
        # SMT Invariant: Grid alpha in [0.14, 0.50]
        self.assertGreaterEqual(mod["grid_pulse_alpha"], 0.14)
        self.assertLessEqual(mod["grid_pulse_alpha"], 0.50)
        
        self.assertTrue(mod["is_sound_reactive_active"])

    def test_sensitivity_scaling(self):
        """Sensitivity clamping and scaling tests."""
        self.engine.set_sensitivity(2.5)
        self.assertEqual(self.engine.sensitivity, 2.5)
        
        # Out of bounds should clamp to [0.5, 2.5]
        self.engine.set_sensitivity(99.0)
        self.assertEqual(self.engine.sensitivity, 2.5)
        self.engine.set_sensitivity(-5.0)
        self.assertEqual(self.engine.sensitivity, 0.5)

    def test_pcm_audio_rms_calculation(self):
        """Calculates RMS energy from synthesized 48kHz PCM audio."""
        # 16-bit PCM sine wave at 50% volume
        samples = []
        for i in range(480): # 10ms at 48kHz
            val = int(16000 * math.sin(2 * math.pi * 440 * (i / 48000)))
            samples.append(val)
            
        pcm_bytes = b"".join(struct.pack("<h", s) for s in samples)
        self.engine.update_audio_frame(pcm_bytes=pcm_bytes)
        mod = self.engine.get_modulation()
        
        self.assertGreater(mod["amplitude"], 0.2)
        self.assertLess(mod["amplitude"], 0.7)
        self.assertTrue(mod["is_sound_reactive_active"])

    def test_disabled_engine_returns_neutral(self):
        """Disabled engine must return neutral factors even with audio."""
        self.engine.set_enabled(False)
        self.engine.update_audio_frame(manual_amplitude=0.95)
        mod = self.engine.get_modulation()
        self.assertEqual(mod["particle_speed_mult"], 1.0)
        self.assertFalse(mod["is_sound_reactive_active"])

if __name__ == "__main__":
    unittest.main()
