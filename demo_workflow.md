# Demo: AI Council CLI Workflow

## Setup
```bash
# Ensure you're in the project directory
cd /path/to/IterativeAICouncil

# Verify CLI is working
python aicouncil.py --help
```

## Example 1: Simple Workflow

### Step 1: View Sample Input
```bash
cat sample_input.md
```

### Step 2: Run Convergence (Mock Mode)
```bash
# Run with 3 models, max 2 iterations
python aicouncil.py converge sample_input.md \
  --models gpt,copilot,claude \
  --max-iterations 2 \
  --output ./demo_output
```

### What Happens:
1. **STATE 0**: Loads artifact from sample_input.md
2. **Iteration 1**:
   - GPT acts as proposer (generates revision)
   - Copilot and Claude act as critics (provide critiques)
   - System shows critiques with severity and categories
   - You approve/reject (in demo, mock critiques shown)
   - Changes applied to artifact
3. **STATE 6**: Checks convergence
4. **Repeat** if not converged
5. **Output**: Final artifact and logs saved

### Step 3: View Results
```bash
# View final artifact
cat demo_output/sample_input_final.md

# View iteration log
cat demo_output/iteration_log.json

# View critique history
cat demo_output/critique_history.json

# View diffs
ls demo_output/diff_history/
```

## Example 2: E-Commerce API Design

```bash
cd examples

python ../aicouncil.py converge ecommerce_api.md \
  --models gpt,copilot,claude \
  --max-iterations 3 \
  --output ../ecommerce_output
```

### Expected Workflow:
- **Iteration 1**: GPT proposes improvements
  - Copilot critiques: Implementation feasibility
  - Claude critiques: Security concerns
  - Human reviews and selects critiques to apply

- **Iteration 2**: Copilot proposes refinements
  - GPT critiques: Clarity and completeness
  - Claude critiques: Additional security checks
  - Human reviews and applies critiques

- **Iteration 3**: Claude proposes final hardening
  - GPT critiques: Documentation quality
  - Copilot critiques: Code implementation readiness
  - Human approves or rejects

- **Convergence**: System stops when:
  - No high-severity (≥3) critiques remain
  - Structural changes < 5%
  - Or max iterations reached

## Example 3: Code Refinement

```bash
cd examples

python ../aicouncil.py converge simple_function.py \
  --models gpt,copilot \
  --max-iterations 3 \
  --output ../code_output
```

### Mock Critiques You'll See:
- **GPT**: Simplicity improvements
- **Copilot**: Bug risk detection (missing validation)
- **Claude** (if included): Security issues

## Interactive Mode

During each iteration, you'll see:

```
============================================================
STATE 4: Human Approval Gate
============================================================

Received 2 critique(s):

1. [3/5] BUG-RISK - copilot
   Location: function parse_input
   Issue: Missing input validation
   Suggestion: Add validation for edge cases and null inputs

2. [4/5] SECURITY - claude
   Location: authentication section
   Issue: Potential security vulnerability in auth flow
   Suggestion: Implement rate limiting and secure token storage

⚠ 1 high-severity critique(s) (severity ≥3)

Options:
  a - Apply all critiques
  s - Selective apply (choose which to apply)
  r - Reject all critiques
  q - Stop iteration (quit)

Your choice [a/s/r/q]:
```

## Output Files Explained

### 1. `<name>_final.md`
The final refined version of your artifact after all iterations.

### 2. `iteration_log.json`
Complete history of all iterations:
```json
{
  "iterations": [
    {
      "iteration_number": 1,
      "proposer": "gpt",
      "critics": ["copilot", "claude"],
      "critiques_received": [...],
      "applied_critiques": [...],
      "rejected_critiques": [...],
      "diff_summary": "Changed 15.3% of content",
      "convergence_score": 0.65
    }
  ],
  "total_iterations": 2,
  "final_version": 3
}
```

### 3. `critique_history.json`
All critiques from all iterations:
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

### 4. `diff_history/`
Unified diffs showing exactly what changed:
```
diff_history/
├── iteration_1.diff
├── iteration_2.diff
└── iteration_3.diff
```

## Tips

1. **Start with 2 iterations** to get familiar with the workflow
2. **Use selective apply** to have fine control over changes
3. **High-severity critiques** (≥3) should be addressed for convergence
4. **Review diffs** to understand what changed between iterations
5. **Mock mode** helps you understand the workflow before LLM integration

## Next: Real LLM Integration

To integrate real LLM APIs, edit `aicouncil.py` and implement:
- `_call_proposer_llm()` - Call OpenAI/Anthropic API
- `_call_critic_llm()` - Call LLM with structured critique prompt
- `_apply_critiques_to_content()` - Call LLM to apply changes

See CLI_README.md for integration details.
