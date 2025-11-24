"""
Точка входа приложения.

Обоснование:
- Единая точка запуска
- Инициализация всех компонентов
- Graceful shutdown
"""
import asyncio
import signal
import sys
from pathlib import Path

from utils.logger import setup_logger, logger
from config import settings
from bot.bot import create_bot, start_bot, stop_bot
from database.models import init_database
from core.copytrading import CopyTradingManager


async def main():
    """Главная функция."""
    try:
        # Логирование
        setup_logger(settings.log_level, settings.log_file)
        logger.info("Starting MEXC Copy Trading Bot")
        
        # База данных
        init_database()
        logger.info("Database initialized")
        
        # Telegram бот
        bot, dp = create_bot()
        logger.info("Telegram bot created")
        
        # Менеджер копи-трейдинга
        copy_manager = CopyTradingManager()
        await copy_manager.start()
        logger.info("Copy trading manager started")
        
        # Graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            asyncio.create_task(stop_bot(bot, dp))
            asyncio.create_task(copy_manager.stop())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Запуск
        await start_bot(bot, dp)
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
