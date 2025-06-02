#!/usr/bin/env python3
"""
БЕЗОПАСНЫЙ диагностический скрипт для проверки документов
Обходит проблемы с PostgreSQL vector типами
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
from sqlalchemy import text
from shared.models.database import engine
from shared.models import Document

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_documents_safe():
    """БЕЗОПАСНАЯ проверка всех документов в базе данных"""
    print("📋 БЕЗОПАСНАЯ ПРОВЕРКА ДОКУМЕНТОВ В БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Получаем все документы
        documents = db.query(Document).all()
        
        if not documents:
            print("❌ Документы не найдены в базе данных")
            return
        
        print(f"📊 Найдено документов: {len(documents)}")
        print()
        
        for doc in documents:
            print(f"📄 Документ ID {doc.id}: {doc.original_filename}")
            print(f"   📁 Путь: {doc.file_path}")
            print(f"   📊 Статус: {doc.processing_status}")
            print(f"   📈 Размер файла: {doc.file_size} байт")
            print(f"   🗓️ Загружен: {doc.created_at}")
            
            if doc.processed_at:
                print(f"   ✅ Обработан: {doc.processed_at}")
            
            if doc.chunks_count:
                print(f"   📦 Чанков: {doc.chunks_count}")
            
            if doc.error_message:
                print(f"   ❌ Ошибка: {doc.error_message}")
            
            # Проверяем существование файла
            file_path = Path(doc.file_path)
            if file_path.exists():
                actual_size = file_path.stat().st_size
                print(f"   ✅ Файл существует (размер: {actual_size} байт)")
                if actual_size != doc.file_size:
                    print(f"   ⚠️ ВНИМАНИЕ: Размер файла не совпадает с БД!")
            else:
                print(f"   ❌ ФАЙЛ НЕ НАЙДЕН: {doc.file_path}")
            
            # БЕЗОПАСНАЯ проверка чанков через SQL
            try:
                result = db.execute(
                    text("SELECT COUNT(*) as chunk_count FROM document_chunks WHERE document_id = :doc_id"),
                    {"doc_id": doc.id}
                )
                actual_chunks = result.fetchone()[0]
                
                if actual_chunks > 0:
                    print(f"   📦 Фактически чанков в БД: {actual_chunks}")
                    if doc.chunks_count != actual_chunks:
                        print(f"   ⚠️ ВНИМАНИЕ: Количество чанков не совпадает!")
                    
                    # Получаем статистику размеров через SQL
                    stats_result = db.execute(
                        text("""
                        SELECT 
                            MIN(content_length) as min_size,
                            MAX(content_length) as max_size,
                            ROUND(AVG(content_length)) as avg_size
                        FROM document_chunks 
                        WHERE document_id = :doc_id
                        """),
                        {"doc_id": doc.id}
                    )
                    stats = stats_result.fetchone()
                    if stats:
                        print(f"   📏 Размеры чанков: мин={stats[0]}, макс={stats[1]}, средний={stats[2]}")
                else:
                    print(f"   📦 Чанки в БД: отсутствуют")
                    
            except Exception as e:
                print(f"   ❌ Ошибка проверки чанков: {str(e)}")
            
            print()
        
        # Общая статистика
        print("=" * 60)
        print("📊 ОБЩАЯ СТАТИСТИКА:")
        
        statuses = {}
        total_chunks = 0
        total_size = 0
        
        for doc in documents:
            status = doc.processing_status
            statuses[status] = statuses.get(status, 0) + 1
            
            if doc.chunks_count:
                total_chunks += doc.chunks_count
            
            if doc.file_size:
                total_size += doc.file_size
        
        print(f"📄 Всего документов: {len(documents)}")
        print(f"📦 Всего чанков: {total_chunks}")
        print(f"💾 Общий размер: {total_size:,} байт ({total_size/1024/1024:.2f} МБ)")
        print()
        
        print("📊 По статусам:")
        for status, count in statuses.items():
            print(f"   {status}: {count}")
        
        # Дополнительная статистика через SQL
        try:
            print("\n📈 ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА (через SQL):")
            
            # Общее количество чанков
            total_chunks_sql = db.execute(text("SELECT COUNT(*) FROM document_chunks")).fetchone()[0]
            print(f"   📦 Всего чанков в БД: {total_chunks_sql}")
            
            # Статистика размеров всех чанков
            chunk_stats = db.execute(text("""
                SELECT 
                    MIN(content_length) as min_size,
                    MAX(content_length) as max_size,
                    ROUND(AVG(content_length)) as avg_size,
                    SUM(content_length) as total_size
                FROM document_chunks
            """)).fetchone()
            
            if chunk_stats and chunk_stats[0] is not None:
                print(f"   📏 Размеры чанков: мин={chunk_stats[0]}, макс={chunk_stats[1]}, средний={chunk_stats[2]}")
                print(f"   💾 Общий размер контента: {chunk_stats[3]:,} символов")
        
        except Exception as e:
            print(f"   ❌ Ошибка получения дополнительной статистики: {str(e)}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {str(e)}")
    
    finally:
        db.close()

def check_specific_document_safe(document_id: int):
    """БЕЗОПАСНАЯ детальная проверка конкретного документа"""
    print(f"🔍 БЕЗОПАСНАЯ ДЕТАЛЬНАЯ ПРОВЕРКА ДОКУМЕНТА ID {document_id}")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            print(f"❌ Документ с ID {document_id} не найден")
            return
        
        print(f"📄 Документ: {document.original_filename}")
        print(f"📁 Путь: {document.file_path}")
        print(f"📊 Статус: {document.processing_status}")
        print(f"📈 Размер: {document.file_size} байт")
        print(f"🗓️ Создан: {document.created_at}")
        print(f"🔄 Обновлен: {document.updated_at}")
        
        if document.processed_at:
            print(f"✅ Обработан: {document.processed_at}")
        
        if document.error_message:
            print(f"❌ Ошибка: {document.error_message}")
        
        print()
        
        # Проверяем файл
        file_path = Path(document.file_path)
        print("📁 ПРОВЕРКА ФАЙЛА:")
        if file_path.exists():
            stat = file_path.stat()
            print(f"   ✅ Файл существует")
            print(f"   📈 Размер: {stat.st_size} байт")
            print(f"   🗓️ Изменен: {stat.st_mtime}")
        else:
            print(f"   ❌ Файл не найден")
        
        print()
        
        # БЕЗОПАСНАЯ проверка чанков через SQL
        print(f"📦 ПРОВЕРКА ЧАНКОВ:")
        try:
            # Количество чанков
            chunk_count = db.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id"),
                {"doc_id": document_id}
            ).fetchone()[0]
            
            print(f"   📊 Количество: {chunk_count}")
            
            if chunk_count > 0:
                # Статистика размеров
                stats = db.execute(text("""
                    SELECT 
                        MIN(content_length) as min_size,
                        MAX(content_length) as max_size,
                        ROUND(AVG(content_length)) as avg_size
                    FROM document_chunks 
                    WHERE document_id = :doc_id
                """), {"doc_id": document_id}).fetchone()
                
                if stats:
                    print(f"   📏 Размеры: мин={stats[0]}, макс={stats[1]}, средний={stats[2]}")
                
                # Первые несколько чанков (только текст, без эмбеддингов)
                chunks_preview = db.execute(text("""
                    SELECT chunk_index, content_length, LEFT(content, 100) as preview
                    FROM document_chunks 
                    WHERE document_id = :doc_id 
                    ORDER BY chunk_index 
                    LIMIT 3
                """), {"doc_id": document_id}).fetchall()
                
                print(f"   📋 Первые 3 чанка:")
                for chunk in chunks_preview:
                    preview = chunk[2].replace('\n', ' ')
                    print(f"      {chunk[0]+1}. [{chunk[1]} символов] {preview}...")
            else:
                print(f"   📦 Чанки отсутствуют")
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки чанков: {str(e)}")
    
    except Exception as e:
        print(f"❌ Ошибка проверки документа: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Безопасная проверка документов в базе данных")
    parser.add_argument("--doc-id", type=int, help="ID конкретного документа для детальной проверки")
    
    args = parser.parse_args()
    
    if args.doc_id:
        check_specific_document_safe(args.doc_id)
    else:
        check_documents_safe() 