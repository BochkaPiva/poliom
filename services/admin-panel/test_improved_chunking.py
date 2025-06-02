#!/usr/bin/env python3
"""
Тест улучшенного алгоритма чанкинга
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

from shared.utils.document_processor import DocumentProcessor

def test_chunking_algorithm():
    """Тестируем улучшенный алгоритм чанкинга"""
    print("🧪 Тестирование улучшенного алгоритма чанкинга\n")
    
    # Создаем процессор документов
    processor = DocumentProcessor()
    
    # Тестовый текст
    test_text = """
    Это первое предложение документа. Оно содержит важную информацию о системе управления.
    
    Второе предложение продолжает тему. Здесь мы рассматриваем различные аспекты работы.
    
    Третье предложение добавляет детали. Важно понимать, что каждый элемент системы взаимосвязан.
    
    Четвертое предложение завершает первый раздел. Переходим к следующей части документа.
    
    Пятое предложение начинает новый раздел. Здесь мы углубляемся в технические детали.
    
    Шестое предложение продолжает техническую тему. Рассматриваем архитектуру системы.
    
    Седьмое предложение добавляет важные нюансы. Каждый компонент имеет свою роль.
    
    Восьмое предложение завершает технический раздел. Переходим к практическим примерам.
    """
    
    print(f"📝 Исходный текст: {len(test_text)} символов")
    print(f"📄 Содержание: {test_text[:200]}...\n")
    
    # Тестируем с разными параметрами
    test_cases = [
        {"chunk_size": 200, "overlap": 50, "name": "Маленькие чанки"},
        {"chunk_size": 500, "overlap": 100, "name": "Средние чанки"},
        {"chunk_size": 1000, "overlap": 200, "name": "Большие чанки"},
    ]
    
    for case in test_cases:
        print(f"🔧 {case['name']} (размер: {case['chunk_size']}, перекрытие: {case['overlap']})")
        print("-" * 60)
        
        chunks = processor.split_into_chunks(
            test_text, 
            chunk_size=case['chunk_size'], 
            overlap=case['overlap']
        )
        
        print(f"📊 Количество чанков: {len(chunks)}")
        
        if chunks:
            chunk_sizes = [len(chunk) for chunk in chunks]
            print(f"📏 Размеры чанков:")
            print(f"   Минимальный: {min(chunk_sizes)} символов")
            print(f"   Максимальный: {max(chunk_sizes)} символов")
            print(f"   Средний: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
            
            print(f"\n📋 Примеры чанков:")
            for i, chunk in enumerate(chunks[:3]):  # Показываем первые 3 чанка
                print(f"   Чанк {i+1}: {chunk[:100]}...")
        
        print("\n" + "="*80 + "\n")

def test_real_document():
    """Тестируем на реальном документе"""
    print("📄 Тестирование на реальном документе\n")
    
    # Путь к документу
    doc_path = Path("uploads/20250602_062848_oplata_truda.docx")
    
    if not doc_path.exists():
        print(f"❌ Документ не найден: {doc_path}")
        return
    
    # Создаем процессор
    processor = DocumentProcessor()
    
    try:
        # Извлекаем текст
        print("📖 Извлекаем текст из документа...")
        text = processor.extract_text(str(doc_path))
        print(f"✅ Текст извлечен: {len(text)} символов")
        
        # Разбиваем на чанки
        print("✂️ Разбиваем на чанки...")
        chunks = processor.split_into_chunks(text, chunk_size=1000, overlap=200)
        
        print(f"✅ Создано {len(chunks)} чанков")
        
        # Статистика
        chunk_sizes = [len(chunk) for chunk in chunks]
        print(f"\n📊 Статистика чанков:")
        print(f"   Минимальный размер: {min(chunk_sizes)} символов")
        print(f"   Максимальный размер: {max(chunk_sizes)} символов")
        print(f"   Средний размер: {sum(chunk_sizes) / len(chunk_sizes):.1f} символов")
        
        # Показываем несколько примеров
        print(f"\n📋 Примеры чанков:")
        for i in range(min(3, len(chunks))):
            print(f"\n--- Чанк {i+1} ({len(chunks[i])} символов) ---")
            print(chunks[i][:300] + "..." if len(chunks[i]) > 300 else chunks[i])
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция"""
    print("🚀 Тестирование улучшенного алгоритма чанкинга\n")
    
    # Тест на синтетических данных
    test_chunking_algorithm()
    
    # Тест на реальном документе
    test_real_document()
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    main() 