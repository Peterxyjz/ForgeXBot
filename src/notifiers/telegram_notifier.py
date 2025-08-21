"""
Telegram Notifier - IMPROVED VERSION
Sends concise, actionable trading alerts via Telegram
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
    """Telegram notification handler with improved alert format"""
    
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
    
    def _format_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format pattern alert message - IMPROVED VERSION
        
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
        Format enhanced pattern alert message - CONCISE & ACTIONABLE
        
        Args:
            pattern: Enhanced pattern with context
            
        Returns:
            Formatted message string
        """
        # Get basic pattern info
        pattern_name = pattern.get('pattern', 'Unknown')
        symbol = pattern.get('symbol', 'Unknown')
        timeframe = pattern.get('timeframe', 'Unknown')
        
        # Vietnamese pattern names (shorter)
        pattern_names_vn = {
            'Bullish Engulfing': 'Nến Nhấn Chìm Tăng',
            'Bearish Engulfing': 'Nến Nhấn Chìm Giảm',
            'Hammer': 'Búa',
            'Shooting Star': 'Sao Băng',
            'Doji': 'Doji'
        }
        pattern_name_vn = pattern_names_vn.get(pattern_name, pattern_name)
        
        # Context information
        trend_context = pattern.get('trend_context', {})
        classification = pattern.get('classification', 'neutral')
        sr_context = pattern.get('sr_context', {})
        ema_context = pattern.get('ema_context', {})
        
        # Get concise analyses
        trend_analysis = self._get_concise_trend_analysis(trend_context)
        ema_analysis = self._get_concise_ema_analysis(ema_context)
        
        # Get signal header
        signal_header = self._get_enhanced_signal_header(pattern)
        
        # Format price (2 decimals for gold, appropriate for others)
        price = pattern.get('candle_close', 0)
        if 'XAU' in symbol.upper():
            price_str = f"{price:.2f}"
        else:
            price_str = f"{price:.5f}"
        
        # Build enhanced message with traditional basic info section
        message = f"""🚨 *PRICE ACTION ALERT* 🚨

{signal_header}

📊 **Thông tin cơ bản:**
• Cặp tiền: {symbol.replace('.s', '')}
• Khung thời gian: {self._get_timeframe_vn(timeframe)}
• Mô hình: {pattern_name_vn}
• Giá đóng: {price_str}

{trend_analysis}
{ema_analysis}"""
        
        # Always add S/R context
        sr_info = self._get_concise_sr_info(sr_context)
        message += sr_info
        
        # Add strength explanation
        strength_explanation = self._get_strength_explanation(pattern)
        message += f"\n\n{strength_explanation}"
        
        # Add timestamp
        timestamp = self._format_timestamp(pattern.get('candle_time'))
        message += f"\n\n⏱ Thời gian: {timestamp}"
        
        return message
    
    def _get_concise_trend_analysis(self, trend_context: Dict) -> str:
        """
        Get concise trend analysis with clear conclusion
        
        Args:
            trend_context: Trend information
            
        Returns:
            Concise trend analysis string
        """
        trend_direction = trend_context.get('direction', 'unknown')
        trend_strength = trend_context.get('strength', 0)
        
        # Trend conclusion with strength levels
        if trend_direction == 'uptrend':
            if trend_strength > 0.7:
                return "🎯 **Xu hướng: Mạnh Tăng \n**"
            elif trend_strength > 0.4:
                return "🎯 **Xu hướng: Vừa Tăng \n**"
            else:
                return "🎯 **Xu hướng: Yếu Tăng \n**"
        elif trend_direction == 'downtrend':
            if trend_strength > 0.7:
                return "🎯 **Xu hướng: Mạnh Giảm \n**"
            elif trend_strength > 0.4:
                return "🎯 **Xu hướng: Vừa Giảm \n**"
            else:
                return "🎯 **Xu hướng: Yếu Giảm \n**"
        else:
            return "🎯 **Xu hướng: Đi ngang \n**"

    def _get_concise_ema_analysis(self, ema_context: Dict) -> str:
        """
        Get concise EMA analysis with clear bias
        
        Args:
            ema_context: EMA position information
            
        Returns:
            Concise EMA analysis string
        """
        price_above_ema20 = ema_context.get('price_above_ema20', False)
        price_above_ema50 = ema_context.get('price_above_ema50', False)
        ema20_above_ema50 = ema_context.get('ema20_above_ema50', False)
        
        # EMA bias conclusion
        if price_above_ema20 and price_above_ema50 and ema20_above_ema50:
            return "💎 **EMA: Ưu thế Tăng \n**"
        elif not price_above_ema20 and not price_above_ema50 and not ema20_above_ema50:
            return "💎 **EMA: Ưu thế Giảm \n**"
        else:
            return "💎 **EMA: Trung lập \n**"

    def _get_concise_sr_info(self, sr_context: Dict) -> str:
        """
        Get concise S/R information - ALWAYS SHOW nearest levels (vertical format)
        
        Args:
            sr_context: Support/resistance context
            
        Returns:
            S/R information string (always present)
        """
        lines = ["\n **🎯 Hỗ trợ/Kháng cự:**"]
        
        # Always show nearest resistance if available
        if sr_context.get('nearest_resistance'):
            resistance = sr_context.get('nearest_resistance', {})
            price = resistance.get('price', 0)
            if sr_context.get('near_resistance'):
                lines.append(f"🔴 **Kháng cự**: {price:.2f} (Gần)")
            else:
                lines.append(f"🔴 **Kháng cự**: {price:.2f}")
        
        # Always show nearest support if available
        if sr_context.get('nearest_support'):
            support = sr_context.get('nearest_support', {})
            price = support.get('price', 0)
            if sr_context.get('near_support'):
                lines.append(f"🟢 **Hỗ trợ:** {price:.2f} (Gần)")
            else:
                lines.append(f"🟢 **Hỗ trợ:** {price:.2f}")
        
        # If no S/R levels found, show placeholder
        if len(lines) == 1:  # Only header
            lines.append("🟡 Chưa xác định S/R")
        
        return "\n".join(lines)
    
    def _get_strength_explanation(self, pattern: Dict) -> str:
        """
        Get clear strength explanation
        
        Args:
            pattern: Pattern with strength data
            
        Returns:
            Clear strength explanation
        """
        original_strength = pattern.get('original_strength', 0)
        enhanced_strength = pattern.get('enhanced_strength', 0)
        classification = pattern.get('classification', 'neutral')
        
        # Strength descriptions
        original_desc = self._get_strength_description(original_strength)
        enhanced_desc = self._get_strength_description(enhanced_strength)
        
        # Classification impact note
        if classification == 'trend_continuation':
            context_note = "(Thuận xu hướng +)"
        elif classification == 'trend_reversal':
            context_note = "(Đảo chiều - cần xác nhận)"
        elif classification == 'range_trading':
            context_note = "(Trong vùng giá)"
        else:
            context_note = ""
        
        return f"""💪 **Độ mạnh tín hiệu:**
• **Pattern gốc:** {original_strength:.0%} ({original_desc})
• **Sau phân tích:** {enhanced_strength:.0%} ({enhanced_desc}) {context_note}"""
    
    def _get_strength_description(self, strength: float) -> str:
        """
        Convert strength percentage to descriptive text
        
        Args:
            strength: Strength value 0.0-1.0
            
        Returns:
            Descriptive text
        """
        if strength >= 0.8:
            return "Rất mạnh"
        elif strength >= 0.7:
            return "Mạnh"
        elif strength >= 0.6:
            return "Khá"
        elif strength >= 0.5:
            return "Trung bình"
        elif strength >= 0.4:
            return "Yếu"
        else:
            return "Rất yếu"
    
    def _format_basic_alert_message(self, pattern: Dict[str, Any]) -> str:
        """
        Format basic pattern alert message (fallback for non-enhanced patterns)
        
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
        
        # Vietnamese pattern names
        pattern_names_vn = {
            'Bullish Engulfing': 'Nến Nhấn Chìm Tăng',
            'Bearish Engulfing': 'Nến Nhấn Chìm Giảm',
            'Hammer': 'Búa',
            'Shooting Star': 'Sao Băng',
            'Doji': 'Doji'
        }
        pattern_name_vn = pattern_names_vn.get(pattern_name, pattern_name)
        
        # Signal header
        if pattern_type == 'bullish':
            signal_header = "🟢 *TÍN HIỆU TĂNG* 📈"
        elif pattern_type == 'bearish':
            signal_header = "🔴 *TÍN HIỆU GIẢM* 📉"
        else:
            signal_header = "⚪️ *TÍN HIỆU Sideway* 😪"
        
        # Format price
        if 'XAU' in symbol.upper():
            price_str = f"{candle_close:.2f}"
        else:
            price_str = f"{candle_close:.5f}"
        
        # Strength description
        strength_desc = self._get_strength_description(strength)
        
        # Create message
        message = f"""🚨 *PRICE ACTION ALERT* 🚨

{signal_header}

📊 **{symbol.replace('.s', '')} - {self._get_timeframe_vn(timeframe)}**
🎯 **{pattern_name_vn}** | Giá: {price_str}

💪 **Độ mạnh:** {strength:.0%} ({strength_desc})

⏱ Thời gian: {self._format_timestamp(pattern.get('candle_time'))}"""
        
        return message.strip()
    
    def _get_enhanced_signal_header(self, pattern: Dict[str, Any]) -> str:
        """Get enhanced signal header based on pattern type and classification"""
        pattern_type = pattern.get('type', 'neutral')
        classification = pattern.get('classification', 'neutral')
        
        if pattern_type == 'bullish':
            if classification == 'trend_continuation':
                return "🟢 *TÍN HIỆU TĂNG MẠNH 📈* (Tiếp tục xu hướng)"
            elif classification == 'trend_reversal':
                return "🟡 *TÍN HIỆU ĐẢO CHIỀU TĂNG 📈* (Cần xác nhận)"
            else:
                return "🟢📈 *TÍN HIỆU TĂNG*"
        elif pattern_type == 'bearish':
            if classification == 'trend_continuation':
                return "🔴 *TÍN HIỆU GIẢM MẠNH 📉* (Tiếp tục xu hướng)"
            elif classification == 'trend_reversal':
                return "🟡 *TÍN HIỆU ĐẢO CHIỀU GIẢM 📉* (Cần xác nhận)"
            else:
                return "🔴 *TÍN HIỆU GIẢM 📉*"
        else:
            return "⚪️ *TÍN HIỆU Sideway 😪*"

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
    
    # Keep other methods for compatibility
    async def send_batch_alerts(self, patterns: List[Dict[str, Any]]) -> int:
        """Send multiple alerts"""
        if not patterns:
            return 0
        
        success_count = 0
        for pattern in patterns:
            if await self.send_alert(pattern):
                success_count += 1
                await asyncio.sleep(0.5)
        
        return success_count
    
    def send_batch_alerts_sync(self, patterns: List[Dict[str, Any]]) -> int:
        """Synchronous wrapper for send_batch_alerts"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_batch_alerts(patterns))
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.bot:
            return False
        
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot connected: @{bot_info.username}")
            
            # Send test message
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=(
                    "💠 *ForgeX Bot v0.0.2 đã sẵn sàng!* 🤖\n\n"
                    "✅ *Kết nối:* Thành công\n"
                    "📊 *Trạng thái:* Đang quét thị trường...\n"
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
        """Send bot shutdown notification"""
        if not self.bot:
            return False
        
        try:
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
