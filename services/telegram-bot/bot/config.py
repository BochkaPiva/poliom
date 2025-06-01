#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация Telegram-бота POLIOM
Управление переменными окружения и настройками
"""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """Класс конфигурации для Telegram-бота"""
    
    def __init__(self):
        """Инициализация конфигурации"""
        # Загружаем переменные окружения
        self._load_environment()
        
        # Основные настройки бота
        self.TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
        self.GIGACHAT_API_KEY: Optional[str] = os.getenv('GIGACHAT_API_KEY')
        self.DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
        
        # Настройки поиска
        self.SEARCH_LIMIT: int = int(os.getenv('SEARCH_LIMIT', '5'))
        self.SIMILARITY_THRESHOLD: float = float(os.getenv('SIMILARITY_THRESHOLD', '0.3'))
        
        # Настройки LLM
        self.LLM_TIMEOUT: int = int(os.getenv('LLM_TIMEOUT', '30'))
        self.LLM_MAX_TOKENS: int = int(os.getenv('LLM_MAX_TOKENS', '2000'))
        
        # Настройки бота
        self.BOT_TIMEOUT: int = int(os.getenv('BOT_TIMEOUT', '30'))
        self.MAX_MESSAGE_LENGTH: int = int(os.getenv('MAX_MESSAGE_LENGTH', '4096'))
        
        # Настройки логирования
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE: Optional[str] = os.getenv('LOG_FILE')
        
        # Настройки разработки
        self.DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
        self.WEBHOOK_URL: Optional[str] = os.getenv('WEBHOOK_URL')
        self.WEBHOOK_PORT: int = int(os.getenv('WEBHOOK_PORT', '8443'))
        
        # Настройки FAQ
        self.FAQ_CACHE_TTL: int = int(os.getenv('FAQ_CACHE_TTL', '3600'))  # 1 час
        self.FAQ_SEARCH_LIMIT: int = int(os.getenv('FAQ_SEARCH_LIMIT', '3'))
        
        # Настройки безопасности
        self.ALLOWED_USERS: Optional[str] = os.getenv('ALLOWED_USERS')  # Список ID через запятую
        self.ADMIN_USERS: Optional[str] = os.getenv('ADMIN_USERS')  # Список ID админов
        
        # Настройки производительности
        self.CONCURRENT_REQUESTS: int = int(os.getenv('CONCURRENT_REQUESTS', '10'))
        self.REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '60'))
        
        logger.info("Конфигурация загружена")
    
    def _load_environment(self) -> None:
        """Загрузка переменных окружения из .env файла"""
        # Ищем .env файл в текущей директории и родительских
        current_dir = Path(__file__).parent
        for path in [current_dir, current_dir.parent, current_dir.parent.parent]:
            env_file = path / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"Загружен .env файл: {env_file}")
                break
        else:
            logger.warning("Файл .env не найден")
    
    def validate(self) -> bool:
        """Валидация конфигурации"""
        errors = []
        
        # Проверяем обязательные параметры
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
        
        if not self.GIGACHAT_API_KEY:
            errors.append("GIGACHAT_API_KEY не установлен")
        
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL не установлен")
        
        # Проверяем числовые параметры
        if self.SEARCH_LIMIT <= 0:
            errors.append("SEARCH_LIMIT должен быть больше 0")
        
        if not (0.0 <= self.SIMILARITY_THRESHOLD <= 1.0):
            errors.append("SIMILARITY_THRESHOLD должен быть между 0.0 и 1.0")
        
        if self.LLM_TIMEOUT <= 0:
            errors.append("LLM_TIMEOUT должен быть больше 0")
        
        if self.BOT_TIMEOUT <= 0:
            errors.append("BOT_TIMEOUT должен быть больше 0")
        
        # Логируем ошибки
        if errors:
            for error in errors:
                logger.error(f"Ошибка конфигурации: {error}")
            return False
        
        logger.info("Конфигурация валидна")
        return True
    
    def get_allowed_users(self) -> list[int]:
        """Получить список разрешенных пользователей"""
        if not self.ALLOWED_USERS:
            return []
        
        try:
            return [int(user_id.strip()) for user_id in self.ALLOWED_USERS.split(',')]
        except ValueError:
            logger.error("Неверный формат ALLOWED_USERS")
            return []
    
    def get_admin_users(self) -> list[int]:
        """Получить список администраторов"""
        if not self.ADMIN_USERS:
            return []
        
        try:
            return [int(user_id.strip()) for user_id in self.ADMIN_USERS.split(',')]
        except ValueError:
            logger.error("Неверный формат ADMIN_USERS")
            return []
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Проверить, разрешен ли пользователь"""
        allowed_users = self.get_allowed_users()
        # Если список пуст, разрешаем всех
        return not allowed_users or user_id in allowed_users
    
    def is_user_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        return user_id in self.get_admin_users()
    
    def setup_logging(self) -> None:
        """Настройка логирования"""
        # Устанавливаем уровень логирования
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Настраиваем формат
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Файловый обработчик (если указан)
        if self.LOG_FILE:
            file_handler = logging.FileHandler(self.LOG_FILE, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
        
        logger.info(f"Логирование настроено: уровень {self.LOG_LEVEL}")
    
    def get_info(self) -> dict:
        """Получить информацию о конфигурации"""
        return {
            'bot_configured': bool(self.TELEGRAM_BOT_TOKEN),
            'gigachat_configured': bool(self.GIGACHAT_API_KEY),
            'database_configured': bool(self.DATABASE_URL),
            'debug_mode': self.DEBUG,
            'search_limit': self.SEARCH_LIMIT,
            'similarity_threshold': self.SIMILARITY_THRESHOLD,
            'llm_timeout': self.LLM_TIMEOUT,
            'bot_timeout': self.BOT_TIMEOUT,
            'log_level': self.LOG_LEVEL,
            'webhook_configured': bool(self.WEBHOOK_URL),
            'allowed_users_count': len(self.get_allowed_users()),
            'admin_users_count': len(self.get_admin_users()),
        }
    
    def __str__(self) -> str:
        """Строковое представление конфигурации"""
        info = self.get_info()
        return f"Config(bot={info['bot_configured']}, gigachat={info['gigachat_configured']}, db={info['database_configured']})"

# Глобальный экземпляр конфигурации
config = Config()

# Функции для удобного доступа
def get_config() -> Config:
    """Получить экземпляр конфигурации"""
    return config

def validate_config() -> bool:
    """Валидировать конфигурацию"""
    return config.validate()

def setup_logging() -> None:
    """Настроить логирование"""
    config.setup_logging()

# Автоматическая настройка логирования при импорте
setup_logging()

# Создаем экземпляр конфигурации
config = Config()

# Сообщения бота
class Messages:
    """Сообщения бота"""
    
    # Приветствие
    WELCOME = """
🤖 Добро пожаловать в корпоративный чат-бот!

Я помогу вам найти информацию в корпоративных документах.

📝 Доступные команды:
/start - Начать работу
/help - Помощь
/stats - Статистика использования
/health - Проверка работоспособности

❓ Просто задайте мне вопрос, и я найду ответ в документах!
    """
    
    # Помощь
    HELP = """
🆘 Помощь по использованию бота

📋 Как пользоваться:
1. Задайте вопрос обычным сообщением
2. Бот найдет релевантную информацию в документах
3. Получите ответ с указанием источников

💡 Советы:
• Формулируйте вопросы четко и конкретно
• Используйте ключевые слова из предметной области
• Если ответ неточный, переформулируйте вопрос

⚡ Команды:
/start - Начать работу
/help - Эта справка
/stats - Ваша статистика
/health - Проверка системы

❓ Если у вас есть вопросы, обратитесь к администратору.
    """
    
    # Ошибки
    ERROR_GENERAL = "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
    ERROR_NO_DOCUMENTS = "📄 В базе данных пока нет документов для поиска."
    ERROR_PROCESSING = "⚠️ Ошибка обработки запроса. Попробуйте переформулировать вопрос."
    ERROR_RATE_LIMIT = "⏰ Вы отправляете сообщения слишком часто. Подождите немного."
    ERROR_TOO_LONG = "📝 Ваше сообщение слишком длинное. Максимум {max_length} символов."
    
    # Статусы
    PROCESSING = "🔄 Обрабатываю ваш запрос..."
    SEARCHING = "🔍 Ищу информацию в документах..."
    GENERATING = "✍️ Формирую ответ..."
    
    # Успех
    SUCCESS_HEALTH = "✅ Все системы работают нормально!"
    
    @staticmethod
    def format_stats(queries_count: int, last_query: str = None) -> str:
        """
        Форматирование статистики пользователя
        
        Args:
            queries_count: Количество запросов
            last_query: Время последнего запроса
            
        Returns:
            Отформатированная статистика
        """
        stats = f"📊 Ваша статистика:\n\n"
        stats += f"📝 Всего запросов: {queries_count}\n"
        
        if last_query:
            stats += f"🕐 Последний запрос: {last_query}\n"
        
        if queries_count == 0:
            stats += "\n💡 Задайте первый вопрос, чтобы начать использовать бота!"
        elif queries_count < 10:
            stats += "\n🌱 Вы только начинаете использовать бота. Отлично!"
        elif queries_count < 50:
            stats += "\n📈 Вы активный пользователь бота!"
        else:
            stats += "\n🏆 Вы опытный пользователь бота!"
        
        return stats 