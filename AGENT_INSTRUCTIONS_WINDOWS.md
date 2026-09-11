# UnderWraps Cross-PC Coordination & Debugging Directives (Windows Host Model)

**Target System**: Windows Host (192.168.50.179)  
**Peer System**: Linux Client (192.168.50.107)  
**Active Repository**: `https://github.com/Alu6hel/UnderWraps.git` (`main` branch)  
**Architectural Author**: David Anthony Jones ("Alu")  

---

## 1. Context & Architectural Overview

The Linux system has established full, live cross-PC connectivity with your Windows host server node (`http://192.168.50.179:8080` and `ws://192.168.50.179:8081`). 

Per user requirement:
1. **Primary Interface is the Android APK (`UnderWraps.apk`)**:
   - The APK is actively deployed and running on ChromeOS (`100.115.92.2:5555`) and the Linux Android subsystem (`emulator-5554`).
   - The user emphasizes that messaging and calling must be seamless through the APK when communicating with your Windows messaging app (`UnderWraps.exe`).
2. **Zero-Click Automatic Connection & Peer Discovery**:
   - Anyone opening the app automatically connects and sees all registered users on the server (via `/api/v1/users/list`) without manual intervention.
3. **Full-Screen Conversations Hub (Gmail-Style UX, Sovereign Theme)**:
   - When not in a chat, the conversations screen covers 100% of the display.
   - Features rich peer cards with Peer Halo cryptographic gradients, live online status indicators, instant search, and filter tabs (`All Chats`, `Direct`, `Online Now`).
   - Tapping any peer opens full-screen chat with a clear `← Chats` back navigation button (and native Android back button interception) returning to the inbox.
4. **48kHz High-Quality Voice Calling**:
   - WebRTC / signaling protocol alignment is required between your Windows desktop app, server, and the APK client.

---

## 2. Voice Calling Protocol Alignment (48kHz Lossless)

Please ensure that your server WebSocket dispatcher and Windows desktop client strictly match the following signaling contract:

### A. Call Initiation (`CALL_INVITE`)
When a user initiates a call, the client emits:
```json
{
  "type": "CALL_INVITE",
  "call_id": "call_<timestamp>",
  "caller_id": "<caller_user_id>",
  "caller_username": "<caller_username>",
  "callee_id": "<target_user_id>",
  "recipient_id": "<target_user_id>",
  "call_type": "VOICE_48KHZ",
  "sdp": { "type": "offer", "sdp": "..." }
}
```

### B. Inbound Invitation (`CALL_INCOMING`)
The server forwards this to the callee's active WebSocket connection:
```json
{
  "type": "CALL_INCOMING",
  "call_id": "call_<timestamp>",
  "caller_id": "<caller_user_id>",
  "caller_username": "<caller_username>",
  "sdp": { "type": "offer", "sdp": "..." }
}
```

### C. Answering the Call (`CALL_ANSWER`)
When the callee clicks **Accept (48kHz)**:
```json
{
  "type": "CALL_ANSWER",
  "call_id": "call_<timestamp>",
  "caller_id": "<caller_user_id>",
  "callee_id": "<callee_user_id>",
  "sdp": { "type": "answer", "sdp": "..." }
}
```

### D. Call Connected (`CALL_ACCEPTED`)
The server relays this back to the caller to finalize the peer connection:
```json
{
  "type": "CALL_ACCEPTED",
  "call_id": "call_<timestamp>",
  "recipient_id": "<caller_user_id>",
  "sdp": { "type": "answer", "sdp": "..." }
}
```

### E. ICE Candidate Relay (`ICE_CANDIDATE`)
```json
{
  "type": "ICE_CANDIDATE",
  "call_id": "call_<timestamp>",
  "recipient_id": "<peer_user_id>",
  "candidate": { ... }
}
```

### F. Decline & Hangup (`CALL_DECLINE`, `CALL_HANGUP`, `CALL_TERMINATED`)
When either party terminates:
- Client sends `{ "type": "CALL_HANGUP", "call_id": "..." }` or `{ "type": "CALL_DECLINE", "call_id": "..." }`
- Server broadcasts `{ "type": "CALL_TERMINATED", "call_id": "..." }` to both parties.

---

## 3. Ollama & Local Coding Agents Orchestration

The user has specified that you have local agents on the Windows machine and should bring up Ollama to utilize local models for collaborative coding tasks.

### Steps to Bring Up Ollama:
1. **Verify / Start Ollama Service**:
   ```cmd
   ollama serve
   ```
   Or launch the Ollama Windows tray service. Verify it is responding on `http://127.0.0.1:11434/api/tags`.

2. **Inspect Available Local Models**:
   ```cmd
   ollama list
   ```
   Recommended coding models:
   - `qwen2.5-coder:latest` (or `qwen2.5-coder:7b` / `14b` / `32b`)
   - `llama3.1:latest` (or `llama3.1:8b`)
   - `deepseek-coder:latest`

3. **Engage Senior & Junior Architect Agents**:
   - **Senior Architect Agent**:
     - Task: Audit the 48kHz voice pipeline, audio capture buffers, and WebSocket routing in `hermetic_server.py`. Ensure zero audio packet drops and proper handling of WebRTC SDP handshakes.
   - **Junior Architect Agent**:
     - Task: Run automated smoke tests against `http://192.168.50.179:8080/api/v1/health` and verify real-time event forwarding to connected clients.

---

## 4. Immediate Synchronization Steps for Windows Model

1. **Pull Latest Updates from GitHub**:
   ```bash
   git pull origin main
   ```
   This will synchronize:
   - `web/index.html` & `web/style.css` (Full-screen conversations hub with Gmail-style UX, peer halo styling, and back-to-chats navigation).
   - `web/app.js` (Zero-click automatic connection, LAN peer discovery, and WebRTC call alignment).
   - `android/` assets and `UnderWraps.apk` binaries.
   - `AGENT_INSTRUCTIONS_WINDOWS.md` (This document).

2. **Verify Server Health & Listeners**:
   Ensure ports 8080 (HTTP) and 8081 (WebSocket) remain open and bound to `0.0.0.0` or `192.168.50.179` so the Android APK on Linux can continue uninterrupted cross-PC communication.

3. **Acknowledge in Chat**:
   Send a confirmation message into direct chat `conv_dm_bb9d9dadda827f03` acknowledging these instructions.
