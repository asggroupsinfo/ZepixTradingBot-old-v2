import requests
import json
import threading
import time
from typing import Dict, Any, TYPE_CHECKING
from config import Config
from risk_manager import RiskManager
from analytics_engine import AnalyticsEngine
from timeframe_trend_manager import TimeframeTrendManager

if TYPE_CHECKING:
    from trading_engine import TradingEngine

class TelegramBot:
    def __init__(self, config: Config):
        self.config = config
        self.token = config["telegram_token"]
        self.chat_id = config["telegram_chat_id"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        self.trend_manager = None
        
        self.command_handlers = {
            "/start": self.handle_start,
            "/status": self.handle_status,
            "/pause": self.handle_pause,
            "/resume": self.handle_resume,
            "/performance": self.handle_performance,
            "/stats": self.handle_stats,
            "/trades": self.handle_trades,
            "/logic1_on": self.handle_logic1_on,
            "/logic1_off": self.handle_logic1_off,
            "/logic2_on": self.handle_logic2_on,
            "/logic2_off": self.handle_logic2_off,
            "/logic3_on": self.handle_logic3_on,
            "/logic3_off": self.handle_logic3_off,
            "/logic_status": self.handle_logic_status,
            "/performance_report": self.handle_performance_report,
            "/pair_report": self.handle_pair_report,
            "/strategy_report": self.handle_strategy_report,
            # Trend commands
            "/set_trend": self.handle_set_trend,
            "/set_auto": self.handle_set_auto,  # NEW COMMAND
            "/show_trends": self.handle_show_trends,
            "/trend_matrix": self.handle_trend_matrix,
            "/trend_mode": self.handle_trend_mode,  # NEW COMMAND
            "/lot_size_status": self.handle_lot_size_status,
            "/set_lot_size": self.handle_set_lot_size,
            "/chains": self.handle_chains_status,
            "/signal_status": self.handle_signal_status
        }
        self.risk_manager = None
        self.trading_engine = None
        self.analytics_engine = AnalyticsEngine()

    def set_dependencies(self, risk_manager: RiskManager, trading_engine: 'TradingEngine'):
        """Set dependent modules"""
        self.risk_manager = risk_manager
        self.trading_engine = trading_engine

    def set_trend_manager(self, trend_manager: TimeframeTrendManager):
        """Set trend manager"""
        self.trend_manager = trend_manager
        print("✅ Trend manager set in Telegram bot")

    def send_message(self, message: str):
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {str(e)}")
            return False

    def handle_start(self, message):
        """Handle /start command"""
        welcome_msg = (
            "🤖 <b>Zepix Trading Bot v2.0</b>\n\n"
            "✅ Bot is active with enhanced features\n"
            "📊 1:1 Risk-Reward System Active\n"
            "🔄 Re-entry System Enabled\n\n"
            "<b>Core Commands:</b>\n"
            "/status - Complete bot status\n"
            "/signal_status - Live signal status\n"
            "/pause - Pause trading\n"
            "/resume - Resume trading\n\n"
            "<b>Performance:</b>\n"
            "/performance - Trading performance\n"
            "/stats - Risk statistics\n"
            "/trades - Open trades\n"
            "/chains - Re-entry chains\n\n"
            "<b>Logic Control:</b>\n"
            "/logic_status - Check logic status\n"
            "/logic1_on/off - Control Logic 1\n"
            "/logic2_on/off - Control Logic 2\n"
            "/logic3_on/off - Control Logic 3\n\n"
            "<b>Trend Management:</b>\n"
            "/set_trend SYMBOL TIMEFRAME TREND - Set MANUAL trend\n"
            "/set_auto SYMBOL TIMEFRAME - Set AUTO mode (TradingView updates)\n"
            "/trend_mode SYMBOL TIMEFRAME - Check current mode\n"
            "/show_trends - View all trends\n"
            "/trend_matrix - Complete trend matrix\n\n"
            "<b>Risk Management:</b>\n"
            "/lot_size_status - Current lot settings\n"
            "/set_lot_size TIER LOT - Override lot size"
        )
        self.send_message(welcome_msg)

    def handle_status(self, message):
        """Handle /status command with enhanced display"""
        if not self.trading_engine or not self.risk_manager:
            self.send_message("❌ Bot not initialized")
            return
        
        stats = self.risk_manager.get_stats()
        
        # Get current trends for major symbol
        xau_trends = self.trend_manager.get_all_trends("XAUUSD") if self.trend_manager else {}
        
        # Check logic alignments
        logic_alignments = {}
        if self.trend_manager:
            for logic in ["LOGIC1", "LOGIC2", "LOGIC3"]:
                alignment = self.trend_manager.check_logic_alignment("XAUUSD", logic)
                logic_alignments[logic] = alignment["direction"]
        
        status_msg = (
            "📊 <b>Bot Status</b>\n\n"
            f"🔸 Trading: {'⏸️ PAUSED' if self.trading_engine.is_paused else '✅ ACTIVE'}\n"
            f"🔸 Simulation: {'✅ ON' if self.config['simulate_orders'] else '❌ OFF'}\n"
            f"🔸 MT5: {'✅ Connected' if self.trading_engine.mt5_client.initialized else '❌ Disconnected'}\n"
            f"🔸 Balance: ${stats.get('account_balance', 0):.2f}\n"
            f"🔸 Lot Size: {stats.get('current_lot_size', 0.05)}\n\n"
            "<b>Current Modes (XAUUSD):</b>\n"
            f"LOGIC1: {logic_alignments.get('LOGIC1', 'NEUTRAL')}\n"
            f"LOGIC2: {logic_alignments.get('LOGIC2', 'NEUTRAL')}\n"
            f"LOGIC3: {logic_alignments.get('LOGIC3', 'NEUTRAL')}\n\n"
            "<b>Live Signals (XAUUSD):</b>\n"
            f"5min: {xau_trends.get('5m', 'NA')}\n"
            f"15min: {xau_trends.get('15m', 'NA')}\n"
            f"1H: {xau_trends.get('1h', 'NA')}\n"
            f"1D: {xau_trends.get('1d', 'NA')}"
        )
        self.send_message(status_msg)

    # NEW COMMAND: Set Auto Mode
    def handle_set_auto(self, message):
        """Set trend back to AUTO mode"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
            
        try:
            parts = message['text'].split()
            
            if len(parts) < 3:
                self.send_message(
                    "📝 <b>Usage:</b> /set_auto SYMBOL TIMEFRAME\n\n"
                    "<b>Symbols:</b> XAUUSD, EURUSD, GBPUSD, etc.\n"
                    "<b>Timeframes:</b> 5m, 15m, 1h, 1d\n\n"
                    "<b>Example:</b> /set_auto XAUUSD 1h\n"
                    "This allows TradingView signals to auto-update this trend"
                )
                return
            
            symbol = parts[1].upper()
            timeframe = parts[2].lower()
            
            valid_timeframes = ['5m', '15m', '1h', '1d']
            if timeframe not in valid_timeframes:
                self.send_message(f"❌ Invalid timeframe. Use: {', '.join(valid_timeframes)}")
                return
            
            self.trend_manager.set_auto_trend(symbol, timeframe)
            current_trend = self.trend_manager.get_trend(symbol, timeframe)
            current_mode = self.trend_manager.get_mode(symbol, timeframe)
            
            self.send_message(f"🔄 <b>Auto Mode Enabled</b>\n"
                            f"{symbol} {timeframe} → {current_trend} ({current_mode})\n"
                            f"📡 Now accepting TradingView signals")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    # NEW COMMAND: Check Trend Mode
    def handle_trend_mode(self, message):
        """Check current trend mode"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
            
        try:
            parts = message['text'].split()
            
            if len(parts) < 3:
                self.send_message(
                    "📝 <b>Usage:</b> /trend_mode SYMBOL TIMEFRAME\n\n"
                    "<b>Example:</b> /trend_mode XAUUSD 1h"
                )
                return
            
            symbol = parts[1].upper()
            timeframe = parts[2].lower()
            
            current_trend = self.trend_manager.get_trend(symbol, timeframe)
            current_mode = self.trend_manager.get_mode(symbol, timeframe)
            
            mode_info = "🔄 AUTO (TradingView updates)" if current_mode == "AUTO" else "🔒 MANUAL (Locked)"
            
            self.send_message(f"📊 <b>Trend Mode</b>\n"
                            f"Symbol: {symbol}\n"
                            f"Timeframe: {timeframe}\n"
                            f"Trend: {current_trend}\n"
                            f"Mode: {mode_info}")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_trend(self, message):
        """Handle /set_trend command - SETS MANUAL MODE"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
            
        try:
            parts = message['text'].split()
            
            if len(parts) < 4:
                self.send_message(
                    "📝 <b>Usage:</b> /set_trend SYMBOL TIMEFRAME TREND\n\n"
                    "<b>Symbols:</b> XAUUSD, EURUSD, GBPUSD, etc.\n"
                    "<b>Timeframes:</b> 5m, 15m, 1h, 1d\n"
                    "<b>Trends:</b> BULLISH, BEARISH, NEUTRAL\n\n"
                    "⚠️ <b>This sets MANUAL mode</b> - TradingView signals won't auto-update\n"
                    "Use /set_auto to allow auto updates\n\n"
                    "<b>Example:</b> /set_trend XAUUSD 1h BULLISH"
                )
                return
            
            symbol = parts[1].upper()
            timeframe = parts[2].lower()
            trend = parts[3].upper()
            
            valid_timeframes = ['5m', '15m', '1h', '1d']
            if timeframe not in valid_timeframes:
                self.send_message(f"❌ Invalid timeframe. Use: {', '.join(valid_timeframes)}")
                return
            
            if trend not in ["BULLISH", "BEARISH", "NEUTRAL"]:
                self.send_message("❌ Trend must be BULLISH, BEARISH, or NEUTRAL")
                return
            
            self.trend_manager.set_manual_trend(symbol, timeframe, trend)
            
            # Verify the trend was set
            current_trend = self.trend_manager.get_trend(symbol, timeframe)
            current_mode = self.trend_manager.get_mode(symbol, timeframe)
            
            self.send_message(f"🔒 <b>Manual Trend Set</b>\n"
                            f"{symbol} {timeframe} → {current_trend} ({current_mode})\n"
                            f"⚠️ TradingView signals won't auto-update this\n"
                            f"Use /set_auto {symbol} {timeframe} to allow auto updates")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_show_trends(self, message):
        """Handle /show_trends command"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
        
        msg = "📊 <b>Current Trends</b>\n\n"
        for symbol in symbols:
            trends = self.trend_manager.get_all_trends_with_mode(symbol)
            has_non_neutral = any(trend_data["trend"] != "NEUTRAL" for trend_data in trends.values())
            
            if has_non_neutral:
                msg += f"<b>{symbol}:</b>\n"
                for tf, trend_data in trends.items():
                    if trend_data["trend"] != "NEUTRAL":
                        mode_icon = "🔒" if trend_data["mode"] == "MANUAL" else "🔄"
                        msg += f"  {tf}: {trend_data['trend']} {mode_icon}\n"
                msg += "─────────────\n"
        
        self.send_message(msg)

    def handle_trend_matrix(self, message):
        """Show complete trend matrix for all symbols"""
        if not self.trend_manager:
            self.send_message("❌ Trend manager not initialized")
            return
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
        
        msg = "🎯 <b>Complete Trend Matrix</b>\n\n"
        
        for symbol in symbols:
            msg += f"<b>{symbol}</b>\n"
            trends = self.trend_manager.get_all_trends_with_mode(symbol)
            
            # Show individual timeframes with mode
            for tf in ["5m", "15m", "1h", "1d"]:
                trend_data = trends.get(tf, {"trend": "NEUTRAL", "mode": "AUTO"})
                trend = trend_data["trend"]
                mode = trend_data["mode"]
                
                emoji = "🟢" if trend == "BULLISH" else "🔴" if trend == "BEARISH" else "⚪"
                mode_icon = "🔒" if mode == "MANUAL" else "🔄"
                
                msg += f"  {tf}: {emoji} {trend} {mode_icon}\n"
            
            # Show logic alignments
            for logic in ["LOGIC1", "LOGIC2", "LOGIC3"]:
                alignment = self.trend_manager.check_logic_alignment(symbol, logic)
                if alignment["aligned"]:
                    msg += f"  ✅ {logic}: {alignment['direction']}\n"
            
            msg += "─────────────\n"
        
        msg += "\n<b>Legend:</b> 🟢BULLISH 🔴BEARISH ⚪NEUTRAL 🔒MANUAL 🔄AUTO"
        self.send_message(msg)

    # ... (rest of the existing functions remain the same - handle_pause, handle_resume, etc.)
    def handle_pause(self, message):
        """Handle /pause command"""
        if self.trading_engine:
            self.trading_engine.is_paused = True
            self.send_message("⏸️ <b>Trading PAUSED</b>\nNo new trades will be executed")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_resume(self, message):
        """Handle /resume command"""
        if self.trading_engine:
            self.trading_engine.is_paused = False
            self.send_message("✅ <b>Trading RESUMED</b>\nReady to execute new trades")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_performance(self, message):
        """Handle /performance command"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
            
        stats = self.risk_manager.get_stats()
        performance_msg = (
            "📈 <b>Trading Performance</b>\n\n"
            f"🔸 Total Trades: {stats['total_trades']}\n"
            f"🔸 Winning Trades: {stats['winning_trades']}\n"
            f"🔸 Win Rate: {stats['win_rate']:.1f}%\n\n"
            f"💰 Today's PnL: ${stats['daily_profit'] - stats['daily_loss']:.2f}\n"
            f"📊 Daily Profit: ${stats['daily_profit']:.2f}\n"
            f"📉 Daily Loss: ${stats['daily_loss']:.2f}\n"
            f"🔻 Lifetime Loss: ${stats['lifetime_loss']:.2f}"
        )
        self.send_message(performance_msg)

    def handle_stats(self, message):
        """Handle /stats command"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
            
        stats = self.risk_manager.get_stats()
        risk_msg = (
            "⚠️ <b>Risk Management</b>\n\n"
            f"🔸 Risk Tier: ${stats['current_risk_tier']}\n"
            f"🔸 Daily Loss Limit: ${stats['risk_parameters']['daily_loss_limit']}\n"
            f"🔸 Max Total Loss: ${stats['risk_parameters']['max_total_loss']}\n\n"
            f"📊 Daily Loss: ${stats['daily_loss']:.2f}/{stats['risk_parameters']['daily_loss_limit']}\n"
            f"🔻 Lifetime Loss: ${stats['lifetime_loss']:.2f}/{stats['risk_parameters']['max_total_loss']}\n\n"
            f"📦 Current Lot Size: {stats['current_lot_size']}"
        )
        self.send_message(risk_msg)

    def handle_trades(self, message):
        """Handle /trades command"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        if not self.trading_engine.open_trades:
            self.send_message("📭 <b>No Open Trades</b>")
            return
        
        trades_msg = "📊 <b>Open Trades</b>\n\n"
        for i, trade in enumerate(self.trading_engine.open_trades, 1):
            if trade.status != "closed":
                chain_info = f" [RE-{trade.chain_level}]" if trade.is_re_entry else ""
                trades_msg += (
                    f"<b>Trade #{i}{chain_info}</b>\n"
                    f"Symbol: {trade.symbol} | {trade.direction.upper()}\n"
                    f"Strategy: {trade.strategy}\n"
                    f"Entry: {trade.entry:.5f} | SL: {trade.sl:.5f}\n"
                    f"TP: {trade.tp:.5f} | RR: 1:1\n"
                    f"Lot: {trade.lot_size:.2f}\n"
                    "────────────────────\n"
                )
        
        self.send_message(trades_msg)

    def handle_chains_status(self, message):
        """Show active re-entry chains"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
        
        chains = self.trading_engine.reentry_manager.active_chains
        
        if not chains:
            self.send_message("🔗 <b>No Active Re-entry Chains</b>")
            return
        
        msg = "🔗 <b>Active Re-entry Chains</b>\n\n"
        for chain_id, chain in chains.items():
            msg += (
                f"<b>{chain.symbol} - {chain.direction.upper()}</b>\n"
                f"Level: {chain.current_level}/{chain.max_level}\n"
                f"Total Profit: ${chain.total_profit:.2f}\n"
                f"Status: {chain.status}\n"
                "────────────────────\n"
            )
        
        self.send_message(msg)

    # Logic control handlers
    def handle_logic1_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(1)
            self.send_message("✅ LOGIC 1 TRADING ENABLED")

    def handle_logic1_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(1)
            self.send_message("⛔ LOGIC 1 TRADING DISABLED")

    def handle_logic2_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(2)
            self.send_message("✅ LOGIC 2 TRADING ENABLED")

    def handle_logic2_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(2)
            self.send_message("⛔ LOGIC 2 TRADING DISABLED")

    def handle_logic3_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(3)
            self.send_message("✅ LOGIC 3 TRADING ENABLED")

    def handle_logic3_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(3)
            self.send_message("⛔ LOGIC 3 TRADING DISABLED")

    def handle_logic_status(self, message):
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        status = self.trading_engine.get_logic_status()
        status_msg = (
            "🤖 <b>LOGIC STATUS:</b>\n\n"
            f"LOGIC 1 (1H+15M→5M): {'✅ ENABLED' if status['logic1'] else '❌ DISABLED'}\n"
            f"LOGIC 2 (1H+15M→15M): {'✅ ENABLED' if status['logic2'] else '❌ DISABLED'}\n"
            f"LOGIC 3 (1D+1H→1H): {'✅ ENABLED' if status['logic3'] else '❌ DISABLED'}\n\n"
            "Use /logic1_on, /logic1_off, etc. to control"
        )
        self.send_message(status_msg)

    def handle_lot_size_status(self, message):
        """Show current lot size settings"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
        
        balance = self.risk_manager.mt5_client.get_account_balance()
        current_lot = self.risk_manager.get_fixed_lot_size(balance)
        tier = self.risk_manager.get_risk_tier(balance)
        
        msg = (
            "📦 <b>Lot Size Configuration</b>\n\n"
            f"Account Balance: ${balance:.2f}\n"
            f"Current Tier: ${tier}\n"
            f"Current Lot Size: {current_lot:.2f}\n\n"
            "<b>Tier Settings:</b>\n"
            "$5,000 → 0.05 lots\n"
            "$10,000 → 0.10 lots\n"
            "$25,000 → 1.00 lots\n"
            "$100,000 → 5.00 lots\n\n"
            "Use /set_lot_size TIER LOT to override"
        )
        self.send_message(msg)

    def handle_set_lot_size(self, message):
        """Handle manual lot size override"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
        
        try:
            parts = message['text'].split()
            
            if len(parts) < 3:
                self.send_message(
                    "📝 <b>Usage:</b> /set_lot_size TIER LOT\n\n"
                    "<b>Example:</b> /set_lot_size 10000 0.15\n"
                    "This sets 0.15 lots for $10,000 tier"
                )
                return
            
            tier = int(parts[1])
            lot_size = float(parts[2])
            
            valid_tiers = [5000, 10000, 25000, 100000]
            if tier not in valid_tiers:
                self.send_message(f"❌ Invalid tier. Use: {', '.join(map(str, valid_tiers))}")
                return
            
            if lot_size <= 0 or lot_size > 10:
                self.send_message("❌ Lot size must be between 0.01 and 10.00")
                return
            
            self.risk_manager.set_manual_lot_size(tier, lot_size)
            self.send_message(f"✅ Lot size override: ${tier} → {lot_size:.2f} lots")
            
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    # Analytics handlers
    def handle_performance_report(self, message):
        report = self.analytics_engine.get_performance_report()
        msg = f"📊 Performance Report (30 Days)\n\n"
        msg += f"Total Trades: {report['total_trades']}\n"
        msg += f"Win Rate: {report['win_rate']:.1f}%\n"
        msg += f"Total PnL: ${report['total_pnl']:.2f}\n"
        msg += f"Avg Win: ${report['average_win']:.2f}\n"
        msg += f"Avg Loss: ${report['average_loss']:.2f}"
        self.send_message(msg)

    def handle_pair_report(self, message):
        pair_stats = self.analytics_engine.get_pair_performance()
        msg = "📈 Pair Performance\n\n"
        for symbol, stats in pair_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            msg += f"{symbol}: {stats['trades']} trades, ${stats['pnl']:.2f}, {win_rate:.1f}% WR\n"
        self.send_message(msg)

    def handle_strategy_report(self, message):
        strategy_stats = self.analytics_engine.get_strategy_performance()
        msg = "🤖 Strategy Performance\n\n"
        for strategy, stats in strategy_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            msg += f"{strategy}: {stats['trades']} trades, ${stats['pnl']:.2f}, {win_rate:.1f}% WR\n"
        self.send_message(msg)

    def handle_signal_status(self, message):
        """Show current signal status for all symbols"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
        
        msg = "📡 <b>Current Signal Status</b>\n\n"
        
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
        
        for symbol in symbols:
            if symbol in self.trading_engine.current_signals:
                signals = self.trading_engine.current_signals[symbol]
                msg += f"<b>{symbol}:</b>\n"
                msg += f"  5m: {signals.get('5m', 'NA')}\n"
                msg += f"  15m: {signals.get('15m', 'NA')}\n"
                msg += f"  1h: {signals.get('1h', 'NA')}\n"
                msg += f"  1d: {signals.get('1d', 'NA')}\n"
            else:
                msg += f"<b>{symbol}:</b> No signals yet\n"
            msg += "─────────────\n"
        
        self.send_message(msg)

    def start_polling(self):
        """Start polling for Telegram commands"""
        def poll_commands():
            offset = 0
            while True:
                try:
                    url = f"{self.base_url}/getUpdates?offset={offset}&timeout=30"
                    response = requests.get(url, timeout=35)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("ok"):
                            print(f"Telegram API error: {data}")
                            time.sleep(10)
                            continue5rt 
                            
                        updates = data.get("result", [])
                        
                        for update in updates:
                            offset = update["update_id"] + 1
                            
                            if "message" in update and "text" in update["message"]:
                                message_data = update["message"]
                                user_id = message_data["from"]["id"]
                                text = message_data["text"].strip()
                                
                                if user_id == self.config["allowed_telegram_user"]:
                                    command_parts = text.split()
                                    if command_parts:
                                        command = command_parts[0]
                                        
                                        if command in self.command_handlers:
                                            try:
                                                self.command_handlers[command](message_data)
                                            except Exception as e:
                                                error_msg = f"❌ Error executing {command}: {str(e)}"
                                                self.send_message(error_msg)
                                                print(f"Command error: {e}")
                
                except Exception as e:
                    print(f"Telegram polling error: {str(e)}")
                    time.sleep(10)
        
        thread = threading.Thread(target=poll_commands, daemon=True)
        thread.start()
        print("✅ Telegram bot polling started")