#!/usr/bin/env python3
"""
Claude Agent for IterativeAICouncil
===================================

Agent that uses Anthropic's Claude API to review and refine plans.
"""

import os
from typing import Optional
try:
    import anthropic
except ImportError:
    anthropic = None


class ClaudeAgent:
    """Agent that uses Claude to review and critique plans."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Claude agent.
        
        Args:
            api_key: Anthropic API key (defaults to CLAUDE_KEY env var)
            model: Claude model to use (default: claude-3-opus)
        """
        self.api_key = api_key or os.getenv("CLAUDE_KEY")
        self.model = model
        
        if not self.api_key:
            print("Warning: CLAUDE_KEY not set. Claude agent will run in mock mode.")
        
        if anthropic and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def review_plan(self, plan: str, iteration: int) -> str:
        """
        Review the plan and provide feedback.
        
        Args:
            plan: Current plan content
            iteration: Current iteration number
            
        Returns:
            Review feedback as markdown text
        """
        if not self.api_key or not self.client:
            return self._mock_review(plan, iteration)
        
        try:
            # Construct review prompt
            prompt = self._build_prompt(plan, iteration)
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=self._get_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            return f"Error calling Claude API: {str(e)}\n\nFalling back to mock review.\n\n{self._mock_review(plan, iteration)}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for Claude agent."""
        return """You are a critical technical reviewer and security analyst.
Your role is to harden plans by identifying risks, edge cases, and potential issues.

Focus on:
- Security considerations
- Error handling and edge cases
- Performance and scalability concerns
- Dependency risks
- Implementation challenges
- Phase boundaries and scope creep
- Tradeoff implications

Be thorough but constructive. Provide specific recommendations in markdown format."""
    
    def _build_prompt(self, plan: str, iteration: int) -> str:
        """Build the review prompt for the current iteration."""
        return f"""Review the following plan with a critical eye (Iteration {iteration}):

---
{plan}
---

Please provide:
1. Security and risk assessment
2. Potential implementation challenges
3. Edge cases and error scenarios
4. Scalability considerations
5. Dependencies and external risks
6. Phase scope analysis (any items that should move to future phases?)
7. Convergence signal (if plan is robust, state "no significant issues")

Provide your critical review in clear markdown format."""
    
    def _mock_review(self, plan: str, iteration: int) -> str:
        """
        Provide a mock review when API is not available.
        Used for testing and development.
        """
        return f"""# Claude Agent Review (Mock Mode - Iteration {iteration})

## Summary
This is a mock review generated without calling the Anthropic API.
Configure CLAUDE_KEY environment variable to enable real reviews.

## Security & Risk Analysis
- Plan length: {len(plan)} characters
- Iteration: {iteration}
- Status: API not configured

## Critical Concerns
1. Configure Anthropic API key for real security analysis
2. Ensure proper error handling in implementation
3. Consider security implications of API key management
4. Verify input validation and sanitization

## Implementation Challenges
- Mock mode does not provide real critical analysis
- Real Claude reviews would identify specific risks
- Security considerations need expert review

## Phase Scope
Mock mode: Cannot assess phase appropriateness without real analysis.

## Convergence Signal
Mock mode: Real critical review needed before approval.

---
*Note: This is a placeholder review. Enable API access for real critical analysis.*
"""


if __name__ == "__main__":
    # Test the agent
    agent = ClaudeAgent()
    test_plan = """# Test Plan
    
## Objective
Build a multi-agent orchestration system.

## Requirements
- Docker containerization
- Multi-LLM support
- Iterative refinement loop
"""
    
    review = agent.review_plan(test_plan, 1)
    print(review)
