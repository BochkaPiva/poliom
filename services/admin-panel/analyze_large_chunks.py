#!/usr/bin/env python3
"""
Анализ больших чанков для понимания проблемы
"""

import sys
import os
from pathlib import Path

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from shared.models.database import SessionLocal
from shared.models.document import DocumentChunk, Document

def analyze_chunk_sizes():
    """Анализируем размеры чанков"""
    print("🔍 АНАЛИЗ РАЗМЕРОВ ЧАНКОВ\n")
    
    db = SessionLocal()
    try:
        # Получаем все чанки
        chunks = db.query(DocumentChunk).all()
        
        if not chunks:
            print("❌ Чанков в базе нет")
            return
        
        print(f"📊 Всего чанков: {len(chunks)}")
        
        # Анализируем размеры
        sizes = [chunk.content_length for chunk in chunks]
        sizes.sort()
        
        print(f"\n📈 Статистика размеров:")
        print(f"   Минимальный: {min(sizes)} символов")
        print(f"   Максимальный: {max(sizes)} символов")
        print(f"   Средний: {sum(sizes) // len(sizes)} символов")
        print(f"   Медианный: {sizes[len(sizes)//2]} символов")
        
        # Распределение по размерам
        tiny = len([s for s in sizes if s < 10])
        small = len([s for s in sizes if 10 <= s < 100])
        medium = len([s for s in sizes if 100 <= s < 500])
        large = len([s for s in sizes if s >= 500])
        
        print(f"\n📊 Распределение:")
        print(f"   Крошечные (<10): {tiny} ({tiny/len(sizes)*100:.1f}%)")
        print(f"   Маленькие (10-100): {small} ({small/len(sizes)*100:.1f}%)")
        print(f"   Средние (100-500): {medium} ({medium/len(sizes)*100:.1f}%)")
        print(f"   Большие (>=500): {large} ({large/len(sizes)*100:.1f}%)")
        
        return chunks
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []
    finally:
        db.close()

def show_large_chunks():
    """Показываем большие чанки"""
    print("\n🔍 АНАЛИЗ БОЛЬШИХ ЧАНКОВ\n")
    
    db = SessionLocal()
    try:
        # Получаем чанки размером больше 500 символов
        large_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.content_length >= 500
        ).order_by(DocumentChunk.content_length.desc()).limit(5).all()
        
        if not large_chunks:
            print("❌ Больших чанков не найдено")
            return
        
        print(f"📄 Найдено {len(large_chunks)} больших чанков:")
        
        for i, chunk in enumerate(large_chunks):
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            
            print(f"\n🧩 ЧАНК #{i+1}")
            print(f"   ID: {chunk.id}")
            print(f"   Документ: {document.original_filename if document else f'ID {chunk.document_id}'}")
            print(f"   Индекс: {chunk.chunk_index}")
            print(f"   Размер: {chunk.content_length} символов")
            print(f"   Содержимое:")
            print(f"   {'-'*60}")
            print(f"   {chunk.content[:300]}...")
            if len(chunk.content) > 300:
                print(f"   [... еще {len(chunk.content) - 300} символов]")
            print(f"   {'-'*60}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

def show_small_chunks():
    """Показываем маленькие чанки"""
    print("\n🔍 АНАЛИЗ МАЛЕНЬКИХ ЧАНКОВ\n")
    
    db = SessionLocal()
    try:
        # Получаем чанки размером меньше 50 символов
        small_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.content_length < 50
        ).order_by(DocumentChunk.chunk_index).limit(10).all()
        
        if not small_chunks:
            print("❌ Маленьких чанков не найдено")
            return
        
        print(f"📄 Найдено {len(small_chunks)} маленьких чанков:")
        
        for i, chunk in enumerate(small_chunks):
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            
            print(f"\n🧩 ЧАНК #{i+1}")
            print(f"   ID: {chunk.id}")
            print(f"   Документ: {document.original_filename if document else f'ID {chunk.document_id}'}")
            print(f"   Индекс: {chunk.chunk_index}")
            print(f"   Размер: {chunk.content_length} символов")
            print(f"   Содержимое: '{chunk.content}'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

def analyze_sequential_chunks():
    """Анализируем последовательные чанки"""
    print("\n🔍 АНАЛИЗ ПОСЛЕДОВАТЕЛЬНЫХ ЧАНКОВ\n")
    
    db = SessionLocal()
    try:
        # Получаем первые 10 чанков по порядку
        chunks = db.query(DocumentChunk).order_by(
            DocumentChunk.document_id, 
            DocumentChunk.chunk_index
        ).limit(10).all()
        
        if not chunks:
            print("❌ Чанков не найдено")
            return
        
        print(f"📄 Первые 10 чанков по порядку:")
        
        for chunk in chunks:
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            
            print(f"\n🧩 Чанк {chunk.chunk_index} (ID: {chunk.id})")
            print(f"   Документ: {document.original_filename if document else f'ID {chunk.document_id}'}")
            print(f"   Размер: {chunk.content_length} символов")
            print(f"   Содержимое: '{chunk.content[:100]}{'...' if len(chunk.content) > 100 else ''}'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 ДЕТАЛЬНЫЙ АНАЛИЗ ЧАНКОВ\n")
    
    # Анализируем размеры
    chunks = analyze_chunk_sizes()
    
    if chunks:
        # Показываем большие чанки
        show_large_chunks()
        
        # Показываем маленькие чанки
        show_small_chunks()
        
        # Анализируем последовательные чанки
        analyze_sequential_chunks()
    
    print("\n" + "="*60)
    print("📊 АНАЛИЗ ЗАВЕРШЕН")
    print("="*60)

if __name__ == "__main__":
    main() 