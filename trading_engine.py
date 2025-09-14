import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from models import Alert, Trade
from config import Config
from risk_manager import RiskManager
from mt5_client import MT5Client
from alert_processor import AlertProcessor
from database import TradeDatabase
from exit_strategies import ExitStrategyManager
import json

class TradingEngine:
    def __init__(self, config: Config, risk_manager: RiskManager, 
                 mt5_client: MT5Client, telegram_bot, 
                 alert_processor: AlertProcessor):
        self.config = config
        self.risk_manager = risk_manager
        self.mt5_client = mt5_client
        self.telegram_bot = telegram_bot
        self.alert_processor = alert_processor
        
        # Risk manager ko MT5 client set karo
        self.risk_manager.set_mt5_client(mt5_client)
        
        # State machine for all 3 logics
        self.logic1_mode = "NEUTRAL"
        self.logic2_mode = "NEUTRAL" 
        self.logic3_mode = "NEUTRAL"
        
        # Current signals
        self.current_1h_bias = None
        self.current_15m_trend = None
        self.current_1d_bias = None
        self.current_1h_trend = None
        
        self.open_trades: List[Trade] = []
        self.is_paused = False
        self.trade_count = 0

        # Logic control flags
        self.logic1_enabled = True
        self.logic2_enabled = True  
        self.logic3_enabled = True

        # Database for trade history
        self.db = TradeDatabase()

        # Exit strategy manager
        self.exit_strategy_manager = ExitStrategyManager(mt5_client, self)

    async def initialize(self):
        """Initialize the trading engine"""
        success = self.mt5_client.initialize()
        if success:
            self.telegram_bot.send_message("✅ MT5 Connection Established")
        return success

    async def process_alert(self, data: Dict[str, Any]) -> bool:
        """Process incoming alert from webhook"""
        try:
            alert = Alert(**data)
            
            # Update signals based on alert type
            if alert.tf == '1h' and alert.type == 'bias':
                self.current_1h_bias = alert.signal
                self.telegram_bot.send_message(f"📊 1H Bias Updated: {alert.signal.upper()}")
                
            elif alert.tf == '15m' and alert.type == 'trend':
                self.current_15m_trend = alert.signal
                self.telegram_bot.send_message(f"📊 15M Trend Updated: {alert.signal.upper()}")
            
            elif alert.tf == '1d' and alert.type == 'bias':
                self.current_1d_bias = alert.signal
                self.telegram_bot.send_message(f"📊 1D Bias Updated: {alert.signal.upper()}")
                
            elif alert.tf == '1h' and alert.type == 'trend':
                self.current_1h_trend = alert.signal
                self.telegram_bot.send_message(f"📊 1H Trend Updated: {alert.signal.upper()}")
            
            # Update all logic states
            self.update_logic_states()
            
            # Execute trades based on alert type
            if alert.type == 'entry':
                await self.execute_trades(alert)
            
            return True
            
        except Exception as e:
            error_msg = f"Alert processing error: {str(e)}"
            self.telegram_bot.send_message(f"❌ {error_msg}")
            return False

    def update_logic_states(self):
        """Update states for all 3 trading logics"""
        # LOGIC 1: 1h bias + 15m trend → 5m entries
        if self.current_1h_bias == "bull" and self.current_15m_trend == "bull":
            if self.logic1_mode != "BULLISH":
                self.telegram_bot.send_message("🚀 LOGIC1: BULLISH MODE ACTIVATED")
            self.logic1_mode = "BULLISH"
        elif self.current_1h_bias == "bear" and self.current_15m_trend == "bear":
            if self.logic1_mode != "BEARISH":
                self.telegram_bot.send_message("🔻 LOGIC1: BEARISH MODE ACTIVATED")
            self.logic1_mode = "BEARISH"
        else:
            if self.logic1_mode != "NEUTRAL":
                self.telegram_bot.send_message("⏸️ LOGIC1: NEUTRAL MODE")
            self.logic1_mode = "NEUTRAL"
        
        # LOGIC 2: 1h bias + 15m trend → 15m entries
        if self.current_1h_bias == "bull" and self.current_15m_trend == "bull":
            if self.logic2_mode != "BULLISH":
                self.telegram_bot.send_message("🚀 LOGIC2: BULLISH MODE ACTIVATED")
            self.logic2_mode = "BULLISH"
        elif self.current_1h_bias == "bear" and self.current_15m_trend == "bear":
            if self.logic2_mode != "BEARISH":
                self.telegram_bot.send_message("🔻 LOGIC2: BEARISH MODE ACTIVATED")
            self.logic2_mode = "BEARISH"
        else:
            if self.logic2_mode != "NEUTRAL":
                self.telegram_bot.send_message("⏸️ LOGIC2: NEUTRAL MODE")
            self.logic2_mode = "NEUTRAL"
        
        # LOGIC 3: 1D bias + 1h trend → 1h entries
        if self.current_1d_bias == "bull" and self.current_1h_trend == "bull":
            if self.logic3_mode != "BULLISH":
                self.telegram_bot.send_message("🚀 LOGIC3: BULLISH MODE ACTIVATED")
            self.logic3_mode = "BULLISH"
        elif self.current_1d_bias == "bear" and self.current_1h_trend == "bear":
            if self.logic3_mode != "BEARISH":
                self.telegram_bot.send_message("🔻 LOGIC3: BEARISH MODE ACTIVATED")
            self.logic3_mode = "BEARISH"
        else:
            if self.logic3_mode != "NEUTRAL":
                self.telegram_bot.send_message("⏸️ LOGIC3: NEUTRAL MODE")
            self.logic3_mode = "NEUTRAL"

    async def execute_trades(self, alert: Alert):
        """Execute trades based on current mode and alert"""
        if self.is_paused:
            return
            
        # Check if specific logic is enabled
        if alert.tf == '5m' and not self.logic1_enabled:
            return
        if alert.tf == '15m' and not self.logic2_enabled:
            return
        if alert.tf == '1h' and not self.logic3_enabled:
            return
            
        # Check risk limits before trading
        if not self.risk_manager.can_trade():
            self.telegram_bot.send_message("⛔ Trading paused due to risk limits")
            return
        
        # LOGIC 1: 5m entries
        if alert.tf == '5m' and alert.type == 'entry':
            if self.logic1_mode == "BULLISH" and alert.signal == "buy":
                await self.place_order(alert, "LOGIC1", "buy")
            elif self.logic1_mode == "BEARISH" and alert.signal == "sell":
                await self.place_order(alert, "LOGIC1", "sell")
        
        # LOGIC 2: 15m entries
        elif alert.tf == '15m' and alert.type == 'entry':
            if self.logic2_mode == "BULLISH" and alert.signal == "buy":
                await self.place_order(alert, "LOGIC2", "buy")
            elif self.logic2_mode == "BEARISH" and alert.signal == "sell":
                await self.place_order(alert, "LOGIC2", "sell")
        
        # LOGIC 3: 1h entries
        elif alert.tf == '1h' and alert.type == 'entry':
            if self.logic3_mode == "BULLISH" and alert.signal == "buy":
                await self.place_order(alert, "LOGIC3", "buy")
            elif self.logic3_mode == "BEARISH" and alert.signal == "sell":
                await self.place_order(alert, "LOGIC3", "sell")

    # Logic control methods
    def enable_logic(self, logic_number: int):
        if logic_number == 1:
            self.logic1_enabled = True
        elif logic_number == 2:
            self.logic2_enabled = True
        elif logic_number == 3:
            self.logic3_enabled = True

    def disable_logic(self, logic_number: int):
        if logic_number == 1:
            self.logic1_enabled = False
        elif logic_number == 2:
            self.logic2_enabled = False
        elif logic_number == 3:
            self.logic3_enabled = False

    def get_logic_status(self) -> Dict[str, bool]:
        return {
            "logic1": self.logic1_enabled,
            "logic2": self.logic2_enabled,
            "logic3": self.logic3_enabled
        }

    async def place_order(self, alert: Alert, strategy: str, direction: str):
        """Place a new trade order"""
        try:
            # Calculate position size based on risk
            lot_size = self.risk_manager.calculate_position_size(alert.symbol, alert.price, alert.sl)
            
            if lot_size <= 0:
                self.telegram_bot.send_message("⚠️ Position size too small, skipping trade")
                return
            
            # Calculate Fibonacci TP levels
            price_diff = abs(alert.price - alert.sl)
            if direction == "buy":
                tp1 = alert.price + price_diff * self.config["fibonacci_levels"]["tp1"]
                tp2 = alert.price + price_diff * self.config["fibonacci_levels"]["tp2"]
                tp3 = alert.price + price_diff * self.config["fibonacci_levels"]["tp3"]
            else:  # sell
                tp1 = alert.price - price_diff * self.config["fibonacci_levels"]["tp1"]
                tp2 = alert.price - price_diff * self.config["fibonacci_levels"]["tp2"]
                tp3 = alert.price - price_diff * self.config["fibonacci_levels"]["tp3"]
            
            # Create trade object
            trade = Trade(
                symbol=alert.symbol,
                entry=alert.price,
                sl=alert.sl,
                tp1=tp1,
                tp2=tp2,
                tp3=tp3,
                lot_size=lot_size,
                direction=direction,
                strategy=strategy,
                open_time=datetime.now().isoformat()
            )
            
            # Execute trade
            if not self.config["simulate_orders"]:
                trade_id = self.mt5_client.place_order(
                    symbol=alert.symbol,
                    order_type=direction,
                    lot_size=lot_size,
                    price=alert.price,
                    sl=alert.sl,
                    comment=f"{strategy}_{direction}"
                )
                if trade_id:
                    trade.trade_id = trade_id
                    
                    # Add default trailing stop
                    self.exit_strategy_manager.add_trailing_stop(
                        trade, 
                        self.config["exit_strategies"]["default_trailing_points"]
                    )
            
            self.open_trades.append(trade)
            self.risk_manager.add_open_trade(trade)
            self.trade_count += 1
            
            # Send notification
            message = (
                f"🎯 NEW TRADE #{self.trade_count}\n"
                f"Strategy: {strategy}\n"
                f"Symbol: {alert.symbol}\n"
                f"Direction: {direction.upper()}\n"
                f"Entry: {alert.price}\n"
                f"SL: {alert.sl}\n"
                f"TP1: {tp1:.5f}\n"
                f"TP2: {tp2:.5f}\n"
                f"TP3: {tp3:.5f}\n"
                f"Lots: {lot_size:.2f}"
            )
            self.telegram_bot.send_message(message)
            
        except Exception as e:
            error_msg = f"Trade execution error: {str(e)}"
            self.telegram_bot.send_message(f"❌ {error_msg}")

    async def manage_open_trades(self):
        """Monitor and manage open trades"""
        while True:
            try:
                for trade in self.open_trades:
                    if trade.status == "closed":
                        continue
                    
                    # Get current price
                    current_price = self.mt5_client.get_current_price(trade.symbol)
                    if current_price == 0:
                        continue
                    
                    # Priority 1: Stop Loss Check
                    if ((trade.direction == "buy" and current_price <= trade.sl) or
                        (trade.direction == "sell" and current_price >= trade.sl)):
                        await self.close_trade(trade, 100, "SL_HIT")
                        continue
                    
                    # Priority 2: Take Profit Levels
                    if trade.direction == "buy":
                        if current_price >= trade.tp1 and not trade.tp1_hit:
                            await self.close_trade(trade, 50, "TP1_HIT")
                            trade.tp1_hit = True
                            
                        if current_price >= trade.tp2 and not trade.tp2_hit:
                            await self.close_trade(trade, 25, "TP2_HIT")
                            trade.tp2_hit = True
                            
                        if current_price >= trade.tp3 and not trade.tp3_hit:
                            await self.close_trade(trade, 25, "TP3_HIT")
                            trade.tp3_hit = True
                    
                    else:  # sell direction
                        if current_price <= trade.tp1 and not trade.tp1_hit:
                            await self.close_trade(trade, 50, "TP1_HIT")
                            trade.tp1_hit = True
                            
                        if current_price <= trade.tp2 and not trade.tp2_hit:
                            await self.close_trade(trade, 25, "TP2_HIT")
                            trade.tp2_hit = True
                            
                        if current_price <= trade.tp3 and not trade.tp3_hit:
                            await self.close_trade(trade, 25, "TP3_HIT")
                            trade.tp3_hit = True
                    
                    # Priority 3: Exit Strategies Check
                    if self.exit_strategy_manager.check_exit_conditions(trade):
                        await self.close_trade(trade, 100, "EXIT_STRATEGY")
                    
                    # Priority 4: Indicator-based Exit
                    if self.should_exit_by_indicator(trade):
                        await self.close_trade(trade, trade.position_open, "INDICATOR_EXIT")
                
                await asyncio.sleep(5)
                
            except Exception as e:
                error_msg = f"Trade management error: {str(e)}"
                self.telegram_bot.send_message(f"❌ {error_msg}")
                await asyncio.sleep(30)

    def should_exit_by_indicator(self, trade: Trade) -> bool:
        """Check if we should exit based on indicator reversal"""
        if trade.strategy == "LOGIC1":
            if ((trade.direction == "buy" and self.logic1_mode != "BULLISH") or
                (trade.direction == "sell" and self.logic1_mode != "BEARISH")):
                return True
        elif trade.strategy == "LOGIC2":
            if ((trade.direction == "buy" and self.logic2_mode != "BULLISH") or
                (trade.direction == "sell" and self.logic2_mode != "BEARISH")):
                return True
        else:  # LOGIC3
            if ((trade.direction == "buy" and self.logic3_mode != "BULLISH") or
                (trade.direction == "sell" and self.logic3_mode != "BEARISH")):
                return True
        return False

    async def close_trade(self, trade: Trade, percentage: float, reason: str):
        """Close a portion of the trade"""
        try:
            if not self.config["simulate_orders"] and hasattr(trade, 'trade_id') and trade.trade_id:
                success = self.mt5_client.close_position(trade.trade_id, percentage)
                if not success:
                    self.telegram_bot.send_message(f"❌ Failed to close trade {trade.trade_id}")
                    return
            
            trade.position_open -= percentage
            if trade.position_open <= 0:
                trade.status = "closed"
                self.risk_manager.remove_open_trade(trade)
            
            # Calculate PnL
            current_price = self.mt5_client.get_current_price(trade.symbol)
            if current_price > 0:
                if trade.direction == "buy":
                    pnl = (current_price - trade.entry) * trade.lot_size * 10000
                else:
                    pnl = (trade.entry - current_price) * trade.lot_size * 10000
                
                # Update risk manager
                self.risk_manager.update_pnl(pnl * (percentage / 100))
                
                # Save to database
                self.db.save_trade(trade)
                
                # Remove exit strategy
                if hasattr(trade, 'trade_id') and trade.trade_id:
                    self.exit_strategy_manager.remove_strategy(trade.trade_id)
                
                # Send notification
                message = (
                    f"🔚 TRADE CLOSED\n"
                    f"Reason: {reason}\n"
                    f"Symbol: {trade.symbol}\n"
                    f"Strategy: {trade.strategy}\n"
                    f"Closed: {percentage}%\n"
                    f"PnL: ${pnl:.2f}"
                )
                self.telegram_bot.send_message(message)
            
        except Exception as e:
            error_msg = f"Trade close error: {str(e)}"
            self.telegram_bot.send_message(f"❌ {error_msg}")