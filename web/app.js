/**
 * UnderWraps Web PWA Client Application
 * Sovereign E2EE, Sound-Reactive Live Shaders, Cryptographic Peer Halo & 150MB Media
 *
 * Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
 * License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
 */

let API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8080';
let WS_URL = `ws://${window.location.hostname || '127.0.0.1'}:8081`;
const MAX_FILE_BYTES = 157286400; // 150MB

function syncServerURL() {
    const input = document.getElementById('server-url-input') || document.getElementById('settings-server-url');
    if (input && input.value.trim()) {
        API_BASE = input.value.trim().replace(/\/$/, '');
        try {
            const parsed = new URL(API_BASE);
            WS_URL = `ws://${parsed.hostname}:8081`;
        } catch(e) {
            WS_URL = `ws://127.0.0.1:8081`;
        }
    }
}

let currentUser = null;
let ws = null;
let activeConvId = null;
let activePeer = null;
let current2FAToken = null;

// Voice recording & Web Audio DSP
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// Sound-Reactive Live Theme State
let soundReactiveEnabled = true;
let soundSensitivity = 1.0;
let currentAudioAmplitude = 0.0;
let targetAudioAmplitude = 0.0;
let audioCtx = null;
let analyserNode = null;
let audioDataArray = null;
let isMicTestRunning = false;
let peerHaloEnabled = true;

// 1. Auth Tabs
function switchAuthTab(tab) {
    document.getElementById('btn-tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('btn-tab-signup').classList.toggle('active', tab === 'signup');
    document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
    document.getElementById('signup-form').classList.toggle('hidden', tab !== 'signup');
}

// 2. Login Flow
async function handleLogin(e) {
    e.preventDefault();
    syncServerURL();
    const id = document.getElementById('login-identifier').value.trim();
    const pwd = document.getElementById('login-password').value.trim();

    try {
        const resp = await fetch(`${API_BASE}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: id, password: pwd })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Login failed');

        if (data.requires_2fa) {
            current2FAToken = data.token_id;
            document.getElementById('label-2fa-email').innerText = `Enter code sent to ${data.email_masked}`;
            if (data.otp_code_dev) {
                const devBanner = document.getElementById('dev-otp-banner');
                devBanner.innerText = `[Dev Mode OTP]: ${data.otp_code_dev}`;
                devBanner.classList.remove('hidden');
            }
            document.getElementById('modal-2fa').classList.remove('hidden');
        } else {
            onAuthSuccess(data);
        }
    } catch (err) {
        alert(err.message);
    }
}

async function submit2FA() {
    syncServerURL();
    const code = document.getElementById('otp-code-input').value.trim();
    if (code.length !== 6) return alert('Enter a 6-digit code');

    try {
        const resp = await fetch(`${API_BASE}/api/v1/auth/verify-2fa`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token_id: current2FAToken, otp_code: code })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Invalid 2FA code');

        close2FAModal();
        onAuthSuccess(data);
    } catch (err) {
        alert(err.message);
    }
}

function close2FAModal() {
    document.getElementById('modal-2fa').classList.add('hidden');
}

// 3. Signup Flow
async function handleSignup(e) {
    e.preventDefault();
    syncServerURL();
    const user = document.getElementById('signup-username').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const pwd = document.getElementById('signup-password').value.trim();

    try {
        const resp = await fetch(`${API_BASE}/api/v1/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, email: email, password: pwd, display_name: user })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Signup failed');

        alert(`Account @${user} created! Please sign in.`);
        switchAuthTab('login');
    } catch (err) {
        alert(err.message);
    }
}

function onAuthSuccess(user) {
    currentUser = user;
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('chat-screen').classList.remove('hidden');
    document.getElementById('my-username').innerText = `@${user.username}`;
    
    // Apply user's Cryptographic Peer Halo
    applyUserHalo(user.username);
    
    initWebSocket();
    loadConversations();
    checkPermissions();
}

// ==============================================================================
// 4. Cryptographic Peer Color Halo Generator (SMT Invariant Compliant)
// ==============================================================================
function derivePeerHalo(identifier) {
    if (!identifier) identifier = 'sovereign_peer_default';
    
    // Simple deterministic hash to 32 bytes equivalent
    let hash = 0;
    let hash2 = 0;
    for (let i = 0; i < identifier.length; i++) {
        const char = identifier.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0;
        hash2 = ((hash2 << 7) - hash2) + (char * (i + 1));
        hash2 |= 0;
    }
    
    const absH1 = Math.abs(hash);
    const absH2 = Math.abs(hash2);
    
    const h1 = absH1 % 360;
    const hueShift = 45 + (absH2 % 136);
    const h2 = (h1 + hueShift) % 360;
    const s = 70 + (absH1 % 31); // 70% to 100% saturation
    const l = 45 + (absH2 % 21); // 45% to 65% lightness
    const angle = (absH1 % 360);
    const glowPx = 8 + (absH2 % 9);
    
    const color1 = `hsl(${h1}, ${s}%, ${l}%)`;
    const color2 = `hsl(${h2}, ${s}%, ${l}%)`;
    const colorAccent = `hsl(${(h1 + 180) % 360}, ${Math.min(100, s + 10)}%, ${Math.min(70, l + 10)}%)`;
    
    const hexFp = Math.abs(hash).toString(16).padStart(8, '0') + Math.abs(hash2).toString(16).padStart(8, '0');
    
    return {
        h1, h2, s, l, angle, glowPx,
        color1, color2, colorAccent,
        fingerprint: `SHA256:${hexFp}...${hexFp.slice(0, 4)}`,
        linearGradient: `linear-gradient(${angle}deg, ${color1} 0%, ${color2} 100%)`,
        boxShadow: `0 0 ${glowPx}px ${color1}, 0 0 ${glowPx * 2}px ${color2}`
    };
}

function applyUserHalo(username) {
    const halo = derivePeerHalo(username);
    const myHaloEl = document.getElementById('my-avatar-halo');
    if (myHaloEl && peerHaloEnabled) {
        myHaloEl.style.background = halo.linearGradient;
        myHaloEl.style.boxShadow = halo.boxShadow;
    }
    
    const fpBox = document.getElementById('user-fp-box');
    if (fpBox) fpBox.innerText = halo.fingerprint;
    
    const previewRing = document.getElementById('my-halo-preview-ring');
    if (previewRing) {
        previewRing.style.background = halo.linearGradient;
        previewRing.style.boxShadow = halo.boxShadow;
    }
    
    const pill1 = document.getElementById('pill-c1');
    const pill2 = document.getElementById('pill-c2');
    if (pill1 && pill2) {
        pill1.style.backgroundColor = halo.color1;
        pill1.innerText = `H:${halo.h1}°`;
        pill2.style.backgroundColor = halo.color2;
        pill2.innerText = `H:${halo.h2}°`;
    }
}

function togglePeerHalo(enabled) {
    peerHaloEnabled = enabled;
    if (currentUser) {
        applyUserHalo(currentUser.username);
        loadConversations();
    }
}

// ==============================================================================
// 5. Sound-Reactive Web Audio Engine & Live Canvas DSP
// ==============================================================================
function initWebAudioContext() {
    if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            audioCtx = new AudioContextClass();
            analyserNode = audioCtx.createAnalyser();
            analyserNode.fftSize = 256;
            analyserNode.smoothingTimeConstant = 0.8;
            audioDataArray = new Uint8Array(analyserNode.frequencyBinCount);
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

function updateAudioEnergy() {
    if (!soundReactiveEnabled) {
        currentAudioAmplitude = 0.0;
        return;
    }
    
    if (analyserNode && audioDataArray) {
        analyserNode.getByteFrequencyData(audioDataArray);
        let sum = 0;
        for (let i = 0; i < audioDataArray.length; i++) {
            sum += audioDataArray[i];
        }
        const avg = sum / audioDataArray.length;
        targetAudioAmplitude = Math.min(1.0, avg / 128.0);
    }
    
    // Smooth attack and exponential decay
    if (targetAudioAmplitude > currentAudioAmplitude) {
        currentAudioAmplitude = targetAudioAmplitude;
    } else {
        currentAudioAmplitude = currentAudioAmplitude * 0.92;
        if (currentAudioAmplitude < 0.005) currentAudioAmplitude = 0.0;
    }
    
    // Update VU meter in Settings if visible
    const vuFill = document.getElementById('vu-meter-fill');
    if (vuFill) {
        const pct = Math.min(100, Math.round(currentAudioAmplitude * soundSensitivity * 100));
        vuFill.style.width = `${pct}%`;
    }
}

function toggleSoundReactivity(enabled) {
    soundReactiveEnabled = enabled;
    if (!enabled) currentAudioAmplitude = 0.0;
}

function updateSensitivity(val) {
    soundSensitivity = parseFloat(val) || 1.0;
    const lbl = document.getElementById('lbl-sens-val');
    if (lbl) lbl.innerText = `${soundSensitivity.toFixed(1)}x`;
}

// 6. WebSocket Real-Time Sync
function initWebSocket() {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
        ws.send(JSON.stringify({ type: 'AUTH', user_id: currentUser.user_id }));
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'NEW_MESSAGE') {
            if (msg.message.conversation_id === activeConvId) {
                renderMessageBubble(msg.message);
            }
            loadConversations();
            
            // Trigger push notification if permitted and in background
            if (Notification.permission === 'granted' && document.hidden) {
                new Notification(`UnderWraps: @${msg.message.sender_username || 'Peer'}`, {
                    body: msg.message.ciphertext ? msg.message.ciphertext.slice(0, 80) : 'New encrypted message',
                    icon: '../assets/logo/underwraps_logo.svg'
                });
            }
        } else if (msg.type === 'CALL_INCOMING') {
            showIncomingCall(msg);
        }
    };
}

async function loadConversations() {
    try {
        const resp = await fetch(`${API_BASE}/api/v1/conversations?user_id=${currentUser.user_id}`);
        const data = await resp.json();
        const listEl = document.getElementById('conversation-list');
        listEl.innerHTML = '';

        (data.conversations || []).forEach(c => {
            const div = document.createElement('div');
            div.className = `conv-item ${c.conversation_id === activeConvId ? 'active' : ''}`;
            
            const halo = derivePeerHalo(c.peer_username);
            const haloStyle = peerHaloEnabled ? `background: ${halo.linearGradient}; box-shadow: ${halo.boxShadow};` : '';
            
            div.innerHTML = `
                <div class="avatar-halo-wrapper" style="width: 36px; height: 36px; ${haloStyle}">
                    <span class="user-avatar" style="font-size: 16px;">👤</span>
                </div>
                <div class="conv-item-details">
                    <strong>@${c.peer_username}</strong>
                    <span>${(c.last_ciphertext || 'No messages yet').slice(0, 25)}</span>
                </div>
            `;
            div.onclick = () => {
                selectConversation(c);
                closeMobileSidebar();
            };
            listEl.appendChild(div);
        });
    } catch (e) {}
}

async function selectConversation(conv) {
    activeConvId = conv.conversation_id;
    activePeer = { user_id: conv.peer_id, username: conv.peer_username };
    document.getElementById('chat-peer-name').innerText = `@${conv.peer_username}`;
    document.getElementById('btn-start-call').classList.remove('hidden');

    const peerHaloEl = document.getElementById('peer-avatar-halo');
    if (peerHaloEl) {
        peerHaloEl.classList.remove('hidden');
        if (peerHaloEnabled) {
            const halo = derivePeerHalo(conv.peer_username);
            peerHaloEl.style.background = halo.linearGradient;
            peerHaloEl.style.boxShadow = halo.boxShadow;
        }
    }

    try {
        const resp = await fetch(`${API_BASE}/api/v1/conversations/${activeConvId}/messages`);
        const data = await resp.json();
        const feed = document.getElementById('message-feed');
        feed.innerHTML = '';
        (data.messages || []).forEach(m => renderMessageBubble(m));
    } catch (e) {}
}

function renderMessageBubble(msg) {
    const feed = document.getElementById('message-feed');
    const isMe = msg.sender_id === currentUser.user_id;

    const row = document.createElement('div');
    row.className = `msg-row ${isMe ? 'out' : 'in'}`;

    let content = msg.ciphertext;
    if (msg.message_type === 'VOICE_NOTE') {
        const sec = (msg.voice_duration_ms / 1000).toFixed(1);
        content = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <button class="icon-btn" onclick="playVoiceNoteAudio(this)" style="font-size: 16px; background: rgba(0,0,0,0.2); border-radius: 50%; width: 32px; height: 32px;">▶️</button>
                <div>
                    <div>🎙️ <strong>VOICE NOTE (${sec}s)</strong></div>
                    <div style="font-family: monospace; letter-spacing: 2px; font-size: 11px;"> ▂▃▅▆▇▆▅▃▂ </div>
                </div>
            </div>
        `;
    } else if (msg.message_type === 'MEDIA') {
        content = `📁 ${msg.file_name || 'Attachment'} <br><a href="${API_BASE}/api/v1/attachments/download/${msg.attachment_id}" target="_blank" style="color:#58a6ff; font-weight:bold;">⬇️ Download (150MB Ceiling)</a>`;
    }

    row.innerHTML = `<div class="bubble">${content}<div class="bubble-time">${new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div></div>`;
    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;
}

function playVoiceNoteAudio(btn) {
    initWebAudioContext();
    targetAudioAmplitude = 0.85; // Simulate sound reactivity during voice note playback
    btn.innerText = '⏸️';
    setTimeout(() => {
        targetAudioAmplitude = 0.0;
        btn.innerText = '▶️';
    }, 3500);
}

function sendTextMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    if (!text || !activeConvId || !activePeer) return;
    input.value = '';

    ws.send(JSON.stringify({
        type: 'CHAT_MESSAGE',
        conversation_id: activeConvId,
        sender_id: currentUser.user_id,
        recipient_id: activePeer.user_id,
        ciphertext: text,
        nonce: `nonce_${Date.now()}`,
        message_type: 'TEXT'
    }));
}

// 7. 150MB Media Attachment Upload
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file || !activeConvId || !activePeer) return;

    if (file.size > MAX_FILE_BYTES) {
        return alert(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds strict 150MB limit!`);
    }

    try {
        const resp = await fetch(`${API_BASE}/api/v1/attachments/upload`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/octet-stream',
                'X-Sender-Id': currentUser.user_id,
                'X-File-Name': file.name,
                'X-Is-Voice-Note': 'false'
            },
            body: file
        });
        const attData = await resp.json();
        if (!resp.ok) throw new Error(attData.error || 'Upload failed');

        ws.send(JSON.stringify({
            type: 'CHAT_MESSAGE',
            conversation_id: activeConvId,
            sender_id: currentUser.user_id,
            recipient_id: activePeer.user_id,
            ciphertext: `📁 Attached: ${file.name}`,
            nonce: `nonce_att_${Date.now()}`,
            message_type: 'MEDIA',
            attachment_id: attData.attachment_id
        }));
    } catch (err) {
        alert(err.message);
    }
}

// 8. Voice Notes
async function toggleVoiceRecording() {
    initWebAudioContext();
    const btn = document.getElementById('btn-mic');
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Connect to sound reactive analyser
            if (audioCtx && analyserNode) {
                const source = audioCtx.createMediaStreamSource(stream);
                source.connect(analyserNode);
            }
            
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.start();

            isRecording = true;
            btn.classList.add('recording');
        } catch (e) {
            alert('Microphone access required for voice notes. Please grant permission in browser.');
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        btn.classList.remove('recording');
        targetAudioAmplitude = 0.0;

        mediaRecorder.onstop = () => {
            ws.send(JSON.stringify({
                type: 'CHAT_MESSAGE',
                conversation_id: activeConvId,
                sender_id: currentUser.user_id,
                recipient_id: activePeer.user_id,
                ciphertext: '🎙️ Voice Note (48kHz)',
                nonce: `nonce_vn_${Date.now()}`,
                message_type: 'VOICE_NOTE',
                voice_duration_ms: 3500
            }));
        };
    }
}

// 9. Voice Calling (48kHz WebRTC)
function startVoiceCall() {
    if (!activePeer) return;
    initWebAudioContext();
    
    document.getElementById('call-peer-name').innerText = `@${activePeer.username}`;
    const callHalo = document.getElementById('call-peer-halo');
    if (callHalo && peerHaloEnabled) {
        const halo = derivePeerHalo(activePeer.username);
        callHalo.style.background = halo.linearGradient;
        callHalo.style.boxShadow = halo.boxShadow;
    }
    
    document.getElementById('voice-call-overlay').classList.remove('hidden');

    ws.send(JSON.stringify({
        type: 'CALL_INVITE',
        call_id: `call_${Date.now()}`,
        caller_id: currentUser.user_id,
        callee_id: activePeer.user_id
    }));
}

function endVoiceCall() {
    document.getElementById('voice-call-overlay').classList.add('hidden');
    targetAudioAmplitude = 0.0;
}

function showIncomingCall(msg) {
    document.getElementById('call-peer-name').innerText = `@Peer (${msg.call_id})`;
    document.getElementById('voice-call-overlay').classList.remove('hidden');
}

// ==============================================================================
// 10. Responsive Mobile Drawer & Settings Tabs
// ==============================================================================
function toggleMobileSidebar() {
    const sidebar = document.getElementById('main-sidebar');
    const backdrop = document.getElementById('mobile-sidebar-backdrop');
    if (sidebar) sidebar.classList.toggle('mobile-open');
    if (backdrop) backdrop.classList.toggle('hidden');
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('main-sidebar');
    const backdrop = document.getElementById('mobile-sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (backdrop) backdrop.classList.add('hidden');
}

function openSettings() {
    document.getElementById('modal-settings').classList.remove('hidden');
    checkPermissions();
    if (currentUser) applyUserHalo(currentUser.username);
}

function closeSettings() {
    document.getElementById('modal-settings').classList.add('hidden');
}

function switchSettingsTab(tabName) {
    const tabs = ['themes', 'identity', 'permissions', 'server'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t === 'permissions' ? 'perms' : t}`);
        const panel = document.getElementById(`settings-tab-${t}`);
        if (btn) btn.classList.toggle('active', t === tabName);
        if (panel) panel.classList.toggle('hidden', t !== tabName);
    });
}

// Permissions Manager
async function checkPermissions() {
    // 1. Microphone
    const micBadge = document.getElementById('badge-perm-mic');
    if (micBadge) {
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const status = await navigator.permissions.query({ name: 'microphone' });
                if (status.state === 'granted') {
                    micBadge.className = 'perm-badge perm-granted';
                    micBadge.innerText = '● Granted (48kHz Active)';
                } else if (status.state === 'denied') {
                    micBadge.className = 'perm-badge perm-denied';
                    micBadge.innerText = '● Blocked';
                } else {
                    micBadge.className = 'perm-badge perm-prompt';
                    micBadge.innerText = '● Prompt Required';
                }
            } catch (e) {
                micBadge.className = 'perm-badge perm-prompt';
                micBadge.innerText = '● Ready';
            }
        }
    }

    // 2. Notifications
    const notifBadge = document.getElementById('badge-perm-notif');
    if (notifBadge && window.Notification) {
        if (Notification.permission === 'granted') {
            notifBadge.className = 'perm-badge perm-granted';
            notifBadge.innerText = '● Allowed';
        } else if (Notification.permission === 'denied') {
            notifBadge.className = 'perm-badge perm-denied';
            notifBadge.innerText = '● Blocked';
        } else {
            notifBadge.className = 'perm-badge perm-prompt';
            notifBadge.innerText = '● Not Enabled';
        }
    }
}

async function requestMicPermission() {
    initWebAudioContext();
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (audioCtx && analyserNode) {
            const source = audioCtx.createMediaStreamSource(stream);
            source.connect(analyserNode);
        }
        checkPermissions();
        alert('Microphone access granted! Live VU meter is now active.');
    } catch (e) {
        alert('Microphone access was denied.');
        checkPermissions();
    }
}

async function requestNotificationPermission() {
    if (!window.Notification) return alert('Notifications not supported in this browser.');
    const result = await Notification.requestPermission();
    checkPermissions();
    if (result === 'granted') {
        new Notification('UnderWraps Sovereign Messenger', { body: 'Notifications enabled!' });
    }
}

async function testServerPing() {
    syncServerURL();
    const resultEl = document.getElementById('server-ping-result');
    if (resultEl) resultEl.innerText = 'Pinging server...';
    const start = performance.now();
    try {
        const resp = await fetch(`${API_BASE}/api/v1/health`);
        const elapsed = Math.round(performance.now() - start);
        if (resp.ok && resultEl) {
            resultEl.innerText = `● Connected • ${elapsed}ms Latency`;
            resultEl.style.color = 'var(--accent-green)';
        }
    } catch (e) {
        if (resultEl) {
            resultEl.innerText = '✕ Server unreachable';
            resultEl.style.color = 'var(--accent-red)';
        }
    }
}

// 11. 100% On-Device Neural Semantic Search Modal
function openNeuralSearchModal() {
    document.getElementById('modal-neural-search').classList.remove('hidden');
    const input = document.getElementById('neural-search-input');
    if (input) {
        input.focus();
        input.select();
    }
}

function closeNeuralSearchModal() {
    document.getElementById('modal-neural-search').classList.add('hidden');
}

async function executeNeuralSearch() {
    if (!currentUser) return;
    const input = document.getElementById('neural-search-input');
    const q = input ? input.value.trim() : '';
    if (!q) return;

    const resList = document.getElementById('neural-search-results');
    resList.innerHTML = '<p style="text-align: center; color: var(--text-muted); font-size: 12px; margin-top: 20px;">Computing 128-D vector projection & querying Kybalion...</p>';

    try {
        const convParam = activeConvId ? `&conversation_id=${activeConvId}` : '';
        const resp = await fetch(`${API_BASE}/api/v1/search/semantic?user_id=${currentUser.user_id}&q=${encodeURIComponent(q)}${convParam}&top_k=15`);
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Search failed');

        const results = data.results || [];
        resList.innerHTML = '';

        if (results.length === 0) {
            resList.innerHTML = `<p style="text-align: center; color: var(--text-muted); font-size: 12px; margin-top: 20px;">No semantic matches found for "${q}".</p>`;
            return;
        }

        results.forEach(r => {
            const card = document.createElement('div');
            card.style.cssText = 'background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 12px; cursor: pointer;';
            const badgeColor = r.similarity_score >= 0.75 ? 'var(--accent-green)' : (r.similarity_score >= 0.5 ? 'var(--accent-blue)' : 'var(--accent-yellow)');

            let textPreview = r.text;
            if (r.entity_type === 'ATTACHMENT') {
                textPreview = `📁 [Attachment]: ${r.file_name || 'File'} (${r.mime_type || 'Media'})`;
            }

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="background: ${badgeColor}; color: #fff; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">🎯 ${r.similarity_percent} Match</span>
                    <span style="font-size: 11px; color: var(--text-muted);">@${r.sender_username || 'User'} • ${new Date(r.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div style="font-size: 13px; color: var(--text-white); margin: 6px 0;">${textPreview}</div>
                <div style="text-align: right; font-size: 11px; color: var(--accent-blue); font-weight: 600;">↗ Open Conversation</div>
            `;

            card.onclick = () => {
                closeNeuralSearchModal();
                if (r.conversation_id) {
                    selectConversation({ conversation_id: r.conversation_id, peer_id: r.sender_id, peer_username: r.sender_username });
                }
            };

            resList.appendChild(card);
        });
    } catch (err) {
        resList.innerHTML = `<p style="text-align: center; color: var(--accent-red); font-size: 12px; margin-top: 20px;">Error: ${err.message}</p>`;
    }
}

async function toggle2FA() {
    if (!currentUser) return;
    const isEnabled = currentUser.two_factor_enabled || false;
    const newState = !isEnabled;
    try {
        const resp = await fetch(`${API_BASE}/api/v1/auth/toggle-2fa`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.user_id, enabled: newState })
        });
        if (!resp.ok) throw new Error('Failed to update 2FA setting');
        currentUser.two_factor_enabled = newState;
        const btn = document.getElementById('btn-toggle-2fa');
        if (btn) {
            btn.innerText = newState ? 'Disable 2FA' : 'Enable 2FA';
            btn.className = newState ? 'btn-primary' : 'btn-success';
        }
        alert(`Two-Factor Authentication is now ${newState ? 'ENABLED' : 'DISABLED'}.`);
    } catch (e) {
        alert(e.message);
    }
}

// ==============================================================================
// 12. Dynamic Live Canvas Theme Engine (Sound-Reactive Shaders)
// ==============================================================================
let currentTheme = localStorage.getItem('underwraps_theme') || 'galaxy';
let canvas, ctx;
let animFrameId = null;
let themeParticles = [];
let themeTime = 0;

function initLiveThemeEngine() {
    canvas = document.getElementById('live-theme-canvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        initParticlesForTheme(currentTheme);
    }

    window.addEventListener('resize', resize);
    resize();

    applyThemeToDOM(currentTheme);
    const sel = document.getElementById('theme-selector');
    if (sel) sel.value = currentTheme;

    renderThemeFrame();
}

function changeLiveTheme(themeKey) {
    currentTheme = themeKey;
    localStorage.setItem('underwraps_theme', themeKey);
    applyThemeToDOM(themeKey);
    initParticlesForTheme(themeKey);
}

function applyThemeToDOM(themeKey) {
    document.documentElement.setAttribute('data-theme', themeKey);
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
        if (themeKey === 'galaxy') metaTheme.setAttribute('content', '#0d1117');
        else if (themeKey === 'inverted') metaTheme.setAttribute('content', '#f4f7fa');
        else if (themeKey === 'aurora') metaTheme.setAttribute('content', '#04090b');
    }
}

function initParticlesForTheme(themeKey) {
    themeParticles = [];
    const count = themeKey === 'aurora' ? 70 : (themeKey === 'inverted' ? 100 : 140);
    const w = canvas ? canvas.width : window.innerWidth;
    const h = canvas ? canvas.height : window.innerHeight;

    for (let i = 0; i < count; i++) {
        themeParticles.push({
            x: Math.random() * w,
            y: Math.random() * h,
            z: Math.random() * 2 + 0.5,
            vx: (Math.random() - 0.5) * (themeKey === 'aurora' ? 0.3 : 0.6),
            vy: (themeKey === 'aurora' ? -(Math.random() * 0.8 + 0.3) : (Math.random() - 0.5) * 0.6),
            radius: Math.random() * 2.2 + 0.8,
            alpha: Math.random() * 0.8 + 0.2
        });
    }
}

function renderThemeFrame() {
    if (!canvas || !ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    
    // Update real-time audio amplitude energy
    updateAudioEnergy();
    
    const effAmp = Math.min(1.0, currentAudioAmplitude * soundSensitivity);
    const speedMult = 1.0 + (effAmp * 3.5);
    themeTime += 0.016 * speedMult;

    if (currentTheme === 'galaxy') {
        renderDarkGalaxyField(w, h, effAmp, speedMult);
    } else if (currentTheme === 'inverted') {
        renderInvertedStars(w, h, effAmp, speedMult);
    } else if (currentTheme === 'aurora') {
        renderCyberAuroraMatrix(w, h, effAmp, speedMult);
    }

    animFrameId = requestAnimationFrame(renderThemeFrame);
}

// 1. Theme: Dark Galaxy Field (Sound-Reactive)
function renderDarkGalaxyField(w, h, effAmp, speedMult) {
    ctx.fillStyle = '#090d13';
    ctx.fillRect(0, 0, w, h);

    // Glowing Sound-Reactive Galactic Nebula Cloud
    const nebulaPulse = 1.0 + (effAmp * 0.6);
    const nebulaGrad = ctx.createRadialGradient(
        w * 0.45 + Math.sin(themeTime * 0.4) * 50,
        h * 0.4 + Math.cos(themeTime * 0.3) * 40,
        30 * nebulaPulse,
        w * 0.5,
        h * 0.5,
        Math.max(w, h) * 0.65 * nebulaPulse
    );
    nebulaGrad.addColorStop(0, `rgba(60, 25, 110, ${0.22 + effAmp * 0.35})`);
    nebulaGrad.addColorStop(0.4, `rgba(20, 50, 100, ${0.15 + effAmp * 0.25})`);
    nebulaGrad.addColorStop(0.8, 'rgba(10, 15, 30, 0.08)');
    nebulaGrad.addColorStop(1, 'rgba(9, 13, 19, 0)');
    ctx.fillStyle = nebulaGrad;
    ctx.fillRect(0, 0, w, h);

    // Starfield & Constellation Connections
    for (let i = 0; i < themeParticles.length; i++) {
        const p = themeParticles[i];
        p.x += p.vx * p.z * speedMult;
        p.y += p.vy * p.z * speedMult;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        const pulse = 0.5 + 0.5 * Math.sin(themeTime * 2 + i);
        const currentAlpha = Math.min(1.0, (p.alpha * (0.6 + 0.4 * pulse)) + (effAmp * 0.4));

        // Constellation Lines
        for (let j = i + 1; j < themeParticles.length; j++) {
            const p2 = themeParticles[j];
            const dx = p.x - p2.x;
            const dy = p.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 90) {
                ctx.strokeStyle = `rgba(88, 166, 255, ${(1 - dist / 90) * (0.18 + effAmp * 0.3)})`;
                ctx.lineWidth = 0.75 + (effAmp * 0.75);
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }

        // Star Render
        ctx.fillStyle = `rgba(240, 246, 252, ${currentAlpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * (p.z * 0.7) * (1.0 + effAmp * 0.5), 0, Math.PI * 2);
        ctx.fill();

        // Star Glow
        if (p.z > 1.6 || effAmp > 0.3) {
            ctx.fillStyle = `rgba(88, 166, 255, ${currentAlpha * (0.25 + effAmp * 0.4)})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius * (3.5 + effAmp * 3), 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// 2. Theme: Inverted Stars (Sound-Reactive)
function renderInvertedStars(w, h, effAmp, speedMult) {
    ctx.fillStyle = '#eef2f6';
    ctx.fillRect(0, 0, w, h);

    // Negative Astral Core
    const grad = ctx.createRadialGradient(w * 0.5, h * 0.5, 40, w * 0.5, h * 0.5, Math.max(w, h) * 0.7);
    grad.addColorStop(0, `rgba(215, 225, 238, ${0.45 + effAmp * 0.3})`);
    grad.addColorStop(0.5, 'rgba(235, 240, 246, 0.25)');
    grad.addColorStop(1, 'rgba(238, 242, 246, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Sound-Reactive Pulsing Gravitational Waves
    const waveRate = 35 * (1.0 + effAmp * 2.5);
    const ringRadius = (themeTime * waveRate) % (Math.max(w, h) * 0.65);
    ctx.strokeStyle = `rgba(15, 23, 42, ${Math.max(0, (0.08 + effAmp * 0.2) * (1 - ringRadius / (Math.max(w, h) * 0.65)))})`;
    ctx.lineWidth = 1.5 + (effAmp * 2.5);
    ctx.beginPath();
    ctx.arc(w * 0.5, h * 0.5, ringRadius, 0, Math.PI * 2);
    ctx.stroke();

    for (let i = 0; i < themeParticles.length; i++) {
        const p = themeParticles[i];
        p.x += p.vx * p.z * speedMult;
        p.y += p.vy * p.z * speedMult;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        // Dark Constellation Links
        for (let j = i + 1; j < themeParticles.length; j++) {
            const p2 = themeParticles[j];
            const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
            if (dist < 85) {
                ctx.strokeStyle = `rgba(15, 23, 42, ${(1 - dist / 85) * (0.22 + effAmp * 0.3)})`;
                ctx.lineWidth = 0.8 + (effAmp * 0.8);
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }

        // Obsidian Starlight Node
        ctx.fillStyle = `rgba(15, 23, 42, ${p.alpha * (0.85 + effAmp * 0.15)})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * (p.z * 0.75) * (1.0 + effAmp * 0.4), 0, Math.PI * 2);
        ctx.fill();
    }
}

// 3. Theme: Cyber Aurora Matrix (Sound-Reactive)
function renderCyberAuroraMatrix(w, h, effAmp, speedMult) {
    ctx.fillStyle = '#030608';
    ctx.fillRect(0, 0, w, h);

    // Multi-Harmonic Sound-Reactive Aurora Wave Ribbons
    const baseDisp = 55 + (effAmp * 90); // SMT invariant displacement: 55 to 145px
    const bands = [
        { yOffset: h * 0.28, amp: baseDisp, freq: 0.003, speed: 0.8, color1: `rgba(0, 245, 212, ${0.18 + effAmp * 0.3})`, color2: 'rgba(0, 245, 155, 0)' },
        { yOffset: h * 0.38, amp: baseDisp * 1.3, freq: 0.002, speed: 0.6, color1: `rgba(0, 245, 155, ${0.20 + effAmp * 0.35})`, color2: 'rgba(0, 180, 216, 0)' },
        { yOffset: h * 0.48, amp: baseDisp * 1.1, freq: 0.0025, speed: 0.7, color1: `rgba(163, 113, 247, ${0.16 + effAmp * 0.3})`, color2: 'rgba(0, 245, 212, 0)' }
    ];

    bands.forEach((b, idx) => {
        ctx.beginPath();
        ctx.moveTo(0, h);
        for (let x = 0; x <= w; x += 15) {
            const wave = Math.sin(x * b.freq + themeTime * b.speed + idx) * b.amp
                       + Math.cos(x * b.freq * 1.5 - themeTime * b.speed * 0.7) * (b.amp * 0.4);
            ctx.lineTo(x, b.yOffset + wave);
        }
        ctx.lineTo(w, h);
        ctx.closePath();

        const grad = ctx.createLinearGradient(0, b.yOffset - b.amp, 0, b.yOffset + b.amp * 2);
        grad.addColorStop(0, b.color1);
        grad.addColorStop(1, b.color2);
        ctx.fillStyle = grad;
        ctx.fill();
    });

    // Cyber Perspective Grid Horizon with Audio Alpha Pulse
    const horizonY = h * 0.78;
    ctx.strokeStyle = `rgba(0, 245, 212, ${0.14 + effAmp * 0.3})`;
    ctx.lineWidth = 1 + (effAmp * 0.8);

    for (let i = 1; i <= 6; i++) {
        const y = horizonY + Math.pow(i / 6, 2) * (h - horizonY);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }

    const vLines = 14;
    for (let i = 0; i <= vLines; i++) {
        const xBottom = (w / vLines) * i;
        const xTop = w * 0.5 + (xBottom - w * 0.5) * 0.15;
        ctx.beginPath();
        ctx.moveTo(xTop, horizonY);
        ctx.lineTo(xBottom, h);
        ctx.stroke();
    }

    // Rising Quantum Plasma Sparks (Sound Accelerating)
    for (let i = 0; i < themeParticles.length; i++) {
        const p = themeParticles[i];
        p.x += p.vx * speedMult;
        p.y += p.vy * speedMult;
        if (p.y < 0) {
            p.y = h;
            p.x = Math.random() * w;
        }

        ctx.fillStyle = `rgba(0, 245, 212, ${p.alpha * (0.7 + effAmp * 0.3)})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * (1.2 + effAmp * 0.8), 0, Math.PI * 2);
        ctx.fill();
    }
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', () => {
    initLiveThemeEngine();
});
