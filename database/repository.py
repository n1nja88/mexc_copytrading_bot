"""Репозиторий для работы с базой данных."""
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from .models import Base, ReplicatedOrder
from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Repository:
    """Репозиторий для работы с БД."""
    
    def __init__(self):
        self.session: Session = SessionLocal()
    
    def save_replicated_order(self, order_data: dict):
        """Сохраняет информацию о реплицированном ордере."""
        order = ReplicatedOrder(**order_data)
        self.session.add(order)
        self.session.commit()
        return order


