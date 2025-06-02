#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест улучшенной системы ответов бота
Проверяет:
1. Правильное экранирование markdown
2. Дедупликацию источников
3. Точность ответов на основе корпоративных документов
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.shared.utils.simple_rag import SimpleRAG
from services.shared.utils.llm_client import SimpleLLMClient

# Загружаем переменные окружения из корневого .env файла
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружен основной .env файл: {env_path}")

# Загружаем локальный .env файл если он есть
local_env_path = Path(__file__).parent / '.env'
if local_env_path.exists():
    load_dotenv(local_env_path, override=True)
    print(f"✅ Загружен локальный .env файл: {local_env_path}")

# Проверяем DATABASE_URL
database_url = os.getenv('DATABASE_URL')
print(f"🔗 DATABASE_URL: {database_url}")

def test_improved_answers():
    """Тестирует улучшенную систему ответов"""
    
    print("🧪 ТЕСТИРОВАНИЕ УЛУЧШЕННОЙ СИСТЕМЫ ОТВЕТОВ")
    print("=" * 60)
    
    # Инициализация
    try:
        print("\n🔧 Инициализация системы...")
        
        # Создаем подключение к БД используя DATABASE_URL
        if not database_url:
            print("❌ DATABASE_URL не найден в переменных окружения")
            return False
            
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        print("✅ Подключение к базе данных установлено")
        
        # Инициализация RAG
        gigachat_key = os.getenv('GIGACHAT_API_KEY')
        if not gigachat_key:
            print("❌ GIGACHAT_API_KEY не найден в .env")
            return False
            
        rag_system = SimpleRAG(db_session, gigachat_key)
        print("✅ RAG система инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False
    
    # Тестовые вопросы
    test_questions = [
        {
            "question": "Когда выплачивается зарплата?",
            "expected_keywords": ["15", "30", "аванс", "основная часть"],
            "description": "Проверка конкретных дат выплаты зарплаты"
        },
        {
            "question": "Размер доплаты за ночную работу",
            "expected_keywords": ["40", "процент", "%"],
            "description": "Проверка конкретных процентов доплат"
        },
        {
            "question": "Как оформить отпуск?",
            "expected_keywords": ["заявление", "руководитель"],
            "description": "Проверка процедуры оформления отпуска"
        },
        {
            "question": "Что такое грейд должности?",
            "expected_keywords": ["грейд", "должност"],
            "description": "Проверка определения грейда"
        },
        {
            "question": "Размер премии сотрудников",
            "expected_keywords": ["премия", "размер"],
            "description": "Проверка информации о премиях"
        }
    ]
    
    print(f"\n🔍 Тестирование {len(test_questions)} вопросов...")
    print("-" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_questions, 1):
        print(f"\n📝 ТЕСТ {i}: {test_case['description']}")
        print(f"❓ Вопрос: {test_case['question']}")
        
        try:
            # Получаем ответ
            result = rag_system.answer_question(test_case['question'])
            
            if result['success']:
                answer = result['answer']
                sources = result['sources']
                
                print(f"✅ Ответ получен ({result['tokens_used']} токенов)")
                print(f"📄 Найдено источников: {len(sources)}")
                
                # Проверяем ответ
                print("\n📋 ОТВЕТ:")
                print("-" * 40)
                print(answer)
                print("-" * 40)
                
                # Проверяем источники
                if sources:
                    print("\n📚 ИСТОЧНИКИ:")
                    unique_titles = set()
                    for j, source in enumerate(sources, 1):
                        title = source['title']
                        if title in unique_titles:
                            print(f"⚠️  {j}. {title} (ДУБЛИРОВАНИЕ!)")
                        else:
                            print(f"✅ {j}. {title}")
                            unique_titles.add(title)
                else:
                    unique_titles = set()  # Инициализируем пустое множество если нет источников
                
                # Проверяем наличие ожидаемых ключевых слов
                found_keywords = []
                for keyword in test_case['expected_keywords']:
                    if keyword.lower() in answer.lower():
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"🎯 Найдены ключевые слова: {', '.join(found_keywords)}")
                else:
                    print("⚠️  Ожидаемые ключевые слова не найдены")
                
                # Проверяем markdown экранирование
                markdown_chars = ['*', '_', '`', '[', ']']
                unescaped_chars = []
                for char in markdown_chars:
                    if char in answer and f'\\{char}' not in answer:
                        unescaped_chars.append(char)
                
                if unescaped_chars:
                    print(f"⚠️  Неэкранированные markdown символы: {unescaped_chars}")
                else:
                    print("✅ Markdown символы правильно экранированы")
                
                results.append({
                    'question': test_case['question'],
                    'success': True,
                    'keywords_found': len(found_keywords),
                    'sources_count': len(sources),
                    'has_duplicates': len(sources) != len(unique_titles),
                    'markdown_ok': len(unescaped_chars) == 0,
                    'tokens_used': result['tokens_used']
                })
                
            else:
                print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                results.append({
                    'question': test_case['question'],
                    'success': False,
                    'error': result.get('error', 'Неизвестная ошибка')
                })
                
        except Exception as e:
            print(f"❌ Исключение: {e}")
            results.append({
                'question': test_case['question'],
                'success': False,
                'error': str(e)
            })
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    
    successful_tests = [r for r in results if r['success']]
    total_tests = len(results)
    success_rate = len(successful_tests) / total_tests * 100
    
    print(f"✅ Успешных тестов: {len(successful_tests)}/{total_tests} ({success_rate:.1f}%)")
    
    if successful_tests:
        total_tokens = sum(r['tokens_used'] for r in successful_tests)
        avg_sources = sum(r['sources_count'] for r in successful_tests) / len(successful_tests)
        duplicates_count = sum(1 for r in successful_tests if r['has_duplicates'])
        markdown_ok_count = sum(1 for r in successful_tests if r['markdown_ok'])
        
        print(f"🔢 Всего токенов использовано: {total_tokens}")
        print(f"📄 Среднее количество источников: {avg_sources:.1f}")
        print(f"🔄 Тестов с дублированием источников: {duplicates_count}")
        print(f"📝 Тестов с правильным markdown: {markdown_ok_count}/{len(successful_tests)}")
        
        # Проверяем улучшения
        print("\n🎯 ПРОВЕРКА УЛУЧШЕНИЙ:")
        if duplicates_count == 0:
            print("✅ Дублирование источников устранено")
        else:
            print(f"⚠️  Все еще есть дублирование в {duplicates_count} тестах")
            
        if markdown_ok_count == len(successful_tests):
            print("✅ Markdown символы правильно экранированы во всех ответах")
        else:
            print(f"⚠️  Проблемы с markdown в {len(successful_tests) - markdown_ok_count} ответах")
    
    print("\n🏁 Тестирование завершено!")
    return success_rate > 80

if __name__ == "__main__":
    success = test_improved_answers()
    sys.exit(0 if success else 1) 