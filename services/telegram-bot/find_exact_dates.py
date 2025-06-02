#!/usr/bin/env python3
"""
Поиск чанков с точными датами выплат
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
    """Поиск чанков с датами"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Прямой поиск в базе данных
        print("\n🔍 ПОИСК ЧАНКОВ С ДАТАМИ В БАЗЕ ДАННЫХ")
        print("=" * 80)
        
        # Получаем доступ к базе данных напрямую
        db_session = next(get_db_session())
        
        # Поиск чанков с "15"
        from sqlalchemy import text
        
        query = text("""
            SELECT dc.id, dc.document_id, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.content ILIKE '%15%'
            AND (dc.content ILIKE '%число%' OR dc.content ILIKE '%дата%' OR dc.content ILIKE '%аванс%')
            ORDER BY dc.id
        """)
        
        result = db_session.execute(query)
        chunks_15 = result.fetchall()
        
        print(f"Найдено {len(chunks_15)} чанков с '15':")
        for chunk in chunks_15:
            print(f"\nЧанк {chunk.id} (Документ: {chunk.title}):")
            print(chunk.content[:400] + "..." if len(chunk.content) > 400 else chunk.content)
            print("-" * 60)
        
        # Поиск чанков с "25"
        query = text("""
            SELECT dc.id, dc.document_id, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.content ILIKE '%25%'
            AND (dc.content ILIKE '%число%' OR dc.content ILIKE '%дата%' OR dc.content ILIKE '%зарплат%')
            ORDER BY dc.id
        """)
        
        result = db_session.execute(query)
        chunks_25 = result.fetchall()
        
        print(f"\nНайдено {len(chunks_25)} чанков с '25':")
        for chunk in chunks_25:
            print(f"\nЧанк {chunk.id} (Документ: {chunk.title}):")
            print(chunk.content[:400] + "..." if len(chunk.content) > 400 else chunk.content)
            print("-" * 60)
        
        # Поиск чанков со словами "выплата" и "срок"
        query = text("""
            SELECT dc.id, dc.document_id, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE (dc.content ILIKE '%срок%выплат%' OR dc.content ILIKE '%дата%выплат%')
            ORDER BY dc.id
        """)
        
        result = db_session.execute(query)
        chunks_dates = result.fetchall()
        
        print(f"\nНайдено {len(chunks_dates)} чанков со сроками выплат:")
        for chunk in chunks_dates:
            print(f"\nЧанк {chunk.id} (Документ: {chunk.title}):")
            print(chunk.content[:400] + "..." if len(chunk.content) > 400 else chunk.content)
            print("-" * 60)
        
        # Поиск чанков с информацией о правилах внутреннего трудового распорядка
        query = text("""
            SELECT dc.id, dc.document_id, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.content ILIKE '%правил%внутренн%трудов%распорядк%'
            OR dc.content ILIKE '%ПВТР%'
            ORDER BY dc.id
        """)
        
        result = db_session.execute(query)
        chunks_pvtr = result.fetchall()
        
        print(f"\nНайдено {len(chunks_pvtr)} чанков с ПВТР:")
        for chunk in chunks_pvtr:
            print(f"\nЧанк {chunk.id} (Документ: {chunk.title}):")
            print(chunk.content[:400] + "..." if len(chunk.content) > 400 else chunk.content)
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 