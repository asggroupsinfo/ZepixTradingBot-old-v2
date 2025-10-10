#!/usr/bin/env python3
"""
Final validation script for dual SL system
Tests accurate P&L calculations for both SL-1 and SL-2 with Gold pip fix verification
"""

from config import Config
from pip_calculator import PipCalculator

def test_gold_pnl_calculation():
    """Test Gold P&L calculation with the pip value fix"""
    print("\n" + "="*80)
    print("TEST 1: GOLD P&L CALCULATION (Pip Value Fix Verification)")
    print("="*80)
    
    config = Config()
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})
    config.update("account_balance", 10000)
    
    calculator = PipCalculator(config)
    
    # XAUUSD @ $10k, SL-1 = 1500 pips, risk cap = $150
    # Expected lot = 0.10 (to stay within $150 risk)
    params = calculator.calculate_trade_params(
        symbol="XAUUSD",
        entry_price=2500.00,
        direction="BUY",
        balance=10000
    )
    
    print(f"\nXAUUSD SL-1 @ $10k:")
    print(f"  Entry: 2500.00")
    print(f"  SL Distance: {params['sl_pips']} pips")
    print(f"  Lot Size: {params['lot_size']}")
    print(f"  Expected Loss at SL: ${params['expected_loss']:.2f}")
    print(f"  Risk Cap: ${params['risk_cap']:.2f}")
    
    # Verify pip value calculation (CRITICAL: should use lot_size * 1, not lot_size * 100)
    expected_pip_value = params['lot_size'] * 1  # Correct calculation
    wrong_pip_value = params['lot_size'] * 100    # Old bug
    
    print(f"\n  Pip Value (CORRECT): ${expected_pip_value:.2f} per pip")
    print(f"  Pip Value (OLD BUG): ${wrong_pip_value:.2f} per pip")
    
    # Calculate expected loss with correct pip value
    correct_loss = params['sl_pips'] * expected_pip_value
    wrong_loss = params['sl_pips'] * wrong_pip_value
    
    print(f"\n  Expected Loss (CORRECT): ${correct_loss:.2f}")
    print(f"  Expected Loss (OLD BUG): ${wrong_loss:.2f}")
    
    # Verify expected loss is within risk cap
    within_cap = params['expected_loss'] <= params['risk_cap'] * 1.1  # 10% tolerance
    
    if within_cap and abs(params['expected_loss'] - correct_loss) < 1:
        print(f"\n  ✅ PASS - Gold pip calculation fixed!")
        return True
    else:
        print(f"\n  ❌ FAIL - P&L calculation issue!")
        return False

def test_sl_system_pnl():
    """Test P&L calculations for both SL-1 and SL-2"""
    print("\n" + "="*80)
    print("TEST 2: SL-1 vs SL-2 P&L COMPARISON")
    print("="*80)
    
    config = Config()
    config.update("account_balance", 10000)
    
    # Test SL-1
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})
    calc1 = PipCalculator(config)
    params1 = calc1.calculate_trade_params("EURUSD", 1.1000, "BUY", 10000)
    
    # Test SL-2
    config.update("active_sl_system", "sl-2")
    calc2 = PipCalculator(config)
    params2 = calc2.calculate_trade_params("EURUSD", 1.1000, "BUY", 10000)
    
    print(f"\nEURUSD @ $10k:")
    print(f"\n  SL-1 ORIGINAL:")
    print(f"    SL Distance: {params1['sl_pips']} pips")
    print(f"    Lot Size: {params1['lot_size']}")
    print(f"    Expected Loss: ${params1['expected_loss']:.2f}")
    
    print(f"\n  SL-2 RECOMMENDED:")
    print(f"    SL Distance: {params2['sl_pips']} pips")
    print(f"    Lot Size: {params2['lot_size']}")
    print(f"    Expected Loss: ${params2['expected_loss']:.2f}")
    
    # Verify both are within risk caps
    sl1_valid = params1['expected_loss'] <= params1['risk_cap'] * 1.1
    sl2_valid = params2['expected_loss'] <= params2['risk_cap'] * 1.1
    
    # Verify SL-2 has tighter SL (less pips) than SL-1
    tighter_sl = params2['sl_pips'] < params1['sl_pips']
    
    if sl1_valid and sl2_valid and tighter_sl:
        print(f"\n  ✅ PASS - Both systems calculate correctly!")
        return True
    else:
        print(f"\n  ❌ FAIL - System comparison issue!")
        return False

def test_reduced_sl_pnl():
    """Test P&L with SL reduction"""
    print("\n" + "="*80)
    print("TEST 3: SL REDUCTION P&L VALIDATION")
    print("="*80)
    
    config = Config()
    config.update("active_sl_system", "sl-1")
    config.update("account_balance", 10000)
    
    # Test without reduction
    config.update("symbol_sl_reductions", {})
    calc_normal = PipCalculator(config)
    params_normal = calc_normal.calculate_trade_params("XAUUSD", 2500.00, "BUY", 10000)
    
    # Test with 20% reduction
    config.update("symbol_sl_reductions", {"XAUUSD": 20})
    calc_reduced = PipCalculator(config)
    params_reduced = calc_reduced.calculate_trade_params("XAUUSD", 2500.00, "BUY", 10000)
    
    print(f"\nXAUUSD SL-1 @ $10k:")
    print(f"\n  NO Reduction:")
    print(f"    SL: {params_normal['sl_pips']} pips")
    print(f"    Lot: {params_normal['lot_size']}")
    print(f"    Expected Loss: ${params_normal['expected_loss']:.2f}")
    
    print(f"\n  20% Reduction:")
    print(f"    SL: {params_reduced['sl_pips']} pips")
    print(f"    Lot: {params_reduced['lot_size']}")
    print(f"    Expected Loss: ${params_reduced['expected_loss']:.2f}")
    
    # Verify reduced SL is 20% less
    expected_reduced_pips = params_normal['sl_pips'] * 0.8
    reduction_correct = abs(params_reduced['sl_pips'] - expected_reduced_pips) <= 1
    
    # Verify lot size increased (since SL is tighter)
    lot_increased = params_reduced['lot_size'] > params_normal['lot_size']
    
    # Verify expected loss still within risk cap
    within_cap = params_reduced['expected_loss'] <= params_reduced['risk_cap'] * 1.1
    
    if reduction_correct and lot_increased and within_cap:
        print(f"\n  ✅ PASS - SL reduction working correctly!")
        return True
    else:
        print(f"\n  ❌ FAIL - Reduction calculation issue!")
        return False

def main():
    """Run all final validation tests"""
    print("\n" + "="*80)
    print(" FINAL VALIDATION - DUAL SL SYSTEM P&L ACCURACY")
    print("="*80)
    
    test1 = test_gold_pnl_calculation()
    test2 = test_sl_system_pnl()
    test3 = test_reduced_sl_pnl()
    
    print("\n" + "="*80)
    print(" VALIDATION SUMMARY")
    print("="*80)
    print(f"Gold Pip Fix Test:     {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"SL System Comparison:  {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"SL Reduction Test:     {'✅ PASS' if test3 else '❌ FAIL'}")
    
    all_pass = test1 and test2 and test3
    print(f"\nFINAL RESULT: {'✅ PRODUCTION READY' if all_pass else '❌ VALIDATION FAILED'}")
    
    # Reset config
    config = Config()
    config.update("active_sl_system", "sl-1")
    config.update("symbol_sl_reductions", {})
    
    return all_pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
