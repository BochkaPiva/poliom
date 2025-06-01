#!/usr/bin/env python3
"""
Главный файл Telegram бота для корпоративного RAG
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к shared модулям (исправлено для Docker)
sys.path.append('/app/shared')

from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties  # Не существует в 3.3.0
from aiogram.enums import ParseMode

from bot.config import config, Messages
from bot.database import init_db
from bot.handlers import register_handlers
from bot.middleware import LoggingMiddleware, AuthMiddleware, RateLimitMiddleware

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    
    # Проверяем конфигурацию
    if not config.validate():
        logger.error("❌ Некорректная конфигурация. Завершение работы.")
        return
    
    # Выводим конфигурацию
    config.print_config()
    
    try:
        # Инициализируем базу данных
        logger.info("🔄 Инициализация базы данных...")
        await init_db()
        logger.info("✅ База данных инициализирована")
        
        # Создаем бота (исправлено для aiogram 3.3.0)
        bot = Bot(
            token=config.BOT_TOKEN,
            parse_mode=ParseMode.HTML  # Используем старый синтаксис
        )
        
        # Создаем диспетчер
        dp = Dispatcher()
        
        # Регистрируем middleware
        dp.message.middleware(LoggingMiddleware())
        dp.message.middleware(AuthMiddleware())
        dp.message.middleware(RateLimitMiddleware(rate_limit=config.RATE_LIMIT_PER_MINUTE))
        
        # Регистрируем обработчики
        register_handlers(dp)
        
        # Проверяем подключение к боту
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username} ({bot_info.full_name})")
        
        # Уведомляем администраторов о запуске
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "🚀 Корпоративный RAG-бот запущен и готов к работе!"
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление администратору {admin_id}: {e}")
        
        # Запускаем polling
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        # Уведомляем администраторов об остановке
        try:
            for admin_id in config.ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        "⏹️ Корпоративный RAG-бот остановлен."
                    )
                except:
                    pass
        except:
            pass
        
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1) 