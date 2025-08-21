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
            candles: OHLCV data
            window: Window size for pivot detection
            
        Returns:
            Dictionary with pivot highs and lows
        """
        highs = candles['high'].values
        lows = candles['low'].values
        times = candles.index.values if hasattr(candles.index, 'values') else range(len(candles))
        
        pivot_highs = []
        pivot_lows = []
        
        for i in range(window, len(highs) - window):
            # Check for pivot high
            is_pivot_high = True
            for j in range(i - window, i + window + 1):
                if j != i and highs[j] >= highs[i]:
                    is_pivot_high = False
                    break
            
            if is_pivot_high:
                pivot_highs.append({
                    'index': i,
                    'time': times[i],
                    'price': highs[i],
                    'type': 'resistance'
                })
            
            # Check for pivot low
            is_pivot_low = True
            for j in range(i - window, i + window + 1):
                if j != i and lows[j] <= lows[i]:
                    is_pivot_low = False
                    break
            
            if is_pivot_low:
                pivot_lows.append({
                    'index': i,
                    'time': times[i],
                    'price': lows[i],
                    'type': 'support'
                })
        
        return {
            'pivot_highs': pivot_highs,
            'pivot_lows': pivot_lows
        }
    
    def cluster_levels(self, levels: List[Dict], current_price: float) -> List[Dict]:
        """
        Cluster nearby support/resistance levels
        
        Args:
            levels: List of support/resistance levels
            current_price: Current market price
            
        Returns:
            Clustered levels
        """
        if not levels:
            return []
        
        # Sort levels by price
        sorted_levels = sorted(levels, key=lambda x: x['price'])
        clustered = []
        
        for level in sorted_levels:
            # Check if this level is close to any existing cluster
            merged = False
            threshold = current_price * self.proximity_threshold
            
            for cluster in clustered:
                if abs(level['price'] - cluster['price']) <= threshold:
                    # Merge into existing cluster
                    cluster['touches'] += level.get('touches', 1)
                    cluster['strength'] = max(cluster['strength'], level.get('strength', 1))
                    cluster['last_touch'] = max(cluster.get('last_touch', level['index']), level['index'])
                    merged = True
                    break
            
            if not merged:
                # Create new cluster
                clustered.append({
                    'price': level['price'],
                    'type': level['type'],
                    'touches': level.get('touches', 1),
                    'strength': level.get('strength', 1),
                    'last_touch': level['index'],
                    'distance_from_current': abs(level['price'] - current_price) / current_price
                })
        
        return clustered
    
    def calculate_level_strength(self, level_price: float, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate strength of a support/resistance level
        
        Args:
            level_price: Price level to analyze
            candles: OHLCV data
            
        Returns:
            Level strength metrics
        """
        threshold = level_price * self.proximity_threshold
        touches = 0
        bounces = 0
        breaks = 0
        
        for i in range(len(candles)):
            candle = candles.iloc[i]
            
            # Check if price touched the level
            if (candle['low'] <= level_price + threshold and 
                candle['high'] >= level_price - threshold):
                touches += 1
                
                # Check for bounce (close away from level)
                if abs(candle['close'] - level_price) > threshold:
                    bounces += 1
                
                # Check for break (close beyond level significantly)
                if (candle['close'] > level_price + threshold * 2 or 
                    candle['close'] < level_price - threshold * 2):
                    breaks += 1
        
        # Calculate strength score
        strength = touches * 0.3 + bounces * 0.5 - breaks * 0.2
        strength = max(0, min(strength, 5))  # Normalize to 0-5
        
        return {
            'touches': touches,
            'bounces': bounces,
            'breaks': breaks,
            'strength': strength
        }
    
    def find_support_resistance_levels(self, candles: pd.DataFrame) -> Dict[str, Any]:
        """
        Find key support and resistance levels
        
        Args:
            candles: OHLCV data
            
        Returns:
            Support and resistance analysis
        """
        if len(candles) < self.lookback_periods:
            return {
                'support_levels': [],
                'resistance_levels': [],
                'nearest_support': None,
                'nearest_resistance': None
            }
        
        # Use recent data
        recent_candles = candles.tail(self.lookback_periods)
        current_price = recent_candles.iloc[-1]['close']
        
        # Find pivot points
        pivots = self.find_pivot_points(recent_candles)
        
        # Process resistance levels (pivot highs)
        resistance_candidates = []
        for pivot in pivots['pivot_highs']:
            strength_info = self.calculate_level_strength(pivot['price'], recent_candles)
            if strength_info['touches'] >= self.min_touches:
                resistance_candidates.append({
                    'price': pivot['price'],
                    'type': 'resistance',
                    'index': pivot['index'],
                    'touches': strength_info['touches'],
                    'strength': strength_info['strength']
                })
        
        # Process support levels (pivot lows)
        support_candidates = []
        for pivot in pivots['pivot_lows']:
            strength_info = self.calculate_level_strength(pivot['price'], recent_candles)
            if strength_info['touches'] >= self.min_touches:
                support_candidates.append({
                    'price': pivot['price'],
                    'type': 'support',
                    'index': pivot['index'],
                    'touches': strength_info['touches'],
                    'strength': strength_info['strength']
                })
        
        # Cluster nearby levels
        resistance_levels = self.cluster_levels(resistance_candidates, current_price)
        support_levels = self.cluster_levels(support_candidates, current_price)
        
        # Sort by distance from current price
        resistance_levels.sort(key=lambda x: x['distance_from_current'])
        support_levels.sort(key=lambda x: x['distance_from_current'])
        
        # Find nearest levels
        nearest_resistance = None
        nearest_support = None
        
        for level in resistance_levels:
            if level['price'] > current_price:
                nearest_resistance = level
                break
        
        for level in support_levels:
            if level['price'] < current_price:
                nearest_support = level
                break
        
        return {
            'support_levels': support_levels[:5],  # Top 5 support levels
            'resistance_levels': resistance_levels[:5],  # Top 5 resistance levels
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'current_price': current_price
        }
    
    def get_sr_context_for_pattern(self, pattern_price: float, sr_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get support/resistance context for a pattern
        
        Args:
            pattern_price: Price where pattern occurred
            sr_analysis: Support/resistance analysis
            
        Returns:
            Context information
        """
        current_price = sr_analysis['current_price']
        proximity_threshold = current_price * self.proximity_threshold * 2  # Wider threshold for patterns
        
        # Check proximity to support/resistance levels
        near_resistance = False
        near_support = False
        
        resistance_distance = float('inf')
        support_distance = float('inf')
        
        # Check nearest resistance
        if sr_analysis['nearest_resistance']:
            resistance_distance = abs(pattern_price - sr_analysis['nearest_resistance']['price'])
            if resistance_distance <= proximity_threshold:
                near_resistance = True
        
        # Check nearest support
        if sr_analysis['nearest_support']:
            support_distance = abs(pattern_price - sr_analysis['nearest_support']['price'])
            if support_distance <= proximity_threshold:
                near_support = True
        
        return {
            'near_resistance': near_resistance,
            'near_support': near_support,
            'resistance_distance': resistance_distance / current_price if resistance_distance != float('inf') else None,
            'support_distance': support_distance / current_price if support_distance != float('inf') else None,
            'nearest_resistance': sr_analysis['nearest_resistance'],
            'nearest_support': sr_analysis['nearest_support']
        }
