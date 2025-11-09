"""Unit tests for PaymentService."""

import logging
from unittest.mock import MagicMock, call, patch

import pytest

from payments_service.app import PaymentService
from payments_service.domain import Payment, PaymentStatus
from payments_service.storage import InMemoryPaymentRepository


@pytest.fixture
def valid_payment_data() -> dict:
    """Fixture providing valid payment request data."""
    return {
        "amount_minor": 1250,
        "currency": "USD",
        "order_id": "order-123",
        "idempotency_key": "idem-key-12345678",
        "metadata": {"user_id": "user-789"},
    }


class TestPaymentServiceRequestPayment:
    """Tests for PaymentService.request_payment method."""

    @pytest.fixture
    def repository(self) -> InMemoryPaymentRepository:
        """Create a fresh repository for each test."""
        return InMemoryPaymentRepository()

    @pytest.fixture
    def service(
        self, repository: InMemoryPaymentRepository
    ) -> PaymentService:
        """Create PaymentService with repository."""
        return PaymentService(repository)

    def test_request_payment_happy_path(
        self, service: PaymentService, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test request_payment happy path.
        
        Verifies:
        - Payment is created with correct fields
        - Payment is saved to repository
        - Status is PENDING
        """
        payment = service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
            metadata={"user_id": "user-789"},
        )

        # Verify payment created with correct fields
        assert payment.amount_minor == 1250
        assert payment.currency == "USD"
        assert payment.order_id == "order-123"
        assert payment.idempotency_key == "idem-key-12345678"
        assert payment.metadata == {"user_id": "user-789"}
        
        # Verify status is PENDING
        assert payment.status == PaymentStatus.PENDING
        assert payment.is_pending is True
        
        # Verify payment is saved to repository
        assert repository.count() == 1
        saved_payment = repository.find_by_id(payment.payment_id)
        assert saved_payment is not None
        assert saved_payment == payment

    def test_request_payment_creates_new_payment(
        self, service: PaymentService, repository: InMemoryPaymentRepository
    ) -> None:
        """Test creating a new payment."""
        payment = service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
            metadata={"user_id": "user-789"},
        )

        assert payment.amount_minor == 1250
        assert payment.currency == "USD"
        assert payment.order_id == "order-123"
        assert payment.idempotency_key == "idem-key-12345678"
        assert payment.status == PaymentStatus.PENDING
        assert payment.metadata == {"user_id": "user-789"}
        assert repository.count() == 1

    def test_request_payment_invalid_amount(
        self, service: PaymentService
    ) -> None:
        """
        Test request_payment with invalid amount.
        
        Should raise ValueError for negative or zero amounts.
        """
        # Negative amount
        with pytest.raises(ValueError, match="Invalid amount"):
            service.request_payment(
                amount_minor=-100,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345678",
            )
        
        # Zero amount
        with pytest.raises(ValueError, match="Invalid amount"):
            service.request_payment(
                amount_minor=0,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345678",
            )

    def test_request_payment_invalid_currency(
        self, service: PaymentService
    ) -> None:
        """
        Test request_payment with invalid currency.
        
        Should raise ValueError for unsupported currencies.
        """
        with pytest.raises(ValueError, match="Invalid currency"):
            service.request_payment(
                amount_minor=1250,
                currency="XXX",
                order_id="order-123",
                idempotency_key="idem-key-12345678",
            )

    def test_request_payment_empty_idempotency_key(
        self, service: PaymentService
    ) -> None:
        """
        Test request_payment with empty idempotency_key.
        
        Should raise ValueError for empty or too short keys.
        """
        # Empty string
        with pytest.raises(ValueError, match="Invalid idempotency key"):
            service.request_payment(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="",
            )
        
        # Too short (< 8 characters)
        with pytest.raises(ValueError, match="Invalid idempotency key"):
            service.request_payment(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="short",
            )

    def test_request_payment_validates_inputs(
        self, service: PaymentService
    ) -> None:
        """Test that invalid inputs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid amount"):
            service.request_payment(
                amount_minor=-100,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345678",
            )

    def test_request_payment_validates_currency(
        self, service: PaymentService
    ) -> None:
        """Test that invalid currency raises ValueError."""
        with pytest.raises(ValueError, match="Invalid currency"):
            service.request_payment(
                amount_minor=1250,
                currency="XXX",
                order_id="order-123",
                idempotency_key="idem-key-12345678",
            )

    def test_request_payment_validates_idempotency_key(
        self, service: PaymentService
    ) -> None:
        """Test that invalid idempotency key raises ValueError."""
        with pytest.raises(ValueError, match="Invalid idempotency key"):
            service.request_payment(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="short",
            )

    def test_request_payment_idempotency(
        self, service: PaymentService, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test request_payment idempotency.
        
        Verifies:
        - First request creates payment
        - Second request with same key returns existing payment
        - Same payment_id is returned
        - Only one payment stored in repository
        """
        # First request with key "test-idempotency-key-001"
        payment1 = service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="test-idempotency-key-001",
        )

        # Second request with same key "test-idempotency-key-001" but different data
        payment2 = service.request_payment(
            amount_minor=5000,  # Different amount
            currency="EUR",  # Different currency
            order_id="order-456",  # Different order
            idempotency_key="test-idempotency-key-001",  # Same key!
        )

        # Verify same payment_id is returned
        assert payment1.payment_id == payment2.payment_id
        
        # Verify original payment data is returned (not new data)
        assert payment2.amount_minor == 1250  # Original amount
        assert payment2.currency == "USD"  # Original currency
        assert payment2.order_id == "order-123"  # Original order
        
        # Verify only one payment stored in repository
        assert repository.count() == 1

    def test_request_payment_idempotency_with_mock(self) -> None:
        """
        Test idempotency using mock to verify repository.save called only once.
        
        Verifies that when idempotency key exists:
        - repository.find_by_idempotency_key is called
        - repository.save is NOT called again
        - Existing payment is returned
        """
        # Create mock repository
        mock_repository = MagicMock()
        service = PaymentService(mock_repository)
        
        # First request - no existing payment
        mock_repository.find_by_idempotency_key.return_value = None
        
        # Mock save to return a payment
        expected_payment = Payment.create(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="test-idempotency-key-001",
        )
        mock_repository.save.return_value = expected_payment
        
        # First request
        payment1 = service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="test-idempotency-key-001",
        )
        
        # Verify save was called once for first request
        assert mock_repository.save.call_count == 1
        
        # Second request - existing payment found
        mock_repository.find_by_idempotency_key.return_value = expected_payment
        
        payment2 = service.request_payment(
            amount_minor=5000,  # Different data
            currency="EUR",
            order_id="order-456",
            idempotency_key="test-idempotency-key-001",  # Same key
        )
        
        # Verify save was NOT called again (still 1)
        assert mock_repository.save.call_count == 1
        
        # Verify find_by_idempotency_key was called twice
        assert mock_repository.find_by_idempotency_key.call_count == 2
        
        # Verify same payment returned
        assert payment2 == expected_payment

    def test_request_payment_with_metadata(
        self, service: PaymentService
    ) -> None:
        """Test creating payment with metadata."""
        metadata = {
            "user_id": "user-123",
            "session_id": "session-456",
            "ip_address": "192.168.1.1",
        }

        payment = service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345",
            metadata=metadata,
        )

        assert payment.metadata == metadata

    def test_request_payment_without_metadata(
        self, service: PaymentService
    ) -> None:
        """Test creating payment without metadata defaults to empty dict."""
        payment = service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345",
        )

        assert payment.metadata == {}

    def test_request_payment_normalizes_currency(
        self, service: PaymentService
    ) -> None:
        """Test that currency is normalized to uppercase."""
        payment = service.request_payment(
            amount_minor=1250,
            currency="usd",
            order_id="order-123",
            idempotency_key="idem-key-12345",
        )

        assert payment.currency == "USD"

    def test_request_payment_logs_operations(
        self, service: PaymentService, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that payment operations are logged."""
        with caplog.at_level(logging.INFO):
            service.request_payment(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345",
            )

        # Check for log messages
        assert "Payment request received" in caplog.text
        assert "Payment saved successfully" in caplog.text

    def test_request_payment_logs_idempotency_hit(
        self, service: PaymentService, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that idempotency hits are logged."""
        # First request
        service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345",
        )

        # Second request with same key
        with caplog.at_level(logging.INFO):
            caplog.clear()
            service.request_payment(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345",
            )

        assert "Returning existing payment" in caplog.text


class TestPaymentServiceGetPayment:
    """Tests for PaymentService.get_payment method."""

    @pytest.fixture
    def repository(self) -> InMemoryPaymentRepository:
        """Create a fresh repository for each test."""
        return InMemoryPaymentRepository()

    @pytest.fixture
    def service(
        self, repository: InMemoryPaymentRepository
    ) -> PaymentService:
        """Create PaymentService with repository."""
        return PaymentService(repository)

    @pytest.fixture
    def sample_payment(
        self, service: PaymentService
    ) -> Payment:
        """Create and save a sample payment."""
        return service.request_payment(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345678",
        )

    def test_get_payment_by_id_returns_payment(
        self, 
        service: PaymentService, 
        repository: InMemoryPaymentRepository,
        sample_payment: Payment
    ) -> None:
        """
        Test get_payment happy path.
        
        Save a payment, then get it by ID - should return the payment.
        """
        # Payment is already saved via sample_payment fixture
        assert repository.count() == 1
        
        # Get payment by ID
        found = service.get_payment(sample_payment.payment_id)

        # Verify payment is returned
        assert found is not None
        assert found.payment_id == sample_payment.payment_id
        assert found.amount_minor == sample_payment.amount_minor
        assert found.currency == sample_payment.currency
        assert found.order_id == sample_payment.order_id

    def test_get_nonexistent_payment_returns_none(
        self, service: PaymentService
    ) -> None:
        """
        Test get_payment with non-existent ID.
        
        Getting a payment that doesn't exist should return None.
        """
        payment = service.get_payment("non-existent-payment-id-12345")

        assert payment is None

    def test_get_payment_existing(
        self, service: PaymentService, sample_payment: Payment
    ) -> None:
        """Test retrieving an existing payment."""
        payment = service.get_payment(sample_payment.payment_id)

        assert payment is not None
        assert payment.payment_id == sample_payment.payment_id
        assert payment.amount_minor == sample_payment.amount_minor

    def test_get_payment_nonexistent(self, service: PaymentService) -> None:
        """Test retrieving a nonexistent payment."""
        payment = service.get_payment("nonexistent-id")

        assert payment is None

    def test_get_payment_logs_success(
        self,
        service: PaymentService,
        sample_payment: Payment,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that successful retrieval is logged."""
        with caplog.at_level(logging.INFO):
            service.get_payment(sample_payment.payment_id)

        assert "Payment found" in caplog.text

    def test_get_payment_logs_not_found(
        self, service: PaymentService, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that not found is logged."""
        with caplog.at_level(logging.INFO):
            service.get_payment("nonexistent-id")

        assert "Payment not found" in caplog.text


class TestPaymentServiceErrorHandling:
    """Tests for PaymentService error handling."""

    def test_repository_save_error_propagates(self) -> None:
        """Test that repository save errors are propagated."""
        mock_repository = MagicMock()
        mock_repository.find_by_idempotency_key.return_value = None
        mock_repository.save.side_effect = Exception("Database error")

        service = PaymentService(mock_repository)

        with pytest.raises(Exception, match="Database error"):
            service.request_payment(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345",
            )

    def test_repository_find_error_propagates(self) -> None:
        """Test that repository find errors are propagated."""
        mock_repository = MagicMock()
        mock_repository.find_by_id.side_effect = Exception("Database error")

        service = PaymentService(mock_repository)

        with pytest.raises(Exception, match="Database error"):
            service.get_payment("some-payment-id")

    def test_validation_errors_are_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that validation errors are logged as warnings."""
        repository = InMemoryPaymentRepository()
        service = PaymentService(repository)

        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError):
                service.request_payment(
                    amount_minor=-100,
                    currency="USD",
                    order_id="order-123",
                    idempotency_key="idem-key-12345",
                )

        assert "validation failed" in caplog.text.lower()

