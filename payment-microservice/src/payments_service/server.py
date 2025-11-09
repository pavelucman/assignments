"""gRPC server application for payment microservice."""

import logging
import os
import signal
import sys
from concurrent import futures
from typing import Optional

import grpc

from payments_service.app import PaymentService
from payments_service.payments_pb2_grpc import (
    add_PaymentServiceServicer_to_server,
)
from payments_service.storage import InMemoryPaymentRepository
from payments_service.transport import PaymentServiceGrpcServicer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class PaymentServer:
    """
    gRPC server for payment microservice.

    Handles server lifecycle including startup, shutdown, and graceful
    termination on SIGTERM/SIGINT signals.
    """

    def __init__(self, port: int = 7000, max_workers: int = 10) -> None:
        """
        Initialize the payment server.

        Args:
            port: Port number to bind the server to
            max_workers: Maximum number of thread pool workers
        """
        self.port = port
        self.max_workers = max_workers
        self.server: Optional[grpc.Server] = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(
            f"PaymentServer initialized (port={port}, workers={max_workers})"
        )

    def _signal_handler(self, signum: int, frame: object) -> None:
        """
        Handle termination signals for graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received signal {signal_name}, initiating shutdown...")
        self.stop()

    def start(self) -> None:
        """
        Start the gRPC server.

        Creates all necessary components, configures the server,
        and starts listening for requests.
        """
        logger.info("Starting payment microservice...")

        try:
            # Create repository
            logger.info("Creating InMemoryPaymentRepository...")
            repository = InMemoryPaymentRepository()

            # Create service
            logger.info("Creating PaymentService...")
            service = PaymentService(repository)

            # Create gRPC servicer
            logger.info("Creating PaymentServiceGrpcServicer...")
            servicer = PaymentServiceGrpcServicer(service)

            # Create gRPC server
            logger.info(
                f"Creating gRPC server with {self.max_workers} workers..."
            )
            self.server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=self.max_workers)
            )

            # Add servicer to server
            logger.info("Adding PaymentService servicer to server...")
            add_PaymentServiceServicer_to_server(servicer, self.server)

            # Bind to port
            address = f"[::]:{self.port}"
            self.server.add_insecure_port(address)
            logger.info(f"Server bound to {address}")

            # Start server
            self.server.start()
            logger.info(
                f"✓ Payment microservice started successfully on port {self.port}"
            )
            logger.info("Server is ready to accept requests")

            # Wait for termination
            self.server.wait_for_termination()

        except Exception as e:
            logger.error(f"Failed to start server: {e}", exc_info=True)
            raise

    def stop(self, grace_period: int = 5) -> None:
        """
        Stop the gRPC server gracefully.

        Args:
            grace_period: Maximum time in seconds to wait for
                         in-flight requests to complete
        """
        if self.server:
            logger.info(
                f"Stopping server (grace period: {grace_period}s)..."
            )
            self.server.stop(grace_period)
            logger.info("✓ Server stopped successfully")
        else:
            logger.warning("Server was not running")


def main() -> None:
    """
    Main entry point for the gRPC server.

    Reads configuration from environment variables and starts the server.
    """
    # Get port from environment variable, default to 7000
    port_str = os.getenv("PORT", "7000")
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {port}")
    except ValueError as e:
        logger.error(f"Invalid PORT environment variable: {e}")
        sys.exit(1)

    # Get max workers from environment variable, default to 10
    workers_str = os.getenv("MAX_WORKERS", "10")
    try:
        max_workers = int(workers_str)
        if max_workers < 1:
            raise ValueError(
                f"MAX_WORKERS must be at least 1, got {max_workers}"
            )
    except ValueError as e:
        logger.error(f"Invalid MAX_WORKERS environment variable: {e}")
        sys.exit(1)

    # Create and start server
    server = PaymentServer(port=port, max_workers=max_workers)

    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

