# Build the APK with GitHub Actions

1. Upload/commit this entire source tree to the repository root, preserving `.github/workflows/build-apk.yml`.
2. Open GitHub → **Actions** → **Build PCShieldStream APK**.
3. If no run started automatically, choose **Run workflow**.
4. Open the newest run. Wait for the `build` job to show green.
5. In **Artifacts**, download `PCShieldStream-debug-apk` and extract `app-debug.apk`.
6. Install it on NVIDIA Shield and test playback with a small MP4 and an MKV.

The workflow uses Java 17, Gradle 8.9, Android SDK Platform 35, Build Tools 35.0.0, and only the supported `platform-tools` package during Android SDK setup. This avoids the obsolete SDK package named `tools`.

A green workflow means the APK compiled successfully; it does not guarantee playback has been verified on physical Shield hardware.
