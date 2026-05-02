# 🚀 Phantom Deployment Guide

> Comprehensive guide for deploying Phantom in production environments.

**Version**: 0.0.1 (Pre-Alpha)  
**Last Updated**: May 2, 2026

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Systemd Service](#systemd-service)
- [Nix Environment](#nix-environment)
- [Cloud Platforms](#cloud-platforms)
- [Database & Storage](#database--storage)
- [Monitoring & Observability](#monitoring--observability)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)

---

## 🔥 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/kernelcore/phantom.git
cd phantom

# Install Nix (if not already installed)
curl -L https://nixos.org/nix/install | sh
. /home/$USER/.nix-profile/etc/profile.d/nix.sh

# Enter development environment
nix develop --extra-experimental-features nix-command --extra-experimental-features flakes

# Run API server
just run-api

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Quick Status Check

```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# System metrics
curl http://localhost:8000/api/system/metrics
```

---

## 🐳 Docker Deployment

### Using Provided Dockerfile

```bash
# Build image
docker build -t phantom:latest .

# Run container
docker run -d \
  --name phantom-api \
  -p 8000:8000 \
  -e PORT=8000 \
  -v /path/to/data:/app/data \
  phantom:latest

# Check logs
docker logs -f phantom-api

# Stop container
docker stop phantom-api
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  phantom-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - PYTHON_LOG_LEVEL=INFO
      - LLAMACPP_BASE_URL=http://llama-cpp:8081
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    networks:
      - phantom
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  llama-cpp:
    image: ghcr.io/ggerganov/llama.cpp:server
    ports:
      - "8081:8081"
    environment:
      - LLAMA_API_KEY=${LLAMA_API_KEY:-}
    volumes:
      - ./models:/models
    command: |
      --model /models/model.gguf
      --alias phi
      --host 0.0.0.0
      --port 8081
      --parallel 4
    networks:
      - phantom
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  phantom:
    driver: bridge
```

Deploy with Docker Compose:

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f phantom-api

# Stop services
docker-compose down
```

### Multi-Stage Build for Optimization

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN pip install --user --no-cache-dir poetry && \
    poetry install --no-dev

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/phantom ./phantom

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000

CMD ["phantom", "api", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔧 Systemd Service

### Create Service File

Create `/etc/systemd/system/phantom-api.service`:

```ini
[Unit]
Description=Phantom API Server
After=network.target
Wants=llama-cpp.service

[Service]
Type=simple
User=phantom
Group=phantom
WorkingDirectory=/opt/phantom

# Environment
Environment="PATH=/home/phantom/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHON_LOG_LEVEL=INFO"
Environment="PORT=8000"
EnvironmentFile=/etc/phantom/api.env

# Execute
ExecStart=/home/phantom/.nix-profile/bin/python -m phantom.api.app

# Restart policy
Restart=on-failure
RestartSec=10s
StartLimitInterval=60s
StartLimitBurst=3

# Resource limits
LimitNOFILE=65535
LimitNPROC=512
MemoryMax=2G
CPUQuota=200%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/opt/phantom/data /opt/phantom/models

[Install]
WantedBy=multi-user.target
```

### Setup & Management

```bash
# Create user
sudo useradd -r -s /bin/nologin phantom

# Setup directories
sudo mkdir -p /opt/phantom/{data,models,logs}
sudo chown -R phantom:phantom /opt/phantom
sudo chmod 755 /opt/phantom

# Create environment file
sudo tee /etc/phantom/api.env << EOF
PORT=8000
PYTHON_LOG_LEVEL=INFO
LLAMACPP_BASE_URL=http://localhost:8081
EOF
sudo chmod 600 /etc/phantom/api.env

# Install service
sudo cp phantom-api.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start service
sudo systemctl start phantom-api

# Check status
sudo systemctl status phantom-api

# View logs
sudo journalctl -u phantom-api -f

# Enable auto-start
sudo systemctl enable phantom-api

# Stop service
sudo systemctl stop phantom-api
```

### Logging with systemd

```bash
# View recent logs
sudo journalctl -u phantom-api -n 50

# Follow logs
sudo journalctl -u phantom-api -f

# Filter by priority
sudo journalctl -u phantom-api -p warning

# Time range
sudo journalctl -u phantom-api --since "2 hours ago"

# JSON output
sudo journalctl -u phantom-api -o json | jq .
```

---

## 📦 Nix Environment

### Production Nix Deployment

Create `nix-shell.nix` for reproducible environment:

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.pip
    python311Packages.poetry
    python311Packages.uvicorn
    python311Packages.fastapi
    python311Packages.pydantic
    gcc
    libffi
    openssl
    git
  ];

  shellHook = ''
    export PYTHONPATH=$PWD/src:$PYTHONPATH
    export PYTHONUNBUFFERED=1
  '';
}
```

Use flake for reproducible build:

```bash
# Enter environment
nix develop

# Run server
python -m phantom.api.app
```

---

## ☁️ Cloud Platforms

### AWS Deployment

```bash
# 1. Create EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name phantom-key \
  --security-groups phantom-sg

# 2. Connect and setup
ssh -i phantom-key.pem ec2-user@<instance-ip>

# 3. Install Nix and deploy
curl -L https://nixos.org/nix/install | sh
git clone https://github.com/kernelcore/phantom.git
cd phantom
nix develop --command phantom api serve --host 0.0.0.0

# 4. Setup load balancer
aws elbv2 create-load-balancer \
  --name phantom-lb \
  --subnets subnet-12345678

# 5. Register target
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-1234567890abcdef0
```

### Heroku Deployment

```bash
# 1. Create app
heroku create phantom-api

# 2. Add buildpack
heroku buildpacks:add https://github.com/nixos/heroku-nixpacks

# 3. Deploy
git push heroku main

# 4. View logs
heroku logs -t

# 5. Scale
heroku ps:scale web=2
```

### Google Cloud Run

```bash
# 1. Build and push image
docker build -t gcr.io/PROJECT_ID/phantom:latest .
docker push gcr.io/PROJECT_ID/phantom:latest

# 2. Deploy
gcloud run deploy phantom \
  --image gcr.io/PROJECT_ID/phantom:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="PORT=8080"

# 3. Check status
gcloud run services list
```

---

## 💾 Database & Storage

### Local SQLite (Default)

```bash
# Already configured in pyproject.toml
# Data stored in ./data/phantom.db
```

### PostgreSQL

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: phantom-secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

  phantom-api:
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/phantom
```

### Vector Store Persistence

```bash
# FAISS index saved to disk
./data/index.faiss

# Backup index
cp data/index.faiss data/index.faiss.backup

# Restore from backup
cp data/index.faiss.backup data/index.faiss
```

---

## 📊 Monitoring & Observability

### Prometheus Integration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'phantom-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

Start Prometheus:

```bash
docker run -d \
  -p 9090:9090 \
  -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### Grafana Dashboard

Create dashboard to visualize:
- Request count over time
- Request latency (p50, p95, p99)
- Error rates
- System resource usage

### Health Check Endpoints

```bash
# Liveness
curl http://localhost:8000/health

# Readiness
curl http://localhost:8000/ready

# System metrics
curl http://localhost:8000/api/system/metrics
```

### Structured Logging

Configuration in environment:

```bash
export PYTHON_LOG_LEVEL=INFO
export LOG_FORMAT=json  # or 'text'
```

View logs:

```bash
# Real-time
tail -f logs/phantom.log

# JSON parsing
cat logs/phantom.log | jq '.level, .message'
```

---

## 🔐 Security Considerations

### API Security

1. **HTTPS Only**
   ```bash
   # Generate self-signed certificate
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
   
   # Run with SSL
   uvicorn phantom.api.app:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```

2. **Rate Limiting**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

3. **Authentication**
   ```bash
   # Setup API key authentication
   export API_KEY=$(openssl rand -hex 32)
   ```

4. **CORS Configuration**
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### File Security

```bash
# Restrict data directory
sudo chmod 700 /opt/phantom/data
sudo chown phantom:phantom /opt/phantom/data

# Scan for secrets
git secrets install
git secrets scan
```

### Network Security

```bash
# Firewall rules
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 9090/tcp  # Prometheus (internal only)
sudo ufw enable
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
PHANTOM_API_PORT=8001 phantom api serve
```

#### 2. Out of Memory

```bash
# Check memory
free -h

# Set memory limits
docker run -m 2g phantom:latest

# Increase swap (temporary)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. LLM Connection Failed

```bash
# Check llama.cpp health
curl http://localhost:8081/health

# Restart llama.cpp
docker restart llama-cpp

# Use different URL
export LLAMACPP_BASE_URL=http://localhost:8081
```

#### 4. FAISS Index Corrupted

```bash
# Rebuild index
python -c "
from phantom.rag.vectors import FAISSVectorStore
store = FAISSVectorStore(embedding_dim=384)
store.save('data/index.faiss')
"
```

### Debug Mode

```bash
# Enable verbose logging
export PYTHON_LOG_LEVEL=DEBUG
phantom api serve

# Check logs
tail -f logs/phantom.log | grep -E "ERROR|WARNING"
```

---

## ⚡ Performance Tuning

### API Server Optimization

```bash
# Increase workers
phantom api serve \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop

# Increase timeout
export TIMEOUT=120
```

### VRAM Management

```bash
# Monitor VRAM
watch -n 1 nvidia-smi

# Set memory limit for llama.cpp
docker run -e "LLAMA_VRAM=4000" llama-cpp:latest

# Use CPU-only mode
export LLAMA_BACKEND=CPU
```

### Vector Store Optimization

```python
# Use GPU acceleration (if available)
from phantom.rag.vectors import FAISSVectorStore
store = FAISSVectorStore(
    embedding_dim=384,
    gpu_enabled=True  # Requires GPU
)

# Or batch operations
embeddings = store.encode_batch(texts, batch_size=128)
```

### Database Optimization

```sql
-- PostgreSQL indexing
CREATE INDEX idx_vectors_content ON vectors USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_documents_source ON documents(source);
```

---

## 📈 Scaling Strategies

### Horizontal Scaling

```yaml
# docker-compose with multiple replicas
services:
  phantom-api:
    deploy:
      replicas: 3
```

### Load Balancing

```nginx
# nginx.conf
upstream phantom_backend {
    server phantom-1:8000;
    server phantom-2:8000;
    server phantom-3:8000;
}

server {
    listen 80;
    server_name api.phantom.example.com;

    location / {
        proxy_pass http://phantom_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Caching Layer

```bash
# Redis cache
docker run -d -p 6379:6379 redis:latest

# Configure phantom to use Redis
export REDIS_URL=redis://localhost:6379
```

---

## 📞 Support

- **Issues**: https://github.com/kernelcore/phantom/issues
- **Discussions**: https://github.com/kernelcore/phantom/discussions
- **Email**: support@phantom.example.com

---

**Last Updated**: 2026-05-02  
**Version**: 1.0.0

