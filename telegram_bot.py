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
            "/set_auto": self.handle_set_auto,
            "/show_trends": self.handle_show_trends,
            "/trend_matrix": self.handle_trend_matrix,
            "/trend_mode": self.handle_trend_mode,
            "/lot_size_status": self.handle_lot_size_status,
            "/set_lot_size": self.handle_set_lot_size,
            "/chains": self.handle_chains_status,
            "/signal_status": self.handle_signal_status,
            "/clear_loss_data": self.handle_clear_loss_data,
            "/tp_system": self.handle_tp_system,
            "/sl_hunt": self.handle_sl_hunt,
            "/exit_continuation": self.handle_exit_continuation,
            "/tp_report": self.handle_tp_report,
            # New configuration commands
            "/simulation_mode": self.handle_simulation_mode,
            "/reentry_config": self.handle_reentry_config,
            "/set_monitor_interval": self.handle_set_monitor_interval,
            "/set_sl_offset": self.handle_set_sl_offset,
            "/set_cooldown": self.handle_set_cooldown,
            "/set_recovery_time": self.handle_set_recovery_time,
            "/set_max_levels": self.handle_set_max_levels,
            "/set_sl_reduction": self.handle_set_sl_reduction,
            "/reset_reentry_config": self.handle_reset_reentry_config,
            "/view_sl_config": self.handle_view_sl_config,
            "/set_symbol_sl": self.handle_set_symbol_sl,
            "/update_volatility": self.handle_update_volatility,
            "/view_risk_caps": self.handle_view_risk_caps,
            "/set_daily_cap": self.handle_set_daily_cap,
            "/set_lifetime_cap": self.handle_set_lifetime_cap,
            "/set_risk_tier": self.handle_set_risk_tier
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
        rr_ratio = self.config.get("rr_ratio", 1.0)
        re_entry = self.config.get("re_entry_config", {})
        welcome_msg = (
            "🤖 <b>Zepix Trading Bot v2.0</b>\n"
            "✅ Bot is active with enhanced features\n"
            f"📊 1:{rr_ratio} Risk-Reward System Active\n"
            "🔄 Re-entry System Enabled\n"
            "🔄 SL Hunt Re-entry System Enabled\n"
            "⚡ Live Price Advanced System Working\n\n"
            
            "<b>📊 TRADING CONTROL</b>\n"
            "/status - Bot &amp; trade status\n"
            "/pause - Pause trading\n"
            "/resume - Resume trading\n"
            "/signal_status - Live signals\n"
            "/simulation_mode [on/off] - Toggle simulation mode\n\n"
            
            "<b>📈 PERFORMANCE &amp; ANALYTICS</b>\n"
            "/performance - Trading metrics\n"
            "/stats - Risk statistics\n"
            "/trades - Open positions\n"
            "/chains - Re-entry chains\n\n"
            
            "<b>⚙️ STRATEGY CONTROL</b>\n"
            "/logic_status - View all logic status\n"
            "/logic1_on, /logic1_off - 1H+15M→5M\n"
            "/logic2_on, /logic2_off - 1H+15M→15M\n"
            "/logic3_on, /logic3_off - D+1H→1H\n\n"
            
            "<b>🔄 ADVANCED RE-ENTRY SYSTEM</b>\n"
            "/tp_system [on/off/status] - TP continuation\n"
            "/sl_hunt [on/off/status] - SL hunt re-entry\n"
            "/tp_report - 30-day re-entry stats\n"
            "/reentry_config - View all re-entry settings\n"
            "/set_monitor_interval [30-300] - Price monitor interval\n"
            "/set_sl_offset [1-5] - SL hunt offset pips\n"
            "/set_cooldown [30-300] - SL hunt cooldown\n"
            "/set_recovery_time [1-10] - Price recovery window\n"
            "/set_max_levels [1-5] - Max chain levels\n"
            "/set_sl_reduction [0.3-0.7] - SL reduction %\n"
            "/reset_reentry_config - Reset to defaults\n\n"
            
            "<b>📍 TREND MANAGEMENT</b>\n"
            "/show_trends - All trends\n"
            "/trend_matrix - Complete matrix\n"
            "/set_trend SYMBOL TF TREND - Manual trend\n"
            "/set_auto SYMBOL TF - Auto mode\n"
            "/trend_mode SYMBOL TF - Check mode\n\n"
            
            "<b>💰 RISK &amp; LOT MANAGEMENT</b>\n"
            "/view_risk_caps - Daily/Lifetime caps &amp; loss\n"
            "/set_daily_cap [amount] - Set daily limit\n"
            "/set_lifetime_cap [amount] - Set lifetime limit\n"
            "/set_risk_tier BALANCE DAILY LIFETIME - Complete tier\n"
            "/clear_loss_data - Reset lifetime loss\n\n"
            "/view_sl_config - Symbol SL settings\n"
            "/set_symbol_sl SYMBOL VOL SL - Update symbol SL\n"
            "/update_volatility SYMBOL LEVEL - Quick volatility\n\n"
            "/lot_size_status - Lot settings\n"
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
        
        rr_ratio = self.config.get("rr_ratio", 1.0)
        trades_msg = "📊 <b>Open Trades</b>\n\n"
        for i, trade in enumerate(self.trading_engine.open_trades, 1):
            if trade.status != "closed":
                chain_info = f" [RE-{trade.chain_level}]" if trade.is_re_entry else ""
                trades_msg += (
                    f"<b>Trade #{i}{chain_info}</b>\n"
                    f"Symbol: {trade.symbol} | {trade.direction.upper()}\n"
                    f"Strategy: {trade.strategy}\n"
                    f"Entry: {trade.entry:.5f} | SL: {trade.sl:.5f}\n"
                    f"TP: {trade.tp:.5f} | RR: 1:{rr_ratio}\n"
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
        if not self.risk_manager or not self.risk_manager.mt5_client:
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
    
    def handle_clear_loss_data(self, message):
        """Clear lifetime loss data"""
        if not self.risk_manager or not self.trading_engine:
            self.send_message("❌ Bot not initialized")
            return
        
        try:
            self.risk_manager.reset_lifetime_loss()
            self.trading_engine.db.clear_lifetime_losses()
            self.send_message("✅ Lifetime loss data cleared successfully")
        except Exception as e:
            self.send_message(f"❌ Error clearing loss data: {str(e)}")
    
    def handle_tp_system(self, message):
        """Control TP re-entry system: /tp_system [on/off/status]"""
        try:
            parts = message["text"].strip().split()
            
            re_entry_config = self.config.get("re_entry_config", {})
            
            if len(parts) < 2:
                enabled = re_entry_config.get("tp_reentry_enabled", False)
                status_emoji = "✅" if enabled else "❌"
                msg = (
                    f"{status_emoji} <b>TP Re-entry System</b>\n\n"
                    f"Status: {'ENABLED' if enabled else 'DISABLED'}\n"
                    f"Chain Levels: {re_entry_config.get('max_reentry_levels', 3)}\n"
                    f"SL Reduction: {re_entry_config.get('sl_reduction_per_level', 0.5)*100:.0f}% per level\n\n"
                    "<b>Usage:</b>\n"
                    "/tp_system on - Enable TP re-entry\n"
                    "/tp_system off - Disable TP re-entry\n"
                    "/tp_system status - Show this status"
                )
                self.send_message(msg)
                return
            
            action = parts[1].lower()
            
            if action == "on":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["tp_reentry_enabled"] = True
                self.send_message("✅ TP re-entry system ENABLED")
            elif action == "off":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["tp_reentry_enabled"] = False
                self.send_message("❌ TP re-entry system DISABLED")
            elif action == "status":
                self.handle_tp_system({"text": "/tp_system"})
            else:
                self.send_message("❌ Invalid action. Use: on, off, or status")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_sl_hunt(self, message):
        """Control SL hunt re-entry system: /sl_hunt [on/off/status]"""
        try:
            parts = message["text"].strip().split()
            
            re_entry_config = self.config.get("re_entry_config", {})
            
            if len(parts) < 2:
                enabled = re_entry_config.get("sl_hunt_reentry_enabled", False)
                status_emoji = "✅" if enabled else "❌"
                msg = (
                    f"{status_emoji} <b>SL Hunt Re-entry System</b>\n\n"
                    f"Status: {'ENABLED' if enabled else 'DISABLED'}\n"
                    f"Offset Pips: {re_entry_config.get('sl_hunt_offset_pips', 1)}\n"
                    f"Cooldown: {re_entry_config.get('sl_hunt_cooldown_seconds', 60)}s\n"
                    f"Price Check: {re_entry_config.get('price_recovery_check_minutes', 2)} min\n\n"
                    "<b>Usage:</b>\n"
                    "/sl_hunt on - Enable SL hunt re-entry\n"
                    "/sl_hunt off - Disable SL hunt re-entry\n"
                    "/sl_hunt status - Show this status"
                )
                self.send_message(msg)
                return
            
            action = parts[1].lower()
            
            if action == "on":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["sl_hunt_reentry_enabled"] = True
                self.send_message("✅ SL hunt re-entry system ENABLED")
            elif action == "off":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["sl_hunt_reentry_enabled"] = False
                self.send_message("❌ SL hunt re-entry system DISABLED")
            elif action == "status":
                self.handle_sl_hunt({"text": "/sl_hunt"})
            else:
                self.send_message("❌ Invalid action. Use: on, off, or status")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_exit_continuation(self, message):
        """Control Exit Continuation system: /exit_continuation [on/off/status]"""
        try:
            parts = message["text"].strip().split()
            
            re_entry_config = self.config.get("re_entry_config", {})
            
            if len(parts) < 2:
                enabled = re_entry_config.get("exit_continuation_enabled", True)
                status_emoji = "✅" if enabled else "❌"
                msg = (
                    f"{status_emoji} <b>Exit Continuation System</b>\n\n"
                    f"Status: {'ENABLED' if enabled else 'DISABLED'}\n"
                    f"Price Gap: {re_entry_config.get('tp_continuation_price_gap_pips', 2)} pips\n"
                    f"Monitor Interval: {re_entry_config.get('price_monitor_interval_seconds', 30)}s\n\n"
                    f"<b>What it does:</b>\n"
                    f"• After Exit Appeared signal → Profit book\n"
                    f"• Continue monitoring with price gap\n"
                    f"• Auto re-entry if price & alignment match\n"
                    f"• Works for: EXIT_APPEARED, REVERSAL, TREND_REVERSAL, OPPOSITE_SIGNAL\n\n"
                    "<b>Usage:</b>\n"
                    "/exit_continuation on - Enable continuation\n"
                    "/exit_continuation off - Disable continuation\n"
                    "/exit_continuation status - Show this status"
                )
                self.send_message(msg)
                return
            
            action = parts[1].lower()
            
            if action == "on":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["exit_continuation_enabled"] = True
                self.send_message("✅ Exit continuation system ENABLED\n\n"
                                "Bot will monitor for re-entry after exit signals with price gap")
            elif action == "off":
                if "re_entry_config" in self.config.config:
                    self.config.config["re_entry_config"]["exit_continuation_enabled"] = False
                self.send_message("❌ Exit continuation system DISABLED\n\n"
                                "Bot will stop monitoring after exit signals")
            elif action == "status":
                self.handle_exit_continuation({"text": "/exit_continuation"})
            else:
                self.send_message("❌ Invalid action. Use: on, off, or status")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
    
    def handle_tp_report(self, message):
        """Show TP re-entry statistics and performance"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
        
        try:
            tp_stats = self.trading_engine.db.get_tp_reentry_stats()
            sl_stats = self.trading_engine.db.get_sl_hunt_reentry_stats()
            reversal_stats = self.trading_engine.reversal_handler.get_reversal_exit_stats()
            
            msg = "📊 <b>Advanced Re-entry Report (30 Days)</b>\n\n"
            
            msg += "<b>TP Re-entry System:</b>\n"
            msg += f"Total TP Re-entries: {tp_stats.get('total_tp_reentries', 0)}\n"
            msg += f"Profitable: {tp_stats.get('profitable_tp_reentries', 0)}\n"
            msg += f"Total PnL: ${tp_stats.get('total_tp_reentry_pnl', 0):.2f}\n"
            msg += f"Avg PnL: ${tp_stats.get('avg_tp_reentry_pnl', 0):.2f}\n\n"
            
            msg += "<b>SL Hunt Re-entry System:</b>\n"
            msg += f"SL Hunt Attempts: {sl_stats.get('sl_hunt_attempts', 0)}\n"
            msg += f"Successful Re-entries: {sl_stats.get('total_sl_hunt_reentries', 0)}\n\n"
            
            msg += "<b>Reversal Exit System:</b>\n"
            msg += f"Total Reversal Exits: {reversal_stats.get('total_reversal_exits', 0)}\n"
            msg += f"Profitable Exits: {reversal_stats.get('profitable_exits', 0)}\n"
            msg += f"Total PnL: ${reversal_stats.get('total_reversal_pnl', 0):.2f}\n"
            msg += f"Avg PnL: ${reversal_stats.get('avg_reversal_pnl', 0):.2f}"
            
            self.send_message(msg)
            
        except Exception as e:
            self.send_message(f"❌ Error generating report: {str(e)}")

    def handle_simulation_mode(self, message):
        """Toggle simulation mode on/off"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /simulation_mode [on/off]")
                return
            
            mode = parts[1].lower()
            if mode not in ['on', 'off']:
                self.send_message("❌ Invalid mode. Use 'on' or 'off'")
                return
            
            simulate = (mode == 'on')
            self.config.update('simulate_orders', simulate)
            
            status = "ENABLED ✅" if simulate else "DISABLED ❌"
            self.send_message(f"🔄 Simulation Mode: {status}\n\n{'⚠️ Orders will be simulated (not live)' if simulate else '✅ Live trading mode active'}")
        
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_reentry_config(self, message):
        """Display all re-entry configuration settings"""
        re_cfg = self.config.get('re_entry_config', {})
        
        msg = "⚙️ <b>Re-entry System Configuration</b>\n\n"
        msg += f"<b>System Status:</b>\n"
        msg += f"TP Re-entry: {'✅ ON' if re_cfg.get('tp_reentry_enabled', True) else '❌ OFF'}\n"
        msg += f"SL Hunt Re-entry: {'✅ ON' if re_cfg.get('sl_hunt_reentry_enabled', True) else '❌ OFF'}\n"
        msg += f"Reversal Exit: {'✅ ON' if re_cfg.get('reversal_exit_enabled', True) else '❌ OFF'}\n"
        msg += f"Exit Continuation: {'✅ ON' if re_cfg.get('exit_continuation_enabled', True) else '❌ OFF'}\n\n"
        
        msg += f"<b>Timing Settings:</b>\n"
        msg += f"Monitor Interval: {re_cfg.get('price_monitor_interval_seconds', 30)}s\n"
        msg += f"SL Hunt Cooldown: {re_cfg.get('sl_hunt_cooldown_seconds', 60)}s\n"
        msg += f"Recovery Window: {re_cfg.get('price_recovery_check_minutes', 2)} min\n\n"
        
        msg += f"<b>Re-entry Rules:</b>\n"
        msg += f"SL Hunt Offset: {re_cfg.get('sl_hunt_offset_pips', 1.0)} pips\n"
        msg += f"Max Chain Levels: {re_cfg.get('max_chain_levels', 2)}\n"
        msg += f"SL Reduction: {int(re_cfg.get('sl_reduction_per_level', 0.5) * 100)}%"
        
        self.send_message(msg)

    def handle_set_monitor_interval(self, message):
        """Set price monitor interval (30-300 seconds)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_monitor_interval [30-300]")
                return
            
            interval = int(parts[1])
            if not (30 <= interval <= 300):
                self.send_message("❌ Interval must be between 30-300 seconds")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['price_monitor_interval_seconds'] = interval
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ Price monitor interval set to {interval}s")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_monitor_interval [30-300]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_sl_offset(self, message):
        """Set SL hunt offset pips (1-5)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_sl_offset [1-5]")
                return
            
            offset = float(parts[1])
            if not (1 <= offset <= 5):
                self.send_message("❌ Offset must be between 1-5 pips")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['sl_hunt_offset_pips'] = offset
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ SL hunt offset set to {offset} pips")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_sl_offset [1-5]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_cooldown(self, message):
        """Set SL hunt cooldown (30-300 seconds)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_cooldown [30-300]")
                return
            
            cooldown = int(parts[1])
            if not (30 <= cooldown <= 300):
                self.send_message("❌ Cooldown must be between 30-300 seconds")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['sl_hunt_cooldown_seconds'] = cooldown
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ SL hunt cooldown set to {cooldown}s")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_cooldown [30-300]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_recovery_time(self, message):
        """Set price recovery window (1-10 minutes)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_recovery_time [1-10]")
                return
            
            minutes = int(parts[1])
            if not (1 <= minutes <= 10):
                self.send_message("❌ Recovery time must be between 1-10 minutes")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['price_recovery_check_minutes'] = minutes
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ Price recovery window set to {minutes} minutes")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_recovery_time [1-10]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_max_levels(self, message):
        """Set max re-entry chain levels (1-5)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_max_levels [1-5]")
                return
            
            levels = int(parts[1])
            if not (1 <= levels <= 5):
                self.send_message("❌ Max levels must be between 1-5")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['max_chain_levels'] = levels
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ Max re-entry levels set to {levels}")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_max_levels [1-5]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_sl_reduction(self, message):
        """Set SL reduction percentage (0.3-0.7 = 30%-70%)"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_sl_reduction [0.3-0.7]")
                return
            
            reduction = float(parts[1])
            if not (0.3 <= reduction <= 0.7):
                self.send_message("❌ Reduction must be between 0.3-0.7 (30%-70%)")
                return
            
            re_cfg = self.config.get('re_entry_config', {})
            re_cfg['sl_reduction_per_level'] = reduction
            self.config.update('re_entry_config', re_cfg)
            
            self.send_message(f"✅ SL reduction set to {int(reduction * 100)}% per level")
        
        except ValueError:
            self.send_message("❌ Invalid number. Use: /set_sl_reduction [0.3-0.7]")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_reset_reentry_config(self, message):
        """Reset all re-entry settings to defaults"""
        default_re_cfg = {
            "max_chain_levels": 2,
            "sl_reduction_per_level": 0.5,
            "recovery_window_minutes": 30,
            "min_time_between_re_entries": 60,
            "sl_hunt_offset_pips": 1.0,
            "tp_reentry_enabled": True,
            "sl_hunt_reentry_enabled": True,
            "reversal_exit_enabled": True,
            "price_monitor_interval_seconds": 30,
            "tp_continuation_price_gap_pips": 2.0,
            "sl_hunt_cooldown_seconds": 60,
            "price_recovery_check_minutes": 2
        }
        
        self.config.update('re_entry_config', default_re_cfg)
        self.send_message("✅ Re-entry config reset to defaults:\n\n"
                         "Monitor Interval: 30s\n"
                         "SL Offset: 1 pip\n"
                         "Cooldown: 60s\n"
                         "Recovery: 2 min\n"
                         "Max Levels: 2\n"
                         "SL Reduction: 50%")

    def handle_view_sl_config(self, message):
        """Display all symbol SL configurations"""
        symbols = self.config.get('symbol_config', {})
        
        msg = "📊 <b>Symbol SL Configuration</b>\n\n"
        
        for symbol, cfg in symbols.items():
            volatility = cfg.get('volatility', 'MEDIUM')
            min_sl = cfg.get('min_sl_distance', 0)
            pip_size = cfg.get('pip_size', 0)
            
            pips = round(min_sl / pip_size) if pip_size > 0 else 0
            
            msg += f"<b>{symbol}</b>\n"
            msg += f"  Volatility: {volatility}\n"
            msg += f"  Min SL Distance: {min_sl}\n"
            msg += f"  Min SL (Pips): {pips} pips\n"
            msg += f"  Pip Size: {pip_size}\n\n"
        
        self.send_message(msg)

    def handle_set_symbol_sl(self, message):
        """Set symbol SL configuration - /set_symbol_sl SYMBOL VOLATILITY SL"""
        try:
            parts = message['text'].split()
            if len(parts) != 4:
                self.send_message("❌ Usage: /set_symbol_sl SYMBOL VOLATILITY SL\nExample: /set_symbol_sl XAUUSD HIGH 0.15")
                return
            
            symbol = parts[1].upper()
            volatility = parts[2].upper()
            sl_distance = float(parts[3])
            
            if volatility not in ['LOW', 'MEDIUM', 'HIGH']:
                self.send_message("❌ Volatility must be LOW, MEDIUM, or HIGH")
                return
            
            symbols = self.config.get('symbol_config', {})
            if symbol not in symbols:
                self.send_message(f"❌ Symbol {symbol} not found in config")
                return
            
            symbols[symbol]['volatility'] = volatility
            symbols[symbol]['min_sl_distance'] = sl_distance
            self.config.update('symbol_config', symbols)
            
            self.send_message(f"✅ {symbol} updated:\nVolatility: {volatility}\nMin SL: {sl_distance}")
        
        except ValueError:
            self.send_message("❌ Invalid SL value. Use decimal format (e.g., 0.15)")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_update_volatility(self, message):
        """Quick volatility update - /update_volatility SYMBOL LEVEL"""
        try:
            parts = message['text'].split()
            if len(parts) != 3:
                self.send_message("❌ Usage: /update_volatility SYMBOL LEVEL\nExample: /update_volatility XAUUSD HIGH")
                return
            
            symbol = parts[1].upper()
            volatility = parts[2].upper()
            
            if volatility not in ['LOW', 'MEDIUM', 'HIGH']:
                self.send_message("❌ Volatility must be LOW, MEDIUM, or HIGH")
                return
            
            symbols = self.config.get('symbol_config', {})
            if symbol not in symbols:
                self.send_message(f"❌ Symbol {symbol} not found")
                return
            
            if symbol == 'XAUUSD':
                sl_defaults = {'LOW': 0.05, 'MEDIUM': 0.10, 'HIGH': 0.15}
            else:
                sl_defaults = {'LOW': 0.0003, 'MEDIUM': 0.0005, 'HIGH': 0.0008}
            
            symbols[symbol]['volatility'] = volatility
            symbols[symbol]['min_sl_distance'] = sl_defaults[volatility]
            self.config.update('symbol_config', symbols)
            
            self.send_message(f"✅ {symbol} volatility updated to {volatility}\nAuto SL: {sl_defaults[volatility]}")
        
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_view_risk_caps(self, message):
        """Display risk caps and current loss status"""
        if not self.risk_manager:
            self.send_message("❌ Risk manager not initialized")
            return
        
        tiers = self.config.get('risk_tiers', {})
        current_tier = self.config.get('default_risk_tier', '5000')
        
        daily_loss = self.risk_manager.daily_loss
        lifetime_loss = self.risk_manager.lifetime_loss
        
        msg = "💰 <b>Risk Caps &amp; Loss Status</b>\n\n"
        msg += f"<b>Current Tier: ${current_tier}</b>\n\n"
        
        msg += f"<b>Current Loss:</b>\n"
        msg += f"Daily: ${abs(daily_loss):.2f}\n"
        msg += f"Lifetime: ${abs(lifetime_loss):.2f}\n\n"
        
        msg += f"<b>All Risk Tiers:</b>\n"
        for balance, caps in sorted(tiers.items(), key=lambda x: int(x[0])):
            daily_cap = caps.get('daily_loss_limit', 0)
            lifetime_cap = caps.get('max_total_loss', 0)
            msg += f"${balance}: Daily ${daily_cap} | Lifetime ${lifetime_cap}\n"
        
        self.send_message(msg)

    def handle_set_daily_cap(self, message):
        """Set daily loss limit for current tier"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_daily_cap AMOUNT\nExample: /set_daily_cap 500")
                return
            
            amount = float(parts[1])
            if amount <= 0:
                self.send_message("❌ Amount must be positive")
                return
            
            current_tier = self.config.get('default_risk_tier', '5000')
            tiers = self.config.get('risk_tiers', {})
            
            if current_tier in tiers:
                tiers[current_tier]['daily_loss_limit'] = amount
                self.config.update('risk_tiers', tiers)
                self.send_message(f"✅ Daily loss limit for ${current_tier} tier set to ${amount}")
            else:
                self.send_message(f"❌ Tier ${current_tier} not found")
        
        except ValueError:
            self.send_message("❌ Invalid amount. Use numbers only")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_lifetime_cap(self, message):
        """Set lifetime loss limit for current tier"""
        try:
            parts = message['text'].split()
            if len(parts) != 2:
                self.send_message("❌ Usage: /set_lifetime_cap AMOUNT\nExample: /set_lifetime_cap 2000")
                return
            
            amount = float(parts[1])
            if amount <= 0:
                self.send_message("❌ Amount must be positive")
                return
            
            current_tier = self.config.get('default_risk_tier', '5000')
            tiers = self.config.get('risk_tiers', {})
            
            if current_tier in tiers:
                tiers[current_tier]['max_total_loss'] = amount
                self.config.update('risk_tiers', tiers)
                self.send_message(f"✅ Lifetime loss limit for ${current_tier} tier set to ${amount}")
            else:
                self.send_message(f"❌ Tier ${current_tier} not found")
        
        except ValueError:
            self.send_message("❌ Invalid amount. Use numbers only")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_set_risk_tier(self, message):
        """Set complete risk tier - /set_risk_tier BALANCE DAILY LIFETIME"""
        try:
            parts = message['text'].split()
            if len(parts) != 4:
                self.send_message("❌ Usage: /set_risk_tier BALANCE DAILY LIFETIME\nExample: /set_risk_tier 10000 500 2000")
                return
            
            balance = parts[1]
            daily_limit = float(parts[2])
            lifetime_limit = float(parts[3])
            
            if daily_limit <= 0 or lifetime_limit <= 0:
                self.send_message("❌ Limits must be positive")
                return
            
            tiers = self.config.get('risk_tiers', {})
            tiers[balance] = {
                'daily_loss_limit': daily_limit,
                'max_total_loss': lifetime_limit
            }
            self.config.update('risk_tiers', tiers)
            
            self.send_message(f"✅ Risk tier ${balance} configured:\nDaily: ${daily_limit}\nLifetime: ${lifetime_limit}")
        
        except ValueError:
            self.send_message("❌ Invalid values. Use: /set_risk_tier BALANCE DAILY LIFETIME")
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

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
                            continue 
                            
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