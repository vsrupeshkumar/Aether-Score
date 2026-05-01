# AETHER-SCORE Architecture

## Overview

AETHER-SCORE is an AI-powered credit scoring system built on the QIE blockchain. It provides on-chain credit scores, staking mechanisms, and DeFi lending capabilities.

## System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[Next.js Frontend]
        SW[Service Worker]
        WC[Wallet Context]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend]
        MW[Middleware Stack]
        AUTH[Auth Middleware]
        RL[Rate Limiting]
    end
    
    subgraph "Service Layer"
        SS[Scoring Service]
        ML[ML Scoring Service]
        BS[Blockchain Service]
        OS[Oracle Service]
        FS[Feature Engineering]
        FD[Fraud Detection]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        RD[(Redis Cache)]
        RQ[RQ Workers]
    end
    
    subgraph "Blockchain Layer"
        QIE[QIE Blockchain]
        CP[Credit Passport NFT]
        ST[Staking Contract]
        LV[Lending Vault]
    end
    
    subgraph "External Services"
        SENTRY[Sentry]
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    FE --> API
    SW --> FE
    WC --> QIE
    API --> MW
    MW --> AUTH
    MW --> RL
    API --> SS
    API --> ML
    API --> BS
    API --> OS
    SS --> FS
    ML --> FS
    FS --> PG
    BS --> QIE
    OS --> QIE
    API --> PG
    API --> RD
    RQ --> PG
    RQ --> RD
    BS --> CP
    BS --> ST
    BS --> LV
    API --> SENTRY
    API --> PROM
    PROM --> GRAF
```

## Component Architecture

### Frontend Components

```mermaid
graph LR
    subgraph "Pages"
        HOME[Home Page]
        DASH[Dashboard]
        STAKE[Staking]
        LEND[Lending]
        HELP[Help Center]
    end
    
    subgraph "Components"
        HERO[Hero Section]
        SCORE[Score Display]
        CHAT[Chat Console]
        WIZARD[Onboarding]
    end
    
    subgraph "Contexts"
        WALLET[Wallet Context]
        THEME[Theme Context]
    end
    
    HOME --> HERO
    DASH --> SCORE
    LEND --> CHAT
    HOME --> WIZARD
    HOME --> WALLET
    HOME --> THEME
```

### Backend Services

```mermaid
graph TB
    subgraph "Core Services"
        SS[ScoringService]
        ML[MLScoringService]
        BS[BlockchainService]
        OS[QIEOracleService]
    end
    
    subgraph "Supporting Services"
        FS[FeatureEngineeringService]
        FD[FraudDetectionService]
        TI[TransactionIndexer]
        LM[LoanMonitor]
    end
    
    subgraph "Data Services"
        SR[ScoreRepository]
        UR[UserRepository]
        TR[TransactionRepository]
    end
    
    SS --> FS
    ML --> FS
    FS --> TI
    FS --> SR
    FD --> FS
    BS --> UR
    LM --> TR
```

## Data Flow

### Credit Score Generation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as Backend API
    participant FS as Feature Engineering
    participant ML as ML Scoring
    participant PG as PostgreSQL
    participant BC as Blockchain
    
    U->>F: Connect Wallet
    F->>API: POST /api/score
    API->>FS: Extract Features
    FS->>PG: Query Transactions
    FS->>BC: Query On-Chain Data
    FS->>FS: Calculate Features
    FS->>ML: Get ML Prediction
    ML->>ML: Predict Score
    ML->>PG: Store Score
    ML->>BC: Mint NFT (if new)
    API->>F: Return Score
    F->>U: Display Score
```

### Loan Creation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant AI as AI Agent
    participant API as Backend API
    participant BC as Blockchain
    
    U->>F: Request Loan
    F->>AI: Start Negotiation
    AI->>AI: Generate Offer
    AI->>F: Present Offer
    U->>F: Accept/Reject
    F->>API: Create Loan
    API->>BC: Deploy Loan Contract
    BC->>BC: Transfer Collateral
    BC->>BC: Emit Events
    API->>F: Loan Created
    F->>U: Show Confirmation
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Frontend"
            FE1[Next.js Instance 1]
            FE2[Next.js Instance 2]
            CDN[CDN/Vercel]
        end
        
        subgraph "Backend"
            API1[API Instance 1]
            API2[API Instance 2]
            LB[Load Balancer]
        end
        
        subgraph "Workers"
            W1[RQ Worker 1]
            W2[RQ Worker 2]
        end
        
        subgraph "Database"
            PG_MASTER[(PostgreSQL Master)]
            PG_REPLICA[(PostgreSQL Replica)]
            REDIS[(Redis Cluster)]
        end
        
        subgraph "Monitoring"
            PROM[Prometheus]
            GRAF[Grafana]
            SENTRY[Sentry]
        end
    end
    
    CDN --> FE1
    CDN --> FE2
    FE1 --> LB
    FE2 --> LB
    LB --> API1
    LB --> API2
    API1 --> PG_MASTER
    API2 --> PG_MASTER
    PG_MASTER --> PG_REPLICA
    API1 --> REDIS
    API2 --> REDIS
    W1 --> REDIS
    W2 --> REDIS
    W1 --> PG_MASTER
    W2 --> PG_MASTER
    API1 --> PROM
    API2 --> PROM
    PROM --> GRAF
    API1 --> SENTRY
    API2 --> SENTRY
```

## Technology Stack

### Frontend
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI, Shadcn-ui
- **State Management**: React Context, TanStack Query
- **Blockchain**: Ethers.js
- **Animations**: Framer Motion
- **Monitoring**: Sentry

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (asyncpg)
- **Cache**: Redis
- **Queue**: RQ (Redis Queue)
- **ML**: XGBoost, scikit-learn
- **Blockchain**: Web3.py
- **Monitoring**: Sentry, Prometheus

### Smart Contracts
- **Language**: Solidity
- **Framework**: Hardhat
- **Patterns**: UUPS Upgradeable, Pausable, Access Control
- **Standards**: ERC-721 (NFT), ERC-20

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana, Sentry
- **Deployment**: Vercel/Render

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        WAF[WAF/Cloudflare]
        AUTH[Authentication]
        RBAC[Role-Based Access]
        VAL[Input Validation]
        ENC[Encryption]
    end
    
    subgraph "Protection Mechanisms"
        RL[Rate Limiting]
        CSRF[CSRF Protection]
        XSS[XSS Protection]
        SQL[SQL Injection Protection]
        REPLAY[Replay Attack Prevention]
    end
    
    WAF --> AUTH
    AUTH --> RBAC
    RBAC --> VAL
    VAL --> ENC
    RL --> CSRF
    CSRF --> XSS
    XSS --> SQL
    SQL --> REPLAY
```

## Scalability Considerations

1. **Horizontal Scaling**: API instances can be scaled independently
2. **Database Replication**: Read replicas for analytics queries
3. **Caching Strategy**: Multi-layer caching (Redis, CDN)
4. **Async Processing**: Background workers for heavy operations
5. **Connection Pooling**: Database and RPC connection pooling
6. **Load Balancing**: Distributed load across instances

## Performance Optimizations

1. **CDN**: Static assets served via CDN
2. **Database Indexing**: Optimized indexes for common queries
3. **Query Optimization**: Batch operations, connection pooling
4. **Caching**: Aggressive caching of scores and API responses
5. **Code Splitting**: Frontend code splitting for faster loads
6. **Service Worker**: Offline support and asset caching


