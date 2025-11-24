"""
Инициализация Telegram бота.

Обоснование:
- Создание бота и диспетчера
- Регистрация handlers и middleware
- Управление жизненным циклом
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from utils.logger import logger
from .handlers import register_handlers


def create_bot() -> tuple[Bot, Dispatcher]:
    """Создает бота и диспетчер."""
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)
    
    return bot, dp


async def start_bot(bot: Bot, dp: Dispatcher) -> None:
    """Запускает бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def stop_bot(bot: Bot, dp: Dispatcher) -> None:
    """Останавливает бота."""
    await dp.stop_polling()
    await bot.session.close()
