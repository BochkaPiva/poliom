#!/usr/bin/env python3
"""
Скрипт для поиска конкретных дат выплаты зарплаты в документах
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
    """Поиск информации о датах выплаты зарплаты"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Список запросов для поиска конкретных дат
        queries = [
            "аванс 15 число месяца",
            "зарплата 25 число месяца", 
            "выплата 10 число",
            "дата выплаты заработной платы",
            "когда выплачивается аванс",
            "график выплат зарплаты",
            "15 число аванс",
            "25 число зарплата"
        ]
        
        print("\n🔍 Поиск конкретных дат выплаты зарплаты...")
        
        for query in queries:
            print(f"\n--- Запрос: '{query}' ---")
            try:
                result = await rag_service.search_documents(query, limit=5)
                
                if result.get('success', False) and result.get('chunks'):
                    print(f"Найдено {len(result['chunks'])} релевантных фрагментов:")
                    for i, chunk in enumerate(result['chunks'], 1):
                        print(f"\n{i}. Документ ID: {chunk.get('document_id', 'N/A')}")
                        print(f"   Схожесть: {chunk.get('similarity', 'N/A'):.3f}")
                        print(f"   Содержание: {chunk.get('content', 'N/A')[:400]}...")
                else:
                    print("❌ Релевантные фрагменты не найдены")
                    
            except Exception as e:
                print(f"❌ Ошибка поиска для запроса '{query}': {e}")
        
        # Попробуем получить полный ответ на вопрос о датах выплат
        print("\n📋 Получаем полный ответ о датах выплат...")
        try:
            result = await rag_service.answer_question("Когда выплачивается зарплата и аванс? Какие конкретные даты?")
            if result.get('success', False):
                print("Ответ системы:")
                print(result['answer'])
                print(f"\nИсточники: {len(result.get('sources', []))}")
                for source in result.get('sources', []):
                    print(f"- {source.get('title', 'N/A')}")
            else:
                print(f"❌ Ошибка получения ответа: {result.get('error', 'Неизвестная ошибка')}")
        except Exception as e:
            print(f"❌ Ошибка получения ответа: {e}")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 