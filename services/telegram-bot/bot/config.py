"""
Конфигурация для Telegram бота
"""

import os
from typing import List

class BotConfig:
    """Конфигурация бота"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/poliom_db")
    
    # GigaChat API
    GIGACHAT_API_KEY: str = os.getenv("GIGACHAT_API_KEY", "")
    GIGACHAT_BASE_URL: str = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
    
    # Администраторы (ID пользователей Telegram)
    ADMIN_IDS: List[int] = [
        int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") 
        if admin_id.strip().isdigit()
    ]
    
    # Настройки RAG
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
    MAX_DOCUMENTS_IN_CONTEXT: int = int(os.getenv("MAX_DOCUMENTS_IN_CONTEXT", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    # Настройки бота
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "4096"))
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    
    # Пути к файлам
    UPLOADS_DIR: str = os.getenv("UPLOADS_DIR", "/app/uploads")
    
    # Настройки эмбеддингов
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    EMBEDDINGS_CACHE_SIZE: int = int(os.getenv("EMBEDDINGS_CACHE_SIZE", "1000"))
    
    # Настройки Redis (если используется)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Настройки производительности
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> bool:
        """
        Проверка корректности конфигурации
        
        Returns:
            True если конфигурация корректна
        """
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL не установлен")
        
        if not cls.GIGACHAT_API_KEY:
            errors.append("GIGACHAT_API_KEY не установлен")
        
        if cls.MAX_CONTEXT_LENGTH <= 0:
            errors.append("MAX_CONTEXT_LENGTH должен быть больше 0")
        
        if cls.SIMILARITY_THRESHOLD < 0 or cls.SIMILARITY_THRESHOLD > 1:
            errors.append("SIMILARITY_THRESHOLD должен быть между 0 и 1")
        
        if errors:
            print("❌ Ошибки конфигурации:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Вывод текущей конфигурации (без секретных данных)"""
        print("🔧 Конфигурация бота:")
        print(f"  - База данных: {cls.DATABASE_URL.split('@')[-1] if '@' in cls.DATABASE_URL else 'не настроена'}")
        print(f"  - Администраторы: {len(cls.ADMIN_IDS)} пользователей")
        print(f"  - Максимальная длина контекста: {cls.MAX_CONTEXT_LENGTH}")
        print(f"  - Максимум документов в контексте: {cls.MAX_DOCUMENTS_IN_CONTEXT}")
        print(f"  - Порог схожести: {cls.SIMILARITY_THRESHOLD}")
        print(f"  - Лимит запросов в минуту: {cls.RATE_LIMIT_PER_MINUTE}")
        print(f"  - Уровень логирования: {cls.LOG_LEVEL}")
        print(f"  - Модель эмбеддингов: {cls.EMBEDDINGS_MODEL}")
        print(f"  - Максимум воркеров: {cls.MAX_WORKERS}")

# Создаем экземпляр конфигурации
config = BotConfig()

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