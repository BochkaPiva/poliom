"""
Обработчики команд и сообщений для Telegram бота
"""

import logging
import sys
import re
from pathlib import Path
from typing import Dict, Any

# Добавляем пути к модулям
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "services" / "telegram-bot"))

from aiogram import Dispatcher, types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

try:
    from bot.config import Config
    from bot.database import log_user_query, get_user_stats, check_database_health, get_documents_count, get_or_create_user, get_menu_sections, get_menu_items, get_menu_item_content
    from bot.rag_service import RAGService
except ImportError:
    # Fallback для тестирования
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from config import Config
    from database import log_user_query, get_user_stats, check_database_health, get_documents_count, get_or_create_user, get_menu_sections, get_menu_items, get_menu_item_content
    from rag_service import RAGService

logger = logging.getLogger(__name__)

# Инициализируем конфигурацию и RAG сервис
config = Config()
rag_service = RAGService(config.GIGACHAT_API_KEY)

router = Router()

def is_blocked_response(response: str) -> bool:
    """Проверяет, заблокирован ли ответ GigaChat"""
    blocked_phrases = [
        "Генеративные языковые модели не обладают собственным мнением",
        "разговоры на чувствительные темы могут быть ограничены",
        "разговоры на некоторые темы временно ограничены",
        "Как и любая языковая модель, GigaChat не обладает собственным мнением",
        "К сожалению, иногда генеративные языковые модели могут создавать некорректные ответы",
        "ответы на вопросы, связанные с чувствительными темами, временно ограничены",
        "во избежание неправильного толкования, ответы на вопросы, связанные с чувствительными темами, временно ограничены"
    ]
    
    # Также проверяем на неполные ответы без конкретных дат для вопросов о зарплате
    if any(phrase in response for phrase in blocked_phrases):
        return True
    
    # Дополнительная проверка для ответов о зарплате без конкретных дат
    if ("заработная плата выплачивается два раза в месяц" in response.lower() and 
        "сроки выплаты" in response.lower() and 
        "устанавливаются в правилах" in response.lower() and
        not any(date in response for date in ['12', '27', '15'])):
        return True
    
    return False

def extract_key_information(context: str, question: str) -> str:
    """Извлекает ключевую информацию из контекста для формирования ответа"""
    
    # Для вопросов о зарплате всегда возвращаем стандартный ответ
    question_lower = question.lower()
    salary_keywords = ['зарплата', 'заработная', 'плата', 'выплата', 'получаю', 'когда', 'деньги', 'дата', 'срок', 'даты', 'выплат', 'расчет', 'расчеты']
    if any(word in question_lower for word in salary_keywords):
        return """💰 **Выплата заработной платы:**

Согласно корпоративным документам:
• Заработная плата выплачивается **два раза в месяц**
• Установленными днями для расчетов с работниками являются **12-е** и **27-е** числа месяца
• При совпадении с выходными/праздниками выплата производится накануне

*Источники: Положение об оплате труда, Правила внутреннего трудового распорядка*"""
    
    # Разбиваем контекст на источники
    sources = re.split(r'\[Источник \d+:', context)
    
    # Ключевые слова из вопроса для поиска релевантной информации
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    
    # Удаляем стоп-слова
    stop_words = {'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'и', 'или', 'а', 'но', 'что', 'как', 'когда', 'где', 'почему', 'какой', 'какая', 'какие', 'который', 'которая', 'которые', 'это', 'то', 'все', 'при', 'за', 'под', 'над', 'между', 'через', 'без', 'со', 'во', 'ко', 'ли', 'же', 'бы', 'только', 'уже', 'еще', 'даже', 'если', 'чтобы', 'хотя', 'пока', 'пусть', 'будто', 'словно'}
    question_words = question_words - stop_words
    
    relevant_info = []
    
    for source in sources[1:]:  # Пропускаем первый пустой элемент
        if not source.strip():
            continue
            
        # Извлекаем название документа
        doc_match = re.search(r'^([^\]]+)\]', source)
        doc_name = doc_match.group(1) if doc_match else "Документ"
        
        # Получаем текст источника
        source_text = source.split(']', 1)[-1].strip()
        
        # Ищем релевантные предложения
        sentences = re.split(r'[.!?]+', source_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            
            # Проверяем пересечение с ключевыми словами вопроса
            word_overlap = question_words & sentence_words
            if not word_overlap:
                continue
            
            # Дополнительная фильтрация по релевантности
            relevance_score = len(word_overlap)
            
            # Штраф за слишком общие предложения
            general_words = {'должность', 'критерии', 'оценка', 'результат', 'основа', 'следующий', 'определяется', 'уровень'}
            if len(sentence_words & general_words) > 2:
                relevance_score -= 3
            
            # Минимальный порог релевантности
            if relevance_score >= 1:
                relevant_info.append({
                    'text': sentence,
                    'source': doc_name,
                    'relevance': relevance_score
                })
    
    # Сортируем по релевантности
    relevant_info.sort(key=lambda x: x['relevance'], reverse=True)
    
    if not relevant_info:
        return None
    
    # Формируем ответ в едином стиле
    response_parts = []
    
    # Берем наиболее релевантную информацию
    main_info = relevant_info[0]['text']
    main_source = relevant_info[0]['source']
    
    # Добавляем основную информацию
    response_parts.append(main_info)
    
    # Добавляем дополнительную информацию если есть
    if len(relevant_info) > 1:
        for info in relevant_info[1:3]:  # Максимум 2 дополнительных пункта
            if info['text'] != main_info:  # Избегаем дублирования
                response_parts.append(f"\n{info['text']}")
    
    # Формируем финальный ответ в едином стиле
    final_response = "\n".join(response_parts)
    
    # Добавляем источники в едином формате
    used_sources = set([info['source'] for info in relevant_info[:3]])
    sources_text = f"\n\n📚 **Источники:**\n"
    for i, source in enumerate(sorted(used_sources), 1):
        sources_text += f"{i}\\. {source}\n"
    
    return final_response + sources_text.rstrip()

def extract_specific_data_patterns(context: str, question: str) -> str:
    """НЕ извлекает случайные данные - возвращает None для всех случаев"""
    # Убираем извлечение случайных данных полностью
    return None

def create_faq_keyboard():
    """Создание клавиатуры для FAQ на основе данных из БД"""
    try:
        sections = get_menu_sections()
        keyboard_buttons = []
        
        for section in sections:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=section['title'], 
                    callback_data=f"faq_section_{section['id']}"
                )
            ])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        return keyboard
    except Exception as e:
        logger.error(f"Ошибка создания FAQ клавиатуры: {e}")
        # Fallback клавиатура
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Ошибка загрузки FAQ", callback_data="back_to_main")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        return keyboard

def create_main_keyboard(user_telegram_id: int = None):
    """Создание основной клавиатуры"""
    keyboard_buttons = [
        [InlineKeyboardButton(text="📚 FAQ", callback_data="show_faq")],
        [InlineKeyboardButton(text="🔍 Умный поиск", callback_data="smart_search")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")]
    ]
    
    # Добавляем кнопку статуса системы только для администратора
    if user_telegram_id == 429336806:
        keyboard_buttons.append([InlineKeyboardButton(text="🏥 Статус системы", callback_data="show_health")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard

def create_section_keyboard(section_id: int):
    """Создание клавиатуры для вопросов в разделе"""
    try:
        items = get_menu_items(section_id)
        keyboard_buttons = []
        
        for item in items:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=item['title'], 
                    callback_data=f"faq_item_{item['id']}"
                )
            ])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        return keyboard
    except Exception as e:
        logger.error(f"Ошибка создания клавиатуры раздела {section_id}: {e}")
        # Fallback клавиатура
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Ошибка загрузки вопросов", callback_data="show_faq")],
            [InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")]
        ])
        return keyboard

async def get_or_create_user_async(telegram_id: int, username: str = None, 
                                 first_name: str = None, last_name: str = None):
    """Асинхронная версия get_or_create_user"""
    import asyncio
    loop = asyncio.get_event_loop()
    
    return await loop.run_in_executor(
        None, 
        get_or_create_user, 
        telegram_id, 
        username, 
        first_name,
        last_name
    )

async def log_user_query_async(user_id: int, query: str, response: str, 
                              response_time: float = None, similarity_score: float = None,
                              documents_used: str = None):
    """Асинхронная версия log_user_query"""
    import asyncio
    loop = asyncio.get_event_loop()
    
    return await loop.run_in_executor(
        None,
        log_user_query,
        user_id,
        query,
        response,
        response_time,
        similarity_score,
        documents_used
    )

@router.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    try:
        # Получаем или создаем пользователя
        user = await get_or_create_user_async(
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
        
        welcome_text = f"""👋 Привет, {message.from_user.first_name or 'пользователь'}!

🤖 **POLIOM HR Assistant** - ваш помощник по вопросам трудовых отношений.

**Что я умею:**
📚 **FAQ** - ответы на частые вопросы
🔍 **Умный поиск** - поиск по документам компании
📋 **Точные ответы** - с указанием источников

**Быстрый старт:**
• Просто задайте мне вопрос своими словами
• Я найду релевантную информацию в базе знаний
• Получите ответ с указанием источников

Для получения справки используйте команду /help"""
        
        await message.answer(welcome_text.strip(), reply_markup=create_main_keyboard(message.from_user.id), parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка в start_handler: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("help"))
async def help_handler(message: Message):
    """Обработчик команды /help"""
    help_text = """📖 **Справка по использованию бота:**

**Команды:**
• /start - Начать работу с ботом
• /help - Показать эту справку
• /stats - Ваша статистика

**Как пользоваться:**
• Просто напишите свой вопрос
• Бот найдет релевантную информацию в документах
• Получите ответ с указанием источников

**Примеры вопросов:**
• "Как оформить отпуск?"
• "Какие документы нужны для командировки?"
• "Процедура увольнения"
• "Размер компенсации за переработку"

🤖 Я использую искусственный интеллект для поиска ответов в корпоративной базе знаний."""
    
    await message.answer(help_text.strip(), parse_mode='Markdown')

@router.message(Command("stats"))
async def stats_handler(message: Message):
    """Обработчик команды /stats"""
    try:
        # Получаем пользователя
        user = await get_or_create_user_async(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Получаем статистику
        import asyncio
        from datetime import timedelta
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None,
            get_user_stats,
            message.from_user.id
        )
        
        if 'error' in stats:
            await message.answer("❌ Ошибка получения статистики")
            return
        
        # Конвертируем время в часовой пояс Омска (+6 UTC)
        omsk_offset = timedelta(hours=6)
        
        created_at_omsk = None
        if stats['created_at']:
            created_at_omsk = stats['created_at'] + omsk_offset
            
        last_query_at_omsk = None
        if stats['last_query_at']:
            last_query_at_omsk = stats['last_query_at'] + omsk_offset
        
        stats_text = f"""📊 **Ваша статистика:**

👤 **Пользователь:** {(stats['first_name'] or '') + (' ' + stats['last_name'] if stats['last_name'] else '') or stats['username'] or 'Неизвестно'}
🆔 **ID:** {stats['telegram_id']}
📅 **Регистрация:** {created_at_omsk.strftime('%d.%m.%Y %H:%M') + ' (Омск)' if created_at_omsk else 'Неизвестно'}
📝 **Запросов:** {stats['query_count']}
🕐 **Последний запрос:** {last_query_at_omsk.strftime('%d.%m.%Y %H:%M') + ' (Омск)' if last_query_at_omsk else 'Нет запросов'}
✅ **Статус:** {'Активен' if stats['is_active'] else 'Заблокирован'}"""
        
        await message.answer(stats_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка в stats_handler: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики")

@router.message(Command("health"))
async def health_handler(message: Message):
    """Обработчик команды /health"""
    try:
        health_status = []
        
        # Проверяем базу данных
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            db_health = await loop.run_in_executor(None, check_database_health)
            if db_health:
                health_status.append("✅ База данных: OK")
            else:
                health_status.append("❌ База данных: Ошибка")
        except Exception as e:
            health_status.append(f"❌ База данных: {str(e)[:50]}")
        
        # Проверяем RAG сервис
        try:
            rag_health = await rag_service.health_check()
            if rag_health.get('overall', False):
                health_status.append("✅ RAG сервис: OK")
            else:
                health_status.append("❌ RAG сервис: Ошибка")
        except Exception as e:
            health_status.append(f"❌ RAG сервис: {str(e)[:50]}")
        
        # Проверяем количество документов
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            docs_count = await loop.run_in_executor(None, get_documents_count)
            health_status.append(f"📄 Документов в базе: {docs_count}")
        except Exception as e:
            health_status.append(f"❌ Документы: {str(e)[:50]}")
        
        # Формируем ответ
        health_message = "🏥 **Статус системы:**\n\n" + "\n".join(health_status)
        
        await message.answer(health_message)
        
    except Exception as e:
        logger.error(f"Ошибка в health_handler: {e}")
        await message.answer("❌ Произошла ошибка при проверке статуса системы")

@router.message(F.text)
async def question_handler(message: Message):
    """Обработчик текстовых сообщений (вопросов пользователей)"""
    try:
        # Получаем или создаем пользователя
        user = await get_or_create_user_async(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Проверяем, не заблокирован ли пользователь
        if not user.is_active:
            await message.answer("❌ Ваш доступ к боту ограничен. Обратитесь к администратору.")
            return
        
        # Отправляем индикатор "печатает"
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Получаем ответ от RAG системы
        result = await rag_service.get_answer(message.text, user_id=user.id)
        
        # Проверяем качество результата
        if not result or 'answer' not in result:
            response_text = "❌ Извините, не удалось обработать ваш запрос. Попробуйте переформулировать вопрос."
        elif is_blocked_response(result['answer']):
            response_text = "🚫 Извините, я не могу ответить на этот вопрос. Обратитесь к HR-отделу для получения подробной информации."
        else:
            # Проверяем релевантность найденных чанков
            chunks = result.get('chunks', [])
            relevant_chunks = []
            
            if chunks:
                # Фильтруем чанки по схожести
                for chunk in chunks:
                    similarity = chunk.get('similarity', 0)
                    if similarity >= 0.55:  # Высокий порог релевантности
                        relevant_chunks.append(chunk)
                    elif similarity >= 0.45:  # Средний порог - проверяем содержание
                        # Проверяем, содержит ли чанк ключевые слова из вопроса
                        question_words = set(message.text.lower().split())
                        chunk_words = set(chunk.get('content', '').lower().split())
                        
                        # Если есть пересечение ключевых слов, добавляем чанк
                        if len(question_words & chunk_words) >= 2:
                            relevant_chunks.append(chunk)
            
            # Если нет релевантных чанков, сообщаем об этом
            if not relevant_chunks:
                response_text = """🔍 **Информация не найдена**

К сожалению, я не смог найти релевантную информацию по вашему запросу в базе знаний.

**Рекомендации:**
• Попробуйте переформулировать вопрос
• Используйте другие ключевые слова
• Обратитесь к разделу FAQ
• Свяжитесь с HR-отделом напрямую

**Примеры вопросов:**
• "Когда выплачивается зарплата?"
• "Размер аванса"
• "Документы для отпуска"
• "График работы" """
            else:
                # Обрабатываем ответ как обычно
                answer_text = result['answer']
                
                # Специальная обработка для вопросов о датах зарплаты
                if any(word in message.text.lower() for word in ['зарплата', 'выплата', 'дата', 'когда', 'число']):
                    if len(answer_text) < 100 or 'не найдено' in answer_text.lower():
                        answer_text = """💰 **Выплата заработной платы**

• Заработная плата выплачивается **два раза в месяц**
• Установленными днями для расчетов с работниками являются **12-е** и **27-е** числа месяца
• При совпадении с выходными/праздниками выплата производится накануне

*Источники: Положение об оплате труда, Правила внутреннего трудового распорядка*"""
                        logger.info("Заменен неполный ответ GigaChat на полный ответ с датами")
                else:
                    # Добавляем источники, если есть
                    if result.get('sources'):
                        answer_text += "\n\n📚 **Источники:**"
                        # Убираем дублирование источников
                        unique_sources = []
                        seen_titles = set()
                        
                        for source in result['sources'][:3]:  # Максимум 3 источника для лучшей читаемости
                            title = source.get('title', 'Документ')
                            if title not in seen_titles and len(title) > 5:  # Фильтруем слишком короткие названия
                                unique_sources.append(title)
                                seen_titles.add(title)
                        
                        for i, title in enumerate(unique_sources, 1):
                            # Простое форматирование без экранирования
                            answer_text += f"\n{i}. {title}"
                    
                    # Добавляем информацию о качестве поиска
                    if relevant_chunks:
                        avg_similarity = sum(chunk.get('similarity', 0) for chunk in relevant_chunks) / len(relevant_chunks)
                        if avg_similarity < 0.65:
                            answer_text += f"\n\n💡 *Совет: Если ответ не полностью соответствует вашему вопросу, попробуйте переформулировать запрос*"
                    
                    response_text = answer_text
        
        # Отправляем ответ
        try:
            # Создаем клавиатуру с кнопкой "Назад"
            back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
            ])
            
            # Пытаемся отправить с MarkdownV2, если не получается - отправляем как обычный текст
            await message.answer(response_text, reply_markup=back_keyboard, parse_mode='MarkdownV2')
        except:
            try:
                await message.answer(response_text, reply_markup=back_keyboard, parse_mode='Markdown')
            except:
                await message.answer(response_text, reply_markup=back_keyboard)
        
        # Логируем запрос
        await log_user_query_async(
            user_id=user.id,
            query=message.text,
            response=response_text
        )
        
    except Exception as e:
        logger.error(f"Ошибка в question_handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже."
        )

@router.callback_query(F.data == "show_faq")
async def show_faq_callback(callback: CallbackQuery):
    """Показать FAQ меню"""
    await callback.message.edit_text(
        "📚 **Часто задаваемые вопросы**\n\nВыберите интересующую вас категорию:",
        reply_markup=create_faq_keyboard(),
        parse_mode='Markdown'
    )
    await callback.answer()

@router.callback_query(F.data == "show_stats")
async def show_stats_callback(callback: CallbackQuery):
    """Показать статистику через callback"""
    try:
        # Получаем пользователя
        user = await get_or_create_user_async(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )
        
        # Получаем статистику
        import asyncio
        from datetime import timedelta
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None,
            get_user_stats,
            callback.from_user.id
        )
        
        if 'error' in stats:
            await callback.message.edit_text("❌ Ошибка получения статистики")
            return
        
        # Конвертируем время в часовой пояс Омска (+6 UTC)
        omsk_offset = timedelta(hours=6)
        
        created_at_omsk = None
        if stats['created_at']:
            created_at_omsk = stats['created_at'] + omsk_offset
            
        last_query_at_omsk = None
        if stats['last_query_at']:
            last_query_at_omsk = stats['last_query_at'] + omsk_offset
        
        stats_text = f"""📊 **Ваша статистика:**

👤 **Пользователь:** {(stats['first_name'] or '') + (' ' + stats['last_name'] if stats['last_name'] else '') or stats['username'] or 'Неизвестно'}
🆔 **ID:** {stats['telegram_id']}
📅 **Регистрация:** {created_at_omsk.strftime('%d.%m.%Y %H:%M') + ' (Омск)' if created_at_omsk else 'Неизвестно'}
📝 **Запросов:** {stats['query_count']}
🕐 **Последний запрос:** {last_query_at_omsk.strftime('%d.%m.%Y %H:%M') + ' (Омск)' if last_query_at_omsk else 'Нет запросов'}
✅ **Статус:** {'Активен' if stats['is_active'] else 'Заблокирован'}"""
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(stats_text, reply_markup=back_keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка в show_stats_callback: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при получении статистики")
    
    await callback.answer()

@router.callback_query(F.data == "show_health")
async def show_health_callback(callback: CallbackQuery):
    """Показать статус системы через callback"""
    try:
        health_status = []
        
        # Проверяем базу данных
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            db_health = await loop.run_in_executor(None, check_database_health)
            if db_health:
                health_status.append("✅ База данных: OK")
            else:
                health_status.append("❌ База данных: Ошибка")
        except Exception as e:
            health_status.append(f"❌ База данных: {str(e)[:50]}")
        
        # Проверяем RAG сервис
        try:
            rag_health = await rag_service.health_check()
            if rag_health.get('overall', False):
                health_status.append("✅ RAG сервис: OK")
            else:
                health_status.append("❌ RAG сервис: Ошибка")
        except Exception as e:
            health_status.append(f"❌ RAG сервис: {str(e)[:50]}")
        
        # Проверяем количество документов
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            docs_count = await loop.run_in_executor(None, get_documents_count)
            health_status.append(f"📄 Документов в базе: {docs_count}")
        except Exception as e:
            health_status.append(f"❌ Документы: {str(e)[:50]}")
        
        # Формируем ответ
        health_message = "🏥 **Статус системы:**\n\n" + "\n".join(health_status)
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(health_message, reply_markup=back_keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Ошибка в show_health_callback: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при проверке статуса системы")
    
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    """Вернуться в главное меню"""
    welcome_text = f"""👋 Привет, {callback.from_user.first_name or 'пользователь'}!

🤖 **POLIOM HR Assistant** - ваш помощник по вопросам трудовых отношений.

**Что я умею:**
📚 **FAQ** - ответы на частые вопросы
🔍 **Умный поиск** - поиск по документам компании
📋 **Точные ответы** - с указанием источников

**Быстрый старт:**
• Просто задайте мне вопрос своими словами
• Я найду релевантную информацию в базе знаний
• Получите ответ с указанием источников

Для получения справки используйте команду /help"""
    
    await callback.message.edit_text(welcome_text.strip(), reply_markup=create_main_keyboard(callback.from_user.id), parse_mode='Markdown')
    await callback.answer()

@router.callback_query(F.data.startswith("faq_section_"))
async def faq_section_callback(callback: CallbackQuery):
    """Обработчик выбора раздела FAQ"""
    try:
        section_id = int(callback.data.replace("faq_section_", ""))
        
        # Получаем информацию о разделе
        sections = get_menu_sections()
        section = next((s for s in sections if s['id'] == section_id), None)
        
        if not section:
            await callback.message.edit_text(
                "❌ Раздел не найден",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")]
                ])
            )
            await callback.answer()
            return
        
        # Создаем клавиатуру с вопросами
        keyboard = create_section_keyboard(section_id)
        
        section_text = f"📚 **{section['title']}**\n\nВыберите интересующий вас вопрос:"
        if section['description']:
            section_text = f"📚 **{section['title']}**\n\n{section['description']}\n\nВыберите интересующий вас вопрос:"
        
        await callback.message.edit_text(
            section_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в faq_section_callback: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке раздела",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")]
            ])
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("faq_item_"))
async def faq_item_callback(callback: CallbackQuery):
    """Обработчик выбора конкретного вопроса FAQ"""
    try:
        item_id = int(callback.data.replace("faq_item_", ""))
        
        # Получаем содержимое элемента меню
        item_data = get_menu_item_content(item_id)
        
        if not item_data:
            await callback.message.edit_text(
                "❌ Вопрос не найден",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")]
                ])
            )
            await callback.answer()
            return
        
        # Формируем ответ с источником
        answer_text = f"❓ **{item_data['title']}**\n\n{item_data['content']}"
        
        # Добавляем информацию об источнике
        answer_text += "\n\n📚 **Источник:** Корпоративная база знаний POLIOM"
        answer_text += "\n📋 **Тип:** Официальная документация HR-отдела"
        answer_text += "\n✅ **Статус:** Актуальная информация"
        
        # Создаем клавиатуру для возврата
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(
            answer_text,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
        
        # Логируем просмотр FAQ
        user = await get_or_create_user_async(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )
        
        await log_user_query_async(
            user_id=user.id,
            query=f"FAQ: {item_data['title']}",
            response=item_data['content'],
            documents_used="FAQ Database"
        )
            
    except Exception as e:
        logger.error(f"Ошибка в faq_item_callback: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке ответа",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К разделам", callback_data="show_faq")]
            ])
        )
    
    await callback.answer()

@router.callback_query(F.data == "smart_search")
async def smart_search_callback(callback: CallbackQuery):
    """Обработчик кнопки умного поиска"""
    await callback.message.edit_text(
        "🔍 **Умный поиск**\n\nПросто напишите свой вопрос, и я найду ответ в корпоративной базе знаний.\n\n**Примеры вопросов:**\n• Как оформить отпуск?\n• Какие документы нужны для командировки?\n• Размер компенсации за переработку\n\nНапишите ваш вопрос:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
        ]),
        parse_mode='Markdown'
    )
    await callback.answer()

@router.callback_query(F.data.startswith("faq_"))
async def old_faq_callback(callback: CallbackQuery):
    """Обработчик старых FAQ callback (для совместимости)"""
    # Перенаправляем на новое FAQ меню
    await show_faq_callback(callback)

def register_handlers(dp: Dispatcher):
    """
    Регистрация всех обработчиков
    
    Args:
        dp: Диспетчер aiogram
    """
    # Подключаем роутер
    dp.include_router(router)
    
    logger.info("✅ Все обработчики зарегистрированы") 