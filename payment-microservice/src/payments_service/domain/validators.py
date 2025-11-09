"""Payment request validation functions."""

from typing import Optional

# Allowed ISO 4217 currency codes
ALLOWED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD"}

# Minimum length for idempotency keys
MIN_IDEMPOTENCY_KEY_LENGTH = 8


def validate_amount(amount_minor: int) -> None:
    """
    Validate payment amount in minor units (cents).

    Args:
        amount_minor: Amount in minor units (e.g., cents for USD)

    Raises:
        ValueError: If amount is not positive
    """
    if amount_minor <= 0:
        raise ValueError(
            f"Payment amount must be positive, got {amount_minor} minor units. "
            "Amount should be specified in cents (e.g., 1250 for $12.50)."
        )


def validate_currency(currency: str) -> None:
    """
    Validate currency code against allowed ISO 4217 codes.

    Supported currencies: USD, EUR, GBP, JPY, CAD, AUD

    Args:
        currency: ISO 4217 currency code (case-insensitive)

    Raises:
        ValueError: If currency is not in the allowed list
    """
    if not currency:
        raise ValueError("Currency code cannot be empty")

    currency_upper = currency.upper()

    if currency_upper not in ALLOWED_CURRENCIES:
        allowed_list = ", ".join(sorted(ALLOWED_CURRENCIES))
        raise ValueError(
            f"Unsupported currency '{currency}'. "
            f"Allowed currencies: {allowed_list}"
        )


def validate_idempotency_key(key: Optional[str]) -> None:
    """
    Validate idempotency key for request deduplication.

    Args:
        key: Idempotency key string

    Raises:
        ValueError: If key is None, empty, or too short
    """
    if key is None:
        raise ValueError("Idempotency key cannot be None")

    if not key:
        raise ValueError("Idempotency key cannot be empty")

    if len(key) < MIN_IDEMPOTENCY_KEY_LENGTH:
        raise ValueError(
            f"Idempotency key must be at least {MIN_IDEMPOTENCY_KEY_LENGTH} "
            f"characters long, got {len(key)}"
        )


def validate_order_id(order_id: Optional[str]) -> None:
    """
    Validate order ID.

    Args:
        order_id: Order identifier string

    Raises:
        ValueError: If order_id is None or empty
    """
    if order_id is None:
        raise ValueError("Order ID cannot be None")

    if not order_id:
        raise ValueError("Order ID cannot be empty")


def validate_payment_request(
    amount_minor: int,
    currency: str,
    order_id: str,
    idempotency_key: str,
) -> None:
    """
    Validate all required fields for a payment request.

    This is a convenience function that validates all payment request fields
    by calling individual validators. If any validation fails, it raises
    a ValueError with a clear error message.

    Args:
        amount_minor: Amount in minor units (cents)
        currency: ISO 4217 currency code
        order_id: Associated order identifier
        idempotency_key: Unique key for idempotent request handling

    Raises:
        ValueError: If any validation check fails with a descriptive message

    Example:
        >>> validate_payment_request(1250, "USD", "order-123", "key-abc123")
        >>> # Returns None if all validations pass
        >>>
        >>> validate_payment_request(-100, "USD", "order-123", "key-abc123")
        ValueError: Payment amount must be positive...
    """
    try:
        validate_amount(amount_minor)
    except ValueError as e:
        raise ValueError(f"Invalid amount: {e}") from e

    try:
        validate_currency(currency)
    except ValueError as e:
        raise ValueError(f"Invalid currency: {e}") from e

    try:
        validate_order_id(order_id)
    except ValueError as e:
        raise ValueError(f"Invalid order ID: {e}") from e

    try:
        validate_idempotency_key(idempotency_key)
    except ValueError as e:
        raise ValueError(f"Invalid idempotency key: {e}") from e

