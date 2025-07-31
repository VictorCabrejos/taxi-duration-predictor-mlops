# 🚀 Deployment Guide - Taxi Duration Predictor

## 📋 **Overview**

Esta guía cubre el **despliegue completo en producción** del sistema de predicción de duración de viajes en taxi, incluyendo **containerización con Docker**, **CI/CD pipeline**, y **deployment en la nube**.

---

## 🐳 **Docker Containerization**

### **📦 Dockerfile - API Server**

```dockerfile
# Dockerfile.api
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY taxi_duration_predictor/ ./taxi_duration_predictor/
COPY 05_fastapi_server.py .
COPY config.py .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "05_fastapi_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **📊 Dockerfile - Dashboard**

```dockerfile
# Dockerfile.dashboard
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY taxi_duration_predictor/ ./taxi_duration_predictor/
COPY 04_streamlit_dashboard.py .
COPY config.py .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start command
CMD ["streamlit", "run", "04_streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **🔧 Docker Compose**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:13
    container_name: taxi-predictor-db
    environment:
      POSTGRES_DB: taxi_duration
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - taxi-network

  # MLflow Tracking Server
  mlflow:
    image: python:3.9-slim
    container_name: taxi-predictor-mlflow
    working_dir: /app
    command: >
      bash -c "
        pip install mlflow[extras] psycopg2-binary &&
        mlflow server
          --backend-store-uri postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/mlflow
          --default-artifact-root ./mlruns
          --host 0.0.0.0
          --port 5000
      "
    volumes:
      - mlflow_data:/app/mlruns
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - taxi-network

  # FastAPI Server
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: taxi-predictor-api
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/taxi_duration
      MLFLOW_TRACKING_URI: http://mlflow:5000
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      mlflow:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - taxi-network
    restart: unless-stopped

  # Streamlit Dashboard
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    container_name: taxi-predictor-dashboard
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/taxi_duration
      MLFLOW_TRACKING_URI: http://mlflow:5000
      API_BASE_URL: http://api:8000
    ports:
      - "8501:8501"
    depends_on:
      api:
        condition: service_healthy
    networks:
      - taxi-network
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: taxi-predictor-nginx
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
      - dashboard
    networks:
      - taxi-network
    restart: unless-stopped

volumes:
  postgres_data:
  mlflow_data:

networks:
  taxi-network:
    driver: bridge
```

### **🌐 Nginx Configuration**

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    upstream dashboard {
        server dashboard:8501;
    }

    # API Server
    server {
        listen 80;
        server_name api.taxi-predictor.local;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://api/health;
            access_log off;
        }
    }

    # Dashboard
    server {
        listen 80;
        server_name dashboard.taxi-predictor.local;

        location / {
            proxy_pass http://dashboard;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

---

## 🔄 **CI/CD Pipeline**

### **🚀 GitHub Actions Workflow**

```yaml
# .github/workflows/mlops-pipeline.yml
name: MLOps CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Data Quality & Testing
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8

    - name: Lint with flake8
      run: |
        flake8 taxi_duration_predictor/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 taxi_duration_predictor/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

    - name: Test with pytest
      run: |
        pytest test/ -v --cov=taxi_duration_predictor --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  # Security Scanning
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # Model Training & Validation
  model-training:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Train models
      run: |
        python 03_mlflow_training.py
      env:
        MLFLOW_TRACKING_URI: sqlite:///mlflow.db

    - name: Validate model performance
      run: |
        python scripts/validate_model.py

    - name: Archive MLflow artifacts
      uses: actions/upload-artifact@v3
      with:
        name: mlflow-artifacts
        path: mlruns/

  # Build Docker Images
  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Extract metadata (tags, labels)
      id: meta-api
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-api
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha

    - name: Build and push API Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: Dockerfile.api
        push: true
        tags: ${{ steps.meta-api.outputs.tags }}
        labels: ${{ steps.meta-api.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Extract metadata for Dashboard
      id: meta-dashboard
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-dashboard

    - name: Build and push Dashboard Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: Dockerfile.dashboard
        push: true
        tags: ${{ steps.meta-dashboard.outputs.tags }}
        labels: ${{ steps.meta-dashboard.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # Deploy to Staging
  deploy-staging:
    needs: [build, model-training]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # Add staging deployment logic here

    - name: Run integration tests
      run: |
        python scripts/integration_tests.py
      env:
        API_BASE_URL: https://staging-api.taxi-predictor.com

  # Deploy to Production
  deploy-production:
    needs: [build, model-training]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to production
      run: |
        echo "Deploying to production environment..."
        # Add production deployment logic here

    - name: Run smoke tests
      run: |
        python scripts/smoke_tests.py
      env:
        API_BASE_URL: https://api.taxi-predictor.com

    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## ☁️ **Cloud Deployment**

### **🚀 AWS Deployment with ECS**

```yaml
# aws/ecs-task-definition.json
{
  "family": "taxi-predictor",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ghcr.io/your-repo/taxi-predictor-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/taxi_duration"
        },
        {
          "name": "MLFLOW_TRACKING_URI",
          "value": "s3://mlflow-bucket/mlruns"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/taxi-predictor",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    },
    {
      "name": "dashboard",
      "image": "ghcr.io/your-repo/taxi-predictor-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_BASE_URL",
          "value": "http://api.taxi-predictor.com"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/taxi-predictor",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "dashboard"
        }
      }
    }
  ]
}
```

### **🔧 Terraform Infrastructure**

```hcl
# aws/main.tf
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "taxi-predictor-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false

  tags = {
    Environment = var.environment
    Project     = "taxi-predictor"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "taxi-predictor-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = module.vpc.public_subnets

  enable_deletion_protection = false

  tags = {
    Environment = var.environment
    Project     = "taxi-predictor"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "taxi-predictor"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
    Project     = "taxi-predictor"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier     = "taxi-predictor-db"
  engine         = "postgres"
  engine_version = "13.7"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true

  db_name  = "taxi_duration"
  username = "postgres"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "07:00-09:00"
  maintenance_window     = "Sun:06:00-Sun:07:00"

  skip_final_snapshot = true

  tags = {
    Environment = var.environment
    Project     = "taxi-predictor"
  }
}

# S3 Bucket for MLflow artifacts
resource "aws_s3_bucket" "mlflow" {
  bucket = "taxi-predictor-mlflow-${random_string.bucket_suffix.result}"

  tags = {
    Environment = var.environment
    Project     = "taxi-predictor"
  }
}

resource "aws_s3_bucket_versioning" "mlflow" {
  bucket = aws_s3_bucket.mlflow.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow" {
  bucket = aws_s3_bucket.mlflow.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

---

## 📊 **Monitoring & Observability**

### **📈 Prometheus Monitoring**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'taxi-predictor-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### **🚨 Alert Rules**

```yaml
# monitoring/alert_rules.yml
groups:
  - name: taxi-predictor-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: ModelDrift
        expr: model_rmse > 8.0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Model performance degradation detected"
          description: "Model RMSE is {{ $value }}, exceeding threshold of 8.0"

      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "PostgreSQL database is not responding"
```

### **📊 Grafana Dashboard**

```json
{
  "dashboard": {
    "title": "Taxi Duration Predictor - MLOps Dashboard",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Model Performance",
        "type": "stat",
        "targets": [
          {
            "expr": "model_rmse",
            "legendFormat": "RMSE"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total[5m]) * 100",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "container_memory_usage_bytes / container_spec_memory_limit_bytes * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      }
    ]
  }
}
```

---

## 🔒 **Security & Best Practices**

### **🔐 Security Configuration**

```yaml
# Security hardening in docker-compose.yml
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### **🛡️ Network Security**

```yaml
# Security groups in docker-compose
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  backend:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/16
```

### **📋 Environment Configuration**

```bash
# .env.production
# Database
POSTGRES_PASSWORD=<secure-password>
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/taxi_duration

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_S3_ENDPOINT_URL=https://s3.amazonaws.com
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>

# API Configuration
API_WORKERS=4
API_MAX_REQUESTS=1000
API_TIMEOUT=30

# Security
SECRET_KEY=<secure-secret-key>
ALLOWED_HOSTS=api.taxi-predictor.com,dashboard.taxi-predictor.com

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
LOG_LEVEL=INFO
```

---

## 🚀 **Deployment Commands**

### **📦 Local Development**

```bash
# Clone repository
git clone https://github.com/your-repo/taxi-duration-predictor.git
cd taxi-duration-predictor

# Set up environment
cp .env.example .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env

# Build and start services
docker-compose up -d

# Check service health
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8501

# View logs
docker-compose logs -f api
docker-compose logs -f dashboard
```

### **🌐 Production Deployment**

```bash
# Production deployment
cp .env.production .env

# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with zero downtime
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Run health checks
./scripts/health-check.sh

# Monitor deployment
docker-compose -f docker-compose.prod.yml logs -f
```

### **🔄 CI/CD Deployment**

```bash
# Trigger deployment via GitHub Actions
git tag v1.0.0
git push origin v1.0.0

# Monitor deployment
gh run list --workflow=mlops-pipeline.yml
gh run view <run-id> --log
```

---

## 📊 **Performance Optimization**

### **⚡ API Optimization**

```python
# Performance configurations
UVICORN_WORKERS = 4
UVICORN_WORKER_CONNECTIONS = 1000
UVICORN_BACKLOG = 2048

# Caching strategy
REDIS_CACHE_TTL = 300  # 5 minutes
MODEL_CACHE_SIZE = 100  # Cache 100 models
```

### **🗄️ Database Optimization**

```sql
-- Database performance tuning
-- Connection pooling
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Indexing strategy
CREATE INDEX CONCURRENTLY idx_taxi_trips_pickup_datetime
ON taxi_trips(pickup_datetime);

CREATE INDEX CONCURRENTLY idx_taxi_trips_distance
ON taxi_trips(trip_distance);
```

### **📈 Monitoring Metrics**

```python
# Key performance indicators
performance_targets = {
    'api_response_time_p95': '< 200ms',
    'api_throughput': '> 1000 req/min',
    'model_inference_time': '< 50ms',
    'database_query_time': '< 100ms',
    'system_uptime': '> 99.9%',
    'error_rate': '< 0.1%'
}
```

---

## 🎯 **Production Checklist**

### **✅ Pre-Deployment**
- [ ] All tests passing (unit, integration, e2e)
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Backup strategy verified
- [ ] Rollback plan prepared

### **✅ Deployment**
- [ ] Blue-green deployment executed
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Log aggregation working
- [ ] SSL certificates valid
- [ ] CDN configured

### **✅ Post-Deployment**
- [ ] Smoke tests passed
- [ ] Performance metrics normal
- [ ] Error rates within threshold
- [ ] User acceptance testing completed
- [ ] Stakeholders notified
- [ ] Documentation published

---

**🚀 Complete Production Deployment Guide**
**📚 Machine Learning y Big Data - UNMSM 2025**
**🎯 Docker + CI/CD + Cloud Deployment Ready**
