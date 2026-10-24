# PCShieldStream

A small LAN-only movie streamer: a Python server on Windows plus an Android TV app source project intended for NVIDIA Shield TV 2019 / Android 11. The app has a dark, Apple-TV-inspired browsing layout, folder navigation, ExoPlayer playback, audio/subtitle track selection, sidecar subtitle auto-loading, seeking via HTTP Range, and server-side resume position storage.

## Important build status

This bundle contains the full source project, but an APK has **not** been compiled here: this environment does not have the Android SDK, Gradle, or an Android build toolchain installed. Build the APK on a PC with Android Studio (steps below). Do not treat this as a tested/release APK until built and tested on the Shield.

## 1. Start the Windows server

1. Install Python 3.10 or newer from python.org and enable the Python launcher (`py`).
2. Open `server/start_server.bat` in Notepad and change `MOVIE_FOLDER` to the actual movie folder, e.g. `E:\Movies`.
3. Run `start_server.bat`. Keep the console open.
4. Run `ipconfig` in a Windows terminal and note the PC's IPv4 address, such as `192.168.1.20`.
5. If Windows Firewall asks, allow Python on **Private networks only**. Do not expose port 8787 to the Internet.

The server is standard-library Python only. Supported video extensions include MKV, MP4, M4V, MOV, AVI, WebM, TS and M2TS. It serves files directly with HTTP byte ranges; it does not transcode.

## 2. Build the Android TV APK

1. Install Android Studio on a Windows PC.
2. Open the `android` folder in Android Studio.
3. Use JDK 17 (Android Studio's bundled JBR is suitable), install Android SDK Platform 35 and accept SDK licenses when prompted. Android Studio will download Gradle and dependencies.
4. Wait for Gradle sync. Then choose **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
5. The debug APK should appear at `android/app/build/outputs/apk/debug/app-debug.apk`.

Alternatively, after installing Android SDK and Gradle, run `gradle assembleDebug` from the `android` folder.

## 3. Install on Shield

Enable Developer options on Shield (Settings > Device Preferences > About, click Build several times), then enable Network debugging or USB debugging. On the PC with Android platform-tools:

```bat
adb connect SHIELD_IP:5555
adb install -r app-debug.apk
```

If Network debugging uses a pairing port, pair with the code/port shown on the Shield first (`adb pair SHIELD_IP:PAIR_PORT`), then connect to the displayed debugging port. Alternatively, copy the APK to a USB drive and install it with a file manager that supports sideloading.

## 4. Connect and play

1. Make sure the PC and Shield are on the same home LAN. Ethernet is recommended for high-bitrate 4K remuxes; good 5 GHz Wi-Fi may also work.
2. Launch PCShieldStream on Shield.
3. Enter the PC address, e.g. `http://192.168.1.20:8787`, and select **Kết nối**.
4. Browse folders and select a video. Seeking works when the file container/server and decoder support it.
5. The app automatically attaches the first matching sidecar subtitle in the same folder (`Movie.srt`, `Movie.vi.srt`, etc.); use the player controls for audio/subtitle track selection.

## Notes and limitations

- Direct Play means the original file bytes are sent without server-side transcoding. Playback depends on Shield hardware/Media3 decoder support for the file's video codec, audio codec, profile, bit depth, and container. Some audio formats may need an external player or remuxing; this server does not convert them.
- Embedded audio tracks are selectable through the Media3 track selector. External subtitle auto-loading supports SRT, ASS/SSA, and VTT files that start with the video filename. ExoPlayer/Media3 support for ASS styling may vary; if an ASS file fails, convert it to SRT or test an external player.
- This first version has a simple list rather than downloaded posters/metadata. It is intentionally folder-based as requested.
- Progress is stored in `server/progress.json`, keyed by the relative root path. The server saves progress when the app is playing every five seconds and when playback is closed.
- The server has no authentication or TLS. Keep it on a trusted home network and only expose selected movie folders.
- This project is a starter implementation and has not been compiled or tested on a physical Shield in this environment. Build and test on the target device before relying on it.
