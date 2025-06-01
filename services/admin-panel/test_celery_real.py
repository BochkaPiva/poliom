#!/usr/bin/env python3
"""
Реальный тест Celery с отправкой задачи
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

def test_celery_ping():
    """Простой пинг Celery"""
    print("🔍 Тестируем Celery ping...")
    
    try:
        # Простой пинг
        result = app.control.ping(timeout=5)
        print(f"📡 Ping результат: {result}")
        
        if result:
            print("✅ Celery worker отвечает на ping!")
            return True
        else:
            print("❌ Worker не отвечает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка ping: {e}")
        return False

def test_simple_add_task():
    """Тестируем простую задачу сложения"""
    print("\n➕ Тестируем простую задачу...")
    
    try:
        # Создаем простую задачу
        @app.task
        def add(x, y):
            return x + y
        
        # Отправляем задачу
        result = add.delay(4, 4)
        print(f"📤 Задача отправлена: {result.id}")
        
        # Ждем результат
        try:
            task_result = result.get(timeout=10)
            print(f"✅ Результат: {task_result}")
            return task_result == 8
            
        except Exception as e:
            print(f"❌ Ошибка получения результата: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания задачи: {e}")
        return False

def test_inspect_workers():
    """Проверяем активных worker'ов"""
    print("\n🔍 Проверяем активных worker'ов...")
    
    try:
        inspect = app.control.inspect()
        
        # Получаем статистику
        stats = inspect.stats()
        print(f"📊 Статистика: {stats}")
        
        # Получаем активные задачи
        active = inspect.active()
        print(f"🏃 Активные задачи: {active}")
        
        # Получаем зарегистрированные задачи
        registered = inspect.registered()
        print(f"📋 Зарегистрированные задачи: {registered}")
        
        return stats is not None
        
    except Exception as e:
        print(f"❌ Ошибка инспекции: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Реальное тестирование Celery\n")
    
    # Тестируем ping
    ping_ok = test_celery_ping()
    
    # Проверяем worker'ов
    inspect_ok = test_inspect_workers()
    
    # Тестируем простую задачу
    task_ok = test_simple_add_task()
    
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ:")
    print("="*50)
    print(f"Ping: {'✅' if ping_ok else '❌'}")
    print(f"Инспекция: {'✅' if inspect_ok else '❌'}")
    print(f"Задача: {'✅' if task_ok else '❌'}")
    
    if all([ping_ok, inspect_ok, task_ok]):
        print("\n🎉 Celery работает отлично!")
        return True
    else:
        print("\n⚠️ Есть проблемы с Celery")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 