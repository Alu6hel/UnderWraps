<p align="center">
  <img src="assets/logo/underwraps_logo.svg" alt="UnderWraps Sovereign Logo" width="128" height="128">
</p>

# 🛡️ UnderWraps — Sovereign Private Messenger & Server Node (v2.1)

**The Ultimate Sovereign Communication Suite powered by Pure ALU, Kybalion DB, Sound-Reactive Shaders & Cryptographic Halos**

[![Pure ALU](https://img.shields.io/badge/Language-Pure_ALU-blue.svg)](https://github.com/Alu6hel/alu-language)
[![Database](https://img.shields.io/badge/Database-Kybalion_DB-purple.svg)](https://github.com/Alu6hel/Kybalion)
[![Media Guard](https://img.shields.io/badge/Strict_Limit-150_MB-brightgreen.svg)](src/alu/file_guard.alu)
[![Neural Search](https://img.shields.io/badge/Neural_Search-100%25_On--Device_128--D-violet.svg)](#-100-on-device-neural-semantic-search)
[![Sound Reactive](https://img.shields.io/badge/Themes-Sound--Reactive_Shaders-orange.svg)](#-sound-reactive-live-themes)
[![Peer Halo](https://img.shields.io/badge/Identity-Cryptographic_Peer_Halo-cyan.svg)](#-cryptographic-peer-color-halo)
[![License](https://img.shields.io/badge/Charter-Alumungandr_Master_Charter-emerald.svg)](ALUMUNGANDR_MASTER_LICENSE.md)

---

## 🌟 Overview

**UnderWraps** is a privacy-first, sovereign messaging ecosystem featuring custom username & password registration, optional email 2FA, End-to-End Encryption (E2EE), high-fidelity 48kHz voice calls, in-app voice notes with waveform visualization, a strictly enforced **150 MB** media attachment ceiling, **100% On-Device Neural Semantic Search** powered by the **Kybalion 128-D Vector Engine**, **Sound-Reactive Live Shaders**, and **Cryptographic Peer Color Halos**.

The server operates as **both an installable application with a visual control dashboard on Windows & Android** and a background daemon powered by the **Kybalion Multi-Modal Database Engine**.

---

## 🎵 Sound-Reactive Live Themes

Connects the 3 Live Dynamic Themes (*Dark Galaxy Field*, *Inverted Stars*, and *Cyber Aurora Matrix*) directly to the real-time 48kHz audio DSP engine:

- **🌌 Dark Galaxy Field**: Starfield velocity accelerates with voice intensity up to $5\times$, galactic nebulae expand and pulse to bass harmonics, and constellation bonds glow.
- **✨ Inverted Stars**: Negative gravitational wave rings pulse outward at frequency peaks, star nodes vibrate, and dark constellation connections intensify.
- **⚡ Cyber Aurora Matrix**: Aurora plasma ribbon harmonics pulse vertically with wave amplitude, cyber grid lines glow and perspective-shift, and quantum plasma sparks burst upward based on sound frequency amplitude.
- **Formally Verified in ALU**: Guaranteed bounded outputs with SMT pre/post conditions (`src/alu/sound_reactive_theme.alu`).

---

## 🔮 Cryptographic Peer Color Halo

Every user has a unique cryptographic public key fingerprint. UnderWraps deterministically converts this fingerprint into a unique glowing ambient gradient halo around their profile avatar and chat header:

- **Zero-Trust Visual Identity**: Instantly recognize verified peers visually without relying on spoofable display names.
- **SMT-Verified High Contrast**: Mathematical bounds guarantee minimum saturation ($\ge 70\%$) and lightness ($45\% - 65\%$) for high contrast on both dark and light themes (`src/alu/crypto_peer_halo.alu`).
- **Full Platform Parity**: Rendered in Desktop Tkinter, Android WebView, and Web PWA via CSS linear/radial gradients.

---

## 🧠 100% On-Device Neural Semantic Search

UnderWraps features zero-knowledge natural language semantic search running entirely on-device with zero external cloud or third-party AI dependencies:

- **128-D Vector Embeddings**: Mathematical harmonic subword n-gram hash projection formally verified in Pure ALU (`src/alu/semantic_vector_engine.alu`).
- **Natural Language Discovery**: Ask natural questions like *"What did we decide about the database schema?"* or *"Find the picture of the server rack"* and instantly retrieve ranked matches with cosine confidence scores.
- **Unified Media & Message Search**: Seamlessly queries encrypted text, voice note transcripts, and 150MB media attachments.
- **Strict Cryptographic Isolation**: Vector searches only scan conversations the authenticated user is an active member of.

---

## 📱 Permissions, Responsiveness & Settings

- **Android Native Manifest**: Pre-configured with granular permissions (`RECORD_AUDIO`, `POST_NOTIFICATIONS`, `FOREGROUND_SERVICE_MICROPHONE`, `READ_MEDIA_*`).
- **Web PWA Permissions**: Dynamic runtime permission handling with browser `getUserMedia` and `Notification.requestPermission` triggers.
- **Responsive Mobile Drawer**: Sidebar seamlessly collapses into a touch-friendly slide-over navigation drawer on mobile viewports ($\le 768\mathrm{px}$).
- **Rich Settings Dashboard**: Multi-tab interface for Themes, Sound-Reactive Sensitivity, Peer Halo Toggles, Email 2FA, Hardware Permissions, and Server Health Ping.

---

## ✨ Core Features

| Feature | Architecture & Implementation |
|---|---|
| **🧠 100% On-Device Neural Search** | Natural language 128-D vector queries across messages and 150MB media with zero cloud leaks (`src/alu/semantic_vector_engine.alu` & `src/database/kybalion_adapter.py`). |
| **🎵 Sound-Reactive Shaders** | Live audio frequency modulation connecting 48kHz voice notes and calls to galaxy, starfield, and aurora shaders (`src/alu/sound_reactive_theme.alu`). |
| **🔮 Cryptographic Peer Halo** | SMT-verified deterministic ambient color halos derived from SHA-256 public key digests (`src/alu/crypto_peer_halo.alu` & `src/crypto/peer_halo.py`). |
| **🔒 Custom Username & Auth** | Users register with custom usernames & passwords, salted & derived with Argon2id / PBKDF2-SHA512 in Pure ALU (`src/alu/crypto_vault.alu`). |
| **🛡️ Optional Email 2FA** | Completely optional 2-Factor Authentication toggleable in Settings. Generates 6-digit cryptographic OTP challenges. |
| **📦 Strict 150MB Media Ceiling** | Formally verified with Microsoft Z3 SMT bounds proving (`src/alu/file_guard.alu`). Strict multi-layer stream rejection at $157,286,400$ bytes. |
| **🎙️ 48kHz Voice Calling** | Lossless 48kHz audio DSP, noise suppression, AGC, and jitter buffering (`src/alu/voice_engine.alu`) with full-duplex WebRTC / UDP signaling. |
| **🎵 Interactive Voice Notes** | In-app audio recording with live level meters, downsampled waveform preview, and inline chat playback. |
| **🗄️ Kybalion DB Core** | Multi-modal embedded database engine with MVCC snapshot isolation, WAL crash recovery, and 128-D neural vector search (`src/database/`). |
| **🖥️ Dual-Purpose Server App** | Installable server app with rich telemetry, QPS graphs, user & session inspector, 150MB storage vault, and KQL query studio. |

---

## 🚀 Quickstart

### 1. Run the Server GUI Node (Windows & Android)
```bash
# Launch Windows 11 Fluent Dark Server Management GUI
python run_server.py

# Or launch as a headless background daemon
python run_server.py --daemon --http-port 8080 --ws-port 8081
```

### 2. Run the Client Messaging App
```bash
# Launch Windows 11 Fluent Dark Messaging Client
python run_client.py
```

### 3. Run Automated Verification Test Suite
```bash
python test_all.py
```

---

## 📂 Repository Layout

```
UnderWraps/
├── alu.toml                    # ALU Ecosystem Manifest (v2.1.0)
├── settings.json               # System configuration & themes
├── CHECKSUMS.txt               # SHA-256 Master Cryptographic Hashes
├── RELEASE_MANIFEST.json       # Release Target Artifact Specifications
├── run_server.py               # Master Server Launcher (GUI & Daemon)
├── run_client.py               # Master Client Launcher
├── test_all.py                 # Automated Test Runner (100% Pass Rate)
├── src/
│   ├── alu/                    # Pure ALU Z3-Verified Systems Core
│   │   ├── sound_reactive_theme.alu # Sound-Reactive Live Shaders Engine
│   │   ├── crypto_peer_halo.alu     # Cryptographic Peer Color Halo Generator
│   │   ├── semantic_vector_engine.alu # 128-D Neural Vector Kernel
│   │   ├── file_guard.alu      # 150MB Strict Media Ceiling & Stream Abort
│   │   ├── crypto_vault.alu    # Password Derivation, 2FA OTP & AES-256-GCM
│   │   ├── voice_engine.alu    # 48kHz Audio DSP & Jitter Buffering
│   │   └── underwraps_core.alu # Master Protocol Coordinator
│   ├── crypto/                 # Cryptographic Derivation Adapters
│   │   └── peer_halo.py        # Python Peer Halo Color Stop Generator
│   ├── database/               # Kybalion Database Engine
│   │   ├── schema.kql          # Kybalion Relational & 128-D Vector Schema
│   │   └── kybalion_adapter.py # Embedded DB Engine & Vector Search
│   ├── server/                 # Multi-Threaded Server Daemon
│   │   └── server_engine.py    # REST APIs, WebSockets & 150MB Streamer
│   ├── server_ui/              # Windows Server Management Node
│   │   └── desktop_server_app.py # Fluent Dark Server Dashboard
│   └── client/                 # Windows Client Messenger
│       ├── desktop_client_app.py # E2EE Messenger with Halo Avatars & Shaders
│       └── sound_reactive_engine.py # Audio DSP Amplitude Modulation Monitor
├── web/                        # Offline-Ready Responsive Web PWA Client
│   ├── index.html              # Responsive Web Interface with Mobile Drawer
│   ├── style.css               # Fluent Dark Stylesheet & Halo CSS Variables
│   ├── app.js                  # PWA Controller, Web Audio DSP & Halos
│   ├── manifest.json           # Web App Manifest
│   └── sw.js                   # Service Worker Cache
├── android/                    # Android Deployment
│   ├── server_app/             # 24/7 Foreground Server Service
│   ├── client_app/             # Android Messaging App & Permissions Manifest
│   └── jni_bridge.cpp          # NDK JNI Bridge to Pure ALU Core
└── tests/                      # Automated Verification Suite (27 Tests)
    ├── test_sound_reactive_themes.py # Sound-Reactive Audio DSP & SMT Bounds
    ├── test_crypto_peer_halo.py     # Halo Determinism & Contrast Invariants
    ├── test_settings_and_permissions.py # Settings & Permissions Verification
    ├── test_semantic_search.py     # 128-D Vector Retrieval & Multi-Tenant Privacy
    ├── test_file_guard.py          # Strict 150MB Boundary Verifier
    ├── test_crypto.py              # Password Hash & 2FA Token Lifecycle
    ├── test_kybalion_integration.py # DB Engine Schemas & CRUD
    ├── test_voice_engine.py        # 48kHz DSP & Waveform Extraction
    └── test_e2e_messaging_and_calling.py # Full Multi-Client E2E Test
```

---

## 🏛️ Legal Notice & Master Charter

Copyright © 2026 Alumungandr. All Rights Reserved.  
**Sole Founder, Originator & Chief Architect**: **David Anthony Jones** ("Alu").  
**Public Contact**: `timesume9@gmail.com`  
Licensed under the [Alumungandr Master Intellectual Property Charter](ALUMUNGANDR_MASTER_LICENSE.md).
