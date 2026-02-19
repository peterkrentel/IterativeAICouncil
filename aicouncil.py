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
    
    def to_dict(self) -> Dict:
        """Convert critique to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'Critique':
        """Create Critique from dictionary."""
        return Critique(**data)
    
    def is_duplicate(self, other: 'Critique') -> bool:
        """Check if this critique is similar to another (for deduplication)."""
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
    """
    iteration_number: int
    proposer: str
    critics: List[str]
    critiques_received: List[Critique] = field(default_factory=list)
    applied_critiques: List[Critique] = field(default_factory=list)
    rejected_critiques: List[Critique] = field(default_factory=list)
    diff_summary: str = ""
    convergence_score: float = 0.0
    
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
            'convergence_score': self.convergence_score
        }


class ConvergenceEngine:
    """Main convergence engine for iterative artifact refinement."""
    
    VALID_CATEGORIES = ['architecture', 'performance', 'security', 'simplicity', 'bug-risk', 'style']
    
    def __init__(self, models: List[str], max_iterations: int = 5, output_dir: str = "./output"):
        """
        Initialize the convergence engine.
        
        Args:
            models: List of model names to use
            max_iterations: Maximum number of iterations (default: 5)
            output_dir: Directory for output files
        """
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
        Run proposer model to generate revised artifact.
        
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
        
        # Placeholder for LLM API call
        revised_content = self._call_proposer_llm(proposer, artifact, iteration_num)
        
        print(f"✓ Proposer generated revision")
        print(f"  Content length: {len(revised_content)} characters")
        
        return revised_content
    
    # STATE 2: Critics run in parallel
    def run_critics(self, critics: List[str], artifact: Artifact, iteration_num: int) -> List[Critique]:
        """
        Run critic models in parallel to generate critiques.
        
        Args:
            critics: List of critic model names
            artifact: Current artifact
            iteration_num: Current iteration number
            
        Returns:
            List of critiques from all critics
        """
        print(f"\n{'='*60}")
        print(f"STATE 2: Running Critics (Iteration {iteration_num})")
        print(f"{'='*60}")
        print(f"Critics: {', '.join(critics)}")
        
        all_critiques = []
        
        # In a real implementation, these would run in parallel
        for critic in critics:
            print(f"\n  Running {critic}...")
            critiques = self._call_critic_llm(critic, artifact, iteration_num)
            all_critiques.extend(critiques)
            print(f"  ✓ {critic} returned {len(critiques)} critique(s)")
        
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
    def human_approval_gate(self, critiques: List[Critique]) -> Tuple[List[Critique], List[Critique], bool]:
        """
        Display critiques and prompt for human approval.
        
        Args:
            critiques: List of consolidated critiques
            
        Returns:
            Tuple of (approved_critiques, rejected_critiques, should_stop)
        """
        print(f"\n{'='*60}")
        print("STATE 4: Human Approval Gate")
        print(f"{'='*60}")
        
        if not critiques:
            print("No critiques to review.")
            return [], [], False
        
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
        
        # Prompt for approval
        print("\nOptions:")
        print("  a - Apply all critiques")
        print("  s - Selective apply (choose which to apply)")
        print("  r - Reject all critiques")
        print("  q - Stop iteration (quit)")
        
        choice = input("\nYour choice [a/s/r/q]: ").strip().lower()
        
        if choice == 'q':
            print("Stopping iteration by user request.")
            return [], critiques, True
        elif choice == 'a':
            print(f"Applying all {len(critiques)} critique(s).")
            return critiques, [], False
        elif choice == 'r':
            print(f"Rejecting all {len(critiques)} critique(s).")
            return [], critiques, False
        elif choice == 's':
            return self._selective_apply(critiques)
        else:
            print("Invalid choice. Defaulting to selective apply.")
            return self._selective_apply(critiques)
    
    def _selective_apply(self, critiques: List[Critique]) -> Tuple[List[Critique], List[Critique], bool]:
        """Helper for selective critique application."""
        approved = []
        rejected = []
        
        for i, critique in enumerate(critiques, 1):
            print(f"\nCritique {i}/{len(critiques)}:")
            print(f"  [{critique.severity}/5] {critique.category} - {critique.critic}")
            print(f"  {critique.description}")
            
            choice = input("  Apply this critique? [y/n/q]: ").strip().lower()
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
                          previous_content: str) -> Tuple[bool, float, str]:
        """
        Check if convergence has been achieved.
        
        Args:
            critiques: Remaining/rejected critiques
            artifact: Current artifact
            previous_content: Previous artifact content
            
        Returns:
            Tuple of (has_converged, convergence_score, reason)
        """
        print(f"\n{'='*60}")
        print("STATE 6: Convergence Check")
        print(f"{'='*60}")
        
        # Check 1: No high-severity critiques remain
        high_severity_remaining = [c for c in critiques if c.severity >= 3]
        no_high_severity = len(high_severity_remaining) == 0
        
        print(f"High-severity critiques remaining: {len(high_severity_remaining)}")
        
        # Check 2: Structural diff < 5%
        diff_ratio = self._calculate_diff_ratio(previous_content, artifact.content)
        small_diff = diff_ratio < 0.05
        
        print(f"Structural diff: {diff_ratio*100:.2f}%")
        
        # Check 3: Max iterations reached
        max_iterations_reached = self.current_iteration >= self.max_iterations
        
        print(f"Iteration: {self.current_iteration}/{self.max_iterations}")
        
        # Calculate convergence score
        convergence_score = 0.0
        if no_high_severity:
            convergence_score += 0.5
        if small_diff:
            convergence_score += 0.3
        convergence_score += min(0.2, (1 - diff_ratio) * 0.2)
        
        print(f"Convergence score: {convergence_score:.2f}")
        
        # Determine convergence
        has_converged = False
        reason = ""
        
        if no_high_severity and small_diff:
            has_converged = True
            reason = "No high-severity critiques and minimal changes"
        elif max_iterations_reached:
            has_converged = True
            reason = f"Maximum iterations ({self.max_iterations}) reached"
        
        if has_converged:
            print(f"✓ CONVERGENCE ACHIEVED: {reason}")
        else:
            print(f"✗ Convergence not yet achieved. Continuing iteration.")
        
        return has_converged, convergence_score, reason
    
    def _calculate_diff_ratio(self, old_content: str, new_content: str) -> float:
        """Calculate the ratio of changes between two strings."""
        if not old_content or not new_content:
            return 1.0
        
        diff = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            lineterm=''
        ))
        
        # Count changed lines
        changed_lines = sum(1 for line in diff if line.startswith('+') or line.startswith('-'))
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
        
        # Save iteration log
        iteration_log = {
            'iterations': [it.to_dict() for it in self.iterations],
            'total_iterations': len(self.iterations),
            'final_version': self.artifact.version if self.artifact else 0
        }
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
            
            # Create iteration object
            iteration = Iteration(
                iteration_number=iteration_num,
                proposer=proposer,
                critics=critics
            )
            
            # Save previous content for diff
            previous_content = artifact.content
            
            # STATE 1: Run proposer
            revised_content = self.run_proposer(proposer, artifact, iteration_num)
            
            # Temporarily update artifact for critics to review
            temp_artifact = Artifact(
                id=artifact.id,
                version=artifact.version,
                content=revised_content,
                history=artifact.history.copy()
            )
            
            # STATE 2: Run critics
            critiques = self.run_critics(critics, temp_artifact, iteration_num)
            iteration.critiques_received = critiques
            
            # STATE 3: Consolidate critiques
            consolidated_critiques = self.consolidate_critiques(critiques)
            
            # STATE 4: Human approval gate
            approved, rejected, should_stop = self.human_approval_gate(consolidated_critiques)
            iteration.applied_critiques = approved
            iteration.rejected_critiques = rejected
            
            if should_stop:
                print("\nStopping by user request.")
                self.iterations.append(iteration)
                break
            
            # STATE 5: Apply critiques
            if approved:
                # Apply to revised content
                final_content = self._apply_critiques_to_content(revised_content, approved)
            else:
                # No critiques applied, use revised content as-is
                final_content = revised_content
            
            # Update artifact
            artifact.content = final_content
            artifact.version += 1
            
            # Save diff
            self.save_diff(iteration_num, previous_content, artifact.content)
            diff_ratio = self._calculate_diff_ratio(previous_content, artifact.content)
            iteration.diff_summary = f"Changed {diff_ratio*100:.2f}% of content"
            
            # STATE 6: Check convergence
            has_converged, score, reason = self.check_convergence(
                rejected, artifact, previous_content
            )
            iteration.convergence_score = score
            
            self.iterations.append(iteration)
            
            if has_converged:
                print(f"\n✓ Convergence achieved: {reason}")
                break
        
        # Save outputs
        self.save_outputs()
        
        print(f"\n{'='*60}")
        print("Convergence Complete!")
        print(f"{'='*60}")
        print(f"Final version: {artifact.version}")
        print(f"Total iterations: {len(self.iterations)}")
    
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
        Placeholder for applying critiques to content.
        
        In a real implementation, this would use an LLM to intelligently
        apply the suggested changes to the content.
        """
        # Mock application: add notes about applied critiques
        applied_notes = "\n\n<!-- Applied Critiques:\n"
        for critique in critiques:
            applied_notes += f"  - [{critique.severity}/5] {critique.category}: {critique.description}\n"
        applied_notes += "-->\n"
        
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
        
        if len(models) < 2:
            print("Error: At least 2 models required (1 proposer + 1 critic minimum)")
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
