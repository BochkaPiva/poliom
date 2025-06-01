#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл Telegram-бота POLIOM
Интеграция FAQ и умного поиска
"""

import logging
import os
import sys
from pathlib import Path

# Добавляем путь к shared модулям
sys.path.append(str(Path(__file__).parent.parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from .config import Config
from .handlers.faq_handler import register_faq_handlers, FAQHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class POLIOMBot:
    def __init__(self):
        self.config = Config()
        self.application = None
        self.faq_handler = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("📚 FAQ", callback_data="faq_menu")],
            [InlineKeyboardButton("🔍 Умный поиск", callback_data="smart_search")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""👋 **Добро пожаловать, {user.first_name}!**

🤖 **POLIOM HR Assistant** - ваш помощник по вопросам трудовых отношений.

**Что я умею:**
📚 **FAQ** - ответы на частые вопросы по разделам
🔍 **Умный поиск** - поиск по всем документам компании
📋 **Точные ответы** - с указанием источников

**Быстрый старт:**
• Выберите раздел в FAQ для просмотра готовых ответов
• Используйте умный поиск для любых вопросов
• Задавайте вопросы своими словами

Выберите действие ниже 👇"""

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        # Если пользователь в режиме поиска, передаем в FAQ handler
        if context.user_data.get('waiting_for_search'):
            await self.faq_handler.handle_search_query(update, context)
            return
        
        # Иначе предлагаем воспользоваться поиском
        keyboard = [
            [InlineKeyboardButton("🔍 Найти ответ", callback_data="smart_search")],
            [InlineKeyboardButton("📚 Посмотреть FAQ", callback_data="faq_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤔 Я вижу, что у вас есть вопрос!\n\n"
            "Воспользуйтесь умным поиском или посмотрите разделы FAQ.",
            reply_markup=reply_markup
        )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            )
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Регистрируем FAQ handlers и сохраняем ссылку
        self.faq_handler = register_faq_handlers(self.application)
        
        # Обработчик текстовых сообщений (должен быть последним)
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def post_init(self, application: Application):
        """Инициализация после запуска"""
        logger.info("🤖 POLIOM Bot запущен и готов к работе!")
        
        # Проверяем подключение к сервисам
        try:
            # Здесь можно добавить проверки подключения к базе данных,
            # поисковому сервису и т.д.
            logger.info("✅ Все сервисы подключены успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к сервисам: {e}")
    
    def run(self):
        """Запуск бота"""
        # Проверяем конфигурацию
        if not self.config.validate():
            logger.error("❌ Ошибка конфигурации. Проверьте настройки.")
            return
        
        # Создаем приложение
        self.application = Application.builder().token(
            self.config.TELEGRAM_BOT_TOKEN
        ).post_init(self.post_init).build()
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        # Запускаем бота
        logger.info("🚀 Запуск POLIOM Telegram Bot...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

def main():
    """Главная функция"""
    try:
        bot = POLIOMBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 