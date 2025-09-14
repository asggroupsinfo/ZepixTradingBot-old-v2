import requests
import json
import threading
import time
from typing import Dict, Any, Callable, TYPE_CHECKING
from config import Config
from risk_manager import RiskManager
from analytics_engine import AnalyticsEngine  # ADDED AnalyticsEngine import

if TYPE_CHECKING:
    from trading_engine import TradingEngine

class TelegramBot:
    def __init__(self, config: Config):
        self.config = config
        self.token = config["telegram_token"]
        self.chat_id = config["telegram_chat_id"]
        self.base_url = f"https://api.telegram.org/bot{self.token}"
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
            "/performance_report": self.handle_performance_report,  # ADDED new command
            "/pair_report": self.handle_pair_report,  # ADDED new command
            "/strategy_report": self.handle_strategy_report,  # ADDED new command
            "/exit_strategies": self.handle_exit_strategies,  # ADDED Phase 2 command
            "/add_trailing": self.handle_add_trailing,  # ADDED Phase 2 command
            "/add_time_exit": self.handle_add_time_exit  # ADDED Phase 2 command
        }
        self.risk_manager = None
        self.trading_engine = None
        self.analytics_engine = AnalyticsEngine()  # ADDED AnalyticsEngine initialization

    def set_dependencies(self, risk_manager: RiskManager, trading_engine: 'TradingEngine'):
        """Set dependent modules"""
        self.risk_manager = risk_manager
        self.trading_engine = trading_engine

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
            "🤖 <b>Zepix Trading Bot Started</b>\n\n"
            "✅ Bot is now active and monitoring alerts\n"
            "📊 Ready to execute trades based on signals\n\n"
            "<b>Available Commands:</b>\n"
            "/status - Bot status\n"
            "/pause - Pause trading\n"
            "/resume - Resume trading\n"
            "/performance - Trading performance\n"
            "/stats - Risk statistics\n"
            "/trades - Open trades\n"
            "/logic1_on/off - Enable/disable Logic 1\n"
            "/logic2_on/off - Enable/disable Logic 2\n"
            "/logic3_on/off - Enable/disable Logic 3\n"
            "/logic_status - Check logic status\n"
            "/performance_report - 30-day performance\n"
            "/pair_report - Pair performance\n"
            "/strategy_report - Strategy performance\n"
            "/exit_strategies - Show active exit strategies\n"  # ADDED to welcome message
            "/add_trailing - Add trailing stop to trade\n"  # ADDED to welcome message
            "/add_time_exit - Add time-based exit to trade"  # ADDED to welcome message
        )
        self.send_message(welcome_msg)

    def handle_status(self, message):
        """Handle /status command"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        status_msg = (
            "📊 <b>Bot Status</b>\n\n"
            f"🔸 Trading: {'⏸️ PAUSED' if self.trading_engine.is_paused else '✅ ACTIVE'}\n"
            f"🔸 Simulation: {'✅ ON' if self.config['simulate_orders'] else '❌ OFF'}\n"
            f"🔸 MT5 Connected: {'✅ YES' if self.trading_engine.mt5_client.initialized else '❌ NO'}\n\n"
            "<b>Current Modes:</b>\n"
            f"LOGIC1: {self.trading_engine.logic1_mode}\n"
            f"LOGIC2: {self.trading_engine.logic2_mode}\n"
            f"LOGIC3: {self.trading_engine.logic3_mode}\n\n"
            f"1H Bias: {self.trading_engine.current_1h_bias or 'N/A'}\n"
            f"15M Trend: {self.trading_engine.current_15m_trend or 'N/A'}\n"
            f"1D Bias: {self.trading_engine.current_1d_bias or 'N/A'}\n"
            f"1H Trend: {self.trading_engine.current_1h_trend or 'N/A'}"
        )
        self.send_message(status_msg)

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
            f"🔸 Per Trade Cap: ${stats['risk_parameters']['per_trade_cap']}\n"
            f"🔸 Daily Loss Limit: ${stats['risk_parameters']['daily_loss_limit']}\n"
            f"🔸 Max Total Loss: ${stats['risk_parameters']['max_total_loss']}\n\n"
            f"📊 Daily Loss: ${stats['daily_loss']:.2f}/{stats['risk_parameters']['daily_loss_limit']}\n"
            f"🔻 Lifetime Loss: ${stats['lifetime_loss']:.2f}/{stats['risk_parameters']['max_total_loss']}"
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
                trades_msg += (
                    f"<b>Trade #{i}</b>\n"
                    f"Symbol: {trade.symbol} | {trade.direction.upper()}\n"
                    f"Strategy: {trade.strategy}\n"
                    f"Entry: {trade.entry} | SL: {trade.sl}\n"
                    f"Open: {trade.position_open}%\n"
                    f"TP1: {trade.tp1:.5f} | TP2: {trade.tp2:.5f} | TP3: {trade.tp3:.5f}\n"
                    "────────────────────\n"
                )
        
        self.send_message(trades_msg)

    # Logic control handlers
    def handle_logic1_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(1)
            self.send_message("✅ LOGIC 1 TRADING ENABLED")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_logic1_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(1)
            self.send_message("⛔ LOGIC 1 TRADING DISABLED")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_logic2_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(2)
            self.send_message("✅ LOGIC 2 TRADING ENABLED")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_logic2_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(2)
            self.send_message("⛔ LOGIC 2 TRADING DISABLED")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_logic3_on(self, message):
        if self.trading_engine:
            self.trading_engine.enable_logic(3)
            self.send_message("✅ LOGIC 3 TRADING ENABLED")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_logic3_off(self, message):
        if self.trading_engine:
            self.trading_engine.disable_logic(3)
            self.send_message("⛔ LOGIC 3 TRADING DISABLED")
        else:
            self.send_message("❌ Trading engine not initialized")

    def handle_logic_status(self, message):
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        status = self.trading_engine.get_logic_status()
        status_msg = (
            "🤖 LOGIC STATUS:\n\n"
            f"LOGIC 1 (1H+15M→5M): {'✅ ENABLED' if status['logic1'] else '❌ DISABLED'}\n"
            f"LOGIC 2 (1H+15M→15M): {'✅ ENABLED' if status['logic2'] else '❌ DISABLED'}\n"
            f"LOGIC 3 (1D+1H→1H): {'✅ ENABLED' if status['logic3'] else '❌ DISABLED'}\n\n"
            "Use /logic1_on, /logic1_off, etc. to control"
        )
        self.send_message(status_msg)

    # Analytics handlers - ADDED NEW FUNCTIONS
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

    # Phase 2: Exit Strategy Handlers - ADDED NEW FUNCTIONS
    def handle_exit_strategies(self, message):
        """Show active exit strategies"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        strategies = self.trading_engine.exit_strategy_manager.get_active_strategies()
        
        if not strategies:
            self.send_message("🤖 No active exit strategies")
            return
            
        msg = "🎯 Active Exit Strategies:\n\n"
        for trade_id, strategy in strategies.items():
            msg += f"Trade: {trade_id}\n"
            msg += f"Symbol: {strategy['symbol']}\n"
            msg += f"Type: {strategy['type']}\n"
            
            if strategy['type'] == 'trailing_stop':
                msg += f"Trailing Points: {strategy['trailing_points']}\n"
                msg += f"Best Price: {strategy['best_price']}\n"
            elif strategy['type'] == 'time_based':
                msg += f"Expires: {strategy['expiry_time'].strftime('%Y-%m-%d %H:%M')}\n"
                
            msg += "────────────────────\n"
            
        self.send_message(msg)

    def handle_add_trailing(self, message):
        """Add trailing stop to a trade"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        try:
            # Example: /add_trailing 123456 75.0
            parts = message['text'].split()
            if len(parts) >= 3:
                trade_id = parts[1]
                points = float(parts[2])
                
                # Find the trade
                for trade in self.trading_engine.open_trades:
                    if str(trade.trade_id) == trade_id:
                        self.trading_engine.exit_strategy_manager.add_trailing_stop(trade, points)
                        self.send_message(f"✅ Trailing SL added to trade {trade_id}")
                        return
                
                self.send_message("❌ Trade not found")
            else:
                self.send_message("❌ Usage: /add_trailing <trade_id> <points>")
                
        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def handle_add_time_exit(self, message):
        """Add time-based exit to a trade"""
        if not self.trading_engine:
            self.send_message("❌ Trading engine not initialized")
            return
            
        try:
            # Example: /add_time_exit 123456 2.0
            parts = message['text'].split()
            if len(parts) >= 3:
                trade_id = parts[1]
                hours = float(parts[2])
                
                # Find the trade
                for trade in self.trading_engine.open_trades:
                    if str(trade.trade_id) == trade_id:
                        self.trading_engine.exit_strategy_manager.add_time_based_exit(trade, hours)
                        self.send_message(f"✅ Time exit added to trade {trade_id}")
                        return
                
                self.send_message("❌ Trade not found")
            else:
                self.send_message("❌ Usage: /add_time_exit <trade_id> <hours>")
                
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
                        updates = response.json().get("result", [])
                        
                        for update in updates:
                            offset = update["update_id"] + 1
                            
                            if "message" in update and "text" in update["message"]:
                                message = update["message"]
                                user_id = message["from"]["id"]
                                text = message["text"]
                                
                                if user_id == self.config["allowed_telegram_user"]:
                                    if text in self.command_handlers:
                                        self.command_handlers[text](message)
                                    else:
                                        self.send_message("❌ Unknown command. Use /start to see available commands.")
                
                except Exception as e:
                    print(f"Telegram polling error: {str(e)}")
                    time.sleep(10)
        
        # Start polling in background thread
        thread = threading.Thread(target=poll_commands, daemon=True)
        thread.start()
        print("✅ Telegram bot polling started")  # ✅ EXTRA 's' REMOVED