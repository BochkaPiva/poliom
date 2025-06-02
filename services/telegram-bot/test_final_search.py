#!/usr/bin/env python3
"""
Финальный тест улучшенной системы поиска для вопросов о датах выплат
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем путь к shared модулям
sys.path.append(str(Path(__file__).parent.parent / "shared"))

from dotenv import load_dotenv

# Импортируем необходимые модули
try:
    from services.shared.config.settings import get_config
    from services.shared.utils.simple_rag import SimpleRAG
except ImportError:
    # Альтернативный импорт
    sys.path.append(str(Path(__file__).parent.parent))
    from shared.config.settings import get_config
    from shared.utils.simple_rag import SimpleRAG

async def test_salary_questions():
    """Тестируем вопросы о зарплате с улучшенной системой поиска"""
    
    # Загружаем переменные окружения
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    print(f"Загружен .env файл: {env_path}")
    
    # Инициализируем конфигурацию и RAG
    config = get_config()
    rag = SimpleRAG(config)
    
    # Список вопросов для тестирования
    test_questions = [
        "Когда выплачивается аванс?",
        "Какого числа выплачивается зарплата?", 
        "В какие дни месяца происходят выплаты?",
        "12 и 27 число - это дни выплат?",
        "Сколько раз в месяц выплачивается зарплата?"
    ]
    
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ УЛУЧШЕННОЙ СИСТЕМЫ ПОИСКА")
    print("=" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- ВОПРОС {i}: {question} ---")
        
        try:
            # Получаем ответ от RAG системы
            answer = await rag.answer_question(question)
            print(f"ОТВЕТ: {answer}")
            
        except Exception as e:
            print(f"ОШИБКА: {e}")
        
        print("-" * 60)
    
    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_salary_questions()) 