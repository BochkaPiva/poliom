#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обработки документов
"""

import os
import sys
import tempfile
from pathlib import Path

# Добавляем путь к services для доступа к shared модулям
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

from shared.utils.document_processor import DocumentProcessor
from shared.utils.embeddings import EmbeddingService
from shared.utils.text_processing import chunk_text

def test_document_processor():
    """Тестируем процессор документов"""
    print("🔍 Тестируем DocumentProcessor...")
    
    processor = DocumentProcessor()
    
    # Создаем тестовый текстовый файл
    test_text = """
    Это тестовый документ для проверки обработки.
    
    Он содержит несколько абзацев текста.
    Каждый абзац должен быть правильно обработан.
    
    Система должна извлечь этот текст и разбить его на чанки.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_text)
        temp_file = f.name
    
    try:
        # Тестируем извлечение текста
        extracted_text = processor.extract_text(temp_file)
        print(f"✅ Текст извлечен: {len(extracted_text)} символов")
        print(f"   Первые 100 символов: {extracted_text[:100]}...")
        
        # Тестируем разбиение на чанки
        chunks = processor.split_into_chunks(extracted_text, chunk_size=100, overlap=20)
        print(f"✅ Создано чанков: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"   Чанк {i+1}: {len(chunk)} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
        
    finally:
        # Удаляем временный файл
        os.unlink(temp_file)

def test_embeddings():
    """Тестируем сервис эмбеддингов"""
    print("\n🧠 Тестируем EmbeddingService...")
    
    try:
        embedding_service = EmbeddingService()
        print(f"✅ Модель загружена: {embedding_service.model_name}")
        
        # Тестируем создание эмбеддинга
        test_text = "Это тестовый текст для создания эмбеддинга"
        embedding = embedding_service.get_embedding(test_text)
        
        print(f"✅ Эмбеддинг создан: размерность {len(embedding)}")
        print(f"   Первые 5 значений: {embedding[:5]}")
        
        # Тестируем схожесть
        text1 = "Собака бегает по парку"
        text2 = "Пес играет в саду"
        text3 = "Компьютер работает быстро"
        
        similarity_12 = embedding_service.similarity(text1, text2)
        similarity_13 = embedding_service.similarity(text1, text3)
        
        print(f"✅ Схожесть '{text1}' и '{text2}': {similarity_12:.3f}")
        print(f"✅ Схожесть '{text1}' и '{text3}': {similarity_13:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_text_processing():
    """Тестируем обработку текста"""
    print("\n📝 Тестируем text_processing...")
    
    try:
        test_text = """
        Это длинный текст для тестирования разбиения на чанки.
        Он содержит несколько предложений. Каждое предложение должно быть учтено.
        
        Система должна правильно разбить текст на части с перекрытием.
        Это поможет сохранить контекст между чанками.
        """
        
        chunks = chunk_text(test_text, chunk_size=100, overlap=20)
        print(f"✅ Создано чанков: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"   Чанк {i+1}: {len(chunk)} символов - '{chunk[:50]}...'")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запускаем тестирование обработки документов\n")
    
    results = []
    
    # Тестируем компоненты
    results.append(test_document_processor())
    results.append(test_embeddings())
    results.append(test_text_processing())
    
    # Выводим результаты
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("="*50)
    
    if all(results):
        print("🎉 Все тесты прошли успешно!")
        print("✅ Система готова к обработке документов")
    else:
        print("⚠️  Некоторые тесты не прошли")
        print("❌ Требуется дополнительная настройка")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 