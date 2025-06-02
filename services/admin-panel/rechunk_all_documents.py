#!/usr/bin/env python3
"""
Скрипт для пересоздания всех чанков с новыми параметрами
Размер чанка: 1500 символов (вместо старых 1000)
Перекрытие: 200 символов
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Добавляем путь к shared модулям
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "shared"))

from shared.models.database import SessionLocal
from shared.models.document import Document, DocumentChunk
from shared.utils.document_processor import DocumentProcessor
from shared.utils.embeddings import EmbeddingService
from sqlalchemy import text


def improved_split_into_chunks(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
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


def rechunk_document(document_id: int, chunk_size: int = 1500, overlap: int = 200):
    """Пересоздаем чанки для одного документа"""
    print(f"\n🔄 Пересоздание чанков для документа {document_id}...")
    print(f"   📏 Размер чанка: {chunk_size} символов")
    print(f"   🔗 Перекрытие: {overlap} символов")
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ {document_id} не найден")
            return False
        
        print(f"📄 Документ: {document.original_filename}")
        
        # Подсчитываем старые чанки
        old_chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
        print(f"🗑️ Удаляем {old_chunks_count} старых чанков...")
        
        # Удаляем старые чанки
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.commit()
        
        # Инициализируем процессор документов
        processor = DocumentProcessor()
        
        # Извлекаем текст из документа
        print("📖 Извлекаем текст из документа...")
        text_content = processor.extract_text(document.file_path)
        if not text_content or not text_content.strip():
            print("❌ Не удалось извлечь текст из документа")
            return False
        
        print(f"✅ Извлечено {len(text_content)} символов текста")
        
        # Разбиваем текст на чанки с новыми параметрами
        print("✂️ Разбиваем текст на чанки...")
        chunks = improved_split_into_chunks(text_content, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            print("❌ Не удалось разбить документ на чанки")
            return False
        
        print(f"✅ Документ разбит на {len(chunks)} чанков")
        
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
                print(f"  📝 Обрабатываем чанк {i+1}/{len(chunks)}...", end='\r')
                
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
                print(f"\n❌ Ошибка создания чанка {i}: {str(e)}")
                continue
        
        # Финальный коммит
        db.commit()
        
        # Обновляем информацию о документе
        document.chunks_count = len(created_chunks)
        document.updated_at = datetime.utcnow()
        document.processing_status = "completed"
        db.commit()
        
        print(f"\n✅ Документ {document_id} успешно обработан:")
        print(f"   📊 Создано чанков: {len(created_chunks)}")
        print(f"   📏 Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        print(f"   🔄 Изменение: {old_chunks_count} → {len(created_chunks)} чанков")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обработки документа {document_id}: {str(e)}")
        try:
            db.rollback()
        except:
            pass
        return False
    finally:
        try:
            db.close()
        except:
            pass


def rechunk_all_documents():
    """Пересоздаем чанки для всех документов"""
    print("🚀 МАССОВОЕ ПЕРЕСОЗДАНИЕ ЧАНКОВ")
    print("=" * 60)
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📏 Новый размер чанков: 1500 символов")
    print(f"🔗 Перекрытие: 200 символов")
    print("=" * 60)
    
    # Создаем отдельную сессию для получения списка документов
    db = SessionLocal()
    try:
        # Получаем все документы
        documents = db.query(Document).all()
        print(f"📄 Найдено документов: {len(documents)}")
        
        if not documents:
            print("❌ Документы не найдены")
            return
        
        # Показываем список документов
        print("\n📋 Список документов:")
        for doc in documents:
            chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
            print(f"   {doc.id}. {doc.original_filename} ({chunks_count} чанков)")
        
        # Сохраняем список ID документов
        document_ids = [doc.id for doc in documents]
        
    except Exception as e:
        print(f"❌ Ошибка получения списка документов: {str(e)}")
        return
    finally:
        db.close()
    
    # Подтверждение
    print(f"\n⚠️ ВНИМАНИЕ: Будут удалены ВСЕ существующие чанки и созданы новые!")
    response = input("Продолжить? (да/нет): ").lower().strip()
    
    if response not in ['да', 'yes', 'y']:
        print("❌ Операция отменена")
        return
    
    # Обрабатываем каждый документ
    success_count = 0
    total_old_chunks = 0
    total_new_chunks = 0
    
    for doc_id in document_ids:
        # Подсчитываем старые чанки перед обработкой
        db_temp = SessionLocal()
        try:
            old_chunks = db_temp.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
            total_old_chunks += old_chunks
        except:
            pass
        finally:
            db_temp.close()
        
        # Обрабатываем документ
        if rechunk_document(doc_id, chunk_size=1500, overlap=200):
            success_count += 1
            
            # Подсчитываем новые чанки после обработки
            db_temp = SessionLocal()
            try:
                new_chunks = db_temp.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
                total_new_chunks += new_chunks
            except:
                pass
            finally:
                db_temp.close()
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   ✅ Успешно обработано: {success_count}/{len(document_ids)} документов")
    print(f"   🔄 Чанков было: {total_old_chunks}")
    print(f"   🔄 Чанков стало: {total_new_chunks}")
    print(f"   📈 Изменение: {total_new_chunks - total_old_chunks:+d} чанков")
    print(f"⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    rechunk_all_documents() 