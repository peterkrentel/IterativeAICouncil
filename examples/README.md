# Examples for AI Council CLI

This directory contains example input files for testing the AI Council CLI.

## Available Examples

### 1. ecommerce_api.md
A comprehensive e-commerce API design document.

**Usage:**
```bash
python ../aicouncil.py converge ecommerce_api.md --models gpt,copilot,claude --max-iterations 3
```

**What it demonstrates:**
- API endpoint design refinement
- Security review (authentication, authorization)
- Architecture feedback
- Data model validation

### 2. simple_function.py
A simple Python function for demonstration.

**Usage:**
```bash
python ../aicouncil.py converge simple_function.py --models gpt,copilot --max-iterations 2
```

**What it demonstrates:**
- Code quality improvements
- Bug risk detection
- Style and simplicity feedback

## Running Examples

From the `examples/` directory:

```bash
# Run with 3 models
python ../aicouncil.py converge ecommerce_api.md --models gpt,copilot,claude

# Run with custom iterations
python ../aicouncil.py converge ecommerce_api.md --models gpt,copilot --max-iterations 4

# Run with custom output directory
python ../aicouncil.py converge ecommerce_api.md --models gpt,copilot,claude --output ../my_results
```

## Expected Workflow

1. **Load artifact**: The CLI loads your input file
2. **Iteration 1**:
   - GPT acts as proposer (generates revision)
   - Copilot and Claude act as critics (provide critiques)
   - You review and approve/reject critiques
3. **Iteration 2**:
   - Copilot acts as proposer
   - GPT and Claude act as critics
   - You review and approve/reject critiques
4. **Iteration 3** (if needed):
   - Claude acts as proposer
   - GPT and Copilot act as critics
   - You review and approve/reject critiques
5. **Convergence**: Process stops when critiques are minimal or max iterations reached

## Output Files

After running, you'll find in the output directory:

- `<filename>_final.md` - Final refined version
- `iteration_log.json` - Complete history
- `critique_history.json` - All critiques
- `diff_history/` - Diffs for each iteration

## Tips

- Use **selective apply** to have fine-grained control over which critiques to apply
- High-severity critiques (≥3) should be addressed for convergence
- The process will auto-stop when structural changes are < 5%
