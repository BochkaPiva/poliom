#!/usr/bin/env python3
"""
Точный поиск чанков с информацией о датах выплат 12 и 27 числа
"""

import sys
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
    from bot.database import get_db_session
    from sqlalchemy import text
    print("✅ Модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def main():
    """Поиск точных дат выплат"""
    try:
        # Получаем доступ к базе данных
        db_session = next(get_db_session())
        
        print("=" * 80)
        print("ПОИСК ЧАНКОВ С ДАТАМИ ВЫПЛАТ 12 И 27 ЧИСЛА")
        print("=" * 80)
        
        # Ищем чанки, содержащие одновременно 12 и 27
        query = text("""
            SELECT dc.id, dc.document_id, dc.chunk_index, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.content ILIKE '%12%' 
              AND dc.content ILIKE '%27%'
              AND (dc.content ILIKE '%выплат%' OR dc.content ILIKE '%зарплат%' OR dc.content ILIKE '%расчет%')
            ORDER BY dc.document_id, dc.chunk_index
        """)
        
        result = db_session.execute(query)
        chunks = result.fetchall()
        
        print(f"Найдено {len(chunks)} чанков с датами 12 и 27:")
        
        for chunk in chunks:
            print(f"\n{'='*60}")
            print(f"Чанк ID: {chunk.id}")
            print(f"Документ: {chunk.title}")
            print(f"Индекс: {chunk.chunk_index}")
            print(f"{'='*60}")
            print(chunk.content)
            print(f"{'='*60}")
        
        # Дополнительный поиск по фразам
        print(f"\n" + "=" * 80)
        print("ПОИСК ПО КЛЮЧЕВЫМ ФРАЗАМ:")
        print("=" * 80)
        
        phrases = [
            "12-е и 27-е",
            "12 и 27 число",
            "установленные дни для расчетов",
            "заработная плата выплачивается",
            "два раза в месяц"
        ]
        
        for phrase in phrases:
            print(f"\n--- Поиск по фразе: '{phrase}' ---")
            
            query_phrase = text("""
                SELECT dc.id, dc.document_id, dc.chunk_index, dc.content, d.title
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.content ILIKE :phrase
                ORDER BY dc.document_id, dc.chunk_index
            """)
            
            result_phrase = db_session.execute(query_phrase, {'phrase': f'%{phrase}%'})
            phrase_chunks = result_phrase.fetchall()
            
            if phrase_chunks:
                for chunk in phrase_chunks:
                    print(f"Чанк {chunk.id} ({chunk.title}): {chunk.content[:200]}...")
            else:
                print("Не найдено")
        
        # Поиск в документе ПВТР (ID=3)
        print(f"\n" + "=" * 80)
        print("ПОИСК В ДОКУМЕНТЕ 'ПРАВИЛА ВНУТРЕННЕГО ТРУДОВОГО РАСПОРЯДКА':")
        print("=" * 80)
        
        query_pvtr = text("""
            SELECT dc.id, dc.chunk_index, dc.content
            FROM document_chunks dc
            WHERE dc.document_id = 3
              AND (dc.content ILIKE '%12%' OR dc.content ILIKE '%27%')
            ORDER BY dc.chunk_index
        """)
        
        result_pvtr = db_session.execute(query_pvtr)
        pvtr_chunks = result_pvtr.fetchall()
        
        print(f"Найдено {len(pvtr_chunks)} чанков в ПВТР с числами 12 или 27:")
        
        for chunk in pvtr_chunks:
            print(f"\n--- Чанк {chunk.id} (индекс {chunk.chunk_index}) ---")
            print(chunk.content)
            print("-" * 60)
        
        db_session.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 