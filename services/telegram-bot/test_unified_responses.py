#!/usr/bin/env python3
"""
Тестирование единого формата ответов на вопросы о зарплате
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к shared модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

# Импортируем функции из handlers
from bot.handlers import extract_key_information, extract_specific_data_patterns, create_direct_answer, create_main_keyboard

def test_unified_salary_responses():
    """Тестируем единый формат ответов на вопросы о зарплате"""
    print("🔍 Тестирование единого формата ответов о зарплате:")
    print("=" * 70)
    
    # Различные варианты вопросов о зарплате
    salary_questions = [
        "Зарплата",
        "Даты зарплат", 
        "Когда выплачивается зарплата",
        "Дата выплат зарплаты",
        "Когда я получаю деньги",
        "Выплата заработной платы",
        "Сроки выплат"
    ]
    
    expected_response = """💰 **Выплата заработной платы:**

Согласно корпоративным документам:
• Заработная плата выплачивается **два раза в месяц**
• Установленными днями для расчетов с работниками являются **12-е** и **27-е** числа месяца
• При совпадении с выходными/праздниками выплата производится накануне

*Источники: Положение об оплате труда, Правила внутреннего трудового распорядка*"""
    
    # Тестовый контекст (не важен для зарплатных вопросов)
    test_context = """[Источник 1: Оплата труда]
    Заработная плата выплачивается два раза в месяц. Сроки выплаты устанавливаются в правилах.
    [Источник 2: Другой документ]
    Рабочий день составляет 8 часов. Премия 100 руб."""
    
    all_passed = True
    
    for i, question in enumerate(salary_questions, 1):
        print(f"\n🧪 Тест {i}: '{question}'")
        
        # Тестируем extract_key_information
        result = extract_key_information(test_context, question)
        
        if result == expected_response:
            print("✅ extract_key_information: ПРАВИЛЬНО")
        else:
            print("❌ extract_key_information: ОШИБКА")
            if result is None:
                print("Получено: None")
            else:
                print(f"Получено: {result[:100]}...")
            all_passed = False
        
        # Тестируем extract_specific_data_patterns (должно возвращать None)
        specific_result = extract_specific_data_patterns(test_context, question)
        
        if specific_result is None:
            print("✅ extract_specific_data_patterns: ПРАВИЛЬНО (None)")
        else:
            print("❌ extract_specific_data_patterns: ОШИБКА (должно быть None)")
            print(f"Получено: {specific_result}")
            all_passed = False
        
        # Тестируем create_direct_answer
        direct_result = create_direct_answer(question, "любой текст", "любые данные")
        
        if direct_result == expected_response:
            print("✅ create_direct_answer: ПРАВИЛЬНО")
        else:
            print("❌ create_direct_answer: ОШИБКА")
            print(f"Получено: {direct_result[:100]}...")
            all_passed = False
        
        print("-" * 70)
    
    return all_passed

def test_admin_keyboard():
    """Тестируем ограничение доступа к статусу системы"""
    print("\n🔐 Тестирование ограничения доступа к статусу системы:")
    print("=" * 70)
    
    # Тестируем для обычного пользователя
    regular_keyboard = create_main_keyboard(123456789)
    regular_buttons = [button.text for row in regular_keyboard.inline_keyboard for button in row]
    
    print(f"👤 Обычный пользователь (ID: 123456789)")
    print(f"📋 Кнопки: {regular_buttons}")
    
    if "🏥 Статус системы" not in regular_buttons:
        print("✅ Статус системы скрыт для обычного пользователя: ПРАВИЛЬНО")
        regular_test_passed = True
    else:
        print("❌ Статус системы виден обычному пользователю: ОШИБКА")
        regular_test_passed = False
    
    # Тестируем для администратора
    admin_keyboard = create_main_keyboard(429336806)
    admin_buttons = [button.text for row in admin_keyboard.inline_keyboard for button in row]
    
    print(f"\n👑 Администратор (ID: 429336806)")
    print(f"📋 Кнопки: {admin_buttons}")
    
    if "🏥 Статус системы" in admin_buttons:
        print("✅ Статус системы виден администратору: ПРАВИЛЬНО")
        admin_test_passed = True
    else:
        print("❌ Статус системы скрыт от администратора: ОШИБКА")
        admin_test_passed = False
    
    print("-" * 70)
    
    return regular_test_passed and admin_test_passed

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ЕДИНОГО ФОРМАТА ОТВЕТОВ")
    print("=" * 80)
    
    # Тестируем единый формат ответов о зарплате
    salary_tests_passed = test_unified_salary_responses()
    
    # Тестируем ограничение доступа к статусу системы
    admin_tests_passed = test_admin_keyboard()
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 80)
    print(f"💰 Единый формат зарплатных ответов: {'✅ ПРОЙДЕН' if salary_tests_passed else '❌ ПРОВАЛЕН'}")
    print(f"🔐 Ограничение доступа к статусу: {'✅ ПРОЙДЕН' if admin_tests_passed else '❌ ПРОВАЛЕН'}")
    
    if salary_tests_passed and admin_tests_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Бот готов к использованию с единым стилем ответов")
    else:
        print("\n❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("🔧 Требуется дополнительная настройка")

if __name__ == "__main__":
    load_dotenv()
    main() 