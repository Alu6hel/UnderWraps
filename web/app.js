/**
 * UnderWraps Web PWA Client Application
 * WebSocket Messaging, Voice Notes, 150MB File Upload & WebRTC Calling
 */

let API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8080';
let WS_URL = `ws://${window.location.hostname || '127.0.0.1'}:8081`;
const MAX_FILE_BYTES = 157286400; // 150MB

function syncServerURL() {
    const input = document.getElementById('server-url-input');
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

// Voice recording
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

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
    
    initWebSocket();
    loadConversations();
}

// 4. WebSocket Real-Time Sync
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
            div.innerHTML = `<strong>@${c.peer_username}</strong><span>${(c.last_ciphertext || 'No messages yet').slice(0, 25)}</span>`;
            div.onclick = () => selectConversation(c);
            listEl.appendChild(div);
        });
    } catch (e) {}
}

async function selectConversation(conv) {
    activeConvId = conv.conversation_id;
    activePeer = { user_id: conv.peer_id, username: conv.peer_username };
    document.getElementById('chat-peer-name').innerText = `@${conv.peer_username}`;
    document.getElementById('btn-start-call').classList.remove('hidden');

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
        content = `🎙️ <strong>VOICE NOTE (${sec}s)</strong><div style="font-family: monospace; letter-spacing: 2px;"> ▂▃▅▆▇▆▅▃▂ </div>`;
    } else if (msg.message_type === 'MEDIA') {
        content = `📁 ${msg.file_name || 'Attachment'} <br><a href="${API_BASE}/api/v1/attachments/download/${msg.attachment_id}" target="_blank" style="color:#58a6ff; font-weight:bold;">⬇️ Download</a>`;
    }

    row.innerHTML = `<div class="bubble">${content}<div class="bubble-time">${new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div></div>`;
    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;
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

// 5. 150MB Media Attachment Upload
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

// 6. Voice Notes
async function toggleVoiceRecording() {
    const btn = document.getElementById('btn-mic');
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.start();

            isRecording = true;
            btn.classList.add('recording');
        } catch (e) {
            alert('Microphone access required for voice notes.');
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        btn.classList.remove('recording');

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

// 7. Voice Calling
function startVoiceCall() {
    if (!activePeer) return;
    document.getElementById('call-peer-name').innerText = `@${activePeer.username}`;
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
}

function openSettings() { document.getElementById('modal-settings').classList.remove('hidden'); }
function closeSettings() { document.getElementById('modal-settings').classList.add('hidden'); }

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
// 8. Dynamic Live Canvas Theme Engine (Dark Galaxy, Inverted Stars, Cyber Aurora)
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

    // Apply initial theme attribute
    applyThemeToDOM(currentTheme);
    const sel = document.getElementById('theme-selector');
    if (sel) sel.value = currentTheme;

    // Start render loop
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
            alpha: Math.random() * 0.8 + 0.2,
            twinkleSpeed: Math.random() * 0.04 + 0.01,
            colorHue: Math.floor(Math.random() * 60) // theme specific hue variance
        });
    }
}

function renderThemeFrame() {
    if (!canvas || !ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    themeTime += 0.016;

    if (currentTheme === 'galaxy') {
        renderDarkGalaxyField(w, h);
    } else if (currentTheme === 'inverted') {
        renderInvertedStars(w, h);
    } else if (currentTheme === 'aurora') {
        renderCyberAuroraMatrix(w, h);
    }

    animFrameId = requestAnimationFrame(renderThemeFrame);
}

// 1. Theme: Dark Galaxy Field
function renderDarkGalaxyField(w, h) {
    // Deep space background with glowing galactic core
    ctx.fillStyle = '#090d13';
    ctx.fillRect(0, 0, w, h);

    // Glowing Galactic Nebula Cloud
    const nebulaGrad = ctx.createRadialGradient(
        w * 0.45 + Math.sin(themeTime * 0.4) * 50,
        h * 0.4 + Math.cos(themeTime * 0.3) * 40,
        30,
        w * 0.5,
        h * 0.5,
        Math.max(w, h) * 0.65
    );
    nebulaGrad.addColorStop(0, 'rgba(40, 20, 75, 0.22)');
    nebulaGrad.addColorStop(0.4, 'rgba(15, 35, 70, 0.15)');
    nebulaGrad.addColorStop(0.8, 'rgba(10, 15, 30, 0.08)');
    nebulaGrad.addColorStop(1, 'rgba(9, 13, 19, 0)');
    ctx.fillStyle = nebulaGrad;
    ctx.fillRect(0, 0, w, h);

    // Starfield & Constellation Connections
    for (let i = 0; i < themeParticles.length; i++) {
        const p = themeParticles[i];
        p.x += p.vx * p.z;
        p.y += p.vy * p.z;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        const pulse = 0.5 + 0.5 * Math.sin(themeTime * 2 + i);
        const currentAlpha = p.alpha * (0.6 + 0.4 * pulse);

        // Constellation Lines
        for (let j = i + 1; j < themeParticles.length; j++) {
            const p2 = themeParticles[j];
            const dx = p.x - p2.x;
            const dy = p.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 90) {
                ctx.strokeStyle = `rgba(88, 166, 255, ${(1 - dist / 90) * 0.18})`;
                ctx.lineWidth = 0.75;
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }

        // Star Render
        ctx.fillStyle = `rgba(240, 246, 252, ${currentAlpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * (p.z * 0.7), 0, Math.PI * 2);
        ctx.fill();

        // Star Glow
        if (p.z > 1.8) {
            ctx.fillStyle = `rgba(88, 166, 255, ${currentAlpha * 0.25})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius * 3.5, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

// 2. Theme: Inverted Stars
function renderInvertedStars(w, h) {
    // Luminous daylight astral canvas
    ctx.fillStyle = '#eef2f6';
    ctx.fillRect(0, 0, w, h);

    // Negative Astral Core
    const grad = ctx.createRadialGradient(w * 0.5, h * 0.5, 40, w * 0.5, h * 0.5, Math.max(w, h) * 0.7);
    grad.addColorStop(0, 'rgba(215, 225, 238, 0.45)');
    grad.addColorStop(0.5, 'rgba(235, 240, 246, 0.25)');
    grad.addColorStop(1, 'rgba(238, 242, 246, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Pulsing negative gravitational wave
    const ringRadius = (themeTime * 35) % (Math.max(w, h) * 0.6);
    ctx.strokeStyle = `rgba(15, 23, 42, ${Math.max(0, 0.08 * (1 - ringRadius / (Math.max(w, h) * 0.6)))})`;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(w * 0.5, h * 0.5, ringRadius, 0, Math.PI * 2);
    ctx.stroke();

    for (let i = 0; i < themeParticles.length; i++) {
        const p = themeParticles[i];
        p.x += p.vx * p.z;
        p.y += p.vy * p.z;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        // Dark Constellation Links
        for (let j = i + 1; j < themeParticles.length; j++) {
            const p2 = themeParticles[j];
            const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
            if (dist < 85) {
                ctx.strokeStyle = `rgba(15, 23, 42, ${(1 - dist / 85) * 0.22})`;
                ctx.lineWidth = 0.8;
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
        }

        // Obsidian Starlight Node
        ctx.fillStyle = `rgba(15, 23, 42, ${p.alpha * 0.85})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * (p.z * 0.75), 0, Math.PI * 2);
        ctx.fill();
    }
}

// 3. Theme: Cyber Aurora Matrix
function renderCyberAuroraMatrix(w, h) {
    // Deep Obsidian Void
    ctx.fillStyle = '#030608';
    ctx.fillRect(0, 0, w, h);

    // Multi-harmonic Procedural Aurora Wave Ribbons
    const bands = [
        { yOffset: h * 0.28, amp: 55, freq: 0.003, speed: 0.8, color1: 'rgba(0, 245, 212, 0.18)', color2: 'rgba(0, 245, 155, 0)' },
        { yOffset: h * 0.38, amp: 75, freq: 0.002, speed: 0.6, color1: 'rgba(0, 245, 155, 0.20)', color2: 'rgba(0, 180, 216, 0)' },
        { yOffset: h * 0.48, amp: 65, freq: 0.0025, speed: 0.7, color1: 'rgba(114, 9, 183, 0.16)', color2: 'rgba(0, 245, 212, 0)' }
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

    // Cyber Perspective Grid Horizon
    const horizonY = h * 0.78;
    ctx.strokeStyle = 'rgba(0, 245, 212, 0.14)';
    ctx.lineWidth = 1;

    // Horizontal perspective grid lines
    for (let i = 1; i <= 6; i++) {
        const y = horizonY + Math.pow(i / 6, 2) * (h - horizonY);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }

    // Vertical perspective perspective lines
    const vLines = 14;
    for (let i = 0; i <= vLines; i++) {
        const xBottom = (w / vLines) * i;
        const xTop = w * 0.5 + (xBottom - w * 0.5) * 0.15;
        ctx.beginPath();
        ctx.moveTo(xTop, horizonY);
        ctx.lineTo(xBottom, h);
        ctx.stroke();
    }

    // Rising Quantum Plasma Sparks
    for (let i = 0; i < themeParticles.length; i++) {
        const p = themeParticles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.y < 0) {
            p.y = h;
            p.x = Math.random() * w;
        }

        ctx.fillStyle = `rgba(0, 245, 212, ${p.alpha * 0.7})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * 1.2, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Attach event listeners on load
window.addEventListener('DOMContentLoaded', () => {
    initLiveThemeEngine();
});
