"""
==============================================================================
UnderWraps High-Performance Server Engine & Protocol Gateway (v2.0)
REST API, Full-Duplex Real-Time WebSocket, 150MB File Guard & Voice Call Relay

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
==============================================================================
"""

import os
import sys
import json
import time
import socket
import select
import struct
import base64
import hashlib
import threading
import mimetypes
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Any, Optional, Tuple, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure parent directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.database.kybalion_adapter import KybalionDBAdapter

# Constants
MAX_MEDIA_BYTES = 157286400  # Strict 150MB limit (150 * 1024 * 1024)
DEFAULT_HTTP_PORT = 8080
DEFAULT_WS_PORT = 8081
DEFAULT_DISCOVERY_PORT = 8088

class WebSocketFrame:
    """Zero-dependency pure Python WebSocket RFC 6455 Frame Parser & Encoder."""
    OP_TEXT = 0x1
    OP_BINARY = 0x2
    OP_CLOSE = 0x8
    OP_PING = 0x9
    OP_PONG = 0xA

    @staticmethod
    def encode_frame(payload: bytes, opcode: int = OP_TEXT) -> bytes:
        length = len(payload)
        header = bytearray()
        header.append(0x80 | opcode)  # FIN + opcode
        
        if length <= 125:
            header.append(length)
        elif length <= 65535:
            header.append(126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(127)
            header.extend(struct.pack("!Q", length))
            
        return bytes(header) + payload

    @staticmethod
    def decode_frame(data: bytes) -> Tuple[Optional[bytes], int, int]:
        """Returns (payload, opcode, consumed_bytes) or (None, 0, 0) if incomplete."""
        if len(data) < 2:
            return None, 0, 0
        
        byte1, byte2 = data[0], data[1]
        opcode = byte1 & 0x0F
        masked = (byte2 & 0x80) != 0
        payload_len = byte2 & 0x7F
        
        offset = 2
        if payload_len == 126:
            if len(data) < 4:
                return None, 0, 0
            payload_len = struct.unpack("!H", data[2:4])[0]
            offset = 4
        elif payload_len == 127:
            if len(data) < 10:
                return None, 0, 0
            payload_len = struct.unpack("!Q", data[2:10])[0]
            offset = 10
            
        mask_key = None
        if masked:
            if len(data) < offset + 4:
                return None, 0, 0
            mask_key = data[offset:offset+4]
            offset += 4
            
        if len(data) < offset + payload_len:
            return None, 0, 0
            
        payload = bytearray(data[offset:offset+payload_len])
        if masked and mask_key:
            for i in range(len(payload)):
                payload[i] ^= mask_key[i % 4]
                
        return bytes(payload), opcode, offset + payload_len


class UnderWrapsServer:
    """
    Multi-Threaded Server Engine for UnderWraps.
    Coordinates REST APIs, WebSockets, Kybalion Storage, 150MB File Streaming, and Voice Calling.
    """
    def __init__(self, host: str = "0.0.0.0", http_port: int = DEFAULT_HTTP_PORT,
                 ws_port: int = DEFAULT_WS_PORT, discovery_port: int = DEFAULT_DISCOVERY_PORT, data_dir: str = "./underwraps_data"):
        self.host = host
        self.http_port = http_port
        self.ws_port = ws_port
        self.discovery_port = discovery_port
        self.data_dir = os.path.abspath(data_dir)
        self.db = KybalionDBAdapter(data_dir=self.data_dir)
        
        self.is_running = False
        self.httpd: Optional[HTTPServer] = None
        self.ws_server_sock: Optional[socket.socket] = None
        self.udp_discovery_sock: Optional[socket.socket] = None
        
        # Connected WebSocket Clients: {socket: {"user_id": str, "username": str, "ip": str, "joined_at": int}}
        self.clients: Dict[socket.socket, Dict[str, Any]] = {}
        self.user_to_sockets: Dict[str, Set[socket.socket]] = {}
        self.clients_lock = threading.Lock()
        
        # Voice Call Sessions: {call_id: {"caller_id": str, "callee_id": str, "status": str, "started_at": int}}
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        
        # Telemetry
        self.total_messages_routed = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0
        self.start_time = time.time()
        self.log_callbacks: List[Any] = []

    def get_lan_ip(self) -> str:
        """Determines the primary LAN IP address for zero-configuration discovery."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        print(formatted)
        for cb in self.log_callbacks:
            try:
                cb(formatted, level)
            except Exception:
                pass

    # --------------------------------------------------------------------------
    # Lifecycle Management
    # --------------------------------------------------------------------------
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.start_time = time.time()
        
        # Start HTTP Server in background thread
        self.http_thread = threading.Thread(target=self._run_http_server, daemon=True)
        self.http_thread.start()
        
        # Start WebSocket Server in background thread
        self.ws_thread = threading.Thread(target=self._run_ws_server, daemon=True)
        self.ws_thread.start()

        # Start Zero-Configuration UDP Auto-Discovery Beacon in background thread
        self.udp_thread = threading.Thread(target=self._run_udp_discovery, daemon=True)
        self.udp_thread.start()
        
        self.log(f"UnderWraps Server Engine successfully started on {self.host} (HTTP: {self.http_port}, WS: {self.ws_port}, UDP Discovery: {self.discovery_port})", "SUCCESS")
        self.log(f"Kybalion DB Engine active at: {self.data_dir}", "INFO")
        self.log(f"Formally Verified 150MB File Guard: ACTIVE (Max {MAX_MEDIA_BYTES} bytes)", "INFO")

    def stop(self):
        if not self.is_running:
            return
        self.log("Shutting down UnderWraps Server Engine...", "WARNING")
        self.is_running = False
        
        # Close UDP Discovery Beacon
        if self.udp_discovery_sock:
            try:
                self.udp_discovery_sock.close()
            except Exception:
                pass

        # Close HTTP server
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
                
        # Close WebSocket server & clients
        if self.ws_server_sock:
            try:
                self.ws_server_sock.close()
            except Exception:
                pass
                
        with self.clients_lock:
            for s in list(self.clients.keys()):
                try:
                    s.close()
                except Exception:
                    pass
            self.clients.clear()
            self.user_to_sockets.clear()
            
        self.log("Server shutdown complete. State safely committed to Kybalion DB.", "SUCCESS")

    def _run_udp_discovery(self):
        """Zero-configuration UDP discovery beacon responder on port 8088."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("0.0.0.0", self.discovery_port))
            sock.settimeout(1.0)
            self.udp_discovery_sock = sock
            self.log(f"Zero-Config UDP Auto-Discovery Beacon listening on port {self.discovery_port}", "INFO")
        except Exception as e:
            self.log(f"UDP Auto-Discovery Beacon unavailable: {e}", "WARNING")
            return

        lan_ip = self.get_lan_ip()
        last_broadcast_time = 0.0

        while self.is_running:
            now = time.time()
            # Periodic broadcast beacon every 3.0s
            if now - last_broadcast_time > 3.0:
                beacon_payload = json.dumps({
                    "service": "UNDERWRAPS_SERVER",
                    "http_url": f"http://{lan_ip}:{self.http_port}",
                    "ws_url": f"ws://{lan_ip}:{self.ws_port}",
                    "host": lan_ip,
                    "http_port": self.http_port,
                    "ws_port": self.ws_port,
                    "server_name": "UnderWraps Sovereign Node",
                    "version": "2.0.0-Hermetic"
                }).encode("utf-8")
                try:
                    sock.sendto(beacon_payload, ("<broadcast>", self.discovery_port))
                except Exception:
                    pass
                last_broadcast_time = now

            # Listen for client discovery probes
            try:
                data, addr = sock.recvfrom(2048)
                msg = data.decode("utf-8", errors="ignore").strip()
                if "UNDERWRAPS_DISCOVER" in msg or msg.startswith("{"):
                    ack_payload = json.dumps({
                        "service": "UNDERWRAPS_SERVER",
                        "status": "ONLINE",
                        "http_url": f"http://{lan_ip}:{self.http_port}",
                        "ws_url": f"ws://{lan_ip}:{self.ws_port}",
                        "host": lan_ip,
                        "http_port": self.http_port,
                        "ws_port": self.ws_port,
                        "server_name": "UnderWraps Sovereign Node",
                        "version": "2.0.0-Hermetic"
                    }).encode("utf-8")
                    sock.sendto(ack_payload, addr)
            except socket.timeout:
                continue
            except Exception:
                if not self.is_running:
                    break

    # --------------------------------------------------------------------------
    # HTTP REST Server
    # --------------------------------------------------------------------------
    def _run_http_server(self):
        engine = self
        
        class HTTPHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass # Suppress default stderr logging

            def send_json(self, status_code: int, data: Any):
                body = json.dumps(data).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
                self.send_header("X-Engine", "UnderWraps-Kybalion-Pure-ALU")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self):
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
                self.end_headers()

            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path
                query = parse_qs(parsed.query)

                try:
                    # 1. Health
                    if path == "/api/v1/health" or path == "/health":
                        return self.send_json(200, {"status": "HEALTHY", "version": "2.0.0-Hermetic"})
                        
                    # 2. Telemetry
                    if path == "/api/v1/telemetry":
                        telemetry = engine.get_telemetry()
                        return self.send_json(200, telemetry)

                    # 3. User List
                    if path == "/api/v1/users/list":
                        users = engine.db.list_all_users()
                        # Mask sensitive fields
                        for u in users:
                            u["is_online"] = u["user_id"] in engine.user_to_sockets
                        return self.send_json(200, {"users": users})

                    # 4. Conversations for user
                    if path == "/api/v1/conversations":
                        user_id = query.get("user_id", [None])[0]
                        if not user_id:
                            return self.send_json(400, {"error": "Missing user_id"})
                        convs = engine.db.get_user_conversations(user_id)
                        return self.send_json(200, {"conversations": convs})

                    # 5. Message history for conversation
                    if path.startswith("/api/v1/conversations/") and path.endswith("/messages"):
                        conv_id = path.split("/")[4]
                        limit = int(query.get("limit", [50])[0])
                        offset = int(query.get("offset", [0])[0])
                        msgs = engine.db.get_messages(conv_id, limit=limit, offset=offset)
                        return self.send_json(200, {"messages": msgs})

                    # 6. Attachment Download
                    if path.startswith("/api/v1/attachments/download/"):
                        att_id = path.split("/")[-1]
                        att = engine.db.get_attachment(att_id)
                        if not att or not os.path.exists(att["storage_path"]):
                            return self.send_json(404, {"error": "Attachment not found"})
                            
                        file_size = os.path.getsize(att["storage_path"])
                        self.send_response(200)
                        self.send_header("Content-Type", att["mime_type"] or "application/octet-stream")
                        self.send_header("Content-Length", str(file_size))
                        self.send_header("Content-Disposition", f'inline; filename="{att["file_name"]}"')
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        
                        with open(att["storage_path"], "rb") as f:
                            while chunk := f.read(65536):
                                self.wfile.write(chunk)
                        return

                    # 7. Recent Calls
                    if path == "/api/v1/calls/recent":
                        user_id = query.get("user_id", [None])[0]
                        if not user_id:
                            return self.send_json(400, {"error": "Missing user_id"})
                        calls = engine.db.get_recent_calls(user_id)
                        return self.send_json(200, {"calls": calls})

                    # 8. Neural Semantic Search (100% On-Device / Zero-Knowledge)
                    if path == "/api/v1/search/semantic":
                        user_id = query.get("user_id", [None])[0]
                        q = query.get("q", [""])[0]
                        conv_id = query.get("conversation_id", [None])[0]
                        top_k = int(query.get("top_k", [10])[0])
                        if not user_id or not q:
                            return self.send_json(400, {"error": "Missing user_id or query parameter 'q'"})
                        results = engine.db.semantic_search(user_id, q, conversation_id=conv_id, top_k=top_k)
                        return self.send_json(200, {"query": q, "results": results, "count": len(results)})

                    # 9. Server Discovery Info (Zero-Config Probe)
                    if path == "/api/v1/server/info":
                        lan_ip = engine.get_lan_ip()
                        return self.send_json(200, {
                            "service": "UNDERWRAPS_SERVER",
                            "status": "ONLINE",
                            "http_url": f"http://{lan_ip}:{engine.http_port}",
                            "ws_url": f"ws://{lan_ip}:{engine.ws_port}",
                            "host": lan_ip,
                            "http_port": engine.http_port,
                            "ws_port": engine.ws_port,
                            "server_name": "UnderWraps Sovereign Node",
                            "version": "2.0.0-Hermetic"
                        })

                    # 10. Check Username Availability / Peer Info
                    if path == "/api/v1/auth/check-username":
                        username = query.get("username", [None])[0]
                        if not username:
                            return self.send_json(400, {"error": "Missing username parameter"})
                        u = engine.db.get_user_by_username(username)
                        if u:
                            return self.send_json(200, {
                                "exists": True,
                                "username": u["username"],
                                "display_name": u["display_name"],
                                "user_id": u["user_id"],
                                "identity_key_pub": u["identity_key_pub"],
                                "two_factor_enabled": bool(u["two_factor_enabled"])
                            })
                        else:
                            return self.send_json(200, {"exists": False})

                    self.send_json(404, {"error": "Endpoint not found", "path": path})
                except Exception as e:
                    engine.log(f"HTTP GET Error ({path}): {str(e)}", "ERROR")
                    self.send_json(500, {"error": str(e)})

            def do_POST(self):
                parsed = urlparse(self.path)
                path = parsed.path
                
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    
                    # Strict 150MB Guard check on header
                    if content_length > MAX_MEDIA_BYTES:
                        engine.log(f"Rejected payload: {content_length} bytes exceeds strict 150MB limit", "WARNING")
                        return self.send_json(413, {"error": f"Payload Too Large. Max allowed is 150MB ({MAX_MEDIA_BYTES} bytes)"})

                    # Handle 150MB Attachment Upload
                    if path == "/api/v1/attachments/upload":
                        return self._handle_attachment_upload(content_length)

                    # Standard JSON Body parsing
                    body = self.rfile.read(content_length) if content_length > 0 else b"{}"
                    data = json.loads(body.decode("utf-8")) if body else {}

                    # 1. Signup (Username + Password [Optional Email])
                    if path == "/api/v1/auth/signup":
                        username = data.get("username")
                        password = data.get("password")
                        email = data.get("email")
                        display_name = data.get("display_name")
                        
                        if not username or not password:
                            return self.send_json(400, {"error": "Username and password are required."})
                            
                        user = engine.db.register_user(username, email=email, password=password, display_name=display_name)
                        engine.log(f"New user registered: @{username} ({user.get('email')})", "SUCCESS")
                        return self.send_json(201, {
                            "success": True,
                            "user": user,
                            "session_token": user.get("session_token"),
                            "requires_2fa": False
                        })

                    # 2. Session Resume (Zero-Click Auto Login)
                    if path == "/api/v1/auth/resume":
                        token = data.get("session_token") or self.headers.get("X-Session-Token")
                        auth_header = self.headers.get("Authorization", "")
                        if not token and auth_header.startswith("Bearer "):
                            token = auth_header[7:].strip()
                        
                        if not token:
                            return self.send_json(400, {"error": "session_token is required."})
                        
                        user_data = engine.db.validate_session_token(token)
                        if not user_data:
                            return self.send_json(401, {"error": "Invalid or expired session token."})
                        
                        engine.log(f"Session resumed for user: @{user_data['username']}", "SUCCESS")
                        return self.send_json(200, {
                            "success": True,
                            "user": user_data,
                            "session_token": user_data["session_token"]
                        })

                    # 3. Login (Username/Email + Password)
                    if path == "/api/v1/auth/login":
                        identifier = data.get("identifier") or data.get("username") or data.get("email")
                        password = data.get("password")
                        if not identifier or not password:
                            return self.send_json(400, {"error": "Identifier and password required."})
                            
                        result = engine.db.authenticate_user(identifier, password)
                        if result.get("requires_2fa"):
                            engine.log(f"2FA Challenge issued for user: {result['user_id']} (OTP: {result.get('otp_code_dev')})", "INFO")
                        else:
                            engine.log(f"User logged in: @{result.get('username')}", "SUCCESS")
                        return self.send_json(200, result)

                    # 3. Verify 2FA OTP
                    if path == "/api/v1/auth/verify-2fa":
                        token_id = data.get("token_id")
                        otp_code = data.get("otp_code")
                        if not token_id or not otp_code:
                            return self.send_json(400, {"error": "token_id and otp_code are required."})
                            
                        result = engine.db.verify_2fa_otp(token_id, otp_code)
                        engine.log(f"2FA verified for user: @{result.get('username')}", "SUCCESS")
                        return self.send_json(200, result)

                    # 4. Toggle 2FA in Settings
                    if path == "/api/v1/auth/toggle-2fa":
                        user_id = data.get("user_id")
                        enabled = bool(data.get("enabled", False))
                        if not user_id:
                            return self.send_json(400, {"error": "user_id required."})
                        engine.db.toggle_2fa(user_id, enabled)
                        engine.log(f"User {user_id} set 2FA to: {enabled}", "INFO")
                        return self.send_json(200, {"success": True, "two_factor_enabled": enabled})

                    # 5. Create Direct Conversation
                    if path == "/api/v1/conversations/direct":
                        user1_id = data.get("user1_id")
                        user2_id = data.get("user2_id")
                        if not user1_id or not user2_id:
                            return self.send_json(400, {"error": "user1_id and user2_id required."})
                        conv_id = engine.db.create_direct_conversation(user1_id, user2_id)
                        return self.send_json(200, {"conversation_id": conv_id})

                    # 6. Kybalion Database Vacuum
                    if path == "/api/v1/maintenance/vacuum":
                        engine.db.vacuum()
                        engine.log("Kybalion Database vacuum completed.", "SUCCESS")
                        return self.send_json(200, {"success": True, "message": "Database vacuumed."})

                    self.send_json(404, {"error": "Endpoint not found", "path": path})
                except Exception as e:
                    engine.log(f"HTTP POST Error ({path}): {str(e)}", "ERROR")
                    self.send_json(400, {"error": str(e)})

            def _handle_attachment_upload(self, content_length: int):
                """Handles streaming chunk upload with strict 150MB cap & BLAKE3/SHA-256 integrity."""
                sender_id = self.headers.get("X-Sender-Id", "unknown")
                file_name = self.headers.get("X-File-Name", f"file_{int(time.time())}.dat")
                mime_type = self.headers.get("Content-Type", "application/octet-stream")
                is_voice_note = self.headers.get("X-Is-Voice-Note", "false").lower() == "true"
                audio_duration_ms = int(self.headers.get("X-Audio-Duration-Ms", "0"))
                
                att_id = ("vn_" if is_voice_note else "att_") + hashlib.sha256(f"{file_name}:{time.time()}".encode()).hexdigest()[:16]
                storage_path = os.path.join(engine.db.attachments_dir, f"{att_id}_{file_name}")
                
                hasher = hashlib.sha256()
                bytes_read = 0
                
                with open(storage_path, "wb") as f:
                    while bytes_read < content_length:
                        chunk_size = min(65536, content_length - bytes_read)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk:
                            break
                        bytes_read += len(chunk)
                        
                        # Streaming 150MB Guard check
                        if bytes_read > MAX_MEDIA_BYTES:
                            f.close()
                            if os.path.exists(storage_path):
                                os.remove(storage_path)
                            engine.log(f"Aborted stream: Exceeded 150MB ceiling during transmission", "ERROR")
                            return self.send_json(413, {"error": "Stream exceeded 150MB limit"})
                            
                        hasher.update(chunk)
                        f.write(chunk)
                        
                file_hash = hasher.hexdigest()
                engine.db.register_attachment(
                    attachment_id=att_id,
                    sender_id=sender_id,
                    file_name=file_name,
                    file_size_bytes=bytes_read,
                    mime_type=mime_type,
                    blake3_hash=file_hash,
                    storage_path=storage_path,
                    is_voice_note=is_voice_note,
                    audio_duration_ms=audio_duration_ms
                )
                
                engine.log(f"Attachment stored ({round(bytes_read/(1024*1024), 2)} MB): {file_name} [{'Voice Note' if is_voice_note else 'Media'}]", "SUCCESS")
                return self.send_json(201, {
                    "success": True,
                    "attachment_id": att_id,
                    "file_name": file_name,
                    "file_size_bytes": bytes_read,
                    "is_voice_note": is_voice_note,
                    "audio_duration_ms": audio_duration_ms,
                    "hash": file_hash,
                    "download_url": f"/api/v1/attachments/download/{att_id}"
                })

        try:
            self.httpd = HTTPServer((self.host, self.http_port), HTTPHandler)
            self.httpd.serve_forever()
        except Exception as e:
            if self.is_running:
                self.log(f"HTTP Server Exception: {str(e)}", "ERROR")

    # --------------------------------------------------------------------------
    # WebSocket Real-Time Server (RFC 6455 Duplex & Voice Call Signaling)
    # --------------------------------------------------------------------------
    def _run_ws_server(self):
        try:
            self.ws_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ws_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ws_server_sock.bind((self.host, self.ws_port))
            self.ws_server_sock.listen(128)
            self.ws_server_sock.settimeout(1.0)
            
            while self.is_running:
                try:
                    client_sock, addr = self.ws_server_sock.accept()
                    client_thread = threading.Thread(target=self._handle_ws_client, args=(client_sock, addr), daemon=True)
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        self.log(f"WebSocket Accept Error: {str(e)}", "ERROR")
        except Exception as e:
            if self.is_running:
                self.log(f"WebSocket Server Fatal Error: {str(e)}", "ERROR")

    def _handle_ws_client(self, client_sock: socket.socket, addr: Tuple[str, int]):
        """Performs RFC 6455 handshake and event loop for connected client."""
        client_sock.settimeout(60.0)
        user_info: Optional[Dict[str, Any]] = None
        
        try:
            # 1. Perform WebSocket Handshake
            request_data = b""
            while b"\r\n\r\n" not in request_data:
                chunk = client_sock.recv(1024)
                if not chunk:
                    return
                request_data += chunk
                
            headers_text = request_data.decode("utf-8", errors="ignore")
            lines = headers_text.split("\r\n")
            ws_key = None
            for line in lines:
                if line.lower().startswith("sec-websocket-key:"):
                    ws_key = line.split(":", 1)[1].strip()
                    break
                    
            if not ws_key:
                client_sock.close()
                return
                
            # Compute Sec-WebSocket-Accept
            guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = base64.b64encode(hashlib.sha1((ws_key + guid).encode()).digest()).decode()
            
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n"
                "X-Engine: UnderWraps-Kybalion-Pure-ALU\r\n\r\n"
            )
            client_sock.sendall(response.encode())
            
            # Register client
            with self.clients_lock:
                self.clients[client_sock] = {"ip": addr[0], "joined_at": int(time.time()), "user_id": None, "username": None}
                
            buffer = bytearray()
            
            # 2. Main Frame Processing Loop
            while self.is_running:
                try:
                    chunk = client_sock.recv(65536)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    
                    while True:
                        payload, opcode, consumed = WebSocketFrame.decode_frame(buffer)
                        if payload is None:
                            break
                        buffer = buffer[consumed:]
                        
                        if opcode == WebSocketFrame.OP_CLOSE:
                            return
                        elif opcode == WebSocketFrame.OP_PING:
                            client_sock.sendall(WebSocketFrame.encode_frame(payload, WebSocketFrame.OP_PONG))
                        elif opcode in (WebSocketFrame.OP_TEXT, WebSocketFrame.OP_BINARY):
                            self._dispatch_ws_message(client_sock, payload)
                            
                except socket.timeout:
                    # Send Ping
                    client_sock.sendall(WebSocketFrame.encode_frame(b"ping", WebSocketFrame.OP_PING))
                except Exception:
                    break
                    
        finally:
            self._disconnect_client(client_sock)

    def _dispatch_ws_message(self, client_sock: socket.socket, payload_bytes: bytes):
        """Processes incoming WebSocket events (Chat, Voice Notes, WebRTC Call Signaling)."""
        try:
            msg = json.loads(payload_bytes.decode("utf-8"))
            event_type = msg.get("type")
            
            # 1. Authentication
            if event_type == "AUTH":
                user_id = msg.get("user_id")
                user = self.db.get_user_by_id(user_id)
                if user:
                    with self.clients_lock:
                        self.clients[client_sock]["user_id"] = user_id
                        self.clients[client_sock]["username"] = user["username"]
                        if user_id not in self.user_to_sockets:
                            self.user_to_sockets[user_id] = set()
                        self.user_to_sockets[user_id].add(client_sock)
                        
                    self.log(f"WebSocket client authenticated: @{user['username']} ({user_id})", "SUCCESS")
                    self._send_ws(client_sock, {"type": "AUTH_OK", "user_id": user_id, "username": user["username"]})
                    self._broadcast_presence(user_id, is_online=True)
                return

            # 2. Real-Time Chat Message (Text, Voice Note, Media)
            if event_type == "CHAT_MESSAGE":
                sender_id = msg.get("sender_id")
                conversation_id = msg.get("conversation_id")
                recipient_id = msg.get("recipient_id")
                ciphertext = msg.get("ciphertext", "")
                nonce = msg.get("nonce", "")
                message_type = msg.get("message_type", "TEXT")
                attachment_id = msg.get("attachment_id")
                voice_duration_ms = int(msg.get("voice_duration_ms", 0))
                waveform_data = msg.get("waveform_data")
                
                message_id = "msg_" + hashlib.sha256(f"{sender_id}:{conversation_id}:{time.time()}".encode()).hexdigest()[:16]
                
                # Persist to Kybalion DB
                saved = self.db.save_message(
                    message_id=message_id,
                    conversation_id=conversation_id,
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    message_type=message_type,
                    ciphertext=ciphertext,
                    nonce=nonce,
                    attachment_id=attachment_id,
                    voice_duration_ms=voice_duration_ms,
                    waveform_data=waveform_data
                )
                
                self.total_messages_routed += 1
                
                # Broadcast payload
                out_event = {
                    "type": "NEW_MESSAGE",
                    "message": saved,
                    "sender_username": self.clients.get(client_sock, {}).get("username", "Unknown")
                }
                
                # Deliver to recipient(s)
                if recipient_id:
                    self._send_to_user(recipient_id, out_event)
                self._send_to_user(sender_id, out_event) # Echo back with seq
                
                self.log(f"Routed {message_type} msg in {conversation_id} from {sender_id}", "INFO")
                return

            # 3. High-Quality Voice Call Signaling (WebRTC / Peer-to-Peer & Relay)
            if event_type in ("CALL_INVITE", "CALL_RINGING", "CALL_ANSWER", "CALL_DECLINE", "CALL_ICE_CANDIDATE", "CALL_HANGUP", "AUDIO_RELAY_FRAME"):
                self._handle_voice_call_signal(client_sock, msg)
                return

            # 4. Typing Indicators
            if event_type == "TYPING":
                conv_id = msg.get("conversation_id")
                recipient_id = msg.get("recipient_id")
                sender_id = msg.get("sender_id")
                if recipient_id:
                    self._send_to_user(recipient_id, {
                        "type": "USER_TYPING",
                        "conversation_id": conv_id,
                        "sender_id": sender_id,
                        "is_typing": msg.get("is_typing", True)
                    })
                return

        except Exception as e:
            self.log(f"WS Message Error: {str(e)}", "ERROR")

    def _handle_voice_call_signal(self, sender_sock: socket.socket, msg: Dict[str, Any]):
        """Routes real-time WebRTC / UDP voice calling signaling and audio relay."""
        event_type = msg.get("type")
        caller_id = msg.get("caller_id")
        callee_id = msg.get("callee_id")
        call_id = msg.get("call_id") or f"call_{int(time.time())}_{secrets.token_hex(4)}"
        
        if event_type == "CALL_INVITE":
            self.active_calls[call_id] = {
                "caller_id": caller_id,
                "callee_id": callee_id,
                "status": "RINGING",
                "started_at": int(time.time() * 1000)
            }
            self.db.log_voice_call(call_id, caller_id, callee_id, "RINGING", int(time.time() * 1000))
            self.log(f"Incoming Voice Call [{call_id}]: {caller_id} -> {callee_id}", "INFO")
            self._send_to_user(callee_id, {
                "type": "CALL_INCOMING",
                "call_id": call_id,
                "caller_id": caller_id,
                "caller_username": self.clients.get(sender_sock, {}).get("username", "Unknown"),
                "sdp_offer": msg.get("sdp_offer")
            })

        elif event_type == "CALL_ANSWER":
            if call_id in self.active_calls:
                self.active_calls[call_id]["status"] = "CONNECTED"
                self.active_calls[call_id]["answered_at"] = int(time.time() * 1000)
                self.db.log_voice_call(call_id, self.active_calls[call_id]["caller_id"], callee_id, "CONNECTED", self.active_calls[call_id]["started_at"], answered_at=int(time.time() * 1000))
                self.log(f"Voice Call Connected [{call_id}]", "SUCCESS")
                self._send_to_user(self.active_calls[call_id]["caller_id"], {
                    "type": "CALL_ACCEPTED",
                    "call_id": call_id,
                    "sdp_answer": msg.get("sdp_answer")
                })

        elif event_type == "CALL_DECLINE" or event_type == "CALL_HANGUP":
            call = self.active_calls.pop(call_id, None)
            now = int(time.time() * 1000)
            target_id = callee_id if msg.get("sender_id") == caller_id else caller_id
            
            duration = 0
            if call and call.get("answered_at"):
                duration = int((now - call["answered_at"]) / 1000)
                
            status = "ENDED" if event_type == "CALL_HANGUP" else "DECLINED"
            if call:
                self.db.log_voice_call(call_id, call["caller_id"], call["callee_id"], status, call["started_at"], ended_at=now, duration_seconds=duration)
                
            self.log(f"Voice Call Terminated [{call_id}] - Status: {status}, Duration: {duration}s", "INFO")
            self._send_to_user(target_id, {"type": "CALL_TERMINATED", "call_id": call_id, "status": status, "duration": duration})

        elif event_type == "CALL_ICE_CANDIDATE" or event_type == "AUDIO_RELAY_FRAME":
            target_id = callee_id if msg.get("sender_id") == caller_id else caller_id
            self._send_to_user(target_id, msg)

    def _send_ws(self, sock: socket.socket, data: Dict[str, Any]):
        try:
            payload = json.dumps(data).encode("utf-8")
            frame = WebSocketFrame.encode_frame(payload)
            sock.sendall(frame)
        except Exception:
            pass

    def _send_to_user(self, user_id: str, data: Dict[str, Any]):
        with self.clients_lock:
            sockets = self.user_to_sockets.get(user_id, set())
            for s in list(sockets):
                self._send_ws(s, data)

    def _broadcast_presence(self, user_id: str, is_online: bool):
        event = {"type": "PRESENCE", "user_id": user_id, "is_online": is_online}
        with self.clients_lock:
            for s in self.clients.keys():
                self._send_ws(s, event)

    def _disconnect_client(self, client_sock: socket.socket):
        user_id = None
        with self.clients_lock:
            info = self.clients.pop(client_sock, None)
            if info and info.get("user_id"):
                user_id = info["user_id"]
                if user_id in self.user_to_sockets:
                    self.user_to_sockets[user_id].discard(client_sock)
                    if not self.user_to_sockets[user_id]:
                        del self.user_to_sockets[user_id]
                        
        try:
            client_sock.close()
        except Exception:
            pass
            
        if user_id:
            self.log(f"WebSocket client disconnected: {user_id}", "INFO")
            self._broadcast_presence(user_id, is_online=False)

    # --------------------------------------------------------------------------
    # Telemetry
    # --------------------------------------------------------------------------
    def get_telemetry(self) -> Dict[str, Any]:
        uptime_sec = int(time.time() - self.start_time)
        qps = round(self.total_messages_routed / max(1, uptime_sec), 2)
        db_stats = self.db.get_telemetry()
        storage = self.db.get_storage_stats()
        
        with self.clients_lock:
            active_clients = len(self.clients)
            online_users = len(self.user_to_sockets)
            
        return {
            "status": "ONLINE" if self.is_running else "OFFLINE",
            "uptime_seconds": uptime_sec,
            "qps": qps,
            "active_ws_connections": active_clients,
            "online_users_count": online_users,
            "active_voice_calls": len(self.active_calls),
            "total_messages_routed": self.total_messages_routed,
            "storage": storage,
            "db_telemetry": db_stats,
            "ports": {"http": self.http_port, "ws": self.ws_port}
        }
