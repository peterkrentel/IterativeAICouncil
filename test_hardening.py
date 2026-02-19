#!/usr/bin/env python3
"""
Unit tests for AI Council CLI - Hardening improvements
"""

import sys
import os
from io import StringIO
from unittest.mock import patch
import tempfile
import shutil

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from aicouncil import ConvergenceEngine, Artifact, Critique, Iteration


def test_minimum_models_assertion():
    """Test that engine requires at least 2 models."""
    print("\n1. Testing minimum models assertion...")
    try:
        engine = ConvergenceEngine(models=['gpt'], max_iterations=2)
        print("   ✗ FAIL: Should have raised assertion")
        return False
    except AssertionError as e:
        print(f"   ✓ PASS: Caught assertion - {e}")
        return True


def test_invalid_human_input_handling():
    """Test that invalid human input is rejected and re-prompted."""
    print("\n2. Testing invalid human input handling...")
    
    models = ['gpt', 'copilot']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir=tempfile.mkdtemp())
    
    # Create mock critiques
    critiques = [
        Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                description='Test issue', suggested_change='Fix it')
    ]
    
    # Simulate invalid inputs followed by valid input
    inputs = ['x', 'invalid', 'r']  # x and invalid are invalid, r is valid
    
    with patch('builtins.input', side_effect=inputs):
        # Capture stdout to verify error messages
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            approved, rejected, should_stop, choice = engine.human_approval_gate(critiques)
            output = mock_stdout.getvalue()
    
    # Verify invalid inputs were rejected
    if '❌ Invalid input' in output and choice == 'r':
        print("   ✓ PASS: Invalid inputs rejected, valid input accepted")
        return True
    else:
        print(f"   ✗ FAIL: Expected invalid input rejection, got choice={choice}")
        return False


def test_selective_apply_with_invalid_input():
    """Test selective apply with invalid input handling."""
    print("\n3. Testing selective apply invalid input...")
    
    models = ['gpt', 'copilot']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir=tempfile.mkdtemp())
    
    critiques = [
        Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                description='Issue 1', suggested_change='Fix 1'),
        Critique(critic='copilot', category='bug-risk', severity=3, location='line 20',
                description='Issue 2', suggested_change='Fix 2')
    ]
    
    # Simulate: invalid, y for first; x, n for second
    inputs = ['invalid', 'y', 'x', 'n']
    
    with patch('builtins.input', side_effect=inputs):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            approved, rejected, should_stop = engine._selective_apply(critiques)
            output = mock_stdout.getvalue()
    
    if len(approved) == 1 and len(rejected) == 1 and '❌ Invalid input' in output:
        print("   ✓ PASS: Selective apply handled invalid input correctly")
        return True
    else:
        print(f"   ✗ FAIL: approved={len(approved)}, rejected={len(rejected)}")
        return False


def test_reject_all_path():
    """Test reject-all critique path."""
    print("\n4. Testing reject-all path...")
    
    models = ['gpt', 'copilot']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir=tempfile.mkdtemp())
    
    critiques = [
        Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                description='Issue 1', suggested_change='Fix 1'),
        Critique(critic='copilot', category='bug-risk', severity=3, location='line 20',
                description='Issue 2', suggested_change='Fix 2')
    ]
    
    with patch('builtins.input', return_value='r'):
        approved, rejected, should_stop, choice = engine.human_approval_gate(critiques)
    
    if len(approved) == 0 and len(rejected) == 2 and choice == 'r':
        print("   ✓ PASS: All critiques rejected correctly")
        return True
    else:
        print(f"   ✗ FAIL: approved={len(approved)}, rejected={len(rejected)}")
        return False


def test_apply_all_path():
    """Test apply-all critique path."""
    print("\n5. Testing apply-all path...")
    
    models = ['gpt', 'copilot']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir=tempfile.mkdtemp())
    
    critiques = [
        Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                description='Issue 1', suggested_change='Fix 1'),
        Critique(critic='copilot', category='bug-risk', severity=3, location='line 20',
                description='Issue 2', suggested_change='Fix 2')
    ]
    
    with patch('builtins.input', return_value='a'):
        approved, rejected, should_stop, choice = engine.human_approval_gate(critiques)
    
    if len(approved) == 2 and len(rejected) == 0 and choice == 'a':
        print("   ✓ PASS: All critiques approved correctly")
        return True
    else:
        print(f"   ✗ FAIL: approved={len(approved)}, rejected={len(rejected)}")
        return False


def test_critique_deduplication():
    """Test critique deduplication edge cases."""
    print("\n6. Testing critique deduplication...")
    
    # Test identical descriptions
    c1 = Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                  description='This code could be simplified', suggested_change='Fix 1')
    c2 = Critique(critic='copilot', category='simplicity', severity=2, location='line 10',
                  description='This code could be simplified', suggested_change='Fix 2')
    
    if c1.is_duplicate(c2):
        print("   ✓ PASS: Identical descriptions detected as duplicates")
    else:
        print("   ✗ FAIL: Should detect identical descriptions as duplicates")
        return False
    
    # Test different categories
    c3 = Critique(critic='gpt', category='security', severity=2, location='line 10',
                  description='This code could be simplified', suggested_change='Fix 1')
    
    if not c1.is_duplicate(c3):
        print("   ✓ PASS: Different categories not duplicates")
    else:
        print("   ✗ FAIL: Different categories should not be duplicates")
        return False
    
    # Test 70% overlap threshold
    c4 = Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                  description='This code could be simplified easily', suggested_change='Fix 1')
    
    if c1.is_duplicate(c4):
        print("   ✓ PASS: 70%+ word overlap detected as duplicates")
        return True
    else:
        print("   ✗ FAIL: Should detect 70%+ overlap as duplicates")
        return False


def test_human_decision_logging():
    """Test that human decisions are logged in iteration."""
    print("\n7. Testing human decision logging...")
    
    iteration = Iteration(
        iteration_number=1,
        proposer='gpt',
        critics=['copilot', 'claude']
    )
    
    # Set human choice
    iteration.human_choice = 'a'
    iteration.applied_critiques = [
        Critique(critic='copilot', category='bug-risk', severity=3, location='line 20',
                description='Issue', suggested_change='Fix')
    ]
    
    # Convert to dict and check
    it_dict = iteration.to_dict()
    
    if 'human_choice' in it_dict and it_dict['human_choice'] == 'a':
        print("   ✓ PASS: Human decision logged in iteration")
        return True
    else:
        print("   ✗ FAIL: Human decision not logged correctly")
        return False


def test_critic_status_tracking():
    """Test per-critic review status tracking."""
    print("\n8. Testing per-critic status tracking...")
    
    models = ['gpt', 'copilot', 'claude']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir=tempfile.mkdtemp())
    
    artifact = Artifact(id='test', version=1, content='test content', history=[])
    
    # Create critiques with different severities
    critiques = [
        Critique(critic='copilot', category='bug-risk', severity=5, location='line 1',
                description='Structural issue', suggested_change='Fix'),
        Critique(critic='claude', category='security', severity=2, location='line 2',
                description='Minor issue', suggested_change='Fix')
    ]
    
    # gpt has no critiques (should be APPROVED)
    # copilot has severity 5 (should be REJECT_STRUCTURAL)
    # claude has severity 2 (should be TIGHTEN_ONLY)
    
    critics = ['gpt', 'copilot', 'claude']
    has_converged, score, reason, statuses = engine.check_convergence(
        critiques, artifact, 'old content', 0.02, critics
    )
    
    if (statuses.get('gpt') == 'APPROVED' and 
        statuses.get('copilot') == 'REJECT_STRUCTURAL' and 
        statuses.get('claude') == 'TIGHTEN_ONLY'):
        print("   ✓ PASS: Critic statuses tracked correctly")
        return True
    else:
        print(f"   ✗ FAIL: Incorrect statuses: {statuses}")
        return False


def test_convergence_all_approved():
    """Test convergence when all critics approved."""
    print("\n9. Testing convergence (all approved)...")
    
    models = ['gpt', 'copilot']
    engine = ConvergenceEngine(models=models, max_iterations=5, output_dir=tempfile.mkdtemp())
    engine.current_iteration = 2  # Set to iteration 2
    
    artifact = Artifact(id='test', version=1, content='test content', history=[])
    
    # No critiques = all approved
    has_converged, score, reason, statuses = engine.check_convergence(
        [], artifact, 'old content', 0.01, ['gpt', 'copilot']
    )
    
    if has_converged and 'APPROVED' in reason:
        print(f"   ✓ PASS: Converged with all approved (score={score:.2f})")
        return True
    else:
        print(f"   ✗ FAIL: Should converge when all approved")
        return False


def test_deterministic_critique_application():
    """Test that critique application is deterministic."""
    print("\n10. Testing deterministic critique application...")
    
    models = ['gpt', 'copilot']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir=tempfile.mkdtemp())
    
    content = "Original content"
    critiques = [
        Critique(critic='copilot', category='bug-risk', severity=3, location='line 20',
                description='Issue B', suggested_change='Fix B'),
        Critique(critic='gpt', category='simplicity', severity=2, location='line 10',
                description='Issue A', suggested_change='Fix A'),
        Critique(critic='claude', category='security', severity=4, location='line 30',
                description='Issue C', suggested_change='Fix C')
    ]
    
    # Apply twice and check if results are identical
    result1 = engine._apply_critiques_to_content(content, critiques)
    result2 = engine._apply_critiques_to_content(content, critiques)
    
    if result1 == result2:
        print("   ✓ PASS: Critique application is deterministic")
        # Verify grouping by category
        if 'BUG-RISK' in result1 and 'SECURITY' in result1 and 'SIMPLICITY' in result1:
            print("   ✓ PASS: Critiques grouped by category")
            return True
        else:
            print("   ✗ FAIL: Critiques not properly grouped")
            return False
    else:
        print("   ✗ FAIL: Results differ between applications")
        return False


def run_all_tests():
    """Run all unit tests."""
    print("="*60)
    print("AI Council CLI - Unit Tests (Hardening)")
    print("="*60)
    
    tests = [
        test_minimum_models_assertion,
        test_invalid_human_input_handling,
        test_selective_apply_with_invalid_input,
        test_reject_all_path,
        test_apply_all_path,
        test_critique_deduplication,
        test_human_decision_logging,
        test_critic_status_tracking,
        test_convergence_all_approved,
        test_deterministic_critique_application
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
