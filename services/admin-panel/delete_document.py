#!/usr/bin/env python3
"""
Утилита для безопасного удаления документов из системы.
Удаляет документ, все его чанки и файл с диска.

Использование:
    python delete_document.py <document_id>
    python delete_document.py --list  # показать все документы
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Добавляем путь к shared модулям
current_dir = Path(__file__).parent
services_dir = current_dir.parent
sys.path.append(str(services_dir))

# Загружаем переменные окружения
load_dotenv(current_dir / '.env.local')

from shared.models.document import Document, DocumentChunk
from shared.models.database import SessionLocal

def list_documents():
    """Показывает список всех документов"""
    db = SessionLocal()
    try:
        documents = db.query(Document).order_by(Document.id).all()
        
        if not documents:
            print("📄 Документы не найдены")
            return
        
        print("📄 Список документов:")
        print("-" * 80)
        print(f"{'ID':<4} {'Название':<30} {'Статус':<12} {'Чанков':<8} {'Размер':<10}")
        print("-" * 80)
        
        for doc in documents:
            chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
            size_mb = doc.file_size / (1024 * 1024) if doc.file_size else 0
            
            print(f"{doc.id:<4} {doc.title[:29]:<30} {doc.processing_status:<12} {chunks_count:<8} {size_mb:.1f}MB")
        
        print("-" * 80)
        print(f"Всего документов: {len(documents)}")
        
    except Exception as e:
        print(f"❌ Ошибка получения списка документов: {e}")
    finally:
        db.close()

def delete_document_safe(document_id):
    """Безопасно удаляет документ и все связанные данные"""
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ с ID {document_id} не найден")
            return False
        
        print(f"📄 Найден документ: {document.title}")
        print(f"   Файл: {document.original_filename}")
        print(f"   Статус: {document.processing_status}")
        print(f"   Путь: {document.file_path}")
        
        # Подсчитываем чанки
        chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
        print(f"   Чанков: {chunks_count}")
        
        # Подтверждение
        confirm = input(f"\n⚠️  Вы уверены, что хотите удалить документ '{document.title}'? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Удаление отменено")
            return False
        
        print("\n🗑️  Начинаю удаление...")
        
        # 1. Удаляем чанки через SQL (избегаем проблем с эмбеддингами)
        try:
            result = db.execute(text("DELETE FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": document_id})
            deleted_chunks = result.rowcount
            print(f"✅ Удалено чанков: {deleted_chunks}")
        except Exception as e:
            print(f"⚠️  Ошибка удаления чанков: {e}")
        
        # 2. Удаляем файл с диска
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                print(f"✅ Файл удален: {document.file_path}")
            else:
                print(f"⚠️  Файл не найден: {document.file_path}")
        except Exception as e:
            print(f"⚠️  Ошибка удаления файла: {e}")
        
        # 3. Удаляем запись документа
        try:
            db.delete(document)
            db.commit()
            print(f"✅ Документ удален из базы данных")
        except Exception as e:
            print(f"❌ Ошибка удаления документа из БД: {e}")
            db.rollback()
            return False
        
        print(f"\n🎉 Документ {document_id} успешно удален!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка удаления документа: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python delete_document.py <document_id>  # удалить документ")
        print("  python delete_document.py --list         # показать все документы")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "--list" or arg == "-l":
        list_documents()
    else:
        try:
            document_id = int(arg)
            delete_document_safe(document_id)
        except ValueError:
            print(f"❌ Неверный ID документа: {arg}")
            sys.exit(1)

if __name__ == "__main__":
    main() 