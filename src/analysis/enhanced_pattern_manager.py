"""
Enhanced Pattern Manager with Trend Context and Signal Filtering
Manages pattern detection with trend analysis and support/resistance context
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from ..patterns.pattern_manager import PatternManager
from .trend_analyzer import TrendAnalyzer, TrendDirection
from .support_resistance import SupportResistanceAnalyzer
from .strength_calculator import StrengthCalculator

logger = logging.getLogger(__name__)


class EnhancedPatternManager(PatternManager):
    """Enhanced pattern manager with trend context and filtering"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize enhanced pattern manager
        
        Args:
            config: Configuration including pattern and analysis settings
        """
        super().__init__(config)
        
        # Initialize analysis modules
        analysis_config = config.get('analysis', {})
        self.trend_analyzer = TrendAnalyzer(analysis_config.get('trend', {}))
        self.sr_analyzer = SupportResistanceAnalyzer(analysis_config.get('support_resistance', {}))
        self.strength_calculator = StrengthCalculator(config)
        
        # Context filtering settings
        self.enable_trend_filtering = analysis_config.get('enable_trend_filtering', True)
        self.enable_sr_filtering = analysis_config.get('enable_sr_filtering', True)
        self.allow_reversal_patterns = analysis_config.get('allow_reversal_patterns', True)
        self.reversal_pattern_names = analysis_config.get('reversal_pattern_names', [
            'hammer', 'shooting_star', 'bullish_engulfing', 'bearish_engulfing'
        ])
        
    def scan_patterns_with_context(
        self, 
        candles: pd.DataFrame,
        symbol: str = None,
        timeframe: str = None
    ) -> List[Dict[str, Any]]:
        """
        Scan for patterns with trend context and filtering
        
        Args:
            candles: DataFrame with OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            List of detected patterns with context
        """
        if candles is None or candles.empty:
            logger.warning("No candles provided for enhanced pattern scanning")
            return []
        
        # Ensure minimum data for analysis
        min_required = max(50, self.trend_analyzer.ema_long_period)
        if len(candles) < min_required:
            logger.warning(f"Insufficient data for enhanced analysis: {len(candles)} < {min_required}")
            # Fall back to basic pattern detection
            return self.scan_patterns(candles, symbol, timeframe)
        
        try:
            # 1. Perform trend analysis
            trend_analysis = self.trend_analyzer.get_comprehensive_trend(candles)
            candles_with_indicators = trend_analysis['candles_with_indicators']
            
            # 2. Perform support/resistance analysis
            sr_analysis = self.sr_analyzer.find_support_resistance_levels(candles)
            
            # 3. Detect basic patterns
            basic_patterns = self.scan_patterns(candles_with_indicators, symbol, timeframe)
            
            # 4. Enhance patterns with context and filtering
            enhanced_patterns = []
            
            for pattern in basic_patterns:
                enhanced_pattern = self._enhance_pattern_with_context(
                    pattern, 
                    trend_analysis, 
                    sr_analysis,
                    candles_with_indicators
                )
                
                # 5. Apply context filtering
                if self._should_keep_pattern(enhanced_pattern):
                    enhanced_patterns.append(enhanced_pattern)
                else:
                    logger.debug(f"Filtered out pattern: {pattern['pattern']} due to context")
            
            return enhanced_patterns
            
        except Exception as e:
            logger.error(f"Error in enhanced pattern scanning: {e}")
            # Fall back to basic scanning
            return self.scan_patterns(candles, symbol, timeframe)
    
    def _enhance_pattern_with_context(
        self,
        pattern: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        sr_analysis: Dict[str, Any],
        candles_with_indicators: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Enhance pattern with trend and S/R context
        
        Args:
            pattern: Basic pattern detection result
            trend_analysis: Trend analysis result
            sr_analysis: Support/resistance analysis
            candles_with_indicators: Candle data with technical indicators
            
        Returns:
            Enhanced pattern with context
        """
        # Get pattern price
        pattern_price = pattern.get('candle_close', candles_with_indicators.iloc[-1]['close'])
        
        # Add trend context
        pattern['trend_context'] = {
            'direction': trend_analysis['direction'].value,
            'strength': trend_analysis['strength'],
            'confidence': trend_analysis['confidence']
        }
        
        # Add EMA context
        ema_context = self.trend_analyzer.get_ema_context(candles_with_indicators)
        pattern['ema_context'] = ema_context
        
        # Add support/resistance context
        sr_context = self.sr_analyzer.get_sr_context_for_pattern(pattern_price, sr_analysis)
        pattern['sr_context'] = sr_context
        
        # Determine pattern classification
        pattern['classification'] = self._classify_pattern_by_context(pattern, trend_analysis)
        
        # Calculate enhanced strength using StrengthCalculator
        pattern['original_strength'] = pattern.get('strength', 0.5)
        
        # Get S/R levels for strength calculation
        sr_levels = [level['price'] for level in sr_analysis.get('levels', [])]
        
        # Calculate enhanced strength
        strength_result = self.strength_calculator.calculate_enhanced_strength(
            candles_with_indicators,
            pattern,
            sr_levels
        )
        
        pattern['enhanced_strength'] = strength_result['total_strength']
        pattern['strength_breakdown'] = strength_result
        pattern['strength'] = pattern['enhanced_strength']
        
        # Add candle index for reference
        pattern['candle_index'] = len(candles_with_indicators) - 1
        
        return pattern
    
    def _classify_pattern_by_context(
        self,
        pattern: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> str:
        """
        Classify pattern based on trend context
        
        Args:
            pattern: Pattern with trend context
            trend_analysis: Trend analysis result
            
        Returns:
            Pattern classification
        """
        pattern_type = pattern.get('type', 'neutral')
        trend_direction = trend_analysis['direction']
        
        # Determine if pattern is with or against trend
        if pattern_type == 'bullish' and trend_direction == TrendDirection.UPTREND:
            return 'trend_continuation'
        elif pattern_type == 'bearish' and trend_direction == TrendDirection.DOWNTREND:
            return 'trend_continuation'
        elif pattern_type == 'bullish' and trend_direction == TrendDirection.DOWNTREND:
            return 'trend_reversal'
        elif pattern_type == 'bearish' and trend_direction == TrendDirection.UPTREND:
            return 'trend_reversal'
        elif trend_direction == TrendDirection.SIDEWAYS:
            return 'range_trading'
        else:
            return 'neutral'
    
    def _calculate_enhanced_strength(
        self,
        pattern: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        sr_context: Dict[str, Any]
    ) -> float:
        """
        Calculate enhanced pattern strength with context
        
        Args:
            pattern: Pattern data
            trend_analysis: Trend analysis
            sr_context: Support/resistance context
            
        Returns:
            Enhanced strength score
        """
        base_strength = pattern.get('original_strength', 0.5)
        enhanced_strength = base_strength
        
        # Trend alignment bonus/penalty
        classification = pattern.get('classification', 'neutral')
        if classification == 'trend_continuation':
            # Bonus for trend continuation patterns
            enhanced_strength += 0.1 * trend_analysis['strength']
        elif classification == 'trend_reversal':
            # Smaller bonus for reversal patterns (they need more confirmation)
            enhanced_strength += 0.05 * trend_analysis['strength']
        
        # Support/resistance proximity bonus
        if sr_context.get('near_resistance') or sr_context.get('near_support'):
            enhanced_strength += 0.15
        
        # EMA proximity bonus
        ema_context = pattern.get('ema_context', {})
        if ema_context.get('distance_from_ema20', 1) < 0.005:  # Within 0.5% of EMA20
            enhanced_strength += 0.1
        
        # Trend confidence multiplier
        confidence_multiplier = 0.8 + (trend_analysis['confidence'] * 0.4)  # 0.8 to 1.2
        enhanced_strength *= confidence_multiplier
        
        # Ensure strength stays within bounds
        return min(max(enhanced_strength, 0.0), 1.0)
    
    def _should_keep_pattern(
        self,
        pattern: Dict[str, Any]
    ) -> bool:
        """
        Determine if pattern should be kept based on context filtering
        
        Args:
            pattern: Enhanced pattern with context
            
        Returns:
            True if pattern should be kept
        """
        # Skip filtering if disabled
        if not self.enable_trend_filtering and not self.enable_sr_filtering:
            return True
        
        classification = pattern.get('classification', 'neutral')
        pattern_name = pattern.get('pattern_id', '')
        trend_context = pattern.get('trend_context', {})
        
        # Trend filtering
        if self.enable_trend_filtering:
            trend_direction = trend_context.get('direction', 'unknown')
            trend_strength = trend_context.get('strength', 0)
            
            # In strong trends, be more selective about counter-trend patterns
            if trend_strength > 0.6:  # Strong trend
                if classification == 'trend_reversal':
                    # Only allow reversal patterns if they're at S/R levels
                    if not self.allow_reversal_patterns:
                        return False
                    
                    sr_context = pattern.get('sr_context', {})
                    if not (sr_context.get('near_resistance') or sr_context.get('near_support')):
                        return False
        
        # Support/Resistance filtering
        if self.enable_sr_filtering:
            sr_context = pattern.get('sr_context', {})
            
            # For reversal patterns, prefer those near S/R levels
            if classification == 'trend_reversal':
                if pattern_name in self.reversal_pattern_names:
                    # Reversal patterns should ideally be near S/R levels
                    if not (sr_context.get('near_resistance') or sr_context.get('near_support')):
                        # Reduce strength but don't completely filter out
                        pattern['strength'] *= 0.7
        
        # Enhanced strength threshold
        min_enhanced_strength = self.config.get('patterns', {}).get('min_enhanced_strength', 0.4)
        if pattern.get('enhanced_strength', 0) < min_enhanced_strength:
            return False
        
        return True
