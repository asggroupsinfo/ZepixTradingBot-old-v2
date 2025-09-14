import json
import os
from datetime import datetime, date
from typing import Dict, Any, List
from config import Config

class RiskManager:
    def __init__(self, config: Config):
        self.config = config
        self.stats_file = "stats.json"
        self.daily_loss = 0.0
        self.lifetime_loss = 0.0
        self.daily_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.current_risk_tier = "5000"
        self.open_trades = []
        self.mt5_client = None
        self.load_stats()

    def load_stats(self):
        """Load statistics from file"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
                
            if stats.get("date") != str(date.today()):
                self.daily_loss = 0.0
                self.daily_profit = 0.0
            else:
                self.daily_loss = stats.get("daily_loss", 0.0)
                self.daily_profit = stats.get("daily_profit", 0.0)
                
            self.lifetime_loss = stats.get("lifetime_loss", 0.0)
            self.total_trades = stats.get("total_trades", 0)
            self.winning_trades = stats.get("winning_trades", 0)

    def save_stats(self):
        """Save statistics to file"""
        stats = {
            "date": str(date.today()),
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "lifetime_loss": self.lifetime_loss,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "current_risk_tier": self.current_risk_tier
        }
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=4)

    def get_risk_tier(self, balance: float) -> str:
        """Get risk tier based on account balance"""
        for tier in ["100000", "50000", "25000", "10000", "5000"]:
            if balance >= int(tier):
                return tier
        return "5000"

    def calculate_floating_loss(self) -> float:
        """Calculate current floating loss from open trades"""
        if not self.mt5_client:
            return 0.0
            
        floating_loss = 0.0
        for trade in self.open_trades:
            if trade.status == "open":
                current_price = self.mt5_client.get_current_price(trade.symbol)
                if current_price == 0:
                    continue
                    
                if trade.direction == "buy":
                    floating_loss += (trade.entry - current_price) * trade.lot_size * 10000
                else:
                    floating_loss += (current_price - trade.entry) * trade.lot_size * 10000
        return floating_loss

    def can_trade(self) -> bool:
        """Check if trading is allowed based on all risk limits"""
        if not self.mt5_client:
            return False
            
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return False
            
        risk_params = self.config["risk_tiers"][risk_tier]
        
        # Check closed loss limits
        if self.lifetime_loss >= risk_params["max_total_loss"]:
            return False
            
        if self.daily_loss >= risk_params["daily_loss_limit"]:
            return False
        
        # Check floating loss limit
        floating_loss = self.calculate_floating_loss()
        if floating_loss >= risk_params["daily_loss_limit"]:
            return False
            
        return True

    def calculate_position_size(self, symbol: str, entry_price: float, sl_price: float) -> float:
        """Calculate position size based on combined risk management"""
        if not self.mt5_client:
            return 0.0
            
        # Get account size and risk parameters
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return 0.0
            
        risk_params = self.config["risk_tiers"][risk_tier]
        base_multiplier = risk_params.get("base_multiplier", 1.0)
        
        # Get symbol volatility config
        symbol_config = self.config.get("symbol_config", {}).get(symbol, {})
        volatility_level = symbol_config.get("volatility", "MEDIUM")
        pip_value = symbol_config.get("pip_value", 10.0)
        max_lots = symbol_config.get("max_lots", 10.0)
        
        # Get base risk from volatility
        volatility_config = self.config.get("volatility_risk_levels", {}).get(volatility_level, {})
        base_risk = volatility_config.get("base_per_trade_cap", 50)
        
        # Apply account size multiplier
        volatility_risk = base_risk * base_multiplier
        
        # Ensure we don't exceed account's per_trade_cap
        actual_risk = min(volatility_risk, risk_params["per_trade_cap"])
        
        price_diff = abs(entry_price - sl_price)
        
        if price_diff == 0:
            return 0
            
        # Calculate lot size
        if "XAU" in symbol or "GOLD" in symbol:
            lot_size = actual_risk / (price_diff * pip_value)
        else:
            lot_size = actual_risk / (price_diff * 100000 / pip_value)
        
        # Apply symbol-specific max lots
        lot_size = max(0.01, min(lot_size, max_lots))
        return round(lot_size, 2)

    def update_pnl(self, pnl: float):
        """Update PnL and risk statistics"""
        self.total_trades += 1
        
        if pnl > 0:
            self.daily_profit += pnl
            self.winning_trades += 1
        else:
            self.daily_loss += abs(pnl)
            self.lifetime_loss += abs(pnl)
        
        self.save_stats()

    def add_open_trade(self, trade):
        """Add trade to open trades list"""
        self.open_trades.append(trade)

    def remove_open_trade(self, trade):
        """Remove trade from open trades list"""
        self.open_trades = [t for t in self.open_trades if getattr(t, 'trade_id', None) != getattr(trade, 'trade_id', None)]

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        if not self.mt5_client:
            return {}
            
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return {}
            
        risk_params = self.config["risk_tiers"][risk_tier]
        floating_loss = self.calculate_floating_loss()
        
        return {
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "lifetime_loss": self.lifetime_loss,
            "floating_loss": floating_loss,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            "current_risk_tier": risk_tier,
            "risk_parameters": risk_params,
            "floating_loss_alert": floating_loss >= risk_params["daily_loss_limit"]
        }

    def set_mt5_client(self, mt5_client):
        """Set MT5 client for balance checking"""
        self.mt5_client = mt5_client