#!/usr/bin/env python3
"""
Тест поиска по новому документу
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text, create_engine

# Загружаем переменные окружения
current_dir = Path(__file__).parent
load_dotenv(current_dir / '.env.local')

# Создаем подключение к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def test_document_content():
    """Проверяем содержимое нового документа"""
    print("🔍 Тестирование содержимого нового документа")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Получаем информацию о новом документе (ID 8)
        doc_result = conn.execute(
            text("SELECT id, title, original_filename, processing_status, chunks_count FROM documents WHERE id = 8")
        )
        doc_info = doc_result.fetchone()
        
        if not doc_info:
            print("❌ Новый документ не найден")
            return
        
        doc_id, title, filename, status, chunks_count = doc_info
        print(f"📄 Документ: {title}")
        print(f"   Файл: {filename}")
        print(f"   Статус: {status}")
        print(f"   Чанков: {chunks_count}")
        print()
        
        # Получаем содержимое чанков (без эмбеддингов)
        chunks_result = conn.execute(
            text("""
                SELECT chunk_index, content, content_length 
                FROM document_chunks 
                WHERE document_id = :doc_id 
                ORDER BY chunk_index 
                LIMIT 5
            """),
            {"doc_id": doc_id}
        )
        
        print("📝 Первые 5 чанков:")
        print("-" * 60)
        
        for chunk in chunks_result:
            chunk_index, content, length = chunk
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"Чанк {chunk_index} (длина: {length}):")
            print(f"   {preview}")
            print()
        
        # Проверяем ключевые слова
        keywords = ["премирование", "премия", "работник", "сотрудник", "выплата"]
        print("🔍 Поиск ключевых слов:")
        print("-" * 60)
        
        for keyword in keywords:
            search_result = conn.execute(
                text("""
                    SELECT COUNT(*) as count, 
                           STRING_AGG(SUBSTRING(content, 1, 100), ' | ') as examples
                    FROM document_chunks 
                    WHERE document_id = :doc_id 
                    AND LOWER(content) LIKE LOWER(:keyword)
                """),
                {"doc_id": doc_id, "keyword": f"%{keyword}%"}
            )
            
            result = search_result.fetchone()
            count, examples = result
            
            if count > 0:
                print(f"✅ '{keyword}': найдено в {count} чанках")
                if examples:
                    print(f"   Примеры: {examples[:200]}...")
            else:
                print(f"❌ '{keyword}': не найдено")
            print()

def test_search_readiness():
    """Проверяем готовность к поиску"""
    print("🚀 Проверка готовности к поиску")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Проверяем наличие эмбеддингов
        embedding_result = conn.execute(
            text("""
                SELECT COUNT(*) as total_chunks,
                       COUNT(embedding) as chunks_with_embeddings
                FROM document_chunks 
                WHERE document_id = 8
            """)
        )
        
        result = embedding_result.fetchone()
        total, with_embeddings = result
        
        print(f"📊 Статистика эмбеддингов:")
        print(f"   Всего чанков: {total}")
        print(f"   С эмбеддингами: {with_embeddings}")
        
        if total == with_embeddings:
            print("✅ Все чанки имеют эмбеддинги - готов к семантическому поиску!")
        else:
            print(f"⚠️  {total - with_embeddings} чанков без эмбеддингов")
        
        print()
        
        # Проверяем размеры эмбеддингов
        size_result = conn.execute(
            text("""
                SELECT 
                    MIN(content_length) as min_size,
                    MAX(content_length) as max_size,
                    ROUND(AVG(content_length)) as avg_size
                FROM document_chunks 
                WHERE document_id = 8
            """)
        )
        
        size_info = size_result.fetchone()
        min_size, max_size, avg_size = size_info
        
        print(f"📏 Размеры чанков:")
        print(f"   Минимальный: {min_size} символов")
        print(f"   Максимальный: {max_size} символов")
        print(f"   Средний: {avg_size} символов")
        
        if 500 <= avg_size <= 1000:
            print("✅ Размеры чанков оптимальны для поиска!")
        else:
            print("⚠️  Размеры чанков могут быть не оптимальными")

def main():
    print("🧪 ТЕСТИРОВАНИЕ НОВОГО ДОКУМЕНТА")
    print("=" * 60)
    print()
    
    try:
        test_document_content()
        print()
        test_search_readiness()
        print()
        print("🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    main() 