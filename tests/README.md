# WatchLLM Test Suite

Comprehensive test suite for WatchLLM services.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_ingest_api.py       # Ingest API unit tests
├── test_billing.py          # Billing service unit tests
├── test_processor.py        # Processor service unit tests
├── e2e/
│   └── test_e2e_flow.py    # End-to-end integration tests
└── integration/             # Service integration tests
```

## Setup

1. **Install test dependencies:**
   ```bash
   pip install -r requirements-test.txt
   ```

2. **For E2E tests, start services:**
   ```bash
   docker-compose up -d
   ```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run only unit tests (fast):
```bash
pytest -m unit
```

### Run integration tests:
```bash
pytest -m integration
```

### Run E2E tests (requires running services):
```bash
pytest -m e2e
```

### Run with coverage:
```bash
pytest --cov=services --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_billing.py
```

### Run specific test:
```bash
pytest tests/test_billing.py::TestSubscriptionRetrieval::test_get_existing_subscription
```

### Parallel execution (faster):
```bash
pytest -n auto
```

## Test Categories

### Unit Tests
- **Fast execution** (< 1s per test)
- **No external dependencies** (use mocks)
- **Test individual functions/classes**

Tests:
- `test_ingest_api.py` - Event validation, schema checks
- `test_billing.py` - Subscription logic, usage limits
- `test_processor.py` - Pricing calculation, alert evaluation

### Integration Tests
- **Require running services** (Redis, MongoDB, ClickHouse)
- **Test service interactions**
- **Use test databases**

### E2E Tests
- **Require full stack** (all services running)
- **Test complete user flows**
- **Slowest but most comprehensive**

Tests:
- `test_e2e_flow.py` - Complete event ingestion pipeline
  - SDK → Ingest API → Queue → Processor → ClickHouse → UI Backend

## Writing Tests

### Example Unit Test

```python
import pytest

def test_pricing_calculation():
    """Test GPT-4 cost calculation."""
    from services.processor.pricing import pricing_calculator
    
    cost = pricing_calculator.calculate_cost(
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500,
    )
    
    assert cost == pytest.approx(0.06, rel=1e-6)
```

### Example Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation(mock_mongodb):
    """Test async database operation."""
    result = await mock_mongodb["db"]["collection"].find_one({"id": "test"})
    assert result is not None
```

### Example E2E Test

```python
import pytest
import httpx

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_event_ingestion():
    """Test complete event flow."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/events",
            json=event_data,
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 202
```

## Fixtures

Common fixtures available in `conftest.py`:

- `mock_mongodb` - Mock MongoDB client
- `mock_clickhouse` - Mock ClickHouse client
- `mock_redis` - Mock Redis client
- `sample_event_data` - Sample event for testing
- `mock_subscription_data` - Sample subscription data
- `pricing_test_cases` - Test cases for pricing

## Coverage

Generate coverage report:
```bash
pytest --cov=services --cov-report=html
open htmlcov/index.html
```

Target: **>80% coverage** for all services.

## CI/CD Integration

GitHub Actions example:
```yaml
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=services --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### E2E tests failing
- Ensure all services are running: `docker-compose ps`
- Check logs: `docker-compose logs processor`
- Wait longer for processing: Increase `asyncio.sleep()` duration

### Import errors
- Verify `services/` is in Python path
- Check `conftest.py` has correct path additions

### Async warnings
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator

## Best Practices

1. **Use descriptive test names** - Test name should explain what it tests
2. **One assertion per test** - Makes failures easier to diagnose
3. **Use fixtures for setup** - Avoid repeating setup code
4. **Mock external services** - Keep unit tests fast and isolated
5. **Test edge cases** - Zero values, empty lists, null inputs
6. **Test error conditions** - Not just happy path
7. **Keep tests independent** - Tests should not depend on each other
