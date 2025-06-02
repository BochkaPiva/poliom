#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
print(f"Загружен .env файл: {env_path}")

def get_db_connection():
    """Получение соединения с базой данных"""
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database=os.getenv("POSTGRES_DB", "poliom"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

def check_specific_chunks():
    """Проверка конкретных чанков с информацией о датах выплат"""
    
    # Подключение к базе данных
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем чанк 2130 (из ПВТР)
    print("="*80)
    print("ПРОВЕРКА ЧАНКА 2130 (ПВТР)")
    print("="*80)
    
    cursor.execute("SELECT id, document_id, content FROM document_chunks WHERE id = 2130")
    result = cursor.fetchone()
    
    if result:
        chunk_id, doc_id, content = result
        print(f"Чанк {chunk_id} (Документ {doc_id}):")
        print(f"Содержимое:\n{content}")
    else:
        print("Чанк 2130 не найден")
    
    # Проверяем название документа
    print("\n" + "="*80)
    print("ИНФОРМАЦИЯ О ДОКУМЕНТЕ")
    print("="*80)
    
    cursor.execute("SELECT id, title FROM documents WHERE id = 3")
    doc_result = cursor.fetchone()
    
    if doc_result:
        doc_id, title = doc_result
        print(f"Документ {doc_id}: {title}")
    else:
        print("Документ 3 не найден")
    
    # Ищем все чанки с информацией о выплатах из документа 3
    print("\n" + "="*80)
    print("ВСЕ ЧАНКИ О ВЫПЛАТАХ ИЗ ДОКУМЕНТА 3 (ПВТР)")
    print("="*80)
    
    cursor.execute("""
        SELECT id, content 
        FROM document_chunks 
        WHERE document_id = 3 
        AND (content ILIKE '%выплат%' OR content ILIKE '%зарплат%' OR content ILIKE '%число%')
        ORDER BY id
    """)
    
    payment_chunks = cursor.fetchall()
    
    if payment_chunks:
        print(f"Найдено {len(payment_chunks)} чанков о выплатах:")
        for chunk_id, content in payment_chunks:
            print(f"\n--- Чанк {chunk_id} ---")
            print(content[:300] + "..." if len(content) > 300 else content)
    else:
        print("Чанки о выплатах не найдены")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        check_specific_chunks()
        print(f"\n{'='*80}")
        print("ПРОВЕРКА ЗАВЕРШЕНА")
        print('='*80)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc() 