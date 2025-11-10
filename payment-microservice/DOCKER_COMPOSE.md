# Docker Compose Guide

Complete guide for running the Payment Microservice with Docker Compose.

## 📋 Services

### 1. `payment-service` (Main Service)
- **Image**: `payments-service:latest`
- **Container**: `payment-service`
- **Port**: `7000:7000`
- **Restart**: `unless-stopped`
- **Health Check**: Python socket check every 30s

### 2. `test-client` (Optional Test Service)
- **Image**: `payments-service-test:latest`
- **Container**: `payment-test-client`
- **Profile**: `test` (only runs when explicitly requested)
- **Depends On**: `payment-service` (waits for health check)
- **Command**: Runs example client against the server

## 🚀 Quick Start

### Start the Payment Service

```bash
# Start in background
docker-compose up -d

# Start with logs (foreground)
docker-compose up

# View logs
docker-compose logs -f payment-service

# Check status
docker-compose ps
```

### Stop the Service

```bash
# Stop containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers, and clean up volumes
docker-compose down -v
```

## 🧪 Running Tests

### Option 1: Run Test Profile

```bash
# Start server and run test client (foreground)
docker-compose --profile test up

# Run in background
docker-compose --profile test up -d

# View test client logs
docker-compose logs test-client
```

### Option 2: Run Test Client Manually

```bash
# Make sure server is running first
docker-compose up -d

# Run test client (one-shot)
docker-compose run --rm test-client

# Run with custom command
docker-compose run --rm test-client python examples/client_example.py
```

### Option 3: Interactive Testing

```bash
# Start server
docker-compose up -d

# Open a shell in test client
docker-compose run --rm test-client bash

# Inside the container, run tests
python examples/client_example.py
python -m pytest tests/
```

## ⚙️ Configuration

### Using Environment Variables

**Method 1: Create a `.env` file**

```bash
# Create .env file in project root
cat > .env << 'EOF'
PORT=8080
MAX_WORKERS=20
PYTHONUNBUFFERED=1
EOF

# Start with custom config
docker-compose up -d
```

**Method 2: Inline environment variables**

```bash
PORT=9000 MAX_WORKERS=15 docker-compose up -d
```

**Method 3: Custom compose file**

```bash
# Create docker-compose.override.yml
cat > docker-compose.override.yml << 'EOF'
version: '3.8'
services:
  payment-service:
    environment:
      - PORT=8080
      - MAX_WORKERS=25
    ports:
      - "8080:8080"
EOF

# Automatically merges with docker-compose.yml
docker-compose up -d
```

### Available Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `7000` | gRPC server port |
| `MAX_WORKERS` | `10` | Thread pool size |
| `PYTHONUNBUFFERED` | `1` | Force stdout/stderr unbuffered |
| `GRPC_SERVER` | `payment-service:7000` | Server address for test client |

## 🔍 Monitoring & Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f payment-service

# Last 100 lines
docker-compose logs --tail=100 payment-service

# Since timestamp
docker-compose logs --since="2024-01-01T00:00:00" payment-service
```

### Check Health Status

```bash
# Via docker-compose
docker-compose ps

# Via docker inspect
docker inspect --format='{{.State.Health.Status}}' payment-service

# Detailed health info
docker inspect payment-service | grep -A 10 "Health"
```

### Execute Commands in Running Container

```bash
# Open shell
docker-compose exec payment-service bash

# Run Python commands
docker-compose exec payment-service python -c "print('Hello from container')"

# Check Python packages
docker-compose exec payment-service pip list

# View process list
docker-compose exec payment-service ps aux
```

### Network Debugging

```bash
# Test connectivity from test client to server
docker-compose run --rm test-client ping payment-service

# Check if port is listening
docker-compose exec payment-service netstat -tuln | grep 7000

# DNS resolution
docker-compose run --rm test-client nslookup payment-service
```

## 🔧 Development Workflow

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Force rebuild (no cache)
docker-compose build --no-cache
docker-compose up -d
```

### Watch Logs During Development

```bash
# Terminal 1: Run server with live logs
docker-compose up

# Terminal 2: Run test client
docker-compose run --rm test-client
```

### Testing Different Configurations

```bash
# Test with more workers
MAX_WORKERS=50 docker-compose up -d
docker-compose logs -f

# Test with different port
PORT=8080 docker-compose up -d
# Update port mapping in docker-compose.yml or use override
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
docker-compose logs payment-service

# Verify port is not in use
lsof -i :7000

# Remove and recreate containers
docker-compose down
docker-compose up -d
```

### Health Check Failing

```bash
# Check health check logs
docker inspect payment-service | grep -A 20 "Health"

# Manually test health check
docker-compose exec payment-service python -c \
  "import socket; s = socket.socket(); s.connect(('localhost', 7000)); s.close(); print('OK')"

# Check if server is listening
docker-compose exec payment-service netstat -tuln | grep 7000
```

### Test Client Can't Connect

```bash
# Verify network connectivity
docker-compose run --rm test-client ping payment-service

# Check server logs
docker-compose logs payment-service

# Verify server is healthy
docker-compose ps

# Try connecting from host
python examples/client_example.py localhost 7000
```

### Container Keeps Restarting

```bash
# Check restart count
docker-compose ps

# View logs for crash reason
docker-compose logs --tail=50 payment-service

# Disable restart to debug
docker-compose up --no-start payment-service
docker-compose start payment-service
docker-compose logs -f payment-service
```

## 📊 Performance Testing

### Run Load Tests

```bash
# Start server
docker-compose up -d

# Run multiple test clients concurrently
for i in {1..10}; do
  docker-compose run --rm -d test-client &
done

# Monitor server performance
docker stats payment-service
```

## 🧹 Cleanup

### Remove Everything

```bash
# Stop and remove containers
docker-compose down

# Remove containers, networks, and volumes
docker-compose down -v

# Remove containers, networks, volumes, and images
docker-compose down -v --rmi all

# Remove orphan containers
docker-compose down --remove-orphans
```

### Clean Up Docker System

```bash
# Remove unused containers, networks, images
docker system prune

# Remove everything including volumes
docker system prune -a --volumes

# See disk usage
docker system df
```

## 📚 Advanced Usage

### Using Multiple Compose Files

```bash
# Base + override
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling Services

```bash
# Note: Not recommended for gRPC with port mapping
# Better to use Kubernetes for orchestration

# Scale to multiple instances (requires removing port mapping)
docker-compose up -d --scale payment-service=3
```

## 🔒 Security Considerations

1. **Non-root user**: Container runs as `appuser` (UID 1001)
2. **Read-only filesystem**: No write permissions needed
3. **Network isolation**: Services communicate on isolated bridge network
4. **Health checks**: Built-in monitoring ensures service availability
5. **Resource limits**: Add in production (`deploy.resources.limits`)

## 📖 Further Reading

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Health Check Documentation](https://docs.docker.com/engine/reference/builder/#healthcheck)

