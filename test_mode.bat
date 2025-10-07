@echo off
title Zepix Trading Bot v2.0 - TEST MODE
cd /d E:\ZepixTrandingbot-New
echo Starting in SIMULATION MODE...
call venv\Scripts\activate.bat
set SIMULATE_ORDERS=true
python main.py --host 127.0.0.1 --port 8000
pause