@echo off
title Operation ShadowStrike - Projector Display Launcher
echo ===================================================
echo     ALGO CLUB - OPERATION SHADOWSTRIKE
echo     Projector Live Display System
echo ===================================================
echo.
echo Launching presentation in default browser...
start "" "%~dp0index.html"
echo.
echo Presentation launched!
echo Tips:
echo   - Press F11 or 'F' key for Fullscreen
echo   - Press 'P' to switch between 16:9 Widescreen and Poster View
echo   - Press 'T' to switch Projector Contrast Presets
echo   - Press 'Q' to zoom the QR code
echo   - Press 'H' to hide the presenter controls
echo.
timeout /t 3 >nul
