#!/usr/bin/env python3
"""
Прямой тест загрузки и обработки документа
"""

import os
import sys
import shutil
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
from shared.models import Document, Admin
from shared.utils.document_processor import DocumentProcessor
from shared.utils.embeddings import EmbeddingService

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_document():
    """Создаем тестовый документ в базе данных"""
    print("📄 Создаем тестовый документ в базе данных...")
    
    db = SessionLocal()
    try:
        # Получаем администратора
        admin = db.query(Admin).first()
        if not admin:
            print("❌ Администратор не найден")
            return None
        
        # Путь к тестовому файлу
        test_file = Path("test_document.txt")
        if not test_file.exists():
            print(f"❌ Тестовый файл не найден: {test_file}")
            return None
        
        # Создаем директорию uploads если её нет
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Копируем файл в uploads
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_test_document.txt"
        dest_path = uploads_dir / unique_filename
        
        shutil.copy2(test_file, dest_path)
        
        # Получаем размер файла
        file_size = dest_path.stat().st_size
        
        # Создаем запись в базе данных
        document = Document(
            filename=unique_filename,
            original_filename="test_document.txt",
            file_path=str(dest_path),
            file_size=file_size,
            file_type="txt",
            title="Тестовый документ для проверки улучшенного чанкинга",
            description="Документ для тестирования улучшенного алгоритма разбиения на чанки",
            processing_status="pending",
            uploaded_by=admin.id
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        print(f"✅ Документ создан с ID: {document.id}")
        print(f"📁 Файл: {dest_path}")
        print(f"📊 Размер: {file_size} байт")
        
        return document.id
        
    except Exception as e:
        print(f"❌ Ошибка создания документа: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def process_test_document(document_id: int):
    """Обрабатываем тестовый документ"""
    print(f"\n🔄 Обрабатываем документ ID: {document_id}")
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ {document_id} не найден")
            return False
        
        print(f"📄 Документ: {document.title}")
        print(f"📁 Путь: {document.file_path}")
        
        # Обновляем статус на "processing"
        document.processing_status = "processing"
        document.updated_at = datetime.utcnow()
        db.commit()
        
        # Инициализируем процессор документов
        print("🔧 Инициализируем процессор документов...")
        processor = DocumentProcessor()
        
        # Извлекаем текст
        print("📖 Извлекаем текст из документа...")
        text_content = processor.extract_text(document.file_path)
        if not text_content or not text_content.strip():
            raise Exception("Не удалось извлечь текст из документа")
        
        print(f"✅ Текст извлечен: {len(text_content)} символов")
        
        # Разбиваем на чанки с УЛУЧШЕННЫМ алгоритмом
        print("✂️ Разбиваем текст на чанки (улучшенный алгоритм)...")
        chunks = processor.split_into_chunks(text_content, chunk_size=500, overlap=100)
        if not chunks:
            raise Exception("Не удалось разбить документ на чанки")
        
        print(f"✅ Документ разбит на {len(chunks)} качественных чанков")
        
        # Анализируем размеры чанков
        chunk_sizes = [len(chunk) for chunk in chunks]
        print(f"📊 Статистика чанков:")
        print(f"   Минимальный размер: {min(chunk_sizes)} символов")
        print(f"   Максимальный размер: {max(chunk_sizes)} символов")
        print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        
        # Показываем примеры чанков
        print(f"\n📋 Примеры чанков:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Чанк {i+1} ({len(chunk)} символов) ---")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        # Инициализируем сервис эмбеддингов
        print("\n🧠 Инициализируем сервис эмбеддингов...")
        embedding_service = EmbeddingService()
        
        # Создаем чанки в базе данных
        print("💾 Создаем чанки в базе данных...")
        from shared.models import DocumentChunk
        
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
        
        print(f"\n🎉 Документ {document_id} успешно обработан!")
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
        except Exception as db_error:
            print(f"❌ Ошибка обновления статуса: {str(db_error)}")
        
        return False
        
    finally:
        db.close()

def verify_results(document_id: int):
    """Проверяем результаты обработки"""
    print(f"\n🔍 Проверяем результаты обработки документа {document_id}...")
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ {document_id} не найден")
            return False
        
        print(f"📄 Документ: {document.title}")
        print(f"📊 Статус: {document.processing_status}")
        print(f"📈 Количество чанков: {document.chunks_count or 0}")
        
        # Получаем чанки
        from shared.models import DocumentChunk
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        
        if chunks:
            chunk_sizes = [chunk.content_length for chunk in chunks]
            print(f"\n📊 Статистика чанков из базы данных:")
            print(f"   Количество: {len(chunks)}")
            print(f"   Минимальный размер: {min(chunk_sizes)} символов")
            print(f"   Максимальный размер: {max(chunk_sizes)} символов")
            print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
            
            # Проверяем эмбеддинги
            embeddings_count = sum(1 for chunk in chunks if chunk.embedding is not None)
            print(f"   Чанков с эмбеддингами: {embeddings_count}/{len(chunks)}")
            
            if embeddings_count > 0:
                # Проверяем размерность эмбеддингов
                first_embedding = next(chunk.embedding for chunk in chunks if chunk.embedding is not None)
                print(f"   Размерность эмбеддингов: {len(first_embedding)}")
        
        return document.processing_status == "completed" and document.chunks_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки результатов: {e}")
        return False
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Прямое тестирование загрузки и обработки документа\n")
    
    # Создаем тестовый документ
    document_id = create_test_document()
    if not document_id:
        print("❌ Не удалось создать тестовый документ")
        return False
    
    # Обрабатываем документ
    processing_success = process_test_document(document_id)
    if not processing_success:
        print("❌ Не удалось обработать документ")
        return False
    
    # Проверяем результаты
    verification_success = verify_results(document_id)
    if not verification_success:
        print("❌ Проверка результатов не пройдена")
        return False
    
    print("\n🎉 Тест успешно завершен!")
    print("✅ Документ загружен, обработан и проверен с улучшенным алгоритмом чанкинга")
    print("✅ Админ-панель готова к работе с новым алгоритмом")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 