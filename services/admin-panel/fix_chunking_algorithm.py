#!/usr/bin/env python3
"""
Исправление алгоритма чанкинга
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from shared.models.database import SessionLocal
from shared.models.document import DocumentChunk, Document
from shared.utils.embeddings import EmbeddingService

def improved_split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    ИСПРАВЛЕННЫЙ алгоритм разбиения текста на чанки
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

def test_improved_chunking():
    """Тестируем улучшенный алгоритм чанкинга"""
    print("🧪 ТЕСТИРОВАНИЕ УЛУЧШЕННОГО АЛГОРИТМА ЧАНКИНГА\n")
    
    # Тестовый текст
    test_text = """
    Это первое предложение документа. Оно содержит важную информацию о системе оплаты труда.
    
    Второй абзац рассказывает о структуре заработной платы. Здесь описываются основные принципы расчета.
    
    Третий раздел посвящен премиальным выплатам. В нем указаны условия получения премий и надбавок.
    
    Четвертая часть содержит информацию об отпусках. Описывается порядок предоставления и оплаты отпусков.
    
    Заключительный раздел включает дополнительные положения. Здесь указаны особые случаи и исключения.
    """ * 5  # Повторяем 5 раз для получения длинного текста
    
    print(f"📄 Исходный текст: {len(test_text)} символов")
    
    # Тестируем старый алгоритм (для сравнения)
    print("\n🔴 СТАРЫЙ алгоритм:")
    old_chunks = old_split_into_chunks(test_text, chunk_size=300, overlap=50)
    print(f"   Создано чанков: {len(old_chunks)}")
    for i, chunk in enumerate(old_chunks[:3]):
        print(f"   Чанк {i+1}: {len(chunk)} символов - '{chunk[:50]}...'")
    
    # Тестируем новый алгоритм
    print("\n🟢 НОВЫЙ алгоритм:")
    new_chunks = improved_split_into_chunks(test_text, chunk_size=300, overlap=50)
    print(f"   Создано чанков: {len(new_chunks)}")
    for i, chunk in enumerate(new_chunks[:3]):
        print(f"   Чанк {i+1}: {len(chunk)} символов - '{chunk[:50]}...'")

def old_split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Старый алгоритм для сравнения"""
    if not text or not text.strip():
        return []
    
    chunks = []
    text = text.strip()
    
    if len(text) <= chunk_size:
        return [text]
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        
        if end < len(text):
            for separator in ['. ', '\n', ' ']:
                sep_pos = text.rfind(separator, start, end)
                if sep_pos != -1:
                    end = sep_pos + len(separator)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = max(start + 1, end - overlap)  # ЭТО ПРОБЛЕМА!
    
    return chunks

def recreate_chunks_with_improved_algorithm(document_id: int = 1):
    """Пересоздаем чанки с улучшенным алгоритмом"""
    print(f"\n🔄 ПЕРЕСОЗДАНИЕ ЧАНКОВ С УЛУЧШЕННЫМ АЛГОРИТМОМ")
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ {document_id} не найден")
            return False
        
        print(f"\n📄 Документ: {document.original_filename}")
        print(f"📁 Путь к файлу: {document.file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(document.file_path):
            print(f"❌ Файл не найден: {document.file_path}")
            return False
        
        # Инициализируем процессор документов
        from shared.utils.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Извлекаем текст из файла
        print("📖 Извлекаем текст из файла...")
        try:
            text_content = processor.extract_text(document.file_path)
            if not text_content or not text_content.strip():
                print("❌ Не удалось извлечь текст из документа")
                return False
        except Exception as e:
            print(f"❌ Ошибка извлечения текста: {e}")
            return False
        
        print(f"✅ Извлечено {len(text_content)} символов текста")
        
        # Сохраняем извлеченный текст в поле content документа
        document.content = text_content
        
        # Анализируем старые чанки
        old_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        print(f"🗑️ Найдено {len(old_chunks)} старых чанков")
        
        # Удаляем старые чанки
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.commit()
        print("✅ Старые чанки удалены")
        
        # Создаем новые чанки с улучшенным алгоритмом
        print("✂️ Создаем новые чанки...")
        new_chunks = improved_split_into_chunks(text_content, chunk_size=1000, overlap=200)
        print(f"✅ Создано {len(new_chunks)} новых чанков")
        
        # Инициализируем сервис эмбеддингов
        from shared.utils.embeddings import EmbeddingService
        embedding_service = EmbeddingService()
        
        # Сохраняем новые чанки в базу данных
        print("💾 Сохраняем чанки в базу данных...")
        for i, chunk_text in enumerate(new_chunks):
            print(f"   Обрабатываем чанк {i+1}/{len(new_chunks)}...", end='\r')
            
            # Создаем эмбеддинг для чанка
            embedding = embedding_service.create_embedding(chunk_text)
            
            # Создаем объект чанка
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk_text,
                content_length=len(chunk_text),
                embedding=embedding,
                created_at=datetime.utcnow()
            )
            
            db.add(chunk)
            
            # Сохраняем каждые 50 чанков
            if (i + 1) % 50 == 0:
                db.commit()
                print(f"   Сохранено {i+1} чанков...")
        
        # Обновляем количество чанков в документе
        document.chunks_count = len(new_chunks)
        document.updated_at = datetime.utcnow()
        document.processing_status = "completed"
        
        db.commit()
        print(f"\n✅ Сохранено {len(new_chunks)} чанков с эмбеддингами")
        
        # Анализируем размеры новых чанков
        print("\n📊 АНАЛИЗ НОВЫХ ЧАНКОВ:")
        chunk_sizes = [len(chunk) for chunk in new_chunks]
        print(f"   Минимальный размер: {min(chunk_sizes)} символов")
        print(f"   Максимальный размер: {max(chunk_sizes)} символов")
        print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        print(f"   Медианный размер: {sorted(chunk_sizes)[len(chunk_sizes)//2]} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 ИСПРАВЛЕНИЕ АЛГОРИТМА ЧАНКИНГА\n")
    
    # Тестируем алгоритм
    test_improved_chunking()
    
    # Спрашиваем подтверждение
    print("\n" + "="*60)
    print("⚠️ ВНИМАНИЕ: Будут пересозданы все чанки с новым алгоритмом!")
    
    response = input("\nПродолжить? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Операция отменена")
        return
    
    # Пересоздаем чанки
    success = recreate_chunks_with_improved_algorithm()
    
    if success:
        print("\n" + "="*60)
        print("🎉 АЛГОРИТМ ЧАНКИНГА ИСПРАВЛЕН!")
        print("✅ Теперь чанки должны быть качественными")
        print("✅ Поиск будет работать намного лучше")
    else:
        print("\n❌ Не удалось исправить чанкинг")

if __name__ == "__main__":
    main() 