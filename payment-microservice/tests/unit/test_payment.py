"""Unit tests for Payment domain model."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from payments_service.domain import Payment, PaymentStatus


@pytest.fixture
def valid_payment_data() -> dict:
    """Fixture providing valid payment data for tests."""
    return {
        "amount_minor": 1250,
        "currency": "USD",
        "order_id": "order-123",
        "idempotency_key": "idem-key-12345678",
    }


@pytest.fixture
def sample_payment(valid_payment_data: dict) -> Payment:
    """Fixture providing a sample payment instance."""
    return Payment.create(**valid_payment_data)


@pytest.fixture
def sample_metadata() -> dict[str, str]:
    """Fixture providing sample metadata."""
    return {
        "user_id": "user-789",
        "session_id": "session-abc123",
        "ip_address": "192.168.1.1",
    }


class TestPaymentCreation:
    """Tests for Payment creation and factory methods."""

    def test_create_payment_with_factory(
        self, valid_payment_data: dict, sample_metadata: dict[str, str]
    ) -> None:
        """
        Test creating payment with factory method.

        Verifies that all fields are properly set including:
        - All input fields
        - Generated payment_id (UUID)
        - Created timestamp
        - Default status (PENDING)
        - Custom message
        - Metadata dictionary
        """
        payment = Payment.create(
            **valid_payment_data,
            message="Test payment",
            metadata=sample_metadata,
        )

        # Verify all input fields
        assert payment.amount_minor == valid_payment_data["amount_minor"]
        assert payment.currency == valid_payment_data["currency"]
        assert payment.order_id == valid_payment_data["order_id"]
        assert payment.idempotency_key == valid_payment_data["idempotency_key"]
        
        # Verify status defaults to PENDING
        assert payment.status == PaymentStatus.PENDING
        
        # Verify custom fields
        assert payment.message == "Test payment"
        assert payment.metadata == sample_metadata
        
        # Verify generated fields
        assert payment.payment_id  # UUID should be generated
        assert isinstance(payment.created_at, datetime)

    def test_payment_id_is_valid_uuid(self, sample_payment: Payment) -> None:
        """
        Test that payment_id is a valid UUID.

        Ensures the generated payment_id follows UUID format.
        """
        # Should be able to parse as UUID without raising exception
        uuid_obj = UUID(sample_payment.payment_id)
        assert str(uuid_obj) == sample_payment.payment_id

    def test_created_at_is_set(self, sample_payment: Payment) -> None:
        """
        Test that created_at timestamp is set.

        Verifies:
        - created_at is a datetime object
        - created_at has timezone info (UTC)
        - created_at is recent (within last minute)
        """
        assert isinstance(sample_payment.created_at, datetime)
        assert sample_payment.created_at.tzinfo == timezone.utc
        
        # Should be recent (within last minute)
        now = datetime.now(timezone.utc)
        time_diff = (now - sample_payment.created_at).total_seconds()
        assert 0 <= time_diff < 60

    def test_status_defaults_to_pending(self, valid_payment_data: dict) -> None:
        """
        Test that status defaults to PENDING.

        New payments should always start with PENDING status.
        """
        payment = Payment.create(**valid_payment_data)
        assert payment.status == PaymentStatus.PENDING
        assert payment.is_pending is True

    def test_all_fields_properly_set(self, valid_payment_data: dict) -> None:
        """
        Test that all fields are properly set.

        Comprehensive check of all payment fields.
        """
        payment = Payment.create(**valid_payment_data)
        
        # Check all required fields
        assert payment.amount_minor == 1250
        assert payment.currency == "USD"
        assert payment.order_id == "order-123"
        assert payment.idempotency_key == "idem-key-12345678"
        assert payment.status == PaymentStatus.PENDING
        assert payment.payment_id is not None
        assert payment.created_at is not None
        assert payment.message == "Payment initiated"  # Default message
        assert payment.metadata == {}  # Default metadata

    def test_payment_with_metadata(
        self, valid_payment_data: dict, sample_metadata: dict[str, str]
    ) -> None:
        """
        Test creating payment with metadata dict.

        Metadata should be stored as-is and accessible.
        """
        payment = Payment.create(
            **valid_payment_data,
            metadata=sample_metadata,
        )

        assert payment.metadata == sample_metadata
        assert payment.metadata["user_id"] == "user-789"
        assert payment.metadata["session_id"] == "session-abc123"
        assert len(payment.metadata) == 3

    def test_payment_without_metadata(self, valid_payment_data: dict) -> None:
        """
        Test creating payment without metadata.

        When metadata is not provided, should default to empty dict.
        """
        payment = Payment.create(**valid_payment_data)

        assert payment.metadata == {}
        assert isinstance(payment.metadata, dict)
        assert len(payment.metadata) == 0

    def test_payment_with_empty_metadata_dict(
        self, valid_payment_data: dict
    ) -> None:
        """
        Test creating payment with explicit empty metadata dict.

        Should handle empty dict same as no metadata.
        """
        payment = Payment.create(
            **valid_payment_data,
            metadata={},
        )

        assert payment.metadata == {}

    def test_create_payment_normalizes_currency(self) -> None:
        """Test that currency is normalized to uppercase."""
        payment = Payment.create(
            amount_minor=1000,
            currency="usd",
            order_id="order-123",
            idempotency_key="idem-key-456",
        )

        assert payment.currency == "USD"

    def test_create_payment_with_defaults(self) -> None:
        """Test creating payment with default values."""
        payment = Payment.create(
            amount_minor=1000,
            currency="EUR",
            order_id="order-123",
            idempotency_key="idem-key-456",
        )

        assert payment.message == "Payment initiated"
        assert payment.metadata == {}

    def test_create_payment_generates_unique_ids(self) -> None:
        """Test that each payment gets a unique ID."""
        payment1 = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-1",
            idempotency_key="key-1",
        )
        payment2 = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-2",
            idempotency_key="key-2",
        )

        assert payment1.payment_id != payment2.payment_id


class TestPaymentValidation:
    """Tests for Payment validation."""

    def test_negative_amount_raises_error(self) -> None:
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="amount_minor must be positive"):
            Payment.create(
                amount_minor=-100,
                currency="USD",
                order_id="order-123",
                idempotency_key="key-123",
            )

    def test_zero_amount_raises_error(self) -> None:
        """Test that zero amount raises ValueError."""
        with pytest.raises(ValueError, match="amount_minor must be positive"):
            Payment.create(
                amount_minor=0,
                currency="USD",
                order_id="order-123",
                idempotency_key="key-123",
            )

    def test_invalid_currency_length_raises_error(self) -> None:
        """Test that invalid currency length raises ValueError."""
        with pytest.raises(ValueError, match="3-letter ISO 4217 code"):
            Payment.create(
                amount_minor=1000,
                currency="US",
                order_id="order-123",
                idempotency_key="key-123",
            )

    def test_lowercase_currency_in_direct_init_raises_error(self) -> None:
        """Test that lowercase currency in direct init raises ValueError."""
        with pytest.raises(ValueError, match="must be uppercase"):
            Payment(
                payment_id="test-id",
                amount_minor=1000,
                currency="usd",
                order_id="order-123",
                idempotency_key="key-123",
                status=PaymentStatus.PENDING,
                message="Test",
                created_at=datetime.now(timezone.utc),
            )

    def test_empty_order_id_raises_error(self) -> None:
        """Test that empty order_id raises ValueError."""
        with pytest.raises(ValueError, match="order_id cannot be empty"):
            Payment.create(
                amount_minor=1000,
                currency="USD",
                order_id="",
                idempotency_key="key-123",
            )

    def test_empty_idempotency_key_raises_error(self) -> None:
        """Test that empty idempotency_key raises ValueError."""
        with pytest.raises(ValueError, match="idempotency_key cannot be empty"):
            Payment.create(
                amount_minor=1000,
                currency="USD",
                order_id="order-123",
                idempotency_key="",
            )


class TestPaymentStatusTransitions:
    """Tests for Payment status transitions."""

    def test_mark_succeeded(self) -> None:
        """Test marking payment as succeeded."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        succeeded = payment.mark_succeeded("Payment processed successfully")

        assert succeeded.status == PaymentStatus.SUCCEEDED
        assert succeeded.message == "Payment processed successfully"
        assert succeeded.payment_id == payment.payment_id  # Same ID
        assert payment.status == PaymentStatus.PENDING  # Original unchanged

    def test_mark_failed(self) -> None:
        """Test marking payment as failed."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        failed = payment.mark_failed("Insufficient funds")

        assert failed.status == PaymentStatus.FAILED
        assert failed.message == "Insufficient funds"
        assert failed.payment_id == payment.payment_id  # Same ID
        assert payment.status == PaymentStatus.PENDING  # Original unchanged

    def test_with_status_creates_new_instance(self) -> None:
        """Test that with_status creates a new instance."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        updated = payment.with_status(PaymentStatus.SUCCEEDED, "Done")

        assert updated is not payment
        assert updated.status == PaymentStatus.SUCCEEDED
        assert payment.status == PaymentStatus.PENDING


class TestPaymentImmutability:
    """Tests for Payment immutability."""

    def test_payment_is_immutable(self, sample_payment: Payment) -> None:
        """
        Test that Payment is a frozen dataclass.

        Payment should be immutable - attempting to modify any field
        after creation should raise AttributeError.
        """
        with pytest.raises(AttributeError):
            sample_payment.amount_minor = 2000  # type: ignore[misc]

    def test_cannot_modify_payment_id(self, sample_payment: Payment) -> None:
        """Test that payment_id cannot be modified."""
        with pytest.raises(AttributeError):
            sample_payment.payment_id = "new-id"  # type: ignore[misc]

    def test_cannot_modify_status(self, sample_payment: Payment) -> None:
        """Test that status cannot be modified directly."""
        with pytest.raises(AttributeError):
            sample_payment.status = PaymentStatus.SUCCEEDED  # type: ignore[misc]

    def test_cannot_modify_metadata(self, sample_payment: Payment) -> None:
        """Test that metadata dict reference cannot be replaced."""
        with pytest.raises(AttributeError):
            sample_payment.metadata = {"new": "data"}  # type: ignore[misc]


class TestPaymentProperties:
    """Tests for Payment properties."""

    def test_amount_decimal(self) -> None:
        """Test amount_decimal property."""
        payment = Payment.create(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        assert payment.amount_decimal == 12.50

    def test_is_pending(self) -> None:
        """Test is_pending property."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        assert payment.is_pending is True
        assert payment.is_succeeded is False
        assert payment.is_failed is False

    def test_is_succeeded(self) -> None:
        """Test is_succeeded property."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        ).mark_succeeded()

        assert payment.is_pending is False
        assert payment.is_succeeded is True
        assert payment.is_failed is False

    def test_is_failed(self) -> None:
        """Test is_failed property."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        ).mark_failed("Error")

        assert payment.is_pending is False
        assert payment.is_succeeded is False
        assert payment.is_failed is True

    def test_string_representation(self) -> None:
        """Test string representation."""
        payment = Payment.create(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        str_repr = str(payment)
        assert "USD 12.50" in str_repr
        assert "PENDING" in str_repr
        assert payment.payment_id in str_repr

