package com.pcshieldstream

import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.lifecycleScope
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.PlaybackException
import androidx.media3.datasource.DefaultDataSource
import androidx.media3.datasource.DefaultHttpDataSource
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import androidx.media3.common.TrackSelectionParameters
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import androidx.media3.ui.TrackSelectionDialogBuilder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import org.json.JSONArray
import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL
import java.util.Locale

private val Bg = Color(0xFF080B12)
private val Panel = Color(0xFF151B28)
private val Accent = Color(0xFF78D7FF)
private val Muted = Color(0xFF9AA8BD)

data class MediaEntry(val name: String, val path: String, val type: String, val size: Long = 0, val root: Boolean = false)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = android.graphics.Color.rgb(8, 11, 18)
        window.navigationBarColor = android.graphics.Color.rgb(8, 11, 18)
        setContent { ShieldApp() }
    }
}

@Composable
@OptIn(UnstableApi::class)
private fun ShieldApp() {
    val context = LocalContext.current
    val activity = context as ComponentActivity
    var server by remember { mutableStateOf("http://192.168.1.20:8787") }
    var serverInput by remember { mutableStateOf(server) }
    var connected by remember { mutableStateOf(false) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var currentPath by remember { mutableStateOf("") }
    var entries by remember { mutableStateOf<List<MediaEntry>>(emptyList()) }
    var playing by remember { mutableStateOf<MediaEntry?>(null) }
    var player by remember { mutableStateOf<ExoPlayer?>(null) }
    var playerView by remember { mutableStateOf<PlayerView?>(null) }
    var savedPosition by remember { mutableLongStateOf(0L) }
    var playbackError by remember { mutableStateOf("") }
    var playbackStatus by remember { mutableStateOf("Đang khởi tạo trình phát…") }

    fun request(path: String) {
        loading = true; error = ""
        activity.lifecycleScope.launch {
            try {
                val list = withContext(Dispatchers.IO) { Api.list(server, path) }
                currentPath = path; entries = list; connected = true
            } catch (e: Exception) { error = "Không kết nối được: ${e.message ?: "kiểm tra IP và mạng LAN"}"; connected = false }
            loading = false
        }
    }

    fun play(entry: MediaEntry) {
        playbackError = ""
        playbackStatus = "Đang kết nối luồng video…"
        playing = entry
        activity.lifecycleScope.launch {
            try {
                val position = withContext(Dispatchers.IO) { Api.progress(server, entry.path) }
                savedPosition = position
                val httpFactory = DefaultHttpDataSource.Factory()
                    .setUserAgent("PCShieldStream/1.1 (Android TV)")
                    .setConnectTimeoutMs(15_000)
                    .setReadTimeoutMs(30_000)
                    .setAllowCrossProtocolRedirects(true)
                val dataSourceFactory = DefaultDataSource.Factory(context, httpFactory)
                val exo = ExoPlayer.Builder(context)
                    .setMediaSourceFactory(DefaultMediaSourceFactory(dataSourceFactory))
                    .build()
                exo.addListener(object : Player.Listener {
                    override fun onPlaybackStateChanged(state: Int) {
                        playbackStatus = when (state) {
                            Player.STATE_BUFFERING -> "Đang tải video…"
                            Player.STATE_READY -> "Đang phát"
                            Player.STATE_ENDED -> "Đã phát hết"
                            else -> "Đang chờ trình phát…"
                        }
                    }
                    override fun onPlayerError(exception: PlaybackException) {
                        val cause = exception.cause?.message?.takeIf { it.isNotBlank() }
                        playbackError = buildString {
                            append("Không phát được video. ")
                            append(exception.errorCodeName)
                            append(": ")
                            append(cause ?: exception.message ?: "Lỗi không xác định")
                        }
                        playbackStatus = "Lỗi trình phát"
                        android.util.Log.e("PCShieldStream", "ExoPlayer playback error", exception)
                    }
                })
                val itemBuilder = MediaItem.Builder().setUri(Api.url(server, "/stream", entry.path)).setMediaId(entry.path)
                // Attach the first matching sidecar subtitle automatically; users can toggle tracks in the player.
                val subtitle = withContext(Dispatchers.IO) { Api.subtitles(server, entry.path).firstOrNull() }
                if (subtitle != null) {
                    val ext = subtitle.name.substringAfterLast('.', "srt").lowercase(Locale.ROOT)
                    val mime = when (ext) { "ass", "ssa" -> "text/x-ssa"; "vtt" -> "text/vtt"; else -> "application/x-subrip" }
                    itemBuilder.setSubtitleConfigurations(listOf(MediaItem.SubtitleConfiguration.Builder(Uri.parse(Api.url(server, "/subtitle", subtitle.path))).setMimeType(mime).setLanguage("und").setSelectionFlags(C.SELECTION_FLAG_DEFAULT).build()))
                }
                player?.release()
                player = exo
                exo.setMediaItem(itemBuilder.build(), position)
                exo.prepare()
                exo.playWhenReady = true
            } catch (e: Exception) {
                playbackError = "Không mở được phim: ${e.message ?: e.javaClass.simpleName}"
                android.util.Log.e("PCShieldStream", "Failed to initialize player", e)
                error = playbackError
                playing = null
            }
        }
    }

    LaunchedEffect(playing, player) {
        while (playing != null && player != null) {
            delay(5000)
            val p = player ?: break
            val item = playing ?: break
            val pos = p.currentPosition.coerceAtLeast(0L)
            savedPosition = pos
            withContext(Dispatchers.IO) { runCatching { Api.saveProgress(server, item.path, pos) } }
        }
    }

    DisposableEffect(player) {
        onDispose { player?.release() }
    }

    MaterialTheme(colorScheme = darkColorScheme(background = Bg, surface = Panel, primary = Accent, onBackground = Color.White, onSurface = Color.White)) {
        if (playing != null && player != null) {
            Column(Modifier.fillMaxSize().background(Color.Black)) {
                AndroidView(factory = { ctx ->
                    PlayerView(ctx).apply {
                        useController = true
                        this.player = player
                        keepScreenOn = true
                        playerView = this
                    }
                }, update = { it.player = player }, modifier = Modifier.fillMaxWidth().weight(1f))
                Row(Modifier.fillMaxWidth().background(Panel).padding(horizontal = 24.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = {
                        val p = player ?: return@Button
                        runCatching { TrackSelectionDialogBuilder(activity, "Âm thanh", p, C.TRACK_TYPE_AUDIO).build().show() }
                    }) { Text("Âm thanh") }
                    Button(onClick = {
                        val p = player ?: return@Button
                        runCatching { TrackSelectionDialogBuilder(activity, "Phụ đề", p, C.TRACK_TYPE_TEXT).build().show() }
                    }) { Text("Phụ đề") }
                    Spacer(Modifier.weight(1f))
                    Column(Modifier.weight(2f)) {
                        Text("${playing?.name ?: ""}", color = Color.White, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(playbackError.ifBlank { playbackStatus }, color = if (playbackError.isBlank()) Muted else Color(0xFFFF9B9B), maxLines = 2, overflow = TextOverflow.Ellipsis, fontSize = 11.sp)
                    }
                    OutlinedButton(onClick = {
                        val p = player; val item = playing
                        if (p != null && item != null) activity.lifecycleScope.launch(Dispatchers.IO) { runCatching { Api.saveProgress(server, item.path, p.currentPosition) } }
                        player?.release(); player = null; playing = null
                        request(currentPath)
                    }) { Text("Đóng") }
                }
            }
        } else {
            Row(Modifier.fillMaxSize().background(Bg)) {
                Column(Modifier.width(250.dp).fillMaxHeight().background(Color(0xFF0D121D)).padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
                    Text("PC  /  SHIELD", color = Accent, fontSize = 13.sp, fontWeight = FontWeight.Bold, letterSpacing = 2.sp)
                    Text("Cinema", color = Color.White, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    Text("Your library, on the big screen.", color = Muted, fontSize = 14.sp)
                    Spacer(Modifier.height(6.dp))
                    Text("SERVER PC", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    OutlinedTextField(value = serverInput, onValueChange = { serverInput = it }, label = { Text("http://IP:8787") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Button(onClick = { server = serverInput.trim().trimEnd('/'); request("") }, modifier = Modifier.fillMaxWidth(), enabled = !loading) { Text(if (loading) "Đang kết nối…" else "Kết nối") }
                    Text(if (connected) "● Đã kết nối" else "○ Chưa kết nối", color = if (connected) Accent else Muted, fontSize = 12.sp)
                    Spacer(Modifier.weight(1f))
                    Text("PCShieldStream 1.0", color = Muted, fontSize = 11.sp)
                }
                Column(Modifier.fillMaxSize().padding(horizontal = 30.dp, vertical = 24.dp)) {
                    Text(if (currentPath.isBlank()) "Thư viện phim" else currentPath.substringAfter(':').ifBlank { "Thư viện phim" }, color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Text("Phát trực tiếp từ PC · Không chuyển mã", color = Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 5.dp, bottom = 18.dp))
                    if (currentPath.isNotBlank()) {
                        TextButton(onClick = { val parent = currentPath.substringBeforeLast('/', ""); request(if (parent.endsWith(":")) parent else parent) }) { Text("← Quay lại") }
                    }
                    if (error.isNotBlank()) Text(error, color = Color(0xFFFF9B9B), modifier = Modifier.padding(bottom = 10.dp))
                    if (!connected && entries.isEmpty()) {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Nhập địa chỉ IP của PC rồi chọn Kết nối", color = Muted, fontSize = 18.sp) }
                    } else if (entries.isEmpty() && !loading) {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Thư mục này chưa có video được hỗ trợ", color = Muted) }
                    } else {
                        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            items(entries, key = { it.path }) { entry ->
                                Row(Modifier.fillMaxWidth().background(Panel, RoundedCornerShape(12.dp)).clickable {
                                    if (entry.type == "dir") request(entry.path) else play(entry)
                                }.focusable().padding(horizontal = 18.dp, vertical = 15.dp), verticalAlignment = Alignment.CenterVertically) {
                                    Text(if (entry.type == "dir") "▰" else "▶", color = Accent, fontSize = 22.sp, modifier = Modifier.width(42.dp))
                                    Column(Modifier.weight(1f)) {
                                        Text(entry.name, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Medium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                        Text(if (entry.type == "dir") "Thư mục" else formatSize(entry.size), color = Muted, fontSize = 12.sp)
                                    }
                                    Text(if (entry.type == "dir") "MỞ  ›" else "PHÁT  ›", color = Accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun formatSize(bytes: Long): String = if (bytes <= 0) "Video" else String.format(Locale.getDefault(), "%.1f GB", bytes / 1073741824.0)

private object Api {
    private fun enc(s: String) = URLEncoder.encode(s, "UTF-8")
    fun url(base: String, endpoint: String, path: String): String = "${base.trimEnd('/')}$endpoint?path=${enc(path)}"
    private fun get(url: String): String {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 5000; c.readTimeout = 15000; c.setRequestProperty("Accept", "application/json")
        try { val code=c.responseCode; val stream=if(code in 200..299) c.inputStream else c.errorStream; val body=stream.bufferedReader(Charsets.UTF_8).use { it.readText() }; if(code !in 200..299) error("HTTP $code: $body"); return body } finally { c.disconnect() }
    }
    fun list(base: String, path: String): List<MediaEntry> {
        val obj=JSONObject(get("${base.trimEnd('/')}/api/list?path=${enc(path)}")); val a=obj.getJSONArray("items")
        return (0 until a.length()).map { val x=a.getJSONObject(it); MediaEntry(x.getString("name"),x.getString("path"),x.getString("type"),x.optLong("size",0),x.optBoolean("root",false)) }
    }
    fun subtitles(base: String, path: String): List<MediaEntry> {
        val obj=JSONObject(get("${base.trimEnd('/')}/api/subtitles?path=${enc(path)}")); val a=obj.getJSONArray("items")
        return (0 until a.length()).map { val x=a.getJSONObject(it); MediaEntry(x.getString("name"),x.getString("path"),"subtitle") }
    }
    fun progress(base: String, path: String): Long = JSONObject(get("${base.trimEnd('/')}/api/progress?path=${enc(path)}")).optLong("positionMs",0)
    fun saveProgress(base: String, path: String, position: Long) {
        val c=URL("${base.trimEnd('/')}/api/progress").openConnection() as HttpURLConnection
        c.requestMethod="POST"; c.doOutput=true; c.connectTimeout=5000; c.readTimeout=5000; c.setRequestProperty("Content-Type","application/json; charset=utf-8")
        try { val body=JSONObject().put("path",path).put("positionMs",position).toString(); c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }; if(c.responseCode !in 200..299) error("Save progress failed") } finally { c.disconnect() }
    }
}
