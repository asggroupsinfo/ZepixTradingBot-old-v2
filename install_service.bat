@echo off
echo Installing Zepix Trading Bot as Windows Service...
venv\Scripts\python.exe windows_service.py install
echo Service installed! Start with: net start ZepixTradingBot
pause