#!/usr/bin/env python3
"""
Скрипт для миграции данных из старой базы данных в новую с pgvector
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_database(database_url):
    """Подключение к базе данных"""
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

def migrate_data():
    """Миграция данных из старой базы в новую"""
    
    # Старая база данных
    old_db_url = "postgresql://postgres:postgres123@localhost:5432/rag_chatbot"
    
    # Новая база данных с pgvector
    new_db_url = "postgresql://postgres:postgres@localhost:5433/poliom"
    
    logger.info("🔄 Начинаем миграцию данных...")
    
    # Подключение к старой базе
    old_conn = connect_to_database(old_db_url)
    if not old_conn:
        logger.error("❌ Не удалось подключиться к старой базе данных")
        return False
    
    # Подключение к новой базе
    new_conn = connect_to_database(new_db_url)
    if not new_conn:
        logger.error("❌ Не удалось подключиться к новой базе данных")
        old_conn.close()
        return False
    
    try:
        old_cursor = old_conn.cursor(cursor_factory=RealDictCursor)
        new_cursor = new_conn.cursor()
        
        # Получаем список всех таблиц из старой базы
        old_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = old_cursor.fetchall()
        logger.info(f"📋 Найдено таблиц для миграции: {len(tables)}")
        
        for table in tables:
            table_name = table['table_name']
            logger.info(f"🔄 Мигрируем таблицу: {table_name}")
            
            # Получаем структуру таблицы
            old_cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position;
            """)
            
            columns = old_cursor.fetchall()
            
            # Создаем таблицу в новой базе
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            column_definitions = []
            
            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']
                is_nullable = col['is_nullable']
                col_default = col['column_default']
                
                # Преобразуем типы данных
                if col_type == 'character varying':
                    col_type = 'VARCHAR'
                elif col_type == 'timestamp without time zone':
                    col_type = 'TIMESTAMP'
                elif col_type == 'double precision':
                    col_type = 'DOUBLE PRECISION'
                elif col_type == 'USER-DEFINED' and col_name == 'embedding':
                    # Это векторное поле - используем vector тип
                    col_type = 'vector(1536)'  # Предполагаем размерность 1536
                
                col_def = f"{col_name} {col_type}"
                
                if is_nullable == 'NO':
                    col_def += " NOT NULL"
                
                if col_default:
                    if 'nextval' in col_default:
                        col_def = col_def.replace(col_type, 'SERIAL')
                    else:
                        col_def += f" DEFAULT {col_default}"
                
                column_definitions.append(col_def)
            
            create_table_sql += ", ".join(column_definitions) + ");"
            
            try:
                new_cursor.execute(create_table_sql)
                logger.info(f"✅ Таблица {table_name} создана")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания таблицы {table_name}: {e}")
                continue
            
            # Копируем данные
            old_cursor.execute(f"SELECT * FROM {table_name}")
            rows = old_cursor.fetchall()
            
            if rows:
                # Получаем названия колонок
                column_names = [desc[0] for desc in old_cursor.description]
                
                # Подготавливаем INSERT запрос
                placeholders = ", ".join(["%s"] * len(column_names))
                insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                
                # Вставляем данные
                for row in rows:
                    try:
                        new_cursor.execute(insert_sql, tuple(row))
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка вставки данных в {table_name}: {e}")
                        continue
                
                logger.info(f"✅ Скопировано {len(rows)} записей в таблицу {table_name}")
            else:
                logger.info(f"ℹ️ Таблица {table_name} пуста")
        
        # Создаем индексы для векторного поиска
        logger.info("🔄 Создаем индексы для векторного поиска...")
        
        # Проверяем существование таблицы document_chunks
        new_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'document_chunks'
            );
        """)
        
        if new_cursor.fetchone()[0]:
            try:
                new_cursor.execute("""
                    CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
                    ON document_chunks USING hnsw (embedding vector_cosine_ops) 
                    WITH (m = 16, ef_construction = 64);
                """)
                logger.info("✅ HNSW индекс для векторного поиска создан")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        # Коммитим изменения
        new_conn.commit()
        logger.info("✅ Миграция данных завершена успешно!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        new_conn.rollback()
        return False
        
    finally:
        old_conn.close()
        new_conn.close()

def main():
    """Главная функция"""
    logger.info("🚀 Запуск миграции данных в pgvector базу...")
    
    if migrate_data():
        logger.info("🎉 Миграция завершена успешно!")
        return 0
    else:
        logger.error("💥 Миграция завершилась с ошибками!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 