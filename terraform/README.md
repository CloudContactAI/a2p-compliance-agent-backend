# Terraform Deployment for A2P Compliance Agent

## Prerequisites

1. **Install Terraform**: Download from [terraform.io](https://terraform.io)
2. **AWS CLI configured** with your `ccai` profile
3. **GitHub Personal Access Token** with repo permissions
4. **VPC and Subnets** in your AWS account

## Quick Start

1. **Copy configuration file:**
```bash
cp terraform.tfvars.example terraform.tfvars
```

2. **Edit terraform.tfvars** with your values:
   - GitHub username and token
   - VPC ID and subnet IDs from AWS console

3. **Get VPC/Subnet IDs** (if you don't have them):
```bash
# List VPCs
aws ec2 describe-vpcs --profile ccai

# List subnets (use your VPC ID)
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxxxxxx" --profile ccai
```

4. **Deploy:**
```bash
terraform init
terraform plan
terraform apply
```

## What This Creates

- **ECR Repository** for Docker images
- **CodePipeline** for CI/CD from GitHub
- **ECS Fargate** cluster and service
- **Application Load Balancer** for public access
- **IAM roles** with minimal required permissions
- **CloudWatch logs** for monitoring

## After Deployment

1. **Get your app URL:**
```bash
terraform output load_balancer_url
```

2. **Push code to GitHub** to trigger deployment

3. **Monitor deployment** in AWS CodePipeline console

## Cleanup

```bash
terraform destroy
```
