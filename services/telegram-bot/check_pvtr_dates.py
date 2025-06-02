import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def get_db_connection():
    """Получение соединения с базой данных"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'poliom_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

def search_pvtr_payment_dates():
    """Поиск дат выплат в документе ПВТР"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 Поиск всех чанков из документа 'Правила внутреннего трудового распорядка'...")
        
        # Получаем все чанки из документа ПВТР (ID=3)
        cursor.execute("""
            SELECT id, content, chunk_index
            FROM document_chunks 
            WHERE document_id = 3
            ORDER BY chunk_index
        """)
        
        pvtr_chunks = cursor.fetchall()
        print(f"Найдено {len(pvtr_chunks)} чанков в документе ПВТР")
        
        # Ищем чанки с датами выплат
        payment_keywords = ['15', '27', '12', 'число', 'дата', 'срок', 'выплат', 'зарплат', 'аванс', 'заработная плата']
        
        relevant_chunks = []
        for chunk in pvtr_chunks:
            content_lower = chunk['content'].lower()
            if any(keyword in content_lower for keyword in payment_keywords):
                relevant_chunks.append(chunk)
        
        print(f"\n📋 Найдено {len(relevant_chunks)} релевантных чанков:")
        
        for chunk in relevant_chunks:
            print(f"\n--- Чанк {chunk['id']} (индекс {chunk['chunk_index']}) ---")
            print(chunk['content'][:500] + "..." if len(chunk['content']) > 500 else chunk['content'])
            print("-" * 80)
        
        # Специальный поиск чанков с числами 12, 15, 27
        print("\n🎯 Поиск чанков с конкретными числами:")
        
        for number in ['12', '15', '27']:
            cursor.execute("""
                SELECT id, content, chunk_index
                FROM document_chunks 
                WHERE document_id = 3 AND content ILIKE %s
                ORDER BY chunk_index
            """, (f'%{number}%',))
            
            number_chunks = cursor.fetchall()
            if number_chunks:
                print(f"\n📅 Чанки с числом '{number}' ({len(number_chunks)} найдено):")
                for chunk in number_chunks:
                    print(f"Чанк {chunk['id']}: {chunk['content'][:200]}...")
            else:
                print(f"\n❌ Чанки с числом '{number}' не найдены")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при поиске: {e}")

if __name__ == "__main__":
    search_pvtr_payment_dates() 