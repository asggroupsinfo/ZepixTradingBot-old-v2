import os
import sys
import ctypes
import subprocess
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_mt5_installation():
    possible_paths = [
        r"C:\Program Files\XM Global MT5",
        r"C:\Program Files\MetaTrader 5",
        r"C:\Program Files (x86)\XM Global MT5",
        r"C:\Program Files (x86)\MetaTrader 5",
        r"C:\Program Files\XM MT5",
        r"C:\Program Files\Exness MT5",
        r"C:\Program Files\FTMO MT5",
    ]
    
    print("🔍 Searching for MetaTrader 5 installation...")
    
    for path in possible_paths:
        terminal_path = os.path.join(path, "terminal64.exe")
        if os.path.exists(terminal_path):
            print(f"✅ Found MT5 at: {path}")
            return path
    
    print("❌ MetaTrader 5 not found in standard locations.")
    print("\n📝 Please install MT5 from your broker or specify custom path.")
    return None

def create_symlink(source, target):
    if os.path.exists(target):
        if os.path.islink(target):
            print(f"✅ Symlink already exists: {target}")
            return True
        else:
            print(f"⚠️  Directory exists but is not a symlink: {target}")
            return False
    
    try:
        if not is_admin():
            print("⚠️  Need administrator privileges to create symlink...")
            print("🔄 Requesting admin access...")
            
            script_path = os.path.abspath(__file__)
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script_path}"', None, 1
            )
            sys.exit(0)
        
        os.symlink(source, target, target_is_directory=True)
        print(f"✅ Symlink created: {target} -> {source}")
        return True
    except Exception as e:
        print(f"❌ Failed to create symlink: {e}")
        return False

def verify_mt5_connection():
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            print("⚠️  MT5 initialize failed. Make sure MT5 terminal is installed and logged in.")
            return False
        
        account_info = mt5.account_info()
        if account_info:
            print(f"✅ MT5 Connected Successfully!")
            print(f"   Account: {account_info.login}")
            print(f"   Balance: ${account_info.balance:.2f}")
            print(f"   Server: {account_info.server}")
        
        mt5.shutdown()
        return True
    except ImportError:
        print("⚠️  MetaTrader5 package not installed. Run: pip install MetaTrader5")
        return False
    except Exception as e:
        print(f"❌ MT5 connection error: {e}")
        return False

def main():
    print("="*60)
    print("MT5 AUTO-CONNECTION SETUP")
    print("="*60)
    
    mt5_path = find_mt5_installation()
    
    if not mt5_path:
        print("\n❌ Setup failed: MT5 installation not found")
        input("\nPress Enter to exit...")
        return False
    
    standard_path = r"C:\Program Files\MetaTrader 5"
    
    if mt5_path != standard_path:
        print(f"\n🔗 Creating symlink for Python MT5 package compatibility...")
        if not create_symlink(mt5_path, standard_path):
            print("\n❌ Setup failed: Could not create symlink")
            input("\nPress Enter to exit...")
            return False
    
    print("\n🔍 Verifying MT5 connection...")
    if verify_mt5_connection():
        print("\n✅ MT5 AUTO-SETUP COMPLETE!")
        return True
    else:
        print("\n⚠️  MT5 installed but connection failed.")
        print("   Please make sure MT5 terminal is running and logged in.")
        return False

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
