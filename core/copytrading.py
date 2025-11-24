"""
Менеджер копи-трейдинга.

Обоснование:
- Координатор всего процесса копирования
- Связывает мониторинг master аккаунта с репликацией на slave
- Управление состоянием (старт/стоп)
"""
import asyncio
from typing import Optional
from exchange.mexc_client import MEXCClient
from exchange.order_monitor import OrderMonitor
from core.order_replicator import OrderReplicator
from config import settings
from utils.logger import logger


class CopyTradingManager:
    """
    Главный менеджер копи-трейдинга.
    
    Обоснование:
    - Единая точка управления всем процессом
    - Координация между мониторингом и репликацией
    - Управление жизненным циклом компонентов
    """
    
    def __init__(self):
        """Инициализация менеджера."""
        # Клиент для master аккаунта
        self.master_client = MEXCClient(
            api_key=settings.master_api_key,
            api_secret=settings.master_api_secret
        )
        
        # Репликатор ордеров
        self.replicator = OrderReplicator()
        
        # Мониторинг ордеров
        self.monitor: Optional[OrderMonitor] = None
        
        self.running = False
    
    async def start(self):
        """Запускает копи-трейдинг."""
        if self.running:
            logger.warning("Copy trading already running")
            return
        
        self.running = True
        
        # Создаем монитор с callbacks
        self.monitor = OrderMonitor(
            client=self.master_client,
            on_order_placed=self._on_order_placed,
            on_order_modified=self._on_order_modified,
            on_order_cancelled=self._on_order_cancelled
        )
        
        # Запускаем мониторинг
        async with self.master_client:
            await self.monitor.start()
        
        logger.info("Copy trading started")
    
    async def stop(self):
        """Останавливает копи-трейдинг."""
        if not self.running:
            return
        
        self.running = False
        
        if self.monitor:
            await self.monitor.stop()
        
        logger.info("Copy trading stopped")
    
    async def _on_order_placed(self, order: dict):
        """Обработчик нового ордера."""
        if not settings.enable_copying:
            return
        
        logger.info(f"New order detected: {order['order_id']}")
        results = await self.replicator.replicate_order(order)
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Order replicated: {success_count}/{len(results)} accounts")
    
    async def _on_order_modified(self, new_order: dict, old_order: dict):
        """Обработчик изменения ордера."""
        if not settings.enable_copying:
            return
        
        logger.info(f"Order modified: {new_order['order_id']}")
        # TODO: Определить изменения и реплицировать
        await self.replicator.replicate_modify(new_order, {})
    
    async def _on_order_cancelled(self, order: dict):
        """Обработчик отмены ордера."""
        if not settings.enable_copying:
            return
        
        logger.info(f"Order cancelled: {order['order_id']}")
        await self.replicator.replicate_cancel(order)
