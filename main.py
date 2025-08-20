"""
Main Bot Engine
Coordinates all components and runs the main scanning loop
"""

import time
import yaml
import signal
import sys
from typing import Dict, Any, List, Set
from datetime import datetime, timedelta
import logging
from src.utils.config_loader import load_config as unified_load_config

from src.connectors.mt5_connector import MT5Connector
from src.patterns.pattern_manager import PatternManager
from src.notifiers.telegram_notifier import TelegramNotifier
from src.utils.alert_cache import AlertCache
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class PriceActionBot:
    """Main bot engine that coordinates all components"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the bot
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.running = False
        
        # Setup logger
        log_config = self.config.get('system', {})
        self.logger = setup_logger(
            log_dir="logs",
            log_level=log_config.get('log_level', 'INFO')
        )
        
        # Initialize components
        self.mt5_connector = None
        self.pattern_manager = None
        self.telegram_notifier = None
        self.alert_cache = None
        
        # Track last candle times for each symbol-timeframe pair
        self.last_candle_times = {}
        
        self._initialize_components()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration via centralized loader (chỉ dùng config_loader)."""
        try:
            config = unified_load_config(config_path)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    def _initialize_components(self):
        """Initialize all bot components"""
        try:
            # Initialize MT5 connector
            self.mt5_connector = MT5Connector(self.config.get('mt5', {}))
            
            # Initialize pattern manager
            self.pattern_manager = PatternManager(self.config)
            
            # Initialize Telegram notifier
            telegram_config = self.config.get('telegram', {})
            telegram_config['timezone'] = self.config.get('system', {}).get('timezone', 'UTC')
            self.telegram_notifier = TelegramNotifier(telegram_config)
            
            # Initialize alert cache
            system_config = self.config.get('system', {})
            self.alert_cache = AlertCache(
                cache_dir="logs",
                cooldown_seconds=system_config.get('alert_cooldown', 3600)
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def connect(self) -> bool:
        """
        Connect to MT5 and test connections
        
        Returns:
            bool: Connection status
        """
        # Connect to MT5
        if not self.mt5_connector.connect():
            logger.error("Failed to connect to MT5")
            return False
        
        # Test Telegram connection
        if self.telegram_notifier:
            if not self.telegram_notifier.test_connection_sync():
                logger.warning("Telegram connection test failed")
        
        return True
    
    def get_candle_close_time(self, current_time: datetime, timeframe: str) -> datetime:
        """
        Calculate when the current candle will close
        
        Args:
            current_time: Current time
            timeframe: Timeframe (M15, H1, H4, D1)
            
        Returns:
            Next candle close time
        """
        if timeframe == 'M15':
            # Round up to next 15 minute mark
            minutes = 15 - (current_time.minute % 15)
            if minutes == 0:
                minutes = 15
            return current_time.replace(second=0, microsecond=0) + timedelta(minutes=minutes)
        
        elif timeframe == 'H1':
            # Round up to next hour
            return current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        elif timeframe == 'H4':
            # Round up to next 4-hour mark (0, 4, 8, 12, 16, 20)
            hour = current_time.hour
            next_h4 = ((hour // 4) + 1) * 4
            if next_h4 >= 24:
                next_h4 = 0
                next_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                next_time = current_time.replace(hour=next_h4, minute=0, second=0, microsecond=0)
            return next_time
        
        elif timeframe == 'D1':
            # Next day at 00:00
            return current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        return current_time + timedelta(minutes=1)
    
    def is_new_candle(self, symbol: str, timeframe: str) -> bool:
        """
        Check if a new candle has closed
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            bool: True if new candle has closed
        """
        key = f"{symbol}_{timeframe}"
        
        # Get the latest closed candle
        latest_candle = self.mt5_connector.get_latest_closed_candle(symbol, timeframe)
        
        if latest_candle is None:
            return False
        
        candle_time = latest_candle['time']
        
        # Check if this is a new candle
        if key not in self.last_candle_times:
            self.last_candle_times[key] = candle_time
            logger.info(f"First scan for {symbol} {timeframe}, candle time: {candle_time}")
            return True  # First time seeing this symbol-timeframe
        
        if candle_time > self.last_candle_times[key]:
            logger.info(f"New candle closed for {symbol} {timeframe}: {candle_time}")
            self.last_candle_times[key] = candle_time
            return True
        
        return False
    
    def scan_for_closed_candles(self) -> List[Dict[str, Any]]:
        """
        Scan only for patterns on newly closed candles
        
        Returns:
            List of detected patterns
        """
        all_patterns = []
        symbols = self.config.get('symbols', [])
        timeframes = self.config.get('timeframes', [])
        
        logger.debug(f"Checking for closed candles on {len(symbols)} symbols across {len(timeframes)} timeframes")
        
        for symbol in symbols:
            try:
                # Check if market is open
                if not self.mt5_connector.is_market_open(symbol):
                    logger.debug(f"Market closed for {symbol}")
                    continue
                
                for timeframe in timeframes:
                    # Check if a new candle has closed
                    if self.is_new_candle(symbol, timeframe):
                        logger.info(f"🕯️ New {timeframe} candle closed for {symbol}, scanning patterns...")
                        
                        # Get candles for pattern detection
                        candles = self.mt5_connector.get_candles(symbol, timeframe, count=100)
                        
                        if candles is not None and not candles.empty:
                            # Scan for patterns
                            patterns = self.pattern_manager.scan_patterns(candles, symbol, timeframe)
                            
                            if patterns:
                                logger.info(f"✅ Found {len(patterns)} patterns on {symbol} {timeframe}")
                                all_patterns.extend(patterns)
                            else:
                                logger.info(f"No patterns found on {symbol} {timeframe}")
                        else:
                            logger.warning(f"No candle data for {symbol} {timeframe}")
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        return all_patterns
    
    def process_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """
        Process detected patterns (filter, cache, notify)
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            Number of alerts sent
        """
        if not patterns:
            return 0
        
        # Filter patterns by strength
        min_strength = self.config.get('patterns', {}).get('min_strength', 0.5)
        filtered_patterns = self.pattern_manager.filter_patterns(
            patterns,
            min_strength=min_strength
        )
        
        logger.info(f"Filtered to {len(filtered_patterns)} patterns with strength >= {min_strength}")
        
        # Process each pattern
        alerts_sent = 0
        
        for pattern in filtered_patterns:
            try:
                # Check cache for duplicates
                if self.alert_cache.is_duplicate(pattern):
                    logger.debug(f"Skipping duplicate alert for {pattern['pattern']} on {pattern['symbol']}")
                    continue
                
                # Send alert
                if self.telegram_notifier:
                    if self.telegram_notifier.send_alert_sync(pattern):
                        alerts_sent += 1
                        # Add to cache
                        self.alert_cache.add_alert(pattern)
                    
            except Exception as e:
                logger.error(f"Error processing pattern: {e}")
                continue
        
        return alerts_sent
    
    def calculate_next_check_time(self) -> int:
        """
        Calculate optimal time to next check based on timeframes
        
        Returns:
            Seconds to wait
        """
        current_time = datetime.now()
        next_check_times = []
        
        # Calculate next close time for each timeframe
        for tf in self.config.get('timeframes', []):
            next_close = self.get_candle_close_time(current_time, tf)
            next_check_times.append(next_close)
        
        if next_check_times:
            # Find the nearest close time
            nearest_close = min(next_check_times)
            wait_seconds = (nearest_close - current_time).total_seconds()
            
            # Add a small buffer (5 seconds) to ensure candle is fully closed
            wait_seconds = max(5, wait_seconds + 5)
            
            # Cap maximum wait time
            wait_seconds = min(wait_seconds, 300)  # Max 5 minutes
            
            return int(wait_seconds)
        
        return 60  # Default to 60 seconds
    
    def run(self):
        """Run the main bot loop"""
        if not self.connect():
            logger.error("Failed to establish connections")
            return
        
        self.running = True
        
        logger.info(f"Bot started - Waiting for candles to close...")
        logger.info(f"Monitoring symbols: {self.config.get('symbols')}")
        logger.info(f"Timeframes: {self.config.get('timeframes')}")
        logger.info(f"Patterns: {self.pattern_manager.get_enabled_patterns()}")
        
        scan_count = 0
        total_patterns = 0
        total_alerts = 0
        
        while self.running:
            try:
                scan_count += 1
                
                # Scan for newly closed candles
                patterns = self.scan_for_closed_candles()
                
                if patterns:
                    # Get statistics
                    stats = self.pattern_manager.get_pattern_statistics(patterns)
                    logger.info(f"🎯 Detected {stats['total']} patterns on closed candles")
                    
                    # Process and send alerts
                    alerts_sent = self.process_patterns(patterns)
                    
                    total_patterns += len(patterns)
                    total_alerts += alerts_sent
                    
                    logger.info(f"📤 Alerts sent: {alerts_sent}")
                
                # Show running statistics every 10 scans
                if scan_count % 10 == 0:
                    logger.info(f"📊 Stats - Scans: {scan_count}, Patterns: {total_patterns}, Alerts: {total_alerts}")
                
                # Calculate optimal wait time until next candle close
                wait_time = self.calculate_next_check_time()
                
                if self.running:
                    current_time = datetime.now().strftime('%H:%M:%S')
                    logger.debug(f"⏱️ [{current_time}] Next check in {wait_time} seconds...")
                    time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                # Wait before retry
                time.sleep(30)
        
        self.stop()
    
    def stop(self):
        """Stop the bot and cleanup"""
        logger.info("Stopping bot...")
        self.running = False
        
        # Disconnect from MT5
        if self.mt5_connector:
            self.mt5_connector.disconnect()
        
        # Save cache
        if self.alert_cache:
            cache_stats = self.alert_cache.get_cache_stats()
            logger.info(f"Cache stats: {cache_stats}")
        
        logger.info("Bot stopped successfully")
    
    def run_test_scan(self):
        """Run a single test scan without loop"""
        if not self.connect():
            logger.error("Failed to establish connections")
            return
        
        logger.info("Running test scan...")
        
        # Clear last candle times to force scan
        self.last_candle_times = {}
        
        # Perform scan
        patterns = self.scan_for_closed_candles()
        
        if patterns:
            # Get statistics
            stats = self.pattern_manager.get_pattern_statistics(patterns)
            logger.info(f"Test scan complete: {stats}")
            
            # Show detected patterns
            for pattern in patterns:
                logger.info(f"Pattern: {pattern['pattern']} on {pattern['symbol']} {pattern['timeframe']}")
                
            # Send one test alert
            if patterns and self.telegram_notifier:
                logger.info("Sending test alert...")
                self.telegram_notifier.send_alert_sync(patterns[0])
        else:
            logger.info("No patterns detected in test scan")
        
        self.stop()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MT5 Price Action Bot')
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run a single test scan'
    )
    
    args = parser.parse_args()
    
    # Create and run bot
    bot = PriceActionBot(args.config)
    
    if args.test:
        bot.run_test_scan()
    else:
        bot.run()


if __name__ == '__main__':
    main()
