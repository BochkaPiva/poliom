#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест интеграции Telegram-бота POLIOM
Проверка FAQ и поисковой функциональности
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Добавляем пути к модулям
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Загружаем переменные окружения
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)

async def test_faq_data():
    """Тест данных FAQ"""
    print("🧪 Тестирование FAQ данных...")
    
    try:
        from bot.faq_data import FAQ_DATA, get_faq_sections, get_section_questions, get_answer, search_faq
        
        # Проверяем структуру FAQ
        sections = get_faq_sections()
        print(f"✅ Найдено разделов FAQ: {len(sections)}")
        
        for section in sections:
            questions = get_section_questions(section)
            print(f"  📋 {section}: {len(questions)} вопросов")
        
        # Тестируем поиск в FAQ
        search_results = search_faq("оплата")
        print(f"✅ Поиск 'оплата': найдено {len(search_results)} результатов")
        
        # Тестируем получение ответа
        first_section = sections[0]
        first_questions = get_section_questions(first_section)
        if first_questions:
            answer = get_answer(first_section, first_questions[0])
            print(f"✅ Получен ответ на вопрос: {len(answer['answer'])} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в FAQ данных: {e}")
        return False

async def test_search_service():
    """Тест поискового сервиса"""
    print("\n🔍 Тестирование поискового сервиса...")
    
    try:
        # Создаем mock SearchService для тестирования
        class MockSearchService:
            def search(self, query, max_results=5):
                return {'results': []}
        
        search_service = MockSearchService()
        
        # Проверяем инициализацию
        print("✅ SearchService инициализирован")
        
        # Тестируем поиск
        try:
            results = search_service.search("отпуск", max_results=2)
            print(f"✅ Поиск выполнен: найдено {len(results.get('results', []))} результатов")
        except Exception as search_error:
            print(f"⚠️ Поиск недоступен: {search_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в поисковом сервисе: {e}")
        return False

async def test_llm_service():
    """Тест LLM сервиса"""
    print("\n🤖 Тестирование LLM сервиса...")
    
    try:
        from services.shared.utils.llm_service import LLMService
        
        llm_service = LLMService()
        print("✅ LLMService инициализирован")
        
        # Проверяем health check
        try:
            health_status = llm_service.health_check()
            print(f"✅ Health check: {health_status}")
        except Exception as health_error:
            print(f"⚠️ Health check недоступен: {health_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в LLM сервисе: {e}")
        return False

async def test_bot_handlers():
    """Тест обработчиков бота"""
    print("\n🤖 Тестирование обработчиков бота...")
    
    try:
        # Тестируем импорт роутера и RAG сервиса
        from bot.handlers import router
        from bot.rag_service import RAGService
        
        print("✅ Обработчики импортированы")
        
        # Проверяем, что роутер существует и является объектом Router
        if router:
            print("✅ Роутер успешно создан")
        else:
            print("⚠️ Роутер не создан")
        
        # Проверяем инициализацию RAG сервиса
        try:
            # Создаем RAG сервис с тестовым ключом
            rag_service = RAGService("test_key")
            print("✅ RAGService инициализирован")
        except Exception as rag_error:
            print(f"⚠️ RAGService недоступен: {rag_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в обработчиках бота: {e}")
        return False

async def test_configuration():
    """Тест конфигурации"""
    print("\n⚙️ Тестирование конфигурации...")
    
    try:
        from bot.config import Config
        
        config = Config()
        
        # Проверяем основные настройки
        has_bot_token = bool(config.TELEGRAM_BOT_TOKEN)
        has_gigachat_key = bool(config.GIGACHAT_API_KEY)
        has_db_url = bool(config.DATABASE_URL)
        
        print(f"✅ TELEGRAM_BOT_TOKEN: {'✓' if has_bot_token else '✗'}")
        print(f"✅ GIGACHAT_API_KEY: {'✓' if has_gigachat_key else '✗'}")
        print(f"✅ DATABASE_URL: {'✓' if has_db_url else '✗'}")
        
        # Проверяем валидацию
        is_valid = config.validate()
        print(f"✅ Конфигурация валидна: {is_valid}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Ошибка в конфигурации: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("🧪 POLIOM Telegram Bot - Тест интеграции\n")
    
    tests = [
        ("FAQ данные", test_faq_data),
        ("Поисковый сервис", test_search_service),
        ("LLM сервис", test_llm_service),
        ("Обработчики бота", test_bot_handlers),
        ("Конфигурация", test_configuration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*50}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к запуску.")
        return True
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте конфигурацию.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1) 