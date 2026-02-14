#!/usr/bin/env python3
"""
ChatGPT Agent for IterativeAICouncil
====================================

Agent that uses OpenAI's GPT API to review and refine plans.
"""

import os
from typing import Optional
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class ChatGPTAgent:
    """Agent that uses ChatGPT to review and critique plans."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize the ChatGPT agent.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_KEY env var)
            model: OpenAI model to use (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("OPENAI_KEY")
        self.model = model
        self.client = None
        
        if not self.api_key:
            print("Warning: OPENAI_KEY not set. ChatGPT agent will run in mock mode.")
        elif OpenAI:
            self.client = OpenAI(api_key=self.api_key)
    
    def review_plan(self, plan: str, iteration: int) -> str:
        """
        Review the plan and provide feedback.
        
        Args:
            plan: Current plan content
            iteration: Current iteration number
            
        Returns:
            Review feedback as markdown text
        """
        if not self.client:
            return self._mock_review(plan, iteration)
        
        try:
            # Construct review prompt
            prompt = self._build_prompt(plan, iteration)
            
            # Call OpenAI API (v1.0.0+ interface)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error calling ChatGPT API: {str(e)}\n\nFalling back to mock review.\n\n{self._mock_review(plan, iteration)}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for ChatGPT agent."""
        return """You are a senior software architect and project planner.
Your role is to review technical plans and provide constructive feedback.

Focus on:
- Clarity and completeness of requirements
- Technical feasibility
- Architectural soundness
- Risk identification
- Phase appropriateness (ensure items belong in current phase)
- Tradeoff analysis

Provide specific, actionable feedback in markdown format."""
    
    def _build_prompt(self, plan: str, iteration: int) -> str:
        """Build the review prompt for the current iteration."""
        return f"""Review the following plan (Iteration {iteration}):

---
{plan}
---

Please provide:
1. Summary of overall plan quality
2. Specific issues or concerns
3. Recommendations for improvement
4. Phase-awareness check (are all items appropriate for current phase?)
5. Convergence signal (if plan is ready, state "no major changes needed")

Provide your review in clear markdown format."""
    
    def _mock_review(self, plan: str, iteration: int) -> str:
        """
        Provide a mock review when API is not available.
        Used for testing and development.
        """
        return f"""# ChatGPT Agent Review (Mock Mode - Iteration {iteration})

## Summary
This is a mock review generated without calling the OpenAI API.
Configure OPENAI_KEY environment variable to enable real reviews.

## Plan Analysis
- Plan length: {len(plan)} characters
- Iteration: {iteration}

## Recommendations
1. Configure OpenAI API key for real reviews
2. Ensure plan has clear objectives and requirements
3. Verify technical feasibility of proposed solutions
4. Check that items are appropriate for current phase

## Convergence Signal
Mock mode: Additional iterations recommended to configure real API access.

---
*Note: This is a placeholder review. Enable API access for real feedback.*
"""


if __name__ == "__main__":
    # Test the agent
    agent = ChatGPTAgent()
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
