"""
Модуль торговых стратегий.

Обоснование:
- Разделение логики принятия торговых решений
- Легко добавлять новые стратегии без изменения остального кода
- Тестирование стратегий независимо от других компонентов
- Возможность комбинирования стратегий
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from enum import Enum

from utils.logger import logger


class SignalSide(Enum):
    """Сторона сделки."""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"


class TradingStrategy(ABC):
    """
    Абстрактный базовый класс для торговых стратегий.
    
    Обоснование:
    - Использование паттерна Strategy для гибкости
    - Единый интерфейс для всех стратегий
    - Легко добавлять новые стратегии, наследуя этот класс
    """
    
    @abstractmethod
    async def analyze(self, market_data: Dict) -> Optional[Dict]:
        """
        Анализирует рыночные данные и возвращает торговый сигнал.
        
        Args:
            market_data: Данные рынка (цена, объем, индикаторы и т.д.)
            
        Returns:
            Optional[Dict]: Торговый сигнал или None если нет сигнала
            
        Обоснование:
        - Абстрактный метод, который должна реализовать каждая стратегия
        - Возвращает структурированные данные сигнала
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает название стратегии."""
        pass


class SimpleCopyStrategy(TradingStrategy):
    """
    Простая стратегия копирования: копирует все сделки трейдера.
    
    Обоснование:
    - Базовая стратегия для копи-трейдинга
    - Минимальная обработка: просто передает сигнал дальше
    - Используется по умолчанию
    """
    
    def __init__(self, trader_id: int):
        """
        Инициализация стратегии.
        
        Args:
            trader_id: ID трейдера, которого копируем
        """
        self.trader_id = trader_id
    
    async def analyze(self, market_data: Dict) -> Optional[Dict]:
        """
        Анализирует сигнал от трейдера.
        
        В простой стратегии просто возвращаем сигнал как есть.
        """
        signal = market_data.get("signal")
        
        if not signal:
            return None
        
        # Валидация сигнала
        if not self._validate_signal(signal):
            logger.warning(f"Invalid signal from trader {self.trader_id}: {signal}")
            return None
        
        return {
            "trader_id": self.trader_id,
            "symbol": signal.get("symbol"),
            "side": signal.get("side"),
            "quantity": signal.get("quantity"),
            "price": signal.get("price"),
            "order_type": signal.get("order_type", "MARKET"),
            "timestamp": market_data.get("timestamp")
        }
    
    def _validate_signal(self, signal: Dict) -> bool:
        """
        Валидирует торговый сигнал.
        
        Args:
            signal: Сигнал для валидации
            
        Returns:
            bool: True если сигнал валиден
        """
        required_fields = ["symbol", "side", "quantity"]
        
        for field in required_fields:
            if field not in signal:
                return False
        
        # Проверка стороны сделки
        if signal["side"] not in [s.value for s in SignalSide]:
            return False
        
        # Проверка количества
        if signal["quantity"] <= 0:
            return False
        
        return True
    
    def get_name(self) -> str:
        """Возвращает название стратегии."""
        return f"SimpleCopyStrategy (Trader {self.trader_id})"


class FilteredCopyStrategy(TradingStrategy):
    """
    Стратегия копирования с фильтрацией сделок.
    
    Обоснование:
    - Копирует только сделки, прошедшие фильтры
    - Позволяет настроить критерии отбора (минимальный размер, определенные символы и т.д.)
    - Улучшенная версия простой стратегии
    """
    
    def __init__(
        self,
        trader_id: int,
        min_trade_size: float = 0.0,
        allowed_symbols: Optional[List[str]] = None,
        exclude_symbols: Optional[List[str]] = None
    ):
        """
        Инициализация стратегии с фильтрами.
        
        Args:
            trader_id: ID трейдера
            min_trade_size: Минимальный размер сделки для копирования
            allowed_symbols: Список разрешенных символов (None = все)
            exclude_symbols: Список исключенных символов
        """
        self.trader_id = trader_id
        self.min_trade_size = min_trade_size
        self.allowed_symbols = allowed_symbols or []
        self.exclude_symbols = exclude_symbols or []
    
    async def analyze(self, market_data: Dict) -> Optional[Dict]:
        """
        Анализирует сигнал с применением фильтров.
        
        Обоснование:
        - Применяет фильтры перед возвратом сигнала
        - Логирует причины отклонения сигналов
        """
        signal = market_data.get("signal")
        
        if not signal:
            return None
        
        # Проверка размера сделки
        trade_size = signal.get("quantity", 0) * signal.get("price", 0)
        if trade_size < self.min_trade_size:
            logger.debug(f"Signal rejected: trade size {trade_size} < {self.min_trade_size}")
            return None
        
        # Проверка разрешенных символов
        symbol = signal.get("symbol")
        if self.allowed_symbols and symbol not in self.allowed_symbols:
            logger.debug(f"Signal rejected: symbol {symbol} not in allowed list")
            return None
        
        # Проверка исключенных символов
        if symbol in self.exclude_symbols:
            logger.debug(f"Signal rejected: symbol {symbol} is excluded")
            return None
        
        return {
            "trader_id": self.trader_id,
            "symbol": symbol,
            "side": signal.get("side"),
            "quantity": signal.get("quantity"),
            "price": signal.get("price"),
            "order_type": signal.get("order_type", "MARKET"),
            "timestamp": market_data.get("timestamp")
        }
    
    def get_name(self) -> str:
        """Возвращает название стратегии."""
        return f"FilteredCopyStrategy (Trader {self.trader_id})"


class StrategyFactory:
    """
    Фабрика для создания стратегий.
    
    Обоснование:
    - Централизованное создание стратегий
    - Легко добавлять новые типы стратегий
    - Конфигурирование через параметры
    """
    
    @staticmethod
    def create_strategy(strategy_type: str, **kwargs) -> TradingStrategy:
        """
        Создает стратегию указанного типа.
        
        Args:
            strategy_type: Тип стратегии ("simple", "filtered")
            **kwargs: Параметры для стратегии
            
        Returns:
            TradingStrategy: Экземпляр стратегии
        """
        if strategy_type == "simple":
            return SimpleCopyStrategy(trader_id=kwargs.get("trader_id"))
        elif strategy_type == "filtered":
            return FilteredCopyStrategy(
                trader_id=kwargs.get("trader_id"),
                min_trade_size=kwargs.get("min_trade_size", 0.0),
                allowed_symbols=kwargs.get("allowed_symbols"),
                exclude_symbols=kwargs.get("exclude_symbols")
            )
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")


