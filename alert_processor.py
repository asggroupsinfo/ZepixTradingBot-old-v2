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
            print(f"📨 Received alert: {alert_data}")  # DEBUG LOGGING
            
            alert = Alert(**alert_data)
            
            # Check if alert is duplicate
            if self.is_duplicate_alert(alert):
                print("❌ Duplicate alert detected")
                return False
                
            # Check if symbol is valid
            if not self.is_valid_symbol(alert.symbol):
                print(f"❌ Invalid symbol: {alert.symbol}")
                return False
                
            # Check if timeframe is valid
            if alert.tf not in ['1h', '15m', '5m']:
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
            self.clean_old_alerts()
            
            print("✅ Alert validation successful")
            return True
            
        except Exception as e:
            print(f"❌ Alert validation error: {str(e)}")
            return False

    def is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if this is a duplicate alert"""
        current_time = datetime.now()
        
        for recent_alert in self.recent_alerts:
            if (recent_alert.type == alert.type and
                recent_alert.symbol == alert.symbol and
                recent_alert.tf == alert.tf and
                recent_alert.signal == alert.signal):
                return True
                
        return False

    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid for trading"""
        valid_symbols = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD']
        return symbol in valid_symbols

    def clean_old_alerts(self):
        """Remove alerts older than the alert window"""
        current_time = datetime.now()
        self.recent_alerts = [
        alert for alert in self.recent_alerts
        if alert.raw_data and current_time - datetime.fromisoformat(alert.raw_data.get('timestamp', current_time.isoformat())) < self.alert_window
    ]

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