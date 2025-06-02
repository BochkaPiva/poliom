#!/usr/bin/env python3
"""
Специальный тест для проверки ответов на вопросы о датах выплат
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
    """Тестируем конкретные вопросы о датах выплат"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Тестовые вопросы с более конкретными формулировками
        test_questions = [
            "Согласно правилам внутреннего трудового распорядка, в какие дни месяца выплачивается заработная плата?",
            "Какие установлены дни для расчетов с работниками согласно ПВТР?",
            "12 и 27 число - это установленные дни выплат?",
            "Два раза в месяц - когда именно происходят выплаты?",
            "Расскажите о сроках выплаты заработной платы в компании",
            "Какая периодичность выплат заработной платы установлена?"
        ]
        
        print("\n" + "=" * 80)
        print("ТЕСТ КОНКРЕТНЫХ ВОПРОСОВ О ДАТАХ ВЫПЛАТ")
        print("=" * 80)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- ВОПРОС {i}: {question} ---")
            
            try:
                # Получаем ответ от RAG системы
                result = await rag_service.answer_question(question)
                
                if result.get('success', True):
                    answer = result.get('answer', 'Нет ответа')
                    print(f"ОТВЕТ: {answer}")
                    
                    # Проверяем, содержит ли ответ ключевые слова
                    answer_lower = answer.lower()
                    key_phrases = ['12', '27', 'число', 'два раза', 'месяц', 'выплат']
                    found_phrases = [phrase for phrase in key_phrases if phrase in answer_lower]
                    
                    if found_phrases:
                        print(f"✅ НАЙДЕНЫ КЛЮЧЕВЫЕ ФРАЗЫ: {found_phrases}")
                    else:
                        print("❌ Ключевые фразы о датах не найдены")
                    
                    sources = result.get('sources', [])
                    if sources:
                        print(f"ИСТОЧНИКИ ({len(sources)}):")
                        for j, source in enumerate(sources, 1):
                            print(f"  {j}. {source}")
                    
                    chunks_found = result.get('chunks_found', 0)
                    print(f"Найдено чанков: {chunks_found}")
                    
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