package com.example.underwraps

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.NetworkInterface
import java.net.Socket
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {

    companion object {
        private const val TAG = "UnderWrapsNative"
        private const val PERMISSION_REQUEST_CODE = 1001
        private const val DEFAULT_SERVER_HTTP = "http://192.168.50.179:8080"
        private const val DEFAULT_SERVER_WS = "ws://192.168.50.179:8081"
    }

    private lateinit var webView: WebView

    @Volatile
    var discoveredServerHttpUrl: String = DEFAULT_SERVER_HTTP
        private set

    @Volatile
    var discoveredServerWsUrl: String = DEFAULT_SERVER_WS
        private set

    @Volatile
    var isDiscoveryComplete: Boolean = false
        private set

    private val discoveryExecutor = Executors.newFixedThreadPool(8)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request runtime permissions
        checkAndRequestPermissions()

        // Enable Chromium DevTools debugging
        WebView.setWebContentsDebuggingEnabled(true)

        webView = WebView(this)
        setContentView(webView)

        setupWebView()

        // Launch autonomous 4-tier server discovery immediately
        startAutonomousDiscovery()

        webView.loadUrl("file:///android_asset/web/index.html")
    }

    private fun setupWebView() {
        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.mediaPlaybackRequiresUserGesture = false
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

        // Register Native UnderWraps Bridge
        webView.addJavascriptInterface(UnderWrapsBridge(), "UnderWrapsNative")

        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null)
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                notifyWebviewOfServer(discoveredServerHttpUrl, discoveredServerWsUrl)
            }
        }
        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                runOnUiThread {
                    request.grant(request.resources)
                }
            }
        }
    }

    inner class UnderWrapsBridge {
        @JavascriptInterface
        fun getDiscoveredServerUrl(): String {
            return discoveredServerHttpUrl
        }

        @JavascriptInterface
        fun getDiscoveredWsUrl(): String {
            return discoveredServerWsUrl
        }

        @JavascriptInterface
        fun isDiscoveryDone(): Boolean {
            return isDiscoveryComplete
        }

        @JavascriptInterface
        fun probeServer(urlStr: String, timeoutMs: Int): Boolean {
            return checkHttpHealth(urlStr, timeoutMs)
        }

        @JavascriptInterface
        fun log(msg: String) {
            Log.d(TAG, "[JS] $msg")
        }
    }

    private fun notifyWebviewOfServer(httpUrl: String, wsUrl: String) {
        runOnUiThread {
            if (::webView.isInitialized) {
                val script = "(function() { " +
                        "if (typeof window.__onServerDiscovered === 'function') { " +
                        "  window.__onServerDiscovered('$httpUrl', '$wsUrl'); " +
                        "} " +
                        "})()"
                webView.evaluateJavascript(script, null)
            }
        }
    }

    private fun startAutonomousDiscovery() {
        discoveryExecutor.execute {
            Log.i(TAG, "Starting autonomous 4-tier network server discovery...")

            // Tier 1: Probe direct candidates (Target Server, Host loopback, Gateway)
            val candidates = mutableListOf(
                "http://192.168.50.179:8080",
                "http://10.0.2.2:8080"
            )

            // Add gateway candidate if accessible
            getGatewayIp()?.let { gw ->
                candidates.add("http://$gw:8080")
            }

            for (cand in candidates) {
                if (checkHttpHealth(cand, 400)) {
                    val ws = deriveWsUrl(cand)
                    discoveredServerHttpUrl = cand
                    discoveredServerWsUrl = ws
                    isDiscoveryComplete = true
                    Log.i(TAG, "Tier 1: Discovered UnderWraps server at $cand")
                    notifyWebviewOfServer(cand, ws)
                    return@execute
                }
            }

            // Tier 2: UDP Broadcast Probe on Port 8088
            val udpResult = probeUdpBroadcast(1200)
            if (udpResult != null) {
                discoveredServerHttpUrl = udpResult.first
                discoveredServerWsUrl = udpResult.second
                isDiscoveryComplete = true
                Log.i(TAG, "Tier 2: UDP broadcast discovered server at ${udpResult.first}")
                notifyWebviewOfServer(udpResult.first, udpResult.second)
                return@execute
            }

            // Tier 3: Parallel Subnet Socket Sweep
            val subnet = getLocalSubnetPrefix()
            if (subnet != null) {
                Log.i(TAG, "Tier 3: Sweeping subnet $subnet.0/24 on port 8080...")
                val sweepPool = Executors.newFixedThreadPool(32)
                var found = false

                for (i in 1..254) {
                    val targetIp = "$subnet.$i"
                    sweepPool.execute {
                        if (found) return@execute
                        try {
                            val sock = Socket()
                            sock.connect(InetSocketAddress(targetIp, 8080), 250)
                            sock.close()
                            val testUrl = "http://$targetIp:8080"
                            if (checkHttpHealth(testUrl, 400)) {
                                found = true
                                val ws = deriveWsUrl(testUrl)
                                discoveredServerHttpUrl = testUrl
                                discoveredServerWsUrl = ws
                                isDiscoveryComplete = true
                                Log.i(TAG, "Tier 3: Subnet sweep discovered server at $testUrl")
                                notifyWebviewOfServer(testUrl, ws)
                            }
                        } catch (ignored: Exception) {}
                    }
                }

                sweepPool.shutdown()
                try {
                    sweepPool.awaitTermination(3, TimeUnit.SECONDS)
                } catch (ignored: Exception) {}

                if (found) return@execute
            }

            // Tier 4: Fallback to default
            Log.w(TAG, "Tier 4: Using default fallback server at $DEFAULT_SERVER_HTTP")
            discoveredServerHttpUrl = DEFAULT_SERVER_HTTP
            discoveredServerWsUrl = DEFAULT_SERVER_WS
            isDiscoveryComplete = true
            notifyWebviewOfServer(DEFAULT_SERVER_HTTP, DEFAULT_SERVER_WS)
        }
    }

    private fun checkHttpHealth(baseHttpUrl: String, timeoutMs: Int): Boolean {
        return try {
            val url = URL("$baseHttpUrl/api/v1/health")
            val conn = url.openConnection() as HttpURLConnection
            conn.connectTimeout = timeoutMs
            conn.readTimeout = timeoutMs
            conn.requestMethod = "GET"
            conn.instanceFollowRedirects = false
            val code = conn.responseCode
            conn.disconnect()
            code == 200
        } catch (e: Exception) {
            false
        }
    }

    private fun probeUdpBroadcast(timeoutMs: Int): Pair<String, String>? {
        var multicastLock: WifiManager.MulticastLock? = null
        return try {
            val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
            multicastLock = wifi?.createMulticastLock("UnderWrapsDiscovery")
            multicastLock?.setReferenceCounted(true)
            multicastLock?.acquire()

            val socket = DatagramSocket()
            socket.broadcast = true
            socket.soTimeout = timeoutMs
            val msg = "UNDERWRAPS_DISCOVER_PROBE".toByteArray(Charsets.UTF_8)

            val broadcastTargets = mutableListOf(
                InetAddress.getByName("255.255.255.255")
            )
            getLocalSubnetPrefix()?.let { sub ->
                try {
                    broadcastTargets.add(InetAddress.getByName("$sub.255"))
                } catch (ignored: Exception) {}
            }

            for (target in broadcastTargets) {
                try {
                    val packet = DatagramPacket(msg, msg.size, target, 8088)
                    socket.send(packet)
                } catch (ignored: Exception) {}
            }

            val buf = ByteArray(2048)
            val recvPacket = DatagramPacket(buf, buf.size)
            socket.receive(recvPacket)
            val reply = String(recvPacket.data, 0, recvPacket.length, Charsets.UTF_8)
            socket.close()

            val json = JSONObject(reply)
            val senderIp = recvPacket.address.hostAddress ?: "192.168.50.179"
            val httpUrl = json.optString("http_url", "http://$senderIp:8080")
            val wsHost = json.optString("host", senderIp)
            val wsPort = json.optInt("ws_port", 8081)
            Pair(httpUrl, "ws://$wsHost:$wsPort")
        } catch (e: Exception) {
            null
        } finally {
            try {
                if (multicastLock?.isHeld == true) {
                    multicastLock.release()
                }
            } catch (ignored: Exception) {}
        }
    }

    private fun deriveWsUrl(httpUrl: String): String {
        return try {
            val uri = java.net.URI(httpUrl)
            val host = uri.host ?: "192.168.50.179"
            "ws://$host:8081"
        } catch (e: Exception) {
            DEFAULT_SERVER_WS
        }
    }

    private fun getGatewayIp(): String? {
        return try {
            val socket = Socket()
            socket.connect(InetSocketAddress("8.8.8.8", 53), 200)
            val localIp = socket.localAddress.hostAddress
            socket.close()
            if (localIp != null && localIp.contains(".")) {
                val parts = localIp.split(".")
                "${parts[0]}.${parts[1]}.${parts[2]}.1"
            } else null
        } catch (e: Exception) {
            null
        }
    }

    private fun getLocalSubnetPrefix(): String? {
        return try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (iface.isLoopback || !iface.isUp) continue
                val addrs = iface.inetAddresses
                while (addrs.hasMoreElements()) {
                    val addr = addrs.nextElement()
                    if (!addr.isLoopbackAddress && addr.hostAddress?.contains(":") == false) {
                        val ip = addr.hostAddress ?: continue
                        val parts = ip.split(".")
                        if (parts.size == 4) {
                            return "${parts[0]}.${parts[1]}.${parts[2]}"
                        }
                    }
                }
            }
            null
        } catch (e: Exception) {
            null
        }
    }

    private fun checkAndRequestPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.MODIFY_AUDIO_SETTINGS
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.READ_MEDIA_AUDIO)
            permissions.add(Manifest.permission.READ_MEDIA_IMAGES)
            permissions.add(Manifest.permission.READ_MEDIA_VIDEO)
        } else {
            permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
        }

        val needed = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (needed.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, needed.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        webView.evaluateJavascript(
            "(function() { " +
            "  var layout = document.getElementById('messenger-layout') || document.querySelector('.messenger-layout'); " +
            "  if (layout && layout.classList.contains('view-chat')) { " +
            "    if (typeof returnToInbox === 'function') { returnToInbox(); return true; } " +
            "  } " +
            "  return false; " +
            "})()"
        ) { result ->
            if (result != "true") {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    super.onBackPressed()
                }
            }
        }
    }

    override fun onDestroy() {
        discoveryExecutor.shutdownNow()
        super.onDestroy()
    }
}

