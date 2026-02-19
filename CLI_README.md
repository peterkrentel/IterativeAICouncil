# AI Council CLI - Convergence Engine

A CLI-based iterative AI Council convergence engine for refining artifacts through multi-model collaboration.

## Overview

The AI Council CLI implements a structured debate and refinement process where:
- One AI model acts as a **proposer**, generating revisions
- Multiple AI models act as **critics**, providing structured feedback
- A **human gate** approves or rejects critiques
- The process iterates until convergence or maximum iterations

## Key Features

### 1. **Artifact Management**
- Tracks artifact ID, version, content, and change history
- Maintains complete revision history
- Generates diffs for each iteration

### 2. **Structured Critique System**
- JSON-based critique format with:
  - Critic name
  - Category (architecture|performance|security|simplicity|bug-risk|style)
  - Severity (1-5)
  - Location (optional)
  - Description
  - Suggested change

### 3. **Role Rotation**
- Models rotate as proposer across iterations
- Example rotation:
  - Iteration 1: GPT = proposer, Copilot & Augment = critics
  - Iteration 2: Copilot = proposer, GPT & Augment = critics
  - Iteration 3: Augment = proposer, GPT & Copilot = critics

### 4. **Human-in-the-Loop**
- Every iteration requires human approval
- Options to:
  - Apply all critiques
  - Selectively apply critiques
  - Reject all critiques
  - Stop iteration

### 5. **Convergence Detection**
- Stops when:
  - No severity ≥3 critiques remain
  - Structural diff < 5%
  - Maximum iterations reached
  - Human selects stop

### 6. **Complete Output**
- Final artifact file
- `iteration_log.json` - Complete iteration history
- `critique_history.json` - All critiques received
- `diff_history/` - Diffs for each iteration

## Installation

### Prerequisites
- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`):
  - openai (optional, for actual LLM integration)
  - anthropic (optional, for actual LLM integration)

### Setup
```bash
# Clone repository
git clone https://github.com/peterkrentel/IterativeAICouncil.git
cd IterativeAICouncil

# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x bin/aicouncil
chmod +x aicouncil.py
```

## Usage

### Basic Command
```bash
python aicouncil.py converge <input_file> --models <model1>,<model2>,<model3>
```

### Examples

#### Example 1: Refine a Markdown document
```bash
python aicouncil.py converge input.md --models gpt,copilot,augment
```

#### Example 2: Custom iterations and output directory
```bash
python aicouncil.py converge design.md --models gpt,copilot,augment --max-iterations 4 --output ./results
```

#### Example 3: Code file refinement
```bash
python aicouncil.py converge script.py --models claude,gpt --max-iterations 3
```

### Command Options

- `input_file` - Path to input artifact (Markdown or code file)
- `--models` - Comma-separated list of model names (minimum 2)
- `--max-iterations` - Maximum iterations (default: 5)
- `--output` - Output directory (default: ./output)

## Execution Flow

The engine follows a 7-state process:

### STATE 0: Load Artifact
- Load input file
- Initialize artifact with version 1
- Create empty history

### STATE 1: Proposer Generation
- Selected model generates revised artifact
- Proposer rotates each iteration

### STATE 2: Run Critics in Parallel
- All non-proposer models critique the revision
- Return structured JSON critiques

### STATE 3: Consolidate Critiques
- Remove duplicate critiques
- Group by category and location
- Display summary

### STATE 4: Human Approval Gate
- Display all critiques with severity and details
- Prompt for user decision:
  - Apply all (a)
  - Selective apply (s)
  - Reject all (r)
  - Quit/Stop (q)

### STATE 5: Apply Critiques
- Apply approved critiques to artifact
- Update version number
- Record in history

### STATE 6: Convergence Check
- Check if no high-severity critiques remain
- Calculate structural diff ratio
- Determine if convergence achieved
- Continue or stop iteration

### Output Generation
- Save final artifact
- Save iteration log
- Save critique history
- Save all diffs

## Output Structure

After running, you'll find:

```
output/
├── <artifact_name>_final.md     # Final refined artifact
├── iteration_log.json            # Complete iteration history
├── critique_history.json         # All critiques from all iterations
└── diff_history/                 # Diffs for each iteration
    ├── iteration_1.diff
    ├── iteration_2.diff
    └── ...
```

### iteration_log.json Structure
```json
{
  "iterations": [
    {
      "iteration_number": 1,
      "proposer": "gpt",
      "critics": ["copilot", "augment"],
      "critiques_received": [...],
      "applied_critiques": [...],
      "rejected_critiques": [...],
      "diff_summary": "Changed 15.3% of content",
      "convergence_score": 0.65
    }
  ],
  "total_iterations": 3,
  "final_version": 4
}
```

### critique_history.json Structure
```json
[
  {
    "iteration": 1,
    "critic": "copilot",
    "category": "bug-risk",
    "severity": 3,
    "location": "function parse_input",
    "description": "Missing input validation",
    "suggested_change": "Add validation for edge cases"
  }
]
```

## Critique Categories

| Category | Description |
|----------|-------------|
| architecture | System design, structure, patterns |
| performance | Speed, efficiency, scalability |
| security | Vulnerabilities, auth, data protection |
| simplicity | Code clarity, maintainability |
| bug-risk | Potential bugs, edge cases |
| style | Formatting, naming, conventions |

## Severity Levels

- **1-2**: Minor/Low - Nice to have improvements
- **3**: Medium - Should be addressed
- **4-5**: High/Critical - Must be addressed

## Guardrails

1. **Max 5 iterations** (configurable)
2. **Critics cannot rewrite** - Only provide structured feedback
3. **Proposer cannot add features** - Only refines based on input
4. **Human approval required** - Every iteration needs approval
5. **Convergence enforced** - Process stops at convergence or max iterations

## Philosophy

> **The human decides quality.**
> The system structures debate, enforces iteration, and tracks convergence.

## Placeholder LLM Functions

The current implementation includes placeholder functions for LLM API calls:
- `_call_proposer_llm()` - Returns mock revised content
- `_call_critic_llm()` - Returns mock critiques
- `_apply_critiques_to_content()` - Returns mock applied changes

### Integrating Real LLM APIs

To integrate actual LLM APIs, implement these functions in `aicouncil.py`:

```python
def _call_proposer_llm(self, proposer: str, artifact: Artifact, iteration_num: int) -> str:
    # Call actual LLM API (OpenAI, Anthropic, etc.)
    # Return revised artifact content
    pass

def _call_critic_llm(self, critic: str, artifact: Artifact, iteration_num: int) -> List[Critique]:
    # Call actual LLM API
    # Parse response into List[Critique]
    pass

def _apply_critiques_to_content(self, content: str, critiques: List[Critique]) -> str:
    # Call LLM to apply critiques to content
    # Return updated content
    pass
```

## Testing

Run the automated test:
```bash
python test_aicouncil.py
```

This tests:
- Artifact loading
- Proposer generation
- Critic execution
- Critique consolidation
- Convergence checking
- Output file generation

## Future Enhancements

- [ ] Integrate actual LLM APIs (OpenAI, Anthropic, etc.)
- [ ] Add Devil's Advocate role for additional critique
- [ ] Support for embeddings and vector DB for semantic similarity
- [ ] Web UI for better visualization
- [ ] Persistent database for history
- [ ] Multi-threaded parallel critic execution
- [ ] Advanced convergence metrics
- [ ] Support for more file types (code, JSON, YAML, etc.)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

See LICENSE file for details.

## Related Tools

This CLI tool is part of the IterativeAICouncil project, which also includes:
- Orchestrator for plan refinement (`agents/orchestrator.py`)
- Individual AI agents (ChatGPT, Claude, Copilot)
- Docker containerization

---

**Status:** MVP - Ready for LLM API integration
