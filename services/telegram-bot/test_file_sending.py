#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала отправки файлов
"""

import sys
import os
import asyncio
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

async def test_file_sending_feature():
    """Тест функционала отправки файлов"""
    print("🧪 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА ОТПРАВКИ ФАЙЛОВ")
    print("=" * 60)
    
    # Инициализируем RAG сервис
    print("🔄 Инициализация RAG сервиса...")
    try:
        from bot.config import config
        from bot.rag_service import RAGService
        
        rag_service = RAGService(config.GIGACHAT_API_KEY)
        await rag_service.initialize()
        print("✅ RAG сервис инициализирован\n")
    except Exception as e:
        print(f"❌ Ошибка инициализации RAG: {e}")
        return
    
    # Тестовый вопрос
    test_question = "Какие документы нужны для командировки?"
    print(f"❓ Тестовый вопрос: '{test_question}'")
    print("-" * 60)
    
    try:
        # Получаем ответ с файлами
        result = await rag_service.answer_question(test_question, user_id=123)
        
        if not result or 'answer' not in result:
            print("❌ Ответ не получен")
            return
        
        print("📝 ОТВЕТ ПОЛУЧЕН:")
        print(result.get('answer', 'Ответ не получен')[:200] + "...")
        
        # Проверяем файлы
        files = result.get('files', [])
        print(f"\n📎 НАЙДЕНО ФАЙЛОВ: {len(files)}")
        
        if files:
            print("\n📋 ИНФОРМАЦИЯ О ФАЙЛАХ:")
            for i, file_info in enumerate(files, 1):
                print(f"\n{i}. {file_info.get('title', 'Без названия')}")
                print(f"   📄 Оригинальное имя: {file_info.get('original_filename', 'N/A')}")
                print(f"   📁 Путь: {file_info.get('file_path', 'N/A')}")
                print(f"   📊 Релевантность: {file_info.get('similarity', 0):.1%}")
                print(f"   📏 Размер: {file_info.get('file_size', 0)} байт")
                print(f"   📋 Тип: {file_info.get('file_type', 'N/A')}")
                
                # Проверяем существование файла
                file_path = file_info.get('file_path')
                if file_path:
                    file_path_obj = Path(file_path)
                    if file_path_obj.exists():
                        actual_size = file_path_obj.stat().st_size
                        print(f"   ✅ Файл существует (размер: {actual_size} байт)")
                        
                        # Проверяем размер для Telegram
                        if actual_size > 50 * 1024 * 1024:
                            print(f"   ⚠️ ВНИМАНИЕ: Файл больше 50MB - не может быть отправлен через Telegram")
                        else:
                            print(f"   ✅ Размер подходит для отправки через Telegram")
                    else:
                        print(f"   ❌ ФАЙЛ НЕ НАЙДЕН НА ДИСКЕ")
                else:
                    print(f"   ❌ ПУТЬ К ФАЙЛУ НЕ УКАЗАН")
        else:
            print("ℹ️ Файлы не найдены для данного вопроса")
        
        # Проверяем источники
        sources = result.get('sources', [])
        print(f"\n📚 ИСТОЧНИКИ: {len(sources)}")
        for i, source in enumerate(sources, 1):
            print(f"   {i}. {source.get('title', 'Документ')}")
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"   • Найдено чанков: {result.get('chunks_found', 0)}")
        print(f"   • Использовано токенов: {result.get('tokens_used', 0)}")
        print(f"   • Длина контекста: {result.get('context_length', 0)} символов")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Тест завершен")

async def test_file_validation():
    """Тест валидации файлов"""
    print("\n🔍 ТЕСТИРОВАНИЕ ВАЛИДАЦИИ ФАЙЛОВ")
    print("=" * 40)
    
    # Тестовые данные
    test_files = [
        {
            'title': 'Маленький файл',
            'file_path': '/path/to/small_file.pdf',
            'file_size': 1024  # 1KB
        },
        {
            'title': 'Большой файл',
            'file_path': '/path/to/big_file.pdf', 
            'file_size': 60 * 1024 * 1024  # 60MB
        },
        {
            'title': 'Файл без пути',
            'file_path': None,
            'file_size': 2048
        }
    ]
    
    for i, file_info in enumerate(test_files, 1):
        print(f"\n{i}. {file_info['title']}")
        
        file_path = file_info.get('file_path')
        file_size = file_info.get('file_size', 0)
        
        # Проверка размера
        if file_size > 50 * 1024 * 1024:
            print(f"   ❌ Слишком большой файл: {file_size / (1024*1024):.1f} MB")
        else:
            print(f"   ✅ Размер подходит: {file_size / 1024:.1f} KB")
        
        # Проверка пути
        if not file_path:
            print(f"   ❌ Путь к файлу отсутствует")
        else:
            print(f"   ✅ Путь указан: {file_path}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    asyncio.run(test_file_sending_feature())
    asyncio.run(test_file_validation()) 