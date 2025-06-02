#!/usr/bin/env python3
"""
БЕЗОПАСНЫЙ анализатор размеров чанков в базе данных
Обходит проблемы с PostgreSQL vector типами
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
from sqlalchemy import text
from shared.models.database import engine
from shared.models import Document

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def analyze_chunk_sizes_safe():
    """БЕЗОПАСНЫЙ анализ размеров чанков в базе данных"""
    print("📊 БЕЗОПАСНЫЙ АНАЛИЗ РАЗМЕРОВ ЧАНКОВ")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Общая статистика через SQL
        print("📈 ОБЩАЯ СТАТИСТИКА ЧАНКОВ:")
        
        # Общее количество чанков
        total_chunks = db.execute(text("SELECT COUNT(*) FROM document_chunks")).fetchone()[0]
        
        if total_chunks == 0:
            print("❌ Чанки не найдены в базе данных")
            return
        
        print(f"📦 Всего чанков: {total_chunks}")
        
        # Статистика размеров
        stats = db.execute(text("""
            SELECT 
                MIN(content_length) as min_size,
                MAX(content_length) as max_size,
                ROUND(AVG(content_length)) as avg_size,
                SUM(content_length) as total_size
            FROM document_chunks
        """)).fetchone()
        
        if stats:
            print(f"📏 Размеры чанков:")
            print(f"   Минимальный: {stats[0]} символов")
            print(f"   Максимальный: {stats[1]} символов")
            print(f"   Средний: {stats[2]} символов")
            print(f"   Общий размер: {stats[3]:,} символов")
        
        print()
        
        # Распределение по размерам
        print("📊 РАСПРЕДЕЛЕНИЕ ПО РАЗМЕРАМ:")
        
        size_ranges = [
            (0, 100, "Очень маленькие (0-100)"),
            (101, 300, "Маленькие (101-300)"),
            (301, 600, "Средние (301-600)"),
            (601, 1000, "Большие (601-1000)"),
            (1001, 1500, "Очень большие (1001-1500)"),
            (1501, 999999, "Огромные (>1500)")
        ]
        
        for min_size, max_size, label in size_ranges:
            if max_size == 999999:
                count = db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE content_length >= :min_size
                """), {"min_size": min_size}).fetchone()[0]
            else:
                count = db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE content_length BETWEEN :min_size AND :max_size
                """), {"min_size": min_size, "max_size": max_size}).fetchone()[0]
            
            percentage = (count / total_chunks * 100) if total_chunks > 0 else 0
            print(f"   {label}: {count} ({percentage:.1f}%)")
        
        print()
        
        # Анализ по документам
        print("📄 АНАЛИЗ ПО ДОКУМЕНТАМ:")
        
        documents = db.query(Document).all()
        
        for doc in documents:
            print(f"\n📄 {doc.original_filename} (ID: {doc.id}):")
            
            # Статистика чанков для документа
            doc_stats = db.execute(text("""
                SELECT 
                    COUNT(*) as chunk_count,
                    MIN(content_length) as min_size,
                    MAX(content_length) as max_size,
                    ROUND(AVG(content_length)) as avg_size
                FROM document_chunks 
                WHERE document_id = :doc_id
            """), {"doc_id": doc.id}).fetchone()
            
            if doc_stats and doc_stats[0] > 0:
                print(f"   📦 Чанков: {doc_stats[0]}")
                print(f"   📏 Размеры: мин={doc_stats[1]}, макс={doc_stats[2]}, средний={doc_stats[3]}")
                
                # Проблемные чанки
                small_chunks = db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE document_id = :doc_id AND content_length < 200
                """), {"doc_id": doc.id}).fetchone()[0]
                
                large_chunks = db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE document_id = :doc_id AND content_length > 1500
                """), {"doc_id": doc.id}).fetchone()[0]
                
                if small_chunks > 0:
                    print(f"   ⚠️ Слишком маленьких чанков (<200): {small_chunks}")
                
                if large_chunks > 0:
                    print(f"   ⚠️ Слишком больших чанков (>1500): {large_chunks}")
                
                # Качество чанков
                quality_score = 100
                if small_chunks > doc_stats[0] * 0.1:  # Более 10% маленьких
                    quality_score -= 20
                if large_chunks > doc_stats[0] * 0.05:  # Более 5% больших
                    quality_score -= 15
                if doc_stats[3] < 500 or doc_stats[3] > 1200:  # Средний размер не в оптимальном диапазоне
                    quality_score -= 10
                
                print(f"   📊 Оценка качества: {quality_score}%")
                
            else:
                print(f"   📦 Чанки отсутствуют")
        
        print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        
        # Анализируем общую статистику для рекомендаций
        if stats:
            avg_size = stats[2]
            min_size = stats[0]
            max_size = stats[1]
            
            recommendations = []
            
            if avg_size < 500:
                recommendations.append("📈 Средний размер чанков слишком мал. Рекомендуется увеличить target_chunk_size")
            elif avg_size > 1200:
                recommendations.append("📉 Средний размер чанков слишком велик. Рекомендуется уменьшить target_chunk_size")
            else:
                recommendations.append("✅ Средний размер чанков в оптимальном диапазоне")
            
            if min_size < 50:
                recommendations.append("⚠️ Есть очень маленькие чанки. Проверьте алгоритм разбиения")
            
            if max_size > 2000:
                recommendations.append("⚠️ Есть очень большие чанки. Проверьте max_chunk_size")
            
            # Проверяем распределение
            small_count = db.execute(text("""
                SELECT COUNT(*) FROM document_chunks WHERE content_length < 200
            """)).fetchone()[0]
            
            large_count = db.execute(text("""
                SELECT COUNT(*) FROM document_chunks WHERE content_length > 1500
            """)).fetchone()[0]
            
            small_percentage = (small_count / total_chunks * 100) if total_chunks > 0 else 0
            large_percentage = (large_count / total_chunks * 100) if total_chunks > 0 else 0
            
            if small_percentage > 15:
                recommendations.append(f"📊 {small_percentage:.1f}% чанков слишком маленькие. Рекомендуется настроить min_chunk_size")
            
            if large_percentage > 10:
                recommendations.append(f"📊 {large_percentage:.1f}% чанков слишком большие. Рекомендуется настроить max_chunk_size")
            
            if not recommendations:
                recommendations.append("🎉 Качество чанков отличное! Никаких изменений не требуется")
            
            for rec in recommendations:
                print(f"   {rec}")
        
        print()
        print("=" * 60)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {str(e)}")
    
    finally:
        db.close()

def analyze_document_chunks_safe(document_id: int):
    """БЕЗОПАСНЫЙ анализ чанков конкретного документа"""
    print(f"🔍 БЕЗОПАСНЫЙ АНАЛИЗ ЧАНКОВ ДОКУМЕНТА ID {document_id}")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Получаем документ
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            print(f"❌ Документ с ID {document_id} не найден")
            return
        
        print(f"📄 Документ: {document.original_filename}")
        print(f"📊 Статус: {document.processing_status}")
        print()
        
        # Статистика чанков
        stats = db.execute(text("""
            SELECT 
                COUNT(*) as chunk_count,
                MIN(content_length) as min_size,
                MAX(content_length) as max_size,
                ROUND(AVG(content_length)) as avg_size,
                SUM(content_length) as total_size
            FROM document_chunks 
            WHERE document_id = :doc_id
        """), {"doc_id": document_id}).fetchone()
        
        if not stats or stats[0] == 0:
            print("❌ Чанки для этого документа не найдены")
            return
        
        print("📊 СТАТИСТИКА ЧАНКОВ:")
        print(f"   📦 Количество: {stats[0]}")
        print(f"   📏 Размеры: мин={stats[1]}, макс={stats[2]}, средний={stats[3]}")
        print(f"   💾 Общий размер: {stats[4]:,} символов")
        print()
        
        # Распределение по размерам
        print("📊 РАСПРЕДЕЛЕНИЕ ПО РАЗМЕРАМ:")
        
        size_ranges = [
            (0, 100, "Очень маленькие (0-100)"),
            (101, 300, "Маленькие (101-300)"),
            (301, 600, "Средние (301-600)"),
            (601, 1000, "Большие (601-1000)"),
            (1001, 1500, "Очень большие (1001-1500)"),
            (1501, 999999, "Огромные (>1500)")
        ]
        
        total_chunks = stats[0]
        
        for min_size, max_size, label in size_ranges:
            if max_size == 999999:
                count = db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE document_id = :doc_id AND content_length >= :min_size
                """), {"doc_id": document_id, "min_size": min_size}).fetchone()[0]
            else:
                count = db.execute(text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE document_id = :doc_id AND content_length BETWEEN :min_size AND :max_size
                """), {"doc_id": document_id, "min_size": min_size, "max_size": max_size}).fetchone()[0]
            
            percentage = (count / total_chunks * 100) if total_chunks > 0 else 0
            print(f"   {label}: {count} ({percentage:.1f}%)")
        
        print()
        
        # Проблемные чанки
        print("⚠️ ПРОБЛЕМНЫЕ ЧАНКИ:")
        
        # Слишком маленькие
        small_chunks = db.execute(text("""
            SELECT chunk_index, content_length, LEFT(content, 50) as preview
            FROM document_chunks 
            WHERE document_id = :doc_id AND content_length < 200
            ORDER BY content_length
            LIMIT 5
        """), {"doc_id": document_id}).fetchall()
        
        if small_chunks:
            print(f"   📉 Слишком маленькие чанки (<200 символов): {len(small_chunks)} найдено")
            for chunk in small_chunks[:3]:  # Показываем только первые 3
                preview = chunk[2].replace('\n', ' ')
                print(f"      Чанк {chunk[0]+1}: {chunk[1]} символов - {preview}...")
        else:
            print("   ✅ Слишком маленьких чанков не найдено")
        
        # Слишком большие
        large_chunks = db.execute(text("""
            SELECT chunk_index, content_length, LEFT(content, 50) as preview
            FROM document_chunks 
            WHERE document_id = :doc_id AND content_length > 1500
            ORDER BY content_length DESC
            LIMIT 5
        """), {"doc_id": document_id}).fetchall()
        
        if large_chunks:
            print(f"   📈 Слишком большие чанки (>1500 символов): {len(large_chunks)} найдено")
            for chunk in large_chunks[:3]:  # Показываем только первые 3
                preview = chunk[2].replace('\n', ' ')
                print(f"      Чанк {chunk[0]+1}: {chunk[1]} символов - {preview}...")
        else:
            print("   ✅ Слишком больших чанков не найдено")
        
        print()
        
        # Примеры чанков
        print("📋 ПРИМЕРЫ ЧАНКОВ:")
        
        sample_chunks = db.execute(text("""
            SELECT chunk_index, content_length, LEFT(content, 100) as preview
            FROM document_chunks 
            WHERE document_id = :doc_id
            ORDER BY chunk_index
            LIMIT 5
        """), {"doc_id": document_id}).fetchall()
        
        for chunk in sample_chunks:
            preview = chunk[2].replace('\n', ' ')
            print(f"   Чанк {chunk[0]+1} [{chunk[1]} символов]: {preview}...")
        
        print()
        
        # Оценка качества
        print("📊 ОЦЕНКА КАЧЕСТВА:")
        
        avg_size = stats[3]
        small_count = len([c for c in small_chunks])
        large_count = len([c for c in large_chunks])
        
        quality_score = 100
        issues = []
        
        if small_count > total_chunks * 0.1:  # Более 10% маленьких
            quality_score -= 20
            issues.append(f"Слишком много маленьких чанков ({small_count})")
        
        if large_count > total_chunks * 0.05:  # Более 5% больших
            quality_score -= 15
            issues.append(f"Слишком много больших чанков ({large_count})")
        
        if avg_size < 500:
            quality_score -= 15
            issues.append("Средний размер слишком мал")
        elif avg_size > 1200:
            quality_score -= 10
            issues.append("Средний размер слишком велик")
        
        print(f"   📊 Общая оценка: {quality_score}%")
        
        if issues:
            print("   ⚠️ Проблемы:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ Качество отличное!")
        
        print()
        print("=" * 60)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка анализа документа: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Безопасный анализ размеров чанков в базе данных")
    parser.add_argument("--doc-id", type=int, help="ID конкретного документа для анализа")
    
    args = parser.parse_args()
    
    if args.doc_id:
        analyze_document_chunks_safe(args.doc_id)
    else:
        analyze_chunk_sizes_safe() 