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
    if success:
        telegram_bot.send_message("🤖 Trading Bot v2.0 Started Successfully!\n📊 1:1 RR System Active\n🔄 Re-entry System Enabled")
        # Start trade management task
        asyncio.create_task(trading_engine.manage_open_trades())
        # Start Telegram polling
        telegram_bot.start_polling()
    else:
        telegram_bot.send_message("❌ Trading Bot Failed to Initialize!")
    
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
    symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
    
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Zepix Trading Bot v2.0")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", default=8000, type=int, help="Port number")
    args = parser.parse_args()
    
    print("=" * 50)
    print("ZEPIX TRADING BOT v2.0")
    print("=" * 50)
    print(f"Starting server on {args.host}:{args.port}")
    print("Features enabled:")
    print("✓ Fixed lot sizes")
    print("✓ Re-entry system") 
    print("✓ SL hunting protection")
    print("✓ 1:1 Risk-Reward")
    print("✓ Progressive SL reduction")
    print("=" * 50)
    
    uvicorn.run(app, host=args.host, port=args.port)