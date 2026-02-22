# Testing Guide

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
1. Commit changes
2. Push to GitHub
3. Follow QUICKSTART.md to deploy to AWS
4. Test production deployment

