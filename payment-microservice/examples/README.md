# Payment Service Examples

This directory contains example code for using the payment microservice.

## Client Example

The `client_example.py` demonstrates all the key features of the payment service:

1. **Health Check** - Verify service is running
2. **Request Payment** - Create a new payment
3. **Get Payment** - Retrieve payment by ID
4. **Idempotency** - Duplicate requests return same payment
5. **Validation** - Invalid requests are rejected
6. **Error Handling** - Not found errors are handled properly

### Running the Example

#### Step 1: Start the Server

In one terminal:

```bash
cd /assignments/payment-microservice

# Install dependencies if not already done
make install

# Generate proto files if not already done
make proto

# Start the server
make run
```

You should see:
```
✓ Payment microservice started successfully on port 7000
Server is ready to accept requests
```

#### Step 2: Run the Client

In another terminal:

```bash
cd /assignments/payment-microservice

# Run the example client
python examples/client_example.py
```

Or with custom host/port:

```bash
python examples/client_example.py localhost 7000
```

### Expected Output

```
2025-11-09 10:00:00 - INFO - Connecting to payment service at localhost:7000...
2025-11-09 10:00:00 - INFO - ✓ Connected to server

=== Health Check ===
2025-11-09 10:00:00 - INFO - ✓ Health status: ok

=== Request Payment ===
2025-11-09 10:00:00 - INFO - Requesting payment:
2025-11-09 10:00:00 - INFO -   Amount: $12.50
2025-11-09 10:00:00 - INFO -   Currency: USD
2025-11-09 10:00:00 - INFO -   Order ID: order-example-123
2025-11-09 10:00:00 - INFO -   Idempotency Key: example-key-12345678
2025-11-09 10:00:00 - INFO - ✓ Payment created:
2025-11-09 10:00:00 - INFO -   Payment ID: 550e8400-e29b-41d4-a716-446655440000
2025-11-09 10:00:00 - INFO -   Status: PAYMENT_STATUS_PENDING
2025-11-09 10:00:00 - INFO -   Message: Payment initiated
2025-11-09 10:00:00 - INFO -   Created At: 2025-11-09 10:00:00+00:00

=== Get Payment ===
2025-11-09 10:00:00 - INFO - Retrieving payment: 550e8400-e29b-41d4-a716-446655440000
2025-11-09 10:00:00 - INFO - ✓ Payment retrieved:
2025-11-09 10:00:00 - INFO -   Payment ID: 550e8400-e29b-41d4-a716-446655440000
2025-11-09 10:00:00 - INFO -   Amount: $12.50
2025-11-09 10:00:00 - INFO -   Currency: USD
2025-11-09 10:00:00 - INFO -   Order ID: order-example-123
2025-11-09 10:00:00 - INFO -   Status: PAYMENT_STATUS_PENDING
2025-11-09 10:00:00 - INFO -   Message: Payment initiated

=== Test Idempotency ===
2025-11-09 10:00:00 - INFO - Sending duplicate request with same idempotency key
2025-11-09 10:00:00 - INFO - ✓ Idempotency working! Same payment returned:
2025-11-09 10:00:00 - INFO -   Payment ID: 550e8400-e29b-41d4-a716-446655440000

=== Test Validation Error ===
2025-11-09 10:00:00 - INFO - Sending invalid request (negative amount)
2025-11-09 10:00:00 - INFO - ✓ Validation error caught: Validation error: Invalid amount: ...

=== Test Not Found Error ===
2025-11-09 10:00:00 - INFO - Requesting nonexistent payment
2025-11-09 10:00:00 - INFO - ✓ Not found error caught: Payment not found: nonexistent-payment-id

=== Client Example Complete ===
```

## Writing Your Own Client

Here's a minimal example:

```python
import grpc
from payments_service.payments_pb2 import RequestPaymentRequest
from payments_service.payments_pb2_grpc import PaymentServiceStub

# Connect to server
channel = grpc.insecure_channel('localhost:7000')
client = PaymentServiceStub(channel)

# Create payment
request = RequestPaymentRequest(
    amount_minor=1250,  # $12.50 in cents
    currency="USD",
    order_id="my-order-123",
    idempotency_key="my-unique-key-12345678"
)

response = client.RequestPayment(request)
print(f"Payment ID: {response.payment_id}")
print(f"Status: {response.status}")
```

## Using grpcurl

If you have `grpcurl` installed:

```bash
# Health check
grpcurl -plaintext localhost:7000 payments.v1.PaymentService/Health

# Request payment
grpcurl -plaintext -d '{
  "amount_minor": 1250,
  "currency": "USD",
  "order_id": "order-123",
  "idempotency_key": "test-key-12345678"
}' localhost:7000 payments.v1.PaymentService/RequestPayment

# Get payment
grpcurl -plaintext -d '{
  "payment_id": "YOUR_PAYMENT_ID_HERE"
}' localhost:7000 payments.v1.PaymentService/GetPayment
```

## Configuration

### Server Configuration

Set environment variables before starting the server:

```bash
# Custom port
PORT=9090 make run

# Custom thread pool size
MAX_WORKERS=20 make run

# Both
PORT=9090 MAX_WORKERS=20 make run
```

### Client Configuration

Pass host and port as command line arguments:

```bash
# Default (localhost:7000)
python examples/client_example.py

# Custom host and port
python examples/client_example.py myserver.com 9090
```

