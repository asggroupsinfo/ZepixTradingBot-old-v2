import sqlite3
from datetime import datetime
from models import Trade

class TradeDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('trading_bot.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                trade_id TEXT,
                symbol TEXT,
                entry_price REAL,
                exit_price REAL,
                sl_price REAL,
                tp_price REAL,
                lot_size REAL,
                direction TEXT,
                strategy TEXT,
                pnl REAL,
                status TEXT,
                open_time DATETIME,
                close_time DATETIME
            )
        ''')
        self.conn.commit()

    def save_trade(self, trade: Trade):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (None, trade.trade_id, trade.symbol, trade.entry, trade.exit_price, 
              trade.sl, trade.tp, trade.lot_size, trade.direction, trade.strategy,
              trade.pnl, trade.status, trade.open_time, trade.close_time))
        self.conn.commit()

    def get_trade_history(self, days=30):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM trades 
            WHERE close_time >= datetime('now', ?)
            ORDER BY close_time DESC
        ''', (f'-{days} days',))
        return cursor.fetchall()