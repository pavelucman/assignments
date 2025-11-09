"""Payment service for handling payment business logic."""

import logging
from typing import Optional

from payments_service.domain import Payment, validate_payment_request
from payments_service.storage import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for handling payment operations and business logic.

    Orchestrates payment creation, validation, and retrieval while ensuring
    idempotency and proper error handling.
    """

    def __init__(self, repository: PaymentRepository) -> None:
        """
        Initialize PaymentService with a repository.

        Args:
            repository: Payment repository for storage operations
        """
        self._repository = repository
        logger.info("PaymentService initialized")

    def request_payment(
        self,
        amount_minor: int,
        currency: str,
        order_id: str,
        idempotency_key: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> Payment:
        """
        Request a new payment with idempotency support.

        This method validates the input, checks for duplicate requests using
        the idempotency key, and creates a new payment if none exists.

        Args:
            amount_minor: Amount in minor units (cents)
            currency: ISO 4217 currency code (e.g., 'USD', 'EUR')
            order_id: Associated order identifier
            idempotency_key: Unique key for idempotent request handling
            metadata: Optional key-value metadata

        Returns:
            Payment instance (either newly created or existing)

        Raises:
            ValueError: If validation fails

        Example:
            >>> service = PaymentService(repository)
            >>> payment = service.request_payment(
            ...     amount_minor=1250,
            ...     currency="USD",
            ...     order_id="order-123",
            ...     idempotency_key="idem-key-12345",
            ...     metadata={"user_id": "user-789"}
            ... )
        """
        logger.info(
            "Payment request received",
            extra={
                "amount_minor": amount_minor,
                "currency": currency,
                "order_id": order_id,
                "idempotency_key": idempotency_key,
            },
        )

        # Validate all inputs
        try:
            validate_payment_request(
                amount_minor=amount_minor,
                currency=currency,
                order_id=order_id,
                idempotency_key=idempotency_key,
            )
            logger.debug("Payment request validation passed")
        except ValueError as e:
            logger.warning(
                f"Payment request validation failed: {e}",
                extra={"idempotency_key": idempotency_key},
            )
            raise

        # Check for existing payment (idempotency)
        existing_payment = self._repository.find_by_idempotency_key(
            idempotency_key
        )
        if existing_payment:
            logger.info(
                "Returning existing payment for idempotency key",
                extra={
                    "payment_id": existing_payment.payment_id,
                    "idempotency_key": idempotency_key,
                    "status": existing_payment.status.value,
                },
            )
            return existing_payment

        # Create new payment
        try:
            payment = Payment.create(
                amount_minor=amount_minor,
                currency=currency,
                order_id=order_id,
                idempotency_key=idempotency_key,
                metadata=metadata,
            )
            logger.debug(
                f"Payment created with ID: {payment.payment_id}",
                extra={"payment_id": payment.payment_id},
            )
        except Exception as e:
            logger.error(
                f"Failed to create payment: {e}",
                extra={"idempotency_key": idempotency_key},
            )
            raise

        # Save payment
        try:
            saved_payment = self._repository.save(payment)
            logger.info(
                "Payment saved successfully",
                extra={
                    "payment_id": saved_payment.payment_id,
                    "amount_minor": saved_payment.amount_minor,
                    "currency": saved_payment.currency,
                    "status": saved_payment.status.value,
                },
            )
            return saved_payment
        except Exception as e:
            logger.error(
                f"Failed to save payment: {e}",
                extra={
                    "payment_id": payment.payment_id,
                    "idempotency_key": idempotency_key,
                },
            )
            raise

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """
        Retrieve a payment by its unique identifier.

        Args:
            payment_id: Unique payment identifier (UUID)

        Returns:
            Payment instance if found, None otherwise

        Example:
            >>> service = PaymentService(repository)
            >>> payment = service.get_payment("550e8400-e29b-41d4-a716-446655440000")
        """
        logger.debug(
            "Payment retrieval requested", extra={"payment_id": payment_id}
        )

        try:
            payment = self._repository.find_by_id(payment_id)

            if payment:
                logger.info(
                    "Payment found",
                    extra={
                        "payment_id": payment_id,
                        "status": payment.status.value,
                    },
                )
            else:
                logger.info(
                    "Payment not found", extra={"payment_id": payment_id}
                )

            return payment
        except Exception as e:
            logger.error(
                f"Error retrieving payment: {e}",
                extra={"payment_id": payment_id},
            )
            raise

