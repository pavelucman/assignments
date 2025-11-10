.PHONY: help proto install lint format typecheck test run docker-build docker-run docker-stop docker-run-bg clean

# Default target
help:
	@echo "Payment Microservice - Available Make Targets"
	@echo "=============================================="
	@echo ""
	@echo "  make proto          - Generate Python code from proto files"
	@echo "  make install        - Install dependencies (dev mode)"
	@echo "  make lint           - Run ruff linter"
	@echo "  make format         - Format code with ruff"
	@echo "  make typecheck      - Run mypy type checker"
	@echo "  make test           - Run tests with coverage"
	@echo "  make run            - Run the payment service locally"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container (foreground)"
	@echo "  make docker-run-bg  - Run Docker container (background)"
	@echo "  make docker-stop    - Stop running Docker container"
	@echo "  make clean          - Remove generated files and caches"
	@echo "  make help           - Show this help message"
	@echo ""

# Generate Python code from proto files
proto:
	@echo "Generating Python code from proto files..."
	python -m grpc_tools.protoc \
		-I proto \
		--python_out=src \
		--grpc_python_out=src \
		--mypy_out=src \
		proto/payments.proto
	@echo "Fixing imports in generated files..."
	@sed -i.bak 's/^import payments_pb2/from payments_service import payments_pb2/' src/payments_service/payments_pb2_grpc.py && rm -f src/payments_service/payments_pb2_grpc.py.bak || true
	@echo "✓ Proto files generated successfully"

# Install dependencies in development mode
install:
	@echo "Installing dependencies..."
	pip install -e ".[dev]"
	@echo "✓ Dependencies installed successfully"

# Run linter
lint:
	@echo "Running ruff linter..."
	ruff check .

# Format code
format:
	@echo "Formatting code with ruff..."
	ruff format .
	@echo "✓ Code formatted successfully"

# Run type checker
typecheck:
	@echo "Running mypy type checker..."
	mypy src/

# Run tests with coverage
test:
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=term-missing --cov-report=html
	@echo "✓ Tests completed"

# Run the payment service
run:
	@echo "Starting payment service..."
	python -m payments_service.server

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t payments-service:latest -t payments-service:0.1.0 .
	@echo "✓ Docker image built successfully"

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker run --rm -p 7000:7000 --name payment-service payments-service:latest

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	docker stop payment-service || true

# Run Docker container in background
docker-run-bg:
	@echo "Running Docker container in background..."
	docker run -d -p 7000:7000 --name payment-service payments-service:latest
	@echo "✓ Container started. View logs with: docker logs -f payment-service"

# Clean generated files and caches
clean:
	@echo "Cleaning generated files and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -f src/payments_service/payments_pb2.py
	rm -f src/payments_service/payments_pb2.pyi
	rm -f src/payments_service/payments_pb2_grpc.py
	@echo "✓ Cleanup completed"

