#!/usr/bin/env python3
"""
Demo Test Client for Payment gRPC Service

This script demonstrates all payment service functionality with clear visual output.
Perfect for demos and quick testing.
"""

import sys
import os
import time
from datetime import datetime

import grpc

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from payments_service.payments_pb2 import (
    RequestPaymentRequest,
    GetPaymentRequest,
    HealthRequest,
)
from payments_service.payments_pb2_grpc import PaymentServiceStub


# ANSI color codes for pretty output
class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")


def print_success(text: str) -> None:
    """Print a success message with checkmark."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def print_field(label: str, value: str) -> None:
    """Print a labeled field."""
    print(f"  {Colors.BOLD}{label}:{Colors.END} {value}")


def test_health_check(client: PaymentServiceStub) -> bool:
    """Test the Health RPC endpoint."""
    print_header("Test 1: Health Check")
    
    try:
        print_info("Sending Health request...")
        response = client.Health(HealthRequest())
        
        print_success(f"Health check passed: {response.status}")
        print_field("Status", response.status)
        return True
        
    except grpc.RpcError as e:
        print_error(f"Health check failed: {e.code()}")
        print_field("Error", str(e.details()))
        return False


def test_create_payment(client: PaymentServiceStub) -> tuple[bool, str]:
    """Test creating a new payment."""
    print_header("Test 2: Create Payment (RequestPayment)")
    
    try:
        print_info("Creating payment request...")
        
        request = RequestPaymentRequest(
            amount_minor=1250,  # $12.50
            currency="USD",
            order_id="order-demo-001",
            idempotency_key="demo-key-12345678",
            metadata={
                "customer_id": "cust-789",
                "product": "Widget Pro",
                "quantity": "2",
            },
        )
        
        print_info("Request details:")
        print_field("Amount", f"${request.amount_minor / 100:.2f} {request.currency}")
        print_field("Order ID", request.order_id)
        print_field("Idempotency Key", request.idempotency_key)
        print_field("Metadata", str(dict(request.metadata)))
        
        print_info("\nSending RequestPayment RPC...")
        response = client.RequestPayment(request)
        
        print_success("Payment created successfully!")
        print_field("Payment ID", response.payment_id)
        print_field("Status", f"{response.status}")
        print_field("Message", response.message)
        print_field("Idempotency Key", response.idempotency_key)
        
        # Format timestamp
        created_at = datetime.fromtimestamp(
            response.created_at.seconds + response.created_at.nanos / 1e9
        )
        print_field("Created At", created_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        return True, response.payment_id
        
    except grpc.RpcError as e:
        print_error(f"Payment creation failed: {e.code()}")
        print_field("Error", str(e.details()))
        return False, ""


def test_idempotency(client: PaymentServiceStub) -> bool:
    """Test idempotency by sending duplicate request."""
    print_header("Test 3: Idempotency (Duplicate Request)")
    
    try:
        idempotency_key = "idempotent-test-key-001"
        
        print_info("Sending first payment request...")
        request1 = RequestPaymentRequest(
            amount_minor=5000,
            currency="USD",
            order_id="order-idem-001",
            idempotency_key=idempotency_key,
        )
        
        response1 = client.RequestPayment(request1)
        payment_id_1 = response1.payment_id
        print_success(f"First payment created: {payment_id_1}")
        
        print_info("\nSending DUPLICATE request (same idempotency key)...")
        time.sleep(0.5)  # Small delay for effect
        
        request2 = RequestPaymentRequest(
            amount_minor=5000,
            currency="USD",
            order_id="order-idem-001",
            idempotency_key=idempotency_key,
        )
        
        response2 = client.RequestPayment(request2)
        payment_id_2 = response2.payment_id
        
        if payment_id_1 == payment_id_2:
            print_success("Idempotency working correctly!")
            print_field("First Payment ID", payment_id_1)
            print_field("Second Payment ID", payment_id_2)
            print_success("Both requests returned the SAME payment (no duplicate!)")
            return True
        else:
            print_error("Idempotency FAILED!")
            print_field("First Payment ID", payment_id_1)
            print_field("Second Payment ID", payment_id_2)
            print_error("Different payment IDs returned (duplicate created!)")
            return False
        
    except grpc.RpcError as e:
        print_error(f"Idempotency test failed: {e.code()}")
        print_field("Error", str(e.details()))
        return False


def test_get_payment(client: PaymentServiceStub, payment_id: str) -> bool:
    """Test retrieving an existing payment."""
    print_header("Test 4: Get Payment (GetPayment)")
    
    try:
        print_info(f"Retrieving payment: {payment_id}")
        
        request = GetPaymentRequest(payment_id=payment_id)
        response = client.GetPayment(request)
        
        print_success("Payment retrieved successfully!")
        print_field("Payment ID", response.payment_id)
        print_field("Status", f"{response.status}")
        print_field("Amount", f"${response.amount_minor / 100:.2f} {response.currency}")
        print_field("Order ID", response.order_id)
        print_field("Idempotency Key", response.idempotency_key)
        print_field("Message", response.message)
        
        created_at = datetime.fromtimestamp(
            response.created_at.seconds + response.created_at.nanos / 1e9
        )
        print_field("Created At", created_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        return True
        
    except grpc.RpcError as e:
        print_error(f"Get payment failed: {e.code()}")
        print_field("Error", str(e.details()))
        return False


def test_payment_not_found(client: PaymentServiceStub) -> bool:
    """Test retrieving a non-existent payment."""
    print_header("Test 5: Get Non-Existent Payment (Error Handling)")
    
    try:
        fake_id = "00000000-0000-0000-0000-000000000000"
        print_info(f"Attempting to retrieve non-existent payment: {fake_id}")
        
        request = GetPaymentRequest(payment_id=fake_id)
        response = client.GetPayment(request)
        
        print_error("Expected NOT_FOUND error, but request succeeded!")
        return False
        
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            print_success("Error handling working correctly!")
            print_field("Status Code", str(e.code()))
            print_field("Error Message", str(e.details()))
            return True
        else:
            print_error(f"Unexpected error code: {e.code()}")
            print_field("Error", str(e.details()))
            return False


def test_invalid_amount(client: PaymentServiceStub) -> bool:
    """Test validation with invalid amount."""
    print_header("Test 6: Input Validation (Invalid Amount)")
    
    try:
        print_info("Sending request with invalid amount (negative)...")
        
        request = RequestPaymentRequest(
            amount_minor=-1000,  # Invalid: negative
            currency="USD",
            order_id="order-invalid-001",
            idempotency_key="invalid-amount-key-001",
        )
        
        response = client.RequestPayment(request)
        
        print_error("Expected INVALID_ARGUMENT error, but request succeeded!")
        return False
        
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
            print_success("Validation working correctly!")
            print_field("Status Code", str(e.code()))
            print_field("Error Message", str(e.details()))
            return True
        else:
            print_error(f"Unexpected error code: {e.code()}")
            print_field("Error", str(e.details()))
            return False


def test_invalid_currency(client: PaymentServiceStub) -> bool:
    """Test validation with invalid currency."""
    print_header("Test 7: Input Validation (Invalid Currency)")
    
    try:
        print_info("Sending request with invalid currency...")
        
        request = RequestPaymentRequest(
            amount_minor=1000,
            currency="INVALID",  # Invalid: not in allowed list
            order_id="order-invalid-002",
            idempotency_key="invalid-currency-key-001",
        )
        
        response = client.RequestPayment(request)
        
        print_error("Expected INVALID_ARGUMENT error, but request succeeded!")
        return False
        
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
            print_success("Currency validation working correctly!")
            print_field("Status Code", str(e.code()))
            print_field("Error Message", str(e.details()))
            return True
        else:
            print_error(f"Unexpected error code: {e.code()}")
            print_field("Error", str(e.details()))
            return False


def test_multiple_currencies(client: PaymentServiceStub) -> bool:
    """Test creating payments in different currencies."""
    print_header("Test 8: Multi-Currency Support")
    
    currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
    amounts = [1000, 2000, 3000, 4000, 5000, 6000]
    
    print_info("Creating payments in multiple currencies...\n")
    
    all_success = True
    for currency, amount in zip(currencies, amounts):
        try:
            request = RequestPaymentRequest(
                amount_minor=amount,
                currency=currency,
                order_id=f"order-{currency.lower()}-001",
                idempotency_key=f"multi-curr-{currency.lower()}-key",
            )
            
            response = client.RequestPayment(request)
            
            if currency == "JPY":
                # JPY doesn't have minor units
                formatted_amount = f"¥{amount}"
            else:
                formatted_amount = f"{amount / 100:.2f} {currency}"
            
            print_success(f"{currency}: {formatted_amount} - ID: {response.payment_id[:8]}...")
            
        except grpc.RpcError as e:
            print_error(f"{currency}: Failed - {e.details()}")
            all_success = False
    
    if all_success:
        print_success("\nAll currencies processed successfully!")
    
    return all_success


def print_summary(results: dict) -> None:
    """Print test summary."""
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n{Colors.BOLD}Total Tests:{Colors.END} {total}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {passed}")
    print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {failed}")
    
    print(f"\n{Colors.BOLD}Details:{Colors.END}\n")
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"  {test_name}: {status}")
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate:{Colors.END} {success_rate:.1f}%")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! 🎉{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed{Colors.END}\n")


def main():
    """Run all tests."""
    # Get server address from environment or use default
    server = os.getenv("GRPC_SERVER", "localhost:7000")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}Payment gRPC Service - Demo Test Client{Colors.END}")
    print(f"{Colors.BOLD}Server:{Colors.END} {server}\n")
    
    # Create gRPC channel
    try:
        print_info(f"Connecting to {server}...")
        channel = grpc.insecure_channel(server)
        client = PaymentServiceStub(channel)
        print_success("Connected successfully!\n")
    except Exception as e:
        print_error(f"Failed to connect to server: {e}")
        print_info("\nMake sure the server is running:")
        print_info("  docker-compose up")
        print_info("  OR")
        print_info("  make run")
        sys.exit(1)
    
    # Run all tests
    results = {}
    payment_id = ""
    
    try:
        # Test 1: Health Check
        results["Health Check"] = test_health_check(client)
        time.sleep(0.3)
        
        # Test 2: Create Payment
        success, payment_id = test_create_payment(client)
        results["Create Payment"] = success
        time.sleep(0.3)
        
        # Test 3: Idempotency
        results["Idempotency"] = test_idempotency(client)
        time.sleep(0.3)
        
        # Test 4: Get Payment (only if we have a payment_id)
        if payment_id:
            results["Get Payment"] = test_get_payment(client, payment_id)
            time.sleep(0.3)
        
        # Test 5: Payment Not Found
        results["Error Handling (Not Found)"] = test_payment_not_found(client)
        time.sleep(0.3)
        
        # Test 6: Invalid Amount
        results["Validation (Invalid Amount)"] = test_invalid_amount(client)
        time.sleep(0.3)
        
        # Test 7: Invalid Currency
        results["Validation (Invalid Currency)"] = test_invalid_currency(client)
        time.sleep(0.3)
        
        # Test 8: Multiple Currencies
        results["Multi-Currency Support"] = test_multiple_currencies(client)
        
    finally:
        # Always print summary
        print_summary(results)
        channel.close()
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()

