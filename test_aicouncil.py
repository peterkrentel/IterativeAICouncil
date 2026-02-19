#!/usr/bin/env python3
"""
Test script for AI Council CLI - non-interactive version for testing
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from aicouncil import ConvergenceEngine, Artifact, Critique

def test_basic_workflow():
    """Test basic workflow without human interaction."""
    print("="*60)
    print("Testing AI Council CLI - Automated Test")
    print("="*60)
    
    # Create a simple test
    models = ['gpt', 'copilot', 'claude']
    engine = ConvergenceEngine(models=models, max_iterations=2, output_dir='./test_output')
    
    # Test artifact loading
    print("\n1. Testing artifact loading...")
    artifact = engine.load_artifact('sample_input.md')
    assert artifact is not None
    assert artifact.version == 1
    print("   ✓ Artifact loaded successfully")
    
    # Test proposer
    print("\n2. Testing proposer...")
    revised = engine.run_proposer('gpt', artifact, 1)
    assert revised is not None
    print("   ✓ Proposer generated revision")
    
    # Test critics
    print("\n3. Testing critics...")
    temp_artifact = Artifact(
        id=artifact.id,
        version=artifact.version,
        content=revised,
        history=[]
    )
    critiques = engine.run_critics(['copilot', 'claude'], temp_artifact, 1)
    assert len(critiques) > 0
    print(f"   ✓ Critics generated {len(critiques)} critiques")
    
    # Test critique consolidation
    print("\n4. Testing critique consolidation...")
    consolidated = engine.consolidate_critiques(critiques)
    assert len(consolidated) <= len(critiques)
    print(f"   ✓ Consolidated to {len(consolidated)} unique critiques")
    
    # Test convergence check
    print("\n5. Testing convergence check...")
    has_converged, score, reason, statuses, ship_it, quality_score, remaining_issues = engine.check_convergence([], artifact, artifact.content)
    print(f"   Convergence score: {score:.2f}")
    print(f"   Quality score: {quality_score:.1f}")
    print(f"   Ship it: {ship_it}")
    print(f"   Remaining issues: {len(remaining_issues)}")
    print(f"   ✓ Convergence check completed")
    
    # Test output saving
    print("\n6. Testing output saving...")
    engine.artifact = artifact
    engine.save_outputs()
    print("   ✓ Outputs saved successfully")
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)

if __name__ == '__main__':
    test_basic_workflow()
