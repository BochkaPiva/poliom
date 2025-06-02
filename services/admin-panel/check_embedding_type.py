#!/usr/bin/env python3
"""
Проверка типа поля embedding
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

from sqlalchemy import text
from shared.models.database import SessionLocal

def main():
    db = SessionLocal()
    try:
        # Проверяем тип поля embedding
        result = db.execute(text("""
            SELECT 
                pg_typeof(embedding) as embedding_type,
                vector_dims(embedding) as dimensions
            FROM document_chunks 
            WHERE embedding IS NOT NULL 
            LIMIT 1
        """)).fetchall()
        
        if result:
            print(f'Тип поля: {result[0][0]}')
            print(f'Размерность: {result[0][1]}')
            
            # Проверяем пример значений
            sample = db.execute(text("""
                SELECT embedding::text
                FROM document_chunks 
                WHERE embedding IS NOT NULL 
                LIMIT 1
            """)).fetchall()
            
            if sample:
                print(f'Пример (первые 100 символов): {sample[0][0][:100]}...')
        else:
            print('Нет данных')
            
    except Exception as e:
        print(f'Ошибка: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    main() 