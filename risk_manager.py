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
        self.open_trades = []
        self.mt5_client = None
        self.load_stats()
        
    def load_stats(self):
        """Load statistics from file with error handling"""
        try:
            if os.path.exists(self.stats_file) and os.path.getsize(self.stats_file) > 0:
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
            else:
                # Initialize with default values if file doesn't exist or is empty
                self.reset_daily_stats()
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Stats file corrupted, resetting: {str(e)}")
            self.reset_daily_stats()
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_loss = 0.0
        self.daily_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.save_stats()
    
    def save_stats(self):
        """Save statistics to file"""
        stats = {
            "date": str(date.today()),
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "lifetime_loss": self.lifetime_loss,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades
        }
        
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=4)
        except Exception as e:
            print(f"❌ Error saving stats: {str(e)}")
    
    def get_fixed_lot_size(self, balance: float) -> float:
        """Get fixed lot size based on account balance"""
        
        # Manual overrides first
        manual_overrides = self.config.get("manual_lot_overrides", {})
        if str(int(balance)) in manual_overrides:
            return manual_overrides[str(int(balance))]
        
        # Then tier-based sizing
        fixed_lots = self.config["fixed_lot_sizes"]
        
        for tier_balance in sorted(fixed_lots.keys(), key=int, reverse=True):
            if balance >= int(tier_balance):
                return fixed_lots[tier_balance]
        
        return 0.05  # Default minimum
    
    def set_manual_lot_size(self, balance_tier: int, lot_size: float):
        """Manually override lot size for a balance tier"""
        
        if "manual_lot_overrides" not in self.config.config:
            self.config.config["manual_lot_overrides"] = {}
        
        self.config.config["manual_lot_overrides"][str(balance_tier)] = lot_size
        self.config.save_config()
    
    def get_risk_tier(self, balance: float) -> str:
        """Get risk tier based on account balance"""
        for tier in ["100000", "50000", "25000", "10000", "5000"]:
            if balance >= int(tier):
                return tier
        return "5000"
    
    def can_trade(self) -> bool:
        """Check if trading is allowed based on risk limits"""
        if not self.mt5_client:
            return False
            
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return False
            
        risk_params = self.config["risk_tiers"][risk_tier]
        
        # Check closed loss limits
        if self.lifetime_loss >= risk_params["max_total_loss"]:
            print(f"⛔ Lifetime loss limit reached: ${self.lifetime_loss}")
            return False
            
        if self.daily_loss >= risk_params["daily_loss_limit"]:
            print(f"⛔ Daily loss limit reached: ${self.daily_loss}")
            return False
        
        return True
    
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
        self.open_trades = [t for t in self.open_trades 
                          if getattr(t, 'trade_id', None) != getattr(trade, 'trade_id', None)]
    
    def set_mt5_client(self, mt5_client):
        """Set MT5 client for balance checking"""
        self.mt5_client = mt5_client
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        if not self.mt5_client:
            return {}
            
        account_balance = self.mt5_client.get_account_balance()
        risk_tier = self.get_risk_tier(account_balance)
        lot_size = self.get_fixed_lot_size(account_balance)
        
        if risk_tier not in self.config["risk_tiers"]:
            return {}
            
        risk_params = self.config["risk_tiers"][risk_tier]
        
        return {
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "lifetime_loss": self.lifetime_loss,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            "current_risk_tier": risk_tier,
            "risk_parameters": risk_params,
            "current_lot_size": lot_size,
            "account_balance": account_balance
        }