# PCShieldStream server (Windows)

Requires Python 3.10+; no pip packages required.

1. Edit `start_server.bat` and set `MOVIE_FOLDER` to the folder containing your movies, e.g. `E:\Phim`. You can add more folders by adding another `--root "E:\Phim2"` to the command.
2. Double-click `start_server.bat`. Allow Python through Windows Defender Firewall on **Private networks only** if prompted.
3. Find the PC's IPv4 address with `ipconfig`. Shield and PC must be on the same LAN. Do not expose port 8787 to the Internet or set port forwarding.
4. In the Android app, enter `http://PC_IP:8787`, for example `http://192.168.1.20:8787`.

The server only exposes files within explicitly configured roots and supports HTTP byte-range requests for seeking. Progress is stored in `progress.json` next to the server script. The server is intended for trusted home LANs; it has no user authentication or TLS, so do not use it on public/untrusted networks.
