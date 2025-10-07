from typing import Dict, Any, List
from datetime import datetime, timedelta
from config import Config
from models import Alert

class AlertProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.recent_alerts: List[Alert] = []
        self.alert_window = timedelta(minutes=5)
    
    def validate_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Validate incoming alert"""
        try:
            print(f"📨 Received alert: {alert_data}")
            
            # Add timestamp if not present
            if 'timestamp' not in alert_data:
                alert_data['timestamp'] = datetime.now().isoformat()
            
            # Store raw_data properly
            alert = Alert(**alert_data, raw_data=alert_data)
            
            # Clean old alerts BEFORE checking for duplicates
            self.clean_old_alerts()
            
            # Check if alert is duplicate
            if self.is_duplicate_alert(alert):
                print("❌ Duplicate alert detected")
                return False
                
            # Check if symbol is valid
            if not self.is_valid_symbol(alert.symbol):
                print(f"❌ Invalid symbol: {alert.symbol}")
                return False
                
            # Check if timeframe is valid
            if alert.tf not in ['1h', '15m', '5m', '1d']:
                print(f"❌ Invalid timeframe: {alert.tf}")
                return False
                
            # Check if signal type is valid
            if alert.type == 'bias' or alert.type == 'trend':
                if alert.signal not in ['bull', 'bear']:
                    print(f"❌ Invalid signal for {alert.type}: {alert.signal}")
                    return False
            elif alert.type == 'entry':
                if alert.signal not in ['buy', 'sell']:
                    print(f"❌ Invalid signal for {alert.type}: {alert.signal}")
                    return False
                    
            # Store alert
            self.recent_alerts.append(alert)
            
            print("✅ Alert validation successful")
            return True
            
        except Exception as e:
            print(f"❌ Alert validation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if this is a duplicate alert"""
        # Get incoming alert's timestamp
        incoming_timestamp = datetime.now()
        if alert.raw_data and isinstance(alert.raw_data, dict):
            timestamp_str = alert.raw_data.get('timestamp')
            if timestamp_str:
                try:
                    incoming_timestamp = datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError):
                    pass
        
        for recent_alert in self.recent_alerts:
            # Skip alerts older than alert_window relative to incoming alert
            if recent_alert.raw_data and isinstance(recent_alert.raw_data, dict):
                recent_timestamp_str = recent_alert.raw_data.get('timestamp')
                if recent_timestamp_str:
                    try:
                        recent_alert_time = datetime.fromisoformat(recent_timestamp_str)
                        if incoming_timestamp - recent_alert_time >= self.alert_window:
                            continue  # Skip old alerts (>5 min apart)
                    except (ValueError, TypeError):
                        pass  # If timestamp invalid, still check for duplicate
            
            if (recent_alert.type == alert.type and
                recent_alert.symbol == alert.symbol and
                recent_alert.tf == alert.tf and
                recent_alert.signal == alert.signal):
                return True
                
        return False
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid for trading"""
        valid_symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 
                        'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY', 'AUDJPY']
        return symbol in valid_symbols
    
    def clean_old_alerts(self):
        """Remove alerts older than the alert window"""
        try:
            current_time = datetime.now()
            cleaned_alerts = []
            
            for alert in self.recent_alerts:
                timestamp_str = None
                
                if alert.raw_data and isinstance(alert.raw_data, dict):
                    timestamp_str = alert.raw_data.get('timestamp')
                
                if timestamp_str:
                    try:
                        alert_time = datetime.fromisoformat(timestamp_str)
                        if current_time - alert_time < self.alert_window:
                            cleaned_alerts.append(alert)
                    except (ValueError, TypeError):
                        cleaned_alerts.append(alert)
                else:
                    cleaned_alerts.append(alert)
            
            self.recent_alerts = cleaned_alerts
            
        except Exception as e:
            print(f"⚠️ Error cleaning alerts: {str(e)}")
    
    def get_recent_alerts(self, alert_type: str = None, symbol: str = None, tf: str = None) -> List[Alert]:
        """Get recent alerts filtered by type, symbol, or timeframe"""
        filtered = self.recent_alerts
        
        if alert_type:
            filtered = [alert for alert in filtered if alert.type == alert_type]
            
        if symbol:
            filtered = [alert for alert in filtered if alert.symbol == symbol]
            
        if tf:
            filtered = [alert for alert in filtered if alert.tf == tf]
            
        return filtered