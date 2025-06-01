#!/usr/bin/env python3
"""
Простой тест для демонстрации поиска с LLM
"""

import sys
import os
from pathlib import Path

# Добавляем путь к services для импорта модулей
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения из корневого .env файла
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from shared.utils.search_service import SearchService

def test_llm_search():
    """Тестирует LLM форматирование поиска"""
    print("🤖 ТЕСТ ПОИСКА С LLM ФОРМАТИРОВАНИЕМ")
    print("=" * 60)
    
    # Инициализируем сервис поиска
    search_service = SearchService()
    
    # Тестовые запросы
    test_queries = [
        "Сколько процентов доплата за ночную работу?",
        "Как оплачивается работа в праздничные дни?",
        "Какой размер надбавки за вредные условия труда?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 ТЕСТ {i}/{len(test_queries)}:")
        print(f"🔍 Запрос: {query}")
        print("-" * 60)
        
        try:
            result = search_service.search(query, max_results=5, min_similarity=0.5)
            
            print(f"📊 Качество поиска: {result['quality']}")
            print(f"📈 Лучшая схожесть: {result['best_similarity']:.3f}")
            print(f"📄 Найдено результатов: {len(result['results'])}")
            print(f"\n💬 ОТФОРМАТИРОВАННЫЙ ОТВЕТ:")
            print(result['formatted_answer'])
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 60)

def test_context_search():
    """Тестирует поиск с контекстом"""
    print("\n🔍 ТЕСТ ПОИСКА С КОНТЕКСТОМ")
    print("=" * 60)
    
    # Инициализируем сервис поиска
    search_service = SearchService()
    
    query = "доплата за ночную работу"
    print(f"🔍 Запрос: {query}")
    print("-" * 60)
    
    try:
        result = search_service.search_with_context(query, context_size=2)
        
        print(f"📊 Качество: {result['quality']}")
        print(f"📄 Найдено: {len(result['results'])} результатов")
        if 'context_chunks' in result:
            print(f"🧩 Контекстных чанков: {len(result['context_chunks'])}")
        
        print(f"\n💬 ОТВЕТ С КОНТЕКСТОМ:")
        print(result['formatted_answer'])
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция"""
    # Проверяем наличие ключа GigaChat
    gigachat_key = os.getenv('GIGACHAT_API_KEY')
    if gigachat_key:
        print("✅ GigaChat API ключ найден - будет использоваться LLM форматирование")
    else:
        print("⚠️ GigaChat API ключ не найден - будет использоваться простое форматирование")
    
    try:
        test_llm_search()
        test_context_search()
        
        print("\n" + "=" * 60)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("📈 Система готова к использованию!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 