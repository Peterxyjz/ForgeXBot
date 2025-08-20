"""
Pattern Detection Module
"""

from .base_pattern import BasePattern
from .engulfing import BullishEngulfing, BearishEngulfing
from .single_candles import Hammer, ShootingStar, Doji
from .pattern_manager import PatternManager

__all__ = [
    'BasePattern',
    'BullishEngulfing',
    'BearishEngulfing',
    'Hammer',
    'ShootingStar',
    'Doji',
    'PatternManager'
]
