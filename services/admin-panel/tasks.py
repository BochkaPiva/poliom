"""
Celery задачи для обработки документов
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from celery import Celery
from sqlalchemy.orm import sessionmaker

# Импортируем shared модули
from shared.models.database import engine
from shared.models import Document, DocumentChunk
from shared.utils.document_processor import DocumentProcessor
from shared.utils.text_processing import chunk_text
from shared.utils.embeddings import EmbeddingService

# Импортируем Celery app
from celery_app import app

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.task(bind=True)
def process_document(self, document_id: int):
    """
    Обработка документа: извлечение текста, создание чанков и эмбеддингов
    """
    db = SessionLocal()
    
    try:
        # Получаем документ из базы данных
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Документ {document_id} не найден")
            return {"status": "error", "message": "Документ не найден"}
        
        # Обновляем статус на "processing"
        document.processing_status = "processing"
        document.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Начинаем обработку документа {document_id}: {document.original_filename}")
        
        # Инициализируем процессор документов
        processor = DocumentProcessor()
        
        # Извлекаем текст из документа
        text_content = processor.extract_text(document.file_path)
        if not text_content or not text_content.strip():
            raise Exception("Не удалось извлечь текст из документа")
        
        # Разбиваем текст на чанки
        chunks = processor.split_into_chunks(text_content)
        if not chunks:
            raise Exception("Не удалось разбить документ на чанки")
        
        logger.info(f"Документ разбит на {len(chunks)} чанков")
        
        # Инициализируем сервис эмбеддингов
        embedding_service = EmbeddingService()
        
        # Создаем чанки в базе данных
        created_chunks = []
        for i, chunk_text in enumerate(chunks):
            try:
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
                logger.error(f"Ошибка создания чанка {i} для документа {document_id}: {str(e)}")
                continue
        
        if not created_chunks:
            raise Exception("Не удалось создать ни одного чанка")
        
        # Сохраняем все чанки
        db.commit()
        
        # Обновляем статус документа на "completed"
        document.processing_status = "completed"
        document.processed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        document.chunks_count = len(created_chunks)
        db.commit()
        
        logger.info(f"Документ {document_id} успешно обработан. Создано {len(created_chunks)} чанков")
        
        return {
            "status": "completed",
            "document_id": document_id,
            "chunks_created": len(created_chunks),
            "message": "Документ успешно обработан"
        }
        
    except Exception as e:
        logger.error(f"Ошибка обработки документа {document_id}: {str(e)}")
        
        # Обновляем статус документа на "failed"
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "failed"
                document.error_message = str(e)
                document.updated_at = datetime.utcnow()
                db.commit()
        except Exception as db_error:
            logger.error(f"Ошибка обновления статуса документа {document_id}: {str(db_error)}")
        
        return {
            "status": "failed",
            "document_id": document_id,
            "error": str(e)
        }
        
    finally:
        db.close()


@app.task
def cleanup_failed_documents():
    """
    Периодическая задача для очистки неудачно обработанных документов
    """
    db = SessionLocal()
    
    try:
        # Находим документы со статусом "failed" старше 24 часов
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        failed_documents = db.query(Document).filter(
            Document.processing_status == "failed",
            Document.updated_at < cutoff_time
        ).all()
        
        cleaned_count = 0
        for document in failed_documents:
            try:
                # Удаляем файл с диска
                file_path = Path(document.file_path)
                if file_path.exists():
                    file_path.unlink()
                
                # Удаляем документ из базы данных
                db.delete(document)
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"Ошибка очистки документа {document.id}: {str(e)}")
                continue
        
        db.commit()
        logger.info(f"Очищено {cleaned_count} неудачно обработанных документов")
        
        return {"cleaned_documents": cleaned_count}
        
    except Exception as e:
        logger.error(f"Ошибка очистки неудачных документов: {str(e)}")
        return {"error": str(e)}
        
    finally:
        db.close() 