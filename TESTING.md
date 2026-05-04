# Testing Guide

## E2E Testing Options

There are two E2E testing paths available. The **default CI E2E** is cloud-agnostic and runs automatically on every pull request. The **AWS E2E** is an optional manual workflow for testing on real cloud infrastructure.

### Option A: Cloud-Agnostic CI E2E (Default — k3d + Helm)

- **Workflow:** `.github/workflows/06-e2e-k3d.yml`
- **Triggers:** Every pull request + manual (`workflow_dispatch`)
- **Requirements:** None — runs entirely on the GitHub Actions runner. No cloud account or credentials needed.
- **How it works:**
  1. Builds the Docker image locally on the runner.
  2. Spins up a [k3d](https://k3d.io) (k3s-in-docker) cluster.
  3. Imports the built image directly into the cluster — **no registry push/pull**.
  4. Deploys the app via the Helm chart at `helm/aicouncil/`.
  5. Waits for rollout and curls `http://localhost:30080/health`.
  6. Cleans up the cluster in an `always()` step.

**Run locally (same steps as CI):**
```bash
# 1. Install k3d: https://k3d.io/#installation
# 2. Create cluster
k3d cluster create aicouncil -p "30080:30080@server:0" --wait

# 3. Build & import image
docker build -t aicouncil:dev .
k3d image import aicouncil:dev -c aicouncil

# 4. Deploy
helm upgrade --install aicouncil ./helm/aicouncil \
  --set image.tag=dev \
  --set image.pullPolicy=IfNotPresent

# 5. Test
curl http://localhost:30080/health

# 6. Cleanup
k3d cluster delete aicouncil
```

---

### Option B: AWS-Based E2E (Optional / Manual)

- **Workflow:** `.github/workflows/05-e2e-test.yml`
- **Triggers:** **Manual only** (`workflow_dispatch` — does **not** run on push or PR)
- **Use when:** You want to validate a production-like deployment on real AWS infrastructure (EC2 + K3s + ECR).

#### Prerequisites

The following GitHub repository secrets must be configured before running this workflow:

| Secret | Description |
|---|---|
| `AWS_ROLE_ARN` | IAM Role ARN for GitHub Actions OIDC federation (e.g. `arn:aws:iam::123456789012:role/github-actions-role`) |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `GROQ_API_KEY` | Groq API key (get from https://console.groq.com/keys) |
| `GOOGLE_API_KEY` | Google Gemini API key (get from https://aistudio.google.com/app/apikey) |

Run `./scripts/bootstrap.sh` once to create the AWS OIDC trust policy and Terraform state bucket. It outputs the values you need for the secrets above.

#### How to trigger

1. Go to **Actions** → **End-to-End Test** → **Run workflow**.
2. The workflow will:
   - Run Terraform to create an EC2 instance + ECR repository (ephemeral, project name `aicouncil-e2e`).
   - Build and push the Docker image to ECR.
   - Wait for K3s on the EC2 instance to deploy the pod.
   - Curl the health endpoint on the EC2 public IP.
   - **Tear down all infrastructure** at the end regardless of pass/fail.

#### Cost and cleanup

- **Estimated cost:** $0.01–$0.10 per run (EC2 `t3.micro` for ~10–15 minutes).
- **Cleanup:** The workflow runs `terraform destroy` in a `finally` step, so infrastructure is removed automatically.
- **Manual cleanup (if workflow fails mid-run):** Run workflow **04 - Destroy** manually, or run `terraform destroy` locally with `terraform/` pointed at the correct state.

> ⚠️ **Note:** If you interrupt the workflow before the destroy step, AWS resources may remain and incur charges. Always verify with `aws ec2 describe-instances` or the AWS Console.

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Get API Keys

**Option A: Groq (Recommended - Fastest)**
1. Go to https://console.groq.com/keys
2. Sign up / Log in
3. Create API key
4. Copy key

**Option B: Google Gemini (Good Alternative)**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Create API key
4. Copy key

**Option C: Both (Best - Redundancy)**
- Get both keys for fallback

### 3. Set Environment Variables

```bash
# Linux/Mac
export GROQ_API_KEY="gsk_..."
export GOOGLE_API_KEY="AIza..."

# Windows PowerShell
$env:GROQ_API_KEY="gsk_..."
$env:GOOGLE_API_KEY="AIza..."

# Or create .env file
cat > .env << EOF
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
EOF
```

---

## Test 1: CLI Mode

### Basic Test

```bash
python aicouncil.py converge sample_input.md \
  --models critic1,critic2 \
  --max-iterations 3 \
  --output ./test_output
```

**Expected Output:**
```
🤖 Using Groq API (llama-3.1-70b-versatile)

============================================================
STATE 0: Loading Artifact
============================================================
Loaded artifact: sample_input.md (XXX bytes)

============================================================
STATE 1: Iteration 1
============================================================
Proposer: critic1
Critics: critic2

  🤖 Calling Groq (llama-3.1-70b-versatile) for revision...
    🤖 Calling Groq (llama-3.1-70b-versatile) for critique...

[... convergence process ...]

============================================================
Convergence Complete!
============================================================
Final Status: CONVERGED
Reason: All critics approved
Total iterations: 3
Final quality score: 85.0/100
```

### Check Output Files

```bash
ls -la test_output/
# Should see:
# - final_artifact.md
# - telemetry.jsonl
# - diff_history/
```

---

## Test 2: Server Mode

### Start Server

```bash
python aicouncil.py serve --port 8000
```

**Expected Output:**
```
🤖 Using Groq API (llama-3.1-70b-versatile)
🚀 Starting AI Council API server on 0.0.0.0:8000
📊 Health check: http://0.0.0.0:8000/health
📝 API docs: http://0.0.0.0:8000/docs
🤖 LLM Provider: Auto-detected from environment variables

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "aicouncil",
  "version": "1.0.0"
}
```

### Test Converge Endpoint

```bash
curl -X POST http://localhost:8000/converge \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Sample API\n\n## Endpoints\n- GET /users\n- POST /users\n\nNo auth required.",
    "models": ["critic1", "critic2"],
    "max_iterations": 3
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "final_content": "# Sample API\n\n[... improved content ...]",
  "iterations": 3,
  "convergence_reason": "All critics approved",
  "quality_score": 85.0
}
```

### Test API Docs

Open in browser:
```
http://localhost:8000/docs
```

You should see interactive Swagger UI documentation.

---

## Test 3: Docker Build (Optional)

```bash
# Build image
docker build -t aicouncil:test .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY="$GROQ_API_KEY" \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  aicouncil:test

# Test health
curl http://localhost:8000/health
```

---

## Troubleshooting

### Issue: "No API keys found. Using mock provider."

**Solution:** Set environment variables
```bash
export GROQ_API_KEY="your-key"
# or
export GOOGLE_API_KEY="your-key"
```

### Issue: "groq package not installed"

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "FastAPI not installed"

**Solution:** Install FastAPI
```bash
pip install fastapi uvicorn
```

### Issue: Port 8000 already in use

**Solution:** Use different port
```bash
python aicouncil.py serve --port 8080
```

### Issue: LLM API errors

**Solution:** Check API key validity
- Groq: https://console.groq.com/keys
- Gemini: https://aistudio.google.com/app/apikey

---

## Success Criteria

✅ CLI mode runs without errors
✅ Server starts successfully
✅ Health endpoint returns 200 OK
✅ Converge endpoint returns valid JSON
✅ LLM provider is detected (not mock)
✅ Output files are created
✅ Telemetry is logged

---

## Next Steps

Once local testing passes:
1. Commit and push — the cloud-agnostic E2E workflow (`06-e2e-k3d.yml`) runs automatically on your PR.
2. To test on real AWS infrastructure, trigger the **End-to-End Test** workflow manually (see **Option B** above).
3. Follow [QUICKSTART.md](QUICKSTART.md) to deploy to AWS for production use.

