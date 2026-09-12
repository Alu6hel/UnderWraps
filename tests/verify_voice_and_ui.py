import asyncio
import json
import time
import urllib.request
import websockets

async def cdp_eval(ws, expr):
    msg_id = int(time.time() * 1000) % 1000000
    req = {
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        }
    }
    await ws.send(json.dumps(req))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            res = resp.get("result", {}).get("result", {})
            if "value" in res:
                return res["value"]
            return res

async def main():
    req = urllib.request.urlopen("http://localhost:9223/json")
    targets = json.loads(req.read().decode("utf-8"))
    page = next(t for t in targets if t.get("type") == "page")
    ws_url = page["webSocketDebuggerUrl"]
    print(f"Connecting to CDP: {ws_url}")

    async with websockets.connect(ws_url) as ws:
        active_screen = await cdp_eval(ws, "document.querySelector('.screen:not(.hidden)')?.id || 'none'")
        print(f"Active Screen: {active_screen}")

        if active_screen != "screen-chat":
            login_res = await cdp_eval(ws, """
                (async () => {
                    if (typeof checkCachedSession === 'function') await checkCachedSession();
                    if (document.getElementById('screen-chat').classList.contains('hidden')) {
                        if (typeof switchScreen === 'function') switchScreen('screen-chat');
                        if (!currentUser) currentUser = { user_id: 'usr_me_test', username: 'alu_test' };
                        if (!activeConvId) {
                            activeConvId = 'conv_alu_test';
                            activePeer = { user_id: 'usr_peer_alu', username: 'alu' };
                        }
                    }
                    return document.querySelector('.screen:not(.hidden)')?.id;
                })()
            """)
            print(f"Screen after navigation: {login_res}")

        setup_chat = await cdp_eval(ws, """
            (() => {
                if (!activeConvId) {
                    activeConvId = 'conv_alu_test';
                    activePeer = { user_id: 'usr_peer_alu', username: 'alu' };
                }
                const peerNameEl = document.getElementById('chat-peer-username');
                if (peerNameEl) peerNameEl.innerText = '@alu';
                return { activeConvId, activePeer };
            })()
        """)
        print(f"Chat setup: {setup_chat}")

        # TEST 1: Voice Note Studio Recording
        print("\n--- TEST 1: Voice Note Studio Recording ---")
        start_rec = await cdp_eval(ws, """
            (async () => {
                startVoiceNoteRecording();
                const studio = document.getElementById('voice-recording-studio');
                const defaultInput = document.getElementById('default-input-controls');
                const numBars = studio.querySelectorAll('.live-vu-bar').length;
                const isStudioVisible = !studio.classList.contains('hidden');
                const isDefaultHidden = defaultInput.classList.contains('hidden');
                return { isStudioVisible, isDefaultHidden, numBars };
            })()
        """)
        print(f"Voice Studio Recording started: {start_rec}")
        assert start_rec["isStudioVisible"] == True, "Voice recording studio not visible!"
        assert start_rec["isDefaultHidden"] == True, "Default input controls not hidden!"
        assert start_rec["numBars"] == 20, f"Expected 20 VU bars, got {start_rec['numBars']}"

        await asyncio.sleep(1.5)

        timer_val = await cdp_eval(ws, "document.getElementById('voice-record-timer').innerText")
        print(f"Voice record timer after 1.5s: {timer_val}")
        assert timer_val != "00:00", "Recording timer failed to update!"

        finish_rec = await cdp_eval(ws, """
            (async () => {
                await finishVoiceNoteRecording();
                const studio = document.getElementById('voice-recording-studio');
                const defaultInput = document.getElementById('default-input-controls');
                const isStudioHidden = studio.classList.contains('hidden');
                const isDefaultVisible = !defaultInput.classList.contains('hidden');
                const bubbles = document.querySelectorAll('.voice-note-player');
                return { isStudioHidden, isDefaultVisible, count: bubbles.length };
            })()
        """)
        print(f"Voice Studio Finished: {finish_rec}")
        assert finish_rec["isStudioHidden"] == True, "Studio did not hide after send!"
        assert finish_rec["isDefaultVisible"] == True, "Default input controls did not restore!"
        assert finish_rec["count"] >= 1, "Voice note player bubble was not rendered in feed!"

        # TEST 2: Voice Note Playback
        print("\n--- TEST 2: Voice Note Playback & Waveform ---")
        player_info = await cdp_eval(ws, """
            (() => {
                const player = document.querySelector('.voice-note-player');
                const voiceId = player.getAttribute('data-voice-id');
                const bars = player.querySelectorAll('.waveform-bar').length;
                const btn = document.getElementById(`btn-vplay-${voiceId}`);
                const durationText = document.getElementById(`vtime-${voiceId}`)?.innerText;
                return { voiceId, bars, btnText: btn?.innerText, durationText };
            })()
        """)
        print(f"Voice note bubble details: {player_info}")
        assert player_info["bars"] == 24, f"Expected 24 waveform bars, got {player_info['bars']}"

        voice_id = player_info["voiceId"]
        play_res = await cdp_eval(ws, f"""
            (() => {{
                toggleVoiceNotePlayback('{voice_id}');
                const item = voiceNoteStore.get('{voice_id}');
                const btn = document.getElementById('btn-vplay-{voice_id}');
                return {{ isPlaying: item?.isPlaying, btnText: btn?.innerText }};
            }})()
        """)
        print(f"Voice note playback toggled: {play_res}")
        assert play_res["isPlaying"] == True, "Voice note item is not playing!"
        assert play_res["btnText"] == "⏸", "Button text did not change to pause!"

        await asyncio.sleep(1.0)
        progress_info = await cdp_eval(ws, f"""
            (() => {{
                const item = voiceNoteStore.get('{voice_id}');
                const barsPlayed = document.querySelectorAll('#vbars-{voice_id} .waveform-bar.played').length;
                const timeText = document.getElementById('vtime-{voice_id}')?.innerText;
                return {{ elapsedMs: item?.elapsedMs, barsPlayed, timeText, targetAmp: targetAudioAmplitude }};
            }})()
        """)
        print(f"Voice note playback progression: {progress_info}")
        assert progress_info["barsPlayed"] > 0, "Waveform bars did not highlight with .played class!"
        assert progress_info["targetAmp"] > 0.0, "Sound-reactive amplitude did not pulse during playback!"

        pause_res = await cdp_eval(ws, f"""
            (() => {{
                toggleVoiceNotePlayback('{voice_id}');
                const item = voiceNoteStore.get('{voice_id}');
                const btn = document.getElementById('btn-vplay-{voice_id}');
                return {{ isPlaying: item?.isPlaying, btnText: btn?.innerText }};
            }})()
        """)
        print(f"Voice note paused: {pause_res}")
        assert pause_res["isPlaying"] == False, "Voice note did not pause!"
        assert pause_res["btnText"] == "▶", "Button text did not revert to play!"

        # TEST 3: Voice Call with Auto-Connect & Two-Way Conversation
        print("\n--- TEST 3: 48kHz Voice Call Lifecycle & Conversation ---")
        call_start = await cdp_eval(ws, """
            (async () => {
                await startVoiceCall();
                const overlay = document.getElementById('voice-call-overlay');
                const isOverlayVisible = !overlay.classList.contains('hidden');
                const timerText = document.getElementById('call-timer')?.innerText;
                return { isOverlayVisible, timerText, state: currentCallState };
            })()
        """)
        print(f"Voice call initiated: {call_start}")
        assert call_start["isOverlayVisible"] == True, "Voice call overlay is not visible!"
        assert "Calling" in call_start["timerText"] or "Connected" in call_start["timerText"]

        print("Waiting 3.6s for call to connect...")
        await asyncio.sleep(3.6)

        call_connected = await cdp_eval(ws, """
            (() => {
                const timerText = document.getElementById('call-timer')?.innerText;
                const isMeterVisible = !document.getElementById('call-audio-meter-wrap').classList.contains('hidden');
                return { state: currentCallState, timerText, isMeterVisible, isCallMuted };
            })()
        """)
        print(f"Voice call connected state: {call_connected}")
        assert call_connected["state"] == "CONNECTED", f"Call did not connect! State: {call_connected['state']}"
        assert call_connected["isMeterVisible"] == True, "Call audio meter is not visible!"

        speak_res = await cdp_eval(ws, """
            (() => {
                speakPeerVoice("Testing two way voice conversation in UnderWraps.");
                const meterWidth = document.getElementById('call-audio-meter')?.style.width;
                return { meterWidth, targetAmp: targetAudioAmplitude };
            })()
        """)
        print(f"Conversational peer speech test: {speak_res}")
        assert speak_res["targetAmp"] > 0.0, "Acoustic audio did not drive amplitude!"

        mute_res = await cdp_eval(ws, """
            (() => {
                toggleCallMute();
                const btnMute = document.getElementById('btn-call-mute');
                return { isCallMuted, btnText: btnMute.innerText };
            })()
        """)
        print(f"Mute toggle: {mute_res}")
        assert mute_res["isCallMuted"] == True, "Mute toggle failed!"

        unmute_res = await cdp_eval(ws, """
            (() => {
                toggleCallMute();
                const btnMute = document.getElementById('btn-call-mute');
                return { isCallMuted, btnText: btnMute.innerText };
            })()
        """)
        print(f"Unmute toggle: {unmute_res}")
        assert unmute_res["isCallMuted"] == False, "Unmute toggle failed!"

        end_res = await cdp_eval(ws, """
            (() => {
                endVoiceCall();
                const timerText = document.getElementById('call-timer')?.innerText;
                return { state: currentCallState, timerText };
            })()
        """)
        print(f"Call ended: {end_res}")
        assert end_res["state"] == "ENDED", "Call state did not transition to ENDED!"
        assert end_res["timerText"] == "Call Ended"

        await asyncio.sleep(1.4)
        overlay_closed = await cdp_eval(ws, "document.getElementById('voice-call-overlay').classList.contains('hidden')")
        print(f"Overlay closed after 1.4s: {overlay_closed}")
        assert overlay_closed == True, "Overlay did not hide after call ended!"

        print("\n>>> ALL TESTS PASSED SUCCESSFULLY ON REAL DEVICE WEBVIEW! <<<")

if __name__ == "__main__":
    asyncio.run(main())
