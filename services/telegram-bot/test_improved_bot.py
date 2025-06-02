#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенных функций бота
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к shared модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Импортируем функции из handlers
from bot.handlers import (
    is_blocked_response, 
    extract_key_information, 
    extract_specific_data_patterns,
    create_direct_answer
)

def test_blocked_response_detection():
    """Тестируем определение заблокированных ответов"""
    print("🔍 Тестирование определения заблокированных ответов:")
    
    test_cases = [
        "Я не могу предоставить информацию по данной теме",
        "Этот вопрос касается чувствительной темы",
        "Обычный ответ о зарплате",
        "Информация недоступна по политике безопасности"
    ]
    
    for case in test_cases:
        result = is_blocked_response(case)
        print(f"  '{case[:50]}...' -> {'ЗАБЛОКИРОВАН' if result else 'РАЗРЕШЕН'}")
    print()

def test_key_information_extraction():
    """Тестируем извлечение ключевой информации"""
    print("📝 Тестирование извлечения ключевой информации:")
    
    context = """
    Установленными днями для расчетов с работниками являются 12-е и 27-е числа месяца.
    Заработная плата выплачивается два раза в месяц.
    Рабочий день составляет 8 часов.
    Отпуск предоставляется 28 календарных дней в году.
    """
    
    questions = [
        "Когда я получаю зарплату?",
        "Сколько часов рабочий день?",
        "Сколько дней отпуска?"
    ]
    
    for question in questions:
        result = extract_key_information(context, question)
        print(f"  Вопрос: {question}")
        print(f"  Ответ: {result[:100] if result else 'Не найдено'}...")
        print()

def test_specific_data_extraction():
    """Тестируем извлечение специфических данных"""
    print("🔢 Тестирование извлечения специфических данных:")
    
    context = """
    Установленными днями для расчетов с работниками являются 12-е и 27-е числа месяца.
    Заработная плата выплачивается два раза в месяц.
    Размер премии составляет 15% от оклада.
    Стоимость обеда 500 рублей.
    """
    
    questions = [
        "Когда выплачивается зарплата?",
        "Какой размер премии?"
    ]
    
    for question in questions:
        result = extract_specific_data_patterns(context, question)
        print(f"  Вопрос: {question}")
        print(f"  Данные: {result[:150] if result else 'Не найдено'}...")
        print()

def test_direct_answer_creation():
    """Тестируем создание прямых ответов"""
    print("💬 Тестирование создания прямых ответов:")
    
    extracted_info = "Установленными днями для расчетов с работниками являются 12-е и 27-е числа месяца"
    specific_data = "📊 **Найденная информация:**\n💰 **Даты выплат:**\n• 12-е число\n• 27-е число"
    
    questions = [
        "Когда я получаю зарплату?",
        "Какой у нас рабочий график?",
        "Сколько дней отпуска?"
    ]
    
    for question in questions:
        result = create_direct_answer(question, extracted_info, specific_data)
        print(f"  Вопрос: {question}")
        print(f"  Прямой ответ: {result[:150]}...")
        print()

def main():
    """Основная функция тестирования"""
    print("🤖 Тестирование улучшенных функций бота\n")
    print("=" * 60)
    
    test_blocked_response_detection()
    test_key_information_extraction()
    test_specific_data_extraction()
    test_direct_answer_creation()
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    load_dotenv()
    main() 