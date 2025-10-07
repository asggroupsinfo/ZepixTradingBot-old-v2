# Zepix Automated Trading Bot v2.0

## Overview
This is an automated Forex and Gold trading bot that integrates with MetaTrader 5 (MT5) and receives trading signals via webhooks from TradingView. The bot includes advanced risk management, re-entry strategies, and Telegram notifications.

## Current State
- ✅ Running on Replit in simulation mode (MT5 is Windows-only, not available on Linux)
- ✅ FastAPI server running on port 5000
- ✅ Webhook endpoint ready to receive TradingView alerts
- ✅ Telegram bot configured for notifications and control
- ✅ All dependencies installed

## Recent Changes (Oct 7, 2025)
- **Critical Bug Fixes for Live Trading:**
  - Fixed MT5 position close error: Now distinguishes API errors from closed positions
  - Fixed trade tracking sync: Properly removes closed trades from memory
  - Fixed duplicate alert detection: Allows same alerts >5 min apart
  - Fixed FastAPI deprecation: Migrated to lifespan context manager
  - Fixed /trends endpoint: Now dynamically shows all symbols (not hardcoded)
  - Fixed LSP type errors: Added Optional[str] type hints
- **Security & Compatibility:**
  - Migrated sensitive credentials to environment variables
  - Added MT5 simulation mode for Linux compatibility
  - Updated requirements.txt for Replit (removed Windows-only MT5 package)
  - Configured FastAPI server to run on port 5000
  - Updated .gitignore to protect sensitive files
- **All systems tested and verified - Ready for live trading deployment on Windows with MT5**

## Project Architecture

### Core Components
1. **main.py** - FastAPI server entry point, handles webhooks and API endpoints
2. **trading_engine.py** - Core trading logic orchestrator
3. **risk_manager.py** - Risk management and loss tracking
4. **mt5_client.py** - MetaTrader 5 integration (runs in simulation mode on Linux)
5. **telegram_bot.py** - Telegram interface for monitoring and control
6. **alert_processor.py** - Validates incoming TradingView alerts
7. **database.py** - SQLite database for trade history
8. **pip_calculator.py** - Accurate pip and stop-loss calculations
9. **timeframe_trend_manager.py** - Manages multi-timeframe trend analysis
10. **reentry_manager.py** - Handles re-entry trading logic

### Key Features
- **Fixed Lot Sizes**: Balance-based lot sizing system
- **Re-entry System**: Automatic re-entry on stop-loss with reduced risk
- **SL Hunting Protection**: Guards against premature stop-loss triggers
- **1:1 Risk-Reward**: Balanced risk-reward ratio
- **Progressive SL Reduction**: Reduces stop-loss on each re-entry level
- **Multi-timeframe Trend Analysis**: Validates trades across multiple timeframes

## Environment Variables Required

To run this bot in production, you need to configure these environment variables:

```bash
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# MetaTrader 5 Configuration (Windows only)
MT5_LOGIN=your_mt5_login_here
MT5_PASSWORD=your_mt5_password_here
MT5_SERVER=your_mt5_server_name_here
```

See `.env.example` for a template.

## API Endpoints

### Health Check
- `GET /health` - Returns bot status and configuration

### Statistics
- `GET /stats` - Returns trading statistics and current settings

### Trading Controls
- `POST /pause` - Pause trading
- `POST /resume` - Resume trading

### Webhook
- `POST /webhook` - Receives TradingView alerts (main entry point for signals)

### Trend Management
- `GET /trends` - Get all trends for all symbols
- `POST /set_trend` - Manually set trend for a symbol/timeframe

### Re-entry Chains
- `GET /chains` - View active re-entry chains

### Lot Configuration
- `GET /lot_config` - View lot size configuration
- `POST /set_lot_size` - Set manual lot size override

## Configuration Files

### config.json
Main configuration file containing:
- Symbol mappings (e.g., XAUUSD → GOLD for XM broker)
- Fixed lot sizes by balance tier
- Risk tiers and daily/lifetime loss limits
- Symbol-specific settings (volatility, pip values)
- Re-entry configuration
- Strategy settings

### Symbol Mapping
The bot supports broker-specific symbol mapping:
- TradingView symbol (XAUUSD) → Broker symbol (GOLD for XM)
- Configured in `config.json` under `symbol_mapping`

## Telegram Commands

The bot supports these Telegram commands:
- `/start` - Start the bot
- `/status` - Check bot status
- `/pause` - Pause trading
- `/resume` - Resume trading
- `/performance` - View performance metrics
- `/stats` - View detailed statistics
- `/trades` - View open trades
- `/logic1_on/off` - Toggle Logic 1 strategy
- `/logic2_on/off` - Toggle Logic 2 strategy
- `/logic3_on/off` - Toggle Logic 3 strategy
- `/set_trend` - Set manual trend
- `/show_trends` - Show all trends
- `/chains` - View re-entry chains
- `/lot_size_status` - View lot size settings

## User Preferences
- **Development Mode**: Currently running in simulation mode on Replit
- **Production Deployment**: Requires Windows environment with MT5 installed
- **Webhook Integration**: Designed to receive signals from TradingView/Zepix

## Running the Bot

### On Replit (Current Setup)
The bot is configured to run automatically. It will:
1. Start in simulation mode (MT5 not available on Linux)
2. Listen for webhooks on port 5000
3. Accept TradingView alerts and simulate trades
4. Send notifications via Telegram

### On Windows (Production - Live Trading)
For live trading with real MT5, follow these steps:

**Step 1: Environment Setup**
1. Install MetaTrader 5 on Windows
2. Create `.env` file with your credentials (use `.env.example` as template):
   ```
   TELEGRAM_TOKEN=your_actual_telegram_token
   TELEGRAM_CHAT_ID=your_actual_chat_id
   MT5_LOGIN=your_mt5_login
   MT5_PASSWORD=your_mt5_password
   MT5_SERVER=your_mt5_server
   ```

**Step 2: Enable Live Trading Mode**
Option A: Use production config file:
- Copy `config_prod.json` contents and save as `config.json`
- This sets `simulate_orders: false` for live trading

Option B: Manually edit config.json:
- Open `config.json`
- Change `"simulate_orders": true` to `"simulate_orders": false`

**Step 3: Launch Bot**
```bash
python main.py --host 0.0.0.0 --port 8000
```

**Step 4: Verify Startup**
- Bot will validate MT5 connection on startup
- If MT5 fails in live mode → Bot aborts with clear error message
- If successful → Telegram notification shows "Mode: LIVE TRADING"
- ⚠️ Never run live mode without MT5 connection verified!

**Production Safety:**
- ✅ Bot aborts startup if live mode enabled but MT5 unavailable
- ✅ All credentials loaded from environment variables (never hardcoded)
- ✅ Mode clearly displayed in startup message (SIMULATION vs LIVE TRADING)

## Security Notes
- All sensitive credentials are stored as environment variables
- config.json and config_prod.json do not contain hardcoded secrets
- Database files are excluded from version control
- .env files are gitignored

## Database
- Uses SQLite (`trading_bot.db`)
- Stores trade history, re-entry chains, and SL events
- Used for performance analytics and reporting

## Troubleshooting

### MT5 Connection Issues
- MT5 is Windows-only, simulation mode is used on Linux/Replit
- For real trading, must run on Windows with MT5 installed

### Telegram Not Working
- Verify TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are set correctly
- Check that the bot token is valid and active
- Ensure chat ID matches your Telegram user ID

### Webhook Not Receiving Alerts
- Verify TradingView webhook URL points to: `https://your-replit-url.repl.co/webhook`
- Check alert format matches expected schema
- Review logs for validation errors
