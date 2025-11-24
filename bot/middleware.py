"""
Middleware для обработки запросов к боту.

Обоснование:
- Централизованная обработка общих задач (логирование, авторизация, rate limiting)
- Не нужно дублировать код в каждом обработчике
- Легко добавлять новую функциональность (например, аналитику)
- Следование принципу DRY (Don't Repeat Yourself)
"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from datetime import datetime

from utils.logger import logger
from database.repository import UserRepository


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования всех обновлений.
    
    Обоснование:
    - Централизованное логирование всех действий пользователей
    - Помогает в отладке и анализе использования бота
    - Не требует изменений в обработчиках
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Логирует информацию о событии перед обработкой."""
        start_time = datetime.now()
        
        # Логирование входящего обновления
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
                username = event.message.from_user.username
                text = event.message.text or event.message.caption or "N/A"
                logger.info(f"Message from {user_id} (@{username}): {text}")
            
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
                username = event.callback_query.from_user.username
                data_callback = event.callback_query.data
                logger.info(f"Callback from {user_id} (@{username}): {data_callback}")
        
        # Вызов следующего middleware или обработчика
        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            # Логирование ошибок
            logger.exception(f"Error in handler: {e}")
            raise
        finally:
            # Логирование времени обработки
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Processing time: {processing_time:.3f}s")


class UserMiddleware(BaseMiddleware):
    """
    Middleware для работы с пользователями.
    
    Обоснование:
    - Автоматическая регистрация пользователей при первом обращении
    - Добавление объекта пользователя в контекст для использования в обработчиках
    - Централизованная логика работы с пользователями
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Добавляет информацию о пользователе в контекст."""
        user_repo = UserRepository()
        
        # Получение информации о пользователе из обновления
        user = None
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user = event.message.from_user
            elif event.callback_query and event.callback_query.from_user:
                user = event.callback_query.from_user
        
        if user:
            # Получение или создание пользователя в БД
            db_user = user_repo.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Добавление в контекст для использования в обработчиках
            data["db_user"] = db_user
        
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов (rate limiting).
    
    Обоснование:
    - Защита от злоупотреблений и спама
    - Предотвращение блокировки бота Telegram
    - Контроль нагрузки на API биржи
    """
    
    def __init__(self):
        """Инициализация с хранением времени последних запросов."""
        self.user_requests: Dict[int, list] = {}
        self.max_requests_per_minute = 20  # Максимум запросов в минуту
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Проверяет частоту запросов от пользователя."""
        user_id = None
        
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id
        
        if user_id:
            now = datetime.now()
            
            # Очистка старых запросов (старше минуты)
            if user_id in self.user_requests:
                self.user_requests[user_id] = [
                    req_time for req_time in self.user_requests[user_id]
                    if (now - req_time).total_seconds() < 60
                ]
            else:
                self.user_requests[user_id] = []
            
            # Проверка лимита
            if len(self.user_requests[user_id]) >= self.max_requests_per_minute:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                
                # Отправка сообщения пользователю (если это Message)
                if isinstance(event, Update) and event.message:
                    await event.message.answer(
                        "⚠️ Слишком много запросов. Пожалуйста, подождите немного."
                    )
                
                return  # Прерываем обработку
            
            # Добавление текущего запроса
            self.user_requests[user_id].append(now)
        
        return await handler(event, data)


def register_middleware(dp: "Dispatcher") -> None:
    """
    Регистрирует все middleware в диспетчере.
    
    Args:
        dp: Экземпляр диспетчера
        
    Обоснование:
    - Порядок регистрации важен: они выполняются в обратном порядке
    - Централизованная регистрация упрощает управление
    """
    # Порядок регистрации: последний зарегистрированный выполняется первым
    # 1. RateLimitMiddleware (проверка лимитов)
    # 2. UserMiddleware (работа с пользователями)
    # 3. LoggingMiddleware (логирование)
    
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    logger.debug("All middleware registered")


