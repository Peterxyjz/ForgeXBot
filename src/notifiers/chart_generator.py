"""
Chart Generator for Telegram Alerts
Tạo biểu đồ kỹ thuật với highlight pattern để gửi qua Telegram
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Thiết lập matplotlib style
plt.style.use('dark_background')


class ChartGenerator:
    """Generator để tạo chart với highlight pattern"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize chart generator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Chart settings
        self.chart_width = 12
        self.chart_height = 8
        self.candle_count = 50  # Số nến hiển thị
        
        # Colors
        self.colors = {
            'bullish_candle': '#00ff88',
            'bearish_candle': '#ff4444',
            'wick': '#ffffff',
            'background': '#1a1a1a',
            'grid': '#333333',
            'text': '#ffffff',
            'highlight': '#ffff00',
            'volume_up': '#00ff8855',
            'volume_down': '#ff444455'
        }
    
    def generate_pattern_chart(
        self,
        candles: pd.DataFrame,
        pattern_info: Dict[str, Any],
        strength_info: Dict[str, Any] = None,
        sr_levels: List[float] = None
    ) -> bytes:
        """
        Tạo chart với pattern được highlight
        
        Args:
            candles: DataFrame với dữ liệu nến
            pattern_info: Thông tin pattern
            strength_info: Thông tin strength chi tiết
            sr_levels: Danh sách S/R levels
            
        Returns:
            Bytes data của hình ảnh
        """
        try:
            # Chuẩn bị dữ liệu
            chart_data = self._prepare_chart_data(candles)
            
            # Tạo figure với subplots
            fig, (ax_price, ax_volume) = plt.subplots(
                2, 1, 
                figsize=(self.chart_width, self.chart_height),
                gridspec_kw={'height_ratios': [3, 1]},
                facecolor=self.colors['background']
            )
            
            # Vẽ price chart
            self._draw_price_chart(ax_price, chart_data, pattern_info, sr_levels)
            
            # Vẽ volume chart
            self._draw_volume_chart(ax_volume, chart_data, pattern_info)
            
            # Thêm thông tin pattern
            self._add_pattern_info(fig, pattern_info, strength_info)
            
            # Thiết lập layout
            plt.tight_layout()
            plt.subplots_adjust(top=0.9, hspace=0.1)
            
            # Export to bytes
            img_buffer = io.BytesIO()
            plt.savefig(
                img_buffer, 
                format='png',
                dpi=150,
                bbox_inches='tight',
                facecolor=self.colors['background'],
                edgecolor='none'
            )
            plt.close(fig)
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            plt.close('all')  # Cleanup
            return self._generate_error_image()
    
    def _prepare_chart_data(self, candles: pd.DataFrame) -> pd.DataFrame:
        """Chuẩn bị dữ liệu cho chart"""
        # Lấy số nến cần thiết
        if len(candles) > self.candle_count:
            chart_data = candles.tail(self.candle_count).copy()
        else:
            chart_data = candles.copy()
        
        # Reset index để có số thứ tự liên tục
        chart_data = chart_data.reset_index(drop=True)
        
        # Thêm cột màu sắc
        chart_data['color'] = chart_data.apply(
            lambda x: self.colors['bullish_candle'] if x['close'] > x['open'] 
            else self.colors['bearish_candle'], 
            axis=1
        )
        
        return chart_data
    
    def _draw_price_chart(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        pattern_info: Dict[str, Any],
        sr_levels: List[float] = None
    ):
        """Vẽ biểu đồ giá với candlesticks"""
        
        # Vẽ candlesticks
        for i, row in data.iterrows():
            # Thân nến
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['open'], row['close'])
            
            # Màu nến
            color = row['color']
            
            # Vẽ thân nến
            rect = Rectangle(
                (i - 0.3, body_bottom),
                0.6,
                body_height,
                facecolor=color,
                edgecolor=color,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Vẽ bóng nến
            ax.plot([i, i], [row['low'], row['high']], 
                   color=self.colors['wick'], linewidth=1, alpha=0.7)
        
        # Highlight pattern candles
        self._highlight_pattern_candles(ax, data, pattern_info)
        
        # Vẽ S/R levels
        if sr_levels:
            self._draw_sr_levels(ax, sr_levels, len(data))
        
        # Thiết lập axes
        ax.set_xlim(-1, len(data))
        ax.set_ylim(data['low'].min() * 0.999, data['high'].max() * 1.001)
        ax.set_ylabel('Price', color=self.colors['text'])
        ax.grid(True, color=self.colors['grid'], alpha=0.3)
        ax.set_facecolor(self.colors['background'])
        
        # Ẩn x-axis labels (sẽ hiển thị ở volume chart)
        ax.set_xticklabels([])
        
        # Thiết lập màu text
        ax.tick_params(colors=self.colors['text'])
        ax.yaxis.label.set_color(self.colors['text'])
    
    def _draw_volume_chart(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        pattern_info: Dict[str, Any]
    ):
        """Vẽ biểu đồ volume"""
        
        # Volume bars
        colors = [self.colors['volume_up'] if row['close'] > row['open'] 
                 else self.colors['volume_down'] for _, row in data.iterrows()]
        
        bars = ax.bar(
            range(len(data)),
            data['volume'],
            color=colors,
            alpha=0.7,
            width=0.8
        )
        
        # Highlight volume của pattern candles
        pattern_candles = self._get_pattern_candle_indices(data, pattern_info)
        for idx in pattern_candles:
            if 0 <= idx < len(bars):
                bars[idx].set_color(self.colors['highlight'])
                bars[idx].set_alpha(0.9)
        
        # Thiết lập axes
        ax.set_xlim(-1, len(data))
        ax.set_ylabel('Volume', color=self.colors['text'])
        ax.grid(True, color=self.colors['grid'], alpha=0.3)
        ax.set_facecolor(self.colors['background'])
        
        # X-axis labels (time)
        self._set_time_labels(ax, data)
        
        # Thiết lập màu text
        ax.tick_params(colors=self.colors['text'])
        ax.yaxis.label.set_color(self.colors['text'])
    
    def _highlight_pattern_candles(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        pattern_info: Dict[str, Any]
    ):
        """Highlight các nến tạo thành pattern"""
        
        pattern_candles = self._get_pattern_candle_indices(data, pattern_info)
        
        for idx in pattern_candles:
            if 0 <= idx < len(data):
                # Vẽ khung highlight xung quanh nến
                row = data.iloc[idx]
                highlight_rect = Rectangle(
                    (idx - 0.4, row['low'] * 0.999),
                    0.8,
                    (row['high'] - row['low']) * 1.002,
                    facecolor='none',
                    edgecolor=self.colors['highlight'],
                    linewidth=3,
                    alpha=0.8
                )
                ax.add_patch(highlight_rect)
                
                # Thêm arrow pointing to pattern
                if idx == max(pattern_candles):  # Nến cuối của pattern
                    ax.annotate(
                        f"{pattern_info.get('pattern', 'Pattern')}",
                        xy=(idx, row['high']),
                        xytext=(idx, row['high'] + (row['high'] - row['low']) * 0.3),
                        arrowprops=dict(
                            arrowstyle='->',
                            color=self.colors['highlight'],
                            lw=2
                        ),
                        color=self.colors['highlight'],
                        fontsize=10,
                        fontweight='bold',
                        ha='center'
                    )
    
    def _get_pattern_candle_indices(
        self,
        data: pd.DataFrame,
        pattern_info: Dict[str, Any]
    ) -> List[int]:
        """Xác định indices của các nến tạo thành pattern"""
        
        pattern_name = pattern_info.get('pattern', '').lower()
        data_len = len(data)
        
        if 'engulfing' in pattern_name:
            # Engulfing: 2 nến cuối
            return [data_len - 2, data_len - 1]
        elif pattern_name in ['hammer', 'shooting_star', 'doji']:
            # Single candle patterns: nến cuối
            return [data_len - 1]
        else:
            # Default: nến cuối
            return [data_len - 1]
    
    def _draw_sr_levels(
        self,
        ax: plt.Axes,
        sr_levels: List[float],
        data_length: int
    ):
        """Vẽ S/R levels"""
        
        for level in sr_levels:
            ax.axhline(
                y=level,
                color='#888888',
                linestyle='--',
                linewidth=1,
                alpha=0.6
            )
            
            # Label cho S/R level
            ax.text(
                data_length * 0.02,
                level,
                f'S/R: {level:.5f}',
                color='#888888',
                fontsize=8,
                verticalalignment='bottom'
            )
    
    def _set_time_labels(self, ax: plt.Axes, data: pd.DataFrame):
        """Thiết lập labels thời gian cho x-axis"""
        
        # Chọn một số điểm để hiển thị label
        step = max(1, len(data) // 8)
        indices = range(0, len(data), step)
        
        labels = []
        for idx in indices:
            if idx < len(data):
                time_val = data.iloc[idx]['time']
                if isinstance(time_val, str):
                    # Nếu time là string, parse nó
                    try:
                        time_dt = pd.to_datetime(time_val)
                        labels.append(time_dt.strftime('%m/%d %H:%M'))
                    except:
                        labels.append(str(idx))
                else:
                    # Nếu time là datetime
                    labels.append(time_val.strftime('%m/%d %H:%M'))
        
        ax.set_xticks(indices)
        ax.set_xticklabels(labels, rotation=45, ha='right')
    
    def _add_pattern_info(
        self,
        fig: plt.Figure,
        pattern_info: Dict[str, Any],
        strength_info: Dict[str, Any] = None
    ):
        """Thêm thông tin pattern vào chart"""
        
        # Title với pattern name - TIẾNG VIỆT
        pattern_name = self._get_pattern_name_vietnamese(pattern_info.get('pattern', 'Unknown Pattern'))
        symbol = pattern_info.get('symbol', 'Unknown')
        timeframe = pattern_info.get('timeframe', 'Unknown')
        
        title = f"{pattern_name} - {symbol} {timeframe}"
        
        # Thêm strength info nếu có
        if strength_info:
            strength = strength_info.get('total_strength', 0)
            strength_desc = self._get_strength_description(strength)
            title += f" | {strength_desc} ({strength:.1%})"
        
        fig.suptitle(
            title,
            color=self.colors['text'],
            fontsize=14,
            fontweight='bold'
        )
        
        # Thêm timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fig.text(
            0.99, 0.01,
            f"Tạo lúc: {current_time}",
            color=self.colors['text'],
            fontsize=8,
            ha='right'
        )
        
        # Thêm strength breakdown nếu có
        if strength_info and 'breakdown' in strength_info:
            breakdown_text = self._format_strength_breakdown(strength_info['breakdown'])
            fig.text(
                0.01, 0.01,
                breakdown_text,
                color=self.colors['text'],
                fontsize=8,
                ha='left',
                va='bottom'
            )
    
    def _format_strength_breakdown(self, breakdown: Dict[str, str]) -> str:
        """Format strength breakdown cho display - TIẾNG VIỆT"""
        lines = ["Chi tiết độ mạnh:"]
        vietnamese_map = {
            'base_pattern': 'Cơ bản',
            'body_comparison': 'Thân nến', 
            'volume_spike': 'Volume',
            'volatility': 'Biến động',
            'sr_proximity': 'Bonus S/R'
        }
        
        for key, value in breakdown.items():
            readable_key = vietnamese_map.get(key, key.replace('_', ' ').title())
            lines.append(f"• {readable_key}: {value}")
        return '\n'.join(lines)
    
    def _get_strength_description(self, strength: float) -> str:
        """Mô tả strength - TIẾNG VIỆT"""
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
    
    def _generate_error_image(self) -> bytes:
        """Tạo hình ảnh lỗi đơn giản"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6), facecolor=self.colors['background'])
            
            ax.text(
                0.5, 0.5,
                'Lỗi tạo biểu đồ\n\nVui lòng kiểm tra logs để biết chi tiết',
                ha='center',
                va='center',
                color=self.colors['text'],
                fontsize=16,
                transform=ax.transAxes
            )
            
            ax.set_facecolor(self.colors['background'])
            ax.set_xticks([])
            ax.set_yticks([])
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            img_buffer.seek(0)
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating error image: {e}")
            return b""  # Return empty bytes if all else fails
