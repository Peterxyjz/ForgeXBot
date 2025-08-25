"""
Support and Resistance Analysis Module
Identifies key support and resistance levels
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SupportResistanceAnalyzer:
    """Analyzes support and resistance levels"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize support/resistance analyzer
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        self.lookback_periods = self.config.get('sr_lookback_periods', 20)
        self.min_touches = self.config.get('sr_min_touches', 2)
        self.proximity_threshold = self.config.get('sr_proximity_threshold', 0.001)  # 0.1%
        
    def find_pivot_points(self, candles: pd.DataFrame, window: int = 5) -> Dict[str, List[Dict]]:
        """
        Find pivot highs and lows
        
        Args:
            candles: DataFrame with OHLC data
            window: Window size for pivot detection
            
        Returns:
            Dictionary with pivot highs and lows
        """
        if len(candles) < window * 2 + 1:
            return {'highs': [], 'lows': []}
        
        highs = []
        lows = []
        
        for i in range(window, len(candles) - window):
            # Check for pivot high
            current_high = candles.iloc[i]['high']
            is_pivot_high = True
            
            for j in range(i - window, i + window + 1):
                if j != i and candles.iloc[j]['high'] >= current_high:
                    is_pivot_high = False
                    break
            
            if is_pivot_high:
                highs.append({
                    'index': i,
                    'price': current_high,
                    'time': candles.iloc[i]['time']
                })
            
            # Check for pivot low
            current_low = candles.iloc[i]['low']
            is_pivot_low = True
            
            for j in range(i - window, i + window + 1):
                if j != i and candles.iloc[j]['low'] <= current_low:
                    is_pivot_low = False
                    break
            
            if is_pivot_low:
                lows.append({
                    'index': i,
                    'price': current_low,
                    'time': candles.iloc[i]['time']
                })
        
        return {'highs': highs, 'lows': lows}
    
    def find_support_resistance_levels(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Find support and resistance levels
        
        Args:
            candles: DataFrame with OHLC data
            
        Returns:
            Support and resistance analysis
        """
        if len(candles) < self.lookback_periods:
            return {'levels': [], 'support_levels': [], 'resistance_levels': []}
        
        # Use recent candles for analysis
        recent_candles = candles.tail(self.lookback_periods)
        
        # Find pivot points
        pivots = self.find_pivot_points(recent_candles)
        
        # Group similar price levels
        resistance_levels = self._group_price_levels([p['price'] for p in pivots['highs']])
        support_levels = self._group_price_levels([p['price'] for p in pivots['lows']])
        
        # Combine all levels
        all_levels = []
        
        for level in resistance_levels:
            all_levels.append({
                'price': level['price'],
                'type': 'resistance',
                'touches': level['count'],
                'strength': self._calculate_level_strength(level, recent_candles)
            })
        
        for level in support_levels:
            all_levels.append({
                'price': level['price'],
                'type': 'support',
                'touches': level['count'],
                'strength': self._calculate_level_strength(level, recent_candles)
            })
        
        # Filter by minimum touches
        significant_levels = [l for l in all_levels if l['touches'] >= self.min_touches]
        
        return {
            'levels': significant_levels,
            'support_levels': [l['price'] for l in significant_levels if l['type'] == 'support'],
            'resistance_levels': [l['price'] for l in significant_levels if l['type'] == 'resistance']
        }
    
    def _group_price_levels(self, prices: List[float]) -> List[Dict]:
        """Group similar price levels together"""
        if not prices:
            return []
        
        grouped = []
        sorted_prices = sorted(prices)
        
        current_group = [sorted_prices[0]]
        
        for i in range(1, len(sorted_prices)):
            price = sorted_prices[i]
            group_avg = sum(current_group) / len(current_group)
            
            # Check if price is within threshold of current group
            if abs(price - group_avg) / group_avg <= self.proximity_threshold:
                current_group.append(price)
            else:
                # Finalize current group
                if len(current_group) >= 1:
                    grouped.append({
                        'price': sum(current_group) / len(current_group),
                        'count': len(current_group),
                        'prices': current_group
                    })
                
                # Start new group
                current_group = [price]
        
        # Add last group
        if len(current_group) >= 1:
            grouped.append({
                'price': sum(current_group) / len(current_group),
                'count': len(current_group),
                'prices': current_group
            })
        
        return grouped
    
    def _calculate_level_strength(self, level: Dict, candles: pd.DataFrame) -> float:
        """Calculate strength of support/resistance level"""
        # Base strength from number of touches
        base_strength = min(level['count'] / 5.0, 1.0)  # Max at 5 touches
        
        # Bonus for recent touches
        level_price = level['price']
        recent_touches = 0
        
        # Check last 10 candles for proximity
        for _, candle in candles.tail(10).iterrows():
            high = candle['high']
            low = candle['low']
            
            # Check if candle touched the level
            if low <= level_price <= high:
                distance = min(abs(high - level_price), abs(low - level_price))
                if distance / level_price <= self.proximity_threshold:
                    recent_touches += 1
        
        recent_bonus = min(recent_touches / 3.0, 0.3)  # Max 30% bonus
        
        return min(base_strength + recent_bonus, 1.0)
    
    def get_sr_context_for_pattern(self, pattern_price: float, sr_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get S/R context for a specific pattern price
        
        Args:
            pattern_price: Price of the pattern
            sr_analysis: Support/resistance analysis result
            
        Returns:
            S/R context dictionary
        """
        context = {
            'near_support': False,
            'near_resistance': False,
            'support_level': None,
            'resistance_level': None,
            'closest_level': None,
            'distance_to_closest': float('inf')
        }
        
        levels = sr_analysis.get('levels', [])
        
        for level in levels:
            level_price = level['price']
            distance = abs(pattern_price - level_price) / pattern_price
            
            # Check if within proximity threshold
            if distance <= self.proximity_threshold:
                if level['type'] == 'support':
                    context['near_support'] = True
                    context['support_level'] = level_price
                elif level['type'] == 'resistance':
                    context['near_resistance'] = True
                    context['resistance_level'] = level_price
            
            # Track closest level
            if distance < context['distance_to_closest']:
                context['distance_to_closest'] = distance
                context['closest_level'] = level_price
        
        return context
