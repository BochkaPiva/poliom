#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Настройка логирования
logging.basicConfig(level=logging.INFO)

def test_search_settings():
    """Тестируем настройки поиска напрямую через SQL"""
    print("🔍 ТЕСТИРОВАНИЕ НАСТРОЕК ПОИСКА")
    print("=" * 60)
    
    # Подключение к базе данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/poliom')
    
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("✅ Подключение к базе данных установлено")
        
        # Проверяем количество документов
        result = db.execute(text("SELECT COUNT(*) FROM documents WHERE processing_status = 'completed'"))
        docs_count = result.scalar()
        print(f"📄 Документов в базе: {docs_count}")
        
        # Проверяем количество чанков
        result = db.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))
        chunks_count = result.scalar()
        print(f"🧩 Чанков с эмбеддингами: {chunks_count}")
        
        # Проверяем средний размер чанков
        result = db.execute(text("SELECT AVG(content_length) FROM document_chunks WHERE content_length > 0"))
        avg_chunk_size = result.scalar()
        print(f"📏 Средний размер чанка: {avg_chunk_size:.0f} символов")
        
        # Проверяем размерность эмбеддингов
        try:
            result = db.execute(text("SELECT vector_dims(embedding) FROM document_chunks WHERE embedding IS NOT NULL LIMIT 1"))
            embedding_dim = result.scalar()
            print(f"🔢 Размерность эмбеддингов: {embedding_dim}")
        except Exception as e:
            print(f"🔢 Размерность эмбеддингов: Не удалось определить ({str(e)[:50]})")
            embedding_dim = None
        
        # Тестируем поиск с разными порогами схожести
        test_questions = [
            "Когда выплачивается зарплата?",
            "Размер аванса",
            "График работы",
            "Как оформить отпуск?",
            "Процедура увольнения"
        ]
        
        print(f"\n🧪 ТЕСТИРОВАНИЕ ПОИСКА:")
        print("-" * 40)
        
        for question in test_questions:
            print(f"\n❓ Вопрос: {question}")
            
            # Простой текстовый поиск
            words = question.lower().split()
            search_conditions = []
            params = {}
            
            for i, word in enumerate(words):
                if len(word) > 2:  # Игнорируем короткие слова
                    param_name = f'word_{i}'
                    search_conditions.append(f"dc.content ILIKE :{param_name}")
                    params[param_name] = f'%{word}%'
            
            if search_conditions:
                query = text(f"""
                    SELECT COUNT(*) as count
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE d.processing_status = 'completed'
                      AND dc.content_length > 100
                      AND ({' OR '.join(search_conditions)})
                """)
                
                result = db.execute(query, params)
                found_count = result.scalar()
                print(f"   📚 Найдено чанков (текстовый поиск): {found_count}")
                
                # Показываем примеры найденных чанков
                if found_count > 0:
                    query_sample = text(f"""
                        SELECT dc.content, dc.content_length
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE d.processing_status = 'completed'
                          AND dc.content_length > 100
                          AND ({' OR '.join(search_conditions)})
                        LIMIT 3
                    """)
                    
                    result = db.execute(query_sample, params)
                    for i, row in enumerate(result, 1):
                        preview = row.content[:100].replace('\n', ' ')
                        print(f"   {i}. [{row.content_length} симв.] {preview}...")
            else:
                print("   ❌ Не удалось извлечь ключевые слова")
        
        # Анализ качества чанков
        print(f"\n📊 АНАЛИЗ КАЧЕСТВА ЧАНКОВ:")
        print("-" * 40)
        
        # Распределение по размерам
        size_ranges = [
            (0, 500, "Маленькие"),
            (500, 1000, "Средние"),
            (1000, 1500, "Большие"),
            (1500, 2000, "Очень большие"),
            (2000, 999999, "Огромные")
        ]
        
        for min_size, max_size, label in size_ranges:
            result = db.execute(text("""
                SELECT COUNT(*) 
                FROM document_chunks 
                WHERE content_length BETWEEN :min_size AND :max_size
                  AND embedding IS NOT NULL
            """), {'min_size': min_size, 'max_size': max_size})
            
            count = result.scalar()
            percentage = (count / chunks_count * 100) if chunks_count > 0 else 0
            print(f"   {label} ({min_size}-{max_size}): {count} ({percentage:.1f}%)")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print("-" * 40)
        
        if avg_chunk_size < 800:
            print("⚠️ Средний размер чанков мал - рекомендуется увеличить до 1000-1500 символов")
        elif avg_chunk_size > 2000:
            print("⚠️ Средний размер чанков велик - может снижать точность поиска")
        else:
            print("✅ Размер чанков оптимален")
        
        if chunks_count < 100:
            print("⚠️ Мало чанков в базе - добавьте больше документов")
        else:
            print(f"✅ Достаточное количество чанков: {chunks_count}")
        
        if embedding_dim == 312:
            print("✅ Используется rubert-tiny2 (312 измерений)")
        elif embedding_dim == 1024:
            print("✅ Используется более мощная модель (1024 измерения)")
        else:
            print(f"❓ Неизвестная модель эмбеддингов ({embedding_dim} измерений)")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция"""
    print(f"🚀 Запуск тестирования настроек поиска")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_search_settings()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    main() 