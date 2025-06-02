#!/usr/bin/env python3
"""
Проверка содержимого контекста, отправляемого в LLM
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
    """Проверяем содержимое контекста"""
    try:
        # Инициализируем конфигурацию
        config = Config()
        print("✅ Конфигурация инициализирована")
        
        # Инициализируем RAG сервис
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован")
        
        # Тестовый вопрос
        question = "Установленные дни для расчетов с работниками"
        
        print(f"\n--- АНАЛИЗ КОНТЕКСТА ДЛЯ ВОПРОСА: {question} ---")
        
        # Получаем релевантные чанки напрямую
        chunks = rag_service.rag_system.search_relevant_chunks(question, 50)
        
        print(f"Найдено {len(chunks)} чанков")
        
        # Ищем чанк 2130
        chunk_2130_found = False
        chunk_2130_position = None
        
        for i, chunk in enumerate(chunks, 1):
            if chunk.get('id') == 2130:
                chunk_2130_found = True
                chunk_2130_position = i
                print(f"\n🎯 ЧАНК 2130 НАЙДЕН НА ПОЗИЦИИ {i}!")
                print(f"Similarity: {chunk.get('similarity', 'N/A')}")
                print(f"Search type: {chunk.get('search_type', 'N/A')}")
                print(f"Содержимое: {chunk.get('content', '')[:200]}...")
                break
        
        if not chunk_2130_found:
            print("\n❌ Чанк 2130 НЕ найден в результатах поиска")
        
        # Формируем контекст как это делает система
        context = rag_service.rag_system.format_context(chunks)
        
        print(f"\n--- АНАЛИЗ КОНТЕКСТА ---")
        print(f"Длина контекста: {len(context)} символов")
        
        # Проверяем, содержит ли контекст информацию о датах 12 и 27
        if '12' in context and '27' in context:
            print("✅ Контекст содержит числа 12 и 27")
        else:
            print("❌ Контекст НЕ содержит числа 12 и 27")
        
        if 'установленными днями для расчетов' in context.lower():
            print("✅ Контекст содержит фразу об установленных днях")
        else:
            print("❌ Контекст НЕ содержит фразу об установленных днях")
        
        # Показываем фрагменты контекста с ключевыми словами
        context_lower = context.lower()
        keywords = ['12', '27', 'установленными днями', 'расчетов с работниками']
        
        print(f"\n--- ПОИСК КЛЮЧЕВЫХ СЛОВ В КОНТЕКСТЕ ---")
        for keyword in keywords:
            if keyword in context_lower:
                # Находим позицию и показываем окружающий текст
                pos = context_lower.find(keyword)
                start = max(0, pos - 100)
                end = min(len(context), pos + 100)
                fragment = context[start:end]
                print(f"✅ '{keyword}' найдено:")
                print(f"   ...{fragment}...")
            else:
                print(f"❌ '{keyword}' не найдено")
        
        # Сохраняем полный контекст в файл для анализа
        with open('context_debug.txt', 'w', encoding='utf-8') as f:
            f.write(f"Вопрос: {question}\n")
            f.write(f"Найдено чанков: {len(chunks)}\n")
            f.write(f"Чанк 2130 найден: {chunk_2130_found}\n")
            if chunk_2130_found:
                f.write(f"Позиция чанка 2130: {chunk_2130_position}\n")
            f.write(f"Длина контекста: {len(context)} символов\n")
            f.write("\n" + "="*80 + "\n")
            f.write("ПОЛНЫЙ КОНТЕКСТ:\n")
            f.write("="*80 + "\n")
            f.write(context)
        
        print(f"\n📄 Полный контекст сохранен в файл 'context_debug.txt'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 