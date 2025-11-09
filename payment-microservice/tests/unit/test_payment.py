"""Unit tests for Payment domain model."""

from datetime import datetime, timezone

import pytest

from payments_service.domain import Payment, PaymentStatus


class TestPaymentCreation:
    """Tests for Payment creation and factory methods."""

    def test_create_payment_with_factory(self) -> None:
        """Test creating payment with factory method."""
        payment = Payment.create(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-456",
            message="Test payment",
            metadata={"user_id": "user-789"},
        )

        assert payment.amount_minor == 1250
        assert payment.currency == "USD"
        assert payment.order_id == "order-123"
        assert payment.idempotency_key == "idem-key-456"
        assert payment.status == PaymentStatus.PENDING
        assert payment.message == "Test payment"
        assert payment.metadata == {"user_id": "user-789"}
        assert payment.payment_id  # UUID should be generated
        assert isinstance(payment.created_at, datetime)

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

    def test_payment_is_immutable(self) -> None:
        """Test that Payment fields cannot be modified."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="key-123",
        )

        with pytest.raises(AttributeError):
            payment.amount_minor = 2000  # type: ignore[misc]


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

