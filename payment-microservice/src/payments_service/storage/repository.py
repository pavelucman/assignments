"""Payment repository abstract base class."""

from abc import ABC, abstractmethod
from typing import Optional

from payments_service.domain import Payment


class PaymentRepository(ABC):
    """
    Abstract base class for payment storage operations.

    Defines the interface for payment persistence, allowing different
    storage implementations (in-memory, database, etc.) while maintaining
    a consistent API.
    """

    @abstractmethod
    def save(self, payment: Payment) -> Payment:
        """
        Store a payment and return the saved instance.

        Args:
            payment: Payment instance to store

        Returns:
            The saved Payment instance

        Raises:
            Exception: Implementation-specific storage errors
        """
        ...

    @abstractmethod
    def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """
        Retrieve a payment by its unique identifier.

        Args:
            payment_id: Unique payment identifier (UUID)

        Returns:
            Payment instance if found, None otherwise
        """
        ...

    @abstractmethod
    def find_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[Payment]:
        """
        Retrieve a payment by its idempotency key.

        Used to prevent duplicate payment processing by checking if a payment
        with the same idempotency key already exists.

        Args:
            idempotency_key: Unique idempotency key from the request

        Returns:
            Payment instance if found, None otherwise
        """
        ...

