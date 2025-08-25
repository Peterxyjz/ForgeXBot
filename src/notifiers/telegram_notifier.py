"""
Telegram Notifier - ENHANCED VERSION với tiếng Việt
Gửi cảnh báo giao dịch súc tích, hữu ích qua Telegram với hỗ trợ biểu đồ
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
import io
import pandas as pd
from .chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram notification handler với enhanced alert format và chart support"""
    
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
        
        # Initialize chart generator
        self.chart_generator = ChartGenerator(config)
        self.send_charts = config.get('send_charts', True)
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
    
    async def send_alert(self, pattern: Dict[str, Any], candles: pd.DataFrame = None) -> bool:
        """
        Gửi cảnh báo pattern qua Telegram với biểu đồ tùy chọn
        
        Args:
            pattern: Kết quả phát hiện pattern (basic hoặc enhanced)
            candles: Dữ liệu nến để tạo biểu đồ
            
        Returns:
            bool: Trạng thái thành công
        """
        if not self.bot:
            logger.error("Telegram bot not configured")
            return False
        
        try:
            message = self._format_alert_message(pattern)
            
            # Gửi biểu đồ nếu được bật và có dữ liệu nến
            if self.send_charts and candles is not None:
                success = await self._send_alert_with_chart(pattern, candles, message)
            else:
                # Gửi tin nhắn text only
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                success = True
            
            if success:
                logger.info(f"Cảnh báo đã gửi: {pattern.get('pattern')} trên {pattern.get('symbol')}")
            
            return success
            
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Lỗi gửi cảnh báo: {e}")
            return False
    
    def send_alert_sync(self, pattern: Dict[str, Any], candles: pd.DataFrame = None) -> bool:
        """
        Wrapper đồng bộ cho send_alert
        
        Args:
            pattern: Kết quả phát hiện pattern
            candles: Dữ liệu nến để tạo biểu đồ
            
        Returns:
            bool: Trạng thái thành công
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_alert(pattern, candles))
    
    async def _send_alert_with_chart(
        self, 
        pattern: Dict[str, Any], 
        candles: pd.DataFrame, 
        message: str
    ) -> bool:
        """
        Gửi cảnh báo kèm biểu đồ
        
        Args:
            pattern: Dữ liệu pattern
            candles: Dữ liệu nến
            message: Tin nhắn cảnh báo
            
        Returns:
            Trạng thái thành công
        """
        try:
            # Tạo biểu đồ
            strength_info = pattern.get('strength_breakdown')
            sr_levels = None
            
            # Extract S/R levels nếu có
            if 'sr_context' in pattern:
                sr_context = pattern['sr_context']
                sr_levels = []
                if sr_context.get('support_level'):
                    sr_levels.append(sr_context['support_level'])
                if sr_context.get('resistance_level'):
                    sr_levels.append(sr_context['resistance_level'])
            
            chart_data = self.chart_generator.generate_pattern_chart(
                candles, pattern, strength_info, sr_levels
            )
            
            if chart_data:
                # Gửi biểu đồ kèm caption
                chart_buffer = io.BytesIO(chart_data)
                chart_buffer.name = f"{pattern.get('symbol', 'chart')}_{pattern.get('pattern', 'pattern')}.png"
                
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=chart_buffer,
                    caption=message,
                    parse_mode='Markdown'
                )
                
                logger.info("Biểu đồ đã gửi thành công")
                return True
            else:
                # Fallback to text message
                logger.warning("Tạo biểu đồ thất bại, gửi text only")
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message + "\n\n⚠️ Không thể tạo biểu đồ",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                return True
                
        except Exception as e:
            logger.error(f"Lỗi gửi biểu đồ: {e}")
            # Fallback to text message
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message + "\n\n⚠️ Biểu đồ không khả dụng",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                return True
            except:
                return False
    
    def _format_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format tin nhắn cảnh báo pattern - PHIÊN BẢN TIẾNG VIỆT
        
        Args:
            pattern: Kết quả phát hiện pattern (basic hoặc enhanced)
            
        Returns:
            Chuỗi tin nhắn đã format
        """
        # Kiểm tra xem có phải enhanced pattern không
        if 'strength_breakdown' in pattern and 'trend_context' in pattern:
            return self._format_enhanced_alert_message(pattern)
        else:
            return self._format_basic_alert_message(pattern)
    
    def _format_enhanced_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format enhanced pattern alert với full context - TIẾNG VIỆT
        
        Args:
            pattern: Enhanced pattern data
            
        Returns:
            Tin nhắn đã format
        """
        # Thông tin cơ bản
        pattern_name = self._get_pattern_name_vietnamese(pattern.get('pattern', 'Unknown Pattern'))
        symbol = pattern.get('symbol', 'Unknown')
        timeframe = pattern.get('timeframe', 'Unknown')
        
        # Enhanced strength info
        strength_breakdown = pattern.get('strength_breakdown', {})
        total_strength = strength_breakdown.get('total_strength', 0)
        
        # Mô tả strength
        strength_desc = self._get_strength_description_vietnamese(total_strength)
        
        # Trend context
        trend_context = pattern.get('trend_context', {})
        trend_direction = trend_context.get('direction', 'Unknown')
        trend_strength = trend_context.get('strength', 0)
        
        # Pattern classification
        classification = pattern.get('classification', 'unknown')
        
        # Thời gian hiện tại
        current_time = datetime.now(self.timezone)
        formatted_time = current_time.strftime('%H:%M - %d/%m/%Y')
        
        # Xây dựng tin nhắn
        message = f"""🎯 *{pattern_name}*\n"""
        
        # Symbol và timeframe
        message += f"💰 *{symbol}* | {timeframe}\n\n"
        
        # Enhanced strength
        message += f"📊 *Độ mạnh:* {strength_desc} ({total_strength:.1%})\n"
        
        # Thêm breakdown strength
        breakdown = strength_breakdown.get('breakdown', {})
        message += f"├ Cơ bản: {breakdown.get('base_pattern', 'N/A')}\n"
        message += f"├ Thân nến: {breakdown.get('body_comparison', 'N/A')}\n"
        message += f"├ Volume: {breakdown.get('volume_spike', 'N/A')}\n"
        message += f"├ Biến động: {breakdown.get('volatility', 'N/A')}\n"
        message += f"└ Bonus S/R: {breakdown.get('sr_proximity', 'N/A')}\n\n"
        
        # Trend context
        trend_emoji = self._get_trend_emoji(trend_direction)
        trend_vn = self._get_trend_name_vietnamese(trend_direction)
        message += f"📈 *Xu hướng:* {trend_emoji} {trend_vn}\n"
        message += f"💪 *Độ mạnh xu hướng:* {trend_strength:.1%}\n\n"
        
        # Pattern classification
        class_emoji = self._get_classification_emoji(classification)
        class_vn = self._get_classification_name_vietnamese(classification)
        message += f"🎲 *Tín hiệu:* {class_emoji} {class_vn}\n\n"
        
        # S/R Context
        sr_context = pattern.get('sr_context', {})
        if sr_context.get('near_support') or sr_context.get('near_resistance'):
            message += "🎯 *Vùng S/R:*\n"
            if sr_context.get('near_support'):
                message += f"├ Gần Support: {sr_context.get('support_level', 'N/A')}\n"
            if sr_context.get('near_resistance'):
                message += f"└ Gần Resistance: {sr_context.get('resistance_level', 'N/A')}\n"
            message += "\n"
        
        
        
        # Gợi ý giao dịch dựa trên pattern type
        pattern_type = pattern.get('type', 'neutral')
        if pattern_type == 'bullish':
            message += "📈 *Gợi ý:* Cân nhắc vị thế LONG\n\n"
        elif pattern_type == 'bearish':
            message += "📉 *Gợi ý:* Cân nhắc vị thế SHORT\n\n"
        else:
            message += "⚖️ *Gợi ý:* Chờ hướng rõ ràng\n\n"

        # Thời gian
        message += f"🕐 *Thời gian:* {formatted_time}\n"
        
        return message
    
    def _format_basic_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format basic pattern alert - TIẾNG VIỆT
        
        Args:
            pattern: Basic pattern data
            
        Returns:
            Tin nhắn đã format
        """
        pattern_name = self._get_pattern_name_vietnamese(pattern.get('pattern', 'Unknown Pattern'))
        symbol = pattern.get('symbol', 'Unknown')
        timeframe = pattern.get('timeframe', 'Unknown')
        strength = pattern.get('strength', 0)
        pattern_type = pattern.get('type', 'neutral')
        
        current_time = datetime.now(self.timezone)
        formatted_time = current_time.strftime('%H:%M - %d/%m/%Y')
        
        # Mô tả strength
        strength_desc = self._get_strength_description_vietnamese(strength)
        
        message = f"""🎯 *{pattern_name}*\n"""
        message += f"💰 *{symbol}* | {timeframe}\n\n"
        message += f"📊 *Độ mạnh:* {strength_desc} ({strength:.1%})\n\n"
        
        
        # Gợi ý giao dịch
        if pattern_type == 'bullish':
            message += "📈 *Gợi ý:* Cân nhắc vị thế LONG\n\n"
        elif pattern_type == 'bearish':
            message += "📉 *Gợi ý:* Cân nhắc vị thế SHORT\n\n"
        else:
            message += "⚖️ *Gợi ý:* Chờ hướng rõ ràng\n\n"

        message += f"🕐 *Thời gian:* {formatted_time}\n"
        return message
    
    def _get_pattern_name_vietnamese(self, pattern_name: str) -> str:
        """Chuyển tên pattern sang tiếng Việt"""
        pattern_map = {
            'bullish_engulfing': 'NẾN NHẤN CHÌM TĂNG',
            'bearish_engulfing': 'NẾN NHẤN CHÌM GIẢM', 
            'hammer': 'NẾN BÚA',
            'shooting_star': 'NẾN SAO BĂNG',
            'doji': 'NẾN DOJI',
            'Bullish Engulfing': 'NẾN NHẤN CHÌM TĂNG',
            'Bearish Engulfing': 'NẾN NHẤN CHÌM GIẢM',
            'Hammer': 'NẾN BÚA',
            'Shooting Star': 'NẾN SAO BĂNG',
            'Doji': 'NẾN DOJI'
        }
        return pattern_map.get(pattern_name, pattern_name.upper())
    
    def _get_strength_description_vietnamese(self, strength: float) -> str:
        """Mô tả strength bằng tiếng Việt với emoji"""
        if strength >= 0.9:
            return "💎 XUẤT SẮC"
        elif strength >= 0.8:
            return "🔥 RẤT MẠNH"
        elif strength >= 0.7:
            return "💪 MẠNH"
        elif strength >= 0.6:
            return "✅ TỐT"
        elif strength >= 0.5:
            return "⚖️ TRUNG BÌNH"
        else:
            return "⚠️ YẾU"
    
    def _get_trend_name_vietnamese(self, trend_direction: str) -> str:
        """Chuyển tên trend sang tiếng Việt"""
        trend_map = {
            'uptrend': 'Tăng',
            'downtrend': 'Giảm', 
            'sideways': 'Ngang',
            'unknown': 'Không rõ'
        }
        return trend_map.get(trend_direction.lower(), 'Không rõ')
    
    def _get_classification_name_vietnamese(self, classification: str) -> str:
        """Chuyển classification sang tiếng Việt"""
        class_map = {
            'trend_continuation': 'Tiếp diễn xu hướng',
            'trend_reversal': 'Đảo chiều xu hướng',
            'range_trading': 'Giao dịch vùng',
            'neutral': 'Trung tính'
        }
        return class_map.get(classification, 'Không rõ')
    
    def _get_trend_emoji(self, trend_direction: str) -> str:
        """Lấy emoji cho hướng trend"""
        if trend_direction.lower() == 'uptrend':
            return "📈"
        elif trend_direction.lower() == 'downtrend':
            return "📉"
        else:
            return "↔️"
    
    def _get_classification_emoji(self, classification: str) -> str:
        """Lấy emoji cho pattern classification"""
        if 'continuation' in classification:
            return "➡️"
        elif 'reversal' in classification:
            return "🔄"
        elif 'range' in classification:
            return "↔️"
        else:
            return "❓"
    
    async def test_connection(self) -> bool:
        """
        Test kết nối Telegram
        
        Returns:
            bool: Trạng thái kết nối
        """
        if not self.bot:
            return False
        
        try:
            await self.bot.get_me()
            logger.info("Test kết nối Telegram thành công")
            return True
        except Exception as e:
            logger.error(f"Test kết nối Telegram thất bại: {e}")
            return False
    
    def test_connection_sync(self) -> bool:
        """Wrapper đồng bộ cho test_connection"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.test_connection())
    
    async def send_startup_notification(self, bot_info: Dict[str, Any] = None) -> bool:
        """
        Gửi thông báo khởi động bot
        
        Args:
            bot_info: Thông tin cấu hình bot
            
        Returns:
            bool: Trạng thái thành công
        """
        if not self.bot:
            return False
        
        try:
            startup_time = datetime.now(self.timezone)
            formatted_time = startup_time.strftime('%H:%M - %d/%m/%Y')
            
            message = f"""🚀 *ForgeX Bot đã khởi động* ✅

⏰ *Thời gian:* {formatted_time}
📊 *Kết nối:* ✅ Thành công"""

            # Thêm thông tin cấu hình nếu có
            if bot_info:
                symbols = bot_info.get('symbols', [])
                timeframes = bot_info.get('timeframes', [])
                patterns = bot_info.get('patterns', [])
                enhanced_mode = bot_info.get('enhanced_mode', False)
                
                message += f"""

🎯 *Cấu hình Bot:*
• Symbols: {', '.join(symbols) if symbols else 'Không có'}
• Timeframes: {', '.join(timeframes) if timeframes else 'Không có'}
• Patterns: {len(patterns)} loại
• Enhanced Mode: {'✅ Bật' if enhanced_mode else '❌ Tắt'}"""
            
            message += "\n\n🔍 *Bot đang giám sát thị trường...*"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("Thông báo khởi động bot đã gửi thành công")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi gửi thông báo khởi động: {e}")
            return False
    
    def send_startup_notification_sync(self, bot_info: Dict[str, Any] = None) -> bool:
        """Wrapper đồng bộ cho send_startup_notification"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_startup_notification(bot_info))
    
    async def send_shutdown_notification(self, stats: Dict[str, Any] = None) -> bool:
        """
        Gửi thông báo tắt bot
        
        Args:
            stats: Thống kê runtime
            
        Returns:
            bool: Trạng thái thành công
        """
        if not self.bot:
            return False
        
        try:
            shutdown_time = datetime.now(self.timezone)
            formatted_time = shutdown_time.strftime('%H:%M - %d/%m/%Y')
            
            message = f"""🔴 *ForgeX Bot đã dừng* 🛑

⏰ *Thời gian dừng:* {formatted_time}
📊 *Trạng thái:* Bot đã ngắt kết nối khỏi thị trường
"""
            
            # Thêm thống kê runtime nếu có
            if stats:
                total_scans = stats.get('total_scans', 0)
                total_patterns = stats.get('total_patterns', 0)
                total_alerts = stats.get('total_alerts', 0)
                runtime = stats.get('runtime', 'N/A')
                
                message += f"""
📈 *Thống kê phiên làm việc:*
• Tổng số lần quét: {total_scans}
• Pattern phát hiện: {total_patterns}
• Cảnh báo đã gửi: {total_alerts}
• Thời gian hoạt động: {runtime}
"""
            
            message += "\n✋ *Cảm ơn bạn đã sử dụng ForgeX Bot!*"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info("Thông báo tắt bot đã gửi thành công")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi gửi thông báo tắt bot: {e}")
            return False
    
    def send_shutdown_notification_sync(self, stats: Dict[str, Any] = None) -> bool:
        """Wrapper đồng bộ cho send_shutdown_notification"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_shutdown_notification(stats))
