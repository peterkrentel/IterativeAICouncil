# IterativeAICouncil

## Overview

**IterativeAICouncil** is a multi-LLM, phase-aware, iterative plan refinement system with two modes of operation:

1. **Plan Orchestrator** - Multi-agent iterative plan refinement (original system)
2. **CLI Convergence Engine** - Interactive artifact refinement with human-in-the-loop (NEW!)

### Plan Orchestrator
- Multiple LLMs act as a "council" reviewing, critiquing, and improving plans.  
- Each iteration incorporates feedback from all agents until **tradeoff consensus** is achieved.  
- Phase-aware execution prevents overbuilding and allows items to move to future phases.  
- Fully **Dockerized** for portability and lift-and-shift deployment.

### CLI Convergence Engine ⚡ NEW!
- **Interactive CLI** for artifact refinement with structured critique workflow
- **Role rotation**: Models alternate as proposer and critics across iterations
- **Human approval gate**: Review and approve/reject critiques at each iteration
- **Convergence detection**: Auto-stops when critiques are minimal or structural changes < 5%
- **Complete audit trail**: Iteration logs, critique history, and diffs for every change

👉 **See [CLI_README.md](CLI_README.md) for CLI tool documentation**

---

## When to Use This System

**Ideal for:**
- 📋 **Complex Project Plans** - Technical specifications, architecture documents, implementation roadmaps
- 🏗️ **Software Design Documents** - API designs, system architectures, database schemas
- 📝 **Technical Proposals** - RFPs, technical white papers, research proposals
- 🎯 **Strategic Planning** - Multi-phase project plans requiring stakeholder consensus

**Not recommended for:**
- ⚠️ Simple configuration files or environment variables
- ⚠️ Single-value decisions or yes/no questions
- ⚠️ Quick edits to existing documents
- ⚠️ Non-technical content without clear requirements

**The system excels when you need:**
- Multiple AI perspectives (ChatGPT for clarity, Claude for security, Copilot for implementation)
- Iterative refinement until all agents reach consensus
- Phase-aware validation to prevent scope creep
- Documented decision history via tradeoff logs

---

## Example Use Cases

### ✅ Good Use Case: Microservices Architecture Plan
```markdown
# Initial Plan (ai/01_plan.md)
## Project: E-Commerce Platform Microservices

### Architecture Goals
- Decompose monolith into 5 microservices
- Event-driven communication via message queues
- Independent deployment pipelines

### Phase 1: Authentication Service
- JWT-based auth
- OAuth2 integration
- Rate limiting
...
```
**Result:** ChatGPT ensures completeness, Claude identifies security gaps (OWASP compliance, token storage), Copilot validates implementation feasibility.

### ❌ Poor Use Case: Simple Configuration
```markdown
# Should we use Redis or Memcached?
```
**Why it's overkill:** This is a single decision point. Use a single LLM or make the decision directly.

### ✅ Good Use Case: API Design Document
Multi-page REST API specification requiring consensus on endpoints, authentication, versioning, error handling, and rate limiting across multiple stakeholders.

### ❌ Poor Use Case: Bug Fix Description
Single bug report or feature request. Too narrow for multi-agent review.

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

**Visual Overview:**

```
┌─────────────────┐
│  01_plan.md     │  ← You create initial plan
│  (Iteration 0)  │
└────────┬────────┘
         │
         ▼
    ┌────────────────────┐
    │  ITERATION LOOP    │
    └────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Step A: Multi-Agent Review        │
├────────────────────────────────────┤
│  ChatGPT → 02_review_chatgpt.md   │
│  Claude  → 03_review_claude.md    │
│  Copilot → 04_review_copilot.md   │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Step B: AI Integration            │
├────────────────────────────────────┤
│  ChatGPT reads:                    │
│   • Current plan (01_plan.md)      │
│   • All agent reviews              │
│  ↓                                 │
│  Generates UPDATED plan            │
│  (addresses feedback, fixes issues)│
│  ↓                                 │
│  Writes back to 01_plan.md         │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Step C: Convergence Check         │
├────────────────────────────────────┤
│  Agents approve? Few concerns?     │
└────────┬───────────────────────────┘
         │
    ┌────┴────┐
    │         │
    NO       YES
    │         │
    │         ▼
    │    ┌─────────────┐
    │    │ 05_final.md │
    │    └─────────────┘
    │
    └─► Loop back to Step A
        (with updated plan)
```

**How the iterative refinement actually works:**

1. **Initial Plan Input**
   - You create `ai/01_plan.md` with your project plan
   - This is the starting point - can be rough, incomplete, or early draft

2. **Iteration Loop** (repeats until convergence):
   
   **Step A: Multi-Agent Review**
   - ChatGPT reviews the current plan → analyzes clarity, completeness, feasibility
   - Claude reviews the current plan → identifies security risks, edge cases, concerns  
   - Copilot reviews the current plan → checks code feasibility, phase appropriateness
   - Each agent writes their review to `02-04_review_*.md`

   **Step B: Feedback Integration with Judgment**
   - **ChatGPT acts as integrator with judgment**: Takes original plan + all agent feedback
   - **Evaluates each piece of feedback** for quality, relevance, and actionability
   - **Identifies synergies**: When multiple agents mention similar concerns, prioritizes those
   - **Resolves conflicts**: When agents disagree, makes judgment calls based on expertise domain
   - **Selectively integrates** only valuable feedback that improves the plan
   - **Updates the plan content** based on selected feedback (not just appending!)
   - Writes updated plan back to `01_plan.md` with integration notes

   **Step C: Convergence Check**
   - Analyzes agent reviews for approval signals vs. concerns
   - If agents approve (>60% threshold) and few concerns remain → **DONE**
   - Otherwise → loop back to Step A with the updated plan

3. **Final Output**
   - Converged plan written to `05_final.md`
   - All iteration history in `tradeoff_log.md`
   - Individual agent reviews preserved in `02-04_review_*.md`

**Key Point:** The plan content actually changes each iteration based on agent feedback. This is true iterative refinement, not just review collection.

**Intelligent Judgment Process:**

The integrator doesn't blindly accept all feedback. It uses judgment to:

1. **Quality Filter**: Evaluates if feedback is specific and actionable vs. vague
2. **Synergy Detection**: When multiple agents flag the same issue, it gets priority
3. **Conflict Resolution**: When agents disagree (e.g., "add more detail" vs. "too complex"), the integrator:
   - Considers which agent's expertise is most relevant
   - Makes balanced judgment calls
   - Documents reasoning in integration notes
4. **Selective Integration**: Only includes feedback that genuinely improves the plan

**Example:**
- ChatGPT: "Add authentication details"
- Claude: "Need OAuth2 security specs"  
- Copilot: "JWT implementation feasible"
- **Integration**: All three align → High priority, all integrated
- But if Claude says "use OAuth2" and Copilot says "OAuth2 too complex for Phase 1" → Integrator judges based on phase scope

**Important Note - Mock Mode vs Real Mode:**
- **With API Keys (Real Mode):** ChatGPT intelligently integrates feedback with judgment
- **Without API Keys (Mock Mode):** System appends feedback for demonstration purposes
- Configure `OPENAI_KEY` and `CLAUDE_KEY` for full AI-driven integration

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

## Quick Start - CLI Convergence Engine

### Installation
```bash
git clone https://github.com/peterkrentel/IterativeAICouncil.git
cd IterativeAICouncil
pip install -r requirements.txt
```

### Basic Usage
```bash
# Refine a Markdown document
python aicouncil.py converge input.md --models gpt,copilot,claude

# Refine with custom iterations
python aicouncil.py converge design.md --models gpt,copilot --max-iterations 4

# See all options
python aicouncil.py converge --help
```

### Example Run
```bash
cd examples
python ../aicouncil.py converge ecommerce_api.md --models gpt,copilot,claude
```

**Process:**
1. Load artifact
2. For each iteration:
   - One model proposes revision
   - Other models critique
   - You approve/reject critiques
   - System applies changes
3. Stops at convergence or max iterations
4. Outputs: final artifact, iteration log, critique history, diffs

👉 **Full documentation:** [CLI_README.md](CLI_README.md)  
👉 **Examples:** [examples/README.md](examples/README.md)

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
