"""Payment domain model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Payment:
    """
    Payment domain model representing a payment transaction.

    Immutable dataclass ensuring payment data integrity.
    """

    payment_id: str
    amount_minor: int  # Amount in minor units (cents)
    currency: str  # ISO 4217 currency code
    order_id: str
    idempotency_key: str
    status: PaymentStatus
    message: str
    created_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate payment data after initialization."""
        if self.amount_minor <= 0:
            raise ValueError(
                f"amount_minor must be positive, got {self.amount_minor}"
            )

        if len(self.currency) != 3:
            raise ValueError(
                f"currency must be a 3-letter ISO 4217 code, got '{self.currency}'"
            )

        if not self.currency.isupper():
            raise ValueError(
                f"currency must be uppercase, got '{self.currency}'"
            )

        if not self.order_id:
            raise ValueError("order_id cannot be empty")

        if not self.idempotency_key:
            raise ValueError("idempotency_key cannot be empty")

    @classmethod
    def create(
        cls,
        amount_minor: int,
        currency: str,
        order_id: str,
        idempotency_key: str,
        message: str = "",
        metadata: Optional[dict[str, str]] = None,
    ) -> "Payment":
        """
        Factory method to create a new payment with generated ID and timestamp.

        Args:
            amount_minor: Amount in minor units (cents)
            currency: ISO 4217 currency code (e.g., 'USD', 'EUR')
            order_id: Associated order identifier
            idempotency_key: Unique key for idempotent request handling
            message: Human-readable message (defaults to empty string)
            metadata: Optional key-value metadata (defaults to empty dict)

        Returns:
            New Payment instance with PENDING status

        Raises:
            ValueError: If validation fails
        """
        return cls(
            payment_id=str(uuid4()),
            amount_minor=amount_minor,
            currency=currency.upper(),
            order_id=order_id,
            idempotency_key=idempotency_key,
            status=PaymentStatus.PENDING,
            message=message or "Payment initiated",
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    def with_status(
        self, status: PaymentStatus, message: str
    ) -> "Payment":
        """
        Create a new Payment instance with updated status and message.

        Since Payment is immutable, this returns a new instance.

        Args:
            status: New payment status
            message: Updated human-readable message

        Returns:
            New Payment instance with updated status and message
        """
        # Use object.__setattr__ to update frozen dataclass
        from dataclasses import replace

        return replace(self, status=status, message=message)

    def mark_succeeded(self, message: str = "Payment successful") -> "Payment":
        """Mark payment as succeeded."""
        return self.with_status(PaymentStatus.SUCCEEDED, message)

    def mark_failed(self, message: str) -> "Payment":
        """Mark payment as failed with error message."""
        return self.with_status(PaymentStatus.FAILED, message)

    @property
    def amount_decimal(self) -> float:
        """Get amount as decimal value (e.g., 1250 cents -> 12.50)."""
        return self.amount_minor / 100.0

    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status == PaymentStatus.PENDING

    @property
    def is_succeeded(self) -> bool:
        """Check if payment succeeded."""
        return self.status == PaymentStatus.SUCCEEDED

    @property
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Payment({self.payment_id}, "
            f"{self.currency} {self.amount_decimal:.2f}, "
            f"{self.status.value})"
        )

