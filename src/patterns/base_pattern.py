"""
Base Pattern Module
Abstract base class for all price action patterns
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BasePattern(ABC):
    """Abstract base class for price action patterns"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize pattern detector
        
        Args:
            config: Pattern configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        
    @abstractmethod
    def detect(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect pattern in candle data
        
        Args:
            candles: DataFrame with OHLCV data
            
        Returns:
            Pattern details if detected, None otherwise
        """
        pass
    
    @abstractmethod
    def get_required_candles(self) -> int:
        """
        Get number of candles required for pattern detection
        
        Returns:
            Number of candles needed
        """
        pass
    
    def validate_candles(self, candles: pd.DataFrame) -> bool:
        """
        Validate if candles DataFrame has required data
        
        Args:
            candles: DataFrame to validate
            
        Returns:
            bool: True if valid
        """
        if candles is None or candles.empty:
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume', 'time']
        if not all(col in candles.columns for col in required_columns):
            logger.error(f"Missing required columns in candles DataFrame")
            return False
        
        if len(candles) < self.get_required_candles():
            logger.error(f"Insufficient candles for {self.name} pattern")
            return False
        
        return True
    
    def calculate_pattern_strength(self, candles: pd.DataFrame) -> float:
        """
        Calculate pattern strength/reliability score
        
        Args:
            candles: DataFrame with pattern
            
        Returns:
            Strength score (0-1)
        """
        # Default implementation - can be overridden
        return 0.5
    
    def get_pattern_info(self) -> Dict[str, Any]:
        """
        Get pattern information
        
        Returns:
            Pattern details dictionary
        """
        return {
            'name': self.name,
            'required_candles': self.get_required_candles(),
            'config': self.config
        }
