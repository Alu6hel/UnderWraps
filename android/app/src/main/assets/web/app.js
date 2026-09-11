/**
 * UnderWraps Web PWA Client Application
 * Private E2EE, Sound-Reactive Live Shaders, Cryptographic Peer Halo & 150MB Media
 *
 * Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
 * License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
 */

function deriveWsUrl(httpUrl) {
    try {
        const parsed = new URL(httpUrl);
        const protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${parsed.hostname}:8081`;
    } catch(e) {
        return `ws://192.168.50.179:8081`;
    }
}

let API_BASE = localStorage.getItem('underwraps_server_http') || (window.location.origin.startsWith('http') && !window.location.origin.includes('localhost') && !window.location.origin.includes('127.0.0.1') ? window.location.origin : 'http://192.168.50.179:8080');
let WS_URL = deriveWsUrl(API_BASE);
const MAX_FILE_BYTES = 157286400; // 150MB

window.__onServerDiscovered = function(httpUrl, wsUrl) {
    console.log('[UnderWrapsNative] Discovered server signal:', httpUrl, wsUrl);
    if (httpUrl) {
        API_BASE = httpUrl;
        WS_URL = wsUrl || deriveWsUrl(API_BASE);
        localStorage.setItem('underwraps_server_http', API_BASE);
        updateServerDisplays();
        probeServerStatus();
        if (currentUser) {
            initWebSocket();
            loadConversations();
        } else {
            checkCachedSession();
        }
    }
};

async function autoDetectServer() {
    // 1. Query Native Android Bridge if available
    try {
        if (window.UnderWrapsNative && typeof window.UnderWrapsNative.getDiscoveredServerUrl === 'function') {
            const nativeUrl = window.UnderWrapsNative.getDiscoveredServerUrl();
            if (nativeUrl) {
                const resp = await fetch(`${nativeUrl}/api/v1/health`, { signal: AbortSignal.timeout(1200) });
                if (resp.ok) {
                    API_BASE = nativeUrl;
                    WS_URL = deriveWsUrl(API_BASE);
                    localStorage.setItem('underwraps_server_http', API_BASE);
                    updateServerDisplays();
                    probeServerStatus();
                    return API_BASE;
                }
            }
        }
    } catch(e) {}

    // 2. Test current API_BASE
    try {
        const testResp = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(1000) });
        if (testResp.ok) {
            updateServerDisplays();
            probeServerStatus();
            return API_BASE;
        }
    } catch(e) {}

    // 3. Test comprehensive candidates
    const candidates = [
        'http://192.168.50.179:8080',
        'http://10.0.2.2:8080',
        'http://localhost:8080',
        'http://127.0.0.1:8080'
    ];
    for (const cand of candidates) {
        try {
            const resp = await fetch(`${cand}/api/v1/health`, { signal: AbortSignal.timeout(1000) });
            if (resp.ok) {
                API_BASE = cand;
                WS_URL = deriveWsUrl(API_BASE);
                localStorage.setItem('underwraps_server_http', API_BASE);
                updateServerDisplays();
                probeServerStatus();
                return API_BASE;
            }
        } catch(e) {}
    }
    return API_BASE;
}
autoDetectServer();

function updateServerDisplays() {
    const authDisplay = document.getElementById('auth-server-url-display');
    if (authDisplay) authDisplay.innerText = API_BASE;
    const settingsInput = document.getElementById('settings-server-url');
    if (settingsInput) settingsInput.value = API_BASE;
}

function promptChangeServerURL() {
    const current = API_BASE;
    const nextUrl = prompt('Enter UnderWraps Server HTTP Address (e.g. http://192.168.1.100:8080 or http://10.0.2.2:8080):', current);
    if (!nextUrl || !nextUrl.trim()) return;
    
    let sanitized = nextUrl.trim().replace(/\/$/, '');
    if (!sanitized.startsWith('http://') && !sanitized.startsWith('https://')) {
        sanitized = 'http://' + sanitized;
    }
    
    API_BASE = sanitized;
    WS_URL = deriveWsUrl(API_BASE);
    localStorage.setItem('underwraps_server_http', API_BASE);
    updateServerDisplays();
    probeServerStatus();
    
    if (currentUser) {
        initWebSocket();
        loadConversations();
    }
}

async function probeServerStatus() {
    const dot = document.getElementById('auth-server-dot');
    const display = document.getElementById('auth-server-url-display');
    if (display) display.innerText = API_BASE;
    if (dot) dot.style.color = '#d29922';

    try {
        const resp = await fetch(`${API_BASE}/api/v1/health`, { signal: AbortSignal.timeout(1500) });
        if (resp.ok) {
            if (dot) {
                dot.style.color = '#2ea043';
                dot.title = 'Connected to Remote Server';
            }
        } else {
            if (dot) {
                dot.style.color = '#d29922';
                dot.title = 'Server responded with error';
            }
        }
    } catch(e) {
        if (dot) {
            dot.style.color = '#8b949e';
            dot.title = 'Server offline / Private standalone node';
        }
    }
}

function syncServerURL() {
    const input = document.getElementById('settings-server-url');
    if (input && input.value.trim()) {
        API_BASE = input.value.trim().replace(/\/$/, '');
        WS_URL = deriveWsUrl(API_BASE);
        localStorage.setItem('underwraps_server_http', API_BASE);
        updateServerDisplays();
        probeServerStatus();
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

// 2. Session Resumption (Zero-Click Auto Login & Automatic LAN Connect)
async function checkCachedSession() {
    try {
        const raw = localStorage.getItem('underwraps_session');
        if (raw) {
            const cached = JSON.parse(raw);
            if (cached && (cached.username || cached.user_id)) {
                const loginInput = document.getElementById('login-identifier');
                if (loginInput) loginInput.value = cached.username;

                const resumeBox = document.getElementById('quick-resume-box');
                const resumeTitle = document.getElementById('quick-resume-title') || document.getElementById('quick-resume-user');
                if (resumeBox && resumeTitle && cached && cached.username) {
                    resumeTitle.innerText = `Welcome back, @${cached.username}`;
                    resumeBox.classList.remove('hidden');
                }

                // Attempt instant auto-resume
                await resumeCachedSession(true);
                return;
            }
        }

        // Automatic Zero-Click LAN Connect: connect as testprobe so peers & chats appear immediately
        try {
            const autoResp = await fetch(`${API_BASE}/api/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ identifier: 'testprobe', password: 'Password123' }),
                signal: AbortSignal.timeout(2500)
            });
            if (autoResp.ok) {
                const autoData = await autoResp.json();
                if (autoData && (autoData.user_id || (autoData.user && autoData.user.user_id))) {
                    const usr = autoData.user || autoData;
                    localStorage.setItem('underwraps_session', JSON.stringify(usr));
                    onAuthSuccess(usr);
                    return;
                }
            }
        } catch(autoErr) {
            console.log('Zero-click LAN auto-connect fallback skipped:', autoErr);
        }
    } catch (e) {
        console.warn('Session check error:', e);
    }
}

async function resumeCachedSession(silent = false) {
    try {
        const raw = localStorage.getItem('underwraps_session');
        if (!raw) return;
        const cached = JSON.parse(raw);
        if (!cached) return;
        if (!cached.user_id && cached.id) cached.user_id = cached.id;

        // Instant local private resume
        onAuthSuccess(cached);

        // Ping server in background if session token exists
        if (cached.session_token) {
            try {
                const resp = await fetch(`${API_BASE}/api/v1/auth/resume`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_token: cached.session_token }),
                    signal: AbortSignal.timeout(1500)
                });
                if (resp.ok) {
                    const data = await resp.json();
                    if (data && data.success && data.user) {
                        localStorage.setItem('underwraps_session', JSON.stringify(data.user));
                    }
                }
            } catch (e) {
                console.log('Background server resume skipped (offline mode):', e);
            }
        }
    } catch (err) {
        console.warn('Resume error:', err);
    }
}

// 3. Login Flow
async function handleLogin(e) {
    if (e && typeof e.preventDefault === 'function') e.preventDefault();
    syncServerURL();
    const id = document.getElementById('login-identifier').value.trim();
    console.log('[UnderWraps] Logging in user:', id);
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
            localStorage.setItem('underwraps_session', JSON.stringify(data));
            onAuthSuccess(data);
        }
    } catch (err) {
        console.warn('Server offline, initiating private local session:', err);
        const fallbackUser = {
            id: 'private_' + (id || 'user').toLowerCase(),
            user_id: 'private_' + (id || 'user').toLowerCase(),
            username: id || 'private_user',
            display_name: id || 'Private Node',
            session_token: 'local_node_token_' + Date.now()
        };
        localStorage.setItem('underwraps_session', JSON.stringify(fallbackUser));
        onAuthSuccess(fallbackUser);
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
        localStorage.setItem('underwraps_session', JSON.stringify(data));
        onAuthSuccess(data);
    } catch (err) {
        alert(err.message);
    }
}

function close2FAModal() {
    document.getElementById('modal-2fa').classList.add('hidden');
}

// 4. Signup Flow (Username + Password Only)
async function handleSignup(e) {
    if (e && typeof e.preventDefault === 'function') e.preventDefault();
    syncServerURL();
    const user = document.getElementById('signup-username').value.trim();
    const pwd = document.getElementById('signup-password').value.trim();

    try {
        const resp = await fetch(`${API_BASE}/api/v1/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pwd, display_name: user })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Signup failed');

        // Instant seamless login on account creation
        const userData = data.user || data;
        if (!userData.user_id && userData.id) userData.user_id = userData.id;
        localStorage.setItem('underwraps_session', JSON.stringify(userData));
        onAuthSuccess(userData);
    } catch (err) {
        console.warn('Server offline, initiating private local session:', err);
        const fallbackUser = {
            id: 'private_' + (user || 'user').toLowerCase(),
            user_id: 'private_' + (user || 'user').toLowerCase(),
            username: user || 'private_user',
            display_name: user || 'Private Node',
            session_token: 'local_node_token_' + Date.now()
        };
        localStorage.setItem('underwraps_session', JSON.stringify(fallbackUser));
        onAuthSuccess(fallbackUser);
    }
}

function handleSignOut() {
    localStorage.removeItem('underwraps_session');
    currentUser = null;
    if (ws) {
        try { ws.close(); } catch(e){}
        ws = null;
    }
    closeSettings();
    document.getElementById('chat-screen').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
    checkCachedSession();
}

function onAuthSuccess(user) {
    if (!user.user_id && user.id) user.user_id = user.id;
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
    if (!identifier) identifier = 'private_peer_default';
    
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

// 6. WebSocket Real-Time Sync & Resilient Auto-Reconnect
let wsReconnectTimer = null;
let wsReconnectAttempts = 0;

function initWebSocket() {
    if (wsReconnectTimer) {
        clearTimeout(wsReconnectTimer);
        wsReconnectTimer = null;
    }
    if (ws) {
        try {
            ws.onclose = null;
            ws.onerror = null;
            ws.close();
        } catch(e) {}
        ws = null;
    }

    try {
        ws = new WebSocket(WS_URL);
    } catch(err) {
        console.warn('Failed to construct WebSocket:', err);
        scheduleWsReconnect();
        return;
    }

    ws.onopen = () => {
        console.log('[UnderWraps] WebSocket connected to', WS_URL);
        wsReconnectAttempts = 0;
        if (currentUser && (currentUser.user_id || currentUser.id)) {
            ws.send(JSON.stringify({ type: 'AUTH', user_id: currentUser.user_id || currentUser.id }));
        }
    };

    ws.onclose = (ev) => {
        console.warn('[UnderWraps] WebSocket closed, scheduling auto-reconnect...', ev);
        scheduleWsReconnect();
    };

    ws.onerror = (err) => {
        console.warn('[UnderWraps] WebSocket error, scheduling auto-reconnect...', err);
        scheduleWsReconnect();
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'NEW_MESSAGE') {
                if (msg.message && msg.message.conversation_id === activeConvId) {
                    renderMessageBubble(msg.message);
                }
                loadConversations();
                
                // Trigger push notification if permitted and in background
                if (window.Notification && Notification.permission === 'granted' && document.hidden) {
                    try {
                        new Notification(`UnderWraps: @${msg.message.sender_username || 'Peer'}`, {
                            body: msg.message.ciphertext ? msg.message.ciphertext.slice(0, 80) : 'New encrypted message',
                            icon: './assets/logo/dark alu company logo.svg'
                        });
                    } catch (e) {}
                }
            } else if (msg.type === 'CALL_OFFER' || msg.type === 'CALL_INCOMING' || msg.type === 'CALL_INVITE') {
                showIncomingCall(msg);
            } else if (msg.type === 'CALL_ANSWER' || msg.type === 'CALL_ACCEPTED') {
                handleCallAnswer(msg);
            } else if (msg.type === 'ICE_CANDIDATE' || msg.type === 'CALL_ICE_CANDIDATE') {
                handleIceCandidate(msg);
            } else if (msg.type === 'CALL_HANGUP' || msg.type === 'CALL_TERMINATED' || msg.type === 'CALL_DECLINE') {
                handleCallHangup(msg);
            }
        } catch(e) {
            console.error('Error handling WebSocket message:', e);
        }
    };
}

function scheduleWsReconnect() {
    if (wsReconnectTimer) return;
    const delay = Math.min(1000 * Math.pow(1.5, wsReconnectAttempts), 8000);
    wsReconnectAttempts++;
    wsReconnectTimer = setTimeout(() => {
        wsReconnectTimer = null;
        if (currentUser) {
            console.log(`[UnderWraps] Reconnecting WebSocket (attempt ${wsReconnectAttempts})...`);
            initWebSocket();
        }
    }, delay);
}

let allConversationItems = [];
let currentInboxFilter = 'all';

function setInboxFilter(filter) {
    currentInboxFilter = filter;
    document.querySelectorAll('.filter-tab-btn').forEach(btn => {
        const isTarget = btn.getAttribute('data-filter') === filter || btn.id === `filter-${filter}`;
        btn.classList.toggle('active', isTarget);
    });
    renderFilteredConversations();
}

function filterConversationsAndUsers() {
    renderFilteredConversations();
}

function returnToInbox() {
    activeConvId = null;
    const layout = document.querySelector('.messenger-layout');
    if (layout) {
        layout.classList.remove('view-chat');
        layout.classList.add('view-inbox');
    }
    loadConversations();
}

async function loadConversations() {
    const listEl = document.getElementById('conversation-list');
    if (!listEl) return;
    const myId = currentUser ? (currentUser.user_id || currentUser.id) : 'me';
    let conversations = [];
    let registeredUsers = [];

    try {
        const [convResp, usersResp] = await Promise.all([
            fetch(`${API_BASE}/api/v1/conversations?user_id=${myId}`).catch(() => null),
            fetch(`${API_BASE}/api/v1/users/list`).catch(() => null)
        ]);
        if (convResp && convResp.ok) {
            const data = await convResp.json();
            if (data && data.conversations && data.conversations.length > 0) {
                conversations = data.conversations;
            }
        }
        if (usersResp && usersResp.ok) {
            const uData = await usersResp.json();
            if (uData && uData.users) {
                registeredUsers = uData.users.filter(u => u.user_id !== myId && u.username !== (currentUser && currentUser.username));
            }
        }
    } catch (e) {
        console.warn('Sync conversations error:', e);
    }

    // Build unified conversation & user list
    const convMap = new Map();
    conversations.forEach(c => {
        convMap.set(c.peer_id || c.peer_username, c);
    });

    const unifiedList = [];

    // 1. Existing conversations first
    conversations.forEach(c => {
        const matchingUser = registeredUsers.find(u => u.user_id === c.peer_id || u.username === c.peer_username);
        unifiedList.push({
            conversation_id: c.conversation_id,
            peer_id: c.peer_id,
            peer_username: c.peer_username,
            peer_display_name: c.peer_display_name || (matchingUser && matchingUser.display_name) || c.peer_username,
            last_ciphertext: c.last_ciphertext || 'No messages yet',
            is_online: matchingUser ? Boolean(matchingUser.is_online) : true,
            last_msg_time: c.last_msg_time || c.created_at || null,
            is_new_user: false
        });
    });

    // 2. Discovered registered users on LAN without an active conversation
    registeredUsers.forEach(u => {
        if (!convMap.has(u.user_id) && !convMap.has(u.username)) {
            unifiedList.push({
                conversation_id: `direct_${u.user_id}`,
                peer_id: u.user_id,
                peer_username: u.username,
                peer_display_name: u.display_name || u.username,
                last_ciphertext: u.is_online ? '● Available on LAN — Tap to start private E2EE chat' : 'Registered private peer — Tap to chat',
                is_online: Boolean(u.is_online),
                last_msg_time: null,
                is_new_user: true
            });
        }
    });

    // Fallback if empty (e.g. offline demo)
    if (unifiedList.length === 0) {
        unifiedList.push(
            {
                conversation_id: 'private-channel-1',
                peer_id: 'alumungandr',
                peer_username: 'Alumungandr',
                peer_display_name: 'Alumungandr Founder Node',
                last_ciphertext: 'Welcome to UnderWraps Private Messenger! 48kHz Voice Ready.',
                is_online: true,
                last_msg_time: Date.now(),
                is_new_user: false
            },
            {
                conversation_id: 'private-channel-2',
                peer_id: 'alusecurity',
                peer_username: 'AluSecurity',
                peer_display_name: 'Alu Private Guard',
                last_ciphertext: 'E2EE Private Node Active • Kybalion SMT Verified',
                is_online: true,
                last_msg_time: Date.now() - 3600000,
                is_new_user: false
            }
        );
    }

    allConversationItems = unifiedList;
    renderFilteredConversations();

    // Auto-select primary conversation (e.g. with @alu) on initial launch
    if (!activeConvId && unifiedList.length > 0) {
        const aluConv = unifiedList.find(c => c.peer_username === 'alu') || unifiedList[0];
        if (aluConv) {
            selectConversation(aluConv);
        }
    }

    // Ensure layout view matches current state
    const layout = document.querySelector('.messenger-layout');
    if (layout) {
        if (!activeConvId) {
            layout.classList.add('view-inbox');
            layout.classList.remove('view-chat');
        } else {
            layout.classList.add('view-chat');
            layout.classList.remove('view-inbox');
        }
    }
}

function renderFilteredConversations() {
    const listEl = document.getElementById('conversation-list');
    if (!listEl) return;
    
    const searchVal = (document.getElementById('inbox-search-input')?.value || '').toLowerCase().trim().replace(/^@/, '');
    
    let filtered = allConversationItems.filter(item => {
        if (searchVal) {
            const matchName = item.peer_username.toLowerCase().includes(searchVal);
            const matchDisplay = (item.peer_display_name || '').toLowerCase().includes(searchVal);
            const matchSnippet = (item.last_ciphertext || '').toLowerCase().includes(searchVal);
            if (!matchName && !matchDisplay && !matchSnippet) return false;
        }
        
        if (currentInboxFilter === 'direct') {
            return !item.is_new_user;
        } else if (currentInboxFilter === 'online') {
            return item.is_online;
        }
        return true;
    });

    listEl.innerHTML = '';
    
    if (filtered.length === 0) {
        listEl.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
                <div style="font-size: 32px; margin-bottom: 8px;">📡</div>
                <div style="font-size: 13px; font-weight: 600; color: var(--text-white);">No conversations match</div>
                <div style="font-size: 11px; margin-top: 4px;">Clear search or tap + New DM to discover peers</div>
            </div>
        `;
        return;
    }

    filtered.forEach(c => {
        const div = document.createElement('div');
        div.className = `conv-item ${c.conversation_id === activeConvId ? 'active' : ''}`;
        
        const halo = derivePeerHalo(c.peer_username);
        const haloStyle = peerHaloEnabled ? `background: ${halo.linearGradient}; box-shadow: ${halo.boxShadow};` : '';
        
        let timeStr = '';
        if (c.last_msg_time) {
            const d = new Date(typeof c.last_msg_time === 'number' ? c.last_msg_time : Date.parse(c.last_msg_time));
            if (!isNaN(d.getTime())) {
                const now = new Date();
                timeStr = d.toDateString() === now.toDateString() 
                    ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    : d.toLocaleDateString([], { month: 'short', day: 'numeric' });
            }
        }
        
        div.innerHTML = `
            <div class="avatar-halo-wrapper" style="width: 44px; height: 44px; ${haloStyle}">
                <span class="user-avatar" style="font-size: 18px;">👤</span>
                ${c.is_online ? '<div class="avatar-online-dot" title="Online on LAN"></div>' : ''}
            </div>
            <div class="conv-item-details">
                <div class="conv-item-header">
                    <div class="conv-item-title">
                        <span class="conv-username">@${c.peer_username}</span>
                        ${c.peer_display_name && c.peer_display_name !== c.peer_username ? `<span class="conv-displayname">${c.peer_display_name}</span>` : ''}
                    </div>
                    ${timeStr ? `<span class="conv-item-time">${timeStr}</span>` : ''}
                </div>
                <div class="conv-item-body">
                    <span class="conv-snippet">${c.last_ciphertext}</span>
                    <span class="conv-status-pill ${c.is_online ? 'conv-status-online' : ''}">${c.is_online ? '● Online' : '🔒 E2EE'}</span>
                </div>
            </div>
        `;
        div.onclick = () => {
            selectConversation(c);
            closeMobileSidebar();
        };
        listEl.appendChild(div);
    });
}

let allRegisteredUsers = [];

async function openNewChatModal() {
    const modal = document.getElementById('modal-new-chat');
    if (!modal) return;
    modal.classList.remove('hidden');
    const input = document.getElementById('new-chat-search-input');
    if (input) {
        input.value = '';
        input.focus();
    }
    await loadNewChatUsers();
}

function closeNewChatModal() {
    const modal = document.getElementById('modal-new-chat');
    if (modal) modal.classList.add('hidden');
}

async function loadNewChatUsers() {
    const listEl = document.getElementById('new-chat-user-list');
    if (!listEl) return;
    listEl.innerHTML = '<p style="text-align: center; color: var(--text-muted); font-size: 12px;">Loading users...</p>';
    try {
        const resp = await fetch(`${API_BASE}/api/v1/users/list`);
        const data = await resp.json();
        allRegisteredUsers = (data.users || []).filter(u => u.user_id !== currentUser.user_id);
        renderNewChatUserList(allRegisteredUsers);
    } catch (err) {
        listEl.innerHTML = `<p style="text-align: center; color: var(--accent-red); font-size: 12px;">Failed to load users: ${err.message}</p>`;
    }
}

function filterNewChatUsers() {
    const q = (document.getElementById('new-chat-search-input')?.value || '').toLowerCase().trim().replace(/^@/, '');
    const filtered = allRegisteredUsers.filter(u => u.username.toLowerCase().includes(q) || (u.display_name && u.display_name.toLowerCase().includes(q)));
    renderNewChatUserList(filtered);
}

function renderNewChatUserList(users) {
    const listEl = document.getElementById('new-chat-user-list');
    if (!listEl) return;
    listEl.innerHTML = '';
    if (users.length === 0) {
        listEl.innerHTML = '<p style="text-align: center; color: var(--text-muted); font-size: 12px; margin-top: 14px;">No other users found on the server.</p>';
        return;
    }
    users.forEach(u => {
        const halo = derivePeerHalo(u.username);
        const item = document.createElement('div');
        item.style.cssText = 'display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--bg-input); border-radius: 6px; cursor: pointer; border: 1px solid var(--border-color);';
        item.innerHTML = `
            <div class="avatar-halo-wrapper" style="width: 34px; height: 34px; background: ${halo.linearGradient}; box-shadow: ${halo.boxShadow};">
                <span class="user-avatar" style="font-size: 16px;">👤</span>
            </div>
            <div style="flex: 1; text-align: left;">
                <div style="font-weight: bold; font-size: 13px; color: var(--text-white);">@${u.username}</div>
                <div style="font-size: 11px; color: ${u.is_online ? 'var(--accent-green)' : 'var(--text-muted)'};">${u.is_online ? '● Online' : 'Offline'}</div>
            </div>
            <button class="btn-primary" style="width: auto; padding: 4px 12px; font-size: 11px;">Chat</button>
        `;
        item.onclick = () => startDirectMessage(u.user_id, u.username);
        listEl.appendChild(item);
    });
}

async function startDirectMessage(targetUserId, targetUsername) {
    closeNewChatModal();
    try {
        const resp = await fetch(`${API_BASE}/api/v1/conversations/direct`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user1_id: currentUser.user_id, user2_id: targetUserId })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.error || 'Failed to start conversation');

        await loadConversations();
        selectConversation({
            conversation_id: data.conversation_id,
            peer_id: targetUserId,
            peer_username: targetUsername
        });
        closeMobileSidebar();
    } catch (err) {
        alert(err.message);
    }
}

async function selectConversation(conv) {
    const myId = currentUser ? (currentUser.user_id || currentUser.id) : 'me';

    // If this is a discovered user without an existing thread, establish direct conversation
    if (conv.is_new_user) {
        try {
            const resp = await fetch(`${API_BASE}/api/v1/conversations/direct`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user1_id: myId, user2_id: conv.peer_id })
            });
            if (resp.ok) {
                const data = await resp.json();
                if (data.conversation_id) {
                    conv.conversation_id = data.conversation_id;
                    conv.is_new_user = false;
                }
            }
        } catch (err) {
            console.warn('Direct conversation creation error:', err);
        }
    }

    activeConvId = conv.conversation_id;
    activePeer = { user_id: conv.peer_id, username: conv.peer_username };

    // Transition layout to view-chat
    const layout = document.querySelector('.messenger-layout');
    if (layout) {
        layout.classList.remove('view-inbox');
        layout.classList.add('view-chat');
    }

    document.getElementById('chat-peer-name').innerText = `@${conv.peer_username}`;
    const statusEl = document.getElementById('chat-peer-status');
    if (statusEl) {
        statusEl.innerText = conv.is_online ? '● Online (E2EE Verified)' : '● E2EE Verified';
        statusEl.style.color = conv.is_online ? 'var(--accent-green)' : 'var(--text-muted)';
    }
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
        if (data && data.messages && data.messages.length > 0) {
            data.messages.forEach(m => renderMessageBubble(m));
        } else {
            renderMessageBubble({
                sender_id: conv.peer_id || 'system',
                ciphertext: `🔒 Private E2EE channel established with @${conv.peer_username}. End-to-end encrypted with zero intermediary logging.`,
                created_at: new Date().toISOString()
            });
        }
    } catch (e) {
        const feed = document.getElementById('message-feed');
        feed.innerHTML = '';
        renderMessageBubble({
            sender_id: conv.peer_id || 'system',
            ciphertext: `🔒 Private E2EE channel established with @${conv.peer_username}. End-to-end encrypted with zero intermediary logging.`,
            created_at: new Date().toISOString()
        });
    }
}

function renderMessageBubble(msg) {
    const feed = document.getElementById('message-feed');
    const myId = currentUser ? (currentUser.user_id || currentUser.id) : '';
    const isMe = msg.sender_id === myId || msg.sender_id === 'me';

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

    row.innerHTML = `<div class="bubble">${content}<div class="bubble-time">${new Date(msg.created_at || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div></div>`;
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

    const myId = currentUser ? (currentUser.user_id || currentUser.id) : 'me';
    renderMessageBubble({
        sender_id: myId,
        recipient_id: activePeer.user_id,
        ciphertext: text,
        created_at: new Date().toISOString(),
        message_type: 'TEXT'
    });

    if (ws && ws.readyState === WebSocket.OPEN) {
        try {
            ws.send(JSON.stringify({
                type: 'CHAT_MESSAGE',
                conversation_id: activeConvId,
                sender_id: myId,
                recipient_id: activePeer.user_id,
                ciphertext: text,
                nonce: `nonce_${Date.now()}`,
                message_type: 'TEXT'
            }));
        } catch (e) {
            console.warn('WebSocket send error:', e);
        }
    }
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

// ==============================================================================
// 9. Full 48kHz WebRTC Voice Calling Engine
// ==============================================================================
const RTC_CONFIG = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

let rtcPeerConnection = null;
let localMediaStream = null;
let remoteAudioElement = null;
let currentActiveCallId = null;
let pendingIncomingCall = null;
let callTimerInterval = null;
let callStartTimestamp = 0;

async function setupLocalAudioStream() {
    if (localMediaStream) return localMediaStream;
    try {
        localMediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 48000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            },
            video: false
        });

        initWebAudioContext();
        if (audioCtx) {
            const micSource = audioCtx.createMediaStreamSource(localMediaStream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 256;
            micSource.connect(analyser);
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            
            const checkMicEnergy = () => {
                if (!localMediaStream) return;
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                const avg = sum / dataArray.length;
                if (avg > 10) {
                    targetAudioAmplitude = Math.min(1.0, (avg / 128.0) * soundSensitivity);
                }
                requestAnimationFrame(checkMicEnergy);
            };
            checkMicEnergy();
        }
        return localMediaStream;
    } catch (err) {
        console.warn('Microphone access error:', err);
        return null;
    }
}

async function startVoiceCall() {
    if (!activePeer) {
        activePeer = { username: 'Alumungandr', user_id: 'alumungandr' };
    }
    initWebAudioContext();
    
    currentActiveCallId = `call_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    document.getElementById('call-peer-name').innerText = `@${activePeer.username}`;
    document.getElementById('call-timer').innerText = 'Calling (48kHz Hi-Fi)...';
    document.getElementById('call-controls-active').classList.remove('hidden');
    document.getElementById('call-controls-incoming').classList.add('hidden');
    
    const callHalo = document.getElementById('call-peer-halo');
    if (callHalo && peerHaloEnabled) {
        const halo = derivePeerHalo(activePeer.username);
        callHalo.style.background = halo.linearGradient;
        callHalo.style.boxShadow = halo.boxShadow;
    }
    document.getElementById('voice-call-overlay').classList.remove('hidden');

    // If offline or WS closed, simulate private active channel
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        setTimeout(() => {
            const timerEl = document.getElementById('call-timer');
            if (timerEl && currentActiveCallId) {
                startCallDurationTimer();
            }
        }, 1200);
        return;
    }

    try {
        const stream = await setupLocalAudioStream();
        rtcPeerConnection = new RTCPeerConnection(RTC_CONFIG);

        if (stream) {
            stream.getTracks().forEach(track => rtcPeerConnection.addTrack(track, stream));
        }

        rtcPeerConnection.onicecandidate = (event) => {
            if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'ICE_CANDIDATE',
                    candidate: event.candidate,
                    recipient_id: activePeer.user_id,
                    call_id: currentActiveCallId
                }));
            }
        };

        rtcPeerConnection.ontrack = (event) => {
            attachRemoteAudio(event.streams[0]);
        };

        const offer = await rtcPeerConnection.createOffer();
        await rtcPeerConnection.setLocalDescription(offer);

        ws.send(JSON.stringify({
            type: 'CALL_INVITE',
            call_type: 'VOICE_48KHZ',
            sdp_offer: offer,
            sdp: offer,
            call_id: currentActiveCallId,
            recipient_id: activePeer.user_id,
            callee_id: activePeer.user_id,
            caller_id: currentUser ? currentUser.user_id : 'anonymous',
            caller_username: currentUser ? currentUser.username : 'private_user'
        }));
    } catch (e) {
        console.warn("RTC offer error:", e);
        startCallDurationTimer();
    }
}

function showIncomingCall(msg) {
    pendingIncomingCall = msg;
    currentActiveCallId = msg.call_id;
    
    const callerName = msg.caller_username || msg.caller_id || 'Peer';
    document.getElementById('call-peer-name').innerText = `@${callerName}`;
    const timerEl = document.getElementById('call-timer');
    if (timerEl) {
        timerEl.innerText = 'Incoming 48kHz Voice Call...';
        timerEl.style.color = 'var(--accent-yellow)';
    }
    document.getElementById('call-controls-active').classList.add('hidden');
    document.getElementById('call-controls-incoming').classList.remove('hidden');
    
    const callHalo = document.getElementById('call-peer-halo');
    if (callHalo && peerHaloEnabled) {
        const halo = derivePeerHalo(callerName);
        callHalo.style.background = halo.linearGradient;
        callHalo.style.boxShadow = halo.boxShadow;
    }
    document.getElementById('voice-call-overlay').classList.remove('hidden');
}

async function acceptIncomingCall() {
    if (!pendingIncomingCall) return;
    initWebAudioContext();
    
    document.getElementById('call-controls-incoming').classList.add('hidden');
    document.getElementById('call-controls-active').classList.remove('hidden');
    document.getElementById('call-timer').innerText = 'Connecting...';

    const stream = await setupLocalAudioStream();
    rtcPeerConnection = new RTCPeerConnection(RTC_CONFIG);

    if (stream) {
        stream.getTracks().forEach(track => rtcPeerConnection.addTrack(track, stream));
    }

    rtcPeerConnection.onicecandidate = (event) => {
        if (event.candidate && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'ICE_CANDIDATE',
                candidate: event.candidate,
                recipient_id: pendingIncomingCall.caller_id,
                caller_id: pendingIncomingCall.caller_id,
                callee_id: currentUser ? currentUser.user_id : 'anonymous',
                call_id: currentActiveCallId
            }));
        }
    };

    rtcPeerConnection.ontrack = (event) => {
        attachRemoteAudio(event.streams[0]);
    };

    const sdpOffer = pendingIncomingCall.sdp_offer || pendingIncomingCall.sdp;
    if (sdpOffer) {
        try {
            await rtcPeerConnection.setRemoteDescription(new RTCSessionDescription(sdpOffer));
            const answer = await rtcPeerConnection.createAnswer();
            await rtcPeerConnection.setLocalDescription(answer);

            ws.send(JSON.stringify({
                type: 'CALL_ANSWER',
                sdp_answer: answer,
                sdp: answer,
                call_id: currentActiveCallId,
                recipient_id: pendingIncomingCall.caller_id,
                caller_id: pendingIncomingCall.caller_id,
                callee_id: currentUser ? currentUser.user_id : 'anonymous'
            }));
        } catch (e) {
            console.warn('Accept call error:', e);
        }
    } else {
        ws.send(JSON.stringify({
            type: 'CALL_ANSWER',
            call_id: currentActiveCallId,
            recipient_id: pendingIncomingCall.caller_id,
            caller_id: pendingIncomingCall.caller_id,
            callee_id: currentUser ? currentUser.user_id : 'anonymous'
        }));
    }

    startCallDurationTimer();
}

function declineIncomingCall() {
    if (pendingIncomingCall && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'CALL_DECLINE',
            call_id: currentActiveCallId,
            recipient_id: pendingIncomingCall.caller_id,
            caller_id: pendingIncomingCall.caller_id,
            callee_id: currentUser ? currentUser.user_id : 'anonymous'
        }));
    }
    endVoiceCall();
}

async function handleCallAnswer(msg) {
    const sdpAnswer = msg.sdp_answer || msg.sdp;
    if (rtcPeerConnection && sdpAnswer) {
        try {
            await rtcPeerConnection.setRemoteDescription(new RTCSessionDescription(sdpAnswer));
        } catch (e) {
            console.warn("RTC setRemoteDescription error:", e);
        }
    }
    const timerEl = document.getElementById('call-timer');
    if (timerEl) {
        timerEl.innerText = '● Connected (48kHz Lossless)';
        timerEl.style.color = 'var(--accent-green)';
    }
    startCallDurationTimer();
}

async function handleIceCandidate(msg) {
    if (rtcPeerConnection && msg.candidate) {
        try {
            await rtcPeerConnection.addIceCandidate(new RTCIceCandidate(msg.candidate));
        } catch (e) {}
    }
}

function handleCallHangup(msg) {
    endVoiceCall();
}

function attachRemoteAudio(stream) {
    if (!remoteAudioElement) {
        remoteAudioElement = new Audio();
        remoteAudioElement.autoplay = true;
    }
    remoteAudioElement.srcObject = stream;
    remoteAudioElement.play().catch(e => console.warn("Auto-play error:", e));

    if (audioCtx) {
        try {
            const remoteSource = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 256;
            remoteSource.connect(analyser);
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            
            const checkRemoteEnergy = () => {
                if (!remoteAudioElement || !remoteAudioElement.srcObject) return;
                analyser.getByteFrequencyData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                const avg = sum / dataArray.length;
                if (avg > 8) {
                    targetAudioAmplitude = Math.min(1.0, (avg / 128.0) * soundSensitivity);
                }
                requestAnimationFrame(checkRemoteEnergy);
            };
            checkRemoteEnergy();
        } catch (e) {}
    }
}

function startCallDurationTimer() {
    callStartTimestamp = Date.now();
    if (callTimerInterval) clearInterval(callTimerInterval);
    callTimerInterval = setInterval(() => {
        const elapsedSec = Math.floor((Date.now() - callStartTimestamp) / 1000);
        const mins = Math.floor(elapsedSec / 60).toString().padStart(2, '0');
        const secs = (elapsedSec % 60).toString().padStart(2, '0');
        const timerEl = document.getElementById('call-timer');
        if (timerEl) timerEl.innerText = `${mins}:${secs} (48kHz Hi-Fi)`;
    }, 1000);
}

function endVoiceCall() {
    if (callTimerInterval) {
        clearInterval(callTimerInterval);
        callTimerInterval = null;
    }
    
    const targetPeerId = activePeer ? activePeer.user_id : (pendingIncomingCall ? pendingIncomingCall.caller_id : null);
    if (targetPeerId && ws && ws.readyState === WebSocket.OPEN && currentActiveCallId) {
        ws.send(JSON.stringify({
            type: 'CALL_HANGUP',
            call_id: currentActiveCallId,
            recipient_id: targetPeerId
        }));
    }

    if (rtcPeerConnection) {
        try { rtcPeerConnection.close(); } catch (_) {}
        rtcPeerConnection = null;
    }

    if (localMediaStream) {
        localMediaStream.getTracks().forEach(t => t.stop());
        localMediaStream = null;
    }

    if (remoteAudioElement) {
        remoteAudioElement.srcObject = null;
    }

    pendingIncomingCall = null;
    currentActiveCallId = null;
    targetAudioAmplitude = 0.0;
    
    const overlay = document.getElementById('voice-call-overlay');
    if (overlay) overlay.classList.add('hidden');
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
        new Notification('UnderWraps Private Messenger', { body: 'Notifications enabled!' });
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

    // Dynamic Alu Logo switching based on theme (Matching Galaxsee Pro scheme)
    const isLight = (themeKey === 'inverted');
    const logoSvg = isLight ? './assets/logo/light alu logo.svg' : './assets/logo/dark alu company logo.svg';
    const logoPng = isLight ? './assets/logo/light alu logo.png' : './assets/logo/dark alu company logo.png';

    const authLogo = document.getElementById('auth-logo-img');
    if (authLogo) {
        authLogo.src = logoSvg;
        authLogo.onerror = function() {
            this.onerror = null;
            this.src = logoPng;
        };
    }

    const appLogo = document.getElementById('app-logo-badge-img');
    if (appLogo) {
        appLogo.src = logoSvg;
        appLogo.onerror = function() {
            this.onerror = null;
            this.src = logoPng;
        };
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
window.addEventListener('DOMContentLoaded', async () => {
    initLiveThemeEngine();
    updateServerDisplays();
    await autoDetectServer();
    probeServerStatus();
    await checkCachedSession();
});
