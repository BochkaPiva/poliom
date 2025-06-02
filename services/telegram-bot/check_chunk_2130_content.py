#!/usr/bin/env python3
"""
Проверка содержимого чанка 2130 с информацией о датах выплат
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
    """Проверка содержимого чанка 2130"""
    try:
        # Получаем доступ к базе данных
        db_session = next(get_db_session())
        
        print("=" * 80)
        print("ПРОВЕРКА СОДЕРЖИМОГО ЧАНКА 2130")
        print("=" * 80)
        
        # Получаем полное содержимое чанка 2130
        query = text("""
            SELECT dc.id, dc.document_id, dc.chunk_index, dc.content, d.title
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.id = 2130
        """)
        
        result = db_session.execute(query)
        chunk = result.fetchone()
        
        if chunk:
            print(f"Чанк ID: {chunk.id}")
            print(f"Документ ID: {chunk.document_id}")
            print(f"Название документа: {chunk.title}")
            print(f"Индекс чанка: {chunk.chunk_index}")
            print(f"Длина содержимого: {len(chunk.content)} символов")
            print("\n" + "=" * 80)
            print("ПОЛНОЕ СОДЕРЖИМОЕ ЧАНКА 2130:")
            print("=" * 80)
            print(chunk.content)
            print("=" * 80)
            
            # Проверяем, содержит ли чанк ключевые слова
            content_lower = chunk.content.lower()
            keywords = ['12', '27', 'число', 'выплат', 'зарплат', 'расчет', 'установленные дни']
            
            print("\nПРОВЕРКА КЛЮЧЕВЫХ СЛОВ:")
            for keyword in keywords:
                if keyword in content_lower:
                    print(f"✅ '{keyword}' - НАЙДЕНО")
                else:
                    print(f"❌ '{keyword}' - НЕ НАЙДЕНО")
            
            # Ищем все чанки из того же документа с похожим содержимым
            print(f"\n" + "=" * 80)
            print(f"ДРУГИЕ ЧАНКИ ИЗ ДОКУМЕНТА '{chunk.title}' С ДАТАМИ:")
            print("=" * 80)
            
            query2 = text("""
                SELECT id, chunk_index, content
                FROM document_chunks 
                WHERE document_id = :doc_id 
                  AND (content ILIKE '%12%' OR content ILIKE '%27%' OR content ILIKE '%число%')
                ORDER BY chunk_index
            """)
            
            result2 = db_session.execute(query2, {'doc_id': chunk.document_id})
            related_chunks = result2.fetchall()
            
            for related_chunk in related_chunks:
                print(f"\n--- Чанк {related_chunk.id} (индекс {related_chunk.chunk_index}) ---")
                print(related_chunk.content[:300] + "..." if len(related_chunk.content) > 300 else related_chunk.content)
                
        else:
            print("❌ Чанк 2130 не найден!")
        
        db_session.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 