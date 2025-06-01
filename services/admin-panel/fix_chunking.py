#!/usr/bin/env python3
"""
Скрипт для исправления разбиения документов на чанки
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
from shared.models import Document, DocumentChunk
from shared.utils.document_processor import DocumentProcessor
from shared.utils.embeddings import EmbeddingService
from datetime import datetime

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def analyze_current_chunks():
    """Анализируем текущие чанки"""
    print("📊 Анализ текущих чанков...\n")
    
    db = SessionLocal()
    try:
        chunks = db.query(DocumentChunk).all()
        
        if not chunks:
            print("❌ Чанков в базе нет")
            return
        
        # Статистика по размерам
        sizes = [chunk.content_length for chunk in chunks]
        sizes.sort()
        
        print(f"📈 Статистика по размерам чанков:")
        print(f"   Всего чанков: {len(sizes)}")
        print(f"   Минимальный размер: {min(sizes)} символов")
        print(f"   Максимальный размер: {max(sizes)} символов")
        print(f"   Средний размер: {sum(sizes) // len(sizes)} символов")
        print(f"   Медианный размер: {sizes[len(sizes)//2]} символов")
        
        # Распределение по размерам
        small = len([s for s in sizes if s < 100])
        medium = len([s for s in sizes if 100 <= s < 500])
        large = len([s for s in sizes if s >= 500])
        
        print(f"\n📊 Распределение по размерам:")
        print(f"   Маленькие (<100 символов): {small} ({small/len(sizes)*100:.1f}%)")
        print(f"   Средние (100-500 символов): {medium} ({medium/len(sizes)*100:.1f}%)")
        print(f"   Большие (>=500 символов): {large} ({large/len(sizes)*100:.1f}%)")
        
        # Примеры маленьких чанков
        small_chunks = [chunk for chunk in chunks if chunk.content_length < 50][:5]
        if small_chunks:
            print(f"\n🔍 Примеры маленьких чанков:")
            for chunk in small_chunks:
                print(f"   Чанк {chunk.chunk_index}: {chunk.content_length} символов - '{chunk.content}'")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
    finally:
        db.close()

def recreate_chunks_for_document(document_id: int, chunk_size: int = 1000, overlap: int = 200):
    """Пересоздаем чанки для документа с новыми параметрами"""
    print(f"\n🔄 Пересоздание чанков для документа {document_id}...")
    print(f"   Размер чанка: {chunk_size} символов")
    print(f"   Перекрытие: {overlap} символов")
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ {document_id} не найден")
            return False
        
        print(f"📄 Документ: {document.original_filename}")
        
        # Удаляем старые чанки
        old_chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
        print(f"🗑️ Удаляем {old_chunks_count} старых чанков...")
        
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
        chunks = processor.split_into_chunks(text_content, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            print("❌ Не удалось разбить документ на чанки")
            return False
        
        print(f"✅ Создано {len(chunks)} новых чанков")
        
        # Анализируем новые чанки
        new_sizes = [len(chunk) for chunk in chunks]
        print(f"📊 Статистика новых чанков:")
        print(f"   Минимальный размер: {min(new_sizes)} символов")
        print(f"   Максимальный размер: {max(new_sizes)} символов")
        print(f"   Средний размер: {sum(new_sizes) // len(new_sizes)} символов")
        
        # Инициализируем сервис эмбеддингов
        print("🧠 Создаем эмбеддинги...")
        embedding_service = EmbeddingService()
        
        # Создаем чанки в базе данных
        created_chunks = []
        for i, chunk_text in enumerate(chunks):
            try:
                print(f"   Обрабатываем чанк {i+1}/{len(chunks)}...", end='\r')
                
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
                
                # Сохраняем каждые 50 чанков
                if (i + 1) % 50 == 0:
                    db.commit()
                    print(f"   Сохранено {i+1} чанков...")
                
            except Exception as e:
                print(f"\n❌ Ошибка создания чанка {i}: {str(e)}")
                continue
        
        # Финальное сохранение
        db.commit()
        print(f"\n✅ Создано {len(created_chunks)} чанков с эмбеддингами")
        
        # Обновляем статус документа
        document.chunks_count = len(created_chunks)
        document.updated_at = datetime.utcnow()
        db.commit()
        
        print(f"🎉 Документ успешно переобработан!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка пересоздания чанков: {e}")
        return False
    finally:
        db.close()

def test_new_search():
    """Тестируем поиск с новыми чанками"""
    print("\n🔍 Тестируем поиск с новыми чанками...\n")
    
    db = SessionLocal()
    try:
        # Инициализируем сервис эмбеддингов
        embedding_service = EmbeddingService()
        
        test_queries = [
            "оплата труда",
            "заработная плата", 
            "трудовой договор",
            "отпуск",
            "премия"
        ]
        
        for query in test_queries:
            print(f"🔍 Поиск: '{query}'")
            
            # Создаем эмбеддинг для запроса
            query_embedding = embedding_service.get_embedding(query)
            if not query_embedding:
                print("❌ Не удалось создать эмбеддинг для запроса")
                continue
            
            # Получаем все чанки с эмбеддингами
            chunks = db.query(DocumentChunk).filter(DocumentChunk.embedding.isnot(None)).all()
            
            if not chunks:
                print("❌ Нет чанков с эмбеддингами")
                continue
            
            # Вычисляем схожесть для каждого чанка
            similarities = []
            for chunk in chunks:
                try:
                    similarity = embedding_service.calculate_similarity(query_embedding, chunk.embedding)
                    similarities.append((chunk, similarity))
                except Exception as e:
                    continue
            
            # Сортируем по убыванию схожести
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Показываем топ-3 результата
            for i, (chunk, similarity) in enumerate(similarities[:3]):
                document = db.query(Document).filter(Document.id == chunk.document_id).first()
                
                print(f"   #{i+1} Сходство: {similarity:.3f}")
                print(f"      📄 Документ: {document.original_filename if document else f'ID {chunk.document_id}'}")
                print(f"      🧩 Чанк {chunk.chunk_index}: {len(chunk.content)} символов")
                print(f"      📝 Текст: {chunk.content[:150]}...")
            
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка тестирования поиска: {e}")
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 ИСПРАВЛЕНИЕ РАЗБИЕНИЯ ДОКУМЕНТОВ НА ЧАНКИ\n")
    
    # Анализируем текущие чанки
    analyze_current_chunks()
    
    # Спрашиваем подтверждение
    print("\n" + "="*60)
    print("⚠️ ВНИМАНИЕ: Будут удалены все существующие чанки и созданы новые!")
    print("Это может занять несколько минут.")
    
    response = input("\nПродолжить? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Операция отменена")
        return
    
    # Пересоздаем чанки для документа ID=1
    success = recreate_chunks_for_document(
        document_id=1,
        chunk_size=1000,  # Увеличиваем размер чанка
        overlap=200       # Уменьшаем перекрытие
    )
    
    if success:
        # Тестируем новый поиск
        test_new_search()
        
        print("\n" + "="*60)
        print("🎉 ЧАНКИ УСПЕШНО ПЕРЕСОЗДАНЫ!")
        print("✅ Теперь поиск должен работать намного лучше")
        print("✅ Чанки имеют оптимальный размер для семантического поиска")
    else:
        print("\n❌ Не удалось пересоздать чанки")

if __name__ == "__main__":
    main() 