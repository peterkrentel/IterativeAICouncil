#!/usr/bin/env python3
"""
Copilot Agent for IterativeAICouncil
====================================

Agent that performs code-level and phase-aware checks on plans.
Can integrate with VSCode or operate independently.
"""

import os
from typing import Optional
import re


class CopilotAgent:
    """Agent that performs code-level analysis and phase-aware validation."""
    
    def __init__(self, phase: str = "1"):
        """
        Initialize the Copilot agent.
        
        Args:
            phase: Current phase number (default: "1")
        """
        self.current_phase = phase
    
    def review_plan(self, plan: str, iteration: int) -> str:
        """
        Review the plan with focus on code-level implementation and phase awareness.
        
        Args:
            plan: Current plan content
            iteration: Current iteration number
            
        Returns:
            Review feedback as markdown text
        """
        # Perform various checks
        phase_check = self._check_phase_appropriateness(plan)
        code_check = self._check_code_feasibility(plan)
        structure_check = self._check_structure(plan)
        
        # Build review
        review = f"""# Copilot Agent Review (Iteration {iteration})

## Phase Awareness Check
{phase_check}

## Code Implementation Feasibility
{code_check}

## Plan Structure Analysis
{structure_check}

## Recommendations
{self._generate_recommendations(plan)}

## Convergence Signal
{self._check_convergence(plan, iteration)}

---
*Code-level and phase-aware analysis complete.*
"""
        return review
    
    def _check_phase_appropriateness(self, plan: str) -> str:
        """Check if all items in plan are appropriate for current phase."""
        # Simple heuristic: look for phase indicators
        phase_keywords = {
            "1": ["basic", "initial", "core", "foundation", "prototype"],
            "2": ["advanced", "optimization", "scaling", "production"],
            "3": ["enhancement", "additional", "future", "optional"]
        }
        
        current_keywords = phase_keywords.get(self.current_phase, [])
        future_indicators = ["future", "later", "phase 2", "phase 3", "optional", "enhancement"]
        
        future_items = []
        for line in plan.split('\n'):
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in future_indicators):
                if line.strip() and not line.strip().startswith('#'):
                    future_items.append(line.strip())
        
        if future_items:
            return f"""**Current Phase:** {self.current_phase}

Items that may belong in future phases:
""" + "\n".join(f"- {item}" for item in future_items[:5])
        
        return f"""**Current Phase:** {self.current_phase}

✓ All items appear appropriate for Phase {self.current_phase}.
No items identified for deferral to future phases."""
    
    def _check_code_feasibility(self, plan: str) -> str:
        """Analyze plan from code implementation perspective."""
        # Look for technical components
        tech_stack = self._identify_tech_stack(plan)
        dependencies = self._identify_dependencies(plan)
        
        feasibility = f"""**Technology Stack Identified:**
{', '.join(tech_stack) if tech_stack else 'None explicitly specified'}

**Dependencies Detected:**
{', '.join(dependencies) if dependencies else 'None explicitly specified'}

**Implementation Notes:**
"""
        
        if not tech_stack:
            feasibility += "- Consider specifying technology stack\n"
        if not dependencies:
            feasibility += "- Consider listing required dependencies\n"
        
        feasibility += "- Ensure all components have clear implementation paths\n"
        feasibility += "- Verify API integrations are well-defined\n"
        
        return feasibility
    
    def _identify_tech_stack(self, plan: str) -> list:
        """Identify technologies mentioned in plan."""
        tech_keywords = [
            'python', 'docker', 'kubernetes', 'openai', 'anthropic',
            'langchain', 'autogen', 'fastapi', 'flask', 'django',
            'nodejs', 'react', 'vue', 'typescript', 'javascript'
        ]
        
        found_tech = []
        plan_lower = plan.lower()
        for tech in tech_keywords:
            if tech in plan_lower:
                found_tech.append(tech)
        
        return found_tech
    
    def _identify_dependencies(self, plan: str) -> list:
        """Identify external dependencies in plan."""
        # Look for common dependency indicators
        dependencies = []
        
        if 'openai' in plan.lower() or 'gpt' in plan.lower():
            dependencies.append('openai')
        if 'claude' in plan.lower() or 'anthropic' in plan.lower():
            dependencies.append('anthropic')
        if 'docker' in plan.lower():
            dependencies.append('docker')
        
        return dependencies
    
    def _check_structure(self, plan: str) -> str:
        """Analyze plan structure and organization."""
        lines = plan.split('\n')
        headers = [line for line in lines if line.strip().startswith('#')]
        
        structure = f"""**Plan Organization:**
- Total lines: {len(lines)}
- Section headers: {len(headers)}
- Has clear structure: {'Yes' if len(headers) >= 3 else 'Consider adding more sections'}

**Structure Quality:**
"""
        if len(headers) >= 3:
            structure += "✓ Plan has good hierarchical organization\n"
        else:
            structure += "⚠ Consider adding more section headers for clarity\n"
        
        return structure
    
    def _generate_recommendations(self, plan: str) -> str:
        """Generate specific recommendations for implementation."""
        recommendations = []
        
        plan_lower = plan.lower()
        
        if 'api' in plan_lower and 'key' not in plan_lower:
            recommendations.append("Consider documenting API key management strategy")
        
        if 'docker' in plan_lower and 'dockerfile' not in plan_lower:
            recommendations.append("Ensure Dockerfile is well-documented and follows best practices")
        
        if 'test' not in plan_lower:
            recommendations.append("Consider adding testing strategy to plan")
        
        if not recommendations:
            recommendations.append("Plan structure looks good for code implementation")
            recommendations.append("Ensure all components have clear acceptance criteria")
        
        return "\n".join(f"{i+1}. {rec}" for i, rec in enumerate(recommendations))
    
    def _check_convergence(self, plan: str, iteration: int) -> str:
        """Determine if plan is ready for implementation from code perspective."""
        # Simple heuristic: check if plan has minimum required elements
        has_objective = 'objective' in plan.lower() or 'goal' in plan.lower()
        has_requirements = 'requirement' in plan.lower() or 'feature' in plan.lower()
        has_structure = len([l for l in plan.split('\n') if l.strip().startswith('#')]) >= 3
        
        if has_objective and has_requirements and has_structure and iteration > 1:
            return "✓ Plan is ready for code implementation. No major changes needed from code perspective."
        elif iteration >= 3:
            return "⚠ Plan has been through multiple iterations. Ready to proceed with minor refinements."
        else:
            return "Additional iteration recommended to ensure all code implementation details are clear."


if __name__ == "__main__":
    # Test the agent
    agent = CopilotAgent(phase="1")
    test_plan = """# Test Plan

## Objective
Build a multi-agent orchestration system.

## Requirements
- Docker containerization
- Multi-LLM support using OpenAI and Anthropic APIs
- Iterative refinement loop

## Implementation
- Python-based orchestrator
- Agent modules for ChatGPT and Claude
"""
    
    review = agent.review_plan(test_plan, 1)
    print(review)
