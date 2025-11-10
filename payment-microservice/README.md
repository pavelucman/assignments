# Payment gRPC Microservice

[![CI](https://github.com/YOUR_USERNAME/payment-microservice/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/payment-microservice/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

An **AI-first Python gRPC microservice** for payment processing with built-in idempotency support. Designed with clean architecture principles, comprehensive testing, and production-ready Docker deployment. Perfect for learning gRPC, microservice patterns, and modern Python development practices.

**Key Highlights:**
- Production-ready gRPC API with Protocol Buffers
- Idempotent payment operations using idempotency keys
- Comprehensive input validation and error handling
- Thread-safe in-memory storage
- 82% test coverage (unit + integration)
- Full Docker and CI/CD support

## Features

### gRPC API
- **3 RPC Endpoints:**
  - `RequestPayment` - Create payment with idempotency
  - `GetPayment` - Retrieve payment by ID
  - `Health` - Service health check

### Idempotency Support
- Duplicate requests with same `idempotency_key` return the same result
- Prevents double-charging and race conditions
- Minimum key length: 8 characters

### Input Validation
- **Amount:** Must be positive (in minor units, e.g., cents)
- **Currency:** ISO 4217 codes (USD, EUR, GBP, JPY, CAD, AUD)
- **Idempotency Key:** Required, minimum 8 characters
- **Order ID:** Required, non-empty string

### In-Memory Storage
- Thread-safe with `threading.Lock`
- Dual-index lookup (by payment_id and idempotency_key)
- Fast O(1) operations
- Suitable for development and testing

### Testing
- **82% test coverage** across all layers
- 123 unit tests + 10 integration tests
- Mocked and real gRPC server tests
- Thread-safety and concurrency tests
- Coverage threshold: 80% (enforced in CI)

### Docker Support
- Multi-stage Dockerfile (~700MB final image)
- Non-root user for security
- Built-in health checks
- Docker Compose for local development
- Optimized with layer caching

### CI/CD with GitHub Actions
- Automated linting (Ruff)
- Type checking (Mypy)
- Test suite with coverage reporting
- Docker build and health check validation
- Coverage reports as artifacts

## Prerequisites

- **Python:** 3.12 or higher
- **Docker:** Latest version (optional, for containerized deployment)
- **Make:** For simplified command execution

## Quick Start

### Local Development

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd payment-microservice

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
make install

# 4. Generate gRPC code from proto files
make proto

# 5. Run the server (port 7000)
make run
```

**Test the server** (in another terminal):

```bash
# Activate virtual environment
source venv/bin/activate

# Run example client
python examples/client_example.py

# Or test manually with grpcurl
grpcurl -plaintext localhost:7000 list
```

### Docker

**Option 1: Docker Compose (Recommended)**

```bash
# Start server
docker-compose up -d

# View logs
docker-compose logs -f

# Test with client
docker-compose run --rm test-client

# Stop server
docker-compose down
```

**Option 2: Docker Commands**

```bash
# Build image
make docker-build

# Run container
make docker-run

# Or manually
docker run -d -p 7000:7000 --name payment-service payments-service:latest

# Check health
docker inspect --format='{{.State.Health.Status}}' payment-service

# Stop and remove
docker rm -f payment-service
```

## Development Commands

All development tasks are available via `make`:

```bash
make help  # Show all available commands
```

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies (dev mode) |
| `make proto` | Generate Python code from proto files |
| `make lint` | Check code quality with Ruff |
| `make format` | Auto-format code with Ruff |
| `make typecheck` | Run Mypy type checker |
| `make test` | Run tests with coverage report |
| `make run` | Start gRPC server locally |
| `make docker-build` | Build Docker image |
| `make docker-run` | Run Docker container (foreground) |
| `make docker-run-bg` | Run Docker container (background) |
| `make docker-stop` | Stop running Docker container |
| `make clean` | Remove generated files and caches |

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/unit/test_payment.py

# Run specific test
pytest tests/unit/test_payment.py::TestPaymentCreation::test_create_payment_with_factory

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View in browser
```

**Coverage Report:**

```bash
# View coverage summary
pytest --cov=src --cov-report=term-missing

# Current coverage: 82%
# Threshold (CI fails if < 80%): 80%
```

## API Documentation

### 1. RequestPayment

Create a new payment or return existing one if idempotency key matches.

**Request:**
```protobuf
message RequestPaymentRequest {
  int64 amount_minor = 1;          // Amount in cents (e.g., 1250 = $12.50)
  string currency = 2;             // ISO 4217 code (USD, EUR, etc.)
  string order_id = 3;             // Merchant order ID
  string idempotency_key = 4;      // Unique key (min 8 chars)
  map<string, string> metadata = 5; // Optional metadata
}
```

**Response:**
```protobuf
message RequestPaymentResponse {
  string payment_id = 1;           // Generated UUID
  PaymentStatus status = 2;        // PENDING, SUCCEEDED, or FAILED
  string message = 3;              // Human-readable status
  string idempotency_key = 4;      // Echo back
  google.protobuf.Timestamp created_at = 5;
}
```

**Example (Python):**
```python
import grpc
from payments_service.payments_pb2 import RequestPaymentRequest
from payments_service.payments_pb2_grpc import PaymentServiceStub

channel = grpc.insecure_channel('localhost:7000')
client = PaymentServiceStub(channel)

request = RequestPaymentRequest(
    amount_minor=1250,
    currency="USD",
    order_id="order-12345",
    idempotency_key="payment-key-00001",
    metadata={"user_id": "user-789"}
)

response = client.RequestPayment(request)
print(f"Payment ID: {response.payment_id}")
print(f"Status: {response.status}")
```

**Error Codes:**
- `INVALID_ARGUMENT` - Invalid amount, currency, or idempotency key
- `INTERNAL` - Unexpected server error

### 2. GetPayment

Retrieve an existing payment by ID.

**Request:**
```protobuf
message GetPaymentRequest {
  string payment_id = 1;  // Payment UUID
}
```

**Response:**
```protobuf
message GetPaymentResponse {
  string payment_id = 1;
  PaymentStatus status = 2;
  int64 amount_minor = 3;
  string currency = 4;
  string order_id = 5;
  string idempotency_key = 6;
  google.protobuf.Timestamp created_at = 7;
  string message = 8;
}
```

**Example (Python):**
```python
request = GetPaymentRequest(payment_id="550e8400-e29b-41d4-a716-446655440000")
response = client.GetPayment(request)
print(f"Amount: {response.amount_minor} {response.currency}")
```

**Error Codes:**
- `NOT_FOUND` - Payment ID does not exist
- `INTERNAL` - Unexpected server error

### 3. Health

Check if the service is running and healthy.

**Request:**
```protobuf
message HealthRequest {}
```

**Response:**
```protobuf
message HealthResponse {
  string status = 1;  // Always "ok"
}
```

**Example (Python):**
```python
request = HealthRequest()
response = client.Health(request)
print(f"Status: {response.status}")  # "ok"
```

## Project Structure

```
payment-microservice/
├── .github/
│   └── workflows/
│       ├── ci.yml              # GitHub Actions CI pipeline
│       └── README.md           # CI documentation
├── proto/
│   └── payments.proto          # Protocol Buffer definitions
├── src/
│   └── payments_service/
│       ├── domain/             # Domain models and business logic
│       │   ├── payment.py          # Payment entity (dataclass)
│       │   └── validators.py       # Input validation functions
│       ├── storage/            # Data persistence layer
│       │   ├── repository.py       # Abstract repository (ABC)
│       │   └── in_memory_repository.py  # Thread-safe in-memory impl
│       ├── app/                # Application services
│       │   └── payment_service.py  # Business logic orchestration
│       ├── transport/          # gRPC transport layer
│       │   └── grpc_servicer.py    # gRPC handler implementation
│       ├── server.py           # gRPC server setup
│       ├── __init__.py
│       └── __main__.py
├── tests/
│   ├── unit/                   # Unit tests (123 tests)
│   │   ├── test_payment.py         # Payment model tests
│   │   ├── test_validators.py     # Validation tests
│   │   ├── test_repository.py     # Repository tests
│   │   ├── test_payment_service.py # Service layer tests
│   │   └── test_grpc_servicer.py   # gRPC handler tests
│   └── integration/            # Integration tests (10 tests)
│       └── test_server.py          # Full server tests
├── examples/
│   ├── client_example.py       # Example gRPC client
│   └── README.md               # Client usage guide
├── Dockerfile                  # Multi-stage production image
├── Dockerfile.test             # Test client image
├── docker-compose.yml          # Local development setup
├── .dockerignore               # Docker build context filter
├── pyproject.toml              # Python dependencies and config
├── Makefile                    # Development commands
├── README.md                   # This file
└── .gitignore                  # Git ignore patterns
```

**Architecture Layers:**

1. **Transport** (`transport/`) - gRPC request/response handling
2. **Application** (`app/`) - Business logic orchestration
3. **Domain** (`domain/`) - Core business models and validation
4. **Storage** (`storage/`) - Data persistence abstraction

## Design Decisions

### Why In-Memory Storage?

**Chosen for:**
- Development and testing simplicity
- No external dependencies required
- Fast O(1) lookup performance
- Easy to understand and debug

**Trade-offs:**
- ❌ Data lost on restart (no persistence)
- ❌ Not suitable for production
- ❌ Limited by available RAM
- ❌ No horizontal scaling

**Production Alternative:**
- PostgreSQL with connection pooling
- Redis for caching layer
- Distributed transactions for consistency

### Idempotency Strategy

**Implementation:**
- Store `idempotency_key` as secondary index
- Check for existing payment before creating new one
- Return existing payment if key matches
- Thread-safe with locking

**Why This Works:**
- Prevents duplicate charges from retries
- Handles network failures gracefully
- Compatible with at-least-once delivery
- No distributed coordination needed

**Example Scenario:**
```python
# Request 1 (succeeds)
request_payment(amount=1000, key="abc123")  # Creates payment-001

# Request 2 (network timeout, client retries)
request_payment(amount=1000, key="abc123")  # Returns payment-001 (no duplicate!)

# Request 3 (different key)
request_payment(amount=1000, key="xyz789")  # Creates payment-002
```

### Error Handling Approach

**gRPC Status Codes:**
- `INVALID_ARGUMENT` - Client errors (bad input)
- `NOT_FOUND` - Resource doesn't exist
- `INTERNAL` - Server errors (unexpected)

**Validation Strategy:**
1. Validate at transport layer (fail fast)
2. Validate at service layer (business rules)
3. Validate at domain layer (invariants)

**Error Propagation:**
```python
# Domain raises ValueError
# ↓
# Service catches and logs
# ↓
# gRPC handler converts to status code
# ↓
# Client receives gRPC error
```

### What Would Be Improved With More Time

**High Priority:**

1. **Persistent Storage**
   - PostgreSQL with SQLAlchemy ORM
   - Migration system (Alembic)
   - Connection pooling and retry logic
   - Database health checks

2. **Authentication & Authorization**
   - API key validation
   - JWT token support
   - Role-based access control (RBAC)
   - Rate limiting per client

3. **Observability**
   - Structured logging (JSON format)
   - Distributed tracing (OpenTelemetry)
   - Prometheus metrics
   - Grafana dashboards

4. **Payment Processing**
   - Async payment status updates
   - Webhook notifications
   - Refund support
   - Multi-currency conversion

**Medium Priority:**

5. **Advanced Testing**
   - Load testing (Locust)
   - Chaos engineering tests
   - Contract testing (Pact)
   - Performance benchmarks

6. **Infrastructure**
   - Kubernetes deployment manifests
   - Helm charts
   - Service mesh integration (Istio)
   - Auto-scaling configuration

7. **Developer Experience**
   - API documentation website
   - SDK generation for multiple languages
   - Interactive API playground
   - Migration from in-memory to SQL guide

**Low Priority:**

8. **Additional Features**
   - Payment method management
   - Subscription support
   - Multi-tenancy
   - Audit logging

## CI/CD

### GitHub Actions Pipeline

Automated quality checks on every push and pull request:

```
lint → typecheck → test → build → summary
```

**Pipeline Stages:**

1. **Lint (Ruff)**
   - Code quality checks
   - Format verification
   - Fast fail for style issues

2. **Type Check (Mypy)**
   - Static type analysis
   - Proto code generation
   - Catch type errors early

3. **Test (Pytest)**
   - Unit + integration tests
   - Coverage reporting (82%)
   - Fail if coverage < 80%
   - Upload HTML/XML reports

4. **Build (Docker)**
   - Build Docker image
   - Start container
   - Validate health check
   - Test gRPC connectivity
   - Export image artifact

5. **Summary**
   - Overall status report
   - Coverage comments on PRs
   - Artifact links

**Artifacts Generated:**
- HTML coverage report (30 days)
- XML coverage report (30 days)
- Docker image (7 days, main/master only)

**Performance:**
- ~10 minutes (cold cache)
- ~6 minutes (warm cache)
- Parallel job execution where possible

See [`.github/workflows/README.md`](.github/workflows/README.md) for detailed CI documentation.

## Coverage Threshold

**Current Coverage:** 82%

**Threshold Settings:**
- **CI Fails If:** < 80%
- **Warning Level:** < 85%
- **Target Level:** > 90%

**Coverage by Layer:**

| Layer | Coverage | Missing |
|-------|----------|---------|
| Domain | 100% | None |
| Storage | 100% | None |
| App | 93% | Error handling paths |
| Transport | 97% | Some proto conversion edge cases |
| Server | 60% | Signal handlers, error paths |

**View Coverage Report:**

```bash
# Generate and open HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# CI enforces minimum
pytest --cov=src --cov-fail-under=80
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `7000` | gRPC server port |
| `MAX_WORKERS` | `10` | Thread pool size |
| `PYTHONUNBUFFERED` | `1` | Disable output buffering |
| `GRPC_SERVER` | `localhost:7000` | Client connection address |

## Troubleshooting

### Server Won't Start

```bash
# Check if port is already in use
lsof -i :7000

# Kill existing process
kill -9 <PID>

# Try different port
PORT=8080 make run
```

### Proto Generation Fails

```bash
# Clean generated files
make clean

# Reinstall dependencies
pip install --force-reinstall grpcio-tools

# Regenerate
make proto
```

### Tests Failing

```bash
# Clear cache and rerun
make clean
pytest -v

# Run specific failing test
pytest tests/unit/test_payment.py -v

# Check proto files are generated
ls -la src/payments_service/payments_pb2*.py
```

### Docker Build Fails

```bash
# Build with no cache
docker build --no-cache -t payments-service:latest .

# Check for Docker daemon
docker info

# Verify .dockerignore
cat .dockerignore
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Run linting (`make lint && make format`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

**Code Style:**
- Follow PEP 8 (enforced by Ruff)
- Type hints required (checked by Mypy)
- Docstrings for public functions
- Test coverage > 80%

## Acknowledgments

- Built with [gRPC](https://grpc.io/) and [Protocol Buffers](https://protobuf.dev/)
- Tested with [Pytest](https://pytest.org/)
- Linted with [Ruff](https://github.com/astral-sh/ruff)
- Type-checked with [Mypy](https://mypy-lang.org/)
- Containerized with [Docker](https://www.docker.com/)

## Contact

For questions, issues, or feedback, please open an issue on GitHub.


