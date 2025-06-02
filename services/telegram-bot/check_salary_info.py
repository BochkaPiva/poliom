#!/usr/bin/env python3
"""
Скрипт для проверки информации о зарплате в документах
"""

import sys
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

# Добавляем пути к модулям
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "services" / "telegram-bot"))

# Загружаем переменные окружения
load_dotenv(project_root / ".env")
load_dotenv(project_root / "services" / "telegram-bot" / ".env.local")

print("✅ Загружены файлы окружения")

try:
    from bot.rag_service import RAGService
    from bot.config import Config
    print("✅ Модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

async def main():
    """Основная функция для проверки информации о зарплате"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Список запросов для поиска информации о зарплате
        queries = [
            "зарплата выплата",
            "график выплаты заработной платы",
            "дата выплаты зарплаты",
            "когда выплачивается зарплата",
            "заработная плата сроки",
            "выплата заработной платы число месяца"
        ]
        
        print("\n🔍 Поиск информации о зарплате...")
        
        for query in queries:
            print(f"\n--- Запрос: '{query}' ---")
            try:
                result = await rag_service.search_documents(query, limit=3)
                
                if result.get('success', False) and result.get('chunks'):
                    print(f"Найдено {len(result['chunks'])} релевантных фрагментов:")
                    for i, chunk in enumerate(result['chunks'], 1):
                        print(f"\n{i}. Документ ID: {chunk.get('document_id', 'N/A')}")
                        print(f"   Схожесть: {chunk.get('similarity', 'N/A'):.3f}")
                        print(f"   Содержание: {chunk.get('content', 'N/A')[:200]}...")
                else:
                    print("❌ Релевантные фрагменты не найдены")
                    
            except Exception as e:
                print(f"❌ Ошибка поиска для запроса '{query}': {e}")
        
        # Проверим общий статус системы
        print("\n📊 Проверка статуса системы...")
        health = await rag_service.health_check()
        print(f"Общий статус: {'✅' if health['overall'] else '❌'}")
        print(f"LLM: {'✅' if health['llm'] else '❌'}")
        print(f"Embeddings: {'✅' if health['embeddings'] else '❌'}")
        print(f"База данных: {'✅' if health['database'] else '❌'}")
        print(f"Количество документов: {health['documents_count']}")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 