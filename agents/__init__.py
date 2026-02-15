"""
IterativeAICouncil Agents Package
==================================

Multi-LLM agent modules for iterative plan refinement.
"""

from .chatgpt_agent import ChatGPTAgent
from .claude_agent import ClaudeAgent
from .copilot_agent import CopilotAgent

__all__ = ['ChatGPTAgent', 'ClaudeAgent', 'CopilotAgent']
__version__ = '1.0.0'
