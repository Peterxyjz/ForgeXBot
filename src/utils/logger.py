"""
Logger Configuration
Sets up logging for the application
"""

import logging
import os
import sys
import io
from datetime import datetime
from logging.handlers import RotatingFileHandler
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def _safe_console_stream():
    """
    Trả về stream console có errors='replace' để không bị UnicodeEncodeError
    và dùng đúng encoding hiện tại của console (hoặc utf-8 nếu không có).
    """
    stream = sys.stdout
    enc = getattr(stream, "encoding", None) or "utf-8"
    # line_buffering=True để xuống dòng là flush luôn, giống hành vi console thường
    return io.TextIOWrapper(stream.buffer, encoding=enc, errors="replace", line_buffering=True)


def setup_logger(
    log_dir: str = "logs",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Setup application logger
    """
    # Create logs directory
    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Format for file logs
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d - %H:%M:%S'
    )
    
    # Format for console logs (with colors if available)
    if HAS_COLORLOG:
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
    
    # File handler (ép UTF-8 để lưu emoji chuẩn)
    if log_to_file:
        log_file = os.path.join(
            log_dir,
            f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding="utf-8"        # 👈 quan trọng
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler (dùng stream “an toàn” để không crash vì emoji)
    if log_to_console:
        safe_stream = _safe_console_stream()
        if HAS_COLORLOG:
            console_handler = colorlog.StreamHandler(stream=safe_stream)
        else:
            console_handler = logging.StreamHandler(stream=safe_stream)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Set levels for specific loggers
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger


def get_logger(module: str, level: str = "INFO") -> logging.Logger:
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(module)
    logger.setLevel(getattr(logging, level.upper()))

    if logger.hasHandlers():
        return logger  # tránh bị add handler 2 lần

    log_file = os.path.join("logs", f"{module}.log")

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d - %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding="utf-8"           # 👈 quan trọng
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console riêng cho module nếu cần (cũng an toàn với Unicode)
    console_handler = logging.StreamHandler(stream=_safe_console_stream())
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
