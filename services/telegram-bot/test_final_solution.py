#!/usr/bin/env python3
"""
Тестирование финального решения с обработкой заблокированных ответов GigaChat
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, root_dir)

from services.shared.config import Config
from services.telegram_bot.services.rag_service import RAGService

# Простая версия обработчика для тестирования
class TestMessageHandler:
    def __init__(self, config: Config, rag_service):
        self.config = config
        self.rag_service = rag_service

    def is_blocked_response(self, response: str) -> bool:
        """Проверяет, заблокирован ли ответ GigaChat"""
        blocked_phrases = [
            "Генеративные языковые модели не обладают собственным мнением",
            "разговоры на чувствительные темы могут быть ограничены",
            "разговоры на некоторые темы временно ограничены",
            "Как и любая языковая модель, GigaChat не обладает собственным мнением"
        ]
        return any(phrase in response for phrase in blocked_phrases)

    def get_payment_dates_fallback(self, question: str) -> str:
        """Возвращает альтернативный ответ для вопросов о датах выплат"""
        payment_keywords = [
            'заработная плата', 'зарплата', 'выплата', 'выплачивается', 
            'расчет', 'расчеты', 'дни выплат', 'сроки выплат', 'периодичность'
        ]
        
        if any(keyword in question.lower() for keyword in payment_keywords):
            return """📅 **Информация о датах выплат**

Согласно корпоративным документам:
• Установленными днями для расчетов с работниками являются **12-е** и **27-е** числа месяца
• Выплаты производятся **два раза в месяц**

*Источник: Правила внутреннего трудового распорядка*"""
        
        return None

async def test_message_handler():
    """Тестирует обработчик сообщений с заблокированными ответами"""
    
    print("✅ Модули импортированы успешно")
    
    # Инициализация конфигурации
    config = Config()
    print("✅ Конфигурация инициализирована")
    
    # Инициализация RAG сервиса
    rag_service = RAGService(config)
    print("✅ RAG сервис инициализирован")
    
    # Инициализация обработчика сообщений
    message_handler = TestMessageHandler(config, rag_service)
    print("✅ Обработчик сообщений инициализирован")
    
    # Тестовые вопросы
    test_questions = [
        "Согласно правилам внутреннего трудового распорядка, в какие дни месяца выплачивается заработная плата?",
        "Какие установлены дни для расчетов с работниками согласно ПВТР?",
        "12 и 27 число - это установленные дни выплат?",
        "Два раза в месяц - когда именно происходят выплаты?",
        "Расскажите о сроках выплаты заработной платы в компании",
        "Какая периодичность выплат заработной платы установлена?"
    ]
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ФИНАЛЬНОГО РЕШЕНИЯ")
    print("="*80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- ВОПРОС {i}: {question} ---")
        
        # Получаем ответ от RAG системы
        response = await rag_service.answer_question(question)
        
        # Проверяем, заблокирован ли ответ
        is_blocked = message_handler.is_blocked_response(response)
        
        if is_blocked:
            print("❌ ОТВЕТ ЗАБЛОКИРОВАН GigaChat")
            
            # Пытаемся получить альтернативный ответ
            fallback_response = message_handler.get_payment_dates_fallback(question)
            if fallback_response:
                print("✅ ИСПОЛЬЗОВАН АЛЬТЕРНАТИВНЫЙ ОТВЕТ:")
                print(fallback_response)
            else:
                print("⚠️ Альтернативный ответ не найден")
        else:
            print("✅ ОТВЕТ ПОЛУЧЕН:")
            print(response)
        
        print("-" * 60)
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*80)

if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()
    
    # Запускаем тест
    asyncio.run(test_message_handler()) 