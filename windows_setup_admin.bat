@echo off
echo ============================================================
echo ZEPIX TRADING BOT - ADMIN MODE DEPLOYMENT (PORT 80)
echo ============================================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: Administrator privileges required
    echo    Right-click windows_setup_admin.bat and select "Run as Administrator"
    timeout /t 5 /nobreak >nul
    exit /b 1
)
echo ✓ Running as Administrator

REM Check Python 64-bit
echo.
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found! Please install Python 3.10 64-bit
    timeout /t 3 /nobreak >nul
    exit /b 1
)

python -c "import struct; exit(0 if struct.calcsize('P') * 8 == 64 else 1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: 32-bit Python detected! MetaTrader5 requires 64-bit Python
    echo    Please install Python 3.10 64-bit from python.org
    timeout /t 3 /nobreak >nul
    exit /b 1
)
echo ✓ Python 64-bit detected

REM Clean old venv if exists
echo.
echo [2/7] Cleaning old virtual environment...
if exist venv (
    echo Removing old venv...
    rmdir /s /q venv
)
echo ✓ Clean state ready

REM Create fresh venv
echo.
echo [3/7] Creating fresh virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ ERROR: Failed to create virtual environment
    timeout /t 3 /nobreak >nul
    exit /b 1
)
echo ✓ Virtual environment created

REM Activate venv
echo.
echo [4/7] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERROR: Failed to activate virtual environment
    timeout /t 3 /nobreak >nul
    exit /b 1
)
echo ✓ Virtual environment activated

REM Upgrade pip
echo.
echo [5/7] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo ✓ pip upgraded

REM Install dependencies
echo.
echo [6/7] Installing dependencies (this may take 1-2 minutes)...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ ERROR: Failed to install dependencies
    timeout /t 3 /nobreak >nul
    exit /b 1
)
echo ✓ All dependencies installed

REM Setup MT5 connection
echo.
echo [7/7] Setting up MT5 connection...
python setup_mt5_connection.py
if errorlevel 1 (
    echo ❌ MT5 auto-setup failed even with admin rights
    echo    Please check if MT5 is installed
    echo    Bot will attempt to run in SIMULATION MODE
    set MT5_MODE=simulation
) else (
    echo ✓ MT5 connection verified with admin rights
    set MT5_MODE=live
)

REM Check .env file
echo.
echo Checking .env configuration...
if not exist .env (
    echo ❌ ERROR: .env file not found!
    echo.
    echo Please create .env with your credentials:
    echo   TELEGRAM_TOKEN=your_token
    echo   TELEGRAM_CHAT_ID=your_chat_id
    echo   MT5_LOGIN=your_login
    echo   MT5_PASSWORD=your_password
    echo   MT5_SERVER=your_server
    echo.
    echo Deployment aborted - .env file is required
    exit /b 1
)
echo ✓ .env file found

echo.
echo ============================================================
echo ✅ ADMIN DEPLOYMENT COMPLETE!
echo ============================================================
if "%MT5_MODE%"=="simulation" (
    echo.
    echo ⚠️  MODE: SIMULATION ^(MT5 not connected^)
    echo    Bot will simulate trades without real execution
    echo    Please check if MT5 is installed and configured
) else (
    echo.
    echo ✅ MODE: LIVE TRADING ^(MT5 connected^)
)
echo.
echo Starting Zepix Trading Bot on PORT 80 (Admin Mode)...
echo Press Ctrl+C to stop the bot
echo.
python main.py --host 0.0.0.0 --port 80
