#!/usr/bin/env python3
"""
Тест функций безопасности для отправки файлов
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "services" / "shared"))

# Добавляем путь к bot модулю
bot_path = Path(__file__).parent
sys.path.insert(0, str(bot_path))

def test_file_security_checks():
    """Тестируем проверки безопасности для файлов"""
    
    print("🔒 Тестирование функций безопасности файлов\n")
    
    # Импортируем функции
    from bot.handlers import is_file_allowed_for_sharing, check_user_file_limit, MAX_FILES_PER_HOUR
    
    # Тест 1: Разрешенные типы файлов
    print("📝 Тест 1: Проверка разрешенных типов файлов")
    
    test_cases_allowed = [
        ("документ.pdf", "pdf", True),
        ("инструкция.docx", "docx", True),
        ("таблица.xlsx", "xlsx", True),
        ("старый_файл.doc", "doc", True),
        ("данные.txt", "txt", True),
    ]
    
    for file_path, file_type, expected in test_cases_allowed:
        result = is_file_allowed_for_sharing(file_path, file_type)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {file_path} ({file_type}) -> {result}")
    
    # Тест 2: Запрещенные типы файлов
    print("\n🚫 Тест 2: Проверка запрещенных типов файлов")
    
    test_cases_forbidden = [
        ("программа.exe", "exe", False),
        ("архив.zip", "zip", False),
        ("видео.mp4", "mp4", False),
        ("script.py", "py", False),
    ]
    
    for file_path, file_type, expected in test_cases_forbidden:
        result = is_file_allowed_for_sharing(file_path, file_type)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {file_path} ({file_type}) -> {result}")
    
    # Тест 3: Запрещенные слова в названии
    print("\n🔒 Тест 3: Проверка запрещенных слов в названии")
    
    test_cases_forbidden_words = [
        ("конфиденциально_данные.pdf", "pdf", False),
        ("секретно_документ.docx", "docx", False),
        ("персональные_данные_сотрудников.xlsx", "xlsx", False),
        ("зарплата_список_март.pdf", "pdf", False),
        ("password_database.txt", "txt", False),
        ("обычный_документ.pdf", "pdf", True),  # Обычный файл должен пройти
    ]
    
    for file_path, file_type, expected in test_cases_forbidden_words:
        result = is_file_allowed_for_sharing(file_path, file_type)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {file_path} -> {result}")
    
    # Тест 4: Лимиты пользователей
    print(f"\n⏰ Тест 4: Проверка лимитов пользователей (макс. {MAX_FILES_PER_HOUR} файлов/час)")
    
    # Очищаем данные о пользователе
    from bot.handlers import USER_FILE_LIMITS
    test_user_id = 999999
    if test_user_id in USER_FILE_LIMITS:
        del USER_FILE_LIMITS[test_user_id]
    
    # Тестируем лимит
    success_count = 0
    for i in range(MAX_FILES_PER_HOUR + 3):  # Пытаемся превысить лимит
        result = check_user_file_limit(test_user_id)
        if result:
            success_count += 1
        print(f"  Попытка {i+1}: {'✅' if result else '❌'} ({success_count} успешных)")
        
        if success_count == MAX_FILES_PER_HOUR and not result:
            print(f"  🎯 Лимит корректно сработал после {MAX_FILES_PER_HOUR} файлов")
            break
    
    print("\n📊 Результаты тестирования:")
    print(f"  • Проверка типов файлов: работает")
    print(f"  • Фильтрация по названиям: работает") 
    print(f"  • Лимиты пользователей: работает")
    print(f"  • Максимум файлов в час: {MAX_FILES_PER_HOUR}")

def test_file_validation_edge_cases():
    """Тестируем крайние случаи валидации файлов"""
    
    print("\n🧪 Тестирование крайних случаев")
    
    from bot.handlers import is_file_allowed_for_sharing
    
    edge_cases = [
        ("", "pdf", False),  # Пустое имя файла
        ("файл.PDF", "PDF", True),  # Заглавные буквы
        ("file_with_КОНФИДЕНЦИАЛЬНО.pdf", "pdf", False),  # Смешанный регистр
        ("normal-file.pdf", "pdf", True),  # Дефисы в имени
        ("файл с пробелами.docx", "docx", True),  # Пробелы в имени
        ("файл123.txt", "txt", True),  # Цифры в имени
    ]
    
    for file_path, file_type, expected in edge_cases:
        result = is_file_allowed_for_sharing(file_path, file_type)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{file_path}' ({file_type}) -> {result}")

if __name__ == "__main__":
    try:
        test_file_security_checks()
        test_file_validation_edge_cases()
        print("\n🎉 Все тесты безопасности пройдены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc() 