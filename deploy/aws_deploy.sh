#!/bin/bash
# deploy/aws_deploy.sh — One-time EC2 setup script
# Run this ONCE on a fresh Ubuntu 22.04 EC2 instance (t3.medium recommended)
# Then CI/CD handles all future deploys automatically

set -e

echo "=== Enterprise Knowledge Agent — EC2 Setup ==="

# 1. System deps
sudo apt-get update -y
sudo apt-get install -y docker.io docker-compose-plugin awscli curl git

# 2. Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# 3. Install CloudWatch agent
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# 4. CloudWatch config — streams app logs to /aws/eka/backend
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null <<'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/eka/app.log",
            "log_group_name": "/aws/eka/backend",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOF
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# 5. Clone repo
git clone https://github.com/YOUR_USERNAME/enterprise-knowledge-agent.git \
  /home/ubuntu/enterprise-knowledge-agent

# 6. Create .env from AWS Secrets Manager (replace SECRET_NAME with yours)
# aws secretsmanager get-secret-value --secret-id eka/prod --query SecretString \
#   --output text > /home/ubuntu/enterprise-knowledge-agent/.env

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Add your .env file to /home/ubuntu/enterprise-knowledge-agent/"
echo "  2. cd /home/ubuntu/enterprise-knowledge-agent"
echo "  3. docker compose -f deploy/docker-compose.yml up -d"
echo "  4. Visit http://$(curl -s ifconfig.me):8000/health"
