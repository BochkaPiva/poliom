import os
import sys
from dotenv import load_dotenv

# Добавляем путь к shared модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from database import engine, Base
from models import Admin, User, Document, DocumentChunk, UserQuery

def create_tables():
    """Создает все таблицы в базе данных"""
    try:
        print("🔧 Создание таблиц в базе данных...")
        
        # Загружаем переменные окружения
        load_dotenv('.env')
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        
        print("✅ Все таблицы созданы успешно!")
        
        # Показываем созданные таблицы
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Созданные таблицы ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")
            
        print("\n🎉 База данных готова к использованию!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables() 