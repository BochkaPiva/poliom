#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.config import config
from bot.rag_service import RAGService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_specific_questions():
    """Тестирование конкретных проблемных вопросов пользователя"""
    
    print("🧪 ТЕСТИРОВАНИЕ ПРОБЛЕМНЫХ ВОПРОСОВ")
    print("=" * 60)
    
    # Инициализация RAG сервиса
    print("🔄 Инициализация RAG сервиса...")
    rag_service = RAGService(config.GIGACHAT_API_KEY)
    await rag_service.initialize()
    print("✅ RAG сервис инициализирован\n")
    
    # Проблемные вопросы пользователя
    test_questions = [
        "выплаты к юбилейным датам",
        "отпуск"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"{i}. Вопрос: '{question}'")
        print("-" * 40)
        
        try:
            # Получаем ответ
            result = await rag_service.answer_question(question, user_id=123)
            
            print(f"✅ Ответ получен")
            print(f"📝 Ответ: {result['answer'][:200]}...")
            print(f"📚 Источников: {len(result.get('sources', []))}")
            
            if result.get('sources'):
                print("📖 Источники:")
                for j, source in enumerate(result['sources'], 1):
                    print(f"   {j}. {source}")
            
            print(f"🔍 Контекст: {len(result.get('context', ''))} символов")
            print()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print()

if __name__ == "__main__":
    asyncio.run(test_specific_questions()) 