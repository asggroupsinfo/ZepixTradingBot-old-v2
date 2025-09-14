@echo off
title Zepix Trading Bot - Production
cd /d E:\ZepixTrandingbot-New

echo 🔹 Activating Virtual Environment...
call venv\Scripts\activate.bat

echo 🔹 Starting Zepix Trading Bot on Port 80...
venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 80
pause