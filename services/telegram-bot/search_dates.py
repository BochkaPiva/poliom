import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.shared.config import Config
from services.shared.database import Database
import psycopg2

def main():
    try:
        config = Config()
        db = Database(config)
        
        # Ищем чанки, содержащие информацию о датах
        cursor = db.connection.cursor()
        cursor.execute('''
            SELECT id, document_id, content 
            FROM document_chunks 
            WHERE content ILIKE '%15%' 
            AND (content ILIKE '%аванс%' OR content ILIKE '%число%' OR content ILIKE '%дата%')
            ORDER BY id
        ''')
        
        results = cursor.fetchall()
        print(f'Найдено {len(results)} чанков с датами:')
        for chunk_id, doc_id, content in results:
            print(f'\nЧанк {chunk_id} (Документ {doc_id}):')
            print(content[:500] + '...' if len(content) > 500 else content)
            print('-' * 80)
            
        # Также ищем чанки с "25"
        cursor.execute('''
            SELECT id, document_id, content 
            FROM document_chunks 
            WHERE content ILIKE '%25%' 
            AND (content ILIKE '%зарплат%' OR content ILIKE '%число%' OR content ILIKE '%дата%')
            ORDER BY id
        ''')
        
        results2 = cursor.fetchall()
        print(f'\nНайдено {len(results2)} чанков с "25":')
        for chunk_id, doc_id, content in results2:
            print(f'\nЧанк {chunk_id} (Документ {doc_id}):')
            print(content[:500] + '...' if len(content) > 500 else content)
            print('-' * 80)
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main() 