"""Example gRPC client for testing the payment service."""

import logging
import sys

import grpc

from payments_service.payments_pb2 import (
    GetPaymentRequest,
    HealthRequest,
    RequestPaymentRequest,
)
from payments_service.payments_pb2_grpc import PaymentServiceStub

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_client_example(host: str = "localhost", port: int = 7000) -> None:
    """
    Run example client demonstrating payment service usage.

    Args:
        host: Server host
        port: Server port
    """
    address = f"{host}:{port}"
    logger.info(f"Connecting to payment service at {address}...")

    # Create gRPC channel
    with grpc.insecure_channel(address) as channel:
        # Wait for channel to be ready
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            logger.info("✓ Connected to server")
        except grpc.FutureTimeoutError:
            logger.error("✗ Failed to connect to server (timeout)")
            sys.exit(1)

        # Create client stub
        client = PaymentServiceStub(channel)

        # 1. Health Check
        logger.info("\n=== Health Check ===")
        try:
            health_request = HealthRequest()
            health_response = client.Health(health_request)
            logger.info(f"✓ Health status: {health_response.status}")
        except grpc.RpcError as e:
            logger.error(f"✗ Health check failed: {e.details()}")

        # 2. Request Payment
        logger.info("\n=== Request Payment ===")
        try:
            payment_request = RequestPaymentRequest(
                amount_minor=1250,  # $12.50
                currency="USD",
                order_id="order-example-123",
                idempotency_key="example-key-12345678",
                metadata={
                    "user_id": "user-789",
                    "session_id": "session-abc123",
                },
            )
            logger.info("Requesting payment:")
            logger.info(f"  Amount: ${payment_request.amount_minor / 100:.2f}")
            logger.info(f"  Currency: {payment_request.currency}")
            logger.info(f"  Order ID: {payment_request.order_id}")
            logger.info(
                f"  Idempotency Key: {payment_request.idempotency_key}"
            )

            payment_response = client.RequestPayment(payment_request)

            logger.info("✓ Payment created:")
            logger.info(f"  Payment ID: {payment_response.payment_id}")
            logger.info(f"  Status: {payment_response.status}")
            logger.info(f"  Message: {payment_response.message}")
            logger.info(
                f"  Created At: {payment_response.created_at.ToDatetime()}"
            )

            payment_id = payment_response.payment_id

        except grpc.RpcError as e:
            logger.error(
                f"✗ Request payment failed: {e.code()} - {e.details()}"
            )
            return

        # 3. Get Payment
        logger.info("\n=== Get Payment ===")
        try:
            get_request = GetPaymentRequest(payment_id=payment_id)
            logger.info(f"Retrieving payment: {payment_id}")

            get_response = client.GetPayment(get_request)

            logger.info("✓ Payment retrieved:")
            logger.info(f"  Payment ID: {get_response.payment_id}")
            logger.info(f"  Amount: ${get_response.amount_minor / 100:.2f}")
            logger.info(f"  Currency: {get_response.currency}")
            logger.info(f"  Order ID: {get_response.order_id}")
            logger.info(f"  Status: {get_response.status}")
            logger.info(f"  Message: {get_response.message}")

        except grpc.RpcError as e:
            logger.error(f"✗ Get payment failed: {e.code()} - {e.details()}")

        # 4. Test Idempotency
        logger.info("\n=== Test Idempotency ===")
        try:
            # Same request as before
            duplicate_request = RequestPaymentRequest(
                amount_minor=1250,
                currency="USD",
                order_id="order-example-123",
                idempotency_key="example-key-12345678",
            )
            logger.info("Sending duplicate request with same idempotency key")

            duplicate_response = client.RequestPayment(duplicate_request)

            if duplicate_response.payment_id == payment_id:
                logger.info("✓ Idempotency working! Same payment returned:")
                logger.info(f"  Payment ID: {duplicate_response.payment_id}")
            else:
                logger.error(
                    "✗ Idempotency failed! Different payment returned"
                )

        except grpc.RpcError as e:
            logger.error(f"✗ Idempotency test failed: {e.details()}")

        # 5. Test Validation Error
        logger.info("\n=== Test Validation Error ===")
        try:
            invalid_request = RequestPaymentRequest(
                amount_minor=-100,  # Invalid: negative amount
                currency="USD",
                order_id="order-error",
                idempotency_key="error-key-12345678",
            )
            logger.info("Sending invalid request (negative amount)")

            client.RequestPayment(invalid_request)
            logger.error("✗ Validation should have failed!")

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                logger.info(f"✓ Validation error caught: {e.details()}")
            else:
                logger.error(f"✗ Unexpected error: {e.code()} - {e.details()}")

        # 6. Test Not Found Error
        logger.info("\n=== Test Not Found Error ===")
        try:
            not_found_request = GetPaymentRequest(
                payment_id="nonexistent-payment-id"
            )
            logger.info("Requesting nonexistent payment")

            client.GetPayment(not_found_request)
            logger.error("✗ Should have returned NOT_FOUND!")

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                logger.info(f"✓ Not found error caught: {e.details()}")
            else:
                logger.error(f"✗ Unexpected error: {e.code()} - {e.details()}")

        logger.info("\n=== Client Example Complete ===")


if __name__ == "__main__":
    import sys

    # Get host and port from command line if provided
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7000

    run_client_example(host, port)

