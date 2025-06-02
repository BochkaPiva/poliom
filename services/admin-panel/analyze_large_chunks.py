#!/usr/bin/env python3
"""
Анализ размеров чанков в базе данных
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

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def analyze_chunk_sizes():
    """Анализируем размеры чанков"""
    print("📊 АНАЛИЗ РАЗМЕРОВ ЧАНКОВ")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Получаем все чанки
        chunks = db.query(DocumentChunk).all()
        
        if not chunks:
            print("❌ Чанки не найдены в базе данных")
            return
        
        print(f"📦 Всего чанков: {len(chunks)}")
        print()
        
        # Анализируем размеры
        sizes = [len(chunk.content) for chunk in chunks]
        
        # Общая статистика
        total_size = sum(sizes)
        min_size = min(sizes)
        max_size = max(sizes)
        avg_size = total_size / len(sizes)
        
        print("📈 ОБЩАЯ СТАТИСТИКА РАЗМЕРОВ:")
        print(f"   Минимальный: {min_size} символов")
        print(f"   Максимальный: {max_size} символов")
        print(f"   Средний: {avg_size:.1f} символов")
        print(f"   Общий размер: {total_size:,} символов")
        print()
        
        # Распределение по диапазонам
        ranges = [
            (0, 100, "Очень маленькие (0-100)"),
            (101, 300, "Маленькие (101-300)"),
            (301, 500, "Небольшие (301-500)"),
            (501, 800, "Средние (501-800)"),
            (801, 1000, "Оптимальные (801-1000)"),
            (1001, 1500, "Большие (1001-1500)"),
            (1501, float('inf'), "Очень большие (1501+)")
        ]
        
        print("📊 РАСПРЕДЕЛЕНИЕ ПО РАЗМЕРАМ:")
        for min_r, max_r, label in ranges:
            count = len([s for s in sizes if min_r <= s <= max_r])
            percentage = (count / len(sizes)) * 100
            print(f"   {label}: {count} чанков ({percentage:.1f}%)")
        
        print()
        
        # Анализ по документам
        print("📄 АНАЛИЗ ПО ДОКУМЕНТАМ:")
        documents = db.query(Document).all()
        
        for doc in documents:
            doc_chunks = [chunk for chunk in chunks if chunk.document_id == doc.id]
            if doc_chunks:
                doc_sizes = [len(chunk.content) for chunk in doc_chunks]
                doc_min = min(doc_sizes)
                doc_max = max(doc_sizes)
                doc_avg = sum(doc_sizes) / len(doc_sizes)
                
                print(f"   📄 {doc.original_filename}:")
                print(f"      Чанков: {len(doc_chunks)}")
                print(f"      Размеры: мин={doc_min}, макс={doc_max}, средний={doc_avg:.1f}")
        
        print()
        
        # Поиск проблемных чанков
        print("⚠️ ПРОБЛЕМНЫЕ ЧАНКИ:")
        
        # Слишком маленькие чанки
        small_chunks = [chunk for chunk in chunks if len(chunk.content) < 100]
        if small_chunks:
            print(f"   📉 Слишком маленькие (<100 символов): {len(small_chunks)}")
            for chunk in small_chunks[:5]:  # Показываем первые 5
                preview = chunk.content[:50].replace('\n', ' ')
                print(f"      ID {chunk.id}: {len(chunk.content)} символов - '{preview}...'")
        
        # Слишком большие чанки
        large_chunks = [chunk for chunk in chunks if len(chunk.content) > 1500]
        if large_chunks:
            print(f"   📈 Слишком большие (>1500 символов): {len(large_chunks)}")
            for chunk in large_chunks[:5]:  # Показываем первые 5
                preview = chunk.content[:50].replace('\n', ' ')
                print(f"      ID {chunk.id}: {len(chunk.content)} символов - '{preview}...'")
        
        if not small_chunks and not large_chunks:
            print("   ✅ Проблемных чанков не найдено")
        
        print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        
        small_percentage = (len(small_chunks) / len(chunks)) * 100
        large_percentage = (len(large_chunks) / len(chunks)) * 100
        optimal_percentage = (len([s for s in sizes if 500 <= s <= 1000]) / len(sizes)) * 100
        
        if small_percentage > 10:
            print(f"   ⚠️ Много маленьких чанков ({small_percentage:.1f}%) - возможно, нужно увеличить минимальный размер")
        
        if large_percentage > 5:
            print(f"   ⚠️ Много больших чанков ({large_percentage:.1f}%) - возможно, нужно улучшить алгоритм разбиения")
        
        if optimal_percentage > 70:
            print(f"   ✅ Хорошее распределение размеров ({optimal_percentage:.1f}% в оптимальном диапазоне)")
        else:
            print(f"   ⚠️ Только {optimal_percentage:.1f}% чанков в оптимальном диапазоне (500-1000 символов)")
        
        if avg_size < 500:
            print("   💡 Средний размер чанка мал - рассмотрите увеличение chunk_size")
        elif avg_size > 1200:
            print("   💡 Средний размер чанка велик - рассмотрите уменьшение chunk_size")
        else:
            print("   ✅ Средний размер чанка в норме")
    
    except Exception as e:
        print(f"❌ Ошибка анализа: {str(e)}")
    
    finally:
        db.close()

def analyze_document_chunks(document_id: int):
    """Анализируем чанки конкретного документа"""
    print(f"🔍 АНАЛИЗ ЧАНКОВ ДОКУМЕНТА ID {document_id}")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"❌ Документ с ID {document_id} не найден")
            return
        
        print(f"📄 Документ: {document.original_filename}")
        print()
        
        # Получаем чанки документа
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        
        if not chunks:
            print("❌ Чанки не найдены")
            return
        
        print(f"📦 Количество чанков: {len(chunks)}")
        
        # Анализируем размеры
        sizes = [len(chunk.content) for chunk in chunks]
        
        print(f"📊 Статистика размеров:")
        print(f"   Минимальный: {min(sizes)} символов")
        print(f"   Максимальный: {max(sizes)} символов")
        print(f"   Средний: {sum(sizes)/len(sizes):.1f} символов")
        print()
        
        # Показываем все чанки с размерами
        print("📋 СПИСОК ЧАНКОВ:")
        for i, chunk in enumerate(chunks):
            size = len(chunk.content)
            preview = chunk.content[:80].replace('\n', ' ')
            
            # Определяем категорию размера
            if size < 300:
                category = "📉 Маленький"
            elif size > 1200:
                category = "📈 Большой"
            else:
                category = "✅ Нормальный"
            
            print(f"   {i+1:3d}. [{size:4d} символов] {category}")
            print(f"        '{preview}...'")
            print()
    
    except Exception as e:
        print(f"❌ Ошибка анализа документа: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Анализ размеров чанков")
    parser.add_argument("--doc-id", type=int, help="ID конкретного документа для анализа")
    
    args = parser.parse_args()
    
    if args.doc_id:
        analyze_document_chunks(args.doc_id)
    else:
        analyze_chunk_sizes() 