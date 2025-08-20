"""
Single Candle Patterns
Detects Hammer, Shooting Star, and Doji patterns
"""

import pandas as pd
from typing import Optional, Dict, Any
from .base_pattern import BasePattern
import logging

logger = logging.getLogger(__name__)


class Hammer(BasePattern):
    """Hammer pattern detector (bullish reversal)"""
    
    def get_required_candles(self) -> int:
        return 1
    
    def detect(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect hammer pattern
        
        Pattern criteria (CORRECTED ALGORITHM):
        - Small body: abs(Close[n] - Open[n]) <= (High[n] - Low[n]) * 0.25
        - Long lower shadow: (min(Open[n], Close[n]) - Low[n]) >= 2 * abs(Close[n] - Open[n])
        - Short upper shadow: (High[n] - max(Open[n], Close[n])) <= (High[n] - Low[n]) * 0.1
        - Typically appears after downtrend
        """
        if not self.validate_candles(candles):
            return None
        
        candle = candles.iloc[-1]
        
        # Calculate metrics
        body = abs(candle['close'] - candle['open'])
        range_total = candle['high'] - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        # Avoid division by zero
        if range_total == 0:
            return None
        
        # CORRECTED HAMMER ALGORITHM
        body_ratio = body / range_total
        
        # 1. Small body: <= 25% of total range
        if body_ratio > 0.25:
            return None
        
        # 2. Long lower shadow: >= 2 * body
        if body == 0:
            # Special case: body is 0 (doji-like), lower shadow should be >= 60% of range
            if lower_shadow < range_total * 0.6:
                return None
        else:
            if lower_shadow < body * 2.0:
                return None
        
        # 3. Short upper shadow: <= 10% of total range
        if upper_shadow > range_total * 0.1:
            return None
        
        # Pattern detected
        strength = self.calculate_strength(candle, candles)
        
        return {
            'pattern': 'Hammer',
            'type': 'bullish',
            'candle_time': candle['time'],
            'candle_close': candle['close'],
            'strength': strength,
            'details': {
                'body_ratio': body_ratio,
                'lower_shadow': lower_shadow,
                'upper_shadow': upper_shadow,
                'candle': {
                    'open': candle['open'],
                    'close': candle['close'],
                    'high': candle['high'],
                    'low': candle['low']
                }
            }
        }
    
    def calculate_strength(self, candle: pd.Series, candles: pd.DataFrame) -> float:
        """Calculate pattern strength"""
        strength = 0.5
        
        # Check if in downtrend (simple check - last 5 candles)
        if len(candles) >= 5:
            trend_candles = candles.iloc[-5:-1]
            if trend_candles['close'].mean() < trend_candles['close'].iloc[0]:
                strength += 0.2
        
        # Volume confirmation
        if len(candles) >= 2:
            if candle['volume'] > candles['volume'].iloc[-2] * 1.2:
                strength += 0.1
        
        # Shadow ratio strength
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        if body > 0:
            ratio = lower_shadow / body
            if ratio > 3:
                strength += 0.2
            elif ratio > 2.5:
                strength += 0.1
        
        return min(strength, 1.0)


class ShootingStar(BasePattern):
    """Shooting Star pattern detector (bearish reversal)"""
    
    def get_required_candles(self) -> int:
        return 1
    
    def detect(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect shooting star pattern
        
        Pattern criteria (CORRECTED ALGORITHM):
        - Small body: abs(Close[n] - Open[n]) <= (High[n] - Low[n]) * 0.25
        - Long upper shadow: (High[n] - max(Open[n], Close[n])) >= 2 * abs(Close[n] - Open[n])
        - Short lower shadow: (min(Open[n], Close[n]) - Low[n]) <= (High[n] - Low[n]) * 0.1
        - Typically appears after uptrend
        """
        if not self.validate_candles(candles):
            return None
        
        candle = candles.iloc[-1]
        
        # Calculate metrics
        body = abs(candle['close'] - candle['open'])
        range_total = candle['high'] - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        # Avoid division by zero
        if range_total == 0:
            return None
        
        # CORRECTED SHOOTING STAR ALGORITHM
        body_ratio = body / range_total
        
        # 1. Small body: <= 25% of total range
        if body_ratio > 0.25:
            return None
        
        # 2. Long upper shadow: >= 2 * body
        if body == 0:
            # Special case: body is 0 (doji-like), upper shadow should be >= 60% of range
            if upper_shadow < range_total * 0.6:
                return None
        else:
            if upper_shadow < body * 2.0:
                return None
        
        # 3. Short lower shadow: <= 10% of total range
        if lower_shadow > range_total * 0.1:
            return None
        
        # Pattern detected
        strength = self.calculate_strength(candle, candles)
        
        return {
            'pattern': 'Shooting Star',
            'type': 'bearish',
            'candle_time': candle['time'],
            'candle_close': candle['close'],
            'strength': strength,
            'details': {
                'body_ratio': body_ratio,
                'upper_shadow': upper_shadow,
                'lower_shadow': lower_shadow,
                'candle': {
                    'open': candle['open'],
                    'close': candle['close'],
                    'high': candle['high'],
                    'low': candle['low']
                }
            }
        }
    
    def calculate_strength(self, candle: pd.Series, candles: pd.DataFrame) -> float:
        """Calculate pattern strength"""
        strength = 0.5
        
        # Check if in uptrend (simple check - last 5 candles)
        if len(candles) >= 5:
            trend_candles = candles.iloc[-5:-1]
            if trend_candles['close'].mean() > trend_candles['close'].iloc[0]:
                strength += 0.2
        
        # Volume confirmation
        if len(candles) >= 2:
            if candle['volume'] > candles['volume'].iloc[-2] * 1.2:
                strength += 0.1
        
        # Shadow ratio strength
        body = abs(candle['close'] - candle['open'])
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        if body > 0:
            ratio = upper_shadow / body
            if ratio > 3:
                strength += 0.2
            elif ratio > 2.5:
                strength += 0.1
        
        return min(strength, 1.0)


class Doji(BasePattern):
    """Doji pattern detector (indecision/reversal)"""
    
    def get_required_candles(self) -> int:
        return 1
    
    def detect(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect doji pattern
        
        Pattern criteria:
        - Very small body (open ≈ close)
        - Body less than 10% of total range
        - Shadows on both sides
        """
        if not self.validate_candles(candles):
            return None
        
        candle = candles.iloc[-1]
        
        # Calculate metrics
        body = abs(candle['close'] - candle['open'])
        range_total = candle['high'] - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        
        # Avoid division by zero
        if range_total == 0:
            return None
        
        # Check doji criteria
        doji_threshold = self.config.get('doji_threshold', 0.1)
        body_ratio = body / range_total if range_total > 0 else 0
        
        # Very small body (less than threshold of range)
        if body_ratio > doji_threshold:
            return None
        
        # Should have shadows on both sides (at least some presence)
        min_shadow = range_total * 0.1
        if upper_shadow < min_shadow or lower_shadow < min_shadow:
            return None
        
        # Determine doji type
        doji_type = self.classify_doji(upper_shadow, lower_shadow, range_total)
        
        # Pattern detected
        strength = self.calculate_strength(candle, candles)
        
        return {
            'pattern': 'Doji',
            'type': 'neutral',  # Can be bullish or bearish depending on context
            'subtype': doji_type,
            'candle_time': candle['time'],
            'candle_close': candle['close'],
            'strength': strength,
            'details': {
                'body_ratio': body_ratio,
                'upper_shadow': upper_shadow,
                'lower_shadow': lower_shadow,
                'candle': {
                    'open': candle['open'],
                    'close': candle['close'],
                    'high': candle['high'],
                    'low': candle['low']
                }
            }
        }
    
    def classify_doji(self, upper_shadow: float, lower_shadow: float, range_total: float) -> str:
        """Classify the type of doji"""
        if range_total == 0:
            return 'standard'
        
        upper_ratio = upper_shadow / range_total
        lower_ratio = lower_shadow / range_total
        
        # Dragonfly Doji (bullish)
        if upper_ratio < 0.1 and lower_ratio > 0.6:
            return 'dragonfly'
        
        # Gravestone Doji (bearish)
        if lower_ratio < 0.1 and upper_ratio > 0.6:
            return 'gravestone'
        
        # Long-legged Doji
        if upper_ratio > 0.3 and lower_ratio > 0.3:
            return 'long_legged'
        
        return 'standard'
    
    def calculate_strength(self, candle: pd.Series, candles: pd.DataFrame) -> float:
        """Calculate pattern strength"""
        strength = 0.5
        
        # Volume spike
        if len(candles) >= 2:
            avg_volume = candles['volume'].iloc[-6:-1].mean() if len(candles) >= 6 else candles['volume'].iloc[:-1].mean()
            if candle['volume'] > avg_volume * 1.5:
                strength += 0.2
        
        # Position in trend (doji after strong move is stronger signal)
        if len(candles) >= 5:
            recent_move = abs(candles['close'].iloc[-5] - candles['close'].iloc[-2])
            avg_range = candles['range'].iloc[-5:].mean() if 'range' in candles.columns else (candles['high'] - candles['low']).iloc[-5:].mean()
            if recent_move > avg_range * 3:
                strength += 0.2
        
        # Doji type strength
        doji_type = self.classify_doji(
            candle['high'] - max(candle['open'], candle['close']),
            min(candle['open'], candle['close']) - candle['low'],
            candle['high'] - candle['low']
        )
        if doji_type in ['dragonfly', 'gravestone']:
            strength += 0.1
        
        return min(strength, 1.0)
