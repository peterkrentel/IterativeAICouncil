# Quick Start Guide

This guide will help you get IterativeAICouncil up and running quickly.

## Prerequisites

- Docker installed on your system
- OpenAI API key (for ChatGPT agent)
- Anthropic API key (for Claude agent)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/peterkrentel/IterativeAICouncil.git
cd IterativeAICouncil
```

### 2. Configure API Keys

Copy the example config file and add your API keys:

```bash
cp config.env.example config.env
```

Edit `config.env` and add your actual API keys:

```bash
OPENAI_KEY=sk-your-actual-openai-key-here
CLAUDE_KEY=sk-ant-your-actual-claude-key-here
```

### 3. Create Your Initial Plan

Edit the file `ai/01_plan.md` with your actual project plan. This is what the agents will review and refine.

Example plan structure:

```markdown
# My Project Plan

## Objectives
- Build a web application for task management
- Support multiple users
- Mobile-responsive design

## Requirements
- User authentication
- Task CRUD operations
- Real-time updates
...
```

### 4. Build the Docker Image

```bash
docker build -t iterative-ai-council .
```

This will create a Docker image with all dependencies installed.

### 5. Run the Orchestrator

```bash
docker run --rm \
  -v $(pwd)/ai:/app/ai \
  --env-file config.env \
  iterative-ai-council
```

**What this does:**
- `--rm` - Removes container after it exits
- `-v $(pwd)/ai:/app/ai` - Mounts your local `ai/` directory so changes persist
- `--env-file config.env` - Loads your API keys from config.env
- `iterative-ai-council` - Runs the orchestrator

### 6. Review the Results

After the orchestrator completes, check these files:

- `ai/05_final.md` - Final refined plan
- `ai/02_review_chatgpt.md` - ChatGPT's review
- `ai/03_review_claude.md` - Claude's review
- `ai/04_review_copilot.md` - Copilot agent's review
- `ai/tradeoff_log.md` - Decision log

## Running Without Docker

If you prefer to run without Docker:

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export OPENAI_KEY="your-key-here"
export CLAUDE_KEY="your-key-here"
```

Or use a .env file with python-dotenv.

### 3. Run the Orchestrator

```bash
cd agents
python orchestrator.py
```

## Mock Mode (Testing Without API Keys)

If you don't have API keys yet, the agents will run in **mock mode** and generate placeholder reviews. This is useful for:
- Testing the system
- Understanding the workflow
- Development

Simply run without setting the API keys and you'll see mock reviews generated.

## Configuration Options

You can customize the behavior using environment variables:

```bash
docker run --rm \
  -v $(pwd)/ai:/app/ai \
  --env-file config.env \
  -e MAX_ITERATIONS=3 \
  -e CURRENT_PHASE=1 \
  iterative-ai-council
```

**Available options:**
- `MAX_ITERATIONS` - Maximum refinement iterations (default: 5)
- `CURRENT_PHASE` - Current project phase (default: 1)
- `AI_DIR` - Directory for plan files (default: ./ai)

## Troubleshooting

### "No initial plan found"

Make sure `ai/01_plan.md` exists and contains your plan before running the orchestrator.

### API Errors

- Verify your API keys are correct
- Check that you have credits/quota available
- Ensure your keys have the necessary permissions

### Docker Volume Issues

On Windows, use PowerShell and adjust the volume mount:

```powershell
docker run --rm `
  -v ${PWD}/ai:/app/ai `
  --env-file config.env `
  iterative-ai-council
```

## Next Steps

1. Review the generated reviews and final plan
2. Iterate on your plan based on feedback
3. Run the orchestrator again with updated plan
4. Continue until convergence is achieved
5. Use the final plan for implementation

## Advanced Usage

### Custom Agent Behavior

You can modify the agent scripts in `agents/` to customize:
- Review prompts
- Convergence criteria
- Feedback merging logic
- Phase management rules

### Integration with CI/CD

You can integrate this into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Refine Plan
  run: |
    docker run --rm \
      -v ${{ github.workspace }}/ai:/app/ai \
      -e OPENAI_KEY=${{ secrets.OPENAI_KEY }} \
      -e CLAUDE_KEY=${{ secrets.CLAUDE_KEY }} \
      iterative-ai-council
```

### Using with LangChain/AutoGen

The agent architecture is designed to be upgraded to frameworks like LangChain or AutoGen without changing the orchestrator. Simply replace the agent implementations while maintaining the same interface.

## Support

For issues or questions, please open an issue on GitHub.
