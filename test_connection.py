import psycopg2
import sys

def test_connection():
    try:
        # Параметры подключения
        connection_params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'rag_chatbot',
            'user': 'postgres',
            'password': 'postgres123'
        }
        
        print("Попытка подключения к PostgreSQL...")
        print(f"Host: {connection_params['host']}")
        print(f"Port: {connection_params['port']}")
        print(f"Database: {connection_params['database']}")
        print(f"User: {connection_params['user']}")
        print("-" * 50)
        
        # Подключение к базе данных
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # Выполнение тестового запроса
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print("✅ Подключение успешно!")
        print(f"Версия PostgreSQL: {version}")
        
        # Проверка существующих таблиц
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n📋 Таблицы не найдены")
        
        # Закрытие соединения
        cursor.close()
        conn.close()
        
        print("\n🎉 Тест подключения завершен успешно!")
        print("\nДля pgAdmin используйте эти настройки:")
        print("Host: localhost")
        print("Port: 5432")
        print("Database: rag_chatbot")
        print("Username: postgres")
        print("Password: postgres123")
        
    except psycopg2.OperationalError as e:
        print("❌ Ошибка подключения:")
        print(f"   {e}")
        print("\n🔧 Возможные решения:")
        print("1. Проверьте, что PostgreSQL запущен: docker ps")
        print("2. Проверьте настройки в .env файле")
        print("3. Попробуйте перезапустить контейнер: docker-compose restart postgres")
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    test_connection() 