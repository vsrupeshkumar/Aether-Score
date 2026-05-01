# Architecture Diagrams

This document contains detailed architecture diagrams for the AETHER-SCORE system.

## System Overview

```mermaid
graph TB
    subgraph "User Interface"
        WEB[Web Application]
        MOBILE[Mobile Browser]
    end
    
    subgraph "Application Layer"
        FE[Frontend - Next.js]
        API[Backend API - FastAPI]
    end
    
    subgraph "Business Logic"
        SCORE[Scoring Engine]
        ML[ML Model]
        ORACLE[Oracle Service]
        FRAUD[Fraud Detection]
    end
    
    subgraph "Data Storage"
        DB[(PostgreSQL)]
        CACHE[(Redis)]
        S3[(S3 Archive)]
    end
    
    subgraph "Blockchain"
        QIE[QIE Network]
        CONTRACTS[Smart Contracts]
    end
    
    WEB --> FE
    MOBILE --> FE
    FE --> API
    API --> SCORE
    API --> ML
    API --> ORACLE
    API --> FRAUD
    SCORE --> DB
    ML --> DB
    ORACLE --> QIE
    FRAUD --> DB
    API --> DB
    API --> CACHE
    DB --> S3
    API --> CONTRACTS
    CONTRACTS --> QIE
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant LB as Load Balancer
    participant API as API Server
    participant MW as Middleware
    participant SVC as Service Layer
    participant DB as Database
    participant BC as Blockchain
    
    C->>LB: HTTP Request
    LB->>API: Route Request
    API->>MW: Process Middleware
    MW->>MW: Auth, Rate Limit, Validation
    MW->>SVC: Call Service
    SVC->>DB: Query Data
    SVC->>BC: Blockchain Call (if needed)
    DB-->>SVC: Return Data
    BC-->>SVC: Return Result
    SVC-->>MW: Service Response
    MW-->>API: Processed Response
    API-->>LB: HTTP Response
    LB-->>C: Return to Client
```

## Database Schema

```mermaid
erDiagram
    USER ||--o{ SCORE : has
    USER ||--o{ LOAN : has
    USER ||--o{ TRANSACTION : has
    USER ||--o{ GDPR_REQUEST : has
    SCORE ||--o{ SCORE_HISTORY : has
    LOAN ||--o{ LOAN_PAYMENT : has
    TRANSACTION ||--o{ TOKEN_TRANSFER : has
    AB_EXPERIMENT ||--o{ AB_ALLOCATION : has
    AB_EXPERIMENT ||--o{ AB_METRIC : has
    
    USER {
        string wallet_address PK
        string email
        boolean gdpr_consent
    }
    
    SCORE {
        string wallet_address PK
        int score
        int risk_band
        string model_version
    }
    
    LOAN {
        int id PK
        string wallet_address FK
        decimal amount
        string status
    }
    
    TRANSACTION {
        int id PK
        string wallet_address FK
        string tx_hash
        string tx_type
    }
```

## Service Interactions

```mermaid
graph LR
    subgraph "API Endpoints"
        E1[/api/score]
        E2[/api/staking]
        E3[/api/loan]
        E4[/api/oracle]
    end
    
    subgraph "Services"
        SS[ScoringService]
        ML[MLScoringService]
        BS[BlockchainService]
        OS[OracleService]
        FS[FeatureEngineering]
    end
    
    E1 --> SS
    E1 --> ML
    E2 --> BS
    E3 --> BS
    E4 --> OS
    SS --> FS
    ML --> FS
    BS --> BC[Blockchain]
    OS --> BC
```


