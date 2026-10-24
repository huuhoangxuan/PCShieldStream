@echo off
chcp 65001 >nul
setlocal
echo This adds a Windows Defender Firewall rule for PCShieldStream on Private networks only.
echo Run this file as Administrator. It limits the rule to your local subnet.
netsh advfirewall firewall add rule name="PCShieldStream LAN 8787" dir=in action=allow protocol=TCP localport=8787 remoteip=localsubnet profile=private
if errorlevel 1 (
  echo Failed. Right-click this file and choose Run as administrator.
) else (
  echo Firewall rule added. Do not create port forwarding on your router.
)
pause
