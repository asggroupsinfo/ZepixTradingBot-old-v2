@echo off
title Zepix Trading Bot v2.0
cd /d E:\ZepixTrandingbot-New
echo Starting Zepix Trading Bot v2.0...
echo ================================
echo Features Enabled:
echo - Fixed Lot Sizes
echo - Re-entry System
echo - SL Hunting Protection
echo - 1:1 Risk-Reward
echo ================================
call venv\Scripts\activate.bat
python main.py --host 0.0.0.0 --port 8000
pause