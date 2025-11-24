"""
Мониторинг ордеров трейдера (master account).

Обоснование:
- Отслеживание всех действий трейдера в реальном времени
- Обнаружение новых ордеров, изменений, отмен
- Передача событий в репликатор
"""
import asyncio
from typing import Callable, Optional
from .mexc_client import MEXCClient
from utils.logger import logger


class OrderMonitor:
    """
    Мониторинг ордеров master аккаунта.
    
    Обоснование:
    - Периодический опрос открытых ордеров
    - Сравнение с предыдущим состоянием для обнаружения изменений
    - Callback для уведомления о событиях
    """
    
    def __init__(
        self,
        client: MEXCClient,
        on_order_placed: Callable,
        on_order_modified: Callable,
        on_order_cancelled: Callable
    ):
        """
        Инициализация монитора.
        
        Args:
            client: Клиент для master аккаунта
            on_order_placed: Callback при новом ордере
            on_order_modified: Callback при изменении ордера
            on_order_cancelled: Callback при отмене ордера
        """
        self.client = client
        self.on_order_placed = on_order_placed
        self.on_order_modified = on_order_modified
        self.on_order_cancelled = on_order_cancelled
        
        self.running = False
        self.last_orders: dict = {}  # order_id -> order_data
        self.poll_interval = 0.5  # секунды между опросами
    
    async def start(self):
        """Запускает мониторинг."""
        self.running = True
        logger.info("Order monitor started")
        await self._monitor_loop()
    
    async def stop(self):
        """Останавливает мониторинг."""
        self.running = False
        logger.info("Order monitor stopped")
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга."""
        while self.running:
            try:
                # Получаем текущие ордера
                current_orders = await self.client.get_open_orders()
                current_orders_dict = {o["order_id"]: o for o in current_orders}
                
                # Обнаружение новых ордеров
                new_orders = set(current_orders_dict.keys()) - set(self.last_orders.keys())
                for order_id in new_orders:
                    await self.on_order_placed(current_orders_dict[order_id])
                
                # Обнаружение изменений ордеров
                for order_id, order in current_orders_dict.items():
                    if order_id in self.last_orders:
                        if order != self.last_orders[order_id]:
                            await self.on_order_modified(order, self.last_orders[order_id])
                
                # Обнаружение отмененных ордеров
                cancelled_orders = set(self.last_orders.keys()) - set(current_orders_dict.keys())
                for order_id in cancelled_orders:
                    await self.on_order_cancelled(self.last_orders[order_id])
                
                self.last_orders = current_orders_dict
                
            except Exception as e:
                logger.exception(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(self.poll_interval)


