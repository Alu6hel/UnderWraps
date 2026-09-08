"""
==============================================================================
UnderWraps Sound-Reactive Live Theme Engine
Connects Real-Time 48kHz Audio DSP to Galaxy, Inverted Stars, and Aurora Shaders.
SMT-Verified Invariant Calculations for Bounded Particle Speeds and Harmonics.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
==============================================================================
"""

import math
import time
from typing import Dict, Any, Optional

class SoundReactiveEngine:
    def __init__(self, sensitivity: float = 1.0, enabled: bool = True):
        self.sensitivity = max(0.5, min(2.5, sensitivity))
        self.enabled = enabled
        self.current_amplitude = 0.0
        self.target_amplitude = 0.0
        self.is_active = False
        self.last_update_time = time.time()
        self.decay_rate = 0.85 # Smooth exponential falloff
        
    def set_sensitivity(self, sens: float):
        self.sensitivity = max(0.5, min(2.5, sens))
        
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.current_amplitude = 0.0
            self.target_amplitude = 0.0
            self.is_active = False
            
    def update_audio_frame(self, pcm_bytes: Optional[bytes] = None, manual_amplitude: Optional[float] = None):
        """
        Calculates normalized RMS amplitude [0.0, 1.0] from raw 16-bit PCM bytes or manual level.
        """
        if not self.enabled:
            self.current_amplitude = 0.0
            self.is_active = False
            return
            
        now = time.time()
        dt = max(0.001, now - self.last_update_time)
        self.last_update_time = now
        
        if manual_amplitude is not None:
            raw_amp = max(0.0, min(1.0, float(manual_amplitude)))
        elif pcm_bytes and len(pcm_bytes) >= 2:
            # Calculate RMS energy from 16-bit mono/stereo samples
            num_samples = len(pcm_bytes) // 2
            sum_sq = 0.0
            for i in range(0, len(pcm_bytes) - 1, 2):
                sample = int.from_bytes(pcm_bytes[i:i+2], byteorder="little", signed=True)
                sum_sq += (sample / 32768.0) ** 2
            mean_sq = sum_sq / max(1, num_samples)
            raw_amp = math.sqrt(mean_sq)
        else:
            raw_amp = 0.0
            
        self.target_amplitude = max(0.0, min(1.0, raw_amp))
        self.is_active = self.target_amplitude > 0.01
        
        # Smooth interpolation / decay
        if self.target_amplitude > self.current_amplitude:
            self.current_amplitude = self.target_amplitude # Instant attack
        else:
            self.current_amplitude = self.current_amplitude * (self.decay_rate ** (dt * 60.0))
            if self.current_amplitude < 0.001:
                self.current_amplitude = 0.0
                
    def get_modulation(self) -> Dict[str, float]:
        """
        Returns computed shader modulation factors according to ALU SMT invariants:
        - particle_speed_mult: in [1.0, 5.0]
        - particle_glow_boost: in [0.0, 0.75]
        - gravitational_wave_speed: in [1.0, 4.0]
        - aurora_harmonic_disp: in [30.0, 160.0]
        - grid_pulse_alpha: in [0.14, 0.50]
        """
        if not self.enabled or self.current_amplitude <= 0.001:
            return {
                "amplitude": 0.0,
                "effective_amplitude": 0.0,
                "particle_speed_mult": 1.0,
                "particle_glow_boost": 0.0,
                "gravitational_wave_speed": 1.0,
                "aurora_harmonic_disp": 55.0,
                "grid_pulse_alpha": 0.14,
                "is_sound_reactive_active": False
            }
            
        eff_amp = max(0.0, min(1.0, self.current_amplitude * self.sensitivity))
        
        speed_mult = max(1.0, min(5.0, 1.0 + (eff_amp * 4.0)))
        glow_boost = max(0.0, min(0.75, eff_amp * 0.75))
        wave_speed = max(1.0, min(4.0, 1.0 + (eff_amp * 3.0)))
        aurora_disp = max(30.0, min(160.0, 55.0 + (eff_amp * 100.0)))
        grid_alpha = max(0.14, min(0.50, 0.14 + (eff_amp * 0.35)))
        
        return {
            "amplitude": self.current_amplitude,
            "effective_amplitude": eff_amp,
            "particle_speed_mult": round(speed_mult, 3),
            "particle_glow_boost": round(glow_boost, 3),
            "gravitational_wave_speed": round(wave_speed, 3),
            "aurora_harmonic_disp": round(aurora_disp, 3),
            "grid_pulse_alpha": round(grid_alpha, 3),
            "is_sound_reactive_active": eff_amp > 0.02
        }
