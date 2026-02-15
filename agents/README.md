# Agents Module

This directory contains the agent implementations and orchestrator for IterativeAICouncil.

## Files

### `orchestrator.py`
Main orchestrator that coordinates the multi-LLM feedback loop. It:
- Reads the initial plan from `ai/01_plan.md`
- Calls all agents iteratively
- Merges feedback from agents
- Checks for convergence
- Writes final plan to `ai/05_final.md`

**Usage:**
```bash
python orchestrator.py
```

**Environment Variables:**
- `AI_DIR` - Directory containing plan files (default: ./ai)
- `MAX_ITERATIONS` - Maximum refinement iterations (default: 5)
- `OPENAI_KEY` - OpenAI API key for ChatGPT agent
- `CLAUDE_KEY` - Anthropic API key for Claude agent

### `chatgpt_agent.py`
Agent that uses OpenAI's GPT API to review and refine plans. Focuses on:
- Clarity and completeness
- Technical feasibility
- Architectural soundness
- Phase appropriateness

**Standalone usage:**
```bash
python chatgpt_agent.py
```

### `claude_agent.py`
Agent that uses Anthropic's Claude API for critical review. Focuses on:
- Security considerations
- Error handling and edge cases
- Performance and scalability
- Dependency risks

**Standalone usage:**
```bash
python claude_agent.py
```

### `copilot_agent.py`
Agent that performs code-level and phase-aware validation. Focuses on:
- Code implementation feasibility
- Phase appropriateness
- Technical stack analysis
- Structure and organization

**Standalone usage:**
```bash
python copilot_agent.py
```

## Agent Interface

All agents implement the same interface:

```python
class Agent:
    def review_plan(self, plan: str, iteration: int) -> str:
        """
        Review the plan and provide feedback.
        
        Args:
            plan: Current plan content
            iteration: Current iteration number
            
        Returns:
            Review feedback as markdown text
        """
        pass
```

## Mock Mode

All agents support **mock mode** for testing without API keys:
- Agents automatically detect missing API keys
- Generate placeholder reviews
- Useful for development and testing

## Extending Agents

To add a new agent:

1. Create a new file `your_agent.py`
2. Implement the agent class with `review_plan()` method
3. Add import to `__init__.py`
4. Update orchestrator to include the new agent

Example:

```python
# your_agent.py
class YourAgent:
    def review_plan(self, plan: str, iteration: int) -> str:
        # Your review logic here
        return "# Your Agent Review\n\n..."
```

```python
# orchestrator.py
from your_agent import YourAgent

# Add to agents dict
self.agents = {
    'chatgpt': ChatGPTAgent(),
    'claude': ClaudeAgent(),
    'copilot': CopilotAgent(),
    'your_agent': YourAgent()  # Add your agent
}
```

## Framework Integration

The agent architecture is designed to be upgraded to frameworks like:
- **LangChain** - For more sophisticated agent chains and memory
- **AutoGen** - For multi-agent conversations
- **OpenClaw** - For advanced orchestration

Simply replace the agent implementations while maintaining the interface.

## Testing

Each agent can be tested independently:

```bash
# Test all agents
python chatgpt_agent.py
python claude_agent.py
python copilot_agent.py

# Test orchestrator
python orchestrator.py
```

## Performance Considerations

- Agents are called sequentially (not in parallel)
- Each iteration calls all agents
- API calls may take time depending on model and response size
- Consider implementing caching for repeated plan reviews

## Future Enhancements

Potential improvements:
- Parallel agent execution
- Streaming responses
- Agent memory and context retention
- More sophisticated convergence detection
- AI-driven feedback merging
- Custom phase management rules
