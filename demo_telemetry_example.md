# Telemetry & Human Override Tracking Demo

## Example telemetry.jsonl Output

Each line is a JSON object representing one iteration:

```jsonl
{"iteration": 1, "agent_initiator": "gpt", "agent_responses": {"copilot": "REJECT_MODERATE", "claude": "TIGHTEN_ONLY"}, "applied_critiques": [{"critic": "copilot", "category": "bug-risk", "severity": 4, "location": "line 42", "description": "Missing null check", "suggested_change": "Add validation"}], "improvement_delta": 85.0, "remaining_issues": [], "ship_it": false, "human_override": "accepted", "notes": null, "timestamp": "2026-02-19T10:30:15.123456"}
{"iteration": 2, "agent_initiator": "copilot", "agent_responses": {"gpt": "APPROVED", "claude": "APPROVED"}, "applied_critiques": [], "improvement_delta": 5.0, "remaining_issues": [], "ship_it": true, "human_override": "accepted", "notes": null, "timestamp": "2026-02-19T10:31:22.654321"}
```

## Human Override Field Values

- `"accepted"` - Human approved critiques (choices: 'a' or 's' with approvals)
- `"rejected"` - Human rejected critiques (choices: 'r' or 'q')
- `null` - No human interaction (automatic processing)

## Usage

The telemetry file is:
- **Append-only**: New iterations add lines, never modifies existing
- **Side-effect free**: Logging failures don't block convergence
- **Machine-readable**: JSONL format for easy parsing
- **Complete audit trail**: Full iteration history with timestamps

## Processing Telemetry

```python
import json

# Read telemetry file
with open('output/telemetry.jsonl', 'r') as f:
    iterations = [json.loads(line) for line in f]

# Analyze iterations
for iter_data in iterations:
    print(f"Iteration {iter_data['iteration']}:")
    print(f"  Proposer: {iter_data['agent_initiator']}")
    print(f"  Ship it: {iter_data['ship_it']}")
    print(f"  Quality delta: {iter_data['improvement_delta']:+.1f}")
    print(f"  Human override: {iter_data['human_override']}")
```
