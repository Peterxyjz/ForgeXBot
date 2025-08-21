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
            config: Configuration parameters
        """
        self.config = config or {}
        self.ema_short_period = self.config.get('ema_short_period', 20)
        self.ema_long_period = self.config.get('ema_long_period', 50)
        self.trend_strength_threshold = self.config.get('trend_strength_threshold', 0.0001)
        self.sideways_threshold = self.config.get('sideways_threshold', 0.0005)
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average
        
        Args:
            data: Price series
            period: EMA period
            
        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def add_technical_indicators(self, candles: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to candle data
        
        Args:
            candles: OHLCV data
            
        Returns:
            DataFrame with added indicators
        """
        df = candles.copy()
        
        # Calculate EMAs
        df['ema20'] = self.calculate_ema(df['close'], self.ema_short_period)
        df['ema50'] = self.calculate_ema(df['close'], self.ema_long_period)
        
        # Price position relative to EMAs
        df['price_vs_ema20'] = (df['close'] - df['ema20']) / df['close']
        df['price_vs_ema50'] = (df['close'] - df['ema50']) / df['close']
        
        # EMA relationship
        df['ema_bullish'] = df['ema20'] > df['ema50']
        df['ema_bearish'] = df['ema20'] < df['ema50']
        
        return df
    
    def identify_trend_by_ema(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Identify trend using EMA crossover and position
        
        Args:
            candles: Candle data with EMA indicators
            
        Returns:
            Trend analysis result
        """
        if len(candles) < self.ema_long_period:
            return {
                'direction': TrendDirection.UNKNOWN,
                'strength': 0.0,
                'method': 'ema',
                'details': 'Insufficient data'
            }
        
        latest = candles.iloc[-1]
        prev = candles.iloc[-2] if len(candles) > 1 else latest
        
        # Current EMA relationship
        ema20 = latest['ema20']
        ema50 = latest['ema50']
        close = latest['close']
        
        # EMA slope (trend strength)
        ema20_slope = (latest['ema20'] - prev['ema20']) / prev['ema20'] if prev['ema20'] != 0 else 0
        ema50_slope = (latest['ema50'] - prev['ema50']) / prev['ema50'] if prev['ema50'] != 0 else 0
        
        # Determine trend direction
        if ema20 > ema50 and close > ema20:
            # Strong uptrend
            if ema20_slope > self.trend_strength_threshold:
                direction = TrendDirection.UPTREND
                strength = min(abs(ema20_slope) * 1000, 1.0)  # Scale to 0-1
            else:
                direction = TrendDirection.SIDEWAYS
                strength = 0.3
        elif ema20 < ema50 and close < ema20:
            # Strong downtrend
            if ema20_slope < -self.trend_strength_threshold:
                direction = TrendDirection.DOWNTREND
                strength = min(abs(ema20_slope) * 1000, 1.0)
            else:
                direction = TrendDirection.SIDEWAYS
                strength = 0.3
        else:
            # Mixed signals or sideways
            direction = TrendDirection.SIDEWAYS
            strength = 0.2
        
        return {
            'direction': direction,
            'strength': strength,
            'method': 'ema',
            'details': {
                'ema20': ema20,
                'ema50': ema50,
                'close': close,
                'ema20_slope': ema20_slope,
                'ema50_slope': ema50_slope,
                'price_vs_ema20': latest['price_vs_ema20'],
                'price_vs_ema50': latest['price_vs_ema50']
            }
        }
    
    def identify_trend_by_structure(self, candles: pd.DataFrame, lookback: int = 10) -> Dict[str, Any]:
        """
        Identify trend using price structure (HH-HL vs LH-LL)
        
        Args:
            candles: Candle data
            lookback: Number of periods to analyze
            
        Returns:
            Trend analysis result
        """
        if len(candles) < lookback:
            return {
                'direction': TrendDirection.UNKNOWN,
                'strength': 0.0,
                'method': 'structure',
                'details': 'Insufficient data'
            }
        
        # Get recent data
        recent = candles.tail(lookback)
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Find peaks and troughs
        higher_highs = 0
        lower_lows = 0
        higher_lows = 0
        lower_highs = 0
        
        for i in range(2, len(highs)):
            # Check for higher highs
            if highs[i] > highs[i-1] and highs[i-1] > highs[i-2]:
                higher_highs += 1
            elif highs[i] < highs[i-1] and highs[i-1] < highs[i-2]:
                lower_highs += 1
                
            # Check for higher lows  
            if lows[i] > lows[i-1] and lows[i-1] > lows[i-2]:
                higher_lows += 1
            elif lows[i] < lows[i-1] and lows[i-1] < lows[i-2]:
                lower_lows += 1
        
        # Determine trend
        uptrend_score = higher_highs + higher_lows
        downtrend_score = lower_highs + lower_lows
        
        if uptrend_score > downtrend_score and uptrend_score > 0:
            direction = TrendDirection.UPTREND
            strength = min(uptrend_score / (lookback / 2), 1.0)
        elif downtrend_score > uptrend_score and downtrend_score > 0:
            direction = TrendDirection.DOWNTREND
            strength = min(downtrend_score / (lookback / 2), 1.0)
        else:
            direction = TrendDirection.SIDEWAYS
            strength = 0.2
        
        return {
            'direction': direction,
            'strength': strength,
            'method': 'structure',
            'details': {
                'higher_highs': higher_highs,
                'higher_lows': higher_lows,
                'lower_highs': lower_highs,
                'lower_lows': lower_lows,
                'uptrend_score': uptrend_score,
                'downtrend_score': downtrend_score
            }
        }
    
    def get_comprehensive_trend(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive trend analysis combining multiple methods
        
        Args:
            candles: Candle data
            
        Returns:
            Comprehensive trend analysis
        """
        # Add technical indicators
        df = self.add_technical_indicators(candles)
        
        # Get trends from different methods
        ema_trend = self.identify_trend_by_ema(df)
        structure_trend = self.identify_trend_by_structure(df)
        
        # Combine results (EMA has higher weight)
        ema_weight = 0.7
        structure_weight = 0.3
        
        # Convert direction to numeric for averaging
        direction_map = {
            TrendDirection.UPTREND: 1,
            TrendDirection.SIDEWAYS: 0,
            TrendDirection.DOWNTREND: -1,
            TrendDirection.UNKNOWN: 0
        }
        
        ema_dir_val = direction_map[ema_trend['direction']]
        structure_dir_val = direction_map[structure_trend['direction']]
        
        combined_direction_val = (ema_dir_val * ema_weight + 
                                 structure_dir_val * structure_weight)
        
        # Convert back to direction
        if combined_direction_val > 0.3:
            final_direction = TrendDirection.UPTREND
        elif combined_direction_val < -0.3:
            final_direction = TrendDirection.DOWNTREND
        else:
            final_direction = TrendDirection.SIDEWAYS
        
        # Combined strength
        combined_strength = (ema_trend['strength'] * ema_weight + 
                           structure_trend['strength'] * structure_weight)
        
        return {
            'direction': final_direction,
            'strength': combined_strength,
            'confidence': min((ema_trend['strength'] + structure_trend['strength']) / 2, 1.0),
            'ema_analysis': ema_trend,
            'structure_analysis': structure_trend,
            'candles_with_indicators': df
        }
    
    def get_ema_context(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Get EMA context for pattern validation
        
        Args:
            candles: Candle data with indicators
            
        Returns:
            EMA context information
        """
        if 'ema20' not in candles.columns:
            candles = self.add_technical_indicators(candles)
        
        latest = candles.iloc[-1]
        
        return {
            'price_above_ema20': latest['close'] > latest['ema20'],
            'price_above_ema50': latest['close'] > latest['ema50'],
            'ema20_above_ema50': latest['ema20'] > latest['ema50'],
            'distance_from_ema20': abs(latest['close'] - latest['ema20']) / latest['close'],
            'distance_from_ema50': abs(latest['close'] - latest['ema50']) / latest['close'],
            'ema20_value': latest['ema20'],
            'ema50_value': latest['ema50'],
            'close_value': latest['close']
        }
