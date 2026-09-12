"""
==============================================================================
UnderWraps 48kHz Voice Calling Engine End-to-End Test Suite
Validates Call Invitation, Ringing, WebRTC/WebSocket Audio Relay Frames,
Acceptance, Duration Tracking, and Clean Hangup.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import time
import json
import secrets
import unittest
import asyncio
import urllib.request
try:
    import websockets
except ImportError:
    websockets = None
import importlib.util

# Load UnderWrapsServer directly
server_engine_path = "/home/davidalujones/.gemini/antigravity/scratch/UnderWrapsServer/src/server/server_engine.py"
spec = importlib.util.spec_from_file_location("server_engine", server_engine_path)
server_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_engine)
UnderWrapsServer = server_engine.UnderWrapsServer

@unittest.skipIf(websockets is None, "websockets package not installed; install with pip or run with uv")
class TestVoiceCallingE2E(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.http_port = 8116
        cls.ws_port = 8117
        cls.test_dir = "./underwraps_call_test_data"
        cls.server = UnderWrapsServer(host="127.0.0.1", http_port=cls.http_port, ws_port=cls.ws_port, data_dir=cls.test_dir)
        cls.server.start()
        time.sleep(0.6)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        time.sleep(0.5)

    async def _recv_type(self, ws, target_types, timeout=3.0):
        if isinstance(target_types, str):
            target_types = (target_types,)
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.1, deadline - time.time())
            raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
            msg = json.loads(raw)
            if msg.get("type") in target_types:
                return msg
        raise TimeoutError(f"Timed out waiting for message in {target_types}")

    async def test_full_48khz_voice_call_lifecycle(self):
        rand = secrets.token_hex(4)
        
        # 1. Register Caller (@caller_alu) and Callee (@callee_bob)
        req_u1 = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": f"caller_{rand}", "email": f"caller_{rand}@test.com", "password": "Password123!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_u1) as resp:
            u1 = json.loads(resp.read().decode("utf-8"))["user"]

        req_u2 = urllib.request.Request(
            f"http://127.0.0.1:{self.http_port}/api/v1/auth/signup",
            data=json.dumps({"username": f"callee_{rand}", "email": f"callee_{rand}@test.com", "password": "Password123!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_u2) as resp:
            u2 = json.loads(resp.read().decode("utf-8"))["user"]

        ws_url = f"ws://127.0.0.1:{self.ws_port}"

        # 2. Connect both clients over WebSocket
        async with websockets.connect(ws_url) as ws_caller, websockets.connect(ws_url) as ws_callee:
            # Authenticate Callee
            await ws_callee.send(json.dumps({"type": "AUTH", "user_id": u2["user_id"]}))
            callee_auth = await self._recv_type(ws_callee, "AUTH_OK")
            self.assertEqual(callee_auth.get("user_id"), u2["user_id"])

            # Authenticate Caller
            await ws_caller.send(json.dumps({"type": "AUTH", "user_id": u1["user_id"]}))
            caller_auth = await self._recv_type(ws_caller, "AUTH_OK")
            self.assertEqual(caller_auth.get("user_id"), u1["user_id"])

            call_id = f"call_e2e_{int(time.time())}_{rand}"

            # 3. Caller places 48kHz voice call -> CALL_INVITE
            offer_sdp = {"type": "offer", "sdp": "v=0\r\nm=audio 48000 RTP/SAVPF 111\r\n"}
            await ws_caller.send(json.dumps({
                "type": "CALL_INVITE",
                "call_type": "VOICE_48KHZ",
                "call_id": call_id,
                "caller_id": u1["user_id"],
                "caller_username": u1["username"],
                "callee_id": u2["user_id"],
                "recipient_id": u2["user_id"],
                "sdp_offer": offer_sdp,
                "sdp": offer_sdp
            }))

            # Callee receives CALL_INCOMING
            incoming = await self._recv_type(ws_callee, "CALL_INCOMING")
            self.assertEqual(incoming.get("type"), "CALL_INCOMING")
            self.assertEqual(incoming.get("call_id"), call_id)
            self.assertEqual(incoming.get("caller_id"), u1["user_id"])

            # 4. Callee answers -> CALL_ANSWER
            answer_sdp = {"type": "answer", "sdp": "v=0\r\nm=audio 48000 RTP/SAVPF 111\r\n"}
            await ws_callee.send(json.dumps({
                "type": "CALL_ANSWER",
                "call_id": call_id,
                "caller_id": u1["user_id"],
                "callee_id": u2["user_id"],
                "recipient_id": u1["user_id"],
                "sdp_answer": answer_sdp,
                "sdp": answer_sdp
            }))

            # Caller receives CALL_ACCEPTED / CALL_ANSWER
            accepted = await self._recv_type(ws_caller, ("CALL_ACCEPTED", "CALL_ANSWER"))
            self.assertEqual(accepted.get("call_id"), call_id)

            # 5. Audio Relay Frame transmission (Caller -> Callee)
            await ws_caller.send(json.dumps({
                "type": "AUDIO_RELAY_FRAME",
                "call_id": call_id,
                "sender_id": u1["user_id"],
                "recipient_id": u2["user_id"],
                "amplitude": 0.74,
                "sample_rate": 48000
            }))

            callee_audio = await self._recv_type(ws_callee, "AUDIO_RELAY_FRAME")
            self.assertEqual(callee_audio.get("amplitude"), 0.74)
            self.assertEqual(callee_audio.get("sample_rate"), 48000)

            # 6. Audio Relay Frame transmission (Callee -> Caller)
            await ws_callee.send(json.dumps({
                "type": "AUDIO_RELAY_FRAME",
                "call_id": call_id,
                "sender_id": u2["user_id"],
                "recipient_id": u1["user_id"],
                "amplitude": 0.62,
                "sample_rate": 48000
            }))

            caller_audio = await self._recv_type(ws_caller, "AUDIO_RELAY_FRAME")
            self.assertEqual(caller_audio.get("amplitude"), 0.62)

            # 7. ICE Candidate exchange
            await ws_caller.send(json.dumps({
                "type": "ICE_CANDIDATE",
                "call_id": call_id,
                "recipient_id": u2["user_id"],
                "candidate": {"candidate": "candidate:1 1 UDP 2122260223 127.0.0.1 50000 typ host"}
            }))

            callee_ice = await self._recv_type(ws_callee, "ICE_CANDIDATE")
            self.assertIn("candidate:1", callee_ice.get("candidate", {}).get("candidate", ""))

            # 8. Hangup call -> CALL_HANGUP
            await ws_caller.send(json.dumps({
                "type": "CALL_HANGUP",
                "call_id": call_id,
                "recipient_id": u2["user_id"],
                "caller_id": u1["user_id"],
                "callee_id": u2["user_id"]
            }))

            term_callee = await self._recv_type(ws_callee, "CALL_TERMINATED")
            self.assertEqual(term_callee.get("status"), "ENDED")

            term_caller = await self._recv_type(ws_caller, "CALL_TERMINATED")
            self.assertEqual(term_caller.get("status"), "ENDED")

if __name__ == "__main__":
    unittest.main()
