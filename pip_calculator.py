from typing import Dict, Tuple
from config import Config

class PipCalculator:
    """
    Accurate pip and SL calculation for all symbols
    Uses TradingView symbol names (XAUUSD) internally
    MT5Client handles the mapping to broker symbols (GOLD)
    """
    
    def __init__(self, config: Config):
        self.config = config
        
    def calculate_sl_price(self, symbol: str, entry_price: float, 
                          direction: str, lot_size: float, 
                          account_balance: float) -> Tuple[float, float]:
        """
        Calculate SL price based on risk amount and lot size
        Symbol parameter uses TradingView naming (XAUUSD, not GOLD)
        Returns: (sl_price, sl_distance_in_price)
        """
        
        # Get symbol configuration using TradingView symbol name
        symbol_config = self.config["symbol_config"][symbol]
        volatility = symbol_config["volatility"]
        
        # Get account tier and risk cap based on balance and volatility
        account_tier = self._get_account_tier(account_balance)
        risk_cap = self.config["risk_by_account_tier"][account_tier][volatility]["risk_dollars"]
        
        # Special handling for gold - checks the is_gold flag in config
        if symbol_config.get("is_gold", False):
            return self._calculate_gold_sl(entry_price, direction, lot_size, risk_cap)
        
        # Calculate pip value for the lot size
        pip_value = self._get_pip_value(symbol, lot_size)
        
        # Calculate SL distance in pips
        sl_pips = risk_cap / pip_value
        
        # Convert pips to price distance
        pip_size = symbol_config["pip_size"]
        sl_distance = sl_pips * pip_size
        
        # Ensure minimum SL distance for safety
        min_distance = symbol_config["min_sl_distance"]
        sl_distance = max(sl_distance, min_distance)
        
        # Calculate actual SL price based on direction
        if direction == "buy":
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance
            
        return sl_price, sl_distance
    
    def _calculate_gold_sl(self, entry_price: float, direction: str, 
                          lot_size: float, risk_cap: float) -> Tuple[float, float]:
        """
        Special calculation for GOLD/XAUUSD
        Gold has unique pip value calculations compared to forex pairs
        """
        
        # For GOLD: 1 pip (0.01) = $1 for 1.0 lot
        # Point value scales linearly with lot size
        point_value = lot_size * 1
        
        # Calculate how many points we need to risk the cap amount
        points_needed = risk_cap / point_value
        
        # Convert points to price distance (GOLD moves in 0.01 increments)
        sl_distance = points_needed
        
        # Ensure minimum distance of 0.50 for gold volatility
        sl_distance = max(sl_distance, 0.50)
        
        # Calculate SL price based on trade direction
        if direction == "buy":
            sl_price = entry_price - sl_distance
        else:
            sl_price = entry_price + sl_distance
            
        return sl_price, sl_distance
    
    def _get_pip_value(self, symbol: str, lot_size: float) -> float:
        """
        Get pip value for a specific lot size
        Pip value is the monetary value of one pip movement
        """
        
        symbol_config = self.config["symbol_config"][symbol]
        
        # Get pip value for 1 standard lot (base value)
        pip_value_std = symbol_config["pip_value_per_std_lot"]
        
        # Scale to actual lot size being traded
        pip_value = pip_value_std * lot_size
        
        return pip_value
    
    def calculate_tp_price(self, entry_price: float, sl_price: float, 
                          direction: str, rr_ratio: float = 1.0) -> float:
        """
        Calculate TP price based on Risk:Reward ratio
        Default is 1:1 RR for this bot
        """
        
        # Calculate SL distance from entry
        sl_distance = abs(entry_price - sl_price)
        
        # Calculate TP distance based on RR ratio
        tp_distance = sl_distance * rr_ratio
        
        # Calculate TP price based on direction
        if direction == "buy":
            tp_price = entry_price + tp_distance
        else:
            tp_price = entry_price - tp_distance
            
        return tp_price
    
    def adjust_sl_for_reentry(self, original_sl_distance: float, 
                             level: int, reduction_percent: float = 0.2) -> float:
        """
        Calculate reduced SL distance for re-entry levels
        Each level reduces SL by 20% to manage cumulative risk
        """
        
        # Progressive reduction: Level 1 = 100%, Level 2 = 80%, Level 3 = 64%, etc.
        reduction_factor = (1 - reduction_percent) ** (level - 1)
        new_sl_distance = original_sl_distance * reduction_factor
        
        return new_sl_distance
    
    def _get_account_tier(self, balance: float) -> str:
        """
        Determine account tier based on balance
        Returns tier key as string for config lookup
        """
        if balance < 7500:
            return "5000"
        elif balance < 17500:
            return "10000"
        elif balance < 37500:
            return "25000"
        elif balance < 75000:
            return "50000"
        else:
            return "100000"