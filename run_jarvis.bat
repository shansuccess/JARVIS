@echo off
title J.A.R.V.I.S. Desktop Assistant
color 0B
cls
echo =========================================================
echo       J.A.R.V.I.S. - STARK INDUSTRIES MARK VII
echo =========================================================
echo.
echo Starting neural bus and local interface...
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found on your PATH.
    echo Please ensure Python is installed and added to PATH.
    pause
    exit /b 1
)

python run_jarvis.py
pause
