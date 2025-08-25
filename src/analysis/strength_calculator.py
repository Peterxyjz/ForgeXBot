"""
Enhanced Strength Calculator
Tính toán độ mạnh pattern với nhiều yếu tố nâng cao
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StrengthCalculator:
    """Calculator for enhanced pattern strength"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize strength calculator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Strength calculation weights
        self.weights = {
            'base_pattern': 0.4,      # 40% - Pattern cơ bản (shadow/body ratio)
            'body_comparison': 0.2,   # 20% - So sánh thân nến với nến trước
            'volume_spike': 0.2,      # 20% - Volume spike
            'volatility': 0.1,        # 10% - ATR volatility
            'sr_proximity': 0.1       # 10% - Gần S/R (bonus +20%)
        }
        
        # Thresholds
        self.body_ratio_threshold = 1.2      # Thân nến lớn hơn 1.2x nến trước
        self.volume_spike_threshold = 1.5    # Volume lớn hơn 1.5x trung bình
        self.sr_proximity_threshold = 0.001  # 0.1% gần S/R
        
    def calculate_enhanced_strength(
        self,
        candles: pd.DataFrame,
        pattern_info: Dict[str, Any],
        sr_levels: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Tính toán độ mạnh pattern nâng cao
        
        Args:
            candles: DataFrame với dữ liệu nến
            pattern_info: Thông tin pattern cơ bản
            sr_levels: Danh sách các mức S/R
            
        Returns:
            Dict với strength chi tiết
        """
        if len(candles) < 20:
            logger.warning("Không đủ dữ liệu để tính enhanced strength")
            return self._basic_strength(pattern_info)
        
        try:
            current_candle = candles.iloc[-1]
            
            # 1. Base pattern strength (từ pattern detector)
            base_strength = pattern_info.get('strength', 0.5)
            
            # 2. Body comparison strength
            body_strength = self._calculate_body_comparison(candles)
            
            # 3. Volume spike strength
            volume_strength = self._calculate_volume_spike(candles)
            
            # 4. Volatility strength (ATR-based)
            volatility_strength = self._calculate_volatility_strength(candles)
            
            # 5. S/R proximity bonus
            sr_bonus = self._calculate_sr_proximity(current_candle, sr_levels)
            
            # Tính tổng strength
            total_strength = (
                base_strength * self.weights['base_pattern'] +
                body_strength * self.weights['body_comparison'] +
                volume_strength * self.weights['volume_spike'] +
                volatility_strength * self.weights['volatility']
            )
            
            # Thêm S/R bonus (tối đa +20%)
            if sr_bonus > 0:
                total_strength += 0.2
            
            # Giới hạn 0-1
            total_strength = min(max(total_strength, 0), 1)
            
            return {
                'total_strength': total_strength,
                'base_strength': base_strength,
                'body_strength': body_strength,
                'volume_strength': volume_strength,
                'volatility_strength': volatility_strength,
                'sr_bonus': sr_bonus,
                'breakdown': {
                    'base_pattern': f"{base_strength:.2f} ({self.weights['base_pattern']*100:.0f}%)",
                    'body_comparison': f"{body_strength:.2f} ({self.weights['body_comparison']*100:.0f}%)",
                    'volume_spike': f"{volume_strength:.2f} ({self.weights['volume_spike']*100:.0f}%)",
                    'volatility': f"{volatility_strength:.2f} ({self.weights['volatility']*100:.0f}%)",
                    'sr_proximity': f"+{sr_bonus:.2f}" if sr_bonus > 0 else "0.00"
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced strength: {e}")
            return self._basic_strength(pattern_info)
    
    def _basic_strength(self, pattern_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to basic strength"""
        base_strength = pattern_info.get('strength', 0.5)
        return {
            'total_strength': base_strength,
            'base_strength': base_strength,
            'body_strength': 0,
            'volume_strength': 0,
            'volatility_strength': 0,
            'sr_bonus': 0,
            'breakdown': {
                'base_pattern': f"{base_strength:.2f} (100%)",
                'body_comparison': "0.00 (0%)",
                'volume_spike': "0.00 (0%)",
                'volatility': "0.00 (0%)",
                'sr_proximity': "0.00"
            }
        }
    
    def _calculate_body_comparison(self, candles: pd.DataFrame) -> float:
        """
        Tính strength dựa trên so sánh thân nến
        
        Args:
            candles: DataFrame với dữ liệu nến
            
        Returns:
            Body comparison strength (0-1)
        """
        if len(candles) < 2:
            return 0
        
        try:
            current_candle = candles.iloc[-1]
            previous_candle = candles.iloc[-2]
            
            current_body = abs(current_candle['close'] - current_candle['open'])
            previous_body = abs(previous_candle['close'] - previous_candle['open'])
            
            if previous_body == 0:
                return 0.5  # Neutral nếu nến trước là doji
            
            body_ratio = current_body / previous_body
            
            # Strength tăng theo tỷ lệ thân nến
            if body_ratio >= 2.0:
                return 1.0
            elif body_ratio >= 1.5:
                return 0.8
            elif body_ratio >= self.body_ratio_threshold:
                return 0.6
            elif body_ratio >= 1.0:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating body comparison: {e}")
            return 0
    
    def _calculate_volume_spike(self, candles: pd.DataFrame) -> float:
        """
        Tính strength dựa trên volume spike
        
        Args:
            candles: DataFrame với dữ liệu nến
            
        Returns:
            Volume spike strength (0-1)
        """
        if len(candles) < 11:
            return 0
        
        try:
            current_volume = candles.iloc[-1]['volume']
            
            # Tính volume trung bình 10 nến trước
            avg_volume = candles.iloc[-11:-1]['volume'].mean()
            
            if avg_volume == 0:
                return 0.5  # Neutral nếu không có volume data
            
            volume_ratio = current_volume / avg_volume
            
            # Strength tăng theo volume spike
            if volume_ratio >= 3.0:
                return 1.0
            elif volume_ratio >= 2.5:
                return 0.9
            elif volume_ratio >= 2.0:
                return 0.8
            elif volume_ratio >= self.volume_spike_threshold:
                return 0.6
            elif volume_ratio >= 1.2:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating volume spike: {e}")
            return 0
    
    def _calculate_volatility_strength(self, candles: pd.DataFrame) -> float:
        """
        Tính strength dựa trên ATR volatility
        
        Args:
            candles: DataFrame với dữ liệu nến
            
        Returns:
            Volatility strength (0-1)
        """
        if len(candles) < 15:
            return 0
        
        try:
            # Tính ATR (Average True Range)
            atr_period = 14
            atr_data = []
            
            for i in range(1, len(candles)):
                high = candles.iloc[i]['high']
                low = candles.iloc[i]['low']
                prev_close = candles.iloc[i-1]['close']
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                atr_data.append(tr)
            
            if len(atr_data) < atr_period:
                return 0.5
            
            # ATR trung bình
            atr = np.mean(atr_data[-atr_period:])
            
            # True Range của nến hiện tại
            current_candle = candles.iloc[-1]
            prev_close = candles.iloc[-2]['close']
            
            current_tr = max(
                current_candle['high'] - current_candle['low'],
                abs(current_candle['high'] - prev_close),
                abs(current_candle['low'] - prev_close)
            )
            
            if atr == 0:
                return 0.5
            
            volatility_ratio = current_tr / atr
            
            # Strength tăng theo volatility
            if volatility_ratio >= 2.5:
                return 1.0
            elif volatility_ratio >= 2.0:
                return 0.8
            elif volatility_ratio >= 1.5:
                return 0.6
            elif volatility_ratio >= 1.2:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating volatility strength: {e}")
            return 0
    
    def _calculate_sr_proximity(
        self, 
        current_candle: pd.Series, 
        sr_levels: Optional[list]
    ) -> float:
        """
        Tính bonus strength khi gần S/R
        
        Args:
            current_candle: Nến hiện tại
            sr_levels: Danh sách các mức S/R
            
        Returns:
            S/R proximity bonus (0 hoặc 1)
        """
        if not sr_levels:
            return 0
        
        try:
            current_price = current_candle['close']
            
            for sr_level in sr_levels:
                distance = abs(current_price - sr_level) / current_price
                
                if distance <= self.sr_proximity_threshold:
                    logger.info(f"Pattern gần S/R level {sr_level:.5f}, distance: {distance:.4f}")
                    return 1.0
            
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating S/R proximity: {e}")
            return 0
    
    def get_strength_description(self, strength_result: Dict[str, Any]) -> str:
        """
        Mô tả strength theo cấp độ
        
        Args:
            strength_result: Kết quả từ calculate_enhanced_strength
            
        Returns:
            Mô tả strength
        """
        total_strength = strength_result.get('total_strength', 0)
        
        if total_strength >= 0.9:
            return "💎 EXCELLENT"
        elif total_strength >= 0.8:
            return "🔥 VERY STRONG"
        elif total_strength >= 0.7:
            return "💪 STRONG"
        elif total_strength >= 0.6:
            return "✅ GOOD"
        elif total_strength >= 0.5:
            return "⚖️ MODERATE"
        else:
            return "⚠️ WEAK"
