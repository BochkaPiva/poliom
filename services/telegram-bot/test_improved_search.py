#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path
import asyncio
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

def test_search_queries():
    """Тестирование поиска по различным запросам"""
    
    # Подключение к базе данных
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Сначала посмотрим структуру таблицы
    print("Структура таблицы document_chunks:")
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'document_chunks'")
    columns = cursor.fetchall()
    for col_name, col_type in columns:
        print(f"  {col_name}: {col_type}")
    
    # Тестовые запросы
    test_queries = [
        ("12 число", "12"),
        ("27 число", "27"), 
        ("два раза в месяц", "два раза"),
        ("установленные дни", "установленные дни"),
        ("расчеты с работниками", "расчеты"),
        ("заработная плата выплачивается", "заработная плата")
    ]
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ПОИСКА ПО КЛЮЧЕВЫМ СЛОВАМ")
    print("="*80)
    
    for description, keyword in test_queries:
        print(f"\n--- ПОИСК: {description} ('{keyword}') ---")
        
        # SQL запрос для поиска по содержимому
        sql = """
        SELECT id, document_id, content
        FROM document_chunks 
        WHERE content ILIKE %s
        ORDER BY id
        LIMIT 5
        """
        
        try:
            cursor.execute(sql, (f'%{keyword}%',))
            results = cursor.fetchall()
            
            if results:
                print(f"Найдено {len(results)} чанков:")
                for chunk_id, doc_id, content in results:
                    print(f"  Чанк {chunk_id} (Документ {doc_id}): {content[:100]}...")
            else:
                print("  Чанки не найдены")
                
        except Exception as e:
            print(f"  Ошибка поиска: {e}")
    
    # Специальный поиск по точным датам
    print(f"\n--- ПОИСК ТОЧНЫХ ДАТ ВЫПЛАТ ---")
    
    date_sql = """
    SELECT id, document_id, content
    FROM document_chunks 
    WHERE (content ILIKE '%12%' AND content ILIKE '%число%')
       OR (content ILIKE '%27%' AND content ILIKE '%число%')
       OR (content ILIKE '%два раза в месяц%')
       OR (content ILIKE '%установленными днями%')
    ORDER BY id
    """
    
    try:
        cursor.execute(date_sql)
        results = cursor.fetchall()
        
        if results:
            print(f"Найдено {len(results)} чанков с датами:")
            for chunk_id, doc_id, content in results:
                print(f"\nЧанк {chunk_id} (Документ {doc_id}):")
                print(f"  {content[:200]}...")
        else:
            print("Чанки с датами не найдены")
            
    except Exception as e:
        print(f"Ошибка поиска дат: {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        test_search_queries()
        print(f"\n{'='*80}")
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print('='*80)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc() 