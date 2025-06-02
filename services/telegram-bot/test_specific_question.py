#!/usr/bin/env python3
"""
Тестирование конкретного вопроса об авансе
"""

import sys
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

# Добавляем пути к модулям
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "services" / "telegram-bot"))

# Загружаем переменные окружения
load_dotenv(project_root / ".env")
load_dotenv(project_root / "services" / "telegram-bot" / ".env.local")

try:
    from bot.rag_service import RAGService
    from bot.config import Config
    print("✅ Модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

async def main():
    """Тестирование конкретных вопросов"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Список вопросов для тестирования
        questions = [
            "Когда выплачивается аванс?",
            "15 числа что выплачивается?",
            "Какого числа аванс?",
            "Размер аванса сколько процентов?",
            "Когда выплачивается зарплата и аванс? Какие конкретные даты?"
        ]
        
        print("\n🧪 Тестирование конкретных вопросов...")
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"ВОПРОС {i}: {question}")
            print('='*60)
            
            try:
                result = await rag_service.answer_question(question)
                
                if result.get('success', False):
                    print("ОТВЕТ БОТА:")
                    print(result['answer'])
                    print(f"\nИСТОЧНИКИ ({len(result.get('sources', []))}):")
                    for source in result.get('sources', []):
                        print(f"- {source.get('title', 'N/A')}")
                    print(f"\nТОКЕНОВ ИСПОЛЬЗОВАНО: {result.get('tokens_used', 0)}")
                else:
                    print(f"❌ ОШИБКА: {result.get('error', 'Неизвестная ошибка')}")
                    
            except Exception as e:
                print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 