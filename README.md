# PCShieldStream 1.3.0

PCShieldStream streams local movie files from a Windows PC to NVIDIA Shield TV / Android TV over a trusted home LAN. The Android app uses Media3 ExoPlayer for direct playback; the Python server serves original file bytes with HTTP byte-range support and stores resume positions.

## Current source status

- Android TV app source and launcher icon included.
- Remembers the server URL and attempts reconnection at launch.
- Folder navigation, local search/filter, sorting by name or file size, automatic poster lookup, audio/subtitle selection, sidecar subtitles, and resume position.
- Poster lookup uses Cinemeta metadata and caches successful results for 30 days and true no-result lookups for 6 hours in `server/posters.json`. Temporary network failures are not cached; concurrent lookups are limited to three. Internet is required for first-time lookups. A missing poster falls back to the app's placeholder.
- HTTP byte ranges support seeking; client disconnects while probing/seeking are logged without attempting a second error response.
- The GitHub Actions workflow overrides the deprecated Android SDK `tools` package and installs only current platform-tools plus SDK Platform 35/build-tools 35.0.0.

**Important:** This is source code, not a prebuilt/tested release APK. This environment has no Android SDK/Gradle toolchain, so compile on GitHub Actions and test the resulting APK on the Shield before relying on it. Direct Play still depends on the Shield's Media3 decoder supporting the file's container and codecs.

## Windows server

1. Install Python 3.10+ from python.org (enable the Python launcher `py`).
2. Edit `server/start_server.bat`. Set `MOVIE_FOLDER` to your main library folder (default `D:\Movies`). Optionally set `MOVIE_FOLDER_2` to another folder. Add more `--root` arguments manually if needed.
3. Run `start_server.bat` and keep its console open.
4. Allow Python on **Private networks only** if Windows Firewall asks. For a stricter inbound rule, run `server/allow_firewall_private.bat` as Administrator; it restricts TCP 8787 to the local subnet and Private profile. Do not forward port 8787 to the internet.
5. Find the PC's LAN IPv4 with `ipconfig`; the app server URL is `http://PC_IP:8787`.

Test in a PC browser: `http://127.0.0.1:8787/api/health`. Expected JSON contains `"ok": true`.

## Build APK on GitHub

The workflow `.github/workflows/build-apk.yml` runs when Android/server/workflow files change or when manually dispatched. Open the repository's **Actions** tab, open the newest successful run, then download artifact `PCShieldStream-debug-apk` and extract `app-debug.apk`.

If the run fails, open the failed step and inspect the first actual `Error:` above the stack trace. A successful build only confirms compilation; it does not prove playback on physical hardware.

## Install / update on Shield

Install `app-debug.apk` via USB/file manager or ADB. Updating with the same package/signing key generally preserves app data. On first run, enter `http://PC_IP:8787` once and press **Kết nối**. The app stores that URL and tries to reconnect on later launches.

## Playback / formats

- No transcoding: original file bytes are streamed to the Shield.
- Common extensions: MKV, MP4, M4V, MOV, AVI, WebM, TS, M2TS, MPG, MPEG, WMV, FLV, OGV.
- Sidecar subtitles: SRT, ASS/SSA, VTT, matching the video basename (for example `Movie.vi.srt`). Embedded tracks can be selected in the player. Subtitle format support depends on Media3.
- Ethernet is recommended for high-bitrate 4K files; reliable 5 GHz Wi-Fi can work.
- Progress is saved every 15 seconds, on app background/close, and reset to the beginning when a title finishes. It is cached in memory and atomically persisted to `server/progress.json`. Do not delete that file if you want to keep watch positions.

## Troubleshooting

1. If folders show but videos do not play, check the server console and the app's playback error text. A `ConnectionResetError` can be a normal cancellation from seeking/probing; it is not by itself proof of a server defect.
2. Verify `http://PC_IP:8787/api/health` from the PC and `http://PC_IP:8787/api/list` on a device on the same LAN.
3. If one MP4 and one MKV both fail, collect Android `adb logcat` around `ExoPlayer`/`MediaCodec` before changing codecs or transcoding.
4. Poster lookup requires internet on the PC and works best with filenames such as `Dune Part Two (2024).mkv`.

## Security

The server has no authentication or TLS and listens on all interfaces for LAN access. It rejects non-private client source IPs as defense in depth, but other devices on the same LAN can still access it. Use only on a trusted private network, allow the port only on Private firewall profile, do not configure router port forwarding, and expose only movie directories you intend to share.
