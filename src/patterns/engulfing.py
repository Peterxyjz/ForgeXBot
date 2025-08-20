"""
Engulfing Pattern Detector
Detects bullish and bearish engulfing patterns
"""

import pandas as pd
from typing import Optional, Dict, Any
from .base_pattern import BasePattern
import logging

logger = logging.getLogger(__name__)


class BullishEngulfing(BasePattern):
    """Bullish Engulfing pattern detector"""
    
    def get_required_candles(self) -> int:
        return 2
    
    def detect(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect bullish engulfing pattern
        
        Pattern criteria:
        - Previous candle is bearish (close < open)
        - Current candle is bullish (close > open)
        - Current candle body completely engulfs previous candle body
        """
        if not self.validate_candles(candles):
            return None
        
        # Get last two candles
        prev_candle = candles.iloc[-2]
        curr_candle = candles.iloc[-1]
        
        # Check if previous candle is bearish
        if prev_candle['close'] >= prev_candle['open']:
            return None
        
        # Check if current candle is bullish
        if curr_candle['close'] <= curr_candle['open']:
            return None
        
        # Check if current candle engulfs previous
        prev_body_high = max(prev_candle['open'], prev_candle['close'])
        prev_body_low = min(prev_candle['open'], prev_candle['close'])
        curr_body_high = max(curr_candle['open'], curr_candle['close'])
        curr_body_low = min(curr_candle['open'], curr_candle['close'])
        
        if curr_body_high > prev_body_high and curr_body_low < prev_body_low:
            # Pattern detected
            strength = self.calculate_strength(prev_candle, curr_candle)
            
            return {
                'pattern': 'Bullish Engulfing',
                'type': 'bullish',
                'candle_time': curr_candle['time'],
                'candle_close': curr_candle['close'],
                'strength': strength,
                'details': {
                    'prev_candle': {
                        'open': prev_candle['open'],
                        'close': prev_candle['close'],
                        'high': prev_candle['high'],
                        'low': prev_candle['low']
                    },
                    'curr_candle': {
                        'open': curr_candle['open'],
                        'close': curr_candle['close'],
                        'high': curr_candle['high'],
                        'low': curr_candle['low']
                    }
                }
            }
        
        return None
    
    def calculate_strength(self, prev_candle: pd.Series, curr_candle: pd.Series) -> float:
        """Calculate pattern strength based on volume and body size"""
        strength = 0.5
        
        # Volume confirmation (if current volume > previous)
        if curr_candle['volume'] > prev_candle['volume'] * 1.5:
            strength += 0.2
        
        # Body size ratio
        curr_body = abs(curr_candle['close'] - curr_candle['open'])
        prev_body = abs(prev_candle['close'] - prev_candle['open'])
        if prev_body > 0:
            body_ratio = curr_body / prev_body
            if body_ratio > 2:
                strength += 0.2
            elif body_ratio > 1.5:
                strength += 0.1
        
        return min(strength, 1.0)


class BearishEngulfing(BasePattern):
    """Bearish Engulfing pattern detector"""
    
    def get_required_candles(self) -> int:
        return 2
    
    def detect(self, candles: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detect bearish engulfing pattern
        
        Pattern criteria:
        - Previous candle is bullish (close > open)
        - Current candle is bearish (close < open)
        - Current candle body completely engulfs previous candle body
        """
        if not self.validate_candles(candles):
            return None
        
        # Get last two candles
        prev_candle = candles.iloc[-2]
        curr_candle = candles.iloc[-1]
        
        # Check if previous candle is bullish
        if prev_candle['close'] <= prev_candle['open']:
            return None
        
        # Check if current candle is bearish
        if curr_candle['close'] >= curr_candle['open']:
            return None
        
        # Check if current candle engulfs previous
        prev_body_high = max(prev_candle['open'], prev_candle['close'])
        prev_body_low = min(prev_candle['open'], prev_candle['close'])
        curr_body_high = max(curr_candle['open'], curr_candle['close'])
        curr_body_low = min(curr_candle['open'], curr_candle['close'])
        
        if curr_body_high > prev_body_high and curr_body_low < prev_body_low:
            # Pattern detected
            strength = self.calculate_strength(prev_candle, curr_candle)
            
            return {
                'pattern': 'Bearish Engulfing',
                'type': 'bearish',
                'candle_time': curr_candle['time'],
                'candle_close': curr_candle['close'],
                'strength': strength,
                'details': {
                    'prev_candle': {
                        'open': prev_candle['open'],
                        'close': prev_candle['close'],
                        'high': prev_candle['high'],
                        'low': prev_candle['low']
                    },
                    'curr_candle': {
                        'open': curr_candle['open'],
                        'close': curr_candle['close'],
                        'high': curr_candle['high'],
                        'low': curr_candle['low']
                    }
                }
            }
        
        return None
    
    def calculate_strength(self, prev_candle: pd.Series, curr_candle: pd.Series) -> float:
        """Calculate pattern strength based on volume and body size"""
        strength = 0.5
        
        # Volume confirmation
        if curr_candle['volume'] > prev_candle['volume'] * 1.5:
            strength += 0.2
        
        # Body size ratio
        curr_body = abs(curr_candle['close'] - curr_candle['open'])
        prev_body = abs(prev_candle['close'] - prev_candle['open'])
        if prev_body > 0:
            body_ratio = curr_body / prev_body
            if body_ratio > 2:
                strength += 0.2
            elif body_ratio > 1.5:
                strength += 0.1
        
        return min(strength, 1.0)
