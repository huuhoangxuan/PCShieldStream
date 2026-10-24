@echo off
chcp 65001 >nul
setlocal
set "MOVIE_FOLDER=D:\Movies"
set "MOVIE_FOLDER_2="
if not exist "%MOVIE_FOLDER%" set "MOVIE_FOLDER=%USERPROFILE%\Videos"
echo PCShieldStream - Windows server
echo Allowed folder 1: %MOVIE_FOLDER%
if not "%MOVIE_FOLDER_2%"=="" if exist "%MOVIE_FOLDER_2%" goto :two_roots
echo Optional second folder is disabled. Edit MOVIE_FOLDER_2 to enable it.
py -3 server.py --root "%MOVIE_FOLDER%" --port 8787
goto :finish
:two_roots
echo Allowed folder 2: %MOVIE_FOLDER_2%
py -3 server.py --root "%MOVIE_FOLDER%" --root "%MOVIE_FOLDER_2%" --port 8787
:finish
if errorlevel 1 pause
