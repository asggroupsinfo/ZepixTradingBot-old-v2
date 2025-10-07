#!/usr/bin/env python3
"""Test script to verify credentials are loaded correctly"""
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Test credential loading
print("=" * 50)
print("CREDENTIAL LOADING TEST")
print("=" * 50)

mt5_login = os.getenv("MT5_LOGIN", "NOT_FOUND")
mt5_password = os.getenv("MT5_PASSWORD", "NOT_FOUND")
mt5_server = os.getenv("MT5_SERVER", "NOT_FOUND")
telegram_token = os.getenv("TELEGRAM_TOKEN", "NOT_FOUND")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "NOT_FOUND")

print(f"\nMT5_LOGIN: {mt5_login}")
print(f"MT5_PASSWORD: {'*' * len(mt5_password) if mt5_password != 'NOT_FOUND' else 'NOT_FOUND'}")
print(f"MT5_SERVER: {mt5_server}")
print(f"TELEGRAM_TOKEN: {'*' * 20 if telegram_token != 'NOT_FOUND' else 'NOT_FOUND'}")
print(f"TELEGRAM_CHAT_ID: {telegram_chat_id}")

print("\n" + "=" * 50)

# Now test Config class
from config import Config

config = Config()

print("\nCONFIG CLASS TEST")
print("=" * 50)
print(f"MT5 Login (from Config): {config['mt5_login']}")
print(f"MT5 Password (from Config): {'*' * len(str(config['mt5_password'])) if config['mt5_password'] else 'EMPTY'}")
print(f"MT5 Server (from Config): {config['mt5_server']}")
print("=" * 50)

if config['mt5_login'] and config['mt5_password'] and config['mt5_server']:
    print("\n✅ ALL CREDENTIALS LOADED SUCCESSFULLY!")
else:
    print("\n❌ CREDENTIALS MISSING - Check your .env file")
