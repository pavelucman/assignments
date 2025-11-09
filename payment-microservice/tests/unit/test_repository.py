"""Unit tests for payment repository implementations."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from payments_service.domain import Payment
from payments_service.storage import InMemoryPaymentRepository


class TestInMemoryPaymentRepository:
    """Tests for InMemoryPaymentRepository."""

    @pytest.fixture
    def repository(self) -> InMemoryPaymentRepository:
        """Create a fresh repository for each test."""
        return InMemoryPaymentRepository()

    @pytest.fixture
    def sample_payment(self) -> Payment:
        """Create a sample payment for testing."""
        return Payment.create(
            amount_minor=1250,
            currency="USD",
            order_id="order-123",
            idempotency_key="idem-key-12345",
        )

    def test_save_payment(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """Test saving a payment."""
        saved = repository.save(sample_payment)

        assert saved == sample_payment
        assert repository.count() == 1

    def test_find_by_id_existing_payment(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """Test finding an existing payment by ID."""
        repository.save(sample_payment)

        found = repository.find_by_id(sample_payment.payment_id)

        assert found is not None
        assert found.payment_id == sample_payment.payment_id
        assert found.amount_minor == sample_payment.amount_minor

    def test_find_by_id_nonexistent_payment(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test finding a nonexistent payment by ID."""
        found = repository.find_by_id("nonexistent-id")

        assert found is None

    def test_find_by_idempotency_key_existing_payment(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """Test finding an existing payment by idempotency key."""
        repository.save(sample_payment)

        found = repository.find_by_idempotency_key(
            sample_payment.idempotency_key
        )

        assert found is not None
        assert found.payment_id == sample_payment.payment_id
        assert found.idempotency_key == sample_payment.idempotency_key

    def test_find_by_idempotency_key_nonexistent(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test finding a nonexistent payment by idempotency key."""
        found = repository.find_by_idempotency_key("nonexistent-key")

        assert found is None

    def test_save_multiple_payments(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test saving multiple payments."""
        payment1 = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-1",
            idempotency_key="key-1",
        )
        payment2 = Payment.create(
            amount_minor=2000,
            currency="EUR",
            order_id="order-2",
            idempotency_key="key-2",
        )

        repository.save(payment1)
        repository.save(payment2)

        assert repository.count() == 2
        assert repository.find_by_id(payment1.payment_id) == payment1
        assert repository.find_by_id(payment2.payment_id) == payment2

    def test_update_payment_status(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """Test updating a payment status."""
        repository.save(sample_payment)

        # Update payment status
        succeeded = sample_payment.mark_succeeded("Payment processed")
        repository.save(succeeded)

        # Retrieve and verify
        found = repository.find_by_id(sample_payment.payment_id)
        assert found is not None
        assert found.status.value == "SUCCEEDED"
        assert found.message == "Payment processed"

    def test_idempotency_key_index_consistency(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test that idempotency key index remains consistent."""
        payment = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-123",
            idempotency_key="unique-key",
        )

        repository.save(payment)

        # Both lookups should return the same payment
        by_id = repository.find_by_id(payment.payment_id)
        by_key = repository.find_by_idempotency_key(payment.idempotency_key)

        assert by_id is not None
        assert by_key is not None
        assert by_id.payment_id == by_key.payment_id

    def test_clear_repository(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """Test clearing all payments from repository."""
        repository.save(sample_payment)
        assert repository.count() == 1

        repository.clear()

        assert repository.count() == 0
        assert repository.find_by_id(sample_payment.payment_id) is None
        assert (
            repository.find_by_idempotency_key(
                sample_payment.idempotency_key
            )
            is None
        )

    def test_overwrite_payment_with_same_id(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """Test that saving a payment with same ID overwrites the old one."""
        repository.save(sample_payment)

        # Create updated version
        updated = sample_payment.mark_succeeded("Updated")
        repository.save(updated)

        # Should have only one payment
        assert repository.count() == 1

        # Should retrieve the updated version
        found = repository.find_by_id(sample_payment.payment_id)
        assert found is not None
        assert found.message == "Updated"

    def test_empty_repository_count(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test that empty repository has count of zero."""
        assert repository.count() == 0

    def test_save_and_find_by_id_returns_same_payment(
        self, repository: InMemoryPaymentRepository, sample_payment: Payment
    ) -> None:
        """
        Test save and find_by_id workflow.
        
        Save a payment, then find by ID - should return the exact same payment.
        """
        # Save payment
        saved = repository.save(sample_payment)
        
        # Find by ID
        found = repository.find_by_id(sample_payment.payment_id)
        
        # Verify it's the same payment
        assert found is not None
        assert found == saved
        assert found == sample_payment
        assert found.payment_id == sample_payment.payment_id
        assert found.amount_minor == sample_payment.amount_minor
        assert found.currency == sample_payment.currency
        assert found.order_id == sample_payment.order_id
        assert found.idempotency_key == sample_payment.idempotency_key

    def test_find_by_id_nonexistent_returns_none(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test find_by_id with non-existent ID.
        
        Finding a payment that doesn't exist should return None.
        """
        found = repository.find_by_id("non-existent-uuid-12345")
        assert found is None

    def test_save_and_find_by_idempotency_key_returns_same_payment(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test save and find_by_idempotency_key workflow.
        
        Save a payment, then find by idempotency_key - should return same payment.
        """
        payment = Payment.create(
            amount_minor=1500,
            currency="EUR",
            order_id="order-456",
            idempotency_key="unique-idem-key-789",
        )
        
        # Save payment
        saved = repository.save(payment)
        
        # Find by idempotency key
        found = repository.find_by_idempotency_key("unique-idem-key-789")
        
        # Verify it's the same payment
        assert found is not None
        assert found == saved
        assert found.payment_id == payment.payment_id
        assert found.idempotency_key == "unique-idem-key-789"

    def test_find_by_idempotency_key_nonexistent_returns_none(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test find_by_idempotency_key with non-existent key.
        
        Finding a payment with a key that doesn't exist should return None.
        """
        found = repository.find_by_idempotency_key("non-existent-key")
        assert found is None

    def test_idempotency_overwrite_same_key(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test idempotency: saving different payment with same idempotency key.
        
        When a payment with the same idempotency key is saved again,
        it should overwrite the previous one (last write wins).
        """
        # Save first payment with key "key1"
        payment1 = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-1",
            idempotency_key="key1",
        )
        repository.save(payment1)
        
        # Try to save different payment with same key "key1"
        payment2 = Payment.create(
            amount_minor=2000,
            currency="EUR",
            order_id="order-2",
            idempotency_key="key1",  # Same key!
        )
        repository.save(payment2)
        
        # Find by idempotency key - should get the second payment
        found = repository.find_by_idempotency_key("key1")
        assert found is not None
        assert found.payment_id == payment2.payment_id
        assert found.amount_minor == 2000
        assert found.currency == "EUR"
        
        # First payment should not be accessible by ID
        # (unless we decide to keep it - current impl overwrites)
        # For this test, we verify only one payment exists per key
        all_by_key = repository.find_by_idempotency_key("key1")
        assert all_by_key.payment_id == payment2.payment_id

    def test_idempotency_multiple_keys(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test that different idempotency keys store different payments.
        
        Each unique idempotency key should map to its own payment.
        """
        payment1 = Payment.create(
            amount_minor=1000,
            currency="USD",
            order_id="order-1",
            idempotency_key="key-unique-1",
        )
        payment2 = Payment.create(
            amount_minor=2000,
            currency="EUR",
            order_id="order-2",
            idempotency_key="key-unique-2",
        )
        payment3 = Payment.create(
            amount_minor=3000,
            currency="GBP",
            order_id="order-3",
            idempotency_key="key-unique-3",
        )
        
        repository.save(payment1)
        repository.save(payment2)
        repository.save(payment3)
        
        # Each key should return its corresponding payment
        found1 = repository.find_by_idempotency_key("key-unique-1")
        found2 = repository.find_by_idempotency_key("key-unique-2")
        found3 = repository.find_by_idempotency_key("key-unique-3")
        
        assert found1 is not None and found1.amount_minor == 1000
        assert found2 is not None and found2.amount_minor == 2000
        assert found3 is not None and found3.amount_minor == 3000
        
        assert repository.count() == 3

    def test_thread_safety_concurrent_saves(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """
        Test thread safety: multiple threads saving payments concurrently.
        
        Use threading to save multiple payments concurrently and verify
        all payments are saved correctly without data corruption.
        """
        num_threads = 10
        payments_per_thread = 10

        def save_payments(thread_id: int) -> None:
            """Save multiple payments from a single thread."""
            for i in range(payments_per_thread):
                payment = Payment.create(
                    amount_minor=1000 + i,
                    currency="USD",
                    order_id=f"order-{thread_id}-{i}",
                    idempotency_key=f"key-{thread_id}-{i}",
                )
                repository.save(payment)

        # Run concurrent saves from multiple threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(save_payments, thread_id)
                for thread_id in range(num_threads)
            ]
            # Wait for all threads to complete
            for future in futures:
                future.result()

        # Verify all payments were saved correctly
        expected_count = num_threads * payments_per_thread
        assert repository.count() == expected_count
        
        # Verify we can find all saved payments
        for thread_id in range(num_threads):
            for i in range(payments_per_thread):
                found = repository.find_by_idempotency_key(
                    f"key-{thread_id}-{i}"
                )
                assert found is not None
                assert found.order_id == f"order-{thread_id}-{i}"

    def test_concurrent_save_operations(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test that concurrent save operations are thread-safe (legacy test)."""
        num_threads = 10
        payments_per_thread = 10

        def save_payments(thread_id: int) -> None:
            """Save multiple payments from a single thread."""
            for i in range(payments_per_thread):
                payment = Payment.create(
                    amount_minor=1000 + i,
                    currency="USD",
                    order_id=f"order-{thread_id}-{i}",
                    idempotency_key=f"key-{thread_id}-{i}",
                )
                repository.save(payment)

        # Run concurrent saves
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(save_payments, thread_id)
                for thread_id in range(num_threads)
            ]
            for future in futures:
                future.result()

        # Verify all payments were saved
        expected_count = num_threads * payments_per_thread
        assert repository.count() == expected_count

    def test_concurrent_read_and_write_operations(
        self, repository: InMemoryPaymentRepository
    ) -> None:
        """Test concurrent reads and writes are thread-safe."""
        # Pre-populate with some payments
        initial_payments = [
            Payment.create(
                amount_minor=1000 + i,
                currency="USD",
                order_id=f"order-{i}",
                idempotency_key=f"key-{i}",
            )
            for i in range(10)
        ]
        for payment in initial_payments:
            repository.save(payment)

        barrier = Barrier(3)  # Synchronize 3 threads
        results: dict[str, list[bool]] = {
            "reads": [],
            "writes": [],
            "idempotency": [],
        }

        def concurrent_reads() -> None:
            """Perform concurrent read operations."""
            barrier.wait()  # Wait for all threads to be ready
            for payment in initial_payments:
                found = repository.find_by_id(payment.payment_id)
                results["reads"].append(found is not None)

        def concurrent_writes() -> None:
            """Perform concurrent write operations."""
            barrier.wait()  # Wait for all threads to be ready
            for i in range(10, 20):
                payment = Payment.create(
                    amount_minor=2000 + i,
                    currency="EUR",
                    order_id=f"order-new-{i}",
                    idempotency_key=f"key-new-{i}",
                )
                repository.save(payment)
                results["writes"].append(True)

        def concurrent_idempotency_checks() -> None:
            """Perform concurrent idempotency key lookups."""
            barrier.wait()  # Wait for all threads to be ready
            for payment in initial_payments:
                found = repository.find_by_idempotency_key(
                    payment.idempotency_key
                )
                results["idempotency"].append(found is not None)

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            future1 = executor.submit(concurrent_reads)
            future2 = executor.submit(concurrent_writes)
            future3 = executor.submit(concurrent_idempotency_checks)

            future1.result()
            future2.result()
            future3.result()

        # Verify all operations completed successfully
        assert len(results["reads"]) == 10
        assert all(results["reads"])  # All reads found payments
        assert len(results["writes"]) == 10
        assert all(results["writes"])  # All writes succeeded
        assert len(results["idempotency"]) == 10
        assert all(results["idempotency"])  # All lookups found payments

        # Verify final count
        assert repository.count() == 20

