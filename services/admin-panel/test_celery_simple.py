#!/usr/bin/env python3
"""
Простой тест Celery worker
"""

import os
import sys
from pathlib import Path

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from celery_app import app
from tasks import process_document

def test_celery_connection():
    """Тестируем подключение к Celery"""
    print("🔍 Тестируем подключение к Celery...")
    
    try:
        # Проверяем статус worker'ов
        inspect = app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery worker активен!")
            for worker_name, worker_stats in stats.items():
                print(f"   Worker: {worker_name}")
                print(f"   Пул: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
        else:
            print("❌ Нет активных worker'ов")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_simple_task():
    """Тестируем простую задачу"""
    print("\n📝 Тестируем простую задачу...")
    print("ℹ️  Для полного теста нужен документ в базе данных")
    print("ℹ️  Пока просто проверим, что задача может быть отправлена")
    
    try:
        # Проверяем, что задача зарегистрирована
        registered_tasks = list(app.tasks.keys())
        print(f"📋 Зарегистрированные задачи: {registered_tasks}")
        
        if 'tasks.process_document' in registered_tasks:
            print("✅ Задача process_document зарегистрирована")
            return True
        else:
            print("❌ Задача process_document не найдена")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки задач: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Тестирование Celery интеграции\n")
    
    # Тестируем подключение
    if not test_celery_connection():
        print("\n❌ Celery worker не запущен или недоступен")
        print("💡 Запустите worker командой: celery -A celery_app worker --loglevel=info")
        return False
    
    # Тестируем задачу
    if not test_simple_task():
        print("\n❌ Тест задачи не прошел")
        return False
    
    print("\n🎉 Все тесты прошли успешно!")
    print("✅ Celery готов к работе")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 