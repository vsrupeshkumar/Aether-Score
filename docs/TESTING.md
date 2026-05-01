# Testing Guide

Comprehensive testing guide for AETHER-SCORE project.

## Overview

AETHER-SCORE uses a multi-layered testing strategy:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API endpoints and service interactions
- **Contract Tests**: Test smart contracts with Hardhat
- **E2E Tests**: Test complete user flows with Playwright
- **Load Tests**: Test performance under high load
- **Security Tests**: Test for vulnerabilities and security issues

## Test Structure

```
backend/
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ unit/          # Unit tests for services and utilities
â”‚   â”œâ”€â”€ integration/   # Integration tests for API endpoints
â”‚   â”œâ”€â”€ load/          # Load testing with Locust
â”‚   â””â”€â”€ security/      # Security tests
â”œâ”€â”€ pytest.ini         # Pytest configuration

contracts/
â”œâ”€â”€ test/              # Hardhat contract tests
â””â”€â”€ hardhat.config.ts  # Hardhat configuration with coverage

frontend/
â”œâ”€â”€ tests/
â”‚   â””â”€â”€ e2e/           # Playwright E2E tests
â””â”€â”€ playwright.config.ts
```

## Backend Testing

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run only unit tests
pytest tests/unit -m unit

# Run only integration tests
pytest tests/integration -m integration

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_scoring.py
```

### Test Coverage

Coverage reports are generated in `backend/htmlcov/`. Open `index.html` in a browser to view.

Target coverage: **80%+**

### Writing Tests

**Unit Test Example:**
```python
import pytest
from services.scoring import ScoringService

@pytest.mark.unit
class TestScoringService:
    @pytest.fixture
    def scoring_service(self):
        # Setup with mocks
        return ScoringService()
    
    def test_calculate_score(self, scoring_service):
        # Test implementation
        result = scoring_service._calculate_score(features)
        assert result[0] >= 0
```

**Integration Test Example:**
```python
import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.integration
class TestAPIScore:
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_generate_score(self, client):
        response = await client.post("/api/score", json={"address": "0x..."})
        assert response.status_code == 200
```

## Contract Testing

### Running Tests

```bash
cd contracts

# Run all tests
npm test

# Run with coverage
COVERAGE=true npm test

# Run specific test file
npx hardhat test test/CreditPassportNFT.test.ts
```

### Test Coverage

Coverage reports are generated in `contracts/coverage/`.

Target coverage: **80%+**

### Writing Contract Tests

```typescript
import { expect } from "chai";
import { ethers } from "hardhat";

describe("CreditPassportNFT", function () {
  it("Should mint a new passport", async function () {
    const tx = await passportNFT.mintOrUpdate(user1.address, 750, 1);
    await expect(tx).to.emit(passportNFT, "PassportMinted");
  });
});
```

## Frontend E2E Testing

### Setup

```bash
cd frontend
npm install
npx playwright install
```

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run in UI mode
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run specific test
npx playwright test tests/e2e/wallet-connect.spec.ts
```

### Writing E2E Tests

```typescript
import { test, expect } from '@playwright/test';

test('should connect wallet', async ({ page }) => {
  await page.goto('/');
  const connectButton = page.getByRole('button', { name: /connect wallet/i });
  await connectButton.click();
  // Verify connection
});
```

## Load Testing

### Setup

```bash
cd backend
pip install locust
```

### Running Load Tests

```bash
# Start Locust web UI
locust -f tests/load/test_api_load.py --host=http://localhost:8000

# Command line (1000 users, 50 spawn rate, 10 minutes)
locust -f tests/load/test_api_load.py \
  --host=http://localhost:8000 \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 10m \
  --headless \
  --html=load_test_report.html
```

### Performance Targets

- Response time: < 500ms (95th percentile)
- Error rate: < 1%
- Throughput: > 1000 req/s
- Concurrent users: 1000+

## Security Testing

### Running Security Scans

```bash
cd backend

# Run all security scans
./scripts/run_security_scans.sh

# Individual scans
bandit -r .
safety check
```

### Security Tools

- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability checker
- **Slither**: Solidity security analyzer

## CI/CD

All tests run automatically on:
- Push to `main` or `feature/fullstack-enhancements`
- Pull requests to `main`

### Workflows

- `.github/workflows/backend.yml`: Backend tests and coverage
- `.github/workflows/contracts.yml`: Contract tests and coverage
- `.github/workflows/frontend.yml`: Frontend build and E2E tests
- `.github/workflows/security.yml`: Security scans

## Test Markers

Pytest markers for organizing tests:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.security`: Security tests
- `@pytest.mark.slow`: Slow-running tests

Run tests by marker:
```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies (blockchain, APIs)
3. **Coverage**: Aim for 80%+ coverage
4. **Speed**: Keep test suite fast (< 5 minutes)
5. **Clarity**: Write clear, descriptive test names
6. **Maintenance**: Update tests when code changes

## Troubleshooting

### Backend Tests Failing

- Check environment variables in `backend/.env`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify test database/blockchain connections

### Contract Tests Failing

- Ensure Hardhat is configured: `npx hardhat compile`
- Check network configuration in `hardhat.config.ts`
- Verify contract addresses in test files

### E2E Tests Failing

- Ensure frontend is running: `npm run dev`
- Check Playwright browsers are installed: `npx playwright install`
- Verify API endpoints are accessible

## Coverage Reports

- **Backend**: `backend/htmlcov/index.html`
- **Contracts**: `contracts/coverage/index.html`
- **CI**: Uploaded as artifacts in GitHub Actions

## Next Steps

- Add more edge case tests
- Increase coverage to 90%+
- Add performance benchmarks
- Set up test data fixtures
- Add contract fuzzing tests


