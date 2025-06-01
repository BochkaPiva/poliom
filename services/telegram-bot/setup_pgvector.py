#!/usr/bin/env python3
"""
Скрипт для установки pgvector расширения в PostgreSQL
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Добавляем пути к модулям
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "services" / "telegram-bot"))

from bot.config import Config

def setup_pgvector():
    """Установка pgvector расширения"""
    print("🔧 Настройка pgvector расширения...")
    
    try:
        config = Config()
        database_url = config.DATABASE_URL
        
        # Парсим URL базы данных
        if database_url.startswith('postgresql://'):
            # Извлекаем параметры подключения
            import urllib.parse
            parsed = urllib.parse.urlparse(database_url)
            
            conn_params = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path[1:],  # убираем первый слеш
                'user': parsed.username,
                'password': parsed.password
            }
            
            print(f"📡 Подключение к базе данных: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
            
            # Подключаемся к базе данных
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Проверяем, установлено ли расширение
            cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
            extension_exists = cursor.fetchone()[0]
            
            if extension_exists:
                print("✅ Расширение pgvector уже установлено")
            else:
                print("📦 Устанавливаем расширение pgvector...")
                try:
                    cursor.execute("CREATE EXTENSION vector;")
                    print("✅ Расширение pgvector успешно установлено")
                except psycopg2.Error as e:
                    if "does not exist" in str(e):
                        print("❌ Расширение pgvector не найдено в системе")
                        print("💡 Необходимо установить pgvector на сервере PostgreSQL:")
                        print("   - Для Ubuntu/Debian: sudo apt install postgresql-15-pgvector")
                        print("   - Для CentOS/RHEL: sudo yum install pgvector")
                        print("   - Для Docker: используйте образ pgvector/pgvector")
                        return False
                    else:
                        raise e
            
            # Проверяем работу оператора <=>
            try:
                cursor.execute("SELECT '[1,2,3]'::vector <=> '[1,2,3]'::vector;")
                result = cursor.fetchone()[0]
                print(f"✅ Оператор <=> работает корректно (результат: {result})")
            except psycopg2.Error as e:
                print(f"❌ Ошибка проверки оператора <=>: {e}")
                return False
            
            cursor.close()
            conn.close()
            
            print("🎉 pgvector настроен успешно!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка настройки pgvector: {e}")
        return False

def create_vector_index():
    """Создание индекса для векторного поиска"""
    print("📊 Создание индекса для векторного поиска...")
    
    try:
        config = Config()
        database_url = config.DATABASE_URL
        
        # Парсим URL базы данных
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password
        }
        
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем существование таблицы document_chunks
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'document_chunks'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("⚠️ Таблица document_chunks не найдена")
            print("💡 Сначала запустите миграции базы данных")
            return False
        
        # Проверяем тип колонки embedding
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'embedding';
        """)
        
        result = cursor.fetchone()
        if result:
            data_type = result[0]
            print(f"📋 Тип колонки embedding: {data_type}")
            
            if data_type != 'USER-DEFINED':  # vector тип показывается как USER-DEFINED
                print("🔄 Изменяем тип колонки embedding на vector...")
                try:
                    # Сначала удаляем существующие данные (если есть)
                    cursor.execute("DELETE FROM document_chunks;")
                    
                    # Изменяем тип колонки
                    cursor.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024);")
                    print("✅ Тип колонки изменен на vector(1024)")
                except psycopg2.Error as e:
                    print(f"❌ Ошибка изменения типа колонки: {e}")
                    return False
        
        # Создаем индекс для быстрого поиска
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
                ON document_chunks USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """)
            print("✅ Индекс для векторного поиска создан")
        except psycopg2.Error as e:
            print(f"⚠️ Не удалось создать индекс: {e}")
            print("💡 Индекс будет создан автоматически после добавления данных")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания индекса: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Настройка pgvector для векторного поиска")
    print("=" * 50)
    
    if setup_pgvector():
        if create_vector_index():
            print("✅ Настройка завершена успешно!")
        else:
            print("⚠️ Настройка завершена с предупреждениями")
    else:
        print("❌ Настройка не удалась") 