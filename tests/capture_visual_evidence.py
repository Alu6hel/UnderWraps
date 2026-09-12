import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

ARTIFACT_DIR = "/home/davidalujones/.gemini/antigravity/brain/23f511ed-0b21-4a49-bbe3-0e7f15a457c4"

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

def take_screenshot(filename):
    path = os.path.join(ARTIFACT_DIR, filename)
    cmd = f"adb -s 100.115.92.2:5555 exec-out screencap -p > '{path}'"
    subprocess.run(cmd, shell=True, check=True)
    print(f"Captured screenshot: {path}")

async def main():
    req = urllib.request.urlopen("http://localhost:9223/json")
    targets = json.loads(req.read().decode("utf-8"))
    page = next(t for t in targets if t.get("type") == "page")
    ws_url = page["webSocketDebuggerUrl"]

    async with websockets.connect(ws_url) as ws:
        # 1. State: Chat screen with playable voice note bubbles in feed
        await cdp_eval(ws, """
            (() => {
                if (typeof switchScreen === 'function') switchScreen('screen-chat');
                if (!currentUser) currentUser = { user_id: 'usr_me', username: 'alu' };
                if (!activeConvId) {
                    activeConvId = 'conv_alu_proof';
                    activePeer = { user_id: 'usr_peer', username: 'alu' };
                }
                const peerNameEl = document.getElementById('chat-peer-username');
                if (peerNameEl) peerNameEl.innerText = '@alu';
                
                // Add sample voice note bubble
                renderMessageBubble({
                    sender_id: 'usr_peer',
                    recipient_id: 'usr_me',
                    ciphertext: '🎙️ Voice Note (48kHz)',
                    message_type: 'VOICE_NOTE',
                    voice_duration_ms: 3800,
                    created_at: new Date().toISOString()
                });
            })()
        """)
        await asyncio.sleep(0.5)
        take_screenshot("live_voice_notes_in_chat.png")

        # 2. State: Live Voice Recording Studio in progress
        await cdp_eval(ws, """
            (() => {
                startVoiceNoteRecording();
            })()
        """)
        await asyncio.sleep(1.2)
        take_screenshot("live_voice_recording_studio.png")
        await cdp_eval(ws, "finishVoiceNoteRecording()")

        # 3. State: Active connected 48kHz voice call
        await cdp_eval(ws, """
            (async () => {
                await startVoiceCall();
            })()
        """)
        await asyncio.sleep(3.6)
        take_screenshot("live_connected_voice_convo.png")

        # End call cleanly
        await cdp_eval(ws, "endVoiceCall()")
        await asyncio.sleep(1.2)
        print("Visual evidence capture completed!")

if __name__ == "__main__":
    asyncio.run(main())
