"""
Обработчики команд Telegram бота.

Обоснование:
- Централизованная регистрация handlers
- Разделение на роутеры для организации
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from utils.logger import logger
from .keyboards import get_main_keyboard


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик /start."""
    await message.answer(
        "🤖 <b>MEXC Copy Trading Bot</b>\n\n"
        "Бот для копирования сделок на фьючерсах MEXC.",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Показывает статус копирования."""
    # TODO: Получить статус из CopyTradingManager
    await message.answer("Статус: Активен\nАккаунтов: 30")


@router.message(Command("stop"))
async def cmd_stop(message: Message):
    """Останавливает копирование."""
    # TODO: Остановить копирование
    await message.answer("Копирование остановлено")


@router.message(Command("start_copy"))
async def cmd_start_copy(message: Message):
    """Запускает копирование."""
    # TODO: Запустить копирование
    await message.answer("Копирование запущено")


def register_handlers(dp: "Dispatcher") -> None:
    """Регистрирует все handlers."""
    dp.include_router(router)
