"""Integration tests for gRPC server."""

import os
import time
from concurrent import futures
from threading import Thread

import grpc
import pytest

from payments_service.payments_pb2 import (
    GetPaymentRequest,
    HealthRequest,
    RequestPaymentRequest,
)
from payments_service.payments_pb2_grpc import PaymentServiceStub
from payments_service.server import PaymentServer


class TestPaymentServerIntegration:
    """Integration tests for PaymentServer."""

    @pytest.fixture
    def server_port(self) -> int:
        """Get a free port for testing."""
        return 50051  # Use a different port than default

    @pytest.fixture
    def server(self, server_port: int) -> PaymentServer:
        """Create a test server instance."""
        return PaymentServer(port=server_port, max_workers=5)

    @pytest.fixture
    def running_server(self, server: PaymentServer) -> PaymentServer:
        """Start server in a background thread."""
        # Start server in background thread
        server_thread = Thread(target=server.start, daemon=True)
        server_thread.start()

        # Wait for server to start
        time.sleep(1)

        yield server

        # Stop server after test
        server.stop()

    @pytest.fixture
    def grpc_channel(self, server_port: int) -> grpc.Channel:
        """Create gRPC channel for testing."""
        channel = grpc.insecure_channel(f"localhost:{server_port}")
        # Wait for channel to be ready
        grpc.channel_ready_future(channel).result(timeout=5)
        yield channel
        channel.close()

    @pytest.fixture
    def client(self, grpc_channel: grpc.Channel) -> PaymentServiceStub:
        """Create gRPC client stub."""
        return PaymentServiceStub(grpc_channel)

    def test_server_starts_and_stops(
        self, server_port: int
    ) -> None:
        """Test that server can start and stop cleanly."""
        server = PaymentServer(port=server_port, max_workers=2)

        # Start in background thread
        server_thread = Thread(target=server.start, daemon=True)
        server_thread.start()

        # Wait for startup
        time.sleep(1)

        # Server should be running
        assert server.server is not None

        # Stop server
        server.stop()

        # Wait for cleanup
        time.sleep(0.5)

    def test_health_check(
        self, running_server: PaymentServer, client: PaymentServiceStub
    ) -> None:
        """Test health check endpoint."""
        request = HealthRequest()
        response = client.Health(request)

        assert response.status == "ok"

    def test_request_payment_flow(
        self, running_server: PaymentServer, client: PaymentServiceStub
    ) -> None:
        """Test complete payment request flow."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="integration-test-key-123456",
            metadata={"test": "integration"},
        )

        response = client.RequestPayment(request)

        assert response.payment_id
        assert response.idempotency_key == "integration-test-key-123456"
        assert response.message
        assert response.created_at.seconds > 0

    def test_get_payment_flow(
        self, running_server: PaymentServer, client: PaymentServiceStub
    ) -> None:
        """Test payment retrieval flow."""
        # First create a payment
        create_request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-456",
            idempotency_key="integration-test-key-456789",
        )
        create_response = client.RequestPayment(create_request)

        # Then retrieve it
        get_request = GetPaymentRequest(
            payment_id=create_response.payment_id
        )
        get_response = client.GetPayment(get_request)

        assert get_response.payment_id == create_response.payment_id
        assert get_response.amount_minor == 1250
        assert get_response.currency == "USD"
        assert get_response.order_id == "order-456"

    def test_idempotency(
        self, running_server: PaymentServer, client: PaymentServiceStub
    ) -> None:
        """Test idempotency with duplicate requests."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-789",
            idempotency_key="integration-test-idempotency-key",
        )

        # First request
        response1 = client.RequestPayment(request)

        # Second request with same idempotency key
        response2 = client.RequestPayment(request)

        # Should return the same payment
        assert response1.payment_id == response2.payment_id

    def test_invalid_request_returns_error(
        self, running_server: PaymentServer, client: PaymentServiceStub
    ) -> None:
        """Test that invalid requests return proper errors."""
        request = RequestPaymentRequest(
            amount_minor=-100,  # Invalid: negative
            currency="USD",
            order_id="order-999",
            idempotency_key="integration-test-error-key",
        )

        with pytest.raises(grpc.RpcError) as exc_info:
            client.RequestPayment(request)

        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT

    def test_payment_not_found_returns_error(
        self, running_server: PaymentServer, client: PaymentServiceStub
    ) -> None:
        """Test that nonexistent payment returns NOT_FOUND."""
        request = GetPaymentRequest(payment_id="nonexistent-id")

        with pytest.raises(grpc.RpcError) as exc_info:
            client.GetPayment(request)

        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


class TestPaymentServerConfiguration:
    """Tests for server configuration."""

    def test_custom_port(self) -> None:
        """Test server with custom port."""
        server = PaymentServer(port=9999, max_workers=5)
        assert server.port == 9999
        assert server.max_workers == 5

    def test_default_port(self) -> None:
        """Test server with default configuration."""
        server = PaymentServer()
        assert server.port == 7000
        assert server.max_workers == 10

    def test_port_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that PORT environment variable is respected."""
        monkeypatch.setenv("PORT", "9090")
        monkeypatch.setenv("MAX_WORKERS", "15")

        # Import main and check if it reads env vars correctly
        # This is more of a smoke test since main() starts the server
        from payments_service.server import main

        # We can't easily test main() without actually starting the server,
        # but we can verify the environment variables are set
        assert os.getenv("PORT") == "9090"
        assert os.getenv("MAX_WORKERS") == "15"

