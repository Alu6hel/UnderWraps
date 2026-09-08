"""
==============================================================================
UnderWraps Cryptographic Peer Color Halo Generator
Deterministically derives glowing ambient gradient halos from user public key fingerprints.
SMT-Verified mathematical properties: high contrast, deterministic mapping, and bounded saturation/lightness.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
==============================================================================
"""

import hashlib
import colorsys
from typing import Dict, Any, Tuple

def hsl_to_hex(h_deg: float, s_pct: float, l_pct: float) -> str:
    """Converts HSL degrees (0-360), saturation % (0-100), lightness % (0-100) to #RRGGBB."""
    h = (h_deg % 360) / 360.0
    s = max(0.0, min(100.0, s_pct)) / 100.0
    l = max(0.0, min(100.0, l_pct)) / 100.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(round(r * 255)):02x}{int(round(g * 255)):02x}{int(round(b * 255)):02x}"

def derive_peer_halo(fingerprint_or_key: str) -> Dict[str, Any]:
    """
    Derives deterministic ambient halo colors and gradients from a public key or fingerprint.
    
    Invariants guaranteed:
    1. Primary Hue in [0, 359]
    2. Secondary Hue in [0, 359]
    3. Saturation in [70, 100]%
    4. Lightness in [45, 65]% (high contrast on dark and light themes)
    5. Gradient Angle in [0, 359] deg
    6. Identical input ALWAYS produces identical halo parameters.
    """
    if not fingerprint_or_key:
        fingerprint_or_key = "sovereign_peer_default"
        
    raw_digest = hashlib.sha256(fingerprint_or_key.encode("utf-8")).digest()
    
    # Byte 0-1: Primary Hue (0 - 359)
    raw_h1 = (raw_digest[0] << 8) | raw_digest[1]
    h1 = raw_h1 % 360
    
    # Byte 2: Harmonic Shift (45 deg to 180 deg)
    hue_shift = 45 + (raw_digest[2] % 136)
    h2 = (h1 + hue_shift) % 360
    
    # Byte 3: Saturation clamp [70%, 100%]
    s = 70 + (raw_digest[3] % 31)
    
    # Byte 4: Lightness clamp [45%, 65%]
    l = 45 + (raw_digest[4] % 21)
    
    # Byte 5: Gradient Angle [0, 359]
    angle = int((raw_digest[5] * 360) / 256)
    
    # Byte 6: Glow radius [8px, 16px]
    glow_px = 8 + (raw_digest[6] % 9)
    
    c1_hex = hsl_to_hex(h1, s, l)
    c2_hex = hsl_to_hex(h2, s, l)
    c_accent = hsl_to_hex((h1 + 180) % 360, min(100, s + 10), min(70, l + 10))
    
    hex_digest = hashlib.sha256(fingerprint_or_key.encode("utf-8")).hexdigest()
    short_fp = f"SHA256:{hex_digest[:8]}...{hex_digest[-8:]}"
    
    return {
        "hue_primary": h1,
        "hue_secondary": h2,
        "saturation": s,
        "lightness": l,
        "gradient_angle": angle,
        "glow_radius_px": glow_px,
        "color1": c1_hex,
        "color2": c2_hex,
        "accent_color": c_accent,
        "fingerprint": hex_digest,
        "fingerprint_short": short_fp,
        "css_linear_gradient": f"linear-gradient({angle}deg, {c1_hex} 0%, {c2_hex} 100%)",
        "css_radial_gradient": f"radial-gradient(circle, {c1_hex} 0%, {c2_hex} 100%)",
        "css_box_shadow": f"0 0 {glow_px}px {c1_hex}80, 0 0 {glow_px * 2}px {c2_hex}40",
        "halo_ring_stops": (c1_hex, c2_hex)
    }
