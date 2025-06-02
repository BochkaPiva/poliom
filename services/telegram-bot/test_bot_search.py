#!/usr/bin/env python3
"""
Тест поиска через Telegram бота
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавляем пути к модулям
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

from bot.rag_service import RAGService
from bot.config import config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_rag_service():
    """Тестирование RAG сервиса"""
    print("🧪 ТЕСТИРОВАНИЕ RAG СЕРВИСА")
    print("=" * 60)
    
    try:
        # Создаем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        
        # Инициализируем
        print("🔄 Инициализация RAG сервиса...")
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Проверяем здоровье системы
        print("\n🏥 Проверка здоровья системы...")
        health = await rag_service.health_check()
        print(f"Общий статус: {'✅' if health['overall'] else '❌'}")
        print(f"LLM: {'✅' if health['llm'] else '❌'}")
        print(f"Эмбеддинги: {'✅' if health['embeddings'] else '❌'}")
        print(f"База данных: {'✅' if health['database'] else '❌'}")
        print(f"Документов: {health['documents_count']}")
        
        # Тестовые вопросы
        test_questions = [
            "Как оформить отпуск?",
            "Размер премии",
            "Премирование работников",
            "Что такое грейд должности?",
            "Условия выплаты заработной платы"
        ]
        
        print("\n🔍 ТЕСТИРОВАНИЕ ПОИСКА")
        print("=" * 60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. Вопрос: '{question}'")
            print("-" * 40)
            
            try:
                result = await rag_service.answer_question(question, user_id=1)
                
                if result['success']:
                    print(f"✅ Ответ получен")
                    print(f"📝 Ответ: {result['answer'][:200]}...")
                    print(f"📚 Источников: {len(result.get('sources', []))}")
                    
                    if result.get('sources'):
                        print("📖 Источники:")
                        for j, source in enumerate(result['sources'][:3], 1):
                            print(f"   {j}. {source.get('title', 'Неизвестно')}")
                else:
                    print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                    
            except Exception as e:
                print(f"❌ Исключение: {e}")
        
        print("\n🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Главная функция"""
    if not config.validate():
        print("❌ Некорректная конфигурация")
        return
    
    await test_rag_service()

if __name__ == "__main__":
    asyncio.run(main()) 