import MetaTrader5 as mt5
import time
from typing import Dict, Any, Optional
from config import Config
from models import Trade

class MT5Client:
    def __init__(self, config: Config):
        self.config = config
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize MT5 connection"""
        for i in range(self.config["mt5_retries"]):
            try:
                if not mt5.initialize():
                    print(f"MT5 initialization failed, retry {i+1}/{self.config['mt5_retries']}")
                    time.sleep(self.config["mt5_wait"])
                    continue
                
                authorized = mt5.login(
                    self.config["mt5_login"],
                    self.config["mt5_password"],
                    self.config["mt5_server"]
                )
                
                if authorized:
                    self.initialized = True
                    print("✅ MT5 connection established")
                    return True
                else:
                    print(f"MT5 login failed, retry {i+1}/{self.config['mt5_retries']}")
                    time.sleep(self.config["mt5_wait"])
                    
            except Exception as e:
                print(f"MT5 connection error: {str(e)}")
                time.sleep(self.config["mt5_wait"])
        
        print("❌ Failed to connect to MT5 after retries")
        return False

    def place_order(self, symbol: str, order_type: str, lot_size: float, 
                   price: float, sl: float, comment: str = "") -> Optional[int]:
        """Place a new order"""
        if not self.initialized:
            if not self.initialize():
                return None
        
        try:
            order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL
            sl_type = mt5.ORDER_TYPE_SELL if order_type == "buy" else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type_mt5,
                "price": price,
                "sl": sl,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Order failed: {result.comment}")
                return None
                
            return result.order
            
        except Exception as e:
            print(f"Order placement error: {str(e)}")
            return None

    def close_position(self, position_id: int, percentage: float = 100):
        """Close a position (fully or partially)"""
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            position = mt5.positions_get(ticket=position_id)
            if not position:
                print(f"Position {position_id} not found")
                return False
                
            position = position[0]
            volume_to_close = position.volume * (percentage / 100)
            
            order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": position_id,
                "symbol": position.symbol,
                "volume": volume_to_close,
                "type": order_type,
                "price": mt5.symbol_info_tick(position.symbol).ask if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(position.symbol).bid,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Close_{percentage}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            print(f"Position close error: {str(e)}")
            return False

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        if not self.initialized:
            if not self.initialize():
                return 0.0
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            return (tick.ask + tick.bid) / 2
        except:
            return 0.0

    def get_account_balance(self) -> float:
        """Get current account balance"""
        if not self.initialized:
            if not self.initialize():
                return 0.0
        
        try:
            account_info = mt5.account_info()
            return account_info.balance
        except:
            return 0.0

    def shutdown(self):
        """Shutdown MT5 connection"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False