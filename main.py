#!/usr/bin/env python3
import json
import os
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, date, timedelta
from typing import Dict, Any

from config import Config
from trading_engine import TradingEngine
from risk_manager import RiskManager
from mt5_client import MT5Client
from telegram_bot import TelegramBot
from alert_processor import AlertProcessor
from analytics_engine import AnalyticsEngine 
from models import Alert

app = FastAPI(title="Zepix Automated Trading Bot")

# Initialize components
config = Config()
risk_manager = RiskManager(config)
mt5_client = MT5Client(config)
telegram_bot = TelegramBot(config)
alert_processor = AlertProcessor(config)
trading_engine = TradingEngine(config, risk_manager, mt5_client, telegram_bot, alert_processor)

# Set dependencies
telegram_bot.set_dependencies(risk_manager, trading_engine)

@app.on_event("startup")
async def startup_event():
    """Initialize the trading bot on startup"""
    success = await trading_engine.initialize()
    if success:
        telegram_bot.send_message("🤖 Trading Bot Started Successfully!")
        # Start trade management task
        asyncio.create_task(trading_engine.manage_open_trades())
        # Start Telegram polling
        telegram_bot.start_polling()
    else:
        telegram_bot.send_message("❌ Trading Bot Failed to Initialize!")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle incoming webhook alerts from TradingView/Zepix"""
    try:
        data = await request.json()
        
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
        "timestamp": datetime.utcnow().isoformat(),
        "daily_loss": risk_manager.daily_loss,
        "lifetime_loss": risk_manager.lifetime_loss,
        "mt5_connected": mt5_client.initialized
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
        "simulation_mode": config["simulate_orders"]
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Zepix Trading Bot")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", default=8000, type=int, help="Port number")
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)