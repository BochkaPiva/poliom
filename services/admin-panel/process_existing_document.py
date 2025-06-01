#!/usr/bin/env python3
"""
Ручная обработка существующего документа
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
from shared.models import Document
from tasks import process_document

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def process_existing_document(document_id: int):
    """Обрабатываем существующий документ"""
    print(f"🔄 Запускаем обработку документа ID: {document_id}")
    
    db = SessionLocal()
    try:
        # Проверяем, что документ существует
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ с ID {document_id} не найден")
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
        
        # Отправляем задачу на обработку
        print("📤 Отправляем задачу в Celery...")
        result = process_document.delay(document_id)
        
        print(f"✅ Задача отправлена: {result.id}")
        print("⏳ Ждем результат обработки...")
        
        # Ждем результат (максимум 60 секунд)
        try:
            task_result = result.get(timeout=60)
            print(f"🎉 Обработка завершена!")
            print(f"📋 Результат: {task_result}")
            
            if isinstance(task_result, dict):
                if task_result.get('status') == 'completed':
                    print(f"✅ Создано чанков: {task_result.get('chunks_created', 0)}")
                    return True
                else:
                    print(f"❌ Ошибка: {task_result.get('error', 'Неизвестная ошибка')}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка выполнения задачи: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()

def list_documents():
    """Показываем все документы"""
    print("📚 Документы в базе данных:\n")
    
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        if not documents:
            print("❌ Документов в базе нет")
            return []
        
        for doc in documents:
            print(f"📄 ID: {doc.id}")
            print(f"   Файл: {doc.original_filename}")
            print(f"   Статус: {doc.processing_status}")
            print(f"   Чанков: {doc.chunks_count or 0}")
            print(f"   Путь: {doc.file_path}")
            print("-" * 40)
        
        return documents
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Обработка существующих документов\n")
    
    # Показываем все документы
    documents = list_documents()
    
    if not documents:
        print("💡 Загрузите документы через админ-панель")
        return
    
    # Обрабатываем документы со статусом 'uploaded'
    unprocessed = [doc for doc in documents if doc.processing_status == 'uploaded']
    
    if not unprocessed:
        print("✅ Все документы уже обработаны")
        return
    
    print(f"\n🔄 Найдено необработанных документов: {len(unprocessed)}")
    
    for doc in unprocessed:
        print(f"\n{'='*50}")
        success = process_existing_document(doc.id)
        
        if success:
            print("✅ Документ успешно обработан")
        else:
            print("❌ Ошибка обработки документа")

if __name__ == "__main__":
    main() 