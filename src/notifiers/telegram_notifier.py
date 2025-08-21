"""
Telegram Notifier
Sends trading alerts via Telegram Bot API in Vietnamese with Enhanced Context Support
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram notification handler with enhanced pattern support"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Telegram notifier
        
        Args:
            config: Telegram configuration
        """
        self.bot_token = config.get('bot_token')
        self.chat_id = config.get('chat_id')
        self.bot = Bot(token=self.bot_token) if self.bot_token else None
        self.timezone = pytz.timezone(config.get('timezone', 'UTC'))
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
    
    async def send_alert(self, pattern: Dict[str, Any]) -> bool:
        """
        Send pattern alert to Telegram
        
        Args:
            pattern: Pattern detection result (basic or enhanced)
            
        Returns:
            bool: Success status
        """
        if not self.bot:
            logger.error("Telegram bot not configured")
            return False
        
        try:
            message = self._format_alert_message(pattern)
            
            # Send message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            logger.info(f"Alert sent: {pattern.get('pattern')} on {pattern.get('symbol')}")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def send_alert_sync(self, pattern: Dict[str, Any]) -> bool:
        """
        Synchronous wrapper for send_alert
        
        Args:
            pattern: Pattern detection result
            
        Returns:
            bool: Success status
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_alert(pattern))
    
    async def send_batch_alerts(self, patterns: List[Dict[str, Any]]) -> int:
        """
        Send multiple alerts
        
        Args:
            patterns: List of pattern detection results
            
        Returns:
            Number of successful sends
        """
        if not patterns:
            return 0
        
        success_count = 0
        
        for pattern in patterns:
            if await self.send_alert(pattern):
                success_count += 1
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.5)
        
        return success_count
    
    def send_batch_alerts_sync(self, patterns: List[Dict[str, Any]]) -> int:
        """
        Synchronous wrapper for send_batch_alerts
        
        Args:
            patterns: List of pattern detection results
            
        Returns:
            Number of successful sends
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_batch_alerts(patterns))
    
    def _format_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format pattern alert message in Vietnamese
        
        Args:
            pattern: Pattern detection result (basic or enhanced)
            
        Returns:
            Formatted message string
        """
        # Check if this is an enhanced pattern
        if 'trend_context' in pattern and 'ema_context' in pattern:
            return self._format_enhanced_alert_message(pattern)
        
        # Use basic formatting for regular patterns
        return self._format_basic_alert_message(pattern)
    
    def _format_enhanced_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format enhanced pattern alert message with context
        
        Args:
            pattern: Enhanced pattern with context
            
        Returns:
            Formatted message string
        """
        # Get basic pattern info
        pattern_name = pattern.get('pattern', 'Unknown')
        symbol = pattern.get('symbol', 'Unknown')
        timeframe = pattern.get('timeframe', 'Unknown')
        
        # Vietnamese pattern names
        pattern_names_vn = {
            'Bullish Engulfing': 'Nến Nhấn Chìm Tăng',
            'Bearish Engulfing': 'Nến Nhấn Chìm Giảm',
            'Hammer': 'Búa (Hammer)',
            'Shooting Star': 'Sao Băng (Shooting Star)',
            'Doji': 'Doji'
        }
        pattern_name_vn = pattern_names_vn.get(pattern_name, pattern_name)
        
        # Context information
        trend_context = pattern.get('trend_context', {})
        classification = pattern.get('classification', 'neutral')
        sr_context = pattern.get('sr_context', {})
        ema_context = pattern.get('ema_context', {})
        
        # Trend direction in Vietnamese
        trend_vn = {
            'uptrend': 'Xu hướng tăng',
            'downtrend': 'Xu hướng giảm',
            'sideways': 'Đi ngang',
            'unknown': 'Không rõ'
        }.get(trend_context.get('direction', 'unknown'), 'Không rõ')
        
        # Classification in Vietnamese
        classification_vn = {
            'trend_continuation': 'Tiếp tục xu hướng',
            'trend_reversal': 'Đảo chiều xu hướng',
            'range_trading': 'Giao dịch trong vùng',
            'neutral': 'Trung lập'
        }.get(classification, 'Trung lập')
        
        # Get signal header
        signal_header = self._get_enhanced_signal_header(pattern)
        
        # Build enhanced message
        message = f"""🚨 *CẢNH BÁO PRICE ACTION* 🚨

{signal_header}

📊 *Thông tin cơ bản:*
• Cặp tiền: {symbol.replace('.s', '')}
• Khung thời gian: {self._get_timeframe_vn(timeframe)}
• Mô hình: {pattern_name_vn}
• Giá đóng: {pattern.get('candle_close', 0):.5f}

🎯 *Phân tích ngữ cảnh:*
• Xu hướng: {trend_vn} (Độ mạnh: {trend_context.get('strength', 0):.0%})
• Phân loại: {classification_vn}
• Độ tin cậy: {trend_context.get('confidence', 0):.0%}

📈 *Vị trí EMA:*
• Giá vs EMA20: {'Trên' if ema_context.get('price_above_ema20') else 'Dưới'}
• Giá vs EMA50: {'Trên' if ema_context.get('price_above_ema50') else 'Dưới'}
• Khoảng cách EMA20: {ema_context.get('distance_from_ema20', 0):.2%}"""
        
        # Add S/R context if relevant
        if sr_context.get('near_resistance') or sr_context.get('near_support'):
            message += "\n\n🎯 *Hỗ trợ/Kháng cự:*"
            if sr_context.get('near_resistance'):
                resistance = sr_context.get('nearest_resistance', {})
                message += f"\n• Gần kháng cự: {resistance.get('price', 0):.5f}"
            if sr_context.get('near_support'):
                support = sr_context.get('nearest_support', {})
                message += f"\n• Gần hỗ trợ: {support.get('price', 0):.5f}"
        
        # Add strength information
        original_strength = pattern.get('original_strength', pattern.get('strength', 0))
        enhanced_strength = pattern.get('enhanced_strength', pattern.get('strength', 0))
        
        message += f"""\n\n💪 *Độ mạnh tín hiệu:*
• Cơ bản: {original_strength:.0%}
• Nâng cao: {enhanced_strength:.0%}"""
        
        # Add timestamp
        timestamp = self._format_timestamp(pattern.get('candle_time'))
        message += f"\n\n⏱ *Thời gian:* {timestamp}"
        message += "\n\n✅ _Tín hiệu đã được xác nhận với ngữ cảnh thị trường_"
        
        return message
    
    def _format_basic_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format basic pattern alert message (original format)
        
        Args:
            pattern: Basic pattern detection result
            
        Returns:
            Formatted message string
        """
        # Get pattern details
        pattern_name = pattern.get('pattern', 'Unknown')
        pattern_type = pattern.get('type', 'unknown')
        symbol = pattern.get('symbol', 'Unknown')
        timeframe = pattern.get('timeframe', 'Unknown')
        candle_close = pattern.get('candle_close', 0)
        strength = pattern.get('strength', 0)
        candle_time = pattern.get('candle_time')
        
        # Translate pattern names to Vietnamese
        pattern_names_vn = {
            'Bullish Engulfing': 'Nến Nhấn Chìm Tăng',
            'Bearish Engulfing': 'Nến Nhấn Chìm Giảm',
            'Hammer': 'Búa (Hammer)',
            'Shooting Star': 'Sao Băng (Shooting Star)',
            'Doji': 'Doji',
            'Morning Star': 'Sao Mai (Morning Star)',
            'Evening Star': 'Sao Hôm (Evening Star)'
        }
        
        pattern_name_vn = pattern_names_vn.get(pattern_name, pattern_name)
        
        # Determine signal type
        if pattern_type == 'bullish':
            signal_header = "🟢📈 *TÍN HIỆU TĂNG*"
            trend_note = "Khả năng đảo chiều tăng"
        elif pattern_type == 'bearish':
            signal_header = "🔴📉 *TÍN HIỆU GIẢM*"
            trend_note = "Khả năng đảo chiều giảm"
        else:
            signal_header = "⚪️ *TÍN HIỆU TRUNG LẬP*"
            trend_note = "Thị trường đang phân vân"
        
        # Format price based on symbol
        if 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
            # Gold typically has 2 decimal places
            price_str = f"{candle_close:.2f}"
        elif 'JPY' in symbol.upper():
            # JPY pairs typically have 3 decimal places
            price_str = f"{candle_close:.3f}"
        else:
            # Most forex pairs have 5 decimal places
            price_str = f"{candle_close:.5f}"
        
        # Clean symbol name (remove .s suffix if present)
        clean_symbol = symbol.replace('.s', '')
        
        # Format timeframe
        timeframe_vn = self._get_timeframe_vn(timeframe)
        
        # Create message
        message = f"""🚨 *CẢNH BÁO PRICE ACTION* 🚨

{signal_header}

📊 *Cặp tiền:* {clean_symbol}
⏰ *Khung thời gian:* {timeframe_vn}
🎯 *Mô hình:* {pattern_name_vn}
💰 *Giá đóng cửa:* {price_str}
💪 *Độ mạnh tín hiệu:* {strength:.0%}

📝 *Ghi chú:* {trend_note}
⏱ *Thời gian:* {self._format_timestamp(candle_time)}

✅ _Nến đã đóng - Tín hiệu đã xác nhận_"""
        
        # Add special note for Doji subtype
        if pattern_name == 'Doji' and 'subtype' in pattern:
            doji_subtypes_vn = {
                'dragonfly': 'Chuồn Chuồn (Dragonfly)',
                'gravestone': 'Bia Mộ (Gravestone)',
                'long_legged': 'Chân Dài (Long-legged)',
                'standard': 'Chuẩn'
            }
            subtype = pattern['subtype']
            subtype_vn = doji_subtypes_vn.get(subtype, subtype)
            message = message.replace(
                f"*Mô hình:* {pattern_name_vn}",
                f"*Mô hình:* {pattern_name_vn} - {subtype_vn}"
            )
        
        return message.strip()
    
    def _get_enhanced_signal_header(self, pattern: Dict[str, Any]) -> str:
        """Get enhanced signal header based on pattern type and classification"""
        pattern_type = pattern.get('type', 'neutral')
        classification = pattern.get('classification', 'neutral')
        
        if pattern_type == 'bullish':
            if classification == 'trend_continuation':
                return "🟢📈 *TÍN HIỆU TĂNG MẠNH* (Tiếp tục xu hướng)"
            elif classification == 'trend_reversal':
                return "🟡📈 *TÍN HIỆU ĐẢO CHIỀU TĂNG* (Cần xác nhận)"
            else:
                return "🟢📈 *TÍN HIỆU TĂNG*"
        elif pattern_type == 'bearish':
            if classification == 'trend_continuation':
                return "🔴📉 *TÍN HIỆU GIẢM MẠNH* (Tiếp tục xu hướng)"
            elif classification == 'trend_reversal':
                return "🟡📉 *TÍN HIỆU ĐẢO CHIỀU GIẢM* (Cần xác nhận)"
            else:
                return "🔴📉 *TÍN HIỆU GIẢM*"
        else:
            return "⚪️ *TÍN HIỆU TRUNG LẬP*"
    
    def _get_timeframe_vn(self, timeframe: str) -> str:
        """Convert timeframe to Vietnamese"""
        return {
            'M15': '15 phút',
            'H1': '1 giờ',
            'H4': '4 giờ',
            'D1': '1 ngày'
        }.get(timeframe, timeframe)
    
    def _format_timestamp(self, candle_time) -> str:
        """Format timestamp with Vietnam timezone"""
        if isinstance(candle_time, datetime):
            # Convert to Vietnam timezone if not already localized
            if candle_time.tzinfo is None:
                # Assume UTC if no timezone info
                candle_time = pytz.UTC.localize(candle_time)
            
            # Convert to Vietnam timezone
            vietnam_time = candle_time.astimezone(self.timezone)
            return vietnam_time.strftime('%H:%M - %d/%m/%Y')
        else:
            return str(candle_time) if candle_time else 'N/A'
    
    def _get_pattern_emoji(self, pattern_type: str) -> str:
        """Get emoji for pattern type"""
        emojis = {
            'bullish': '🟢',
            'bearish': '🔴',
            'neutral': '⚪'
        }
        return emojis.get(pattern_type, '📊')
    
    async def send_summary(self, stats: Dict[str, Any]) -> bool:
        """
        Send daily/periodic summary in Vietnamese
        
        Args:
            stats: Pattern statistics
            
        Returns:
            bool: Success status
        """
        if not self.bot:
            return False
        
        try:
            message = self._format_summary_message(stats)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
            return False
    
    def _format_summary_message(self, stats: Dict[str, Any]) -> str:
        """Format summary message in Vietnamese"""
        total = stats.get('total', 0)
        by_pattern = stats.get('by_pattern', {})
        by_type = stats.get('by_type', {})
        avg_strength = stats.get('avg_strength', 0)
        
        message = f"""
📈 *BÁO CÁO TỔNG KẾT PHÂN TÍCH*

*Tổng số mô hình phát hiện:* {total}
*Độ mạnh trung bình:* {avg_strength:.1%}

*Phân loại theo xu hướng:*
"""
        
        type_names_vn = {
            'bullish': 'Tăng',
            'bearish': 'Giảm',
            'neutral': 'Trung lập'
        }
        
        for ptype, count in by_type.items():
            emoji = self._get_pattern_emoji(ptype)
            type_vn = type_names_vn.get(ptype, ptype.capitalize())
            message += f"{emoji} {type_vn}: {count}\n"
        
        message += "\n*Phân loại theo mô hình:*\n"
        for pattern, count in by_pattern.items():
            message += f"• {pattern}: {count}\n"
        
        return message.strip()
    
    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection
        
        Returns:
            bool: Connection status
        """
        if not self.bot:
            return False
        
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot connected: @{bot_info.username}")
            
            # Send test message in Vietnamese
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=(
                    "💠 *ForgeX Bot v0.0.2 đã sẵn sàng!* 🤖\n\n"
                    "✅ *Kết nối:* Thành công\n"
                    "📊 *Trạng thái:* Đang bắt đầu quét thị trường...\n"
                    "🚀 *Tính năng mới:* Phân tích ngữ cảnh nâng cao"
                ),
                parse_mode="Markdown"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def test_connection_sync(self) -> bool:
        """Synchronous wrapper for test_connection"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.test_connection())
    
    async def send_shutdown_notification(self, stats: Dict[str, Any] = None) -> bool:
        """
        Send bot shutdown notification in Vietnamese
        
        Args:
            stats: Optional runtime statistics
            
        Returns:
            bool: Success status
        """
        if not self.bot:
            return False
        
        try:
            # Get current Vietnam time for shutdown notification
            shutdown_time = datetime.now(self.timezone)
            formatted_time = shutdown_time.strftime('%H:%M - %d/%m/%Y')
            
            message = f"""🔴 *ForgeX Bot v0.0.2 đã dừng hoạt động* 🛑

⏰ *Thời gian dừng:* {formatted_time}
📊 *Trạng thái:* Bot đã ngắt kết nối khỏi thị trường
"""
            
            # Add runtime statistics if provided
            if stats:
                total_scans = stats.get('total_scans', 0)
                total_patterns = stats.get('total_patterns', 0)
                total_alerts = stats.get('total_alerts', 0)
                runtime = stats.get('runtime', 'N/A')
                
                message += f"""
📈 *Thống kê phiên làm việc:*
• Số lần quét: {total_scans}
• Patterns phát hiện: {total_patterns}
• Alerts đã gửi: {total_alerts}
• Thời gian hoạt động: {runtime}
"""
            
            message += "\n✋ *Cảm ơn bạn đã sử dụng ForgeX Bot!*"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("Shutdown notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending shutdown notification: {e}")
            return False
    
    def send_shutdown_notification_sync(self, stats: Dict[str, Any] = None) -> bool:
        """Synchronous wrapper for send_shutdown_notification"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_shutdown_notification(stats))
