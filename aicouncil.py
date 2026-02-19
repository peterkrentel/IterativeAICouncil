#!/usr/bin/env python3
"""
AI Council CLI - Iterative Convergence Engine
==============================================

CLI-based tool for iterative artifact refinement using multiple AI models
acting as proposer and critics.

Usage:
    aicouncil converge input.md --models gpt,copilot,augment --max-iterations 4
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import difflib
import shutil


@dataclass
class Artifact:
    """
    Represents the artifact being refined.
    
    Attributes:
        id: Unique identifier for the artifact
        version: Current version number
        content: Current content of the artifact
        history: List of applied changes with metadata
    """
    id: str
    version: int
    content: str
    history: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert artifact to dictionary."""
        return asdict(self)
    
    def apply_change(self, change_description: str, new_content: str) -> None:
        """Apply a change to the artifact and update history."""
        self.history.append({
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            'change': change_description,
            'content_length': len(new_content)
        })
        self.content = new_content
        self.version += 1


@dataclass
class Critique:
    """
    Structured critique from a critic model.
    
    Attributes:
        critic: Name of the critic model
        category: Category of the critique
        severity: Severity level (1-5)
        location: Optional location in the artifact
        description: Description of the issue
        suggested_change: Suggested change to address the issue
    """
    critic: str
    category: str  # architecture|performance|security|simplicity|bug-risk|style
    severity: int  # 1-5
    location: Optional[str]
    description: str
    suggested_change: str
    
    def __post_init__(self):
        """Validate critique fields after initialization."""
        # Validate severity is in range 1-5
        if not isinstance(self.severity, int) or not (1 <= self.severity <= 5):
            raise ValueError(f"Critique severity must be an integer between 1 and 5, got: {self.severity}")
        
        # Validate category is valid
        valid_categories = ['architecture', 'performance', 'security', 'simplicity', 'bug-risk', 'style']
        if self.category not in valid_categories:
            raise ValueError(f"Critique category must be one of {valid_categories}, got: {self.category}")
    
    def to_dict(self) -> Dict:
        """Convert critique to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'Critique':
        """Create Critique from dictionary."""
        return Critique(**data)
    
    def is_duplicate(self, other: 'Critique') -> bool:
        """
        Check if this critique is similar to another (for deduplication).
        
        Uses a simple heuristic: 70% word overlap for descriptions in the same category.
        
        NOTE: Future improvement - Use semantic similarity (embeddings) for better deduplication.
        The current word-overlap approach is an MVP heuristic that works for most cases.
        
        Args:
            other: Another critique to compare against
            
        Returns:
            True if critiques are considered duplicates
        """
        # Simple similarity check: same category, similar description
        if self.category != other.category:
            return False
        # Check description similarity (simple word overlap)
        words1 = set(self.description.lower().split())
        words2 = set(other.description.lower().split())
        
        # Handle empty descriptions
        if not words1 and not words2:
            return True  # Both empty, consider duplicates
        if not words1 or not words2:
            return False  # One empty, one not - not duplicates
        
        # 70% overlap threshold (tuned for MVP)
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap > 0.7


@dataclass
class Iteration:
    """
    Represents one iteration of the convergence process.
    
    Attributes:
        iteration_number: Iteration number
        proposer: Name of the proposer model
        critics: List of critic model names
        critiques_received: All critiques received
        applied_critiques: Critiques that were applied
        rejected_critiques: Critiques that were rejected
        diff_summary: Summary of changes made
        convergence_score: Convergence score (0-1)
        quality_score: Quality score (0-100)
        improvement_delta: Improvement from previous iteration (0-100)
        remaining_issues: List of remaining actionable issues
        human_choice: Human decision made ('a', 's', 'r', 'q')
        human_override: Human override status ('accepted', 'rejected', or None)
        notes: Optional notes from human review
        critic_statuses: Per-critic review status
        ship_it: True if all critics approved
        timestamp: ISO timestamp for this iteration
    """
    iteration_number: int
    proposer: str
    critics: List[str]
    critiques_received: List[Critique] = field(default_factory=list)
    applied_critiques: List[Critique] = field(default_factory=list)
    rejected_critiques: List[Critique] = field(default_factory=list)
    diff_summary: str = ""
    convergence_score: float = 0.0
    quality_score: float = 0.0
    improvement_delta: float = 0.0
    remaining_issues: List[str] = field(default_factory=list)
    human_choice: str = ""
    human_override: Optional[str] = None
    notes: Optional[str] = None
    critic_statuses: Dict[str, str] = field(default_factory=dict)
    ship_it: bool = False
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        """Convert iteration to dictionary."""
        return {
            'iteration_number': self.iteration_number,
            'proposer': self.proposer,
            'critics': self.critics,
            'critiques_received': [c.to_dict() for c in self.critiques_received],
            'applied_critiques': [c.to_dict() for c in self.applied_critiques],
            'rejected_critiques': [c.to_dict() for c in self.rejected_critiques],
            'diff_summary': self.diff_summary,
            'convergence_score': self.convergence_score,
            'quality_score': self.quality_score,
            'improvement_delta': self.improvement_delta,
            'remaining_issues': self.remaining_issues,
            'human_choice': self.human_choice,
            'human_override': self.human_override,
            'notes': self.notes,
            'critic_statuses': self.critic_statuses,
            'ship_it': self.ship_it,
            'timestamp': self.timestamp
        }


class ConvergenceEngine:
    """Main convergence engine for iterative artifact refinement."""
    
    VALID_CATEGORIES = ['architecture', 'performance', 'security', 'simplicity', 'bug-risk', 'style']
    
    def __init__(self, models: List[str], max_iterations: int = 5, output_dir: str = "./output"):
        """
        Initialize the convergence engine.
        
        Ensures deterministic model rotation and critic assignment.
        
        Args:
            models: List of model names to use (minimum 2 required)
            max_iterations: Maximum number of iterations (default: 5)
            output_dir: Directory for output files
        """
        # Assert minimum 2 models required
        assert len(models) >= 2, "At least 2 models required (1 proposer + 1 critic minimum)"
        
        self.models = models
        self.max_iterations = max_iterations
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create diff_history directory
        self.diff_dir = self.output_dir / "diff_history"
        self.diff_dir.mkdir(exist_ok=True)
        
        # Iteration tracking
        self.iterations: List[Iteration] = []
        self.current_iteration = 0
        
        # Artifact
        self.artifact: Optional[Artifact] = None
        
        # Telemetry file path
        self.telemetry_file = self.output_dir / "telemetry.jsonl"
        
    def _log_telemetry(self, iteration: 'Iteration') -> None:
        """
        Append iteration telemetry to JSONL log file.
        
        This is side-effect free - failures do not block convergence.
        
        Args:
            iteration: Iteration object to log
        """
        try:
            telemetry_entry = {
                'iteration': iteration.iteration_number,
                'agent_initiator': iteration.proposer,
                'agent_responses': {critic: iteration.critic_statuses.get(critic, 'UNKNOWN') 
                                   for critic in iteration.critics},
                'applied_critiques': [c.to_dict() for c in iteration.applied_critiques],
                'improvement_delta': iteration.improvement_delta,
                'remaining_issues': iteration.remaining_issues,
                'ship_it': iteration.ship_it,
                'human_override': iteration.human_override,
                'notes': iteration.notes,
                'timestamp': iteration.timestamp
            }
            
            # Append to JSONL file
            with open(self.telemetry_file, 'a') as f:
                f.write(json.dumps(telemetry_entry) + '\n')
                
        except Exception as e:
            # Log error but don't block convergence
            print(f"⚠ Telemetry logging failed (non-blocking): {e}")
        
    # STATE 0: Load artifact from CLI
    def load_artifact(self, input_file: str) -> Artifact:
        """
        Load artifact from input file.
        
        Args:
            input_file: Path to input file
            
        Returns:
            Loaded Artifact object
        """
        print(f"\n{'='*60}")
        print("STATE 0: Loading Artifact")
        print(f"{'='*60}")
        
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        content = input_path.read_text()
        artifact_id = input_path.stem
        
        artifact = Artifact(
            id=artifact_id,
            version=1,
            content=content,
            history=[]
        )
        
        print(f"✓ Loaded artifact: {artifact_id}")
        print(f"  Content length: {len(content)} characters")
        print(f"  Initial version: {artifact.version}")
        
        self.artifact = artifact
        return artifact
    
    # STATE 1: Proposer generates revised artifact
    def run_proposer(self, proposer: str, artifact: Artifact, iteration_num: int) -> str:
        """
        Run proposer model to generate revised artifact with error handling.
        
        Args:
            proposer: Name of the proposer model
            artifact: Current artifact
            iteration_num: Current iteration number
            
        Returns:
            Revised artifact content
        """
        print(f"\n{'='*60}")
        print(f"STATE 1: Proposer Generation (Iteration {iteration_num})")
        print(f"{'='*60}")
        print(f"Proposer: {proposer}")
        
        # Call LLM with error handling
        try:
            revised_content = self._call_proposer_llm(proposer, artifact, iteration_num)
            print(f"✓ Proposer generated revision")
            print(f"  Content length: {len(revised_content)} characters")
            return revised_content
        except Exception as e:
            print(f"✗ Error calling proposer LLM: {e}")
            print(f"  Falling back to original content")
            return artifact.content
    
    # STATE 2: Critics run in parallel
    def run_critics(self, critics: List[str], artifact: Artifact, iteration_num: int) -> List[Critique]:
        """
        Run critic models to generate critiques with error handling.
        
        Args:
            critics: List of critic model names
            artifact: Current artifact
            iteration_num: Current iteration number
            
        Returns:
            List of critiques from all critics (empty list from failed critics)
        """
        print(f"\n{'='*60}")
        print(f"STATE 2: Running Critics (Iteration {iteration_num})")
        print(f"{'='*60}")
        print(f"Critics: {', '.join(critics)}")
        
        all_critiques = []
        
        # In a real implementation, these would run in parallel
        for critic in critics:
            print(f"\n  Running {critic}...")
            try:
                critiques = self._call_critic_llm(critic, artifact, iteration_num)
                all_critiques.extend(critiques)
                print(f"  ✓ {critic} returned {len(critiques)} critique(s)")
            except Exception as e:
                print(f"  ✗ {critic} failed: {e}")
                print(f"  ℹ Continuing without critiques from {critic}")
        
        print(f"\n✓ Total critiques received: {len(all_critiques)}")
        return all_critiques
        
        print(f"\n✓ Total critiques received: {len(all_critiques)}")
        return all_critiques
    
    # STATE 3: Consolidate critiques
    def consolidate_critiques(self, critiques: List[Critique]) -> List[Critique]:
        """
        Consolidate critiques by removing duplicates and grouping.
        
        Args:
            critiques: List of all critiques
            
        Returns:
            Consolidated list of unique critiques
        """
        print(f"\n{'='*60}")
        print("STATE 3: Consolidating Critiques")
        print(f"{'='*60}")
        print(f"Initial critiques: {len(critiques)}")
        
        # Remove duplicates
        unique_critiques = []
        for critique in critiques:
            is_duplicate = any(critique.is_duplicate(existing) for existing in unique_critiques)
            if not is_duplicate:
                unique_critiques.append(critique)
        
        # Group by category and location
        grouped = {}
        for critique in unique_critiques:
            key = (critique.category, critique.location or 'general')
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(critique)
        
        print(f"After deduplication: {len(unique_critiques)} unique critique(s)")
        print(f"Grouped into {len(grouped)} category/location combination(s)")
        
        # Display summary
        for (category, location), group in grouped.items():
            print(f"  {category} @ {location}: {len(group)} critique(s)")
        
        return unique_critiques
    
    # STATE 4: Human gate
    def human_approval_gate(self, critiques: List[Critique]) -> Tuple[List[Critique], List[Critique], bool, str]:
        """
        Display critiques and prompt for human approval with input validation.
        
        Args:
            critiques: List of consolidated critiques
            
        Returns:
            Tuple of (approved_critiques, rejected_critiques, should_stop, human_choice)
        """
        print(f"\n{'='*60}")
        print("STATE 4: Human Approval Gate")
        print(f"{'='*60}")
        
        if not critiques:
            print("No critiques to review.")
            return [], [], False, 'n'
        
        # Display critiques
        print(f"\nReceived {len(critiques)} critique(s):\n")
        for i, critique in enumerate(critiques, 1):
            print(f"{i}. [{critique.severity}/5] {critique.category.upper()} - {critique.critic}")
            print(f"   Location: {critique.location or 'General'}")
            print(f"   Issue: {critique.description}")
            print(f"   Suggestion: {critique.suggested_change}")
            print()
        
        # High severity critiques
        high_severity = [c for c in critiques if c.severity >= 3]
        if high_severity:
            print(f"⚠ {len(high_severity)} high-severity critique(s) (severity ≥3)")
        
        # Prompt for approval with validation loop
        print("\nOptions:")
        print("  a - Apply all critiques")
        print("  s - Selective apply (choose which to apply)")
        print("  r - Reject all critiques")
        print("  q - Stop iteration (quit)")
        
        valid_choices = ['a', 's', 'r', 'q']
        choice = None
        
        while choice not in valid_choices:
            user_input = input("\nYour choice [a/s/r/q]: ").strip().lower()
            if user_input in valid_choices:
                choice = user_input
            else:
                print(f"❌ Invalid input '{user_input}'. Please enter one of: a, s, r, q")
        
        if choice == 'q':
            print("Stopping iteration by user request.")
            return [], critiques, True, choice
        elif choice == 'a':
            print(f"Applying all {len(critiques)} critique(s).")
            return critiques, [], False, choice
        elif choice == 'r':
            print(f"Rejecting all {len(critiques)} critique(s).")
            return [], critiques, False, choice
        elif choice == 's':
            approved, rejected, should_stop = self._selective_apply(critiques)
            return approved, rejected, should_stop, choice
        
        # Should never reach here due to validation loop
        return [], critiques, False, choice
    
    def _selective_apply(self, critiques: List[Critique]) -> Tuple[List[Critique], List[Critique], bool]:
        """
        Helper for selective critique application with input validation.
        
        Args:
            critiques: List of critiques to review
            
        Returns:
            Tuple of (approved, rejected, should_stop)
        """
        approved = []
        rejected = []
        valid_choices = ['y', 'n', 'q']
        
        for i, critique in enumerate(critiques, 1):
            print(f"\nCritique {i}/{len(critiques)}:")
            print(f"  [{critique.severity}/5] {critique.category} - {critique.critic}")
            print(f"  {critique.description}")
            
            choice = None
            while choice not in valid_choices:
                user_input = input("  Apply this critique? [y/n/q]: ").strip().lower()
                if user_input in valid_choices:
                    choice = user_input
                else:
                    print(f"  ❌ Invalid input '{user_input}'. Please enter: y, n, or q")
            
            if choice == 'q':
                # User quit - reject remaining critiques (starting from current index i)
                rejected.extend(critiques[i:])
                return approved, rejected, True
            elif choice == 'y':
                approved.append(critique)
            else:
                rejected.append(critique)
        
        print(f"\nApproved: {len(approved)}, Rejected: {len(rejected)}")
        return approved, rejected, False
    
    # STATE 5: Apply approved critiques
    def apply_critiques(self, artifact: Artifact, critiques: List[Critique]) -> str:
        """
        Apply approved critiques to artifact.
        
        Args:
            artifact: Current artifact
            critiques: List of approved critiques
            
        Returns:
            Updated artifact content
        """
        print(f"\n{'='*60}")
        print("STATE 5: Applying Critiques")
        print(f"{'='*60}")
        
        if not critiques:
            print("No critiques to apply. Artifact unchanged.")
            return artifact.content
        
        print(f"Applying {len(critiques)} critique(s)...")
        
        # Placeholder for actual application logic
        # In a real implementation, this would use an LLM to apply the changes
        updated_content = self._apply_critiques_to_content(artifact.content, critiques)
        
        # Update artifact
        change_description = f"Applied {len(critiques)} critiques"
        artifact.apply_change(change_description, updated_content)
        
        print(f"✓ Critiques applied, artifact updated to version {artifact.version}")
        return updated_content
    
    # STATE 6: Convergence check
    def check_convergence(self, critiques: List[Critique], artifact: Artifact, 
                          previous_content: str, diff_ratio: Optional[float] = None,
                          critics: Optional[List[str]] = None) -> Tuple[bool, float, str, Dict[str, str], bool, float, List[str]]:
        """
        Check if convergence has been achieved using multiple criteria.
        
        Convergence logic combines:
        1. Traditional: No high-severity critiques + small diff ratio
        2. Consensus: Per-critic review status
        3. Ship-it flag: All critics APPROVED
        4. Empty critiques: No actionable issues
        
        Critic review statuses:
        - REJECT_STRUCTURAL: Severe structural issues (severity 5)
        - REJECT_MODERATE: Moderate issues (severity 3-4)
        - TIGHTEN_ONLY: Minor issues only (severity 1-2)
        - APPROVED: No critiques from this critic
        
        Args:
            critiques: Remaining/unapplied critiques
            artifact: Current artifact
            previous_content: Previous artifact content
            diff_ratio: Pre-calculated diff ratio (optional, will calculate if not provided)
            critics: List of critic names to assess
            
        Returns:
            Tuple of (has_converged, convergence_score, reason, critic_statuses, ship_it, quality_score, remaining_issues)
        """
        print(f"\n{'='*60}")
        print("STATE 6: Convergence Check")
        print(f"{'='*60}")
        
        # Calculate per-critic review status
        critic_statuses = {}
        if critics:
            for critic in critics:
                critic_critiques = [c for c in critiques if c.critic == critic]
                
                if not critic_critiques:
                    critic_statuses[critic] = 'APPROVED'
                else:
                    max_severity = max(c.severity for c in critic_critiques)
                    if max_severity >= 5:
                        critic_statuses[critic] = 'REJECT_STRUCTURAL'
                    elif max_severity >= 3:
                        critic_statuses[critic] = 'REJECT_MODERATE'
                    else:
                        critic_statuses[critic] = 'TIGHTEN_ONLY'
        
        # Display critic statuses
        print("\nPer-Critic Review Status:")
        for critic, status in critic_statuses.items():
            print(f"  {critic}: {status}")
        
        # Check ship_it flag: All critics approved
        ship_it = all(status == 'APPROVED' for status in critic_statuses.values()) if critic_statuses else False
        
        if ship_it:
            print(f"\n🚀 SHIP IT! All critics APPROVED")
        
        # Build remaining issues list (actionable critiques only)
        remaining_issues = []
        for critique in critiques:
            if critique.severity >= 3:  # Only include actionable issues (severity >= 3)
                issue_desc = f"[{critique.category}] {critique.description}"
                if critique.location:
                    issue_desc += f" @ {critique.location}"
                remaining_issues.append(issue_desc)
        
        print(f"\nActionable issues remaining: {len(remaining_issues)}")
        
        # Check 1: Traditional high-severity check
        high_severity_remaining = [c for c in critiques if c.severity >= 3]
        no_high_severity = len(high_severity_remaining) == 0
        
        print(f"High-severity critiques remaining: {len(high_severity_remaining)}")
        
        # Check 2: Structural diff < 5%
        if diff_ratio is None:
            diff_ratio = self._calculate_diff_ratio(previous_content, artifact.content)
        small_diff = diff_ratio < 0.05
        
        print(f"Structural diff: {diff_ratio*100:.2f}%")
        
        # Check 3: Max iterations reached
        max_iterations_reached = self.current_iteration >= self.max_iterations
        
        print(f"Iteration: {self.current_iteration}/{self.max_iterations}")
        
        # Check 4: Empty critiques (anti-loop protection)
        no_critiques = len(critiques) == 0
        
        # Calculate convergence score (0.0 - 1.0) combining both approaches
        convergence_score = 0.0
        
        # Consensus-based component (60% weight)
        if ship_it:
            consensus_score = 1.0
        elif all(status in ['APPROVED', 'TIGHTEN_ONLY'] for status in critic_statuses.values()):
            consensus_score = 0.8
        else:
            # Calculate based on status distribution
            approved_count = sum(1 for s in critic_statuses.values() if s == 'APPROVED')
            tighten_count = sum(1 for s in critic_statuses.values() if s == 'TIGHTEN_ONLY')
            total_critics = len(critic_statuses) if critic_statuses else 1
            consensus_score = (approved_count * 1.0 + tighten_count * 0.8) / total_critics
        
        # Traditional component (40% weight)
        traditional_score = 0.0
        if no_high_severity:
            traditional_score += 0.5
        if small_diff:
            traditional_score += 0.3
        traditional_score += min(0.2, (1 - diff_ratio) * 0.2)
        
        # Combined score
        convergence_score = (consensus_score * 0.6) + (traditional_score * 0.4)
        
        # Calculate quality score (0-100 scale)
        # Quality is inverse of remaining issues, weighted by severity
        if not critiques:
            quality_score = 100.0
        else:
            # Deduct points based on severity
            total_deduction = sum(
                20 if c.severity >= 5 else
                10 if c.severity >= 3 else
                3 if c.severity >= 2 else 1
                for c in critiques
            )
            quality_score = max(0.0, 100.0 - total_deduction)
        
        print(f"Convergence score: {convergence_score:.2f}")
        print(f"Quality score: {quality_score:.1f}/100")
        
        # Determine convergence using multiple criteria
        has_converged = False
        reason = ""
        
        # Priority 1: Empty critiques (anti-loop protection)
        if self.current_iteration >= 1 and no_critiques:
            has_converged = True
            reason = "No critiques received - converged"
        # Priority 2: Ship it flag (strongest signal)
        elif self.current_iteration >= 1 and ship_it:
            has_converged = True
            reason = "All critics APPROVED - ship it! 🚀"
        # Priority 3: Traditional convergence (backward compatible)
        elif self.current_iteration >= 1 and no_high_severity and small_diff:
            has_converged = True
            reason = "No high-severity critiques and minimal changes"
        # Priority 4: Consensus convergence (all tighten only after 2+ iterations)
        elif self.current_iteration >= 2 and all(status in ['APPROVED', 'TIGHTEN_ONLY'] for status in critic_statuses.values()):
            has_converged = True
            reason = "All critics at TIGHTEN_ONLY or better - acceptable quality"
        # Priority 5: Max iterations (fallback)
        elif max_iterations_reached:
            has_converged = True
            reason = f"Maximum iterations ({self.max_iterations}) reached"
        
        if has_converged:
            print(f"✓ CONVERGENCE ACHIEVED: {reason}")
        else:
            print(f"✗ Convergence not yet achieved. Continuing iteration.")
        
        return has_converged, convergence_score, reason, critic_statuses, ship_it, quality_score, remaining_issues
    
    def _calculate_diff_ratio(self, old_content: str, new_content: str) -> float:
        """Calculate the ratio of changes between two strings."""
        # Handle edge case: both empty or None
        if not old_content and not new_content:
            return 0.0
        if not old_content or not new_content:
            return 1.0
        
        # Handle edge case: identical content
        if old_content == new_content:
            return 0.0
        
        diff = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            lineterm=''
        ))
        
        # Count only actual content changes (lines starting with + or - but not +++ or ---)
        changed_lines = sum(1 for line in diff 
                          if (line.startswith('+') and not line.startswith('+++')) or 
                             (line.startswith('-') and not line.startswith('---')))
        total_lines = max(len(old_content.splitlines()), len(new_content.splitlines()))
        
        if total_lines == 0:
            return 0.0
        
        return changed_lines / total_lines
    
    def save_diff(self, iteration_num: int, old_content: str, new_content: str) -> None:
        """Save diff for this iteration."""
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f'version_{iteration_num}',
            tofile=f'version_{iteration_num + 1}',
            lineterm=''
        )
        
        diff_file = self.diff_dir / f"iteration_{iteration_num}.diff"
        diff_file.write_text(''.join(diff))
    
    # Output functions
    def save_outputs(self) -> None:
        """Save all output files."""
        print(f"\n{'='*60}")
        print("Saving Outputs")
        print(f"{'='*60}")
        
        # Save final artifact
        if self.artifact:
            final_file = self.output_dir / f"{self.artifact.id}_final.md"
            final_file.write_text(self.artifact.content)
            print(f"✓ Final artifact: {final_file}")
        
        # Determine final status
        if not self.iterations:
            final_status = "BLOCKED"
        else:
            last_iteration = self.iterations[-1]
            if last_iteration.ship_it:
                final_status = "CONVERGED"
            elif self.current_iteration >= self.max_iterations:
                final_status = "MAX_ITERATIONS"
            elif len(last_iteration.remaining_issues) == 0:
                final_status = "CONVERGED"
            else:
                final_status = "CONVERGED"
        
        # Save iteration log with enhanced convergence metrics
        iteration_log = {
            'iterations': [it.to_dict() for it in self.iterations],
            'total_iterations': len(self.iterations),
            'final_version': self.artifact.version if self.artifact else 0,
            'final_status': final_status,
            'artifact_history': self.artifact.history if self.artifact else []
        }
        
        # Add final metrics if iterations exist
        if self.iterations:
            last_iter = self.iterations[-1]
            iteration_log['iteration_count'] = len(self.iterations)
            iteration_log['quality_score'] = last_iter.quality_score
            iteration_log['improvement_delta'] = last_iter.improvement_delta
            iteration_log['remaining_issues'] = last_iter.remaining_issues
        
        log_file = self.output_dir / "iteration_log.json"
        log_file.write_text(json.dumps(iteration_log, indent=2))
        print(f"✓ Iteration log: {log_file}")
        
        # Save critique history
        all_critiques = []
        for iteration in self.iterations:
            for critique in iteration.critiques_received:
                all_critiques.append({
                    'iteration': iteration.iteration_number,
                    **critique.to_dict()
                })
        
        critique_file = self.output_dir / "critique_history.json"
        critique_file.write_text(json.dumps(all_critiques, indent=2))
        print(f"✓ Critique history: {critique_file}")
        
        # Telemetry file
        if self.telemetry_file.exists():
            print(f"✓ Telemetry log (JSONL): {self.telemetry_file}")
        
        print(f"✓ Diff history: {self.diff_dir}/")
    
    # Main convergence loop
    def converge(self, input_file: str) -> None:
        """
        Run the complete convergence process.
        
        Args:
            input_file: Path to input artifact file
        """
        print(f"\n{'='*60}")
        print("AI Council Convergence Engine")
        print(f"{'='*60}")
        print(f"Models: {', '.join(self.models)}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Output directory: {self.output_dir}")
        
        # STATE 0: Load artifact
        artifact = self.load_artifact(input_file)
        
        # Main iteration loop
        for iteration_num in range(1, self.max_iterations + 1):
            self.current_iteration = iteration_num
            
            print(f"\n{'#'*60}")
            print(f"# ITERATION {iteration_num}/{self.max_iterations}")
            print(f"{'#'*60}")
            
            # Rotate models: first model is proposer, rest are critics
            proposer_idx = (iteration_num - 1) % len(self.models)
            proposer = self.models[proposer_idx]
            critics = [m for i, m in enumerate(self.models) if i != proposer_idx]
            
            print(f"\nRoles for this iteration:")
            print(f"  Proposer: {proposer}")
            print(f"  Critics: {', '.join(critics)}")
            
            # Create iteration object with timestamp
            iteration = Iteration(
                iteration_number=iteration_num,
                proposer=proposer,
                critics=critics,
                timestamp=datetime.now().isoformat()
            )
            
            # Save previous content for diff
            previous_content = artifact.content
            
            # STATE 1: Run proposer
            revised_content = self.run_proposer(proposer, artifact, iteration_num)
            
            # Temporarily update artifact for critics to review
            # Use deep copy of history to prevent mutation
            import copy
            temp_artifact = Artifact(
                id=artifact.id,
                version=artifact.version,
                content=revised_content,
                history=copy.deepcopy(artifact.history)
            )
            
            # STATE 2: Run critics
            critiques = self.run_critics(critics, temp_artifact, iteration_num)
            iteration.critiques_received = critiques
            
            # STATE 3: Consolidate critiques
            consolidated_critiques = self.consolidate_critiques(critiques)
            
            # STATE 4: Human approval gate
            approved, rejected, should_stop, human_choice = self.human_approval_gate(consolidated_critiques)
            iteration.applied_critiques = approved
            iteration.rejected_critiques = rejected
            iteration.human_choice = human_choice
            
            # Set human_override field based on decision
            if human_choice == 'a':
                iteration.human_override = 'accepted'
            elif human_choice == 'r':
                iteration.human_override = 'rejected'
            elif human_choice == 'q':
                iteration.human_override = 'rejected'  # User quit, treated as rejection
            else:  # 's' for selective
                iteration.human_override = 'accepted' if approved else 'rejected'
            
            # Log human decision
            print(f"\n📝 Human Decision Logged:")
            print(f"  Choice: {human_choice}")
            print(f"  Applied: {len(approved)} critique(s)")
            print(f"  Rejected: {len(rejected)} critique(s)")
            print(f"  Override: {iteration.human_override}")
            
            if should_stop:
                print("\nStopping by user request.")
                self.iterations.append(iteration)
                # Log telemetry before stopping
                self._log_telemetry(iteration)
                break
            
            # STATE 5: Apply critiques
            if approved:
                # Apply to revised content
                final_content = self._apply_critiques_to_content(revised_content, approved)
            else:
                # No critiques applied, use revised content as-is
                final_content = revised_content
            
            # Update artifact using apply_change to maintain history consistency
            change_description = f"Iteration {iteration_num}: Proposer={proposer}, Applied {len(approved)} critique(s)"
            artifact.apply_change(change_description, final_content)
            
            # Calculate diff once for both saving and convergence check
            diff_ratio = self._calculate_diff_ratio(previous_content, artifact.content)
            
            # Save diff
            self.save_diff(iteration_num, previous_content, artifact.content)
            iteration.diff_summary = f"Changed {diff_ratio*100:.2f}% of content"
            
            # STATE 6: Check convergence
            # Check all critiques that weren't applied (both rejected and high-severity ones)
            unapplied_critiques = rejected
            has_converged, score, reason, critic_statuses, ship_it, quality_score, remaining_issues = self.check_convergence(
                unapplied_critiques, artifact, previous_content, diff_ratio, critics
            )
            iteration.convergence_score = score
            iteration.quality_score = quality_score
            iteration.remaining_issues = remaining_issues
            iteration.critic_statuses = critic_statuses
            iteration.ship_it = ship_it
            
            # Calculate improvement delta (quality improvement from previous iteration)
            if self.iterations:
                prev_quality = self.iterations[-1].quality_score
                iteration.improvement_delta = quality_score - prev_quality
            else:
                iteration.improvement_delta = quality_score  # First iteration baseline
            
            print(f"Improvement delta: {iteration.improvement_delta:+.1f}")
            
            self.iterations.append(iteration)
            
            # Log telemetry after iteration is complete
            self._log_telemetry(iteration)
            
            # Anti-loop protection: Check for minimal improvement
            if (len(self.iterations) >= 2 and 
                abs(iteration.improvement_delta) < 0.1 and 
                len(remaining_issues) == 0):
                print("\n⚠ Minimal improvement with no remaining issues - triggering convergence")
                has_converged = True
                reason = "No meaningful improvement and no actionable issues"
            
            if has_converged:
                print(f"\n✓ Convergence achieved: {reason}")
                break
        
        # Save outputs
        self.save_outputs()
        
        # Determine final status
        if not self.iterations:
            final_status = "BLOCKED"
            convergence_reason = "No iterations completed"
        else:
            last_iteration = self.iterations[-1]
            if last_iteration.ship_it:
                final_status = "CONVERGED"
                convergence_reason = "All critics approved"
            elif self.current_iteration >= self.max_iterations:
                final_status = "MAX_ITERATIONS"
                convergence_reason = f"Reached max iterations ({self.max_iterations})"
            elif len(last_iteration.remaining_issues) == 0:
                final_status = "CONVERGED"
                convergence_reason = "No actionable issues remaining"
            else:
                final_status = "CONVERGED"
                convergence_reason = "Convergence criteria met"
        
        print(f"\n{'='*60}")
        print("Convergence Complete!")
        print(f"{'='*60}")
        print(f"Final Status: {final_status}")
        print(f"Reason: {convergence_reason}")
        print(f"Total iterations: {len(self.iterations)}")
        if self.iterations:
            print(f"Final quality score: {self.iterations[-1].quality_score:.1f}/100")
            print(f"Final improvement delta: {self.iterations[-1].improvement_delta:+.1f}")
            print(f"Remaining issues: {len(self.iterations[-1].remaining_issues)}")
        print(f"Final version: {artifact.version}")
    
    # Placeholder LLM functions
    def _call_proposer_llm(self, proposer: str, artifact: Artifact, iteration_num: int) -> str:
        """
        Placeholder for proposer LLM API call.
        
        In a real implementation, this would call the actual LLM API
        to generate a revised version of the artifact.
        """
        print(f"  [PLACEHOLDER] Calling {proposer} LLM for revision...")
        
        # Mock revision: add a comment indicating revision
        revision_note = f"\n\n<!-- Revised by {proposer} in iteration {iteration_num} -->\n"
        return artifact.content + revision_note
    
    def _call_critic_llm(self, critic: str, artifact: Artifact, iteration_num: int) -> List[Critique]:
        """
        Placeholder for critic LLM API call.
        
        In a real implementation, this would call the actual LLM API
        to generate structured critiques in JSON format.
        """
        print(f"    [PLACEHOLDER] Calling {critic} LLM for critique...")
        
        # Mock critiques based on critic name
        mock_critiques = []
        
        if 'gpt' in critic.lower():
            mock_critiques.append(Critique(
                critic=critic,
                category='simplicity',
                severity=2,
                location='line 10-20',
                description='Code could be more concise',
                suggested_change='Refactor complex logic into smaller functions'
            ))
        
        if 'copilot' in critic.lower():
            mock_critiques.append(Critique(
                critic=critic,
                category='bug-risk',
                severity=3,
                location='function parse_input',
                description='Missing input validation',
                suggested_change='Add validation for edge cases and null inputs'
            ))
        
        if 'augment' in critic.lower() or 'claude' in critic.lower():
            mock_critiques.append(Critique(
                critic=critic,
                category='security',
                severity=4,
                location='authentication section',
                description='Potential security vulnerability in auth flow',
                suggested_change='Implement rate limiting and secure token storage'
            ))
        
        return mock_critiques
    
    def _apply_critiques_to_content(self, content: str, critiques: List[Critique]) -> str:
        """
        Apply critiques to content in a structured, deterministic manner.
        
        This is an MVP placeholder that transforms critiques into structured sections.
        Groups critiques by category for organized presentation.
        Real LLM-based text rewriting is NOT implemented here.
        
        Args:
            content: Original content
            critiques: List of critiques to apply
            
        Returns:
            Content with structured critique application notes
        """
        if not critiques:
            return content
        
        # Group critiques by category for structured output
        by_category = {}
        for critique in critiques:
            if critique.category not in by_category:
                by_category[critique.category] = []
            by_category[critique.category].append(critique)
        
        # Build structured application notes deterministically
        # Sort categories for consistent output
        applied_notes = "\n\n<!-- Applied Critiques -->\n"
        applied_notes += "<!-- \n"
        
        for category in sorted(by_category.keys()):
            category_critiques = by_category[category]
            applied_notes += f"\n{category.upper()} ({len(category_critiques)} critique(s)):\n"
            
            # Sort by severity (descending) then by description for determinism
            sorted_critiques = sorted(category_critiques, 
                                     key=lambda c: (-c.severity, c.description))
            
            for critique in sorted_critiques:
                applied_notes += f"  [{critique.severity}/5] {critique.critic}:\n"
                applied_notes += f"    Issue: {critique.description}\n"
                applied_notes += f"    Change: {critique.suggested_change}\n"
                if critique.location:
                    applied_notes += f"    Location: {critique.location}\n"
        
        applied_notes += "\n-->\n"
        
        return content + applied_notes


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='AI Council Convergence Engine - Iterative artifact refinement',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s converge input.md --models gpt,copilot,augment
  %(prog)s converge design.md --models gpt,copilot,augment --max-iterations 4
  %(prog)s converge code.py --models claude,gpt --output ./results
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Converge command
    converge_parser = subparsers.add_parser('converge', help='Run convergence process on an artifact')
    converge_parser.add_argument('input_file', help='Input artifact file (Markdown or code)')
    converge_parser.add_argument('--models', required=True, 
                                 help='Comma-separated list of models (e.g., gpt,copilot,augment)')
    converge_parser.add_argument('--max-iterations', type=int, default=5,
                                 help='Maximum number of iterations (default: 5)')
    converge_parser.add_argument('--output', default='./output',
                                 help='Output directory (default: ./output)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'converge':
        # Parse models
        models = [m.strip() for m in args.models.split(',')]
        
        # Validate models
        if len(models) < 2:
            print("Error: At least 2 models required (1 proposer + 1 critic minimum)")
            sys.exit(1)
        
        # Check for duplicate models
        if len(models) != len(set(models)):
            print("Error: Duplicate model names detected. Each model must be unique.")
            sys.exit(1)
        
        # Create engine and run
        engine = ConvergenceEngine(
            models=models,
            max_iterations=args.max_iterations,
            output_dir=args.output
        )
        
        try:
            engine.converge(args.input_file)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving partial results...")
            engine.save_outputs()
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
