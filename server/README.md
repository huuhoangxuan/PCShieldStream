# PCShieldStream server (Windows)

Requires Python 3.10+; no pip packages required.

1. Edit `start_server.bat` and set `MOVIE_FOLDER` to the folder containing your movies, e.g. `E:\Phim`. You can add more folders by adding another `--root "E:\Phim2"` to the command.
2. Double-click `start_server.bat`. Allow Python through Windows Defender Firewall on **Private networks only** if prompted.
3. Optional but recommended: run `allow_firewall_private.bat` as Administrator to add a Windows Defender Firewall allow rule for TCP 8787 on **Private** networks and the local subnet only. Do not add a Public-profile rule.
4. Find the PC's IPv4 address with `ipconfig`. Shield and PC must be on the same LAN. Do not expose port 8787 to the Internet or set port forwarding.
4. In the Android app, enter `http://PC_IP:8787`, for example `http://192.168.1.20:8787`.

The server only exposes files within explicitly configured roots and supports HTTP byte-range requests for seeking. It rejects client source addresses that are not loopback/private/link-local as defense in depth, but **this is not authentication**: other devices on the same LAN can still access the configured media. Progress is cached in memory and atomically persisted to `progress.json`; poster results are cached in `posters.json` (successful lookups for 30 days, no-result lookups for 6 hours; network errors are not cached). The server has no user authentication or TLS, so use only on a trusted home LAN and do not forward port 8787 from your router.
