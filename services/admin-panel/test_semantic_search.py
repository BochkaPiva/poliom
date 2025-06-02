#!/usr/bin/env python3
"""
Тест семантического поиска с обходом проблемы эмбеддингов
"""

import os
import sys
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from sentence_transformers import SentenceTransformer

# Загружаем переменные окружения
current_dir = Path(__file__).parent
load_dotenv(current_dir / '.env.local')

# Создаем подключение к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def load_embedding_model():
    """Загружаем модель эмбеддингов"""
    print("🤖 Загружаем модель эмбеддингов...")
    model = SentenceTransformer('cointegrated/rubert-tiny2')
    print("✅ Модель загружена!")
    return model

def text_search(query, limit=5):
    """Простой текстовый поиск по содержимому"""
    print(f"🔍 Текстовый поиск: '{query}'")
    print("-" * 60)
    
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT 
                    dc.document_id,
                    d.title,
                    dc.chunk_index,
                    dc.content,
                    dc.content_length
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE LOWER(dc.content) LIKE LOWER(:query)
                ORDER BY dc.document_id, dc.chunk_index
                LIMIT :limit
            """),
            {"query": f"%{query}%", "limit": limit}
        )
        
        results = result.fetchall()
        
        if not results:
            print("❌ Ничего не найдено")
            return []
        
        print(f"✅ Найдено {len(results)} результатов:")
        print()
        
        for i, (doc_id, title, chunk_idx, content, length) in enumerate(results, 1):
            # Находим позицию ключевого слова для контекста
            query_lower = query.lower()
            content_lower = content.lower()
            pos = content_lower.find(query_lower)
            
            if pos != -1:
                # Показываем контекст вокруг найденного слова
                start = max(0, pos - 100)
                end = min(len(content), pos + len(query) + 100)
                context = content[start:end]
                if start > 0:
                    context = "..." + context
                if end < len(content):
                    context = context + "..."
            else:
                context = content[:200] + "..."
            
            print(f"{i}. Документ: {title} (ID: {doc_id})")
            print(f"   Чанк: {chunk_idx}, Длина: {length}")
            print(f"   Контекст: {context}")
            print()
        
        return results

def semantic_search_simulation(query, model, limit=5):
    """Симуляция семантического поиска без чтения эмбеддингов из БД"""
    print(f"🧠 Семантический поиск (симуляция): '{query}'")
    print("-" * 60)
    
    # Создаем эмбеддинг для запроса
    query_embedding = model.encode([query])[0]
    print(f"✅ Создан эмбеддинг запроса (размерность: {len(query_embedding)})")
    
    with engine.connect() as conn:
        # Получаем все чанки без эмбеддингов
        result = conn.execute(
            text("""
                SELECT 
                    dc.document_id,
                    d.title,
                    dc.chunk_index,
                    dc.content,
                    dc.content_length
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.processing_status = 'completed'
                ORDER BY dc.document_id, dc.chunk_index
            """)
        )
        
        chunks = result.fetchall()
        print(f"📊 Обрабатываем {len(chunks)} чанков...")
        
        # Создаем эмбеддинги для всех чанков (в реальности они уже есть в БД)
        chunk_texts = [chunk[3] for chunk in chunks]  # content
        chunk_embeddings = model.encode(chunk_texts)
        
        # Вычисляем косинусное сходство
        similarities = []
        for i, chunk_emb in enumerate(chunk_embeddings):
            similarity = np.dot(query_embedding, chunk_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_emb)
            )
            similarities.append((similarity, chunks[i]))
        
        # Сортируем по убыванию сходства
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        print(f"✅ Найдены наиболее релевантные результаты:")
        print()
        
        for i, (similarity, (doc_id, title, chunk_idx, content, length)) in enumerate(similarities[:limit], 1):
            preview = content[:300] + "..." if len(content) > 300 else content
            
            print(f"{i}. Сходство: {similarity:.4f}")
            print(f"   Документ: {title} (ID: {doc_id})")
            print(f"   Чанк: {chunk_idx}, Длина: {length}")
            print(f"   Содержимое: {preview}")
            print()
        
        return similarities[:limit]

def test_search_queries():
    """Тестируем различные поисковые запросы"""
    print("🎯 ТЕСТИРОВАНИЕ ПОИСКОВЫХ ЗАПРОСОВ")
    print("=" * 60)
    
    # Загружаем модель
    model = load_embedding_model()
    print()
    
    # Тестовые запросы
    queries = [
        "премирование работников",
        "размер премии",
        "условия выплаты",
        "отчетный период",
        "грейд должности"
    ]
    
    for query in queries:
        print("=" * 60)
        
        # Текстовый поиск
        text_results = text_search(query, limit=3)
        print()
        
        # Семантический поиск (симуляция)
        semantic_results = semantic_search_simulation(query, model, limit=3)
        print()
        
        # Сравнение результатов
        print("📊 Сравнение результатов:")
        print(f"   Текстовый поиск: {len(text_results)} результатов")
        print(f"   Семантический поиск: {len(semantic_results)} результатов")
        
        if semantic_results:
            best_similarity = semantic_results[0][0]
            print(f"   Лучшее сходство: {best_similarity:.4f}")
        
        print()

def main():
    print("🔍 ТЕСТ СЕМАНТИЧЕСКОГО ПОИСКА")
    print("=" * 60)
    print()
    
    try:
        test_search_queries()
        print("🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 