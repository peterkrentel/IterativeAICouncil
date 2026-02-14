#!/usr/bin/env python3
"""
IterativeAICouncil Orchestrator
================================

Main orchestrator script that coordinates the multi-LLM feedback loop.
Reads initial plan, calls all agents iteratively, merges feedback, and
produces a final stabilized plan.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json
import time

# Import agent modules
from chatgpt_agent import ChatGPTAgent
from claude_agent import ClaudeAgent
from copilot_agent import CopilotAgent


class Orchestrator:
    """Main orchestrator for multi-LLM iterative plan refinement."""
    
    def __init__(self, ai_dir: str = "./ai", max_iterations: int = 5):
        """
        Initialize the orchestrator.
        
        Args:
            ai_dir: Directory containing plan and review files
            max_iterations: Maximum number of refinement iterations
        """
        self.ai_dir = Path(ai_dir)
        self.max_iterations = max_iterations
        
        # Initialize agents
        self.agents = {
            'chatgpt': ChatGPTAgent(),
            'claude': ClaudeAgent(),
            'copilot': CopilotAgent()
        }
        
        # File paths
        self.plan_file = self.ai_dir / "01_plan.md"
        self.review_files = {
            'chatgpt': self.ai_dir / "02_review_chatgpt.md",
            'claude': self.ai_dir / "03_review_claude.md",
            'copilot': self.ai_dir / "04_review_copilot.md"
        }
        self.final_file = self.ai_dir / "05_final.md"
        self.tradeoff_log = self.ai_dir / "tradeoff_log.md"
        
        # Ensure AI directory exists
        self.ai_dir.mkdir(exist_ok=True)
        
    def read_plan(self) -> str:
        """Read the current plan from 01_plan.md."""
        if not self.plan_file.exists():
            return ""
        return self.plan_file.read_text()
    
    def write_plan(self, content: str) -> None:
        """Write updated plan to 01_plan.md."""
        self.plan_file.write_text(content)
    
    def write_final(self, content: str) -> None:
        """Write final stabilized plan to 05_final.md."""
        self.final_file.write_text(content)
    
    def log_tradeoff(self, message: str) -> None:
        """Append a tradeoff or decision log entry."""
        with open(self.tradeoff_log, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}] {message}\n")
    
    def call_agents(self, plan: str, iteration: int) -> Dict[str, str]:
        """
        Call all agents to review the current plan.
        
        Args:
            plan: Current plan content
            iteration: Current iteration number
            
        Returns:
            Dictionary mapping agent names to their review outputs
        """
        reviews = {}
        
        for agent_name, agent in self.agents.items():
            print(f"Calling {agent_name} agent (iteration {iteration})...")
            try:
                review = agent.review_plan(plan, iteration)
                reviews[agent_name] = review
                
                # Write review to file
                review_file = self.review_files[agent_name]
                review_file.write_text(review)
                
                print(f"  ✓ {agent_name} review complete")
            except Exception as e:
                print(f"  ✗ {agent_name} agent failed: {e}")
                reviews[agent_name] = f"Error: {str(e)}"
        
        return reviews
    
    def merge_feedback(self, plan: str, reviews: Dict[str, str]) -> str:
        """
        Merge feedback from all agents into updated plan.
        
        This is a simple implementation that concatenates feedback.
        Future versions could use AI-driven merging or diff-based updates.
        
        Args:
            plan: Current plan content
            reviews: Dictionary of agent reviews
            
        Returns:
            Updated plan with merged feedback
        """
        # Simple merge strategy: append all feedback sections
        merged = plan + "\n\n---\n## Feedback Integration\n\n"
        
        for agent_name, review in reviews.items():
            merged += f"\n### {agent_name.title()} Review\n{review}\n"
        
        return merged
    
    def check_convergence(self, reviews: Dict[str, str]) -> bool:
        """
        Check if agents have reached consensus (convergence).
        
        Simple heuristic: check if all reviews indicate no major changes needed.
        Future versions could use more sophisticated AI-based analysis.
        
        Args:
            reviews: Dictionary of agent reviews
            
        Returns:
            True if convergence achieved, False otherwise
        """
        convergence_keywords = [
            "no major changes",
            "looks good",
            "approved",
            "no significant issues",
            "ready to proceed"
        ]
        
        converged_count = 0
        for review in reviews.values():
            review_lower = review.lower()
            if any(keyword in review_lower for keyword in convergence_keywords):
                converged_count += 1
        
        # Consider converged if majority of agents approve
        return converged_count >= len(reviews) * 0.6
    
    def run(self) -> None:
        """
        Run the main orchestration loop.
        
        1. Read initial plan
        2. Call all agents for review
        3. Merge feedback
        4. Check for convergence
        5. Repeat until convergence or max iterations
        6. Write final plan
        """
        print("=" * 60)
        print("IterativeAICouncil Orchestrator")
        print("=" * 60)
        
        # Initialize tradeoff log
        self.log_tradeoff("Starting orchestration")
        
        # Read initial plan
        plan = self.read_plan()
        if not plan:
            print("Error: No initial plan found in 01_plan.md")
            print("Please create an initial plan file before running orchestrator.")
            sys.exit(1)
        
        print(f"Initial plan loaded ({len(plan)} characters)")
        
        # Iterative refinement loop
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'=' * 60}")
            print(f"Iteration {iteration}/{self.max_iterations}")
            print(f"{'=' * 60}\n")
            
            # Call all agents
            reviews = self.call_agents(plan, iteration)
            
            # Check for convergence
            if self.check_convergence(reviews):
                print("\n✓ Convergence achieved! All agents approve.")
                self.log_tradeoff(f"Convergence achieved at iteration {iteration}")
                break
            
            # Merge feedback into plan
            print("\nMerging feedback...")
            plan = self.merge_feedback(plan, reviews)
            self.write_plan(plan)
            
            self.log_tradeoff(f"Iteration {iteration} complete, feedback merged")
            
            if iteration == self.max_iterations:
                print(f"\n⚠ Maximum iterations ({self.max_iterations}) reached")
                self.log_tradeoff("Maximum iterations reached without full convergence")
        
        # Write final plan
        print("\nWriting final plan...")
        self.write_final(plan)
        
        print(f"\n{'=' * 60}")
        print("Orchestration complete!")
        print(f"Final plan written to: {self.final_file}")
        print(f"Tradeoff log: {self.tradeoff_log}")
        print(f"{'=' * 60}\n")


def main():
    """Main entry point for the orchestrator."""
    # Configuration from environment or defaults
    ai_dir = os.getenv("AI_DIR", "./ai")
    max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))
    
    # Create and run orchestrator
    orchestrator = Orchestrator(ai_dir=ai_dir, max_iterations=max_iterations)
    orchestrator.run()


if __name__ == "__main__":
    main()
