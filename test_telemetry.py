#!/usr/bin/env python3
"""
Test telemetry logging and human override tracking
"""

import json
from pathlib import Path
from aicouncil import ConvergenceEngine, Critique, Iteration
from datetime import datetime

def test_human_override_field():
    """Test that human_override field is properly set"""
    print("\n1. Testing human_override field...")
    
    iteration = Iteration(
        iteration_number=1,
        proposer="gpt",
        critics=["copilot", "claude"],
        timestamp=datetime.now().isoformat()
    )
    
    # Test setting human_override
    iteration.human_override = "accepted"
    iteration.notes = "Test note"
    
    # Convert to dict
    iter_dict = iteration.to_dict()
    
    assert 'human_override' in iter_dict, "human_override field missing"
    assert iter_dict['human_override'] == "accepted", f"Expected 'accepted', got {iter_dict['human_override']}"
    assert 'notes' in iter_dict, "notes field missing"
    assert iter_dict['notes'] == "Test note", f"Expected 'Test note', got {iter_dict['notes']}"
    
    print("   ✓ PASS: human_override and notes fields present and correct")

def test_telemetry_logging():
    """Test telemetry JSONL logging"""
    print("\n2. Testing telemetry JSONL logging...")
    
    # Create temp output dir
    output_dir = Path("test_telemetry_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create engine
    engine = ConvergenceEngine(models=["gpt", "copilot"], max_iterations=2, output_dir=str(output_dir))
    
    # Create test iteration
    iteration = Iteration(
        iteration_number=1,
        proposer="gpt",
        critics=["copilot"],
        timestamp=datetime.now().isoformat()
    )
    
    iteration.human_choice = "a"
    iteration.human_override = "accepted"
    iteration.notes = "All good"
    iteration.ship_it = True
    iteration.quality_score = 95.0
    iteration.improvement_delta = 5.0
    iteration.remaining_issues = []
    iteration.critic_statuses = {"copilot": "APPROVED"}
    iteration.applied_critiques = [
        Critique(
            critic="copilot",
            category="style",
            severity=2,
            location="line 10",
            description="Minor style issue",
            suggested_change="Fix style"
        )
    ]
    
    # Log telemetry
    engine._log_telemetry(iteration)
    
    # Check telemetry file exists
    telemetry_file = output_dir / "telemetry.jsonl"
    assert telemetry_file.exists(), "Telemetry file not created"
    
    # Read and verify content
    with open(telemetry_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"
    
    entry = json.loads(lines[0])
    
    # Verify required fields
    required_fields = [
        'iteration', 'agent_initiator', 'agent_responses', 
        'applied_critiques', 'improvement_delta', 'remaining_issues',
        'ship_it', 'human_override', 'notes', 'timestamp'
    ]
    
    for field in required_fields:
        assert field in entry, f"Missing required field: {field}"
    
    # Verify values
    assert entry['iteration'] == 1, f"Expected iteration 1, got {entry['iteration']}"
    assert entry['agent_initiator'] == "gpt", f"Expected gpt, got {entry['agent_initiator']}"
    assert entry['ship_it'] == True, f"Expected True, got {entry['ship_it']}"
    assert entry['human_override'] == "accepted", f"Expected 'accepted', got {entry['human_override']}"
    assert entry['notes'] == "All good", f"Expected 'All good', got {entry['notes']}"
    assert entry['improvement_delta'] == 5.0, f"Expected 5.0, got {entry['improvement_delta']}"
    assert entry['remaining_issues'] == [], f"Expected empty list, got {entry['remaining_issues']}"
    assert len(entry['applied_critiques']) == 1, f"Expected 1 critique, got {len(entry['applied_critiques'])}"
    
    print("   ✓ PASS: Telemetry JSONL file created with all required fields")
    
    # Cleanup
    import shutil
    shutil.rmtree(output_dir)

def test_telemetry_append():
    """Test that telemetry logs append (multiple iterations)"""
    print("\n3. Testing telemetry append mode...")
    
    # Create temp output dir
    output_dir = Path("test_telemetry_append")
    output_dir.mkdir(exist_ok=True)
    
    # Create engine
    engine = ConvergenceEngine(models=["gpt", "copilot"], max_iterations=2, output_dir=str(output_dir))
    
    # Log multiple iterations
    for i in range(1, 4):
        iteration = Iteration(
            iteration_number=i,
            proposer="gpt",
            critics=["copilot"],
            timestamp=datetime.now().isoformat()
        )
        iteration.human_override = "accepted"
        iteration.ship_it = False
        iteration.quality_score = 80.0 + i
        iteration.improvement_delta = i
        iteration.remaining_issues = []
        iteration.critic_statuses = {"copilot": "TIGHTEN_ONLY"}
        
        engine._log_telemetry(iteration)
    
    # Check telemetry file
    telemetry_file = output_dir / "telemetry.jsonl"
    assert telemetry_file.exists(), "Telemetry file not created"
    
    # Read and verify content
    with open(telemetry_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
    
    # Verify each entry
    for i, line in enumerate(lines, 1):
        entry = json.loads(line)
        assert entry['iteration'] == i, f"Expected iteration {i}, got {entry['iteration']}"
        assert entry['improvement_delta'] == i, f"Expected delta {i}, got {entry['improvement_delta']}"
    
    print("   ✓ PASS: Telemetry correctly appends multiple iterations")
    
    # Cleanup
    import shutil
    shutil.rmtree(output_dir)

def test_telemetry_failure_non_blocking():
    """Test that telemetry failures don't block convergence"""
    print("\n4. Testing telemetry failure is non-blocking...")
    
    # Create temp output dir
    output_dir = Path("test_telemetry_fail")
    output_dir.mkdir(exist_ok=True)
    
    # Create engine
    engine = ConvergenceEngine(models=["gpt", "copilot"], max_iterations=2, output_dir=str(output_dir))
    
    # Make telemetry file read-only to force failure
    telemetry_file = output_dir / "telemetry.jsonl"
    telemetry_file.write_text("")
    telemetry_file.chmod(0o444)  # Read-only
    
    # Create test iteration
    iteration = Iteration(
        iteration_number=1,
        proposer="gpt",
        critics=["copilot"],
        timestamp=datetime.now().isoformat()
    )
    iteration.human_override = "accepted"
    
    # This should not raise an exception
    try:
        engine._log_telemetry(iteration)
        print("   ✓ PASS: Telemetry failure handled gracefully (non-blocking)")
    except Exception as e:
        print(f"   ✗ FAIL: Telemetry failure raised exception: {e}")
        raise
    finally:
        # Cleanup
        telemetry_file.chmod(0o644)  # Restore permissions
        import shutil
        shutil.rmtree(output_dir)

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Telemetry and Human Override Features")
    print("=" * 60)
    
    test_human_override_field()
    test_telemetry_logging()
    test_telemetry_append()
    test_telemetry_failure_non_blocking()
    
    print("\n" + "=" * 60)
    print("Results: 4/4 tests passed")
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
