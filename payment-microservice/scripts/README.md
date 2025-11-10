# Test Scripts

This directory contains utility scripts for testing and demonstrating the payment microservice.

## test_client.py

A **demo-friendly test client** that runs comprehensive tests against the payment gRPC service with beautiful visual output.

### Features

- ✅ **8 comprehensive tests** covering all functionality
- ✅ **Color-coded output** with ✓/✗ marks
- ✅ **Clear test sections** with headers
- ✅ **Detailed results** for each test
- ✅ **Summary report** at the end
- ✅ **Proper error handling** with informative messages
- ✅ **Configurable server address** via environment variable

### Tests Included

1. **Health Check** - Verify service is running
2. **Create Payment** - Test RequestPayment RPC
3. **Idempotency** - Verify duplicate requests return same payment
4. **Get Payment** - Retrieve payment by ID
5. **Error Handling** - Test NOT_FOUND for non-existent payment
6. **Validation (Amount)** - Test negative amount rejection
7. **Validation (Currency)** - Test invalid currency rejection
8. **Multi-Currency** - Create payments in 6 different currencies

### Usage

#### With Docker Compose (Recommended)

**Terminal 1** - Start the server:
```bash
docker-compose up
```

**Terminal 2** - Run the test client:
```bash
python scripts/test_client.py
```

#### With Local Server

**Terminal 1** - Start the server:
```bash
make run
```

**Terminal 2** - Run the test client:
```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Run the test client
python scripts/test_client.py
```

#### With Custom Server Address

```bash
# Connect to different server
GRPC_SERVER=localhost:8080 python scripts/test_client.py

# Connect to remote server
GRPC_SERVER=payment-service.example.com:443 python scripts/test_client.py
```

### Example Output

```
Payment gRPC Service - Demo Test Client
Server: localhost:7000

ℹ Connecting to localhost:7000...
✓ Connected successfully!

======================================================================
                         Test 1: Health Check                         
======================================================================

ℹ Sending Health request...
✓ Health check passed: ok
  Status: ok

======================================================================
                   Test 2: Create Payment (RequestPayment)           
======================================================================

ℹ Creating payment request...
ℹ Request details:
  Amount: $12.50 USD
  Order ID: order-demo-001
  Idempotency Key: demo-key-12345678
  Metadata: {'customer_id': 'cust-789', 'product': 'Widget Pro', 'quantity': '2'}

ℹ Sending RequestPayment RPC...
✓ Payment created successfully!
  Payment ID: 550e8400-e29b-41d4-a716-446655440000
  Status: PENDING
  Message: Payment pending
  Idempotency Key: demo-key-12345678
  Created At: 2025-11-10 14:23:45

...

======================================================================
                            Test Summary                             
======================================================================

Total Tests: 8
Passed: 8
Failed: 0

Details:

  Health Check: ✓ PASSED
  Create Payment: ✓ PASSED
  Idempotency: ✓ PASSED
  Get Payment: ✓ PASSED
  Error Handling (Not Found): ✓ PASSED
  Validation (Invalid Amount): ✓ PASSED
  Validation (Invalid Currency): ✓ PASSED
  Multi-Currency Support: ✓ PASSED

Success Rate: 100.0%

🎉 All tests passed! 🎉
```

### Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed or connection error

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_SERVER` | `localhost:7000` | gRPC server address to connect to |

### Requirements

The script uses the generated protobuf files, so make sure to generate them first:

```bash
make proto
```

### Troubleshooting

**Connection Refused Error:**
```bash
# Make sure server is running
docker-compose ps
# OR
ps aux | grep payments_service
```

**Import Error:**
```bash
# Generate proto files
make proto

# Make sure dependencies are installed
make install
```

**Module Not Found:**
```bash
# Run from project root
cd /path/to/payment-microservice
python scripts/test_client.py
```

## Adding New Tests

To add a new test to `test_client.py`:

1. **Create test function:**
```python
def test_your_feature(client: PaymentServiceStub) -> bool:
    """Test description."""
    print_header("Test X: Your Feature")
    
    try:
        # Your test logic here
        print_success("Test passed!")
        return True
    except grpc.RpcError as e:
        print_error(f"Test failed: {e.details()}")
        return False
```

2. **Add to main():**
```python
results["Your Feature"] = test_your_feature(client)
time.sleep(0.3)
```

3. **Test it:**
```bash
python scripts/test_client.py
```

## Tips for Demos

1. **Run in split terminal** - Server on left, client on right
2. **Use dark theme** - Colors show up better
3. **Increase font size** - For better visibility
4. **Add delays** - Uncomment `time.sleep()` calls for slower pace
5. **Focus on summary** - Scroll to summary at the end

## Related Files

- [`examples/client_example.py`](../examples/client_example.py) - Simpler example client for learning
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) - CI pipeline that runs integration tests
- [`tests/integration/test_server.py`](../tests/integration/test_server.py) - Integration tests (pytest)

