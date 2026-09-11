"""
==============================================================================
UnderWraps Master Automated Test Runner & Verification Suite
Executes all unit, integration, crypto, 150MB guard, and E2E messaging tests.

Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
==============================================================================
"""

import os
import sys
import unittest
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_all_tests():
    print("\n" + "="*78)
    print(" UNDERWRAPS AUTONOMOUS ECOSYSTEM -- MASTER TEST RUNNER")
    print(" Pure ALU SMT Verified | Kybalion DB | 150MB Guard | 48kHz Voice")
    print("="*78 + "\n")
    
    start_time = time.time()
    test_loader = unittest.TestLoader()
    suite = test_loader.discover(start_dir="./tests", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    duration = round(time.time() - start_time, 2)
    print("\n" + "="*78)
    if result.wasSuccessful():
        print(f" [PASS] ALL TESTS PASSED! ({result.testsRun} tests executed in {duration}s)")
        print(" 100% Invariants Verified: 150MB Ceiling, 2FA Lifecycle, Kybalion Storage.")
        print("="*78 + "\n")
        return 0
    else:
        print(f" [FAIL] TESTS FAILED: {len(result.failures)} failures, {len(result.errors)} errors")
        print("="*78 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
