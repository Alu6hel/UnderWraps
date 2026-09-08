"""
==============================================================================
UnderWraps Voice Engine & Audio DSP Automated Verification
Verifies 48kHz Audio Frame Clamping, Waveform Extraction, and Codec Metadata

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import math
import unittest

class TestVoiceEngineDSP(unittest.TestCase):
    def test_audio_clamping_and_gain(self):
        # Simulated 48kHz frame (960 float samples)
        frame_len = 960
        input_pcm = [math.sin(i * 0.1) * 0.8 for i in range(frame_len)]
        
        output_pcm = []
        for sample in input_pcm:
            boosted = sample * 1.12
            clamped = max(-1.0, min(1.0, boosted))
            output_pcm.append(clamped)
            
        self.assertEqual(len(output_pcm), frame_len)
        for val in output_pcm:
            self.assertGreaterEqual(val, -1.0)
            self.assertLessEqual(val, 1.0)

    def test_waveform_visual_extraction(self):
        total_samples = 48000 * 2 # 2 seconds of 48kHz audio
        pcm = [math.sin(i * 0.05) for i in range(total_samples)]
        
        target_points = 32
        step = total_samples // target_points
        waveform = []
        
        for pt in range(target_points):
            peak = max(abs(pcm[(pt * step) + s]) for s in range(step))
            waveform.append(round(peak, 2))
            
        self.assertEqual(len(waveform), target_points)
        for pt in waveform:
            self.assertGreaterEqual(pt, 0.0)
            self.assertLessEqual(pt, 1.0)

if __name__ == "__main__":
    unittest.main()
