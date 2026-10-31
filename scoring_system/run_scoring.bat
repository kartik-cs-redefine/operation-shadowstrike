@echo off
title WAYGROUND 4-ROUND SCORING & LEADERBOARD SYSTEM
color 0A
cd /d "%~dp0"

echo ===============================================================================
echo     ALGO CLUB - OPERATION SHADOWSTRIKE
echo     AUTOMATED 4-ROUND WAYGROUND SCORING & FINAL LEADERBOARD GENERATOR
echo ===============================================================================
echo.

python leaderboard_engine.py

echo.
echo ===============================================================================
echo     EXECUTION FINISHED
echo ===============================================================================
pause
