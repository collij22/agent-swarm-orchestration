#!/bin/bash

# QuickShop MVP AWS Deployment Script
# Usage: ./deploy-aws.sh [staging|production]

set -e

# Configuration
ENVIRONMENT=${1:-staging}
PROJECT_NAME="quickshop-mvp"
REGION="us-east-1"
KEY_NAME="quickshop-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install it first."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Run 'aws configure' first."
    fi
    
    log "Prerequisites check passed!"
}

# Create security group
create_security_group() {
    local sg_name="${PROJECT_NAME}-${ENVIRONMENT}-sg"
    
    log "Creating security group: $sg_name"
    
    # Check if security group already exists
    if aws ec2 describe-security-groups --group-names "$sg_name" --region "$REGION" &> /dev/null; then
        warn "Security group $sg_name already exists"
        return
    fi
    
    # Create security group
    local sg_id=$(aws ec2 create-security-group \
        --group-name "$sg_name" \
        --description "Security group for QuickShop MVP $ENVIRONMENT" \
        --region "$REGION" \
        --query 'GroupId' --output text)
    
    # Add inbound rules
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$sg_id" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region "$REGION"
    
    log "Security group created: $sg_id"
}

# Launch EC2 instance
launch_instance() {
    local instance_name="${PROJECT_NAME}-${ENVIRONMENT}"
    local sg_name="${PROJECT_NAME}-${ENVIRONMENT}-sg"
    
    log "Launching EC2 instance: $instance_name"
    
    # Check if instance already exists
    local existing_instance=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=$instance_name" "Name=instance-state-name,Values=running,pending" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].InstanceId' --output text)
    
    if [[ "$existing_instance" != "None" && "$existing_instance" != "" ]]; then
        warn "Instance $instance_name already exists: $existing_instance"
        echo "$existing_instance"
        return
    fi
    
    # User data script for instance initialization
    local user_data=$(cat << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker git

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Create application directory
mkdir -p /opt/quickshop
chown ec2-user:ec2-user /opt/quickshop
EOF
)
    
    # Launch instance
    local instance_id=$(aws ec2 run-instances \
        --image-id ami-0c02fb55956c7d316 \
        --count 1 \
        --instance-type t3.medium \
        --key-name "$KEY_NAME" \
        --security-groups "$sg_name" \
        --user-data "$user_data" \
        --region "$REGION" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$instance_name},{Key=Environment,Value=$ENVIRONMENT},{Key=Project,Value=$PROJECT_NAME}]" \
        --query 'Instances[0].InstanceId' --output text)
    
    log "Instance launched: $instance_id"
    log "Waiting for instance to be running..."
    
    aws ec2 wait instance-running --instance-ids "$instance_id" --region "$REGION"
    
    echo "$instance_id"
}

# Deploy application to instance
deploy_application() {
    local instance_id=$1
    
    log "Getting instance public IP..."
    local public_ip=$(aws ec2 describe-instances \
        --instance-ids "$instance_id" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    
    log "Instance public IP: $public_ip"
    log "Waiting for SSH to be available..."
    
    # Wait for SSH to be available
    local max_attempts=30
    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.ssh/${KEY_NAME}.pem ec2-user@$public_ip "echo 'SSH ready'" &> /dev/null; then
            break
        fi
        log "Attempt $attempt/$max_attempts - SSH not ready yet, waiting..."
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "SSH connection timeout"
    fi
    
    log "Deploying application..."
    
    # Copy application files
    scp -o StrictHostKeyChecking=no -i ~/.ssh/${KEY_NAME}.pem -r . ec2-user@$public_ip:/opt/quickshop/
    
    # Set up environment and start services
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/${KEY_NAME}.pem ec2-user@$public_ip << 'ENDSSH'
        cd /opt/quickshop
        
        # Copy environment file
        if [[ ! -f .env ]]; then
            cp .env.example .env
            echo "Please edit /opt/quickshop/.env with your configuration"
        fi
        
        # Start services
        docker-compose down || true
        docker-compose pull
        docker-compose up -d
        
        # Wait for services to be healthy
        echo "Waiting for services to be healthy..."
        sleep 30
        
        # Check service health
        docker-compose ps
ENDSSH
    
    log "Application deployed successfully!"
    log "Application URL: http://$public_ip"
    log "SSH access: ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@$public_ip"
}

# Setup monitoring
setup_monitoring() {
    local instance_id=$1
    
    log "Setting up CloudWatch monitoring..."
    
    # Create CloudWatch dashboard
    cat > dashboard.json << EOF
{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/EC2", "CPUUtilization", "InstanceId", "$instance_id"],
                    [".", "NetworkIn", ".", "."],
                    [".", "NetworkOut", ".", "."]
                ],
                "period": 300,
                "stat": "Average",
                "region": "$REGION",
                "title": "EC2 Instance Metrics"
            }
        }
    ]
}
EOF
    
    aws cloudwatch put-dashboard \
        --dashboard-name "${PROJECT_NAME}-${ENVIRONMENT}" \
        --dashboard-body file://dashboard.json \
        --region "$REGION"
    
    rm dashboard.json
    
    log "Monitoring dashboard created"
}

# Main deployment flow
main() {
    log "Starting deployment for environment: $ENVIRONMENT"
    
    check_prerequisites
    create_security_group
    local instance_id=$(launch_instance)
    deploy_application "$instance_id"
    setup_monitoring "$instance_id"
    
    log "Deployment completed successfully!"
    log "Next steps:"
    log "1. Update DNS records to point to the instance"
    log "2. Configure SSL certificate"
    log "3. Set up backup procedures"
    log "4. Configure monitoring alerts"
}

# Run main function
main