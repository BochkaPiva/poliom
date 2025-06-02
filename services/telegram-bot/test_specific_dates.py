#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Добавляем путь к shared модулям
sys.path.append(str(Path(__file__).parent.parent / "shared"))

from dotenv import load_dotenv
from utils.config import Config
from utils.simple_rag import RAGService

# Загружаем переменные окружения
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
print(f"Загружен .env файл: {env_path}")

async def main():
    try:
        # Инициализация конфигурации и RAG
        config = Config()
        print("Конфигурация инициализирована")
        
        rag_service = RAGService(config)
        print("RAG сервис инициализирован")
        
        # Тестовые запросы о датах выплат
        queries = [
            "Когда выплачивается аванс?",
            "В какие дни месяца выплачивается зарплата?", 
            "12 число месяца выплата",
            "27 число месяца выплата",
            "Установленные дни для расчетов с работниками",
            "два раза в месяц заработная плата"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*80}")
            print(f"ЗАПРОС {i}: {query}")
            print('='*80)
            
            try:
                # Получаем ответ от RAG системы
                answer = await rag_service.answer_question(query)
                print(f"ОТВЕТ: {answer}")
                
            except Exception as e:
                print(f"Ошибка при обработке запроса '{query}': {e}")
        
        print(f"\n{'='*80}")
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print('='*80)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 