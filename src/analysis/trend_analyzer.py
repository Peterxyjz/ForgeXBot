"""
Trend Analysis Module
Identifies market trends using EMA and price structure
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction enumeration"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class TrendAnalyzer:
    """Analyzes market trends using multiple methods"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize trend analyzer
        
        Args:
            config: Trend analysis configuration
        """
        self.config = config or {}
        
        # EMA periods
        self.ema_short_period = self.config.get('ema_short_period', 20)
        self.ema_long_period = self.config.get('ema_long_period', 50)
        
        # Trend thresholds
        self.trend_strength_threshold = self.config.get('trend_strength_threshold', 0.0001)  # 0.01%
        self.sideways_threshold = self.config.get('sideways_threshold', 0.0005)  # 0.05%
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average
        
        Args:
            data: Price data series
            period: EMA period
            
        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def get_comprehensive_trend(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive trend analysis
        
        Args:
            candles: DataFrame with OHLC data
            
        Returns:
            Trend analysis dictionary
        """
        if len(candles) < max(self.ema_short_period, self.ema_long_period):
            return {
                'direction': TrendDirection.UNKNOWN,
                'strength': 0,
                'confidence': 0,
                'candles_with_indicators': candles
            }
        
        # Calculate EMAs
        candles_copy = candles.copy()
        candles_copy['ema_short'] = self.calculate_ema(candles_copy['close'], self.ema_short_period)
        candles_copy['ema_long'] = self.calculate_ema(candles_copy['close'], self.ema_long_period)
        
        # Get latest values
        latest_close = candles_copy['close'].iloc[-1]
        latest_ema_short = candles_copy['ema_short'].iloc[-1]
        latest_ema_long = candles_copy['ema_long'].iloc[-1]
        
        # Determine trend direction
        direction = self._determine_trend_direction(latest_ema_short, latest_ema_long)
        
        # Calculate trend strength
        strength = self._calculate_trend_strength(candles_copy)
        
        # Calculate confidence
        confidence = self._calculate_trend_confidence(candles_copy, direction)
        
        return {
            'direction': direction,
            'strength': strength,
            'confidence': confidence,
            'ema_short': latest_ema_short,
            'ema_long': latest_ema_long,
            'current_price': latest_close,
            'candles_with_indicators': candles_copy
        }
    
    def _determine_trend_direction(self, ema_short: float, ema_long: float) -> TrendDirection:
        """Determine trend direction based on EMA relationship"""
        if pd.isna(ema_short) or pd.isna(ema_long):
            return TrendDirection.UNKNOWN
        
        ema_diff = abs(ema_short - ema_long) / ema_long
        
        if ema_diff < self.sideways_threshold:
            return TrendDirection.SIDEWAYS
        elif ema_short > ema_long:
            return TrendDirection.UPTREND
        else:
            return TrendDirection.DOWNTREND
    
    def _calculate_trend_strength(self, candles: pd.DataFrame) -> float:
        """Calculate trend strength (0-1)"""
        if len(candles) < 10:
            return 0
        
        try:
            # Calculate slope of EMA short over last 10 periods
            recent_ema = candles['ema_short'].tail(10)
            if recent_ema.isna().any():
                return 0
            
            # Linear regression slope
            x = np.arange(len(recent_ema))
            slope = np.polyfit(x, recent_ema, 1)[0]
            
            # Normalize slope relative to price
            avg_price = recent_ema.mean()
            if avg_price == 0:
                return 0
            
            normalized_slope = abs(slope) / avg_price
            
            # Convert to 0-1 scale
            strength = min(normalized_slope / self.trend_strength_threshold, 1.0)
            
            return strength
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0
    
    def _calculate_trend_confidence(self, candles: pd.DataFrame, direction: TrendDirection) -> float:
        """Calculate confidence in trend direction (0-1)"""
        if direction == TrendDirection.UNKNOWN or len(candles) < 20:
            return 0
        
        try:
            # Count consecutive periods where EMA relationship holds
            recent_candles = candles.tail(20)
            consistent_periods = 0
            
            for i in range(len(recent_candles)):
                ema_short = recent_candles['ema_short'].iloc[i]
                ema_long = recent_candles['ema_long'].iloc[i]
                
                if pd.isna(ema_short) or pd.isna(ema_long):
                    continue
                
                if direction == TrendDirection.UPTREND and ema_short > ema_long:
                    consistent_periods += 1
                elif direction == TrendDirection.DOWNTREND and ema_short < ema_long:
                    consistent_periods += 1
                elif direction == TrendDirection.SIDEWAYS:
                    diff_ratio = abs(ema_short - ema_long) / ema_long
                    if diff_ratio < self.sideways_threshold:
                        consistent_periods += 1
            
            confidence = consistent_periods / len(recent_candles)
            return min(max(confidence, 0), 1)
            
        except Exception as e:
            logger.error(f"Error calculating trend confidence: {e}")
            return 0
    
    def get_ema_context(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Get EMA context for current price
        
        Args:
            candles: DataFrame with EMA indicators
            
        Returns:
            EMA context dictionary
        """
        if 'ema_short' not in candles.columns or 'ema_long' not in candles.columns:
            return {}
        
        latest = candles.iloc[-1]
        current_price = latest['close']
        ema_short = latest.get('ema_short', current_price)
        ema_long = latest.get('ema_long', current_price)
        
        if pd.isna(ema_short) or pd.isna(ema_long):
            return {}
        
        return {
            'price_vs_ema_short': 'above' if current_price > ema_short else 'below',
            'price_vs_ema_long': 'above' if current_price > ema_long else 'below',
            'distance_from_ema20': abs(current_price - ema_short) / current_price,
            'distance_from_ema50': abs(current_price - ema_long) / current_price,
            'ema_separation': abs(ema_short - ema_long) / ema_long
        }
