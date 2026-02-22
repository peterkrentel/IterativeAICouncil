# AI Council - Quick Start

Get your AI Council deployed to AWS in 15 minutes.

## TL;DR

```bash
# 1. Bootstrap (run once locally)
./scripts/bootstrap.sh

# 2. Add secrets to GitHub (from bootstrap output)
# Go to: Settings → Secrets → Actions

# 3. Deploy infrastructure (GitHub Actions)
# Actions → "Terraform Apply" → Type "apply" → Run

# 4. Add EC2_SSH_PRIVATE_KEY secret (from Terraform outputs)

# 5. Deploy app (GitHub Actions)
# Actions → "Build and Deploy" → Run

# 6. Test
curl http://YOUR_EC2_IP/health
```

## Prerequisites

- AWS Account
- GitHub Account
- AWS CLI installed
- 15 minutes

## Step-by-Step

### 1. Get API Keys (5 min)

**Groq (Free):**
1. Go to https://console.groq.com
2. Sign up
3. Create API key
4. Copy it

**Google Gemini (Free):**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google
3. Create API key
4. Copy it

### 2. Bootstrap AWS (2 min)

```bash
# Configure AWS CLI
aws configure

# Run bootstrap
cd /path/to/IterativeAICouncil
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

**Save the output!** You'll need it for GitHub secrets.

### 3. Add GitHub Secrets (3 min)

Go to: `https://github.com/YOUR_USERNAME/IterativeAICouncil/settings/secrets/actions`

Add these secrets (from bootstrap output):
- `AWS_REGION`
- `AWS_ROLE_ARN`
- `TF_STATE_BUCKET`
- `TF_LOCK_TABLE`
- `GROQ_API_KEY`
- `GOOGLE_API_KEY`

### 4. Create Production Environment (1 min)

Go to: `https://github.com/YOUR_USERNAME/IterativeAICouncil/settings/environments`

1. Click "New environment"
2. Name: `production`
3. Add yourself as required reviewer
4. Save

### 5. Deploy Infrastructure (5 min)

1. Go to Actions → "Terraform Apply"
2. Click "Run workflow"
3. Type `apply`
4. Click "Run workflow"
5. Approve when prompted
6. Wait ~5 minutes

**After completion:**
1. Download `terraform-outputs` artifact
2. Extract `ssh_private_key` from JSON
3. Add as GitHub secret: `EC2_SSH_PRIVATE_KEY`

### 6. Deploy Application (2 min)

1. Go to Actions → "Build and Deploy"
2. Click "Run workflow"
3. Wait ~2 minutes

### 7. Test It! (1 min)

```bash
# Get your EC2 IP from Terraform outputs
curl http://YOUR_EC2_IP/health

# Should return: {"status": "healthy"}
```

## What You Just Built

- ✅ AWS EC2 instance with K3s (Kubernetes)
- ✅ AI Council API running in container
- ✅ Connected to free LLM APIs (Groq + Gemini)
- ✅ Full CI/CD pipeline with GitHub Actions
- ✅ Infrastructure as Code (Terraform)
- ✅ Production-ready deployment

## Cost

**Year 1:** $0-3/month (AWS free tier)
**Year 2+:** ~$21/month (reserved instance)
**LLMs:** $0/month (free tier)

## Next Steps

- Read [DEPLOYMENT.md](DEPLOYMENT.md) for full details
- Read [README.md](README.md) for API usage
- Try the API: `curl http://YOUR_EC2_IP/docs`

## Troubleshooting

**Workflow fails?**
- Check GitHub secrets are correct
- Verify AWS CLI is configured: `aws sts get-caller-identity`

**Can't connect to EC2?**
- Wait 5 minutes for K3s to install
- Check security group allows your IP

**Application not responding?**
- Check logs: `kubectl logs -f deployment/aicouncil`
- Verify API keys are set correctly

## Destroy Everything

When you're done:

1. Go to Actions → "Destroy Infrastructure"
2. Type `destroy`
3. Run workflow

**Total cleanup time:** 2 minutes

---

**Questions?** See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guide.
