#!/usr/bin/env python3
"""
Тест семантического поиска по документам
"""

import os
import sys
from pathlib import Path

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from sqlalchemy.orm import sessionmaker
from shared.models.database import engine
from shared.models import Document, DocumentChunk
from shared.utils.embeddings import EmbeddingService

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_semantic_search(query: str, top_k: int = 5):
    """Тестируем семантический поиск"""
    print(f"🔍 Семантический поиск: '{query}'")
    print("-" * 60)
    
    db = SessionLocal()
    try:
        # Инициализируем сервис эмбеддингов
        embedding_service = EmbeddingService()
        
        # Генерируем эмбеддинг для запроса
        print("🧠 Генерируем эмбеддинг для запроса...")
        query_embedding = embedding_service.get_embedding(query)
        print(f"✅ Эмбеддинг сгенерирован: {len(query_embedding)} измерений")
        
        # Выполняем поиск по косинусному сходству
        print(f"📊 Ищем {top_k} наиболее релевантных чанков...")
        
        # SQL запрос для поиска по косинусному сходству
        sql_query = """
        SELECT 
            dc.id,
            dc.document_id,
            dc.chunk_index,
            dc.content,
            dc.content_length,
            d.original_filename,
            1 - (dc.embedding <=> %s::vector) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE d.processing_status = 'completed'
        ORDER BY dc.embedding <=> %s::vector
        LIMIT %s
        """
        
        # Выполняем запрос
        result = db.execute(sql_query, (query_embedding, query_embedding, top_k))
        results = result.fetchall()
        
        if not results:
            print("❌ Результаты не найдены")
            return
        
        print(f"✅ Найдено {len(results)} результатов:")
        print()
        
        for i, row in enumerate(results, 1):
            chunk_id, doc_id, chunk_idx, content, content_len, filename, similarity = row
            
            print(f"📄 Результат {i}:")
            print(f"   Документ: {filename}")
            print(f"   Чанк: {chunk_idx + 1} (ID: {chunk_id})")
            print(f"   Сходство: {similarity:.4f}")
            print(f"   Размер: {content_len} символов")
            print(f"   Содержание: {content[:200]}...")
            print()
        
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
    finally:
        db.close()

def test_document_statistics():
    """Показываем статистику по документам"""
    print("📊 Статистика документов")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Получаем информацию о документах
        documents = db.query(Document).all()
        
        print(f"📚 Всего документов: {len(documents)}")
        print()
        
        for doc in documents:
            print(f"📄 {doc.original_filename}")
            print(f"   ID: {doc.id}")
            print(f"   Статус: {doc.processing_status}")
            print(f"   Чанков: {doc.chunks_count or 0}")
            print(f"   Размер файла: {doc.file_size} байт")
            print(f"   Загружен: {doc.created_at}")
            if doc.processed_at:
                print(f"   Обработан: {doc.processed_at}")
            print()
        
        # Статистика чанков
        chunk_stats = db.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                MIN(content_length) as min_size,
                MAX(content_length) as max_size,
                ROUND(AVG(content_length)) as avg_size
            FROM document_chunks
        """).fetchone()
        
        if chunk_stats:
            total, min_size, max_size, avg_size = chunk_stats
            print(f"📊 Общая статистика чанков:")
            print(f"   Всего чанков: {total}")
            print(f"   Минимальный размер: {min_size} символов")
            print(f"   Максимальный размер: {max_size} символов")
            print(f"   Средний размер: {avg_size} символов")
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Тестирование семантического поиска\n")
    
    # Показываем статистику
    test_document_statistics()
    print("\n" + "="*80 + "\n")
    
    # Тестовые запросы
    test_queries = [
        "социальная помощь работникам",
        "отпуск и дополнительные дни отдыха",
        "компенсация медицинских расходов",
        "оплата труда и заработная плата",
        "путевки в санаторий"
    ]
    
    for query in test_queries:
        test_semantic_search(query, top_k=3)
        print("\n" + "="*80 + "\n")
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    main() 