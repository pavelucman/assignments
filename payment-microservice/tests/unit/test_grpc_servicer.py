"""Unit tests for gRPC servicer."""

import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock

import grpc
import pytest
from google.protobuf.timestamp_pb2 import Timestamp

from payments_service.app import PaymentService
from payments_service.domain import Payment, PaymentStatus
from payments_service.payments_pb2 import (
    GetPaymentRequest,
    HealthRequest,
    PaymentStatus as ProtoPaymentStatus,
    RequestPaymentRequest,
)
from payments_service.storage import InMemoryPaymentRepository
from payments_service.transport import PaymentServiceGrpcServicer


@pytest.fixture
def mock_service() -> MagicMock:
    """Fixture providing mock PaymentService."""
    return MagicMock(spec=PaymentService)


@pytest.fixture
def mock_context() -> MagicMock:
    """Fixture providing mock gRPC context."""
    context = MagicMock(spec=grpc.ServicerContext)
    context.abort.side_effect = grpc.RpcError("Aborted")
    return context


@pytest.fixture
def sample_payment() -> Payment:
    """Fixture providing sample payment for testing."""
    return Payment.create(
        amount_minor=1250,
        currency="USD",
        order_id="order-123",
        idempotency_key="idem-key-12345678",
    )


class TestPaymentServiceGrpcServicerRequestPayment:
    """Tests for RequestPayment RPC method."""

    @pytest.fixture
    def repository(self) -> InMemoryPaymentRepository:
        """Create a fresh repository."""
        return InMemoryPaymentRepository()

    @pytest.fixture
    def service(
        self, repository: InMemoryPaymentRepository
    ) -> PaymentService:
        """Create PaymentService."""
        return PaymentService(repository)

    @pytest.fixture
    def servicer(self, service: PaymentService) -> PaymentServiceGrpcServicer:
        """Create gRPC servicer."""
        return PaymentServiceGrpcServicer(service)

    @pytest.fixture
    def mock_context_local(self) -> MagicMock:
        """Create mock gRPC context."""
        context = MagicMock(spec=grpc.ServicerContext)
        context.abort.side_effect = grpc.RpcError("Aborted")
        return context

    def test_request_payment_with_mocked_service(
        self, mock_service: MagicMock, mock_context: MagicMock, sample_payment: Payment
    ) -> None:
        """
        Test RequestPayment RPC with mocked service layer.
        
        Verifies:
        - Proto request is created correctly
        - Service layer is called with correct args
        - Proto response has correct fields
        """
        # Setup mock
        mock_service.request_payment.return_value = sample_payment
        servicer = PaymentServiceGrpcServicer(mock_service)
        
        # Create valid proto request
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
            metadata={"user_id": "user-789"},
        )
        
        # Call RPC
        response = servicer.RequestPayment(request, mock_context)
        
        # Verify service.request_payment was called with correct args
        mock_service.request_payment.assert_called_once_with(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
            metadata={"user_id": "user-789"},
        )
        
        # Verify proto response has correct fields
        assert response.payment_id == sample_payment.payment_id
        assert response.status == ProtoPaymentStatus.PAYMENT_STATUS_PENDING
        assert response.idempotency_key == "idem-key-12345678"
        assert response.message == sample_payment.message
        assert response.created_at.seconds > 0

    def test_request_payment_validation_error_with_mock(
        self, mock_service: MagicMock, mock_context: MagicMock
    ) -> None:
        """
        Test RequestPayment with validation error using mocked service.
        
        Verifies:
        - Service raises ValueError
        - context.abort is called with INVALID_ARGUMENT status code
        """
        # Setup mock to raise ValueError
        mock_service.request_payment.side_effect = ValueError("Invalid amount: amount must be positive")
        servicer = PaymentServiceGrpcServicer(mock_service)
        
        # Create request
        request = RequestPaymentRequest(
            amount_minor=-100,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )
        
        # Call RPC - should abort
        with pytest.raises(grpc.RpcError):
            servicer.RequestPayment(request, mock_context)
        
        # Verify context.abort was called with INVALID_ARGUMENT
        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
        assert "Validation error" in call_args[0][1]

    def test_request_payment_success(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test successful payment request."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
            metadata={"user_id": "user-789"},
        )

        response = servicer.RequestPayment(request, mock_context_local)

        assert response.payment_id  # UUID generated
        assert response.status == ProtoPaymentStatus.PAYMENT_STATUS_PENDING
        assert response.idempotency_key == "idem-key-12345678"
        assert response.message
        assert response.created_at.seconds > 0

    def test_request_payment_idempotency(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test that duplicate requests return same payment."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

        # First request
        response1 = servicer.RequestPayment(request, mock_context_local)

        # Second request with same idempotency key
        response2 = servicer.RequestPayment(request, mock_context_local)

        # Should return the same payment
        assert response1.payment_id == response2.payment_id

    def test_request_payment_invalid_amount(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test that invalid amount aborts with INVALID_ARGUMENT."""
        request = RequestPaymentRequest(
            amount_minor=-100,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

        with pytest.raises(grpc.RpcError):
            servicer.RequestPayment(request, mock_context_local)

        mock_context_local.abort.assert_called_once()
        call_args = mock_context_local.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT
        assert "Validation error" in call_args[0][1]

    def test_request_payment_invalid_currency(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test that invalid currency aborts with INVALID_ARGUMENT."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="XXX",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

        with pytest.raises(grpc.RpcError):
            servicer.RequestPayment(request, mock_context_local)

        mock_context_local.abort.assert_called_once()
        call_args = mock_context_local.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT

    def test_request_payment_invalid_idempotency_key(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test that invalid idempotency key aborts with INVALID_ARGUMENT."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="short",
        )

        with pytest.raises(grpc.RpcError):
            servicer.RequestPayment(request, mock_context_local)

        mock_context_local.abort.assert_called_once()
        call_args = mock_context_local.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT

    def test_request_payment_with_metadata(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test payment request with metadata."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
            metadata={
                "user_id": "user-789",
                "session_id": "session-456",
            },
        )

        response = servicer.RequestPayment(request, mock_context_local)

        assert response.payment_id

    def test_request_payment_logs_request(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that request is logged."""
        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

        with caplog.at_level(logging.INFO):
            servicer.RequestPayment(request, mock_context_local)

        assert "RequestPayment RPC called" in caplog.text

    def test_request_payment_internal_error(
        self, mock_context: MagicMock
    ) -> None:
        """Test that unexpected errors abort with INTERNAL."""
        # Create servicer with mocked service that raises exception
        mock_service = MagicMock(spec=PaymentService)
        mock_service.request_payment.side_effect = Exception("Database error")

        servicer = PaymentServiceGrpcServicer(mock_service)

        request = RequestPaymentRequest(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

        with pytest.raises(grpc.RpcError):
            servicer.RequestPayment(request, mock_context)

        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INTERNAL
        assert "Internal error" in call_args[0][1]


class TestPaymentServiceGrpcServicerGetPayment:
    """Tests for GetPayment RPC method."""

    @pytest.fixture
    def repository(self) -> InMemoryPaymentRepository:
        """Create a fresh repository."""
        return InMemoryPaymentRepository()

    @pytest.fixture
    def service(
        self, repository: InMemoryPaymentRepository
    ) -> PaymentService:
        """Create PaymentService."""
        return PaymentService(repository)

    @pytest.fixture
    def servicer(self, service: PaymentService) -> PaymentServiceGrpcServicer:
        """Create gRPC servicer."""
        return PaymentServiceGrpcServicer(service)

    @pytest.fixture
    def mock_context_local(self) -> MagicMock:
        """Create mock gRPC context."""
        context = MagicMock(spec=grpc.ServicerContext)
        context.abort.side_effect = grpc.RpcError("Aborted")
        return context

    @pytest.fixture
    def sample_payment_local(self, service: PaymentService) -> Payment:
        """Create a sample payment."""
        return service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

    def test_get_payment_with_mocked_service(
        self, mock_service: MagicMock, mock_context: MagicMock, sample_payment: Payment
    ) -> None:
        """
        Test GetPayment RPC with mocked service layer.
        
        Verifies:
        - Service.get_payment is called with correct payment_id
        - Proto response has correct fields
        """
        # Setup mock to return a payment
        mock_service.get_payment.return_value = sample_payment
        servicer = PaymentServiceGrpcServicer(mock_service)
        
        # Create proto request
        request = GetPaymentRequest(payment_id=sample_payment.payment_id)
        
        # Call RPC
        response = servicer.GetPayment(request, mock_context)
        
        # Verify service.get_payment was called with correct args
        mock_service.get_payment.assert_called_once_with(sample_payment.payment_id)
        
        # Verify proto response is correct
        assert response.payment_id == sample_payment.payment_id
        assert response.amount_minor == 1250
        assert response.currency == "USD"
        assert response.order_id == "order-123"
        assert response.idempotency_key == "idem-key-12345678"
        assert response.status == ProtoPaymentStatus.PAYMENT_STATUS_PENDING
        assert response.message == sample_payment.message
        assert response.created_at.seconds > 0

    def test_get_payment_not_found_with_mock(
        self, mock_service: MagicMock, mock_context: MagicMock
    ) -> None:
        """
        Test GetPayment not found with mocked service.
        
        Verifies:
        - Service.get_payment returns None
        - context.abort is called with NOT_FOUND status code
        """
        # Setup mock to return None (not found)
        mock_service.get_payment.return_value = None
        servicer = PaymentServiceGrpcServicer(mock_service)
        
        # Create request
        request = GetPaymentRequest(payment_id="nonexistent-id")
        
        # Call RPC - should abort
        with pytest.raises(grpc.RpcError):
            servicer.GetPayment(request, mock_context)
        
        # Verify service.get_payment was called
        mock_service.get_payment.assert_called_once_with("nonexistent-id")
        
        # Verify context.abort was called once with NOT_FOUND
        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.NOT_FOUND
        assert "not found" in call_args[0][1].lower()

    def test_get_payment_success(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
        sample_payment_local: Payment,
    ) -> None:
        """Test successful payment retrieval."""
        request = GetPaymentRequest(payment_id=sample_payment_local.payment_id)

        response = servicer.GetPayment(request, mock_context_local)

        assert response.payment_id == sample_payment_local.payment_id
        assert response.amount_minor == 1250
        assert response.currency == "USD"
        assert response.order_id == "order-123"
        assert response.idempotency_key == "idem-key-12345678"
        assert response.status == ProtoPaymentStatus.PAYMENT_STATUS_PENDING
        assert response.message
        assert response.created_at.seconds > 0

    def test_get_payment_not_found(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test that nonexistent payment aborts with NOT_FOUND."""
        request = GetPaymentRequest(payment_id="nonexistent-id")

        with pytest.raises(grpc.RpcError):
            servicer.GetPayment(request, mock_context_local)

        # Verify context.abort was called once with NOT_FOUND
        mock_context_local.abort.assert_called_once()
        call_args = mock_context_local.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.NOT_FOUND
        assert "Payment not found" in call_args[0][1]

    def test_get_payment_logs_request(
        self,
        servicer: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
        sample_payment_local: Payment,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that request is logged."""
        request = GetPaymentRequest(payment_id=sample_payment_local.payment_id)

        with caplog.at_level(logging.INFO):
            servicer.GetPayment(request, mock_context_local)

        assert "GetPayment RPC called" in caplog.text

    def test_get_payment_internal_error(
        self, mock_context: MagicMock
    ) -> None:
        """Test that unexpected errors abort with INTERNAL."""
        # Create servicer with mocked service that raises exception
        mock_service = MagicMock(spec=PaymentService)
        mock_service.get_payment.side_effect = Exception("Database error")

        servicer = PaymentServiceGrpcServicer(mock_service)

        request = GetPaymentRequest(payment_id="some-id")

        with pytest.raises(grpc.RpcError):
            servicer.GetPayment(request, mock_context)

        mock_context.abort.assert_called_once()
        call_args = mock_context.abort.call_args
        assert call_args[0][0] == grpc.StatusCode.INTERNAL
        assert "Internal error" in call_args[0][1]


class TestPaymentServiceGrpcServicerHealth:
    """Tests for Health RPC method."""

    @pytest.fixture
    def servicer_local(self) -> PaymentServiceGrpcServicer:
        """Create gRPC servicer with minimal setup."""
        mock_service_local = MagicMock(spec=PaymentService)
        return PaymentServiceGrpcServicer(mock_service_local)

    @pytest.fixture
    def mock_context_local(self) -> MagicMock:
        """Create mock gRPC context."""
        return MagicMock(spec=grpc.ServicerContext)

    def test_health_rpc_returns_ok(
        self, mock_service: MagicMock, mock_context: MagicMock
    ) -> None:
        """
        Test Health RPC.
        
        Verifies:
        - Response.status == "ok"
        - No service methods are called
        """
        servicer = PaymentServiceGrpcServicer(mock_service)
        request = HealthRequest()

        response = servicer.Health(request, mock_context)

        # Verify response.status == "ok"
        assert response.status == "ok"
        
        # Verify no service methods were called (health check is independent)
        mock_service.request_payment.assert_not_called()
        mock_service.get_payment.assert_not_called()

    def test_health_returns_ok(
        self,
        servicer_local: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
    ) -> None:
        """Test that health check returns OK."""
        request = HealthRequest()

        response = servicer_local.Health(request, mock_context_local)

        assert response.status == "ok"

    def test_health_logs_request(
        self,
        servicer_local: PaymentServiceGrpcServicer,
        mock_context_local: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that health check is logged."""
        request = HealthRequest()

        with caplog.at_level(logging.DEBUG):
            servicer_local.Health(request, mock_context_local)

        assert "Health RPC called" in caplog.text


class TestPaymentServiceGrpcServicerConversions:
    """Tests for domain-to-protobuf conversion methods."""

    @pytest.fixture
    def servicer(self) -> PaymentServiceGrpcServicer:
        """Create gRPC servicer with minimal setup."""
        mock_service = MagicMock(spec=PaymentService)
        return PaymentServiceGrpcServicer(mock_service)

    def test_status_conversion_pending(
        self, servicer: PaymentServiceGrpcServicer
    ) -> None:
        """Test status conversion for PENDING."""
        proto_status = servicer._domain_status_to_proto(PaymentStatus.PENDING)
        assert proto_status == ProtoPaymentStatus.PAYMENT_STATUS_PENDING

    def test_status_conversion_succeeded(
        self, servicer: PaymentServiceGrpcServicer
    ) -> None:
        """Test status conversion for SUCCEEDED."""
        proto_status = servicer._domain_status_to_proto(
            PaymentStatus.SUCCEEDED
        )
        assert proto_status == ProtoPaymentStatus.PAYMENT_STATUS_SUCCEEDED

    def test_status_conversion_failed(
        self, servicer: PaymentServiceGrpcServicer
    ) -> None:
        """Test status conversion for FAILED."""
        proto_status = servicer._domain_status_to_proto(PaymentStatus.FAILED)
        assert proto_status == ProtoPaymentStatus.PAYMENT_STATUS_FAILED

    def test_timestamp_conversion(
        self, servicer: PaymentServiceGrpcServicer
    ) -> None:
        """Test that datetime is correctly converted to protobuf Timestamp."""
        payment = Payment.create(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

        response = servicer._payment_to_request_payment_response(payment)

        # Verify timestamp is set and reasonable
        assert response.created_at.seconds > 0
        # Convert back to verify (ToDatetime returns naive datetime in UTC)
        dt = response.created_at.ToDatetime(tzinfo=timezone.utc)
        assert dt.tzinfo == timezone.utc
        # Verify it's recent (within last minute)
        now = datetime.now(timezone.utc)
        time_diff = (now - dt).total_seconds()
        assert 0 <= time_diff < 60

