#!/usr/bin/env python3
"""
Финальный тест RAG системы с улучшенным поиском
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
    """Тестируем улучшенную RAG систему"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Тестовые вопросы о датах выплат
        test_questions = [
            "Когда выплачивается аванс?",
            "Какого числа выплачивается зарплата?", 
            "В какие дни месяца происходят выплаты?",
            "12 и 27 число - это дни выплат?",
            "Сколько раз в месяц выплачивается зарплата?",
            "Установленные дни для расчетов с работниками"
        ]
        
        print("\n" + "=" * 80)
        print("ТЕСТИРОВАНИЕ УЛУЧШЕННОЙ RAG СИСТЕМЫ")
        print("=" * 80)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- ВОПРОС {i}: {question} ---")
            
            try:
                # Получаем ответ от RAG системы
                result = await rag_service.answer_question(question)
                
                if result.get('success', True):
                    print(f"ОТВЕТ: {result.get('answer', 'Нет ответа')}")
                    
                    sources = result.get('sources', [])
                    if sources:
                        print(f"ИСТОЧНИКИ ({len(sources)}):")
                        for j, source in enumerate(sources, 1):
                            print(f"  {j}. {source}")
                else:
                    print(f"ОШИБКА: {result.get('error', 'Неизвестная ошибка')}")
                
            except Exception as e:
                print(f"ОШИБКА: {e}")
                import traceback
                traceback.print_exc()
            
            print("-" * 60)
        
        print("\n" + "=" * 80)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 