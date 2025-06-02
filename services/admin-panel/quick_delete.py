#!/usr/bin/env python3
"""
Быстрое удаление документа без загрузки эмбеддингов
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Загружаем переменные окружения
current_dir = Path(__file__).parent
load_dotenv(current_dir / '.env.local')

# Создаем подключение к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def quick_delete_document(document_id):
    """Быстро удаляет документ через SQL"""
    with engine.connect() as conn:
        # Начинаем транзакцию
        trans = conn.begin()
        try:
            # Получаем информацию о документе
            doc_result = conn.execute(
                text("SELECT title, file_path FROM documents WHERE id = :doc_id"),
                {"doc_id": document_id}
            )
            doc_info = doc_result.fetchone()
            
            if not doc_info:
                print(f"❌ Документ с ID {document_id} не найден")
                return False
            
            title, file_path = doc_info
            print(f"📄 Найден документ: {title}")
            print(f"   Путь к файлу: {file_path}")
            
            # Удаляем чанки
            chunks_result = conn.execute(
                text("DELETE FROM document_chunks WHERE document_id = :doc_id"),
                {"doc_id": document_id}
            )
            deleted_chunks = chunks_result.rowcount
            print(f"✅ Удалено чанков: {deleted_chunks}")
            
            # Удаляем документ
            doc_delete_result = conn.execute(
                text("DELETE FROM documents WHERE id = :doc_id"),
                {"doc_id": document_id}
            )
            
            if doc_delete_result.rowcount > 0:
                # Удаляем файл с диска
                try:
                    file_path_obj = Path(file_path)
                    if file_path_obj.exists():
                        file_path_obj.unlink()
                        print(f"✅ Файл удален: {file_path}")
                    else:
                        print(f"⚠️  Файл не найден: {file_path}")
                except Exception as e:
                    print(f"⚠️  Ошибка удаления файла: {e}")
                
                # Подтверждаем транзакцию
                trans.commit()
                print(f"🎉 Документ {document_id} успешно удален!")
                return True
            else:
                print(f"❌ Не удалось удалить документ {document_id}")
                trans.rollback()
                return False
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            trans.rollback()
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python quick_delete.py <document_id>")
        sys.exit(1)
    
    try:
        document_id = int(sys.argv[1])
        quick_delete_document(document_id)
    except ValueError:
        print("❌ Неверный ID документа")
        sys.exit(1) 