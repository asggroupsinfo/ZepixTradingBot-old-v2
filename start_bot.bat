@echo off
cd /d C:\ZepixTrandingbot-New
call venv\Scripts\activate.bat

REM Start python without console window
start /B venv\Scripts\python.exe main.py --host 127.0.0.1 --port 8000

echo Bot started in background. Check logs for details.