#!/usr/bin/env python3
"""
Отладка контекста, передаваемого в LLM
"""

import sys
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

# Загружаем переменные окружения
env_path = root_dir / '.env'
load_dotenv(env_path)

try:
    from services.shared.config import Config
    from services.shared.database import Database
    from services.bot.rag_service import RAGService
    print("✅ Модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

async def main():
    """Отладка контекста для LLM"""
    try:
        # Инициализация
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        db = Database(config)
        print("✅ База данных подключена")
        
        rag_service = RAGService(config, db)
        print("✅ RAG сервис инициализирован")
        
        # Поиск чанков с датами в базе данных
        print("\n🔍 ПОИСК ЧАНКОВ С ДАТАМИ В БАЗЕ ДАННЫХ")
        print("=" * 80)
        
        cursor = db.connection.cursor()
        
        # Ищем чанки с "15" и словами связанными с авансом
        cursor.execute('''
            SELECT id, document_id, content 
            FROM document_chunks 
            WHERE content ILIKE '%15%' 
            AND (content ILIKE '%аванс%' OR content ILIKE '%число%' OR content ILIKE '%дата%')
            ORDER BY id
        ''')
        
        results = cursor.fetchall()
        print(f'Найдено {len(results)} чанков с "15":')
        for chunk_id, doc_id, content in results:
            print(f'\nЧанк {chunk_id} (Документ {doc_id}):')
            print(content[:300] + '...' if len(content) > 300 else content)
            print('-' * 40)
            
        # Ищем чанки с "25" и словами связанными с зарплатой
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
            print(content[:300] + '...' if len(content) > 300 else content)
            print('-' * 40)
        
        # Тестируем вопрос
        question = "Когда выплачивается аванс?"
        print(f"\n🔍 ОТЛАДКА ВОПРОСА: {question}")
        print("=" * 80)
        
        answer = await rag_service.answer_question(question)
        
        print(f"\n🤖 ПОЛУЧАЕМ ОТВЕТ ОТ LLM...")
        print("=" * 80)
        print(f"ОТВЕТ LLM:\n{answer}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 