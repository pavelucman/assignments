# Payment Microservice

[![CI](https://github.com/YOUR_USERNAME/payment-microservice/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/payment-microservice/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python gRPC payment microservice with idempotency support, validation, and comprehensive testing.

## Features

- ✅ gRPC API with Protocol Buffers
- ✅ Idempotent payment requests
- ✅ Input validation (amount, currency, idempotency keys)
- ✅ Thread-safe in-memory storage
- ✅ Comprehensive logging
- ✅ Graceful shutdown handling
- ✅ Full test coverage (unit + integration tests)

## Architecture

```
src/payments_service/
├── domain/          # Domain models and business logic
│   ├── payment.py       # Payment entity
│   └── validators.py    # Input validation
├── storage/         # Data persistence layer
│   ├── repository.py    # Abstract repository interface
│   └── in_memory_repository.py  # In-memory implementation
├── app/             # Application services
│   └── payment_service.py  # Payment business logic
├── transport/       # gRPC layer
│   └── grpc_servicer.py  # gRPC service implementation
└── server.py        # Server entry point
```

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Install dependencies
make install

# Or manually
pip install -e ".[dev]"
```

### Generate Proto Files

```bash
make proto
```

This generates Python gRPC code from `proto/payments.proto`.

## Running the Server

### Basic Usage

```bash
# Run with default settings (port 7000)
python -m payments_service.server

# Or using make
make run
```

### Configuration

Configure via environment variables:

```bash
# Custom port
PORT=9090 python -m payments_service.server

# Custom thread pool size
MAX_WORKERS=20 python -m payments_service.server

# Both
PORT=9090 MAX_WORKERS=20 python -m payments_service.server
```

## Docker Deployment

### Building the Docker Image

```bash
# Build the image
make docker-build

# Or manually
docker build -t payments-service:latest .
```

The Dockerfile uses multi-stage builds for:
- ✅ Minimal image size (~150MB)
- ✅ Security (runs as non-root user)
- ✅ Optimized layer caching
- ✅ Built-in health checks

### Running with Docker

```bash
# Run in foreground (logs to stdout)
make docker-run

# Run in background
make docker-run-bg

# Stop the container
make docker-stop

# View logs
docker logs -f payment-service
```

### Docker Configuration

Pass environment variables to the container:

```bash
# Custom port
docker run --rm -p 8080:8080 -e PORT=8080 payments-service:latest

# Custom worker threads
docker run --rm -p 7000:7000 -e MAX_WORKERS=20 payments-service:latest

# Both
docker run --rm -p 9000:9000 \
  -e PORT=9000 \
  -e MAX_WORKERS=20 \
  payments-service:latest
```

### Health Check

The Docker container includes a built-in health check that runs every 30 seconds:

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' payment-service

# View health check logs
docker inspect --format='{{json .State.Health}}' payment-service | python -m json.tool
```

### Docker Compose (Recommended for Local Development)

**Basic Usage:**

```bash
# Start service in background
docker-compose up -d

# View logs
docker-compose logs -f payment-service

# Stop service
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

**Run with Test Client:**

The Docker Compose setup includes an optional test client service that demonstrates the payment service functionality:

```bash
# Start server and run test client
docker-compose --profile test up

# Or run test client against running server
docker-compose run --rm test-client

# View test client logs
docker-compose logs test-client
```

**Environment Variables:**

You can override environment variables in a `.env` file:

```bash
# Create .env file
cat > .env << EOF
PORT=8080
MAX_WORKERS=20
EOF

# Start with custom configuration
docker-compose up -d
```

### Server Output

```
2025-11-09 10:00:00 - payments_service.server - INFO - PaymentServer initialized (port=7000, workers=10)
2025-11-09 10:00:00 - payments_service.server - INFO - Starting payment microservice...
2025-11-09 10:00:00 - payments_service.server - INFO - Creating InMemoryPaymentRepository...
2025-11-09 10:00:00 - payments_service.server - INFO - Creating PaymentService...
2025-11-09 10:00:00 - payments_service.server - INFO - Creating PaymentServiceGrpcServicer...
2025-11-09 10:00:00 - payments_service.server - INFO - Creating gRPC server with 10 workers...
2025-11-09 10:00:00 - payments_service.server - INFO - Adding PaymentService servicer to server...
2025-11-09 10:00:00 - payments_service.server - INFO - Server bound to [::]:7000
2025-11-09 10:00:00 - payments_service.server - INFO - ✓ Payment microservice started successfully on port 7000
2025-11-09 10:00:00 - payments_service.server - INFO - Server is ready to accept requests
```

### Graceful Shutdown

Press `Ctrl+C` or send `SIGTERM`:

```
^C2025-11-09 10:05:00 - payments_service.server - INFO - Received signal SIGINT, initiating shutdown...
2025-11-09 10:05:00 - payments_service.server - INFO - Stopping server (grace period: 5s)...
2025-11-09 10:05:00 - payments_service.server - INFO - ✓ Server stopped successfully
```

## API Usage

### gRPC Client Example

```python
import grpc
from payments_service.payments_pb2 import RequestPaymentRequest
from payments_service.payments_pb2_grpc import PaymentServiceStub

# Create channel
channel = grpc.insecure_channel('localhost:7000')
client = PaymentServiceStub(channel)

# Request payment
request = RequestPaymentRequest(
    amount_minor=1250,  # $12.50 in cents
    currency="USD",
    order_id="order-123",
    idempotency_key="unique-key-12345678",
    metadata={"user_id": "user-789"}
)

response = client.RequestPayment(request)
print(f"Payment ID: {response.payment_id}")
print(f"Status: {response.status}")
print(f"Message: {response.message}")

# Get payment
from payments_service.payments_pb2 import GetPaymentRequest

get_request = GetPaymentRequest(payment_id=response.payment_id)
payment = client.GetPayment(get_request)
print(f"Amount: ${payment.amount_minor / 100:.2f}")
print(f"Currency: {payment.currency}")

# Health check
from payments_service.payments_pb2 import HealthRequest

health_request = HealthRequest()
health_response = client.Health(health_request)
print(f"Health: {health_response.status}")
```

### Using grpcurl

```bash
# Health check
grpcurl -plaintext localhost:7000 payments.v1.PaymentService/Health

# Request payment
grpcurl -plaintext -d '{
  "amount_minor": 1250,
  "currency": "USD",
  "order_id": "order-123",
  "idempotency_key": "test-key-12345678"
}' localhost:7000 payments.v1.PaymentService/RequestPayment

# Get payment
grpcurl -plaintext -d '{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000"
}' localhost:7000 payments.v1.PaymentService/GetPayment
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run all checks
make format lint typecheck test
```

### Supported Operations

#### 1. RequestPayment (Idempotent)

Creates a new payment or returns existing one based on idempotency key.

**Validation:**
- `amount_minor` must be positive
- `currency` must be one of: USD, EUR, GBP, JPY, CAD, AUD
- `idempotency_key` must be at least 8 characters
- `order_id` cannot be empty

**Status Codes:**
- `OK` - Payment created/retrieved successfully
- `INVALID_ARGUMENT` - Validation failed
- `INTERNAL` - Server error

#### 2. GetPayment

Retrieves payment by ID.

**Status Codes:**
- `OK` - Payment found
- `NOT_FOUND` - Payment doesn't exist
- `INTERNAL` - Server error

#### 3. Health

Lightweight health check.

**Status Codes:**
- `OK` - Service is healthy

## Docker

```bash
# Build image
make docker-build

# Run container
docker run -p 7000:7000 payments-service:latest

# With custom port
docker run -p 9090:9090 -e PORT=9090 payments-service:latest
```

## Project Structure

```
payment-microservice/
├── proto/                  # Protocol Buffer definitions
│   └── payments.proto
├── src/
│   └── payments_service/   # Main package
│       ├── domain/         # Business entities and validation
│       ├── storage/        # Data persistence
│       ├── app/            # Application services
│       ├── transport/      # gRPC servicer
│       ├── server.py       # Server entry point
│       └── __main__.py     # Module entry point
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── pyproject.toml         # Dependencies and config
├── Makefile              # Build automation
└── README.md             # This file
```

## License

MIT

