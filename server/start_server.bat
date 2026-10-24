@echo off
chcp 65001 >nul
setlocal
set "MOVIE_FOLDER=D:\Movies"
if not exist "%MOVIE_FOLDER%" set "MOVIE_FOLDER=%USERPROFILE%\Videos"
echo PCShieldStream - Windows server
echo Current allowed folder: %MOVIE_FOLDER%
echo Edit this BAT file to change MOVIE_FOLDER or add another --root argument.
py -3 server.py --root "%MOVIE_FOLDER%" --port 8787
if errorlevel 1 pause
