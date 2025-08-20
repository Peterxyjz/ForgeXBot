"""
Alert Cache Manager
Manages alert history to prevent duplicate notifications
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)


class AlertCache:
    """Manages alert cache to prevent duplicate notifications"""
    
    def __init__(self, cache_dir: str = "logs", cooldown_seconds: int = 3600):
        """
        Initialize alert cache
        
        Args:
            cache_dir: Directory for cache file
            cooldown_seconds: Seconds before same alert can trigger again
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "alert_cache.json")
        self.cooldown_seconds = cooldown_seconds
        self.cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                self._clean_expired()
                logger.info(f"Loaded {len(self.cache)} cached alerts")
            else:
                self.cache = {}
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _generate_alert_key(self, pattern: Dict[str, Any]) -> str:
        """
        Generate unique key for alert
        
        Args:
            pattern: Pattern detection result
            
        Returns:
            Unique key string
        """
        # Create key from important pattern attributes
        key_parts = [
            pattern.get('symbol', ''),
            pattern.get('timeframe', ''),
            pattern.get('pattern', ''),
            str(pattern.get('candle_close', ''))
        ]
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_duplicate(self, pattern: Dict[str, Any]) -> bool:
        """
        Check if alert is duplicate within cooldown period
        
        Args:
            pattern: Pattern detection result
            
        Returns:
            bool: True if duplicate
        """
        key = self._generate_alert_key(pattern)
        
        if key in self.cache:
            cached_time = datetime.fromisoformat(self.cache[key]['timestamp'])
            current_time = datetime.now()
            
            if (current_time - cached_time).total_seconds() < self.cooldown_seconds:
                logger.debug(f"Duplicate alert filtered: {key}")
                return True
        
        return False
    
    def add_alert(self, pattern: Dict[str, Any]):
        """
        Add alert to cache
        
        Args:
            pattern: Pattern detection result
        """
        key = self._generate_alert_key(pattern)
        
        self.cache[key] = {
            'timestamp': datetime.now().isoformat(),
            'pattern': pattern.get('pattern'),
            'symbol': pattern.get('symbol'),
            'timeframe': pattern.get('timeframe')
        }
        
        self._save_cache()
        logger.debug(f"Alert cached: {key}")
    
    def _clean_expired(self):
        """Remove expired entries from cache"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, data in self.cache.items():
            cached_time = datetime.fromisoformat(data['timestamp'])
            if (current_time - cached_time).total_seconds() > self.cooldown_seconds * 2:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
            self._save_cache()
    
    def clear_cache(self):
        """Clear all cached alerts"""
        self.cache = {}
        self._save_cache()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Statistics dictionary
        """
        current_time = datetime.now()
        active_count = 0
        
        for data in self.cache.values():
            cached_time = datetime.fromisoformat(data['timestamp'])
            if (current_time - cached_time).total_seconds() < self.cooldown_seconds:
                active_count += 1
        
        return {
            'total_cached': len(self.cache),
            'active_alerts': active_count,
            'cooldown_seconds': self.cooldown_seconds
        }
    
    def update_cooldown(self, seconds: int):
        """
        Update cooldown period
        
        Args:
            seconds: New cooldown period in seconds
        """
        self.cooldown_seconds = seconds
        logger.info(f"Cooldown updated to {seconds} seconds")
