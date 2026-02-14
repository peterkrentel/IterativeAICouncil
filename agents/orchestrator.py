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
    
    # Configuration constants
    CONVERGENCE_THRESHOLD = 0.6  # Fraction of agents that must approve for convergence
    
    def __init__(self, ai_dir: str = "./ai", max_iterations: int = 5, convergence_threshold: float = CONVERGENCE_THRESHOLD):
        """
        Initialize the orchestrator.
        
        Args:
            ai_dir: Directory containing plan and review files
            max_iterations: Maximum number of refinement iterations
            convergence_threshold: Fraction of agents required for convergence (default: 0.6)
        """
        self.ai_dir = Path(ai_dir)
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        
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
        
        Uses ChatGPT to intelligently integrate feedback from all agents
        into an improved version of the plan.
        
        Args:
            plan: Current plan content
            reviews: Dictionary of agent reviews
            
        Returns:
            Updated plan with feedback integrated
        """
        # If no ChatGPT agent available, fall back to simple append
        if 'chatgpt' not in self.agents or not hasattr(self.agents['chatgpt'], 'client') or not self.agents['chatgpt'].client:
            return self._simple_merge_feedback(plan, reviews)
        
        # Build comprehensive feedback summary
        feedback_summary = "# Agent Feedback Summary\n\n"
        for agent_name, review in reviews.items():
            feedback_summary += f"## {agent_name.title()} Agent:\n{review}\n\n"
        
        # Use ChatGPT to integrate feedback into plan
        try:
            integration_prompt = f"""You are a technical plan integrator. Your task is to update a project plan based on feedback from multiple AI agents.

ORIGINAL PLAN:
{plan}

FEEDBACK FROM AGENTS:
{feedback_summary}

Your task:
1. Review the original plan and all agent feedback
2. Integrate the feedback to create an IMPROVED version of the plan
3. Address concerns raised by agents
4. Keep the same structure and format as the original
5. Do NOT just append feedback - actually UPDATE the plan content based on the suggestions
6. Return ONLY the updated plan, no meta-commentary

Updated Plan:"""

            response = self.agents['chatgpt'].client.chat.completions.create(
                model=self.agents['chatgpt'].model,
                messages=[
                    {"role": "system", "content": "You are a technical plan integrator that improves plans based on multi-agent feedback."},
                    {"role": "user", "content": integration_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent integration
                max_tokens=4000
            )
            
            updated_plan = response.choices[0].message.content
            
            # Log the integration
            self.log_tradeoff(f"Plan updated based on feedback from {len(reviews)} agents")
            
            return updated_plan
            
        except Exception as e:
            print(f"  ⚠ Error integrating feedback via AI: {e}")
            print(f"  ℹ Falling back to simple merge")
            return self._simple_merge_feedback(plan, reviews)
    
    def _simple_merge_feedback(self, plan: str, reviews: Dict[str, str]) -> str:
        """
        Fallback: Simple merge that appends feedback sections.
        Used when AI integration is not available.
        """
        merged = plan + "\n\n---\n## Agent Feedback (Iteration)\n\n"
        
        for agent_name, review in reviews.items():
            merged += f"### {agent_name.title()} Review\n{review}\n\n"
        
        return merged
    
    def check_convergence(self, reviews: Dict[str, str]) -> bool:
        """
        Check if agents have reached consensus (convergence).
        
        Analyzes reviews to determine if agents think the plan is ready.
        Looks for explicit approval signals and absence of major concerns.
        
        Args:
            reviews: Dictionary of agent reviews
            
        Returns:
            True if convergence achieved, False otherwise
        """
        # Keywords indicating approval/convergence
        approval_keywords = [
            "no major changes",
            "looks good",
            "approved",
            "no significant issues",
            "ready to proceed",
            "ready for implementation",
            "ready for code",
            "plan is complete",
            "no critical",
            "convergence achieved"
        ]
        
        # Keywords indicating more work needed
        concern_keywords = [
            "critical",
            "must address",
            "requires",
            "missing",
            "unclear",
            "additional iteration",
            "more work needed",
            "significant issues",
            "major concerns"
        ]
        
        approved_count = 0
        concern_count = 0
        
        for agent_name, review in reviews.items():
            review_lower = review.lower()
            
            # Check for approval signals
            has_approval = any(keyword in review_lower for keyword in approval_keywords)
            # Check for concerns
            has_concerns = any(keyword in review_lower for keyword in concern_keywords)
            
            if has_approval and not has_concerns:
                approved_count += 1
                print(f"  ✓ {agent_name} signals approval")
            elif has_concerns:
                concern_count += 1
                print(f"  ⚠ {agent_name} has concerns")
            else:
                print(f"  - {agent_name} neutral")
        
        # Consider converged if threshold of agents approve and few concerns
        threshold_met = approved_count >= len(reviews) * self.convergence_threshold
        few_concerns = concern_count < len(reviews) * 0.5
        
        converged = threshold_met and few_concerns
        
        if converged:
            print(f"\n  → Convergence achieved: {approved_count}/{len(reviews)} agents approve")
        else:
            print(f"\n  → More iteration needed: {approved_count}/{len(reviews)} approve, {concern_count} have concerns")
        
        return converged
    
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
            print("\n" + "─" * 60)
            if 'chatgpt' not in self.agents or not hasattr(self.agents['chatgpt'], 'client') or not self.agents['chatgpt'].client:
                print("Integrating feedback (mock mode - feedback appended)...")
                print("ℹ Configure OPENAI_KEY for AI-driven plan integration")
            else:
                print("Integrating feedback via AI...")
            print("─" * 60)
            
            updated_plan = self.merge_feedback(plan, reviews)
            
            # Check if plan actually changed
            if updated_plan != plan:
                print(f"✓ Plan updated ({len(updated_plan) - len(plan):+d} chars)")
                plan = updated_plan
                self.write_plan(plan)
            else:
                print("ℹ Plan unchanged - agents may be satisfied")
            
            self.log_tradeoff(f"Iteration {iteration} complete, plan updated")
            
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
    convergence_threshold = float(os.getenv("CONVERGENCE_THRESHOLD", "0.6"))
    
    # Create and run orchestrator
    orchestrator = Orchestrator(
        ai_dir=ai_dir, 
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
