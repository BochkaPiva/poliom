#!/usr/bin/env python3
"""
Обработка нового документа с улучшенным алгоритмом чанкинга
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from sqlalchemy.orm import sessionmaker
from shared.models.database import engine
from shared.models import Document, DocumentChunk
from shared.utils.document_processor import DocumentProcessor
from shared.utils.embeddings import EmbeddingService

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def process_document_with_improved_chunking(document_id: int):
    """Обрабатываем документ с улучшенным алгоритмом чанкинга"""
    print(f"🔄 Обработка документа ID: {document_id} с улучшенным алгоритмом")
    
    db = SessionLocal()
    try:
        # Получаем документ из базы данных
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ {document_id} не найден")
            return False
        
        print(f"📄 Документ: {document.original_filename}")
        print(f"📁 Путь: {document.file_path}")
        print(f"📊 Текущий статус: {document.processing_status}")
        
        # Проверяем, что файл существует
        file_path = Path(document.file_path)
        if not file_path.exists():
            print(f"❌ Файл не найден: {document.file_path}")
            return False
        
        print(f"✅ Файл найден: {file_path.stat().st_size} байт")
        
        # Обновляем статус на "processing"
        document.processing_status = "processing"
        document.updated_at = datetime.utcnow()
        db.commit()
        print("📊 Статус изменен на 'processing'")
        
        # Удаляем старые чанки если есть
        old_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        if old_chunks:
            print(f"🗑️ Удаляем {len(old_chunks)} старых чанков...")
            for chunk in old_chunks:
                db.delete(chunk)
            db.commit()
        
        # Инициализируем процессор документов
        print("🔧 Инициализируем процессор документов...")
        processor = DocumentProcessor()
        
        # Извлекаем текст из документа
        print("📖 Извлекаем текст из документа...")
        text_content = processor.extract_text(document.file_path)
        if not text_content or not text_content.strip():
            raise Exception("Не удалось извлечь текст из документа")
        
        print(f"✅ Текст извлечен: {len(text_content)} символов")
        
        # Разбиваем текст на чанки с УЛУЧШЕННЫМ алгоритмом
        print("✂️ Разбиваем текст на чанки (улучшенный алгоритм)...")
        chunks = processor.split_into_chunks(text_content, chunk_size=1000, overlap=200)
        if not chunks:
            raise Exception("Не удалось разбить документ на чанки")
        
        print(f"✅ Документ разбит на {len(chunks)} качественных чанков")
        
        # Анализируем размеры чанков
        chunk_sizes = [len(chunk) for chunk in chunks]
        print(f"📊 Статистика чанков:")
        print(f"   Минимальный размер: {min(chunk_sizes)} символов")
        print(f"   Максимальный размер: {max(chunk_sizes)} символов")
        print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        print(f"   Медианный размер: {sorted(chunk_sizes)[len(chunk_sizes)//2]} символов")
        
        # Показываем примеры чанков
        print(f"\n📋 Примеры чанков:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Чанк {i+1} ({len(chunk)} символов) ---")
            print(chunk[:300] + "..." if len(chunk) > 300 else chunk)
        
        # Инициализируем сервис эмбеддингов
        print("\n🧠 Инициализируем сервис эмбеддингов...")
        embedding_service = EmbeddingService()
        
        # Создаем чанки в базе данных
        print("💾 Создаем чанки в базе данных...")
        created_chunks = []
        for i, chunk_text in enumerate(chunks):
            try:
                print(f"  📝 Обрабатываем чанк {i+1}/{len(chunks)}...")
                
                # Генерируем эмбеддинг для чанка
                embedding = embedding_service.get_embedding(chunk_text)
                
                # Создаем чанк в базе данных
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk_text,
                    content_length=len(chunk_text),
                    embedding=embedding,
                    created_at=datetime.utcnow()
                )
                
                db.add(chunk)
                created_chunks.append(chunk)
                
                # Коммитим каждые 10 чанков для избежания проблем с памятью
                if (i + 1) % 10 == 0:
                    db.commit()
                    print(f"  💾 Сохранено {i+1} чанков...")
                
            except Exception as e:
                print(f"❌ Ошибка создания чанка {i}: {str(e)}")
                continue
        
        if not created_chunks:
            raise Exception("Не удалось создать ни одного чанка")
        
        # Финальное сохранение
        print("💾 Финальное сохранение чанков...")
        db.commit()
        
        # Обновляем статус документа на "completed"
        document.processing_status = "completed"
        document.processed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        document.chunks_count = len(created_chunks)
        db.commit()
        
        print(f"\n🎉 Документ {document_id} успешно обработан!")
        print(f"✅ Создано {len(created_chunks)} качественных чанков")
        print(f"📊 Статус изменен на 'completed'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обработки документа {document_id}: {str(e)}")
        
        # Обновляем статус документа на "failed"
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "failed"
                document.error_message = str(e)
                document.updated_at = datetime.utcnow()
                db.commit()
                print("📊 Статус изменен на 'failed'")
        except Exception as db_error:
            print(f"❌ Ошибка обновления статуса: {str(db_error)}")
        
        return False
        
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Обработка нового документа с улучшенным алгоритмом чанкинга\n")
    
    # Обрабатываем новый документ с ID 2
    document_id = 2
    success = process_document_with_improved_chunking(document_id)
    
    if success:
        print("\n✅ Обработка завершена успешно!")
        print("🔍 Проверим результаты в базе данных...")
        
        # Проверяем результаты
        db = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                print(f"📄 Документ: {document.original_filename}")
                print(f"📊 Статус: {document.processing_status}")
                print(f"📈 Количество чанков: {document.chunks_count}")
                
                # Проверяем чанки в базе
                chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
                if chunks:
                    chunk_sizes = [chunk.content_length for chunk in chunks]
                    print(f"\n📊 Статистика из базы данных:")
                    print(f"   Чанков в БД: {len(chunks)}")
                    print(f"   Мин. размер: {min(chunk_sizes)} символов")
                    print(f"   Макс. размер: {max(chunk_sizes)} символов")
                    print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        finally:
            db.close()
    else:
        print("\n❌ Обработка завершена с ошибкой!")
    
    return success

if __name__ == "__main__":
    main() 