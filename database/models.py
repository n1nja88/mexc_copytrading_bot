"""
Модели данных для базы данных.

Обоснование:
- Хранение конфигурации аккаунтов
- История реплицированных ордеров
- Статистика копирования
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from config import settings

Base = declarative_base()


class ReplicatedOrder(Base):
    """Модель реплицированного ордера."""
    __tablename__ = "replicated_orders"
    
    id = Column(Integer, primary_key=True)
    master_order_id = Column(String, nullable=False)
    slave_account = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    order_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    slave_order_id = Column(String)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)


def init_database():
    """Инициализирует базу данных."""
    engine = create_engine(settings.database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


