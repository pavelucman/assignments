"""gRPC servicer implementation for PaymentService."""

import logging
from typing import Any

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from payments_service.app import PaymentService
from payments_service.domain import Payment, PaymentStatus
from payments_service.payments_pb2 import (
    GetPaymentResponse,
    HealthResponse,
    PaymentStatus as ProtoPaymentStatus,
    RequestPaymentResponse,
)
from payments_service.payments_pb2_grpc import PaymentServiceServicer

logger = logging.getLogger(__name__)


class PaymentServiceGrpcServicer(PaymentServiceServicer):
    """
    gRPC servicer implementation for PaymentService.

    Implements the gRPC service interface, handling request/response
    conversion and error handling with appropriate status codes.
    """

    def __init__(self, service: PaymentService) -> None:
        """
        Initialize the gRPC servicer.

        Args:
            service: PaymentService instance for business logic
        """
        self._service = service
        logger.info("PaymentServiceGrpcServicer initialized")

    def RequestPayment(
        self, request: Any, context: grpc.ServicerContext
    ) -> RequestPaymentResponse:
        """
        Handle RequestPayment gRPC call.

        Creates a new payment or returns an existing one based on
        idempotency key.

        Args:
            request: RequestPaymentRequest protobuf message
            context: gRPC service context

        Returns:
            RequestPaymentResponse protobuf message

        Raises:
            grpc.RpcError: With INVALID_ARGUMENT for validation errors,
                          INTERNAL for unexpected errors
        """
        logger.info(
            "RequestPayment RPC called",
            extra={
                "amount_minor": request.amount_minor,
                "currency": request.currency,
                "order_id": request.order_id,
                "idempotency_key": request.idempotency_key,
            },
        )

        try:
            # Extract metadata from protobuf map
            metadata = dict(request.metadata) if request.metadata else {}

            # Call business logic
            payment = self._service.request_payment(
                amount_minor=request.amount_minor,
                currency=request.currency,
                order_id=request.order_id,
                idempotency_key=request.idempotency_key,
                metadata=metadata,
            )

            # Convert to protobuf response
            response = self._payment_to_request_payment_response(payment)

            logger.info(
                "RequestPayment RPC completed successfully",
                extra={
                    "payment_id": payment.payment_id,
                    "status": payment.status.value,
                },
            )

            return response

        except ValueError as e:
            # Validation errors
            error_msg = f"Validation error: {str(e)}"
            logger.warning(
                error_msg,
                extra={"idempotency_key": request.idempotency_key},
            )
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, error_msg)

        except grpc.RpcError:
            # Re-raise gRPC errors (from context.abort) without catching them
            raise

        except Exception as e:
            # Unexpected errors only
            logger.error(
                f"RequestPayment RPC failed with unexpected error: {e}",
                extra={"idempotency_key": request.idempotency_key},
                exc_info=True,
            )
            context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal error processing payment request",
            )

    def GetPayment(
        self, request: Any, context: grpc.ServicerContext
    ) -> GetPaymentResponse:
        """
        Handle GetPayment gRPC call.

        Retrieves a payment by its unique identifier.

        Args:
            request: GetPaymentRequest protobuf message
            context: gRPC service context

        Returns:
            GetPaymentResponse protobuf message

        Raises:
            grpc.RpcError: With NOT_FOUND if payment doesn't exist,
                          INTERNAL for unexpected errors
        """
        logger.info(
            "GetPayment RPC called", extra={"payment_id": request.payment_id}
        )

        try:
            # Call business logic
            payment = self._service.get_payment(request.payment_id)

        except Exception as e:
            # Unexpected errors from service layer
            logger.error(
                f"GetPayment RPC failed with unexpected error: {e}",
                extra={"payment_id": request.payment_id},
                exc_info=True,
            )
            context.abort(
                grpc.StatusCode.INTERNAL,
                "Internal error retrieving payment",
            )

        # Check if payment was found (do this outside try-except to avoid catching abort exception)
        if payment is None:
            error_msg = f"Payment not found: {request.payment_id}"
            logger.info(error_msg)
            context.abort(grpc.StatusCode.NOT_FOUND, error_msg)

        # Convert to protobuf response
        response = self._payment_to_get_payment_response(payment)

        logger.info(
            "GetPayment RPC completed successfully",
            extra={
                "payment_id": payment.payment_id,
                "status": payment.status.value,
            },
        )

        return response

    def Health(
        self, request: Any, context: grpc.ServicerContext
    ) -> HealthResponse:
        """
        Handle Health gRPC call.

        Simple health check endpoint.

        Args:
            request: HealthRequest protobuf message
            context: gRPC service context

        Returns:
            HealthResponse with status="ok"
        """
        logger.debug("Health RPC called")

        response = HealthResponse(status="ok")

        logger.debug("Health RPC completed")

        return response

    def _payment_to_request_payment_response(
        self, payment: Payment
    ) -> RequestPaymentResponse:
        """
        Convert Payment domain model to RequestPaymentResponse protobuf.

        Args:
            payment: Payment domain model

        Returns:
            RequestPaymentResponse protobuf message
        """
        # Convert datetime to protobuf Timestamp
        timestamp = Timestamp()
        timestamp.FromDatetime(payment.created_at)

        # Convert status
        proto_status = self._domain_status_to_proto(payment.status)

        return RequestPaymentResponse(
            payment_id=payment.payment_id,
            status=proto_status,
            message=payment.message,
            idempotency_key=payment.idempotency_key,
            created_at=timestamp,
        )

    def _payment_to_get_payment_response(
        self, payment: Payment
    ) -> GetPaymentResponse:
        """
        Convert Payment domain model to GetPaymentResponse protobuf.

        Args:
            payment: Payment domain model

        Returns:
            GetPaymentResponse protobuf message
        """
        # Convert datetime to protobuf Timestamp
        timestamp = Timestamp()
        timestamp.FromDatetime(payment.created_at)

        # Convert status
        proto_status = self._domain_status_to_proto(payment.status)

        return GetPaymentResponse(
            payment_id=payment.payment_id,
            status=proto_status,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            order_id=payment.order_id,
            idempotency_key=payment.idempotency_key,
            created_at=timestamp,
            message=payment.message,
        )

    def _domain_status_to_proto(
        self, status: PaymentStatus
    ) -> ProtoPaymentStatus:
        """
        Convert domain PaymentStatus to protobuf PaymentStatus.

        Args:
            status: Domain PaymentStatus enum

        Returns:
            Protobuf PaymentStatus enum value
        """
        status_mapping = {
            PaymentStatus.PENDING: ProtoPaymentStatus.PAYMENT_STATUS_PENDING,
            PaymentStatus.SUCCEEDED: ProtoPaymentStatus.PAYMENT_STATUS_SUCCEEDED,
            PaymentStatus.FAILED: ProtoPaymentStatus.PAYMENT_STATUS_FAILED,
        }
        return status_mapping[status]

