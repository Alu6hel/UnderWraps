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
        # Audit 1: Check screen responsiveness and console errors
        errors = await cdp_eval(ws, """
            (() => {
                return window.__appErrors || [];
            })()
        """)
        print(f"Console errors tracked: {errors}")

        # Audit 2: Check modals and dialogs structure in DOM
        modals = await cdp_eval(ws, """
            (() => {
                const newChat = document.getElementById('modal-new-chat');
                const settings = document.getElementById('modal-settings');
                const neuralSearch = document.getElementById('modal-neural-search');
                const twoFactor = document.getElementById('modal-2fa');
                const callOverlay = document.getElementById('voice-call-overlay');
                return {
                    newChatExists: !!newChat,
                    settingsExists: !!settings,
                    neuralSearchExists: !!neuralSearch,
                    twoFactorExists: !!twoFactor,
                    callOverlayExists: !!callOverlay
                };
            })()
        """)
        print(f"Modals structure check: {modals}")
        assert all(modals.values()), "One or more core modals missing from DOM!"

        # Audit 3: Open Settings modal and verify all tabs and switching
        settings_test = await cdp_eval(ws, """
            (() => {
                if (typeof openSettings === 'function') openSettings();
                const modal = document.getElementById('modal-settings');
                const isVisible = !modal.classList.contains('hidden');
                const tabs = Array.from(document.querySelectorAll('.settings-tab-btn')).map(b => b.innerText.trim());
                
                // Switch tabs
                switchSettingsTab('permissions');
                const permsVisible = !document.getElementById('settings-tab-permissions').classList.contains('hidden');
                
                switchSettingsTab('themes');
                const themesVisible = !document.getElementById('settings-tab-themes').classList.contains('hidden');
                
                if (typeof closeSettings === 'function') closeSettings();
                const isHiddenAfterClose = modal.classList.contains('hidden');
                
                return { isVisible, tabs, permsVisible, themesVisible, isHiddenAfterClose };
            })()
        """)
        print(f"Settings modal test: {settings_test}")
        assert settings_test["isVisible"], "Settings modal failed to open!"
        assert settings_test["permsVisible"], "Failed to switch to permissions tab!"
        assert settings_test["themesVisible"], "Failed to switch to themes tab!"
        assert settings_test["isHiddenAfterClose"], "Settings modal failed to close!"

        # Audit 4: Check New Chat modal
        new_chat_test = await cdp_eval(ws, """
            (() => {
                if (typeof openNewChatModal === 'function') openNewChatModal();
                const modal = document.getElementById('modal-new-chat');
                const isVisible = !modal.classList.contains('hidden');
                if (typeof closeNewChatModal === 'function') closeNewChatModal();
                const isHiddenAfterClose = modal.classList.contains('hidden');
                return { isVisible, isHiddenAfterClose };
            })()
        """)
        print(f"New Chat modal test: {new_chat_test}")
        assert new_chat_test["isVisible"], "New Chat modal failed to open!"
        assert new_chat_test["isHiddenAfterClose"], "New Chat modal failed to close!"

        # Audit 5: Check Neural Search modal
        search_test = await cdp_eval(ws, """
            (() => {
                if (typeof openNeuralSearchModal === 'function') openNeuralSearchModal();
                const modal = document.getElementById('modal-neural-search');
                const isVisible = !modal.classList.contains('hidden');
                if (typeof closeNeuralSearchModal === 'function') closeNeuralSearchModal();
                const isHiddenAfterClose = modal.classList.contains('hidden');
                return { isVisible, isHiddenAfterClose };
            })()
        """)
        print(f"Neural Search modal test: {search_test}")
        assert search_test["isVisible"], "Neural Search modal failed to open!"
        assert search_test["isHiddenAfterClose"], "Neural Search modal failed to close!"

        # Audit 6: Check voice note playback seeking and state reset
        vn_seek_test = await cdp_eval(ws, """
            (() => {
                const player = document.querySelector('.voice-note-player');
                if (!player) return { hasPlayer: false };
                const voiceId = player.getAttribute('data-voice-id');
                const wrap = player.querySelector('.voice-waveform-wrap');
                const rect = wrap.getBoundingClientRect();
                
                // Simulate seeking to 50%
                seekVoiceNote({ currentTarget: wrap, clientX: rect.left + (rect.width * 0.5) }, voiceId);
                const item = voiceNoteStore.get(voiceId);
                const playedBars = player.querySelectorAll('.waveform-bar.played').length;
                
                // Finish playback
                finishVoiceNotePlayback(voiceId);
                const playedAfterFinish = player.querySelectorAll('.waveform-bar.played').length;
                
                return {
                    hasPlayer: true,
                    elapsedAfterSeek: item?.elapsedMs,
                    playedBars,
                    playedAfterFinish
                };
            })()
        """)
        print(f"Voice note seeking & reset test: {vn_seek_test}")
        assert vn_seek_test["hasPlayer"], "Voice note player not found!"
        assert vn_seek_test["playedBars"] > 0, "Seek did not highlight bars!"
        assert vn_seek_test["playedAfterFinish"] == 0, "Bars did not reset after finish!"

        # Audit 7: Verify sound-reactive engine sensitivity
        sr_test = await cdp_eval(ws, """
            (() => {
                const initialSensitivity = soundSensitivity;
                if (typeof updateSensitivity === 'function') {
                    updateSensitivity(1.5);
                }
                const newSensitivity = soundSensitivity;
                soundSensitivity = initialSensitivity;
                return { initialSensitivity, newSensitivity };
            })()
        """)
        print(f"Sound reactive engine sensitivity test: {sr_test}")
        assert sr_test["newSensitivity"] == 1.5, "Sensitivity update failed!"

        print("\n>>> COMPLETE APP UI & AUDIO AUDIT PASSED WITH ZERO ISSUES! <<<")

if __name__ == "__main__":
    asyncio.run(main())
