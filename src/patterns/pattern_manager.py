"""
Pattern Manager
Manages all pattern detectors and coordinates pattern detection
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from .base_pattern import BasePattern
from .engulfing import BullishEngulfing, BearishEngulfing
from .single_candles import Hammer, ShootingStar, Doji

logger = logging.getLogger(__name__)


class PatternManager:
    """Manages and coordinates all pattern detectors"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize pattern manager
        
        Args:
            config: Pattern configuration
        """
        self.config = config
        self.patterns = {}
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """Initialize all enabled pattern detectors"""
        pattern_config = self.config.get('patterns', {})
        enabled_patterns = pattern_config.get('enabled', [])
        
        # Map pattern names to classes
        pattern_classes = {
            'bullish_engulfing': BullishEngulfing,
            'bearish_engulfing': BearishEngulfing,
            'hammer': Hammer,
            'shooting_star': ShootingStar,
            'doji': Doji
        }
        
        # Initialize enabled patterns
        for pattern_name in enabled_patterns:
            if pattern_name in pattern_classes:
                pattern_class = pattern_classes[pattern_name]
                self.patterns[pattern_name] = pattern_class(pattern_config)
                logger.info(f"Initialized pattern detector: {pattern_name}")
            else:
                logger.warning(f"Unknown pattern: {pattern_name}")
        
        logger.info(f"Initialized {len(self.patterns)} pattern detectors")
    
    def scan_patterns(
        self, 
        candles: pd.DataFrame,
        symbol: str = None,
        timeframe: str = None
    ) -> List[Dict[str, Any]]:
        """
        Scan for all enabled patterns
        
        Args:
            candles: DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            List of detected patterns
        """
        detected_patterns = []
        
        if candles is None or candles.empty:
            logger.warning("No candles provided for pattern scanning")
            return detected_patterns
        
        # Scan each pattern
        for pattern_name, pattern_detector in self.patterns.items():
            try:
                # Ensure we have enough candles
                required_candles = pattern_detector.get_required_candles()
                if len(candles) < required_candles:
                    continue
                
                # Detect pattern
                result = pattern_detector.detect(candles)
                
                if result:
                    # Add metadata
                    result['symbol'] = symbol
                    result['timeframe'] = timeframe
                    result['pattern_id'] = pattern_name
                    detected_patterns.append(result)
                    
                    logger.info(
                        f"Pattern detected: {result['pattern']} on {symbol} {timeframe}"
                    )
                    
            except Exception as e:
                logger.error(f"Error detecting {pattern_name}: {e}")
                continue
        
        return detected_patterns
    
    def scan_multiple_timeframes(
        self,
        mt5_connector,
        symbol: str,
        timeframes: List[str],
        candle_count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scan patterns across multiple timeframes
        
        Args:
            mt5_connector: MT5 connection instance
            symbol: Trading symbol
            timeframes: List of timeframes to scan
            candle_count: Number of candles to analyze
            
        Returns:
            List of all detected patterns
        """
        all_patterns = []
        
        for timeframe in timeframes:
            try:
                # Get candles
                candles = mt5_connector.get_candles(symbol, timeframe, candle_count)
                
                if candles is not None and not candles.empty:
                    # Scan patterns
                    patterns = self.scan_patterns(candles, symbol, timeframe)
                    all_patterns.extend(patterns)
                else:
                    logger.warning(f"No candles retrieved for {symbol} {timeframe}")
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol} {timeframe}: {e}")
                continue
        
        return all_patterns
    
    def filter_patterns(
        self,
        patterns: List[Dict[str, Any]],
        min_strength: float = 0.5,
        pattern_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter patterns based on criteria
        
        Args:
            patterns: List of detected patterns
            min_strength: Minimum strength threshold
            pattern_types: Filter by pattern types (bullish/bearish/neutral)
            
        Returns:
            Filtered patterns list
        """
        filtered = patterns
        
        # Filter by strength
        if min_strength > 0:
            filtered = [p for p in filtered if p.get('strength', 0) >= min_strength]
        
        # Filter by type
        if pattern_types:
            filtered = [p for p in filtered if p.get('type') in pattern_types]
        
        return filtered
    
    def get_pattern_statistics(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for detected patterns
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            Statistics dictionary
        """
        if not patterns:
            return {
                'total': 0,
                'by_pattern': {},
                'by_type': {},
                'by_symbol': {},
                'by_timeframe': {},
                'avg_strength': 0
            }
        
        stats = {
            'total': len(patterns),
            'by_pattern': {},
            'by_type': {},
            'by_symbol': {},
            'by_timeframe': {},
            'avg_strength': 0
        }
        
        total_strength = 0
        
        for pattern in patterns:
            # By pattern name
            pattern_name = pattern.get('pattern', 'Unknown')
            stats['by_pattern'][pattern_name] = stats['by_pattern'].get(pattern_name, 0) + 1
            
            # By type
            pattern_type = pattern.get('type', 'unknown')
            stats['by_type'][pattern_type] = stats['by_type'].get(pattern_type, 0) + 1
            
            # By symbol
            symbol = pattern.get('symbol', 'Unknown')
            stats['by_symbol'][symbol] = stats['by_symbol'].get(symbol, 0) + 1
            
            # By timeframe
            timeframe = pattern.get('timeframe', 'Unknown')
            stats['by_timeframe'][timeframe] = stats['by_timeframe'].get(timeframe, 0) + 1
            
            # Strength
            total_strength += pattern.get('strength', 0)
        
        stats['avg_strength'] = total_strength / len(patterns) if patterns else 0
        
        return stats
    
    def get_enabled_patterns(self) -> List[str]:
        """Get list of enabled pattern names"""
        return list(self.patterns.keys())
    
    def add_pattern(self, pattern_name: str, pattern_instance: BasePattern):
        """
        Add a custom pattern detector
        
        Args:
            pattern_name: Pattern identifier
            pattern_instance: Pattern detector instance
        """
        self.patterns[pattern_name] = pattern_instance
        logger.info(f"Added custom pattern: {pattern_name}")
    
    def remove_pattern(self, pattern_name: str):
        """
        Remove a pattern detector
        
        Args:
            pattern_name: Pattern identifier
        """
        if pattern_name in self.patterns:
            del self.patterns[pattern_name]
            logger.info(f"Removed pattern: {pattern_name}")
