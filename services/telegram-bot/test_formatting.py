#!/usr/bin/env python3
"""
Тестовый скрипт для проверки форматирования ответов бота
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.config import config
from bot.rag_service import RAGService

async def test_formatting():
    """Тестируем форматирование ответов"""
    print("🧪 ТЕСТИРОВАНИЕ ФОРМАТИРОВАНИЯ ОТВЕТОВ")
    print("=" * 60)
    
    # Инициализируем RAG сервис
    print("🔄 Инициализация RAG сервиса...")
    rag_service = RAGService(config.GIGACHAT_API_KEY)
    await rag_service.initialize()
    print("✅ RAG сервис инициализирован\n")
    
    # Тестовые вопросы
    test_questions = [
        "Какие выплаты есть к юбилейным датам?",
        "Какие документы нужны для командировки?",
        "Когда можно взять отпуск?",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Вопрос: '{question}'")
        print("-" * 50)
        
        try:
            result = await rag_service.answer_question(question, user_id=123)
            
            if not result or 'answer' not in result:
                print("❌ Ответ не получен")
                continue
            
            print("📝 ФИНАЛЬНЫЙ ОТВЕТ:")
            print(result.get('answer', 'Ответ не получен'))
            
            print("\n📚 ИСТОЧНИКИ:")
            sources = result.get('sources', [])
            for j, source in enumerate(sources, 1):
                title = source.get('title', 'Документ')
                print(f"{j}. {title}")
            
            print(f"\n📄 ФАЙЛЫ ({len(result.get('files', []))} шт.):")
            files = result.get('files', [])
            for j, file in enumerate(files, 1):
                print(f"{j}. {file}")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке вопроса: {e}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_formatting()) 