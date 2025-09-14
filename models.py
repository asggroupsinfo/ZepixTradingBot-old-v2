from typing import Dict, Any, Optional, List
from pydantic import BaseModel, validator
from datetime import datetime
import json

class Alert(BaseModel):
    type: str  # "bias", "trend", or "entry"
    symbol: str
    signal: str  # "buy", "sell", "bull", "bear"
    tf: str  # "1h", "15m", "5m"
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    strategy: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @validator('type')
    def validate_type(cls, v):
        if v not in ['bias', 'trend', 'entry']:
            raise ValueError('Type must be bias, trend, or entry')
        return v

    @validator('tf')
    def validate_tf(cls, v):
        if v not in ['1h', '15m', '5m']:
            raise ValueError('Timeframe must be 1h, 15m, or 5m')
        return v

class Trade(BaseModel):
    symbol: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    lot_size: float
    direction: str  # "buy" or "sell"
    strategy: str  # "LOGIC1", "LOGIC2", "LOGIC3"
    status: str = "open"  # open, partially_closed, closed
    trade_id: Optional[int] = None
    open_time: str
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    position_open: float = 100  # Percentage of position still open
    pnl: Optional[float] = None

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "entry": self.entry,
            "sl": self.sl,
            "tp1": self.tp1,
            "tp2": self.tp2,
            "tp3": self.tp3,
            "lot_size": self.lot_size,
            "direction": self.direction,
            "strategy": self.strategy,
            "status": self.status,
            "trade_id": self.trade_id,
            "open_time": self.open_time,
            "tp1_hit": self.tp1_hit,
            "tp2_hit": self.tp2_hit,
            "tp3_hit": self.tp3_hit,
            "position_open": self.position_open,
            "pnl": self.pnl
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)