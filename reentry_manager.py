from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from models import Trade, ReEntryChain
import uuid

class ReEntryManager:
    """Manage re-entry chains and SL hunting protection"""
    
    def __init__(self, config):
        self.config = config
        self.active_chains = {}  # chain_id -> ReEntryChain
        self.recent_sl_hits = {}  # symbol -> list of recent SL hits
        self.completed_tps = {}  # symbol -> recent TP completions
        
    def create_chain(self, trade: Trade) -> ReEntryChain:
        """Create a new re-entry chain from initial trade"""
        
        chain_id = f"{trade.symbol}_{uuid.uuid4().hex[:8]}"
        
        # Handle simulation mode where trade_id might be None
        # Use negative timestamp-based ID for simulation trades
        trade_ids = []
        if trade.trade_id is not None:
            trade_ids = [trade.trade_id]
        else:
            # Create a pseudo-ID for simulation mode
            sim_id = int(datetime.now().timestamp() * 1000) % 1000000
            trade_ids = [sim_id]
            print(f"ℹ️ Simulation mode: Using pseudo trade ID {sim_id}")
        
        chain = ReEntryChain(
            chain_id=chain_id,
            symbol=trade.symbol,
            direction=trade.direction,
            original_entry=trade.entry,
            original_sl_distance=abs(trade.entry - trade.sl),
            current_level=1,
            max_level=self.config["re_entry_config"]["max_chain_levels"],
            trades=trade_ids,
            created_at=datetime.now().isoformat(),
            last_update=datetime.now().isoformat()
        )
        
        self.active_chains[chain_id] = chain
        trade.chain_id = chain_id
        
        return chain
    
    def check_reentry_opportunity(self, symbol: str, signal: str, 
                                 price: float) -> Dict[str, Any]:
        """Check if new signal qualifies for re-entry"""
        
        result = {
            "is_reentry": False,
            "type": None,  # "tp_continuation" or "sl_recovery"
            "chain_id": None,
            "level": 1,
            "sl_adjustment": 1.0
        }
        
        # Check for TP continuation
        tp_opportunity = self._check_tp_continuation(symbol, signal, price)
        if tp_opportunity["eligible"]:
            result["is_reentry"] = True
            result["type"] = "tp_continuation"
            result["chain_id"] = tp_opportunity["chain_id"]
            result["level"] = tp_opportunity["level"]
            result["sl_adjustment"] = tp_opportunity["sl_adjustment"]
            return result
        
        # Check for SL recovery
        sl_opportunity = self._check_sl_recovery(symbol, signal, price)
        if sl_opportunity["eligible"]:
            result["is_reentry"] = True
            result["type"] = "sl_recovery"
            result["level"] = 1
            result["sl_adjustment"] = 0.8  # 80% of original SL for recovery
            return result
        
        return result
    
    def _check_tp_continuation(self, symbol: str, signal: str, 
                              price: float) -> Dict[str, Any]:
        """Check if this is a continuation after TP hit"""
        
        result = {"eligible": False}
        
        if symbol not in self.completed_tps:
            return result
        
        recent_tps = self.completed_tps[symbol]
        current_time = datetime.now()
        
        for tp_event in recent_tps:
            time_since_tp = current_time - tp_event["time"]
            
            # Check if within continuation window
            if time_since_tp > timedelta(minutes=self.config["re_entry_config"]["recovery_window_minutes"]):
                continue
            
            # Check if same direction
            signal_direction = "buy" if signal in ["buy", "bull"] else "sell"
            if signal_direction != tp_event["direction"]:
                continue
            
            # Check if we haven't exceeded max levels
            chain = self.active_chains.get(tp_event["chain_id"])
            if chain and chain.current_level < chain.max_level:
                result["eligible"] = True
                result["chain_id"] = chain.chain_id
                result["level"] = chain.current_level + 1
                
                # Calculate SL adjustment
                reduction_per_level = self.config["re_entry_config"]["sl_reduction_per_level"]
                result["sl_adjustment"] = (1 - reduction_per_level) ** (result["level"] - 1)
                
                break
        
        return result
    
    def _check_sl_recovery(self, symbol: str, signal: str, 
                          price: float) -> Dict[str, Any]:
        """Check if this is a recovery after SL hit"""
        
        result = {"eligible": False}
        
        if symbol not in self.recent_sl_hits:
            return result
        
        recent_sls = self.recent_sl_hits[symbol]
        current_time = datetime.now()
        
        for sl_event in recent_sls:
            time_since_sl = current_time - sl_event["time"]
            
            # Check if within recovery window
            if time_since_sl > timedelta(minutes=self.config["re_entry_config"]["recovery_window_minutes"]):
                continue
            
            # Check if same direction
            signal_direction = "buy" if signal in ["buy", "bull"] else "sell"
            if signal_direction != sl_event["direction"]:
                continue
            
            # Check if price has recovered to near original entry
            recovery_zone = 0.001 if symbol != "XAUUSD" else 1.0  # 10 pips for forex, 100 points for gold
            if abs(price - sl_event["original_entry"]) <= recovery_zone:
                result["eligible"] = True
                break
        
        return result
    
    def record_tp_hit(self, trade: Trade, tp_price: float):
        """Record TP hit for continuation tracking"""
        
        if trade.symbol not in self.completed_tps:
            self.completed_tps[trade.symbol] = []
        
        # Keep only recent TPs (last 30 minutes)
        self._clean_old_events(self.completed_tps[trade.symbol])
        
        self.completed_tps[trade.symbol].append({
            "time": datetime.now(),
            "chain_id": trade.chain_id,
            "direction": trade.direction,
            "tp_price": tp_price,
            "original_entry": trade.original_entry or trade.entry
        })
        
        # Update chain status
        if trade.chain_id in self.active_chains:
            chain = self.active_chains[trade.chain_id]
            chain.total_profit += abs(tp_price - trade.entry) * trade.lot_size * 10000
            chain.last_update = datetime.now().isoformat()
    
    def record_sl_hit(self, trade: Trade):
        """Record SL hit for recovery tracking"""
        
        if trade.symbol not in self.recent_sl_hits:
            self.recent_sl_hits[trade.symbol] = []
        
        # Keep only recent SLs (last 30 minutes)
        self._clean_old_events(self.recent_sl_hits[trade.symbol])
        
        self.recent_sl_hits[trade.symbol].append({
            "time": datetime.now(),
            "direction": trade.direction,
            "sl_price": trade.sl,
            "original_entry": trade.original_entry or trade.entry
        })
        
        # Mark chain as stopped if it exists
        if trade.chain_id in self.active_chains:
            self.active_chains[trade.chain_id].status = "stopped"
    
    def _clean_old_events(self, events: List[Dict]):
        """Remove events older than recovery window"""
        
        current_time = datetime.now()
        window = timedelta(minutes=self.config["re_entry_config"]["recovery_window_minutes"])
        
        events[:] = [e for e in events if current_time - e["time"] <= window]
    
    def update_chain_level(self, chain_id: str, new_trade_id: int):
        """Update chain when new re-entry is placed"""
        
        if chain_id in self.active_chains:
            chain = self.active_chains[chain_id]
            chain.current_level += 1
            
            # Handle None trade_id for simulation mode
            if new_trade_id is not None:
                chain.trades.append(new_trade_id)
            else:
                # Create pseudo-ID for simulation
                sim_id = int(datetime.now().timestamp() * 1000) % 1000000
                chain.trades.append(sim_id)
                print(f"ℹ️ Simulation mode: Using pseudo trade ID {sim_id} for re-entry")
            
            chain.last_update = datetime.now().isoformat()
            
            if chain.current_level >= chain.max_level:
                chain.status = "completed"