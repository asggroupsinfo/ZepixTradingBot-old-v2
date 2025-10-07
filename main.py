#!/usr/bin/env python3
import json
import os
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta
from typing import Dict, Any
from contextlib import asynccontextmanager

from config import Config
from trading_engine import TradingEngine
from risk_manager import RiskManager
from mt5_client import MT5Client
from telegram_bot import TelegramBot
from alert_processor import AlertProcessor
from analytics_engine import AnalyticsEngine 
from models import Alert

# Initialize components
config = Config()
risk_manager = RiskManager(config)
mt5_client = MT5Client(config)
telegram_bot = TelegramBot(config)
alert_processor = AlertProcessor(config)

# Initialize trading engine with all components
trading_engine = TradingEngine(config, risk_manager, mt5_client, telegram_bot, alert_processor)

# Set dependencies
telegram_bot.set_dependencies(risk_manager, trading_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    success = await trading_engine.initialize()
    
    # Critical: If live trading mode is enabled, abort if MT5 fails to connect
    if not config.get('simulate_orders', False) and not success:
        error_msg = "❌ CRITICAL: Live trading mode enabled but MT5 connection failed!\n" \
                   "✋ Bot startup aborted to prevent trading errors.\n" \
                   "🔧 Please verify:\n" \
                   "  1. MetaTrader 5 is installed and running\n" \
                   "  2. MT5 credentials are correct in environment variables\n" \
                   "  3. MT5 server is accessible"
        telegram_bot.send_message(error_msg)
        print(error_msg)
        raise RuntimeError("MT5 connection required for live trading mode")
    
    if success:
        mode = "SIMULATION" if config.get('simulate_orders', False) else "LIVE TRADING"
        telegram_bot.send_message(f"🤖 Trading Bot v2.0 Started Successfully!\n"
                                 f"🔧 Mode: {mode}\n"
                                 f"📊 1:1 RR System Active\n"
                                 f"🔄 Re-entry System Enabled")
        # Start trade management task
        asyncio.create_task(trading_engine.manage_open_trades())
        # Start Telegram polling
        telegram_bot.start_polling()
    else:
        telegram_bot.send_message("⚠️ Trading Bot Started in Simulation Mode (MT5 not available)")
    
    yield
    
    # Shutdown (cleanup if needed)
    print("🔄 Trading bot shutting down...")

app = FastAPI(title="Zepix Automated Trading Bot v2.0", lifespan=lifespan)

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook alerts from TradingView/Zepix"""
    try:
        data = await request.json()
        
        print(f"📨 Webhook received: {json.dumps(data, indent=2)}")
        
        # Validate alert
        if not alert_processor.validate_alert(data):
            return JSONResponse(content={"status": "rejected", "message": "Alert validation failed"})
        
        # Process alert
        result = await trading_engine.process_alert(data)
        
        if result:
            return JSONResponse(content={"status": "success", "message": "Alert processed"})
        else:
            return JSONResponse(content={"status": "rejected", "message": "Alert processing failed"})
            
    except Exception as e:
        error_msg = f"Webhook processing error: {str(e)}"
        telegram_bot.send_message(f"❌ {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "daily_loss": risk_manager.daily_loss,
        "lifetime_loss": risk_manager.lifetime_loss,
        "mt5_connected": mt5_client.initialized,
        "features": {
            "fixed_lots": True,
            "reentry_system": True,
            "sl_hunting_protection": True,
            "1_1_rr": True
        }
    }

@app.get("/stats")
async def get_stats():
    """Get current statistics"""
    stats = risk_manager.get_stats()
    return {
        "daily_profit": stats["daily_profit"],
        "daily_loss": stats["daily_loss"],
        "lifetime_loss": stats["lifetime_loss"],
        "total_trades": stats["total_trades"],
        "winning_trades": stats["winning_trades"],
        "win_rate": stats["win_rate"],
        "current_risk_tier": stats["current_risk_tier"],
        "risk_parameters": stats["risk_parameters"],
        "trading_paused": trading_engine.is_paused,
        "simulation_mode": config["simulate_orders"],
        "lot_size": stats["current_lot_size"],
        "balance": stats["account_balance"]
    }

@app.post("/pause")
async def pause_trading():
    """Pause trading"""
    trading_engine.is_paused = True
    return {"status": "success", "message": "Trading paused"}

@app.post("/resume")
async def resume_trading():
    """Resume trading"""
    trading_engine.is_paused = False
    return {"status": "success", "message": "Trading resumed"}

@app.get("/trends")
async def get_trends():
    """Get all trends"""
    trends = {}
    
    # Get all symbols that have trends set (both from webhooks and manual)
    trend_data = trading_engine.trend_manager.trends.get("symbols", {})
    
    # If no symbols set, show default list
    if not trend_data:
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
    else:
        symbols = list(trend_data.keys())
    
    for symbol in symbols:
        trends[symbol] = trading_engine.trend_manager.get_all_trends(symbol)
    
    return {"status": "success", "trends": trends}

@app.post("/set_trend")
async def set_trend_api(symbol: str, timeframe: str, trend: str, mode: str = "MANUAL"):
    """Set trend via API"""
    try:
        trading_engine.trend_manager.update_trend(symbol, timeframe, trend.lower(), mode)
        return {"status": "success", "message": f"Trend set for {symbol} {timeframe}: {trend}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/chains")
async def get_reentry_chains():
    """Get active re-entry chains"""
    chains = []
    for chain_id, chain in trading_engine.reentry_manager.active_chains.items():
        chains.append(chain.dict())
    return {"status": "success", "chains": chains}

@app.get("/lot_config")
async def get_lot_config():
    """Get lot size configuration"""
    return {
        "fixed_lots": config["fixed_lot_sizes"],
        "manual_overrides": config.get("manual_lot_overrides", {}),
        "current_balance": mt5_client.get_account_balance(),
        "current_lot": risk_manager.get_fixed_lot_size(mt5_client.get_account_balance())
    }

@app.post("/set_lot_size")
async def set_lot_size(tier: int, lot_size: float):
    """Set manual lot size override"""
    try:
        risk_manager.set_manual_lot_size(tier, lot_size)
        return {"status": "success", "message": f"Lot size set: ${tier} → {lot_size}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/reset_stats")
async def reset_stats():
    """Reset risk manager stats (for testing only)"""
    try:
        risk_manager.daily_loss = 0.0
        risk_manager.daily_profit = 0.0
        risk_manager.lifetime_loss = 0.0
        risk_manager.total_trades = 0
        risk_manager.winning_trades = 0
        risk_manager.save_stats()
        return {"status": "success", "message": "Stats reset successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Zepix Trading Bot v2.0")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", default=8000, type=int, help="Port number")
    args = parser.parse_args()
    
    rr_ratio = config.get("rr_ratio", 1.0)
    print("=" * 50)
    print("ZEPIX TRADING BOT v2.0")
    print("=" * 50)
    print(f"Starting server on {args.host}:{args.port}")
    print("Features enabled:")
    print("✓ Fixed lot sizes")
    print("✓ Re-entry system") 
    print("✓ SL hunting protection")
    print(f"✓ 1:{rr_ratio} Risk-Reward")
    print("✓ Progressive SL reduction")
    print("=" * 50)
    
    uvicorn.run(app, host=args.host, port=args.port)