#!/usr/bin/env python3
"""
Прямая обработка документа без Celery
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

def improved_split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    УЛУЧШЕННЫЙ алгоритм разбиения текста на чанки
    Учитывает границы предложений и создает качественные чанки
    """
    if not text or not text.strip():
        return []
    
    text = text.strip()
    
    # Если текст короткий, возвращаем его как один чанк
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Определяем конец текущего чанка
        end = min(start + chunk_size, len(text))
        
        # Если это не последний чанк, ищем хорошее место для разрыва
        if end < len(text):
            # Ищем ближайшую границу предложения в последних 200 символах чанка
            search_start = max(start, end - 200)
            
            # Ищем разделители в порядке приоритета
            best_break = -1
            
            # 1. Точка с пробелом
            for i in range(end - 1, search_start - 1, -1):
                if i < len(text) - 1 and text[i] == '.' and text[i + 1] == ' ':
                    best_break = i + 1
                    break
            
            # 2. Восклицательный или вопросительный знак с пробелом
            if best_break == -1:
                for i in range(end - 1, search_start - 1, -1):
                    if i < len(text) - 1 and text[i] in '!?' and text[i + 1] == ' ':
                        best_break = i + 1
                        break
            
            # 3. Двойной перенос строки
            if best_break == -1:
                double_newline = text.rfind('\n\n', search_start, end)
                if double_newline != -1:
                    best_break = double_newline + 2
            
            # 4. Одинарный перенос строки
            if best_break == -1:
                newline = text.rfind('\n', search_start, end)
                if newline != -1:
                    best_break = newline + 1
            
            # 5. Пробел (последний вариант)
            if best_break == -1:
                space = text.rfind(' ', search_start, end)
                if space != -1:
                    best_break = space + 1
            
            # Если нашли хорошее место для разрыва, используем его
            if best_break != -1:
                end = best_break
        
        # Извлекаем чанк
        chunk = text[start:end].strip()
        
        # Добавляем чанк только если он не пустой и достаточно длинный
        if chunk and len(chunk) > 10:  # Минимум 10 символов
            chunks.append(chunk)
        
        # Вычисляем начало следующего чанка
        if end >= len(text):
            break
        
        # Следующий чанк начинается с учетом перекрытия
        # НО не раньше чем через минимальный шаг
        min_step = max(50, chunk_size // 4)  # Минимальный шаг - 50 символов или 1/4 размера чанка
        next_start = max(start + min_step, end - overlap)
        
        # Убеждаемся, что мы продвигаемся вперед
        if next_start <= start:
            next_start = start + min_step
        
        start = next_start
    
    return chunks

def process_document_directly(document_id: int):
    """Обрабатываем документ напрямую без Celery"""
    print(f"🔄 Прямая обработка документа ID: {document_id}")
    
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
        chunks = improved_split_into_chunks(text_content, chunk_size=1000, overlap=200)
        if not chunks:
            raise Exception("Не удалось разбить документ на чанки")
        
        print(f"✅ Документ разбит на {len(chunks)} качественных чанков")
        
        # Анализируем размеры чанков
        chunk_sizes = [len(chunk) for chunk in chunks]
        print(f"📊 Статистика чанков:")
        print(f"   Минимальный размер: {min(chunk_sizes)} символов")
        print(f"   Максимальный размер: {max(chunk_sizes)} символов")
        print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        
        # Инициализируем сервис эмбеддингов
        print("🧠 Инициализируем сервис эмбеддингов...")
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
                
            except Exception as e:
                print(f"❌ Ошибка создания чанка {i}: {str(e)}")
                continue
        
        if not created_chunks:
            raise Exception("Не удалось создать ни одного чанка")
        
        # Сохраняем все чанки
        print("💾 Сохраняем чанки в базе данных...")
        db.commit()
        
        # Обновляем статус документа на "completed"
        document.processing_status = "completed"
        document.processed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        document.chunks_count = len(created_chunks)
        db.commit()
        
        print(f"🎉 Документ {document_id} успешно обработан!")
        print(f"✅ Создано {len(created_chunks)} качественных чанков")
        
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
    print("🚀 Прямая обработка документов с улучшенным алгоритмом чанкинга\n")
    
    # Обрабатываем документ с ID 2 (новый документ)
    document_id = 2
    success = process_document_directly(document_id)
    
    if success:
        print("\n✅ Обработка завершена успешно!")
    else:
        print("\n❌ Обработка завершена с ошибкой!")
    
    return success

if __name__ == "__main__":
    main() 