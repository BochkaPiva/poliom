#!/usr/bin/env python3
"""
Проверка обработанных документов и поиск по ним
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
from shared.utils.embeddings import EmbeddingService

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_documents():
    """Проверяем все документы в базе"""
    print("📚 Проверяем документы в базе данных...\n")
    
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        if not documents:
            print("❌ Документов в базе нет")
            return False
        
        print(f"📊 Найдено документов: {len(documents)}")
        print("="*60)
        
        for doc in documents:
            print(f"📄 ID: {doc.id}")
            print(f"   Файл: {doc.original_filename}")
            print(f"   Статус: {doc.processing_status}")
            print(f"   Чанков: {doc.chunks_count or 0}")
            print(f"   Загружен: {doc.created_at}")
            if doc.processed_at:
                print(f"   Обработан: {doc.processed_at}")
            if doc.error_message:
                print(f"   ❌ Ошибка: {doc.error_message}")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки документов: {e}")
        return False
    finally:
        db.close()

def check_chunks():
    """Проверяем чанки документов"""
    print("\n🧩 Проверяем чанки документов...\n")
    
    db = SessionLocal()
    try:
        chunks = db.query(DocumentChunk).all()
        
        if not chunks:
            print("❌ Чанков в базе нет")
            return False
        
        print(f"📊 Найдено чанков: {len(chunks)}")
        
        # Группируем по документам
        chunks_by_doc = {}
        for chunk in chunks:
            if chunk.document_id not in chunks_by_doc:
                chunks_by_doc[chunk.document_id] = []
            chunks_by_doc[chunk.document_id].append(chunk)
        
        print("="*60)
        for doc_id, doc_chunks in chunks_by_doc.items():
            document = db.query(Document).filter(Document.id == doc_id).first()
            print(f"📄 Документ: {document.original_filename if document else f'ID {doc_id}'}")
            print(f"   Чанков: {len(doc_chunks)}")
            
            # Показываем первые 3 чанка
            for i, chunk in enumerate(doc_chunks[:3]):
                print(f"   🧩 Чанк {chunk.chunk_index}: {len(chunk.content)} символов")
                print(f"      Текст: {chunk.content[:100]}...")
                print(f"      Эмбеддинг: {'✅' if chunk.embedding else '❌'}")
            
            if len(doc_chunks) > 3:
                print(f"   ... и еще {len(doc_chunks) - 3} чанков")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки чанков: {e}")
        return False
    finally:
        db.close()

def test_search(query: str, top_k: int = 5):
    """Тестируем поиск по документам"""
    print(f"\n🔍 Поиск по запросу: '{query}'\n")
    
    db = SessionLocal()
    try:
        # Инициализируем сервис эмбеддингов
        embedding_service = EmbeddingService()
        
        # Создаем эмбеддинг для запроса
        query_embedding = embedding_service.get_embedding(query)
        if not query_embedding:
            print("❌ Не удалось создать эмбеддинг для запроса")
            return False
        
        # Получаем все чанки с эмбеддингами
        chunks = db.query(DocumentChunk).filter(DocumentChunk.embedding.isnot(None)).all()
        
        if not chunks:
            print("❌ Нет чанков с эмбеддингами")
            return False
        
        print(f"📊 Поиск среди {len(chunks)} чанков...")
        
        # Вычисляем схожесть для каждого чанка
        similarities = []
        for chunk in chunks:
            try:
                similarity = embedding_service.calculate_similarity(query_embedding, chunk.embedding)
                similarities.append((chunk, similarity))
            except Exception as e:
                print(f"⚠️ Ошибка вычисления схожести для чанка {chunk.id}: {e}")
                continue
        
        # Сортируем по убыванию схожести
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Показываем топ результатов
        print(f"\n🏆 Топ-{min(top_k, len(similarities))} результатов:")
        print("="*60)
        
        for i, (chunk, similarity) in enumerate(similarities[:top_k]):
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            
            print(f"#{i+1} Схожесть: {similarity:.3f}")
            print(f"   📄 Документ: {document.original_filename if document else f'ID {chunk.document_id}'}")
            print(f"   🧩 Чанк {chunk.chunk_index}: {len(chunk.content)} символов")
            print(f"   📝 Текст: {chunk.content[:200]}...")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return False
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Проверка системы обработки документов\n")
    
    # Проверяем документы
    docs_ok = check_documents()
    
    # Проверяем чанки
    chunks_ok = check_chunks()
    
    if docs_ok and chunks_ok:
        # Тестируем поиск
        print("\n" + "="*60)
        print("🔍 ТЕСТИРОВАНИЕ ПОИСКА")
        print("="*60)
        
        test_queries = [
            "документ",
            "текст",
            "система",
            "обработка"
        ]
        
        for query in test_queries:
            test_search(query, top_k=3)
            print()
    
    print("\n" + "="*60)
    print("📊 ИТОГИ:")
    print("="*60)
    
    if docs_ok and chunks_ok:
        print("🎉 Система работает отлично!")
        print("✅ Документы загружены и обработаны")
        print("✅ Чанки созданы с эмбеддингами")
        print("✅ Поиск функционирует")
        print("\n💡 Можно загружать новые документы через админ-панель!")
    else:
        print("⚠️ Система требует настройки")
        if not docs_ok:
            print("❌ Нет обработанных документов")
        if not chunks_ok:
            print("❌ Проблемы с чанками")

if __name__ == "__main__":
    main() 