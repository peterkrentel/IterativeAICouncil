#!/bin/bash
# Bootstrap script for AWS infrastructure
# Run this ONCE locally to set up S3 backend and OIDC for GitHub Actions

set -e

echo "🚀 Bootstrapping AWS infrastructure for GitHub Actions..."

# Variables
AWS_REGION="${AWS_REGION:-us-east-1}"
GITHUB_ORG="${GITHUB_ORG:-peterkrentel}"
GITHUB_REPO="${GITHUB_REPO:-IterativeAICouncil}"
TF_STATE_BUCKET="aicouncil-terraform-state-$(date +%s)"

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install it first: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration:"
echo "  AWS Account: ${AWS_ACCOUNT_ID}"
echo "  Region: ${AWS_REGION}"
echo "  GitHub: ${GITHUB_ORG}/${GITHUB_REPO}"
echo "  S3 Bucket: ${TF_STATE_BUCKET}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Create S3 bucket for Terraform state
echo "📦 Creating S3 bucket: ${TF_STATE_BUCKET}"
aws s3 mb s3://${TF_STATE_BUCKET} --region ${AWS_REGION}

echo "🔒 Enabling versioning (for state history and recovery)..."
aws s3api put-bucket-versioning \
  --bucket ${TF_STATE_BUCKET} \
  --versioning-configuration Status=Enabled

echo "🔐 Enabling encryption..."
aws s3api put-bucket-encryption \
  --bucket ${TF_STATE_BUCKET} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

aws s3api put-public-access-block \
  --bucket ${TF_STATE_BUCKET} \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# 2. Create OIDC provider for GitHub Actions
echo "🔐 Setting up OIDC provider for GitHub Actions..."
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  2>/dev/null || echo "OIDC provider may already exist"

# 4. Create IAM role for GitHub Actions
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_ORG}/${GITHUB_REPO}:*"
        }
      }
    }
  ]
}
EOF

echo "👤 Creating IAM role: GitHubActionsRole"
aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  2>/dev/null || echo "Role may already exist"

# 5. Attach policies to role
echo "🔑 Attaching policies to role..."
aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  2>/dev/null || echo "Policy may already be attached"

# 5. Create backend config file
cat > terraform/backend-config.tfvars <<EOF
bucket  = "${TF_STATE_BUCKET}"
key     = "aicouncil/terraform.tfstate"
region  = "${AWS_REGION}"
encrypt = true
EOF

# 6. Output configuration
echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Add these secrets to your GitHub repository:"
echo "   Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo "AWS_REGION=${AWS_REGION}"
echo "AWS_ROLE_ARN=arn:aws:iam::${AWS_ACCOUNT_ID}:role/GitHubActionsRole"
echo "TF_STATE_BUCKET=${TF_STATE_BUCKET}"
echo ""
echo "Also add your LLM API keys:"
echo "GROQ_API_KEY=<get from https://console.groq.com>"
echo "GOOGLE_API_KEY=<get from https://aistudio.google.com/app/apikey>"
echo ""
echo "S3 Bucket Features:"
echo "  ✅ Versioning enabled (state history & recovery)"
echo "  ✅ Encryption enabled (AES256)"
echo "  ✅ Public access blocked"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

rm /tmp/trust-policy.json

