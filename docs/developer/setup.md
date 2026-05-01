# Developer Setup Guide

## Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)
- Git

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/AETHER-SCORE.git
cd AETHER-SCORE
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Run backend
uvicorn app:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Run frontend
npm run dev
```

### 4. Database Setup

```bash
# Create database
createdb AETHER-SCORE_dev

# Run migrations
cd backend
alembic upgrade head
```

### 5. Redis Setup

```bash
# Start Redis (if not using Docker)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

## Docker Setup (Alternative)

### Quick Start

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: your feature description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## Project Structure

```
AETHER-SCORE/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app.py                 # FastAPI application
â”‚   â”œâ”€â”€ services/              # Business logic services
â”‚   â”œâ”€â”€ database/              # Database models and repositories
â”‚   â”œâ”€â”€ middleware/            # Custom middleware
â”‚   â”œâ”€â”€ utils/                 # Utility functions
â”‚   â”œâ”€â”€ tests/                 # Test files
â”‚   â””â”€â”€ requirements.txt       # Python dependencies
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ app/                   # Next.js app directory
â”‚   â”œâ”€â”€ components/            # React components
â”‚   â”œâ”€â”€ lib/                  # Utility functions
â”‚   â”œâ”€â”€ tests/                # Test files
â”‚   â””â”€â”€ package.json          # Node dependencies
â”œâ”€â”€ contracts/
â”‚   â”œâ”€â”€ contracts/            # Solidity contracts
â”‚   â”œâ”€â”€ scripts/             # Deployment scripts
â”‚   â”œâ”€â”€ test/                # Contract tests
â”‚   â””â”€â”€ hardhat.config.ts    # Hardhat configuration
â””â”€â”€ docs/                    # Documentation
```

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://localhost:5432/AETHER-SCORE_dev

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Blockchain
QIE_TESTNET_RPC_URL=https://rpc1testnet.qie.digital/
PRIVATE_KEY=<your-private-key>

# Security
JWT_SECRET=dev-secret-key
API_KEY_ENCRYPTION_KEY=<fernet-key>

# Monitoring
SENTRY_DSN=
LOG_LEVEL=DEBUG
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CHAIN_ID=12345
NEXT_PUBLIC_RPC_URL=https://rpc1testnet.qie.digital/
```

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_scoring.py

# Run specific test
pytest tests/test_scoring.py::test_compute_score
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm test

# E2E tests
npm run test:e2e

# E2E with UI
npm run test:e2e:ui
```

### Contract Tests

```bash
cd contracts

# Run tests
npx hardhat test

# Run with coverage
npx hardhat coverage
```

## Code Quality

### Linting

```bash
# Backend
cd backend
ruff check .
black --check .

# Frontend
cd frontend
npm run lint
```

### Formatting

```bash
# Backend
cd backend
black .
ruff format .

# Frontend
cd frontend
npm run format
```

## Debugging

### Backend Debugging

```bash
# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn app:app --reload

# VS Code: Attach to debugger on port 5678
```

### Frontend Debugging

```bash
# Run with debugger
NODE_OPTIONS='--inspect' npm run dev

# Chrome: chrome://inspect
```

## Common Tasks

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding Dependencies

```bash
# Backend
pip install package-name
pip freeze > requirements.txt

# Frontend
npm install package-name
```

### Building for Production

```bash
# Backend
cd backend
docker build -t AETHER-SCORE/backend:latest .

# Frontend
cd frontend
npm run build
docker build -t AETHER-SCORE/frontend:latest .
```

## Code Structure

### Backend Structure

```
backend/
â”œâ”€â”€ app.py                 # FastAPI application entry point
â”œâ”€â”€ services/              # Business logic services
â”‚   â”œâ”€â”€ scoring.py        # Credit scoring service
â”‚   â”œâ”€â”€ blockchain.py      # Blockchain interaction service
â”‚   â”œâ”€â”€ oracle.py         # Oracle data service
â”‚   â”œâ”€â”€ staking.py        # Staking service
â”‚   â”œâ”€â”€ ml_scoring.py     # ML-based scoring
â”‚   â”œâ”€â”€ fraud_detection.py # Fraud detection
â”‚   â””â”€â”€ ...
â”œâ”€â”€ database/              # Database layer
â”‚   â”œâ”€â”€ models.py         # SQLAlchemy models
â”‚   â”œâ”€â”€ repositories.py   # Data access layer
â”‚   â””â”€â”€ connection.py    # Database connection
â”œâ”€â”€ middleware/            # Custom middleware
â”‚   â”œâ”€â”€ auth.py          # Authentication
â”‚   â”œâ”€â”€ rate_limit.py    # Rate limiting
â”‚   â””â”€â”€ ...
â”œâ”€â”€ utils/                 # Utility functions
â”‚   â”œâ”€â”€ validators.py    # Input validation
â”‚   â”œâ”€â”€ logger.py        # Logging utilities
â”‚   â””â”€â”€ ...
â”œâ”€â”€ tests/                 # Test files
â”‚   â”œâ”€â”€ unit/             # Unit tests
â”‚   â”œâ”€â”€ integration/     # Integration tests
â”‚   â””â”€â”€ ...
â””â”€â”€ requirements.txt       # Python dependencies
```

### Frontend Structure

```
frontend/
â”œâ”€â”€ app/                   # Next.js app directory
â”‚   â”œâ”€â”€ page.tsx          # Home page
â”‚   â”œâ”€â”€ dashboard/        # Dashboard pages
â”‚   â””â”€â”€ ...
â”œâ”€â”€ components/           # React components
â”‚   â”œâ”€â”€ ui/              # UI components (Shadcn)
â”‚   â”œâ”€â”€ layout/          # Layout components
â”‚   â””â”€â”€ ...
â”œâ”€â”€ contexts/            # React contexts
â”‚   â””â”€â”€ WalletContext.tsx # Wallet connection context
â”œâ”€â”€ lib/                 # Utility functions
â”‚   â”œâ”€â”€ utils.ts        # General utilities
â”‚   â””â”€â”€ errors.ts       # Error handling
â”œâ”€â”€ tests/               # Test files
â”‚   â”œâ”€â”€ unit/           # Unit tests
â”‚   â””â”€â”€ e2e/            # E2E tests
â””â”€â”€ package.json        # Node dependencies
```

### Contract Structure

```
contracts/
â”œâ”€â”€ contracts/           # Solidity contracts
â”‚   â”œâ”€â”€ CreditPassportNFT.sol
â”‚   â”œâ”€â”€ AETHER-SCOREStaking.sol
â”‚   â”œâ”€â”€ LendingVault.sol
â”‚   â””â”€â”€ ...
â”œâ”€â”€ scripts/            # Deployment scripts
â”‚   â”œâ”€â”€ deploy.ts       # Deployment script
â”‚   â””â”€â”€ upgrade.ts      # Upgrade script
â”œâ”€â”€ test/               # Contract tests
â”‚   â”œâ”€â”€ CreditPassportNFT.test.ts
â”‚   â””â”€â”€ ...
â””â”€â”€ hardhat.config.ts   # Hardhat configuration
```

## Contribution Guidelines

### Code Style

#### Python

- Follow PEP 8 style guide
- Use `black` for formatting
- Use `ruff` for linting
- Maximum line length: 100 characters

```bash
# Format code
black .

# Lint code
ruff check .
```

#### TypeScript/JavaScript

- Follow ESLint rules
- Use Prettier for formatting
- Use TypeScript for type safety

```bash
# Format code
npm run format

# Lint code
npm run lint
```

#### Solidity

- Follow Solidity style guide
- Use NatSpec comments
- Maximum line length: 120 characters

### Git Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Examples:
```
feat: add ML-based credit scoring
fix: resolve database connection pool issue
docs: update API documentation
```

### Pull Request Process

1. **Create PR**: Use PR template
2. **Review**: Address review comments
3. **Tests**: Ensure all tests pass
4. **Merge**: Squash and merge

### Testing Guidelines

- Write tests for all new features
- Maintain >80% code coverage
- Run tests before committing
- Update tests when changing behavior

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check PostgreSQL is running
2. **Port conflicts**: Change ports in .env files
3. **Module not found**: Reinstall dependencies
4. **Migration errors**: Check database state
5. **Contract compilation errors**: Check Solidity version
6. **Type errors**: Run type checking (`mypy` for Python, `tsc` for TypeScript)

### Getting Help

- Check documentation in `/docs`
- Review existing issues on GitHub
- Ask in team Slack channel
- Create new issue if needed


