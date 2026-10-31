@echo off
title Operation ShadowStrike - Kiosk Projector Mode
echo Starting Fullscreen Projector Display...
set FILE_URL=file:///%~dp0index.html
set FILE_URL=%FILE_URL:\=/%

:: Try Chrome first, then Edge, then default start
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --start-fullscreen "%FILE_URL%"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --start-fullscreen "%FILE_URL%"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --start-fullscreen "%FILE_URL%"
) else (
    start "" "%~dp0index.html"
)
exit
