@echo off
title CopyPasta - Windows Clipboard Manager & 2FA
cd /d "%~dp0"

echo Starting CopyPasta...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo CopyPasta encountered an error. Press any key to exit.
    pause
)
