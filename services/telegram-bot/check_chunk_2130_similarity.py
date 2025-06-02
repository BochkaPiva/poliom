#!/usr/bin/env python3
"""
Проверка similarity score чанка 2130 при разных запросах
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
    """Проверка similarity score чанка 2130"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        print("\n" + "=" * 80)
        print("ПРОВЕРКА SIMILARITY SCORE ЧАНКА 2130")
        print("=" * 80)
        
        # Тестовые запросы
        test_queries = [
            "12 и 27 число",
            "установленные дни для расчетов",
            "заработная плата выплачивается два раза",
            "12-е и 27-е числа месяца",
            "два раза в месяц",
            "расчеты с работниками"
        ]
        
        for query in test_queries:
            print(f"\n--- ЗАПРОС: '{query}' ---")
            
            # Получаем ВСЕ результаты поиска (без лимита)
            loop = asyncio.get_event_loop()
            all_chunks = await loop.run_in_executor(
                None,
                rag_service.rag_system.search_relevant_chunks,
                query,
                50  # Увеличиваем лимит
            )
            
            # Ищем чанк 2130 среди всех результатов
            found_2130 = False
            for i, chunk in enumerate(all_chunks, 1):
                if chunk.get('id') == 2130:
                    found_2130 = True
                    similarity = chunk.get('similarity', 'N/A')
                    print(f"  🎯 Чанк 2130 найден на позиции {i} с similarity: {similarity}")
                    break
            
            if not found_2130:
                print("  ❌ Чанк 2130 НЕ найден даже в топ-50")
        
        print("\n" + "=" * 80)
        print("ПРОВЕРКА ЗАВЕРШЕНА")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 