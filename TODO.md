# AI Council - TODO

## ✅ COMPLETED

### Infrastructure & DevOps
- [x] Terraform infrastructure (VPC, EC2, K3s, ECR)
- [x] GitHub Actions workflows (plan, apply, deploy, destroy)
- [x] Bootstrap script for AWS setup
- [x] Kubernetes manifests (deployment, service, ingress)
- [x] Dockerfile with security best practices
- [x] Complete documentation (DEPLOYMENT.md, QUICKSTART.md)

### Files Created
- [x] `scripts/bootstrap.sh` - One-time AWS setup
- [x] `terraform/*.tf` - Complete infrastructure as code
- [x] `.github/workflows/*.yml` - Full CI/CD pipeline
- [x] `k8s/*.yaml` - Kubernetes manifests
- [x] `Dockerfile` - Production container image
- [x] `.env.example` - Environment variable template
- [x] Updated `.gitignore` - Proper exclusions
- [x] Updated `requirements.txt` - Added Groq, Gemini, FastAPI

---

## 🚧 TODO (To Make It Work)

### 1. Update aicouncil.py with LLM Providers

**Current state:** Has placeholder functions
**Needed:** Real LLM API integration

```python
# Need to implement:
class LLMProvider:
    def chat(self, messages): pass

class GroqProvider(LLMProvider):
    def chat(self, messages):
        # Call Groq API
        pass

class GeminiProvider(LLMProvider):
    def chat(self, messages):
        # Call Gemini API
        pass

# Replace placeholder functions:
def _call_proposer_llm(content, critiques):
    # Currently returns placeholder
    # Need to call actual LLM
    pass

def _call_critic_llm(content, role):
    # Currently returns placeholder
    # Need to call actual LLM
    pass
```

### 2. Add FastAPI Server Mode

**Current state:** CLI only
**Needed:** HTTP API server for K8s deployment

```python
# Add to aicouncil.py:
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/converge")
def converge_api(content: str):
    # Run convergence engine
    # Return results
    pass

# Add CLI command:
def serve(host="0.0.0.0", port=8000):
    uvicorn.run(app, host=host, port=port)
```

### 3. Test Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"

# Test CLI
python aicouncil.py converge sample_input.md

# Test server
python aicouncil.py serve
curl http://localhost:8000/health
```

### 4. Deploy to AWS

Follow [QUICKSTART.md](QUICKSTART.md):
1. Run bootstrap script
2. Add GitHub secrets
3. Run Terraform Apply workflow
4. Run Build and Deploy workflow

---

## 📋 Optional Enhancements

### Monitoring & Observability
- [ ] Add Prometheus metrics
- [ ] Set up CloudWatch dashboards
- [ ] Add structured logging
- [ ] Set up alerts (Slack/email)

### Security Hardening
- [ ] Add SSL/TLS (Let's Encrypt)
- [ ] Restrict SSH to specific IPs
- [ ] Add WAF (Web Application Firewall)
- [ ] Implement rate limiting
- [ ] Add API authentication

### Features
- [ ] Add caching layer (Redis)
- [ ] Support multiple LLM providers simultaneously
- [ ] Add web UI for convergence visualization
- [ ] Store convergence history in database
- [ ] Add user authentication

### Cost Optimization
- [ ] Use spot instances (70% savings)
- [ ] Auto-scaling based on load
- [ ] Schedule instance stop/start
- [ ] Optimize Docker image size

### Testing
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add E2E tests in CI/CD
- [ ] Load testing

---

## 🎯 Priority Order

### Must Have (To Deploy)
1. **LLM Provider Integration** - Without this, app doesn't work
2. **FastAPI Server** - Needed for K8s deployment
3. **Local Testing** - Verify it works before deploying

### Should Have (For Production)
4. **SSL/TLS** - HTTPS for security
5. **Monitoring** - Know when things break
6. **Tests** - Prevent regressions

### Nice to Have (Future)
7. **Web UI** - Better UX
8. **Database** - Persistence
9. **Authentication** - Multi-user support

---

## 🚀 Next Immediate Steps

**To make this deployable TODAY:**

1. **Update aicouncil.py** (30 min)
   - Add Groq provider
   - Add Gemini provider
   - Add FastAPI server mode

2. **Test locally** (15 min)
   - Test CLI with real LLMs
   - Test server mode
   - Verify health endpoint

3. **Deploy** (15 min)
   - Run bootstrap script
   - Add GitHub secrets
   - Run workflows

**Total time to working deployment: ~1 hour**

---

## 📝 Notes

- Infrastructure is 100% ready
- CI/CD pipeline is 100% ready
- Only missing: LLM integration in aicouncil.py
- Once that's done, everything else is automated

**The hard part is done. Now just wire up the LLMs!**

