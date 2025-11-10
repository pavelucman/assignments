# Multi-stage Dockerfile for Python gRPC Payment Microservice
# Optimized for small image size and security

# =============================================================================
# Stage 1: Builder - Install dependencies and generate gRPC code
# =============================================================================
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .

# Create virtual environment and install dependencies
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /app/venv/bin/pip install --no-cache-dir -e ".[dev]"

# Copy proto files
COPY proto/ proto/

# Copy source code (needed for package structure)
COPY src/ src/

# Generate gRPC code and move to correct location
RUN /app/venv/bin/python -m grpc_tools.protoc \
    -I proto \
    --python_out=. \
    --grpc_python_out=. \
    proto/payments.proto && \
    # Move generated files to payments_service package \
    mv payments_pb2.py src/payments_service/ && \
    mv payments_pb2_grpc.py src/payments_service/ && \
    # Fix imports in generated gRPC file \
    sed -i 's/^import payments_pb2/from payments_service import payments_pb2/' src/payments_service/payments_pb2_grpc.py

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.12-slim AS runtime

# Metadata labels
LABEL maintainer="payment-service@example.com"
LABEL version="0.1.0"
LABEL description="Python gRPC Payment Microservice"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/venv/bin:$PATH" \
    PORT=7000

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Copy source code with generated proto files from builder
COPY --from=builder /app/src/payments_service /app/payments_service

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose gRPC port
EXPOSE 7000

# Health check using Python socket check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2); s.connect(('localhost', 7000)); s.close()" || exit 1

# Run the gRPC server
CMD ["python", "-m", "payments_service.server"]

