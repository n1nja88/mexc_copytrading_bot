"""Настройка логирования."""
from loguru import logger
import sys
from pathlib import Path


def setup_logger(level: str = "INFO", log_file: str = "logs/bot.log"):
    """Настраивает логирование."""
    # Создаем директорию для логов
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Удаляем стандартный handler
    logger.remove()
    
    # Добавляем консольный вывод
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level
    )
    
    # Добавляем файловый вывод
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=level
    )


