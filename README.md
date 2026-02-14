# IterativeAICouncil

## Overview

**IterativeAICouncil** is a multi-LLM, phase-aware, iterative plan refinement system.  

- Multiple LLMs act as a "council" reviewing, critiquing, and improving plans.  
- Each iteration incorporates feedback from all agents until **tradeoff consensus** is achieved.  
- Phase-aware execution prevents overbuilding and allows items to move to future phases.  
- Fully **Dockerized** for portability and lift-and-shift deployment.  

---

## Features

- **Multi-Agent Loop:** ChatGPT generates initial plan, Claude reviews and hardens it, Copilot/Augment performs code-level and phase-aware checks.  
- **Iteration Until Convergence:** Loop continues until all agents agree that plan is complete.  
- **Phase Management:** Supports splitting work across multiple phases.  
- **Portable & Scalable:** Docker container encapsulates orchestrator, agents, dependencies, and API keys.  
- **Future-Proof:** Agent scripts can be upgraded to LangChain, AutoGen, or OpenClaw frameworks.  

---

## Folder Structure

```
/IterativeAICouncil
  /ai
    01_plan.md               # Initial plan
    02_review_chatgpt.md     # ChatGPT agent output
    03_review_claude.md      # Claude agent output
    04_review_copilot.md     # Copilot/Augment agent output
    05_final.md              # Merged & stabilized plan
    tradeoff_log.md          # Optional: convergence and decision log
  /agents
    chatgpt_agent.py
    claude_agent.py
    copilot_agent.py
    orchestrator.py           # Main orchestrator script
  Dockerfile
  requirements.txt
  config.env                # Stores API keys (OpenAI, Claude)
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/peterkrentel/IterativeAICouncil.git
cd IterativeAICouncil
```

### 2. Configure API Keys

Create a `config.env` file:

```bash
OPENAI_KEY=your_openai_api_key
CLAUDE_KEY=your_claude_api_key
# Optional: Copilot token or Augment credentials if available
```

These keys will be loaded by the orchestrator and agent scripts.

---

### 3. Build Docker Container

```bash
docker build -t iterative-ai-council .
```

---

### 4. Run the Orchestrator

```bash
docker run -v $(pwd)/ai:/app/ai --env-file config.env iterative-ai-council
```

- Mounting `/ai` ensures that plan and review files persist outside the container.
- The orchestrator runs iterative loops, calls all agents, merges feedback, and outputs the final plan to `05_final.md`.

---

## Workflow

1. **Ground Plan**
   - Start with `01_plan.md`.
   - ChatGPT agent generates initial plan structure.

2. **LLM Reviews**
   - ChatGPT reviews plan → `02_review_chatgpt.md`.
   - Claude reviews plan → `03_review_claude.md`.
   - Copilot/Augment reviews plan → `04_review_copilot.md`.

3. **Integrator / Feedback Merge**
   - Orchestrator merges feedback from all agents into `01_plan.md`.
   - Updates `05_final.md` with stabilized plan.

4. **Iteration / Convergence**
   - Loop continues until no new critical feedback emerges.
   - Tradeoff and phase-aware decisions logged in `tradeoff_log.md`.

---

## Agent Implementation Notes

- **ChatGPT Agent:** Calls OpenAI API to review and refine plan.
- **Claude Agent:** Calls Anthropic API to critique plan and suggest improvements.
- **Copilot/Augment Agent:** Can read/write plan files via VSCode integration.
- **Future Upgrade:** Replace agents with multi-agent frameworks (LangChain, OpenClaw) without changing orchestrator logic.

---

## Phase Management

- Items not relevant to current phase are automatically moved to future phases.
- Phase boundaries are tracked in `tradeoff_log.md`.
- Orchestrator ensures that implementation only occurs at correct phase scope.

---

## Next Steps for Copilot / Augment

1. Generate agent scripts: `chatgpt_agent.py`, `claude_agent.py`, `copilot_agent.py` using API calls or VSCode hooks.
2. Build orchestrator logic: read plan, call agents, merge feedback, loop until convergence.
3. Implement merge & convergence heuristics: simple diff-based first, upgrade to AI-driven later.
4. Add optional logging: track tradeoffs, decisions, and phase transitions.

---

## Goals for Phase 1

- Fully automated iterative plan refinement inside Docker container.
- Multi-LLM feedback loop operating without manual copy/paste.
- Phase-aware output for code implementation via Augment/Copilot.
- Portable for cloud deployment or multiple team members.

---

**Repo Name:** IterativeAICouncil  
**Alias in code:** iac (optional)  
**Status:** Phase 1 Dockerized Agent Orchestrator
