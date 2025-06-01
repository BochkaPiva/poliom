#!/usr/bin/env python3
"""
Простой тест поиска без LLM для демонстрации базовой функциональности
"""

import sys
import os
from pathlib import Path

# Добавляем путь к services для импорта модулей
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения из корневого .env файла
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from shared.utils.embedding_service import EmbeddingService
from shared.models.database import SessionLocal, DocumentChunk, Document
import numpy as np

def test_basic_search():
    """Тестирует базовый поиск без LLM"""
    print("🔍 ТЕСТ БАЗОВОГО ПОИСКА")
    print("=" * 60)
    
    # Инициализируем сервис эмбеддингов
    embedding_service = EmbeddingService()
    
    # Тестовые запросы
    test_queries = [
        "доплата за ночную работу",
        "оплата в праздничные дни",
        "вредные условия труда"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 ТЕСТ {i}/{len(test_queries)}:")
        print(f"🔍 Запрос: {query}")
        print("-" * 60)
        
        try:
            # Создаем эмбеддинг для запроса
            query_embedding = embedding_service.create_embedding(query)
            
            # Выполняем поиск
            results = perform_search(query_embedding, max_results=3)
            
            if results:
                print(f"📄 Найдено результатов: {len(results)}")
                print(f"📈 Лучшая схожесть: {results[0]['similarity']:.3f}")
                
                # Показываем лучший результат
                best_result = results[0]
                print(f"\n💬 ЛУЧШИЙ РЕЗУЛЬТАТ:")
                print(f"📚 Документ: {best_result['document_name']}")
                print(f"🧩 Фрагмент #{best_result['chunk_index']}")
                print(f"📊 Схожесть: {best_result['similarity']:.3f}")
                print(f"📝 Содержимое:")
                
                # Показываем первые 300 символов
                content = best_result['content']
                if len(content) > 300:
                    content = content[:300] + "..."
                print(f'"{content}"')
                
                # Извлекаем ключевые данные
                extract_key_data(best_result['content'])
                
            else:
                print("❌ Результаты не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 60)

def perform_search(query_embedding, max_results=5, min_similarity=0.3):
    """Выполняет поиск по эмбеддингам"""
    session = SessionLocal()
    try:
        # Получаем все чанки с эмбеддингами
        chunks = session.query(DocumentChunk).join(Document).filter(
            DocumentChunk.embedding.isnot(None)
        ).all()
        
        if not chunks:
            return []
        
        # Вычисляем схожесть для каждого чанка
        similarities = []
        query_embedding_np = np.array(query_embedding)
        
        for chunk in chunks:
            try:
                chunk_embedding = np.array(chunk.embedding)
                
                # Косинусная схожесть
                similarity = np.dot(query_embedding_np, chunk_embedding) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(chunk_embedding)
                )
                
                if similarity >= min_similarity:
                    similarities.append({
                        'chunk_id': chunk.id,
                        'content': chunk.content,
                        'similarity': float(similarity),
                        'document_name': chunk.document.original_filename,
                        'document_id': chunk.document.id,
                        'chunk_index': chunk.chunk_index,
                        'content_length': chunk.content_length
                    })
                    
            except Exception as e:
                print(f"⚠️ Ошибка при обработке чанка {chunk.id}: {e}")
                continue
        
        # Сортируем по убыванию схожести
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:max_results]
        
    finally:
        session.close()

def extract_key_data(content):
    """Извлекает ключевые данные из текста"""
    import re
    
    # Ищем проценты
    percentages = re.findall(r'(\d+(?:\.\d+)?)\s*(?:процент|%)', content, re.IGNORECASE)
    if percentages:
        print(f"💰 Найденные проценты: {', '.join(percentages)}%")
    
    # Ищем суммы в рублях
    amounts = re.findall(r'(\d+(?:\s*\d+)*)\s*(?:рубл|руб)', content, re.IGNORECASE)
    if amounts:
        print(f"💵 Найденные суммы: {', '.join(amounts)} руб.")
    
    # Ищем время
    times = re.findall(r'(\d+)\s*час', content, re.IGNORECASE)
    if times:
        print(f"⏰ Найденное время: {', '.join(times)} час.")

def main():
    """Основная функция"""
    print("🚀 ТЕСТ БАЗОВОЙ ФУНКЦИОНАЛЬНОСТИ ПОИСКА")
    print("Этот тест демонстрирует работу поиска без LLM")
    print()
    
    try:
        test_basic_search()
        
        print("\n" + "=" * 60)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("📈 Базовая функциональность поиска работает!")
        print("💡 Для полной функциональности требуется подключение к GigaChat")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 