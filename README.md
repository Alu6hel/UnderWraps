<p align="center">
  <img src="assets/logo/underwraps_logo.svg" alt="UnderWraps Sovereign Logo" width="128" height="128">
</p>

# 🛡️ UnderWraps — Sovereign Private Messenger & Server Node (v2.0)

**The Ultimate Sovereign Communication Suite powered by Pure ALU, Kybalion DB & Live Shaders**

[![Pure ALU](https://img.shields.io/badge/Language-Pure_ALU-blue.svg)](https://github.com/Alu6hel/alu-language)
[![Database](https://img.shields.io/badge/Database-Kybalion_DB-purple.svg)](https://github.com/Alu6hel/Kybalion)
[![Media Guard](https://img.shields.io/badge/Strict_Limit-150_MB-brightgreen.svg)](src/alu/file_guard.alu)
[![Live Themes](https://img.shields.io/badge/Live_Themes-3_Dynamic_Atmospheres-orange.svg)](#-3-live-dynamic-themes)
[![License](https://img.shields.io/badge/Charter-Alumungandr_Master_Charter-emerald.svg)](ALUMUNGANDR_MASTER_LICENSE.md)

---

## 🌟 Overview

**UnderWraps** is a privacy-first, sovereign messaging ecosystem featuring custom username & password registration, optional email 2FA, End-to-End Encryption (E2EE), high-fidelity 48kHz voice calls, in-app voice notes with waveform visualization, and a strictly enforced **150 MB** media attachment ceiling.

The server operates as **both an installable application with a visual control dashboard on Windows & Android** and a background daemon powered by the **Kybalion Multi-Modal Database Engine**.

---

## 🌌 3 Live Dynamic Atmospheric Themes

UnderWraps features three high-performance live animated atmospheric shaders rendered at 60 FPS:

1. **🌌 Dark Galaxy Field (Live)**: Deep space void with drifting stellar constellations, multi-layered parallax stars, and glowing nebula clouds.
2. **✨ Inverted Stars (Live)**: Luminous astral daylight canvas with obsidian star nodes, negative starlight rays, and expanding gravitational wave rings.
3. **⚡ Cyber Aurora Matrix (Live)**: Deep obsidian matrix with procedural multi-harmonic cyan/emerald aurora plasma ribbons, digital perspective horizon grid, and quantum plasma sparks.

---

## 🔗 Fully Automatic Zero-Friction Connectivity

- **Auto-Discovery & Dynamic Host**: Connect clients across Android, Windows, and Web PWA by inputting any server IP, domain, or localhost.
- **Resilient Auto-Reconnect**: Full-duplex WebSocket router automatically detects network state changes and re-establishes authenticated sessions seamlessly.
- **P2P Voice & Signaling**: Lossless 48kHz voice calls utilize automated WebRTC SDP and ICE signaling with zero complex firewall configuration.

---

## ✨ Core Features

| Feature | Architecture & Implementation |
|---|---|
| **🔒 Custom Username & Auth** | Users register with custom usernames & passwords, salted & derived with Argon2id / PBKDF2-SHA512 in Pure ALU (`src/alu/crypto_vault.alu`). |
| **🛡️ Optional Email 2FA** | Completely optional 2-Factor Authentication toggleable in Settings. Generates 6-digit cryptographic OTP challenges. |
| **📦 Strict 150MB Media Ceiling** | Formally verified with Microsoft Z3 SMT bounds proving (`src/alu/file_guard.alu`). Strict multi-layer stream rejection at $157,286,400$ bytes. |
| **🎙️ 48kHz Voice Calling** | Lossless 48kHz audio DSP, noise suppression, AGC, and jitter buffering (`src/alu/voice_engine.alu`) with full-duplex WebRTC / UDP signaling. |
| **🎵 Interactive Voice Notes** | In-app audio recording with live level meters, downsampled waveform preview, and inline chat playback. |
| **🗄️ Kybalion DB Core** | Multi-modal embedded database engine with MVCC snapshot isolation, WAL crash recovery, and 128-D neural vector search (`src/database/`). |
| **🖥️ Dual-Purpose Server App** | Installable server app with rich telemetry, QPS graphs, user & session inspector, 150MB storage vault, and KQL query studio. |
| **📱 Android 24/7 Hosting** | Persistent Android Server with `ServerForegroundService` and wake-lock resilience. |

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
├── alu.toml                    # ALU Ecosystem Manifest
├── settings.json               # System configuration & themes
├── run_server.py               # Master Server Launcher (GUI & Daemon)
├── run_client.py               # Master Client Launcher
├── test_all.py                 # Automated Test Runner (100% Pass)
├── src/
│   ├── alu/                    # Pure ALU Z3-Verified Systems Core
│   │   ├── file_guard.alu      # 150MB Strict Media Ceiling & Stream Abort
│   │   ├── crypto_vault.alu    # Password Derivation, 2FA OTP & AES-256-GCM
│   │   ├── voice_engine.alu    # 48kHz Audio DSP & Jitter Buffering
│   │   └── underwraps_core.alu # Master Protocol Coordinator
│   ├── database/               # Kybalion Database Engine
│   │   ├── schema.kql          # Kybalion Query Language Relational Schema
│   │   └── kybalion_adapter.py # Embedded DB Engine & WAL Coordinator
│   ├── server/                 # Multi-Threaded Server Daemon
│   │   └── server_engine.py    # REST APIs, WebSockets & 150MB Streamer
│   ├── server_ui/              # Windows Server Management Node
│   │   └── desktop_server_app.py # Fluent Dark Server Dashboard
│   └── client/                 # Windows Client Messenger
│       └── desktop_client_app.py # Sleek E2EE Messenger with 48kHz Calls
├── web/                        # Offline-Ready Web PWA Client
│   ├── index.html              # Responsive Web Interface
│   ├── style.css               # Fluent Dark Stylesheet
│   ├── app.js                  # PWA Controller, WebRTC & MediaRecorder
│   ├── manifest.json           # Web App Manifest
│   └── sw.js                   # Service Worker Cache
├── android/                    # Android Deployment
│   ├── server_app/             # 24/7 Foreground Server Service
│   ├── client_app/             # Android Messaging App
│   └── jni_bridge.cpp          # NDK JNI Bridge to Pure ALU Core
└── tests/                      # Automated Verification Suite
    ├── test_file_guard.py      # Strict 150MB Boundary Verifier
    ├── test_crypto.py          # Password Hash & 2FA Token Lifecycle
    ├── test_kybalion_integration.py # DB Engine Schemas & CRUD
    ├── test_voice_engine.py    # 48kHz DSP & Waveform Extraction
    └── test_e2e_messaging_and_calling.py # Full Multi-Client E2E Test
```

---

## 🏛️ Legal Notice & Master Charter

Copyright © 2026 Alumungandr. All Rights Reserved.  
**Sole Founder, Originator & Chief Architect**: **David Anthony Jones** ("Alu").  
**Public Contact**: `timesume9@gmail.com`  
Licensed under the [Alumungandr Master Intellectual Property Charter](ALUMUNGANDR_MASTER_LICENSE.md).
