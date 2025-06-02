#!/usr/bin/env python3
"""
Поиск конкретных дат выплат в ПВТР
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
    """Поиск дат в ПВТР"""
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
        
        print("\n🔍 ПОИСК ВСЕХ ЧАНКОВ ИЗ ДОКУМЕНТА 'ПРАВИЛА ВНУТРЕННЕГО ТРУДОВОГО РАСПОРЯДКА'")
        print("=" * 80)
        
        from sqlalchemy import text
        
        # Поиск всех чанков из документа ПВТР
        query = text("""
            SELECT dc.id, dc.document_id, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.title ILIKE '%правил%внутренн%трудов%распорядк%'
            ORDER BY dc.chunk_index
        """)
        
        result = db_session.execute(query)
        chunks_pvtr = result.fetchall()
        
        print(f"Найдено {len(chunks_pvtr)} чанков в ПВТР:")
        
        # Ищем чанки с числами или датами
        relevant_chunks = []
        for chunk in chunks_pvtr:
            content_lower = chunk.content.lower()
            if any(word in content_lower for word in ['15', '25', 'число', 'дата', 'срок', 'выплат', 'зарплат', 'аванс']):
                relevant_chunks.append(chunk)
        
        print(f"\nИз них {len(relevant_chunks)} содержат информацию о датах/выплатах:")
        
        for i, chunk in enumerate(relevant_chunks, 1):
            print(f"\n--- ЧАНК {i} (ID: {chunk.id}) ---")
            print(chunk.content)
            print("-" * 80)
        
        # Дополнительный поиск по ключевым словам
        print(f"\n🔍 ПОИСК ЧАНКОВ СО СЛОВАМИ О ВЫПЛАТАХ")
        print("=" * 80)
        
        query = text("""
            SELECT dc.id, dc.document_id, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE (dc.content ILIKE '%выплат%зарплат%' 
                   OR dc.content ILIKE '%выплат%заработн%'
                   OR dc.content ILIKE '%срок%выплат%'
                   OR dc.content ILIKE '%дата%выплат%'
                   OR dc.content ILIKE '%график%выплат%')
            ORDER BY d.title, dc.chunk_index
        """)
        
        result = db_session.execute(query)
        payment_chunks = result.fetchall()
        
        print(f"Найдено {len(payment_chunks)} чанков с информацией о выплатах:")
        
        for i, chunk in enumerate(payment_chunks, 1):
            print(f"\n--- ЧАНК {i} (ID: {chunk.id}, Документ: {chunk.title}) ---")
            print(chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content)
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 