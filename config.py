"""
Конфигурация приложения.

Обоснование:
- Централизованное хранение настроек
- Валидация через pydantic
- Поддержка переменных окружения
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import json
from typing import List, Dict

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Telegram
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    
    # Master account (трейдер)
    master_api_key: str = Field(..., env="MASTER_API_KEY")
    master_api_secret: str = Field(..., env="MASTER_API_SECRET")
    
    # Slave accounts (аккаунты для копирования)
    slave_accounts_json: str = Field(..., env="SLAVE_ACCOUNTS")
    
    # Database
    database_url: str = Field(default="sqlite:///./copytrading.db", env="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/bot.log", env="LOG_FILE")
    
    # Copy trading
    copy_multiplier: float = Field(default=1.0, gt=0, env="COPY_MULTIPLIER")
    enable_copying: bool = Field(default=True, env="ENABLE_COPYING")
    
    @property
    def slave_accounts(self) -> List[Dict[str, str]]:
        """Парсит JSON с аккаунтами."""
        return json.loads(self.slave_accounts_json)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
