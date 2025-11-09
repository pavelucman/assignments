"""In-memory implementation of PaymentRepository."""

from threading import Lock
from typing import Optional

from payments_service.domain import Payment
from payments_service.storage.repository import PaymentRepository


class InMemoryPaymentRepository(PaymentRepository):
    """
    Thread-safe in-memory implementation of PaymentRepository.

    Uses two dictionaries for efficient lookup by payment ID and idempotency key.
    Thread-safe for concurrent access using a threading.Lock.

    Useful for testing and development. Not suitable for production as
    data is lost when the process terminates.
    """

    def __init__(self) -> None:
        """Initialize empty storage dictionaries and thread lock."""
        self._payments_by_id: dict[str, Payment] = {}
        self._payments_by_idempotency: dict[str, Payment] = {}
        self._lock = Lock()

    def save(self, payment: Payment) -> Payment:
        """
        Store a payment in memory (thread-safe).

        Stores the payment in both dictionaries for efficient lookup
        by payment ID and idempotency key.

        Args:
            payment: Payment instance to store

        Returns:
            The saved Payment instance

        Thread Safety:
            This method is thread-safe and can be called concurrently
            from multiple threads.
        """
        with self._lock:
            self._payments_by_id[payment.payment_id] = payment
            self._payments_by_idempotency[payment.idempotency_key] = payment
            return payment

    def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """
        Retrieve a payment by its unique identifier (thread-safe).

        Args:
            payment_id: Unique payment identifier (UUID)

        Returns:
            Payment instance if found, None otherwise

        Thread Safety:
            This method is thread-safe and can be called concurrently
            from multiple threads.
        """
        with self._lock:
            return self._payments_by_id.get(payment_id)

    def find_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[Payment]:
        """
        Retrieve a payment by its idempotency key (thread-safe).

        Used to prevent duplicate payment processing by checking if a payment
        with the same idempotency key already exists.

        Args:
            idempotency_key: Unique idempotency key from the request

        Returns:
            Payment instance if found, None otherwise

        Thread Safety:
            This method is thread-safe and can be called concurrently
            from multiple threads.
        """
        with self._lock:
            return self._payments_by_idempotency.get(idempotency_key)

    def clear(self) -> None:
        """
        Clear all stored payments (useful for testing).

        Thread Safety:
            This method is thread-safe and can be called concurrently
            from multiple threads.
        """
        with self._lock:
            self._payments_by_id.clear()
            self._payments_by_idempotency.clear()

    def count(self) -> int:
        """
        Return the number of stored payments (useful for testing).

        Thread Safety:
            This method is thread-safe and can be called concurrently
            from multiple threads.
        """
        with self._lock:
            return len(self._payments_by_id)

