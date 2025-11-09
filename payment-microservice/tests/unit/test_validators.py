"""Unit tests for payment validators."""

import pytest

from payments_service.domain import (
    validate_amount,
    validate_currency,
    validate_idempotency_key,
    validate_order_id,
    validate_payment_request,
)


class TestValidateAmount:
    """Tests for validate_amount function."""

    def test_positive_amount_is_valid(self) -> None:
        """Test that positive amounts pass validation."""
        validate_amount(1)
        validate_amount(100)
        validate_amount(1250)
        validate_amount(999999)
        # Should not raise any exception

    def test_zero_amount_raises_error(self) -> None:
        """Test that zero amount raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_amount(0)

    def test_negative_amount_raises_error(self) -> None:
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            validate_amount(-100)

    def test_error_message_includes_amount(self) -> None:
        """Test that error message includes the invalid amount."""
        with pytest.raises(ValueError, match="-500"):
            validate_amount(-500)


class TestValidateCurrency:
    """Tests for validate_currency function."""

    def test_supported_currencies_are_valid(self) -> None:
        """Test that all supported currencies pass validation."""
        for currency in ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]:
            validate_currency(currency)
            # Should not raise any exception

    def test_case_insensitive_validation(self) -> None:
        """Test that currency validation is case-insensitive."""
        validate_currency("usd")
        validate_currency("Eur")
        validate_currency("gbp")
        validate_currency("JPY")
        # Should not raise any exception

    def test_unsupported_currency_raises_error(self) -> None:
        """Test that unsupported currency raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported currency"):
            validate_currency("XXX")

    def test_error_message_lists_allowed_currencies(self) -> None:
        """Test that error message lists allowed currencies."""
        with pytest.raises(ValueError, match="Allowed currencies"):
            validate_currency("BTC")

    def test_empty_currency_raises_error(self) -> None:
        """Test that empty currency raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_currency("")

    def test_invalid_currency_codes(self) -> None:
        """Test various invalid currency codes."""
        invalid_currencies = ["US", "USDD", "123", "BTC", "CHF", "CNY"]
        for currency in invalid_currencies:
            with pytest.raises(ValueError):
                validate_currency(currency)


class TestValidateIdempotencyKey:
    """Tests for validate_idempotency_key function."""

    def test_valid_idempotency_keys(self) -> None:
        """Test that valid idempotency keys pass validation."""
        validate_idempotency_key("12345678")
        validate_idempotency_key("abcd-1234-efgh-5678")
        validate_idempotency_key("a" * 100)
        # Should not raise any exception

    def test_none_key_raises_error(self) -> None:
        """Test that None key raises ValueError."""
        with pytest.raises(ValueError, match="cannot be None"):
            validate_idempotency_key(None)

    def test_empty_key_raises_error(self) -> None:
        """Test that empty key raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_idempotency_key("")

    def test_too_short_key_raises_error(self) -> None:
        """Test that keys shorter than minimum length raise ValueError."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_idempotency_key("short")

    def test_minimum_length_boundary(self) -> None:
        """Test boundary condition for minimum length."""
        # 7 chars - should fail
        with pytest.raises(ValueError):
            validate_idempotency_key("1234567")

        # 8 chars - should pass
        validate_idempotency_key("12345678")

    def test_error_message_includes_length(self) -> None:
        """Test that error message includes actual length."""
        with pytest.raises(ValueError, match="got 5"):
            validate_idempotency_key("12345")


class TestValidateOrderId:
    """Tests for validate_order_id function."""

    def test_valid_order_ids(self) -> None:
        """Test that valid order IDs pass validation."""
        validate_order_id("order-123")
        validate_order_id("ORD_12345")
        validate_order_id("a")
        # Should not raise any exception

    def test_none_order_id_raises_error(self) -> None:
        """Test that None order_id raises ValueError."""
        with pytest.raises(ValueError, match="cannot be None"):
            validate_order_id(None)

    def test_empty_order_id_raises_error(self) -> None:
        """Test that empty order_id raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_order_id("")


class TestValidatePaymentRequest:
    """Tests for validate_payment_request function."""

    def test_all_valid_fields_pass(self) -> None:
        """Test that valid payment request passes all validations."""
        validate_payment_request(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345",
        )
        # Should not raise any exception

    def test_invalid_amount_raises_error(self) -> None:
        """Test that invalid amount raises ValueError with context."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_payment_request(
                amount_minor=-100,
                currency="USD",
                order_id="order-123",
                idempotency_key="idem-key-12345",
            )

    def test_invalid_currency_raises_error(self) -> None:
        """Test that invalid currency raises ValueError with context."""
        with pytest.raises(ValueError, match="Invalid currency"):
            validate_payment_request(
                amount_minor=1250,
                currency="XXX",
                order_id="order-123",
                idempotency_key="idem-key-12345",
            )

    def test_invalid_order_id_raises_error(self) -> None:
        """Test that invalid order_id raises ValueError with context."""
        with pytest.raises(ValueError, match="Invalid order ID"):
            validate_payment_request(
                amount_minor=1250,
                currency="USD",
                order_id="",
                idempotency_key="idem-key-12345",
            )

    def test_invalid_idempotency_key_raises_error(self) -> None:
        """Test that invalid idempotency_key raises ValueError with context."""
        with pytest.raises(ValueError, match="Invalid idempotency key"):
            validate_payment_request(
                amount_minor=1250,
                currency="USD",
                order_id="order-123",
                idempotency_key="short",
            )

    def test_multiple_invalid_fields_reports_first_error(self) -> None:
        """Test that first validation error is reported."""
        # Amount is checked first, so should get amount error
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_payment_request(
                amount_minor=-100,
                currency="XXX",
                order_id="",
                idempotency_key="",
            )

    def test_case_insensitive_currency_in_full_validation(self) -> None:
        """Test that currency is case-insensitive in full validation."""
        validate_payment_request(
            amount_minor=1250,
            currency="usd",
            order_id="order-123",
            idempotency_key="idem-key-12345",
        )
        # Should not raise any exception

    def test_various_valid_combinations(self) -> None:
        """Test various valid payment request combinations."""
        test_cases = [
            (1, "EUR", "ord-1", "12345678"),
            (999999, "GBP", "order-abc-123", "key-" + "x" * 20),
            (100, "jpy", "ORDER_999", "idem_key_123456"),
        ]

        for amount, currency, order_id, idem_key in test_cases:
            validate_payment_request(
                amount_minor=amount,
                currency=currency,
                order_id=order_id,
                idempotency_key=idem_key,
            )
            # Should not raise any exception

