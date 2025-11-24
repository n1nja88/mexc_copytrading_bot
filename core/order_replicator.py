"""
Репликатор ордеров на slave аккаунты.

Обоснование:
- Асинхронная репликация на все аккаунты параллельно
- Поддержка всех типов ордеров
- Применение множителя копирования
- Обработка ошибок для каждого аккаунта независимо
"""
import asyncio
from typing import List, Dict
from exchange.mexc_client import MEXCClient
from config import settings
from utils.logger import logger


class OrderReplicator:
    """
    Реплицирует ордера на все slave аккаунты.
    
    Обоснование:
    - Параллельное выполнение для скорости (критично для копи-трейдинга)
    - Независимая обработка каждого аккаунта (ошибка одного не блокирует остальные)
    - Применение настроек (множитель, фильтры)
    """
    
    def __init__(self):
        """Инициализация репликатора."""
        self.slave_clients: List[MEXCClient] = []
        self._init_clients()
    
    def _init_clients(self):
        """Создает клиенты для всех slave аккаунтов."""
        for account in settings.slave_accounts:
            client = MEXCClient(
                api_key=account["api_key"],
                api_secret=account["api_secret"]
            )
            self.slave_clients.append(client)
    
    async def replicate_order(self, master_order: Dict) -> Dict[str, bool]:
        """
        Реплицирует ордер на все slave аккаунты.
        
        Args:
            master_order: Ордер от master аккаунта
            
        Returns:
            Словарь {account_name: success}
            
        Обоснование:
        - Параллельное выполнение через asyncio.gather
        - Применение copy_multiplier к количеству
        - Сохранение всех параметров ордера (тип, цена, стоп-цена)
        """
        # Применяем множитель
        quantity = master_order["quantity"] * settings.copy_multiplier
        
        # Подготовка параметров для репликации
        order_params = {
            "symbol": master_order["symbol"],
            "side": master_order["side"],
            "order_type": master_order["order_type"],
            "quantity": quantity,
            "price": master_order.get("price"),
            "stop_price": master_order.get("stop_price"),
            "reduce_only": master_order.get("reduce_only", False)
        }
        
        # Параллельная репликация на все аккаунты
        tasks = [
            self._place_order_on_account(client, account, order_params)
            for client, account in zip(self.slave_clients, settings.slave_accounts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Формируем результат
        result_dict = {}
        for account, result in zip(settings.slave_accounts, results):
            account_name = account.get("name", "Unknown")
            if isinstance(result, Exception):
                logger.error(f"Error replicating to {account_name}: {result}")
                result_dict[account_name] = False
            else:
                result_dict[account_name] = result
        
        return result_dict
    
    async def _place_order_on_account(
        self,
        client: MEXCClient,
        account: Dict,
        order_params: Dict
    ) -> bool:
        """Размещает ордер на конкретном аккаунте."""
        try:
            async with client:
                result = await client.place_order(**order_params)
                logger.info(f"Order replicated to {account.get('name')}: {result.get('order_id')}")
                return True
        except Exception as e:
            logger.error(f"Failed to replicate to {account.get('name')}: {e}")
            return False
    
    async def replicate_cancel(self, master_order: Dict) -> Dict[str, bool]:
        """Реплицирует отмену ордера."""
        # TODO: Реализовать отмену на всех аккаунтах
        pass
    
    async def replicate_modify(self, master_order: Dict, changes: Dict) -> Dict[str, bool]:
        """Реплицирует изменение ордера."""
        # TODO: Реализовать изменение на всех аккаунтах
        pass


