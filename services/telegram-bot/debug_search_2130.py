#!/usr/bin/env python3
"""
Отладка поиска чанка 2130 с информацией о датах выплат
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

try:
    from bot.rag_service import RAGService
    from bot.config import Config
    from bot.database import get_db_session
    print("✅ Модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

async def main():
    """Отладка поиска чанка 2130"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Получаем доступ к базе данных напрямую
        db_session = next(get_db_session())
        
        print("\n" + "=" * 80)
        print("ОТЛАДКА ПОИСКА ЧАНКА 2130")
        print("=" * 80)
        
        # Проверяем содержимое чанка 2130
        from sqlalchemy import text
        
        query = text("SELECT id, document_id, content FROM document_chunks WHERE id = 2130")
        result = db_session.execute(query)
        chunk_2130 = result.fetchone()
        
        if chunk_2130:
            print(f"Чанк 2130 найден:")
            print(f"Документ ID: {chunk_2130.document_id}")
            print(f"Содержимое: {chunk_2130.content[:200]}...")
        else:
            print("Чанк 2130 не найден!")
            return
        
        # Тестируем поиск с разными запросами
        test_queries = [
            "12 и 27 число",
            "установленные дни для расчетов",
            "заработная плата выплачивается два раза",
            "12-е и 27-е числа месяца"
        ]
        
        for query in test_queries:
            print(f"\n--- ТЕСТ ПОИСКА: '{query}' ---")
            
            # Получаем результаты поиска от RAG системы (синхронно)
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None,
                rag_service.rag_system.search_relevant_chunks,
                query,
                15
            )
            
            print(f"Найдено {len(chunks)} чанков:")
            
            found_2130 = False
            for i, chunk in enumerate(chunks, 1):
                chunk_id = chunk.get('id', 'N/A')
                similarity = chunk.get('similarity', 'N/A')
                content_preview = chunk.get('content', '')[:100] + "..."
                
                if chunk_id == 2130:
                    found_2130 = True
                    print(f"  ✅ {i}. Чанк {chunk_id} (similarity: {similarity})")
                    print(f"      {content_preview}")
                else:
                    print(f"  {i}. Чанк {chunk_id} (similarity: {similarity})")
                    print(f"      {content_preview}")
            
            if found_2130:
                print("  🎯 ЧАНК 2130 НАЙДЕН!")
            else:
                print("  ❌ Чанк 2130 НЕ найден в результатах")
        
        print("\n" + "=" * 80)
        print("ОТЛАДКА ЗАВЕРШЕНА")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 