"""
Обработчики команд и сообщений для Telegram бота
"""

import logging
from typing import Dict, Any

from aiogram import Dispatcher, types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from .config import config, Messages
from .database import log_user_query, get_user_stats, check_database_health, get_documents_count, get_or_create_user
from .rag_service import RAGService

logger = logging.getLogger(__name__)

# Инициализируем RAG сервис
rag_service = RAGService()

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    try:
        # Получаем или создаем пользователя
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        if not user.is_active:
            await message.answer(
                "❌ Ваш аккаунт заблокирован. Обратитесь к администратору."
            )
            return
        
        welcome_text = f"""
👋 Привет, {message.from_user.first_name or 'пользователь'}!

Я корпоративный RAG-чатбот. Задавайте мне вопросы по документам компании, и я найду для вас ответы.

🔍 Просто напишите свой вопрос, и я найду релевантную информацию в базе знаний.

Для получения справки используйте команду /help
        """
        
        await message.answer(welcome_text.strip())
        
    except Exception as e:
        logging.error(f"Ошибка в start_handler: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    help_text = """
📖 Справка по использованию бота:

• Просто напишите свой вопрос
• Бот найдет релевантную информацию в документах
• Получите ответ с указанием источников

Команды:
/start - Начать работу с ботом
/help - Показать эту справку

❓ Примеры вопросов:
• "Как оформить отпуск?"
• "Какие документы нужны для командировки?"
• "Процедура увольнения"
    """
    
    await message.answer(help_text.strip())

@router.message(F.text)
async def question_handler(message: Message):
    """Обработчик текстовых сообщений (вопросов)"""
    try:
        # Проверяем пользователя
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        if not user.is_active:
            await message.answer(
                "❌ Ваш аккаунт заблокирован. Обратитесь к администратору."
            )
            return
        
        # Отправляем сообщение о том, что обрабатываем запрос
        processing_message = await message.answer("🔍 Ищу информацию...")
        
        # Получаем ответ от RAG системы
        answer = await rag_service.get_answer(message.text)
        
        # Удаляем сообщение о обработке
        await processing_message.delete()
        
        # Отправляем ответ
        await message.answer(answer)
        
        # Логируем запрос
        await log_user_query(
            user_id=user.id,
            query=message.text,
            response=answer
        )
        
    except Exception as e:
        logging.error(f"Ошибка в question_handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже."
        )

async def cmd_stats(message: Message, user: Any = None, **kwargs):
    """
    Обработчик команды /stats
    
    Args:
        message: Сообщение от пользователя
        user: Пользователь из middleware
    """
    try:
        if not user:
            await message.answer("❌ Ошибка получения данных пользователя")
            return
        
        # Получаем статистику пользователя
        stats = get_user_stats(user.id)
        
        stats_message = Messages.format_stats(
            queries_count=stats.get('queries_count', 0),
            last_query=stats.get('last_query_time', None)
        )
        
        await message.answer(stats_message, parse_mode="HTML")
        
        # Логируем команду
        log_user_query(
            user_id=user.id,
            query="/stats",
            response="Статистика пользователя",
            response_time=0.1
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в cmd_stats: {e}")
        await message.answer(Messages.ERROR_GENERAL)

async def cmd_health(message: Message, user: Any = None, **kwargs):
    """
    Обработчик команды /health
    
    Args:
        message: Сообщение от пользователя
        user: Пользователь из middleware
    """
    try:
        # Проверяем здоровье системы
        health_status = []
        
        # Проверяем базу данных
        try:
            db_health = check_database_health()
            if db_health:
                health_status.append("✅ База данных: OK")
            else:
                health_status.append("❌ База данных: Ошибка")
        except Exception as e:
            health_status.append(f"❌ База данных: {str(e)[:50]}")
        
        # Проверяем RAG сервис
        try:
            rag_health = await rag_service.health_check()
            if rag_health:
                health_status.append("✅ RAG сервис: OK")
            else:
                health_status.append("❌ RAG сервис: Ошибка")
        except Exception as e:
            health_status.append(f"❌ RAG сервис: {str(e)[:50]}")
        
        # Проверяем количество документов
        try:
            docs_count = get_documents_count()
            health_status.append(f"📄 Документов в базе: {docs_count}")
        except Exception as e:
            health_status.append(f"❌ Документы: {str(e)[:50]}")
        
        # Формируем ответ
        health_message = "🏥 Статус системы:\n\n" + "\n".join(health_status)
        
        await message.answer(health_message, parse_mode="HTML")
        
        # Логируем команду
        if user:
            log_user_query(
                user_id=user.id,
                query="/health",
                response="Проверка здоровья системы",
                response_time=0.1
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка в cmd_health: {e}")
        await message.answer(Messages.ERROR_GENERAL)

async def handle_admin_command(message: Message, user: Any = None, is_admin: bool = False, **kwargs):
    """
    Обработчик административных команд
    
    Args:
        message: Сообщение от пользователя
        user: Пользователь из middleware
        is_admin: Флаг администратора
    """
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    try:
        command = message.text.lower()
        
        if command == "/admin_stats":
            # Общая статистика системы
            docs_count = get_documents_count()
            
            stats_text = f"""
📊 <b>Административная статистика</b>

📄 Документов в базе: {docs_count}
🤖 Статус RAG: {"✅ Работает" if await rag_service.health_check() else "❌ Ошибка"}
💾 Статус БД: {"✅ Работает" if check_database_health() else "❌ Ошибка"}

⚙️ Конфигурация:
• Макс. длина контекста: {config.MAX_CONTEXT_LENGTH}
• Макс. документов в контексте: {config.MAX_DOCUMENTS_IN_CONTEXT}
• Порог схожести: {config.SIMILARITY_THRESHOLD}
• Лимит запросов/мин: {config.RATE_LIMIT_PER_MINUTE}
            """
            
            await message.answer(stats_text, parse_mode="HTML")
            
        elif command == "/admin_help":
            help_text = """
🔧 <b>Административные команды</b>

/admin_stats - Статистика системы
/admin_help - Эта справка

💡 Для получения детальной информации используйте /health
            """
            await message.answer(help_text, parse_mode="HTML")
            
        else:
            await message.answer("❓ Неизвестная административная команда. Используйте /admin_help")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_admin_command: {e}")
        await message.answer(Messages.ERROR_GENERAL)

def register_handlers(dp: Dispatcher):
    """
    Регистрация всех обработчиков
    
    Args:
        dp: Диспетчер aiogram
    """
    # Основные команды
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_health, Command("health"))
    
    # Административные команды
    dp.message.register(handle_admin_command, Command("admin_stats"))
    dp.message.register(handle_admin_command, Command("admin_help"))
    
    # Обработчик текстовых сообщений (вопросы)
    dp.message.register(handle_question, F.text)
    
    logger.info("✅ Все обработчики зарегистрированы") 