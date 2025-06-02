#!/usr/bin/env python3
"""
Тестирование ответов на вопросы о зарплате
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

def test_salary_questions():
    """Тестируем ответы на различные вопросы о зарплате"""
    print("💰 Тестирование вопросов о зарплате:")
    print("=" * 60)
    
    # Контекст с информацией о выплатах (как в реальной базе)
    context = """
    [Источник 1: Оплата труда]
    Заработная плата выплачивается два раза в месяц. Сроки выплаты заработной платы за первую и за вторую половину месяца устанавливаются в правилах внутреннего трудового распорядка Общества. При совпадении дня выплаты с выходным или нерабочим праздничным днем, выплата заработной платы производится накануне выходного дня или праздника.
    
    [Источник 2: Правила внутреннего трудового распорядка]
    Установленными днями для расчетов с работниками являются 12-е и 27-е числа месяца.
    """
    
    questions = [
        "Когда я получаю зарплату?",
        "Зарплата",
        "Выплата зарплаты", 
        "Даты выплаты зарплаты",
        "Размер зарплаты",
        "Когда выплачивается заработная плата?"
    ]
    
    for question in questions:
        print(f"\n🔍 Вопрос: {question}")
        print("-" * 40)
        
        # Проверяем извлечение ключевой информации
        extracted_info = extract_key_information(context, question)
        print(f"📝 Извлеченная информация:")
        if extracted_info:
            print(extracted_info)
        else:
            print("Не найдено")
        
        # Проверяем извлечение специфических данных
        specific_data = extract_specific_data_patterns(context, question)
        print(f"\n📊 Специфические данные:")
        if specific_data:
            print(specific_data)
        else:
            print("Не найдено")
        
        # Создаем прямой ответ
        direct_answer = create_direct_answer(question, extracted_info, specific_data)
        print(f"\n💬 Прямой ответ:")
        if direct_answer:
            print(direct_answer)
        else:
            print("Не создан")
        
        print("\n" + "=" * 60)

def test_blocked_responses():
    """Тестируем обработку заблокированных ответов"""
    print("\n🚫 Тестирование заблокированных ответов:")
    print("=" * 60)
    
    blocked_responses = [
        "К сожалению, иногда генеративные языковые модели могут создавать некорректные ответы",
        "разговоры на чувствительные темы могут быть ограничены",
        "Как и любая языковая модель, GigaChat не обладает собственным мнением"
    ]
    
    for response in blocked_responses:
        is_blocked = is_blocked_response(response)
        print(f"📝 Ответ: {response[:50]}...")
        print(f"🚫 Заблокирован: {'ДА' if is_blocked else 'НЕТ'}")
        print("-" * 40)

def test_fallback_mechanism():
    """Тестируем fallback-механизм"""
    print("\n🔄 Тестирование fallback-механизма:")
    print("=" * 60)
    
    # Пустой контекст (ничего не найдено)
    empty_context = ""
    
    salary_questions = [
        "Когда зарплата?",
        "Выплата заработной платы",
        "Получаю деньги когда?"
    ]
    
    for question in salary_questions:
        print(f"\n🔍 Вопрос: {question}")
        
        # Проверяем, что ключевая информация не найдена
        extracted_info = extract_key_information(empty_context, question)
        specific_data = extract_specific_data_patterns(empty_context, question)
        
        print(f"📝 Извлечено: {'Да' if extracted_info else 'Нет'}")
        print(f"📊 Данные: {'Да' if specific_data else 'Нет'}")
        
        # Проверяем fallback
        direct_answer = create_direct_answer(question, extracted_info, specific_data)
        print(f"💬 Fallback ответ:")
        if direct_answer:
            print(direct_answer[:200] + "..." if len(direct_answer) > 200 else direct_answer)
        else:
            print("Не создан")
        
        print("-" * 40)

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТКИ ВОПРОСОВ О ЗАРПЛАТЕ")
    print("=" * 80)
    
    test_salary_questions()
    test_blocked_responses()
    test_fallback_mechanism()
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    load_dotenv()
    main() 