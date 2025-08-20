"""
MT5 Connector Module
Handles connection and data retrieval from MetaTrader 5
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any
import pytz

logger = logging.getLogger(__name__)


class MT5Connector:
    """MetaTrader 5 connection and data handler"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MT5 connector
        
        Args:
            config: MT5 configuration dictionary
        """
        self.config = config
        self.connected = False
        self.timezone = pytz.timezone('UTC')
        
    def connect(self) -> bool:
        """
        Establish connection to MT5
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Prepare initialization parameters
            init_params = {
                'login': self.config.get('login'),
                'password': self.config.get('password'),
                'server': self.config.get('server')
            }
            
            # Only add path if it exists and is not empty
            path = self.config.get('path')
            if path and path.strip():
                init_params['path'] = path
            
            # Initialize MT5
            if not mt5.initialize(**init_params):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            # Check terminal info
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                logger.error("Failed to get terminal info")
                return False
                
            logger.info(f"Connected to MT5: {terminal_info.name}")
            logger.info(f"Account: {mt5.account_info().login}")
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 100,
        include_current: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Get historical candle data
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., 'M15', 'H1', 'H4', 'D1')
            count: Number of candles to retrieve
            include_current: If False, exclude the current (incomplete) candle
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
        
        try:
            # Convert timeframe string to MT5 constant
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1
            }
            
            timeframe_mt5 = tf_map.get(timeframe)
            if not timeframe_mt5:
                logger.error(f"Invalid timeframe: {timeframe}")
                return None
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol {symbol} not found")
                return None
            
            # Enable symbol if not visible
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Failed to select symbol {symbol}")
                    return None
            
            # Get rates - fetch one extra if we need to exclude current
            fetch_count = count + 1 if not include_current else count
            rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, fetch_count)
            
            if rates is None or len(rates) == 0:
                logger.error(f"Failed to get rates for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            
            # Rename tick_volume to volume for consistency
            if 'tick_volume' in df.columns:
                df['volume'] = df['tick_volume']
            elif 'real_volume' in df.columns and df['real_volume'].sum() > 0:
                df['volume'] = df['real_volume']
            else:
                # If no volume data, create dummy volume
                df['volume'] = 1000
            
            # Convert time to datetime
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Remove the current (incomplete) candle if requested
            if not include_current and len(df) > count:
                df = df.iloc[:-1]  # Remove last row (current candle)
                logger.debug(f"Excluded current candle, returning {len(df)} closed candles")
            
            # Add additional columns
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            
            # Calculate additional metrics
            df['body'] = abs(df['close'] - df['open'])
            df['range'] = df['high'] - df['low']
            df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
            df['is_bullish'] = df['close'] > df['open']
            
            # Log successful data retrieval
            logger.debug(f"Retrieved {len(df)} candles for {symbol} {timeframe}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting candles for {symbol} {timeframe}: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Symbol info dictionary or None
        """
        if not self.connected:
            return None
        
        try:
            info = mt5.symbol_info(symbol)
            if info:
                return info._asdict()
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def is_market_open(self, symbol: str) -> bool:
        """
        Check if market is open for trading
        
        Args:
            symbol: Trading symbol
            
        Returns:
            bool: True if market is open
        """
        if not self.connected:
            return False
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                # Check if trading is allowed (trade_mode == 4 means SYMBOL_TRADE_MODE_FULL)
                return symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
            return False
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            # Return True to allow scanning even if check fails
            return True
    
    def get_latest_closed_candle(
        self, 
        symbol: str, 
        timeframe: str
    ) -> Optional[pd.Series]:
        """
        Get the latest fully closed candle
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Series with candle data or None
        """
        # Get candles excluding the current one
        df = self.get_candles(symbol, timeframe, count=2, include_current=False)
        
        if df is not None and len(df) > 0:
            # Return the last candle (which is the latest closed one)
            return df.iloc[-1]
        return None
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get account information
        
        Returns:
            Account info dictionary or None
        """
        if not self.connected:
            return None
        
        try:
            info = mt5.account_info()
            if info:
                return info._asdict()
            return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
