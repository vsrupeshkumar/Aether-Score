from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class WalletFeatures:
    """Features extracted from wallet history"""
    tx_count: int
    total_volume: float
    stablecoin_ratio: float
    avg_tx_value: float
    days_active: int
    unique_contracts: int
    max_drawdown: float
    volatility: float

@dataclass
class ScoreResult:
    """Credit score result"""
    score: int  # 0-1000
    riskBand: int  # 0-3 (0=unknown, 1=low, 2=medium, 3=high)
    explanation: str
    features: Optional[WalletFeatures] = None

