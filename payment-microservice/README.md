# Payment Microservice

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

